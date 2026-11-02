# Bundled verifier/report-queue entrypoint. Reports leave the host only through MCP.
$runtime = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $runtime) { Write-Output '{"status":"unavailable","code":"python3_required"}'; exit 1 }
& $runtime.Source -B (Join-Path $PSScriptRoot 'install_runtime.py') verify @args
exit $LASTEXITCODE
