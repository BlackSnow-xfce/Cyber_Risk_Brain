param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigPath
)

$ErrorActionPreference = 'Stop'

$resolved = (Resolve-Path $ConfigPath).Path
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Push-Location $root
try {
    python -c "from pathlib import Path; from aidp_orchestration.product_owner_service import build_product_owner_confirmation_runtime; runtime = build_product_owner_confirmation_runtime(Path(r'$resolved')); print('PRODUCT_OWNER_CONFIRMATION_READY', flush=True); runtime.serve_forever()"
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
