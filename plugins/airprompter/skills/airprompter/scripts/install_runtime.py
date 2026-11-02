#!/usr/bin/env python3
"""AIR-2167 data-only install/verify engine. Only the two bundled launchers are host entrypoints.

No workflow execution, arbitrary HTTP, shell evaluation, credential custody or daemon.
Same-user processes are trusted; private directories and no-link checks protect the cache
from other users and refuse pre-existing links. Exact inventory + an MCP/server-supplied
fingerprint protect against corrupted payloads, including rewritten local checksum files.
"""
import argparse
import contextlib
import datetime
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import ssl
import stat
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

# Receipts/checksums are projections of the bounded response. Read them under
# the same byte ceiling: contract character limits are not UTF-8 byte limits.
MAX_RESPONSE = 4_000_000
MAX_DOWNLOAD = 8_000_000
MAX_FILES = 264
HASH = re.compile(r"^[0-9a-f]{64}$")
TOKEN = re.compile(r"^[A-Za-z0-9_-]{43}$")
API_ORIGINS = {"prod": "https://api.airprompter.com", "dev": "https://api-dev.airprompter.com"}
# Stored-file download pins per target, from the trusted deployment configuration
# (SSM /<env>/cdk/stack-refs/database/workflow-files/download-domain). Never learned
# from a workflow, the redemption payload or a signed URL. `dev` is the internal QA
# target only; customers use `prod`, which has no file-download distribution yet,
# so a prod install refuses before redemption and those workflows run remotely.
DOWNLOAD_ORIGINS = {"dev": "https://d3e65ddf0mnnkp.cloudfront.net"}
HOST_FAMILIES = {"claude", "codex", "cursor", "gemini", "antigravity", "hermes", "chatgpt", "openclaw", "unknown"}
REPORT_HOSTS = {"mcp", "chrome", "firefox", "safari", "chatgpt", "codex", "claude", "cursor", "unknown"}
# P4b-3: python.org macOS builds ship without a CA bundle until "Install Certificates.command"
# runs. These are the OS's own bundles; verification itself is never disabled.
SYSTEM_CA_BUNDLES = ("/etc/ssl/cert.pem", "/private/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt")
STDIN_SECONDS = 10
MAX_TOKEN_REQUEST = 512
# Fixed hints for the calling agent (never server/file/URL/token data). The user hears
# none of this: a failure means the remote run, and the TLS line only if they ask why.
TOKEN_FILE_INSTALL = "scripts/install --token-file <tokenFolder>/<new file> --fingerprint <fingerprint> --target {target}"
PIPE_INSTALL = "printf '%s' '{{\"token\":\"<token>\"}}' | scripts/install --fingerprint <fingerprint> --target {target}"
HEREDOC_REPORTS = "scripts/verify --reports <queue|ack> --folder <path> --fingerprint <expected> --principal-key <principal> <<'JSON' (the JSON, then a line JSON)"
REMOTE = "Run remotely: call the run tool again without client."
HINTS = {
    "tls_certificates_unavailable": "If the user asks why: Your computer's Python can't check secure web connections yet; on a Mac, double-click Install Certificates in its Python folder. " + REMOTE,
    "private_directory_required": "~/.airprompter (or a folder in it) is open to every user, belongs to another user or could not be made private; it was left unchanged. " + REMOTE,
    "download_origin_not_configured": "Stored scripts and assets cannot install for this target yet. " + REMOTE,
    "platform_unvalidated": "Local installs are not validated on this operating system yet. " + REMOTE,
    "state_dir_not_writable": "~/.airprompter is not writable here (a sandbox). " + REMOTE,
}
# The token was not used for these: deliver it once more the documented way, then go remote.
STDIN_CODES = {"interactive_stdin", "stdin_empty", "stdin_timeout", "token_file_refused"}

def stdin_hint(entry, target, code=None):
    if entry == "install":
        cleanup = "Delete the file you wrote if it is still there. " if code == "token_file_refused" else ""
        return f"The token was not used. {cleanup}Retry once: write {{\"token\":\"<token>\"}} to a new file in tokenFolder with your file-write tool and run: {TOKEN_FILE_INSTALL.format(target=target)}. If that write needs approval or is outside your writable roots: {PIPE_INSTALL.format(target=target)}. Never in an interactive terminal session; on another failure, {REMOTE[0].lower() + REMOTE[1:]}"
    return f"Pass the JSON in one non-interactive command, never an interactive terminal session: {HEREDOC_REPORTS}."

class Refusal(Exception):
    """Messages are fixed codes: never include server/file/URL/token data."""

def require(ok, code="invalid_install"):
    if not ok:
        raise Refusal(code)

def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")

def digest(data):
    return hashlib.sha256(data).hexdigest()

def closed(value, required, optional=()):
    require(isinstance(value, dict) and set(required) <= value.keys() <= set(required) | set(optional))

def integer(value, maximum):
    require(type(value) is int and 0 <= value <= maximum)

def hash_value(value):
    require(isinstance(value, str) and HASH.fullmatch(value))
    return value

def no_link(path):
    info = path.lstat()
    require(not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & 0x400), "unsafe_filesystem")
    return info

def ancestry(path):
    require(path.is_absolute(), "absolute_destination_required")
    for part in reversed([path, *path.parents]):
        if os.path.lexists(part):
            info = no_link(part)
            if hasattr(os, "getuid"):
                # A private child cannot protect its pathname when another OS user can
                # rename an ancestor. Root-owned sticky temp directories are safe exceptions.
                require(info.st_uid in (0, os.getuid()), "unsafe_parent_owner")
                if stat.S_ISDIR(info.st_mode):
                    require(not info.st_mode & 0o022 or info.st_mode & stat.S_ISVTX, "unsafe_parent_permissions")

def tighten(path):
    # Self-heal (P5-3): other tooling often creates ~/.airprompter (or a level below it)
    # as 0755. Open the directory itself without following a link and change THAT
    # descriptor, so a swap between the check and the change cannot redirect it.
    # Never chmods a link, a non-directory or another user's directory.
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        raise Refusal("private_directory_required")
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid(), "private_directory_required")
        os.fchmod(descriptor, 0o700)
    finally:
        os.close(descriptor)

def private_level(path):
    # One AirPrompter-owned level: created 0700, or an own-user real directory tightened to 0700.
    if not os.path.lexists(path):
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            pass
    info = no_link(path)
    require(stat.S_ISDIR(info.st_mode), "unsafe_filesystem")
    if hasattr(os, "getuid"):
        # 0755/0775 (Ubuntu's umask 002) heal; a level every user could write is refused.
        require(info.st_uid == os.getuid() and not info.st_mode & 0o002, "private_directory_required")
        if info.st_mode & 0o077:
            tighten(path)
            info = no_link(path)
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o077, "private_directory_required")
    # Windows ACLs inherit from the user's home; cross-OS ACL proof is a release requirement.

# Write errors that mean "~/.airprompter is not writable here" (a sandbox such as Codex
# workspace-write), as opposed to an integrity refusal. Either way the run goes remote;
# the private cache is ~/.airprompter only (owner ruling), never a temp folder.
NOT_WRITABLE = {errno.EACCES, errno.EPERM, errno.EROFS}

def home_state_root():
    return Path.home() / ".airprompter"

def state_root():
    root = home_state_root()
    try:
        # Ancestors above the state root keep the strict check: never chmod the user's home.
        ancestry(root.parent)
        private_level(root)
        descriptor, name = tempfile.mkstemp(prefix=".write-", dir=root)
        os.close(descriptor)
        os.unlink(name)
    except OSError as error:
        if error.errno in NOT_WRITABLE:
            raise Refusal("state_dir_not_writable")
        raise
    return root

def state_dir(*parts):
    # Every level from the state root down is the runtime's own and is private.
    path = state_root()
    for part in parts:
        path = path / part
        private_level(path)
    ancestry(path)
    return path

def safe_paths(paths):
    require(1 <= len(paths) <= MAX_FILES and "SKILL.md" in paths)
    files, folders = set(), set()
    for path in [*paths, "install.json", "SHA256SUMS", ".airprompter"]:
        require(isinstance(path, str) and 0 < len(path.encode("utf-16-le")) // 2 <= 400)
        parts = path.split("/")
        require(len(parts) <= 8 and not re.search(r'[\\\x00-\x1f\x7f<>:"|?*]', path))
        require(all(p and p not in (".", "..") and not p.endswith((".", " ")) for p in parts))
        if path != ".airprompter":
            require(all(not p.startswith(".") for p in parts))
        require(all(not re.match(r"^(con|prn|aux|nul|com\d|lpt\d)(\.|$)", p, re.I) for p in parts))
        key = "/".join(unicodedata.normalize("NFC", p).lower() for p in parts)
        above = {"/".join(key.split("/")[:i]) for i in range(1, len(parts))}
        require(key not in files and key not in folders and not above & files, "path_collision")
        files.add(key)
        folders.update(above)

def identity(value):
    closed(value, ("workflowId", "scopeId", "explicitPrivate"), ("organizationId", "versionId"))
    require(type(value["explicitPrivate"]) is bool)
    for key, limit in (("workflowId", 160), ("scopeId", 240), ("organizationId", 160), ("versionId", 200)):
        if key in value:
            require(isinstance(value[key], str) and 0 < len(value[key].encode("utf-16-le")) // 2 <= limit)
    return value

def metadata(value):
    closed(value, ("schema", "principalKey", "identity", "fingerprint", "files"))
    require(value["schema"] == "airprompter.install.v1")
    hash_value(value["principalKey"])
    hash_value(value["fingerprint"])
    identity(value["identity"])
    require(isinstance(value["files"], list))
    for file in value["files"]:
        closed(file, ("path", "sha256", "bytes"))
        hash_value(file["sha256"])
        integer(file["bytes"], MAX_DOWNLOAD)
    safe_paths([f["path"] for f in value["files"]])
    require(sum(f["bytes"] for f in value["files"]) <= MAX_RESPONSE + MAX_DOWNLOAD)
    return value

def scope_key(meta):
    # Stable sorted identity serialization, independent of HTTP/local JSON member ordering.
    return digest(json_bytes({k: meta["identity"][k] for k in sorted(meta["identity"])}))

def report_scope_key(meta):
    # Reports from earlier versions/workflows must drain on the next call in this tenant scope.
    return digest(json_bytes({"scopeId": meta["identity"]["scopeId"], "organizationId": meta["identity"].get("organizationId")}))

def checksums(files):
    return "".join(f'{f["sha256"]}  {f["path"]}\n' for f in files).encode("utf-8")

def fingerprint(payload):
    entries = []
    for path, data in payload.items():
        if path == "SKILL.md":
            text = data.decode("utf-8")
            if text.startswith("---\n"):
                end = text.find("\n---\n", 3)
                if end >= 0:
                    text = "\n".join(line for line in text[:end + 1].split("\n") if not re.match(r"^[ \t]*airprompter_exported:", line)) + text[end + 1:]
            data = text.encode("utf-8")
        entries.append(path + "\x00" + digest(data))
    return tree_fingerprint(entries)

def tree_fingerprint(entries):
    return digest(json_bytes(sorted(entries, key=lambda entry: entry.encode("utf-16-be"))))

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Refusal("redirect_refused")

def origin(url):
    parsed = urllib.parse.urlsplit(url)
    require(parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password and parsed.port in (None, 443) and not parsed.fragment, "unsafe_origin")
    return "https://" + parsed.hostname

# The verified fallback context, once one worked in this process (later downloads reuse it).
TLS = {"context": None}

def open_url(request, context=None):
    handlers = [NoRedirect(), *([urllib.request.HTTPSHandler(context=context)] if context is not None else [])]
    return urllib.request.build_opener(*handlers).open(request, timeout=5)

def certificate_failure(error):
    return isinstance(error, ssl.SSLCertVerificationError) or isinstance(getattr(error, "reason", None), ssl.SSLCertVerificationError)

def fallback_context():
    # No new dependency: the first OS bundle that loads, else certifi only if already importable.
    # create_default_context keeps CERT_REQUIRED and hostname checking.
    for bundle in SYSTEM_CA_BUNDLES:
        if os.path.isfile(bundle):
            try:
                return ssl.create_default_context(cafile=bundle)
            except (OSError, ssl.SSLError):
                continue
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None

def open_verified(request):
    # A certificate failure happens in the TLS handshake, before any request byte is sent,
    # so one retry cannot redeem a single-use token twice. Any other failure is not retried.
    try:
        return open_url(request, TLS["context"])
    except (urllib.error.URLError, ssl.SSLError) as error:
        if not certificate_failure(error):
            raise
        require(TLS["context"] is None, "tls_certificates_unavailable")
    context = fallback_context()
    require(context is not None, "tls_certificates_unavailable")
    try:
        response = open_url(request, context)
    except (urllib.error.URLError, ssl.SSLError) as error:
        require(not certificate_failure(error), "tls_certificates_unavailable")
        raise
    TLS["context"] = context
    return response

def fetch(url, limit, body=None):
    # urllib verifies TLS by default. Redirects and compressed bodies are refused, never retried.
    origin(url)
    request = urllib.request.Request(url, data=body, headers={"Accept": "application/json" if body else "application/octet-stream", "Accept-Encoding": "identity", **({"Content-Type": "application/json"} if body else {})})
    with open_verified(request) as response:
        require(response.status == 200 and response.headers.get("Content-Encoding", "identity") == "identity", "download_refused")
        length = response.headers.get("Content-Length")
        require(length is None or (length.isdigit() and int(length) <= limit), "response_too_large")
        chunks, total, started = [], 0, time.monotonic()
        while True:
            require(time.monotonic() - started < 30, "download_timeout")
            chunk = response.read1(min(65536, limit + 1 - total))
            require(time.monotonic() - started < 30, "download_timeout")
            if not chunk:
                break
            total += len(chunk)
            require(total <= limit, "response_too_large")
            chunks.append(chunk)
        return b"".join(chunks)

def read_json(data):
    # Duplicate keys can give different manifests to different parsers; reject them.
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value)
            value[key] = item
        return value
    return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=lambda _: require(False))

def read_file(path, limit):
    ancestry(path.parent)
    info = no_link(path)
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= limit, "unsafe_filesystem")
    if hasattr(os, "getuid"):
        require(info.st_uid == os.getuid() and not info.st_mode & 0o022, "unsafe_file_permissions")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, "response_too_large")
    return data

# Owner decision 2026-11-01, final ("Tighten"): THE rule the Download Skill zip uses (the domain
# helper skillFileIsExecutable, 0755 there). SKILL_FILE_EXECUTABLE_RULE mirrors it; the parity
# test extensions/agents/shared/scripts/local-install-runtime.test.mjs checks this data and every
# case against the shared fixture packages/domain/test/skills/fixtures/skill-executable-cases.json
# (as packages/domain/test/skills/zipStore.test.ts does for the domain). The path is relative to the skill
# folder. A file's extension is the text after the last "." in its name, unless that dot is the
# name's first character (".gitkeep" and "pre-commit" have none); extensions match in any case.
# - An empty file is never executable.
# - A shell-family extension is executable anywhere.
# - Another script language is executable only by the bytes or folder rules below.
# - Any other extension (data, .md/.markdown/.txt, .bin/.exe, ...) never is.
# - No extension: only by the bytes or folder rules.
# Bytes rule: the file starts with "#!". Folder rules: the path's first folder is exactly
# scripts, or any folder is exactly hooks; they skip a name starting with "." and a README,
# LICENSE or CHANGELOG (any case, with or without one extension: the name before its last dot).
# The private install is owner-only, so an executable file is 0o700 and every other file
# (install.json and SHA256SUMS too) stays 0o600. Verification hashes bytes only, never modes,
# and read_file refuses only group/other write, so a verified or cached copy keeps both modes.
# On Windows (install.ps1 runs this same file) os.open honours only the write bit, so both
# modes create the same ordinary writable file there.
SKILL_FILE_EXECUTABLE_RULE = {
    "shellExtensions": ("sh", "bash", "zsh", "fish", "ksh", "csh", "tcsh", "command"),
    "scriptExtensions": ("py", "js", "mjs", "cjs", "ts", "mts", "cts", "rb", "pl", "php", "lua", "ps1", "swift", "r", "bats"),
    "shebang": b"#!",
    "scriptsFolder": "scripts",
    "hooksFolder": "hooks",
    # The domain's SKILL_EXECUTABLE_RULES.folderRulesSkipNamesStartingWith: only the folder rules skip these names.
    "folderRulesSkipNamesStartingWith": ".",
    "folderRulesSkipNames": ("README", "LICENSE", "CHANGELOG"),
}

def file_extension(path):
    name = path.split("/")[-1]
    dot = name.rfind(".")
    return name[dot + 1:].lower() if dot > 0 else None

def executable(path, data):
    rule = SKILL_FILE_EXECUTABLE_RULE
    if not data:
        return False
    extension = file_extension(path)
    if extension in rule["shellExtensions"]:
        return True
    if extension is not None and extension not in rule["scriptExtensions"]:
        return False
    if data[:2] == rule["shebang"]:
        return True
    *folders, name = path.split("/")
    # The name before its LAST dot, as the domain helper reads it: README.md is README, README.old.py is not.
    dot = name.rfind(".")
    stem = name[:dot] if dot > 0 else name
    if name.startswith(rule["folderRulesSkipNamesStartingWith"]) or stem.upper() in rule["folderRulesSkipNames"]:
        return False
    return folders[:1] == [rule["scriptsFolder"]] or rule["hooksFolder"] in folders

def apply_install_modes(folder, payload):
    # Review round 1 (item 22): a verified reinstall returns early, so a copy installed under an
    # earlier rule keeps that rule's modes. Set each file the installer wrote to what the rule says
    # now (0o700 or 0o600, adding or removing owner-execute), through a no-follow descriptor on the
    # user's own regular single-link file; a file already right is left untouched.
    if os.name == "nt" or not hasattr(os, "fchmod"):
        return
    for path, data in payload.items():
        wanted = 0o700 if executable(path, data) else 0o600
        target = folder / path
        ancestry(target.parent)
        descriptor = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        try:
            info = os.fstat(descriptor)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid(), "unsafe_filesystem")
            if stat.S_IMODE(info.st_mode) != wanted:
                os.fchmod(descriptor, wanted)
        finally:
            os.close(descriptor)

def write_file(path, data, mode=0o600):
    ancestry(path.parent)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), mode)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)

def install_directory(path):
    info = no_link(path)
    require(stat.S_ISDIR(info.st_mode), "unsafe_filesystem")
    if hasattr(os, "getuid"):
        # Sticky shared temp ancestors are allowed ABOVE an install, never inside it:
        # another user could add a new importable module even without replacing a file.
        require(info.st_uid in (0, os.getuid()) and not info.st_mode & 0o022, "unsafe_install_directory")


def inventory_on_disk(folder, meta, local_skill=False):
    ancestry(folder)
    require(folder.is_dir(), "install_missing")
    install_directory(folder)
    info_path = ".airprompter/install.json" if local_skill else "install.json"
    expected = {f["path"] for f in meta["files"]} | {info_path, "SHA256SUMS"}
    expected_dirs = {"/".join(p.split("/")[:i]) for p in expected for i in range(1, len(p.split("/")))}
    actual = set()
    for directory, dirs, files in os.walk(folder, followlinks=False):
        for name in [*dirs, *files]:
            target = Path(directory) / name
            info = no_link(target)
            relative = target.relative_to(folder).as_posix()
            if stat.S_ISDIR(info.st_mode):
                install_directory(target)
                require(relative in expected_dirs, "unexpected_file")
            else:
                require(relative in expected, "unexpected_file")
                actual.add(relative)
    require(actual == expected, "incomplete_install")
    require(read_file(folder / "SHA256SUMS", MAX_RESPONSE) == checksums(meta["files"]), "checksum_manifest_changed")
    payload = {}
    for file in meta["files"]:
        data = read_file(folder / file["path"], min(MAX_DOWNLOAD, file["bytes"]))
        require(len(data) == file["bytes"] and digest(data) == file["sha256"], "file_changed")
        payload[file["path"]] = data
    return payload

def verified_copy(folder, expected, principal=None, local_skill=False):
    # The receipt and the byte-verified files of one installed copy.
    hash_value(expected)
    ancestry(folder)
    info_path = ".airprompter/install.json" if local_skill else "install.json"
    meta = metadata(read_json(read_file(folder / info_path, MAX_RESPONSE)))
    require(meta["fingerprint"] == expected and (principal is None or meta["principalKey"] == principal), "install_context_changed")
    payload = inventory_on_disk(folder, meta, local_skill)
    require(fingerprint(payload) == expected, "fingerprint_changed")
    return meta, payload

def verify_folder(folder, expected, principal=None, local_skill=False):
    return verified_copy(folder, expected, principal, local_skill)[0]

@contextlib.contextmanager
def destination_lock(destination):
    # OS-owned advisory lock: a killed process releases it. Keep the file so waiters
    # never lock different inodes for the same destination after an unlink/recreate.
    lock = destination.with_name(destination.name + ".lock")
    ancestry(lock)
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    locked = False
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "unsafe_filesystem")
        if hasattr(os, "getuid"):
            require(info.st_uid == os.getuid() and not info.st_mode & 0o077, "private_file_required")
        if info.st_size == 0:
            os.write(descriptor, b"\0")
        if os.name == "nt":
            import msvcrt
            def acquire():
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            def release():
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            def acquire():
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            def release():
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        for _ in range(100):
            try:
                acquire()
                locked = True
                break
            except OSError as error:
                require(error.errno in (11, 13, 35), "locking_unavailable")
                time.sleep(0.05)
        require(locked, "install_busy")
        yield
    finally:
        if locked:
            release()
        os.close(descriptor)


def stable_identity(meta):
    return {k: v for k, v in meta["identity"].items() if k != "versionId"}


def publish(payload, meta, destination, local_skill=False, repair=False):
    ancestry(destination)
    require(destination.parent.is_dir(), "destination_parent_missing")
    with destination_lock(destination):
        if os.path.lexists(destination):
            # Repair is not permission to replace another account/workflow or an unknown folder.
            info_path = ".airprompter/install.json" if local_skill else "install.json"
            previous = metadata(read_json(read_file(destination / info_path, MAX_RESPONSE)))
            require(previous["principalKey"] == meta["principalKey"] and stable_identity(previous) == stable_identity(meta), "install_context_changed")
            try:
                existing = verify_folder(destination, previous["fingerprint"], meta["principalKey"], local_skill)
                if existing["fingerprint"] == meta["fingerprint"] and existing["identity"] == meta["identity"]:
                    apply_install_modes(destination, payload)
                    return
            except Refusal:
                pass
            require(repair, "existing_install_changed")
        stage = Path(tempfile.mkdtemp(prefix=".install-", dir=destination.parent))
        try:
            for path, data in payload.items():
                write_file(stage / path, data, 0o700 if executable(path, data) else 0o600)
            write_file(stage / (".airprompter/install.json" if local_skill else "install.json"), json_bytes(meta))
            write_file(stage / "SHA256SUMS", checksums(meta["files"]))
            verify_folder(stage, meta["fingerprint"], meta["principalKey"], local_skill)
            if os.path.lexists(destination):
                # Explicit repair preserves changed files; no recursive deletion or link following.
                no_link(destination)
                os.rename(destination, destination.with_name(".changed-" + os.urandom(12).hex()))
            os.rename(stage, destination)
        finally:
            if stage.exists():
                shutil.rmtree(stage)

def download_pin(target, download_origin=None):
    # install_required implies stored files, so a target without a pin refuses BEFORE
    # redemption (no token spent). An explicit origin must equal the pin: never widens trust.
    pin = DOWNLOAD_ORIGINS.get(target)
    require(pin is not None, "download_origin_not_configured")
    require(download_origin is None or download_origin == pin, "download_origin_mismatch")
    return pin

PRUNE_AGE_SECONDS = 24 * 3600

def mark_used(folder):
    # Prune age is LAST USE: every successful reuse or verify of a cache copy touches
    # its receipt, so a copy another session is still running is never "old".
    with contextlib.suppress(OSError):
        os.utime(folder / "install.json")

def lock_held(lock):
    # True when another open file holds the advisory lock (POSIX flock is per open file).
    import fcntl
    descriptor = os.open(lock, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        return False
    except OSError:
        return True
    finally:
        os.close(descriptor)

def prune(keep, meta, now=None):
    # H-4: after a successful install, older cached copies of THIS workflow (same
    # principal, workflow, scope and private choice; any version) are removed. Kept:
    # the new copy, the newest previous copy and anything used in the last 24 h (a run
    # in another session may still use it), other workflows, `.changed-*` preserved
    # edits, stage folders and links. An old copy that fails verification was edited:
    # it is preserved as `.changed-*`, never deleted. Lock files stay while in use (as
    # destination_lock requires); a later prune removes one only when its folder is gone
    # and nobody holds it. Never fails the install.
    if os.name == "nt" or not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
        return
    principal = keep.parent.parent
    with contextlib.suppress(OSError):
        for scope in [entry for entry in principal.iterdir() if not entry.name.startswith(".")]:
            with contextlib.suppress(OSError):
                for lock in [entry for entry in scope.iterdir() if entry.name.endswith(".lock") and HASH.fullmatch(entry.name[:-5])]:
                    with contextlib.suppress(Refusal, OSError):
                        if stat.S_ISREG(no_link(lock).st_mode) and not os.path.lexists(lock.with_name(lock.name[:-5])) and not lock_held(lock):
                            lock.unlink()
    previous = []
    with contextlib.suppress(OSError):
        for scope in [entry for entry in principal.iterdir() if not entry.name.startswith(".")]:
            with contextlib.suppress(OSError):
                for folder in [entry for entry in scope.iterdir() if HASH.fullmatch(entry.name) and entry != keep]:
                    with contextlib.suppress(Refusal, OSError, ValueError):
                        require(stat.S_ISDIR(no_link(folder).st_mode))
                        old = metadata(read_json(read_file(folder / "install.json", MAX_RESPONSE)))
                        require(old["principalKey"] == meta["principalKey"] and stable_identity(old) == stable_identity(meta))
                        previous.append((os.lstat(folder / "install.json").st_mtime, str(folder), old))
    previous.sort(reverse=True)
    cutoff = (time.time() if now is None else now) - PRUNE_AGE_SECONDS
    for installed_at, name, old in previous[1:]:
        if installed_at > cutoff:
            continue
        folder = Path(name)
        with contextlib.suppress(Refusal, OSError, ValueError):
            with destination_lock(folder):
                try:
                    verify_folder(folder, old["fingerprint"], meta["principalKey"])
                except Refusal:
                    no_link(folder)
                    os.rename(folder, folder.with_name(".changed-" + os.urandom(12).hex()))
                    continue
                no_link(folder)
                shutil.rmtree(folder)

def install(request, expected, target, download_origin=None, local_destination=None, fetcher=fetch, repair=False):
    closed(request, ("token",))
    require(isinstance(request["token"], str) and TOKEN.fullmatch(request["token"]))
    hash_value(expected)
    download_origin = download_pin(target, download_origin)
    response = read_json(fetcher(API_ORIGINS[target] + "/v1/skill-installs/redeem", MAX_RESPONSE, json_bytes(request)))
    closed(response, ("install", "sha256sums", "files", "storedFiles"))
    meta = metadata(response["install"])
    require(meta["fingerprint"] == expected, "install_context_changed")
    require(isinstance(response["files"], list) and 1 <= len(response["files"]) <= 64 and isinstance(response["storedFiles"], list) and len(response["storedFiles"]) <= 200)
    require(response["sha256sums"].encode("utf-8") == checksums(meta["files"]))
    delivered = [*response["files"], *response["storedFiles"]]
    require([{k: f[k] for k in ("path", "sha256", "bytes")} for f in delivered] == meta["files"])
    safe_paths([f["path"] for f in delivered])
    require(sum(f["bytes"] for f in response["storedFiles"]) <= MAX_DOWNLOAD)
    payload = {}
    for file in response["files"]:
        closed(file, ("path", "sha256", "bytes", "content"))
        require(isinstance(file["content"], str))
        payload[file["path"]] = file["content"].encode("utf-8")
    # Validate the whole download manifest and pins before making any download request.
    if response["storedFiles"]:
        require(download_origin is not None and origin(download_origin) == download_origin, "download_origin_not_configured")
    for file in response["storedFiles"]:
        closed(file, ("path", "sha256", "bytes", "role", "scan", "url", "expiresAt"))
        require(file["role"] in ("script", "asset") and file["scan"] in ("unscanned", "clean"), "file_scan_refused")
        require(len(file["url"]) <= 2048 and origin(file["url"]) == download_origin, "download_origin_mismatch")
        expiry = datetime.datetime.fromisoformat(file["expiresAt"].replace("Z", "+00:00"))
        require(expiry.tzinfo is not None and expiry > datetime.datetime.now(datetime.timezone.utc), "download_expired")
    parent = state_dir("workflows", meta["principalKey"], scope_key(meta))
    destination = parent / expected
    reused = None
    if os.path.lexists(destination):
        try:
            reused = verify_folder(destination, expected, meta["principalKey"])
            require(reused["identity"] == meta["identity"], "install_context_changed")
        except Refusal:
            require(repair, "existing_install_changed")
    if reused:
        payload = inventory_on_disk(destination, reused)
        meta = reused
        mark_used(destination)
    else:
        for file in response["storedFiles"]:
            payload[file["path"]] = fetcher(file["url"], file["bytes"])
        for file in meta["files"]:
            data = payload[file["path"]]
            require(len(data) == file["bytes"] and digest(data) == file["sha256"], "file_changed")
    require(fingerprint(payload) == expected, "fingerprint_changed")
    publish(payload, meta, destination, repair=repair)
    prune(destination, meta)
    if local_destination:
        publish(payload, meta, local_destination, True, repair=repair)
    # IDs/scan facts only. Never emit payload bytes, URLs, or bearer material.
    return {"status": "installed", "path": str(local_destination or destination), "principalKey": meta["principalKey"], "scopeKey": scope_key(meta), "fingerprint": expected, "storedFiles": [{k: f[k] for k in ("path", "sha256", "role", "scan")} for f in response["storedFiles"]]}

def selector_key(value):
    return re.sub(r"[\s_-]+", "-", unicodedata.normalize("NFC", value).strip().lower())

def skill_name(folder):
    # The exported SKILL.md's frontmatter `name:` line, used only to match a cached copy by name.
    text = read_file(folder / "SKILL.md", MAX_DOWNLOAD).decode("utf-8", "replace")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 3)
    for line in text[4:end if end >= 0 else 0].split("\n"):
        match = re.match(r"^name:\s*[\"']?(.*?)[\"']?\s*$", line)
        if match:
            return match.group(1)
    return None

def selector_words(key):
    return {word for word in re.split(r"[\W_]+", key) if word}

def name_matches(key, name_key):
    # The whole name (case and spacing ignored), or every word of the selector is a word of the
    # name ("wizard" finds "skill-wizard"). Several workflows matching is ambiguous: no hint.
    words = selector_words(key)
    return name_key == key or (bool(words) and words <= selector_words(name_key))

def cached(selector, principal=None, expected=None):
    # The newest verified private-cache copy of one workflow, matched by workflowId or SKILL.md
    # name, so the FIRST run call can carry installed.fingerprint. No network, no token; it writes only
    # the modes of a verified copy (the executable rule) and its last-use time.
    # `--fingerprint` (after install_required) keeps only a copy at that exact fingerprint.
    # Only byte-verified copies count (a tampered copy never does; `.changed-*` edits are skipped);
    # copies from several workflows, scopes or principals: no hint (ambiguous). `--principal-key`
    # limits it to one connection's principal. The server's fingerprint check still decides.
    require(isinstance(selector, str) and 0 < len(selector) <= 200, "invalid_arguments")
    if principal is not None:
        hash_value(principal)
    if expected is not None:
        hash_value(expected)
    key = selector_key(selector)
    root = home_state_root() / "workflows"
    found = []
    if os.path.isdir(root):
        for owner in sorted(p for p in root.iterdir() if HASH.fullmatch(p.name) and principal in (None, p.name)):
            for scope in sorted(p for p in owner.iterdir() if HASH.fullmatch(p.name)):
                for folder in sorted(p for p in scope.iterdir() if HASH.fullmatch(p.name)):
                    with contextlib.suppress(Refusal, OSError, ValueError):
                        require(stat.S_ISDIR(no_link(folder).st_mode))
                        meta = metadata(read_json(read_file(folder / "install.json", MAX_RESPONSE)))
                        # The receipt must name the folder it sits in: principal, scope and fingerprint.
                        require(meta["principalKey"] == owner.name and scope_key(meta) == scope.name and folder.name == meta["fingerprint"])
                        name = skill_name(folder)
                        if meta["identity"]["workflowId"] != selector and (name is None or not name_matches(key, selector_key(name))):
                            continue
                        # Review round 2 (item 3): after install_required, only a copy at the answer's
                        # fingerprint is a hit; an older copy of the same workflow is not (no stale loop).
                        if expected is not None and meta["fingerprint"] != expected:
                            continue
                        _, files = verified_copy(folder, meta["fingerprint"], meta["principalKey"])
                        # Round 2 (item 21): a code-mode cache hit also brings an older copy's modes to the rule.
                        # Final review (item 6): a mode change the filesystem refuses (a read-only sandbox) keeps
                        # the hit; the copy's bytes are verified, only its modes stay as they were.
                        with contextlib.suppress(OSError):
                            apply_install_modes(folder, files)
                        found.append((os.lstat(folder / "install.json").st_mtime, folder, meta, name))
    contexts = {(m["principalKey"], json_bytes(stable_identity(m))) for _, _, m, _ in found}
    if not found:
        return {"status": "none"}
    if len(contexts) > 1:
        return {"status": "ambiguous", "copies": len(contexts)}
    found.sort(key=lambda item: item[0], reverse=True)
    _, folder, meta, name = found[0]
    mark_used(folder)
    return {"status": "cached", "fingerprint": meta["fingerprint"], "path": str(folder), "workflowId": meta["identity"]["workflowId"], **({"name": name} if name else {})}

def reach(target):
    # A token-free HTTPS request to the target API before any token is minted, so a
    # machine without working TLS or network runs remotely before export_skill.
    # Any HTTP answer (even an error status or a refused redirect) proves verified TLS.
    request = urllib.request.Request(API_ORIGINS[target] + "/", headers={"Accept": "application/json", "Accept-Encoding": "identity"})
    try:
        with open_verified(request):
            pass
    except urllib.error.HTTPError as error:
        error.close()
    except Refusal as error:
        require(str(error) == "redirect_refused", str(error))
    except (urllib.error.URLError, OSError):
        raise Refusal("install_unavailable")

def probe(host, target="prod"):
    # Run only after install_required: capable means an install for THIS target can finish.
    require(host in HOST_FAMILIES, "unknown_host_family")
    require(os.name != "nt", "platform_unvalidated")  # Windows ACL/PowerShell proof is still pending.
    download_pin(target)
    reach(target)
    root = state_root()
    descriptor, name = tempfile.mkstemp(prefix=".probe-", dir=root)
    os.close(descriptor)
    Path(name).unlink()
    with destination_lock(root / "probe"):
        pass  # Probe locking support before advertising a local-capable client.
    marker = root / "host.json"
    previous = read_json(read_file(marker, 8192)) if marker.exists() else {}
    require(isinstance(previous, dict))
    previous[host] = {"runtime": "python3", "writable": True, "checkedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    temp = root / (".host-" + os.urandom(12).hex())
    try:
        write_file(temp, json_bytes(previous))
        os.replace(temp, marker)
    finally:
        if temp.exists():
            temp.unlink()
    # The private folder the host's file-write tool puts a token file in (see token_file).
    # The private folder the host's file-write tool puts a token file in (see token_file).
    return {"status": "capable", "host": host, "target": target, "tokenFolder": str(state_dir("tokens"))}

def report_facts(report):
    closed(report, ("localRunId", "workflowId", "startedAt", "finishedAt", "stepTimings", "outcome", "host"), ("runId", "fingerprint", "mode", "scriptErrors", "tokens", "steps"))
    for key in ("localRunId", "workflowId", "runId"):
        if key in report:
            require(isinstance(report[key], str) and 0 < len(report[key]) <= (160 if key == "workflowId" else 200) and report[key] == report[key].strip())
    require(all(isinstance(report[k], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", report[k]) for k in ("startedAt", "finishedAt")))
    started, finished = [datetime.datetime.fromisoformat(report[k].replace("Z", "+00:00")) for k in ("startedAt", "finishedAt")]
    require(started.tzinfo is not None and finished.tzinfo is not None and started <= finished)
    require(report["outcome"] in ("completed", "failed", "canceled") and report["host"] in REPORT_HOSTS)
    require(isinstance(report["stepTimings"], list) and len(report["stepTimings"]) <= 100)
    seen = set()
    for step in report["stepTimings"]:
        closed(step, ("stepId", "durationMs"))
        require(isinstance(step["stepId"], str) and 0 < len(step["stepId"]) <= 200 and step["stepId"] not in seen and step["stepId"] == step["stepId"].strip())
        seen.add(step["stepId"])
        integer(step["durationMs"], 86_400_000)
    if "fingerprint" in report:
        hash_value(report["fingerprint"])
    if "mode" in report:
        require(report["mode"] in ("cache", "local_skill"))
    if "scriptErrors" in report:
        require(isinstance(report["scriptErrors"], list) and len(report["scriptErrors"]) <= 50)
        for error in report["scriptErrors"]:
            # Local paths are intentionally not accepted by the helper; only exit-code facts.
            closed(error, (), ("exitCode",))
            require("exitCode" not in error or type(error["exitCode"]) is int)
    if "tokens" in report:
        closed(report["tokens"], ("source",), ("input", "output"))
        require(report["tokens"]["source"] == "host_reported")
        for key in ("input", "output"):
            if key in report["tokens"]:
                integer(report["tokens"][key], 10_000_000)
    # Extension values are server-validated; this helper does not queue open content-shaped objects.
    require("steps" not in report, "report_extensions_not_supported")
    return report

def report_queue(action, folder, expected, principal, local_skill=False, value=None):
    if action == "queue":
        # A failed run may have changed its files. Keep its facts even when byte verification now fails.
        ancestry(folder)
        meta = metadata(read_json(read_file(folder / (".airprompter/install.json" if local_skill else "install.json"), MAX_RESPONSE)))
        require(meta["fingerprint"] == expected and meta["principalKey"] == principal, "report_context_changed")
    else:
        meta = verify_folder(folder, expected, principal, local_skill)
    parent = state_dir("reports", meta["principalKey"], report_scope_key(meta))
    with destination_lock(parent / "queue"):
        if action == "queue":
            report = report_facts(value)
            require(report["workflowId"] == meta["identity"]["workflowId"] and report.get("fingerprint") == expected and report.get("mode") == ("local_skill" if local_skill else "cache"), "report_context_changed")
            path = parent / (digest(report["localRunId"].encode("utf-8")) + ".json")
            data = json_bytes(report)
            require(len(data) <= 100_000, "report_too_large")
            if path.exists():
                require(read_file(path, 100_000) == data, "report_id_conflict")
            else:
                # Never let an interrupted write become a visible report that blocks this scope.
                staged = parent / (".report-" + os.urandom(12).hex())
                try:
                    write_file(staged, data)
                    with staged.open("rb") as stream:
                        os.fsync(stream.fileno())
                    os.rename(staged, path)
                finally:
                    if staged.exists():
                        staged.unlink()
            return {"status": "queued"}
        reports = []
        for path in sorted(parent.glob("*.json")):
            report = report_facts(read_json(read_file(path, 100_000)))
            require(path.name == digest(report["localRunId"].encode("utf-8")) + ".json", "report_context_changed")
            if action == "ack":
                closed(value, ("results",))
                require(isinstance(value["results"], list) and len(value["results"]) <= 20)
                acknowledged = {r["localRunId"] for r in value["results"] if isinstance(r, dict) and (r.get("status") in ("filed", "replayed") or (r.get("status") == "rejected" and isinstance(r.get("reason"), str) and r["reason"] not in ("over_limit", "unavailable"))) and isinstance(r.get("localRunId"), str)}
                if report["localRunId"] in acknowledged:
                    path.unlink()
            elif len(reports) < 20:
                reports.append(report)
        return {"pendingRunReports": reports} if action == "pending" else {"status": "acknowledged"}

def token_file(path):
    # P4b-5 primary path: the host's file-write tool puts {"token": ...} in a new file
    # directly inside the private tokens folder, so no command line ever carries it.
    # Only the user's own regular single-link file there is read, then deleted before
    # redemption, so a failed install never leaves a bearer on disk.
    folder = state_dir("tokens")
    path = Path(os.path.abspath(path))
    require(path.parent == folder, "token_file_refused")
    try:
        info = no_link(path)
        # A FIFO or device would block or never end: only a regular file is opened at all.
        require(stat.S_ISREG(info.st_mode), "token_file_refused")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    except (Refusal, OSError):
        raise Refusal("token_file_refused")
    try:
        opened = os.fstat(descriptor)
        require(stat.S_ISREG(opened.st_mode) and (opened.st_dev, opened.st_ino) == (info.st_dev, info.st_ino), "token_file_refused")
        require(opened.st_nlink == 1 and opened.st_size <= MAX_TOKEN_REQUEST, "token_file_refused")
        if hasattr(os, "getuid"):
            require(opened.st_uid == os.getuid(), "token_file_refused")
        data = os.read(descriptor, MAX_TOKEN_REQUEST + 1)
    finally:
        os.close(descriptor)
    path.unlink()
    return data

def token_folder_entry(path):
    # The token file's path when it names an entry directly inside a real (no link),
    # own-user ~/.airprompter/tokens; None otherwise. Used for cleanup only, so it
    # never raises; both levels are lstat-checked so the unlink cannot be redirected.
    if path is None:
        return None
    root = home_state_root()
    folder = root / "tokens"
    path = Path(os.path.abspath(path))
    if path.parent != folder:
        return None
    for level in (root, folder):
        try:
            info = os.lstat(level)
        except OSError:
            return None
        if not stat.S_ISDIR(info.st_mode) or (hasattr(os, "getuid") and info.st_uid != os.getuid()):
            return None
    return path

def private_stdin(limit):
    # P4b-5: JSON (the single-use token, or report facts) arrives only through a pipe.
    # A terminal never sends EOF by itself, so a TTY is refused BEFORE any read: the
    # caller gets a code at once instead of a hang, and nothing typed is consumed.
    stream = sys.stdin
    require(stream is not None, "stdin_empty")
    require(not stream.isatty(), "interactive_stdin")
    source = stream.buffer
    try:
        descriptor = source.fileno()
    except (AttributeError, OSError, ValueError):
        descriptor = None
    if descriptor is None or os.name == "nt":
        data = source.read(limit + 1)
    else:
        # An open pipe that never closes would block forever: bound the wait for EOF.
        import select
        chunks, total, deadline = [], 0, time.monotonic() + STDIN_SECONDS
        while total <= limit:
            remaining = deadline - time.monotonic()
            require(remaining > 0 and select.select([descriptor], [], [], remaining)[0], "stdin_timeout")
            chunk = os.read(descriptor, limit + 1 - total)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        data = b"".join(chunks)
    require(data.strip(), "stdin_empty")
    return data

class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default error echoes unrecognized values, potentially a misplaced bearer.
        self.exit(2, '{"status":"unavailable","code":"invalid_arguments"}\n')

def main():
    # No abbreviations: a misplaced `--token <bearer>` must fail parsing, never become `--token-file`.
    parser = SafeArgumentParser(description="Bundled AirPrompter install/verify helper; bearer input uses a token file or stdin only.", allow_abbrev=False)
    parser.add_argument("entry", choices=("install", "verify"))
    parser.add_argument("--fingerprint")
    parser.add_argument("--folder", type=Path)
    parser.add_argument("--principal-key")
    parser.add_argument("--local-skill", action="store_true")
    parser.add_argument("--local-destination", type=Path)
    parser.add_argument("--repair", action="store_true", help="Preserve changed target beside it and reinstall verified bytes; user choice for personal changes.")
    parser.add_argument("--target", choices=API_ORIGINS, default="prod")
    parser.add_argument("--download-origin")
    parser.add_argument("--token-file")
    parser.add_argument("--probe", choices=sorted(HOST_FAMILIES))
    parser.add_argument("--reports", choices=("queue", "pending", "ack"))
    parser.add_argument("--cached")
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.entry == "verify" and args.cached is not None:
            value = cached(args.cached, args.principal_key, args.fingerprint)
        elif args.entry == "verify" and args.probe:
            value = probe(args.probe, args.target)
        elif args.entry == "install":
            # Every refusal that does not need the token comes before reading it.
            require(os.name != "nt", "platform_unvalidated")
            download_pin(args.target, args.download_origin)
            data = token_file(args.token_file) if args.token_file else private_stdin(MAX_TOKEN_REQUEST)
            require(len(data) <= MAX_TOKEN_REQUEST, "request_too_large")
            # Editors and PowerShell may prepend a UTF-8 BOM: read the JSON as utf-8-sig.
            if data.startswith(b"\xef\xbb\xbf"):
                data = data[3:]
            value = install(read_json(data), args.fingerprint, args.target, args.download_origin, args.local_destination, repair=args.repair)
        else:
            require(args.folder is not None and args.fingerprint is not None)
            if args.reports:
                require(args.principal_key is not None, "current_principal_required")
                hash_value(args.principal_key)
                data = private_stdin(100_000) if args.reports != "pending" else None
                require(data is None or len(data) <= 100_000, "report_too_large")
                value = report_queue(args.reports, args.folder, args.fingerprint, args.principal_key, args.local_skill, read_json(data) if data else None)
            else:
                meta = verify_folder(args.folder, args.fingerprint, args.principal_key, args.local_skill)
                if not args.local_skill:
                    mark_used(args.folder)
                value = {"status": "verified", "fingerprint": meta["fingerprint"]}
        print(json_bytes(value).decode("utf-8"))
    except Exception as error:
        # HTTP/JSON/OS exceptions often contain sensitive URL or file data; expose fixed outcomes only.
        code = str(error) if isinstance(error, Refusal) else "install_unavailable"
        hint = stdin_hint(args.entry, args.target, code) if code in STDIN_CODES else HINTS.get(code)
        print(json.dumps({"status": "unavailable", "code": code, **({"hint": hint} if hint else {})}))
        return 1
    finally:
        # A token file inside the tokens folder never outlives this process, on any exit path
        # (refused, failed or installed). Removing the entry never follows a link.
        leftover = token_folder_entry(getattr(args, "token_file", None)) if args.entry == "install" else None
        if leftover is not None:
            with contextlib.suppress(OSError):
                leftover.unlink()
    return 0

if __name__ == "__main__":
    sys.exit(main())
