@echo off
setlocal
cd /d "%~dp0"
py panel.pyw
if errorlevel 1 pause
