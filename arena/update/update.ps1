# 왕관 쟁탈전 자동 업데이트 — 서버 폴더에서 update.bat 을 더블클릭
# GitHub 최신 버전을 받아 Skript 스크립트와 데이터팩을 덮어씁니다. (리소스팩은 주소가 항상 최신)
# 문제가 생기면 같은 폴더의 update_log.txt 를 보내주세요.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"      # 진행 막대를 끄면 다운로드가 훨씬 빠르다 (PowerShell 5)
$server = Split-Path -Parent $MyInvocation.MyCommand.Path
$log = Join-Path $server "update_log.txt"
function Say($m) { Write-Host $m; Add-Content -LiteralPath $log -Value $m -Encoding UTF8 }
function Fail($step, $err) {
    Say ""
    Say "[실패] $step"
    Say ("  " + $err.Exception.Message)
    Say "  → 이 창을 캡처하거나 update_log.txt 를 보내주세요."
    exit 1
}
Set-Content -LiteralPath $log -Value ("업데이트 " + (Get-Date)) -Encoding UTF8
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

$url = "https://github.com/za12ra3da4-bot/minecraft/archive/refs/heads/claude/wonderful-cray-expxq7.zip"
$tmp = Join-Path $env:TEMP "bg_arena_update"
$zip = Join-Path $tmp "src.zip"

# 1) 받기
try {
    if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
    New-Item -ItemType Directory $tmp | Out-Null
    Say "1/4 최신 버전 받는 중..."
    $ok = $false
    try { Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing; $ok = $true } catch { Say ("   (Invoke-WebRequest 실패, curl 로 다시) " + $_.Exception.Message) }
    if (-not $ok) { & curl.exe -sL -o $zip $url; if ($LASTEXITCODE -ne 0) { throw "curl 실패 ($LASTEXITCODE)" } }
    if (-not (Test-Path -LiteralPath $zip) -or (Get-Item -LiteralPath $zip).Length -lt 100000) { throw "받은 파일이 너무 작습니다 (인터넷 · 방화벽 확인)" }
} catch { Fail "다운로드" $_ }

# 2) 풀기 (윈도우 기본 tar 가 빠르고 안정적, 안 되면 Expand-Archive)
try {
    Say "2/4 압축 푸는 중..."
    $out = Join-Path $tmp "x"
    New-Item -ItemType Directory $out | Out-Null
    $done = $false
    try { & tar.exe -xf $zip -C $out; if ($LASTEXITCODE -eq 0) { $done = $true } } catch {}
    if (-not $done) { Expand-Archive -LiteralPath $zip -DestinationPath $out -Force }
    $root = Get-ChildItem -LiteralPath $out -Directory | Select-Object -First 1
    if (-not $root) { throw "압축 안에 폴더가 없습니다" }
    $srcSk = Join-Path $root.FullName "Skript\scripts\arena"
    $srcDp = Join-Path $root.FullName "arena\datapack\bg_arena"
    if (-not (Test-Path -LiteralPath $srcSk) -or -not (Test-Path -LiteralPath $srcDp)) { throw "받은 파일에 arena 폴더가 없습니다" }
} catch { Fail "압축 풀기" $_ }

# 3) 월드 이름 (server.properties 의 level-name)
$level = "world"
$props = Join-Path $server "server.properties"
if (Test-Path -LiteralPath $props) {
    $line = Select-String -LiteralPath $props -Pattern "^level-name=" | Select-Object -First 1
    if ($line) { $level = $line.Line.Substring(11).Trim() }
}
$skRoot = Join-Path $server "plugins\Skript\scripts"
$sk = Join-Path $skRoot "arena"
$dp = Join-Path $server "$level\datapacks\bg_arena"
if (-not (Test-Path -LiteralPath $skRoot)) { Say "[실패] $skRoot 가 없습니다. update.bat 을 서버 폴더(서버 jar 가 있는 곳)에 두세요."; exit 1 }
if (-not (Test-Path -LiteralPath (Join-Path $server "$level"))) { Say "[실패] 월드 폴더 '$level' 가 없습니다."; exit 1 }

# 4) 덮어쓰기
try {
    Say "3/4 스크립트 교체 중... ($sk)"
    if (Test-Path -LiteralPath $sk) { Remove-Item -LiteralPath $sk -Recurse -Force }
    Copy-Item -LiteralPath $srcSk -Destination $sk -Recurse -Force
    # scripts 폴더 바로 아래 잘못 복사된 같은 이름 파일 정리 (두 번 로드되면 오류)
    Get-ChildItem -LiteralPath $sk -File | ForEach-Object {
        $dup = Join-Path $skRoot $_.Name
        if (Test-Path -LiteralPath $dup) { Remove-Item -LiteralPath $dup -Force; Say "   중복 파일 삭제: $dup" }
    }
    Get-ChildItem -LiteralPath $skRoot -File -Filter "-old-*.sk" -ErrorAction SilentlyContinue | Remove-Item -Force
    try {
        $vt = Get-Content -LiteralPath (Join-Path $srcSk "a00-version.sk") -Raw -Encoding UTF8
        $vv = [regex]::Match($vt, 'ver\} to "([^"]+)"').Groups[1].Value
        if ($vv) { Say "   스크립트 버전: $vv  (게임에서 /업데이트테스트 로 실제 적용 확인)" }
    } catch {}
} catch { Fail "스크립트 교체 (서버가 파일을 잡고 있으면 서버를 끄고 다시)" $_ }
try {
    Say "4/4 데이터팩 교체 중... ($dp)"
    New-Item -ItemType Directory -Path (Split-Path $dp) -Force | Out-Null
    if (Test-Path -LiteralPath $dp) { Remove-Item -LiteralPath $dp -Recurse -Force }
    Copy-Item -LiteralPath $srcDp -Destination $dp -Recurse -Force
} catch { Fail "데이터팩 교체" $_ }

# server.properties 에 최신 리소스팩 주소 + sha1 (sha1 이 있어야 클라이언트가 새 팩을 받는다) — 서버 재시작 후 적용
try {
    $gen = Get-Content -LiteralPath (Join-Path $srcSk "a04-gen-pack.sk") -Raw -Encoding UTF8
    $pu = [regex]::Match($gen, 'url\} to "([^"]+)"').Groups[1].Value
    $ph = [regex]::Match($gen, 'sha1\} to "([0-9a-f]{40})"').Groups[1].Value
    if ($pu -and $ph -and (Test-Path -LiteralPath $props)) {
        $lines = Get-Content -LiteralPath $props -Encoding UTF8
        $esc = $pu.Replace(':', '\:').Replace('=', '\=')
        $lines = $lines | Where-Object { $_ -notmatch '^resource-pack=' -and $_ -notmatch '^resource-pack-sha1=' }
        $lines += "resource-pack=$esc"
        $lines += "resource-pack-sha1=$ph"
        [IO.File]::WriteAllLines($props, $lines)
        Say "   server.properties 리소스팩 갱신 (sha1 $($ph.Substring(0,8))...) — 서버를 재시작하면 적용"
    }
} catch { Say ("   (server.properties 갱신 실패: " + $_.Exception.Message + ")") }

# 업데이트 도구 자신도 최신으로
try {
    # update.bat 은 지금 실행 중이라 내용이 같으면 건드리지 않는다 (바뀌면 cmd 가 엉뚱한 줄을 읽음)
    $nb = Join-Path $root.FullName "arena\update\update.bat"
    $ob = Join-Path $server "update.bat"
    if (-not (Test-Path -LiteralPath $ob) -or ((Get-FileHash -LiteralPath $nb).Hash -ne (Get-FileHash -LiteralPath $ob).Hash)) {
        Copy-Item -LiteralPath $nb -Destination $ob -Force
    }
    Copy-Item -LiteralPath (Join-Path $root.FullName "arena\update\update.ps1") -Destination (Join-Path $server "update.ps1.next") -Force
} catch {}
try { Remove-Item -LiteralPath $tmp -Recurse -Force } catch {}
Say ""
Say "완료! 서버를 재시작하세요 (리소스팩 설정 적용). 재시작이 어려우면 게임에서  /sk reload all  →  /minecraft:reload  →  /리팩 @a"
Say "적용됐는지 확인: 게임에서  /업데이트테스트  (OP)"
