# 왕관 쟁탈전 자동 업데이트 — 서버 폴더에서 실행 (update.bat 을 더블클릭)
# GitHub 최신 버전을 받아 Skript 스크립트와 데이터팩을 덮어씁니다. 리소스팩은 주소가 항상 최신이라 따로 할 일 없음.
$ErrorActionPreference = "Stop"
$server = Split-Path -Parent $MyInvocation.MyCommand.Path
$url = "https://github.com/za12ra3da4-bot/minecraft/archive/refs/heads/claude/wonderful-cray-expxq7.zip"
$tmp = Join-Path $env:TEMP "bg_arena_update"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory $tmp | Out-Null
Write-Host "최신 버전 받는 중..."
Invoke-WebRequest -Uri $url -OutFile (Join-Path $tmp "src.zip")
Expand-Archive (Join-Path $tmp "src.zip") -DestinationPath $tmp
$root = Get-ChildItem $tmp -Directory | Select-Object -First 1
# 월드 이름 (server.properties 의 level-name)
$level = "world"
$props = Join-Path $server "server.properties"
if (Test-Path $props) {
    $line = Select-String -Path $props -Pattern "^level-name=" | Select-Object -First 1
    if ($line) { $level = $line.Line.Substring(11) }
}
$sk = Join-Path $server "plugins\Skript\scripts\arena"
$dp = Join-Path $server "$level\datapacks\bg_arena"
if (Test-Path $sk) { Remove-Item $sk -Recurse -Force }
if (Test-Path $dp) { Remove-Item $dp -Recurse -Force }
Copy-Item (Join-Path $root.FullName "Skript\scripts\arena") $sk -Recurse
Copy-Item (Join-Path $root.FullName "arena\datapack\bg_arena") $dp -Recurse
Remove-Item $tmp -Recurse -Force
Write-Host ""
Write-Host "완료! 게임에서  /sk reload all  그리고  /reload  (또는 서버 재시작)"
