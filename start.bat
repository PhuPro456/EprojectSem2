@echo off
rem Double-click this file to start the BookStore Pro website.
rem Add options after the command, e.g.:  start.bat --sqlite
cd /d "%~dp0"
python run.py %*
if errorlevel 1 pause
