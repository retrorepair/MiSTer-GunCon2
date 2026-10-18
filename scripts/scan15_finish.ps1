# Wait for a running quartus_fit (the sweep's seed), then, if it fitted, assemble, time it and save the rbf; if it failed, stop and HOLD
# (no further seeds). Used when the sweep script itself was stopped so a failed fit does not roll on to the next seed unattended.
#
#   powershell -ExecutionPolicy Bypass -File scripts\scan15_finish.ps1 -FitPid 221476 -Seed 1604
param(
  [Parameter(Mandatory)][int]$FitPid,
  [Parameter(Mandatory)][int]$Seed,
  [string]$Dir = 'C:\Users\joelw\Mister Guncon2\build\model2_scan15'
)
$q   = 'C:\intelFPGA_lite\17.0\quartus\bin64'
$out = Join-Path $Dir 'output_files'
$res = Join-Path (Split-Path $Dir) 'scan15_sweep.txt'
function Log($m) { Add-Content -Path $res -Value "$(Get-Date -Format 'HH:mm:ss') $m" }

Log "finish: waiting for fitter pid $FitPid (seed $Seed); a failed fit is held, not retried"
try { Wait-Process -Id $FitPid -ErrorAction Stop } catch { }
$sum    = Get-Content "$out\Model2.fit.summary" -ErrorAction SilentlyContinue
$status = ($sum | Select-String 'Fitter Status').Line
$alm    = ($sum | Select-String 'Logic utilization').Line
Log "seed ${Seed}: $status | $alm"
if ($status -match 'Successful') {
  Push-Location $Dir
  & "$q\quartus_asm.exe" Model2 *> (Join-Path (Split-Path $Dir) "sweep_asm_$Seed.log")
  & "$q\quartus_sta.exe" Model2 *> (Join-Path (Split-Path $Dir) "sweep_sta_$Seed.log")
  Pop-Location
  Log "seed ${Seed}: assembled and timed; summary follows"
  if (Test-Path "$out\Model2.sta.summary") { Get-Content "$out\Model2.sta.summary" | Select-String 'Type|Slack' | ForEach-Object { Add-Content $res $_.Line } }
  if (Test-Path "$out\Model2.rbf") { Copy-Item "$out\Model2.rbf" (Join-Path (Split-Path $Dir) "Model2_scan15_s$Seed.rbf") -Force; Log "seed ${Seed}: rbf saved" }
} else {
  Log "seed ${Seed}: did not fit; HOLDING as instructed (nothing further started)"
  $err = Get-Content (Join-Path (Split-Path $Dir) "sweep_fit_$Seed.log") -ErrorAction SilentlyContinue | Select-String 'Error \(' | Select-Object -First 3
  foreach ($e in $err) { Add-Content $res ("    " + $e.Line.Substring(0, [Math]::Min(200, $e.Line.Length))) }
}
Log "finish: done"
