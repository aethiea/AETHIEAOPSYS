$ErrorActionPreference = "Stop"

Clear-Host
Write-Host "=== AETHIEAOPSYS HOSTLESS AUTHORITY BOOT ===" -ForegroundColor Cyan
Write-Host ""

function Find-AethRoot {
    param([string]$Start)

    $cursor = (Resolve-Path -LiteralPath $Start).Path

    while ($true) {
        if (Test-Path -LiteralPath (Join-Path $cursor ".aeth_root")) {
            return $cursor
        }

        $parent = Split-Path -Parent $cursor
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $cursor) {
            throw "NO_AETH_ROOT_FOUND_FROM: $Start"
        }

        $cursor = $parent
    }
}

$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath
$WinRoot = Find-AethRoot -Start $ScriptDir

$DriveQualifier = Split-Path -Qualifier $WinRoot
$DriveLetter = $DriveQualifier.TrimEnd(":").TrimEnd("\")
$DriveLower = $DriveLetter.ToLowerInvariant()

$DriveRoot = "$DriveLetter`:\"
$RelativeRoot = $WinRoot.Substring($DriveRoot.Length).Replace("\", "/")

if ([string]::IsNullOrWhiteSpace($RelativeRoot)) {
    $WslRoot = "/mnt/$DriveLower"
} else {
    $WslRoot = "/mnt/$DriveLower/$RelativeRoot"
}

Write-Host "Windows Root: $WinRoot"
Write-Host "Drive: $DriveLetter`:"
Write-Host "WSL Root: $WslRoot"
Write-Host ""

$Bash = @"
set -euo pipefail

echo '=== AETHIEA WSL AUTHORITY CHECK ==='
echo 'WSL_ROOT=$WslRoot'

if [ ! -d '/mnt/$DriveLower' ]; then
  echo 'WSL_MOUNT_MISSING=/mnt/$DriveLower'
  exit 11
fi

if [ ! -d '$WslRoot' ]; then
  echo 'WSL_ROOT_MISSING=$WslRoot'
  exit 12
fi

if [ ! -f '$WslRoot/.aeth_root' ]; then
  echo 'AETH_ROOT_MARKER_MISSING=$WslRoot/.aeth_root'
  exit 13
fi

cd '$WslRoot'

echo 'AETH_ROOT_MARKER_OK'
echo 'AETHIEA ROOT:' '$WslRoot'
echo

exec bash -i
"@

Write-Host "=== LAUNCHING WSL HOSTLESS ROOT ===" -ForegroundColor Green
wsl.exe -e bash -lc $Bash

Write-Host ""
Write-Host "=== AETHIEA BOOT HOLD ==="
Read-Host "Press Enter to close when finished"
