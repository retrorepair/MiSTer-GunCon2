# Start scan15_sweep.ps1 detached (hidden window), so the hours-long fit survives this shell.
#   launch_scan15_sweep.ps1                  synthesis, then the fitter per seed
#   launch_scan15_sweep.ps1 -MapOnly         synthesis only, with its area estimate in build\scan15_sweep.txt
#   launch_scan15_sweep.ps1 -Seeds 1604 -SkipMap   fit one seed on the synthesis already done
param([string]$Seeds = '1604,1605,1606,1607,1608,1609', [switch]$MapOnly, [switch]$SkipMap)
$root = 'C:\Users\joelw\Mister Guncon2'
$argv = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$root\scripts\scan15_sweep.ps1`"", '-Seeds', $Seeds)
if ($MapOnly) { $argv += '-MapOnly' }
if ($SkipMap) { $argv += '-SkipMap' }
Start-Process -FilePath powershell.exe -WindowStyle Hidden -ArgumentList $argv `
  -RedirectStandardOutput "$root\build\sweep2_stdout.txt" -RedirectStandardError "$root\build\sweep2_stderr.txt"
