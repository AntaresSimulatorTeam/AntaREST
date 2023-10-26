@echo off

echo %*
set "exit_status=%errorlevel%"
echo exit %exit_status%
exit /B %exit_status%
