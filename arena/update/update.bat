@echo off
chcp 65001 > nul
cd /d "%~dp0"
rem 지난번에 받아 둔 새 update.ps1 이 있으면 교체
if exist "%~dp0update.ps1.next" move /y "%~dp0update.ps1.next" "%~dp0update.ps1" > nul
rem 항상 최신 업데이트 도구로 (실패해도 계속)
curl.exe -sfL -o "%~dp0update.ps1.new" "https://raw.githubusercontent.com/za12ra3da4-bot/minecraft/claude/wonderful-cray-expxq7/arena/update/update.ps1" && move /y "%~dp0update.ps1.new" "%~dp0update.ps1" > nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update.ps1"
pause
