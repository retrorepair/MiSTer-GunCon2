# Start scan15_sweep.ps1 detached (hidden window), so the hours-long fit survives this shell.
param([string]$Seeds = '1604,1605,1606,1607,1608,1609')
$root = 'C:\Users\joelw\Mister Guncon2'
Start-Process -FilePath powershell.exe -WindowStyle Hidden `
  -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$root\scripts\scan15_sweep.ps1`"", '-Seeds', $Seeds) `
  -RedirectStandardOutput "$root\build\sweep2_stdout.txt" -RedirectStandardError "$root\build\sweep2_stderr.txt"
