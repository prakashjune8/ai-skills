# Register Windows Scheduled Task for Autonomous GitHub Sync
$TaskName = "AntigravityGitHubAutoSync"
$VbsPath = "D:\AI SKILLS\launch_auto_sync_silent.vbs"

# Check if task already exists
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$VbsPath`""
# Trigger: At startup/logon and repeat every 30 minutes indefinitely
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Autonomous background GitHub synchronizer for all Antigravity projects under prakashjune8"

Write-Host "Windows Scheduled Task '$TaskName' registered successfully!" -ForegroundColor Green
