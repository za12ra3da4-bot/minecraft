@echo off
chcp 65001 > nul
cd /d "%~dp0"
rem Whole script is one block: cmd reads it all before running, so update.ps1 may replace this file safely.
(
  if exist "%~dp0update.ps1.next" move /y "%~dp0update.ps1.next" "%~dp0update.ps1" > nul
  curl.exe -sfL -o "%~dp0update.ps1.new" "https://raw.githubusercontent.com/za12ra3da4-bot/minecraft/claude/wonderful-cray-expxq7/arena/update/update.ps1" && move /y "%~dp0update.ps1.new" "%~dp0update.ps1" > nul
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update.ps1"
  pause
  exit /b
)
