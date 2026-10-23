@echo off
rem Pulls the gun logs and state off the MiSTer over ssh (it asks for the root password once) into build\mister_logs.tgz.
rem It only reads from the MiSTer (tools\mister\collect_logs.sh).
cd /d "%~dp0\..\.."
ssh -o StrictHostKeyChecking=accept-new root@192.168.1.204 "tr -d '\r' | sh" < tools\mister\collect_logs.sh > build\mister_logs.tgz
echo.
echo Finished (exit code %errorlevel%). Press any key to close.
pause >nul
