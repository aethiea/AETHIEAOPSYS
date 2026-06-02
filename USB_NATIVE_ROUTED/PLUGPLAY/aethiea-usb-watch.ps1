# AETHIEA USB WATCHER
# Hidden host-side watcher. When AEUSB appears, launches visible cockpit.

$last = ""

while ($true) {
  $drive = Get-PSDrive -PSProvider FileSystem |
    Where-Object { Test-Path "$($_.Root)AETHIEAOPSYS\.aeth_root" } |
    Select-Object -First 1

  if ($drive) {
    $current = $drive.Name

    if ($current -ne $last) {
      $last = $current

      $cockpit = "$($drive.Root)START_AETHIEA.cmd"

      if (Test-Path $cockpit) {
        Start-Process -FilePath "cmd.exe" -ArgumentList "/k `"$cockpit`""
      }
    }
  } else {
    $last = ""
  }

  Start-Sleep -Seconds 5
}
