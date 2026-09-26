#!/bin/sh
# 왕관 쟁탈전 자동 업데이트 (리눅스 서버) — 서버 폴더에서 ./update.sh
set -e
cd "$(dirname "$0")"
URL="https://github.com/za12ra3da4-bot/minecraft/archive/refs/heads/claude/wonderful-cray-expxq7.zip"
LEVEL=$(grep '^level-name=' server.properties 2>/dev/null | cut -d= -f2)
LEVEL=${LEVEL:-world}
TMP=$(mktemp -d)
curl -sL "$URL" -o "$TMP/src.zip"
unzip -q "$TMP/src.zip" -d "$TMP"
ROOT=$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)
rm -rf plugins/Skript/scripts/arena "$LEVEL/datapacks/bg_arena"
cp -r "$ROOT/Skript/scripts/arena" plugins/Skript/scripts/arena
# scripts 바로 아래 중복 파일 정리 (두 번 로드 방지)
for f in plugins/Skript/scripts/arena/*.sk; do rm -f "plugins/Skript/scripts/$(basename "$f")"; done
cp -r "$ROOT/arena/datapack/bg_arena" "$LEVEL/datapacks/bg_arena"
rm -rf "$TMP"
echo "완료! 게임에서 /sk reload all 그리고 /reload (또는 서버 재시작)"
