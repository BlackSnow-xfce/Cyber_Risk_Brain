[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$orchestrationRoot = "D:\CyberRiskBrain-orchestration-execution"
$productRoot = "D:\CyberRiskBrain"
$architectRoot = "D:\CyberRiskBrain-architect-contracts"
$python = "D:\CyberRiskBrain\venv\Scripts\python.exe"
$productBranch = "aidp/task-0111-live-acceptance"
$contractBranch = "aidp/architect-contracts"
$runtimeRoot = Join-Path $env:LOCALAPPDATA "PredatorAI\AIDP"
$logRoot = Join-Path $runtimeRoot "logs"

$Host.UI.RawUI.WindowTitle = "PredatorAI AIDP Visible Autonomous Watcher"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "AIDP Python executable is unavailable: $python"
}
if (-not (Test-Path -LiteralPath (Join-Path $orchestrationRoot "aidp_orchestration\__main__.py") -PathType Leaf)) {
    throw "Authoritative AIDP orchestration checkout is unavailable: $orchestrationRoot"
}

New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$transcript = Join-Path $logRoot ("visible-watcher-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
$activityLog = Join-Path $logRoot "visible-watcher-activity.jsonl"
Start-Transcript -LiteralPath $transcript -Append | Out-Null

try {
    Set-Location -LiteralPath $orchestrationRoot
    Write-Host "PredatorAI AIDP VISIBLE AUTONOMOUS WATCHER" -ForegroundColor Cyan
    Write-Host "Orchestration: $orchestrationRoot"
    Write-Host "Product:       $productRoot"
    Write-Host "Contracts:     $architectRoot [$contractBranch]"
    Write-Host "Lifecycle:     autonomous Codex + visible Architect review"
    Write-Host "Product gate:  watcher remains active and stops advancement at Product Owner acceptance"
    Write-Host "Transcript:    $transcript"
    Write-Host "Activity log:  $activityLog"

    while ($true) {
        Write-Host ("[{0}] Starting authoritative watcher" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz")) -ForegroundColor Green
        $savedErrorActionPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = "Continue"
            & $python -u -m aidp_orchestration `
                --watch `
                --root $productRoot `
                --watch-interval 10 `
                --timeout 14400 `
                --architect-contract-branch $contractBranch `
                --autonomous-architect `
                --product-branch $productBranch `
                --infrastructure-root $orchestrationRoot `
                --architect-contract-root $architectRoot 2>&1 |
                Tee-Object -FilePath $activityLog -Append
            $exitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $savedErrorActionPreference
        }
        Write-Host ("[{0}] Watcher exited with code {1}; restarting in 10 seconds" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"), $exitCode) -ForegroundColor Red
        Start-Sleep -Seconds 10
    }
}
finally {
    Stop-Transcript | Out-Null
}
