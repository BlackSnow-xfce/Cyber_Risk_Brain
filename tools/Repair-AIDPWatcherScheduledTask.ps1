[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$taskName = "PredatorAI AIDP Watcher"
$orchestrationRoot = "D:\CyberRiskBrain-orchestration-execution"
$launcher = Join-Path $orchestrationRoot "tools\Start-AIDPVisibleWatcher.ps1"
$powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw "Visible AIDP launcher is unavailable: $launcher"
}

$action = New-ScheduledTaskAction `
    -Execute $powershell `
    -Argument ('-NoLogo -NoProfile -ExecutionPolicy Bypass -WindowStyle Normal -NoExit -File "{0}"' -f $launcher) `
    -WorkingDirectory $orchestrationRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -DontStopOnIdleEnd `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName $taskName `
    -Description "Visible autonomous PredatorAI AIDP lifecycle watcher" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null

Export-ScheduledTask -TaskName $taskName
