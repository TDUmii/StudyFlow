@echo off
cd /d "%~dp0"
python -m teaching.main
if errorlevel 1 pause
