param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigPath
)

$ErrorActionPreference = 'Stop'

$resolved = (Resolve-Path -LiteralPath $ConfigPath).Path
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Push-Location $root
try {
    & python -m aidp_orchestration.product_owner_service --config $resolved
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
