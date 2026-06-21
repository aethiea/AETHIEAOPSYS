@echo off
setlocal

set "AETH_ROOT=%~dp0"
set "AETH_ROOT=%AETH_ROOT:~0,-1%"
set "AETH_SCRIPT=%AETH_ROOT%\USB_NATIVE_ROUTED\PLUGPLAY\start-aethiea.ps1"

echo === AETHIEA ROOT COCKPIT ===
echo BODY ROOT: %AETH_ROOT%
echo SCRIPT: %AETH_SCRIPT%

if not exist "%AETH_ROOT%\.aeth_root" (
  echo FAIL: .aeth_root not found at %AETH_ROOT%
  exit /b 1
)

if not exist "%AETH_SCRIPT%" (
  echo FAIL: launcher not found: %AETH_SCRIPT%
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%AETH_SCRIPT%"
