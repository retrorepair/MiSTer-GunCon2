@echo off
rem Sends the calibration core, the app (the trace build or the clean one) and tools\mister\deploy_guncal.sh to the MiSTer over ssh (it asks for the
rem root password once) and runs the script there.
rem usage: tools\mister\deploy_guncal.bat <md5 of GunCal.rbf> <md5 of the app> <md5 of the clean app>
rem The files are taken from build\: GunCal.rbf, MiSTer_tracker_debug (installed) and MiSTer_tracker (kept as MiSTer.clean).
cd /d "%~dp0\..\.."
copy /y tools\mister\deploy_guncal.sh build\deploy_guncal.sh >nul
copy /y build\MiSTer_tracker_debug build\MiSTer.app >nul
copy /y build\MiSTer_tracker build\MiSTer.clean >nul
tar cf - -C build GunCal.rbf MiSTer.app MiSTer.clean deploy_guncal.sh | ssh -o StrictHostKeyChecking=accept-new root@192.168.1.204 "cd /tmp && tar xf - && tr -d '\r' < /tmp/deploy_guncal.sh > /tmp/d.sh && sh /tmp/d.sh %1 %2 %3"
echo.
echo Finished (exit code %errorlevel%). Press any key to close.
pause >nul
