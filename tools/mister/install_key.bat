@echo off
rem One password entry: adds this PC's ssh key (the PUBLIC key, in build\install_key.sh) to the MiSTer's /root/.ssh/authorized_keys, so that later
rem connections from this PC need no password.
cd /d "%~dp0\..\.."
type build\install_key.sh | ssh -o StrictHostKeyChecking=accept-new root@192.168.1.204 "tr -d '\r' | sh"
echo.
echo Finished (exit code %errorlevel%). Press any key to close.
pause >nul
