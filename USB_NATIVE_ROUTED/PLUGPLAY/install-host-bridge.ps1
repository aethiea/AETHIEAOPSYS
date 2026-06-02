# AETHIEA HOST BRIDGE INSTALLER

$ErrorActionPreference = "Stop"

$installDir = "$env:LOCALAPPDATA\AETHIEA"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

$drive = Get-PSDrive -PSProvider FileSystem |
  Where-Object { Test-Path "$($_.Root)AETHIEAOPSYS\.aeth_root" } |
  Select-Object -First 1

if (-not $drive) {
  Write-Host "AETHIEAOPSYS body not found. Run this from the AEUSB host."
  exit 1
}

$source = "$($drive.Root)AETHIEAOPSYS\USB_NATIVE_ROUTED\PLUGPLAY\aethiea-usb-watch.ps1"
$target = "$installDir\aethiea-usb-watch.ps1"

Copy-Item $source $target -Force

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$target`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "AETHIEA USB PlugPlay Watcher" -Action $action -Trigger $trigger -Settings $settings -Description "Watches for AEUSB and launches AETHIEAOPSYS." -Force | Out-Null

Write-Host "AETHIEA USB PlugPlay Watcher installed."
Write-Host "Restart or log out/in once. After that, plugging AEUSB wakes the route."
