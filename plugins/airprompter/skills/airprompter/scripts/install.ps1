# Bundled installer entrypoint. Python3 must already be available; never install a runtime.
$runtime = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $runtime) { Write-Output '{"status":"unavailable","code":"python3_required"}'; exit 1 }
& $runtime.Source -B (Join-Path $PSScriptRoot 'install_runtime.py') install @args
exit $LASTEXITCODE
