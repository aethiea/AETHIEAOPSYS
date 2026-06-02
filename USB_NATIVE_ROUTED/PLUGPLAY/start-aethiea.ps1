# AETHIEA USB PLUGPLAY STARTER

$ErrorActionPreference = "SilentlyContinue"

$drive = Get-PSDrive -PSProvider FileSystem |
  Where-Object { Test-Path "$($_.Root)AETHIEAOPSYS\.aeth_root" } |
  Select-Object -First 1

if (-not $drive) {
  Write-Host "AETHIEAOPSYS body not found. Plug AEUSB in and try again."
  exit 1
}

$letter = $drive.Name
$lower = $letter.ToLower()
$linuxMount = "/mnt/$lower"
$linuxRoot = "$linuxMount/AETHIEAOPSYS"

Write-Host "AETHIEA AEUSB found at $letter`:"
Write-Host "Mounting into WSL at $linuxMount"

wsl.exe -d ubuntu -u root -- bash -lc "mkdir -p $linuxMount; mountpoint -q $linuxMount || mount -t drvfs $letter`: $linuxMount; true"

Write-Host "Launching AETHIEAOPSYS..."
wsl.exe -d ubuntu -u d_ny5u5 --cd $linuxRoot
