# Fit the Model 2 "Filled" build under several fitter seeds, one after another, and stop at the first that fits.
#
# Why: the core fills 99% of the chip, so whether a build fits (and meets timing) is largely down to the fitter seed
# (the author's own notes: "it's normal for some seeds to miss"). Fits are sequential here because one peaks near 5 GB.
# Synthesis is done once; each seed then only re-runs the fitter. The fitter often segfaults ON EXIT after succeeding, so success is
# read from the fit summary, not the exit code, and assembly and timing analysis are run stage by stage.
#
#   powershell -ExecutionPolicy Bypass -File scripts\scan15_sweep.ps1 -Seeds 1604,1605,1606
param(
  [string[]]$Seeds = @('1604', '1605', '1606', '1607', '1608', '1609'),   # a comma list also works through -File
  [string]$Src  = 'C:\Users\joelw\Mister Guncon2\forks\sega-model2-mister',
  [string]$Dir  = 'C:\Users\joelw\Mister Guncon2\build\model2_scan15',
  [switch]$SkipMap,
  [switch]$MapOnly      # synthesis only, then print its area estimate and stop (no fitting)
)
$Seeds = @($Seeds | ForEach-Object { $_ -split ',' } | ForEach-Object { [int]$_ })
$q   = 'C:\intelFPGA_lite\17.0\quartus\bin64'
$out = Join-Path $Dir 'output_files'
$res = Join-Path (Split-Path $Dir) 'scan15_sweep.txt'
function Log($m) { $l = "$(Get-Date -Format 'HH:mm:ss') $m"; Add-Content -Path $res -Value $l; Write-Output $l }

Log "sweep start, seeds: $($Seeds -join ',')"
Copy-Item "$Src\Model2.sv", "$Src\Model2.qsf" $Dir -Force
Copy-Item "$Src\rtl\video\m2_scan15.sv" "$Dir\rtl\video\" -Force

if (-not $SkipMap) {
  Remove-Item "$Dir\db", "$Dir\incremental_db", $out -Recurse -Force -ErrorAction SilentlyContinue
  Push-Location $Dir
  & "$q\quartus_map.exe" Model2 *> (Join-Path (Split-Path $Dir) 'sweep_map.log')
  Pop-Location
  $mapok = Select-String -Path "$out\Model2.map.summary" -Pattern 'Successful' -Quiet
  Log "synthesis: $(if ($mapok) {'ok'} else {'FAILED'})"
  if (-not $mapok) { exit 1 }
}

if ($MapOnly) {
  $rpt = Get-Content "$out\Model2.map.rpt" -ErrorAction SilentlyContinue
  foreach ($k in 'Estimate of Logic utilization', 'Dedicated logic registers', 'Total block memory bits', 'Total DSP Blocks') {
    $l = ($rpt | Select-String -SimpleMatch $k | Select-Object -First 1).Line
    if ($l) { Log ("map: " + ($l -replace '\s+', ' ')) }
  }
  Log "map only: done"
  exit 0
}

foreach ($seed in $Seeds) {
  Log "seed ${seed}: fitting"
  Push-Location $Dir
  & "$q\quartus_fit.exe" Model2 "--seed=$seed" *> (Join-Path (Split-Path $Dir) "sweep_fit_$seed.log")
  Pop-Location
  $sum = Get-Content "$out\Model2.fit.summary" -ErrorAction SilentlyContinue
  $status = ($sum | Select-String 'Fitter Status').Line
  $alm = ($sum | Select-String 'Logic utilization').Line
  Log "seed ${seed}: $status | $alm"
  if ($status -match 'Successful') {
    Push-Location $Dir
    & "$q\quartus_asm.exe" Model2 *> (Join-Path (Split-Path $Dir) "sweep_asm_$seed.log")
    & "$q\quartus_sta.exe" Model2 *> (Join-Path (Split-Path $Dir) "sweep_sta_$seed.log")
    Pop-Location
    Log "seed ${seed}: assembled and timed; summary follows"
    if (Test-Path "$out\Model2.sta.summary") { Get-Content "$out\Model2.sta.summary" | Select-String 'Type|Slack' | ForEach-Object { Add-Content $res $_.Line } }
    if (Test-Path "$out\Model2.rbf") { Copy-Item "$out\Model2.rbf" (Join-Path (Split-Path $Dir) "Model2_scan15_s$seed.rbf") -Force; Log "seed ${seed}: rbf saved" }
    break
  }
}
Log "sweep done"
