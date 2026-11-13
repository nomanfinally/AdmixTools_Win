@echo off
setlocal DisableDelayedExpansion
set "taskPowerShell=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if defined PROCESSOR_ARCHITEW6432 set "taskPowerShell=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%taskPowerShell%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-install-windows.ps1" %*
set "taskExit=%ERRORLEVEL%"
if not "%taskExit%"=="0" echo Build/install failed. Read the error above before retrying.
if "%~1"=="" pause
exit /b %taskExit%
