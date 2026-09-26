"""전체 빌드: python3 build.py [--no-map] [--no-render]

 출력
   arena/resourcepack/bg_arena_pack.zip       리소스팩
   arena/datapack/bg_arena/                   데이터팩 (world/datapacks 에 복사)
   Skript/scripts/arena/a90-generated-*.sk    Skript 데이터 (글리프 · 맵 좌표 · 보스 애니메이션)
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "rp"))
sys.path.insert(0, os.path.join(HERE, "mapgen"))

import dp
from pack import Pack
import hud_build
import hud as H
import telegraphs
import bossgen
import decor
import weapons_w as weapons
import pixel_art
import weapons_legend
import decor2d
import decor_w
import skgen
import portraits

OUT_RP = os.path.join(ROOT, "arena", "resourcepack", "bg_arena_pack.zip")
OUT_RP_DIR = os.path.join(HERE, ".cache", "rp_folder")
OUT_DP = os.path.join(ROOT, "arena", "datapack", "bg_arena")
OUT_SK = os.path.join(ROOT, "Skript", "scripts", "arena")


OLYMPUS = os.path.join(ROOT, "resourcepack", "olympus_pack.zip")


def merge_olympus(zpath):
    """기존 게임 팩(olympus_pack, 네임스페이스 oly)을 한 팩으로 합침 — 서버는 팩을 하나만 보낼 수 있다"""
    import zipfile
    if not os.path.exists(OLYMPUS):
        return
    with zipfile.ZipFile(zpath) as z:
        have = set(z.namelist())
    with zipfile.ZipFile(OLYMPUS) as src, zipfile.ZipFile(zpath, "a", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            if info.is_dir() or info.filename == "pack.mcmeta" or info.filename in have:
                continue
            dst.writestr(info.filename, src.read(info.filename))


def main(args):
    t0 = time.time()
    import shutil
    if os.path.exists(OUT_DP):
        shutil.rmtree(OUT_DP)
    dp.core_functions(OUT_DP)
    # 맵
    import build_map
    if "--no-map" in args and os.path.exists(os.path.join(HERE, ".cache", "map.npz")):
        world = build_map.load()
    else:
        world, T = build_map.generate()
        build_map.save(world, T)
    ncmd, nparts = dp.map_functions(OUT_DP, world)
    ndeco = dp.decor_functions(OUT_DP, world)
    print(f"[dp] 맵 명령 {ncmd} ({nparts} 단계), 장식 {ndeco}")
    # 리소스팩
    pack = Pack("bg")
    # 보스 (초상화 먼저)
    portraits.render_all()
    bmeta = bossgen.export(pack, os.path.join(OUT_DP, "data", "bg", "function"))
    font = hud_build.build(pack)
    telegraphs.export(pack)
    decor.export(pack)
    decor_w.export(pack)
    pixel_art.export(pack)
    weapons_legend.export(pack)
    n = pack.write(OUT_RP_DIR, OUT_RP, "왕관 쟁탈전 + 올림포스 통합 팩")
    merge_olympus(OUT_RP)
    print(f"[rp] 파일 {n}개 → {OUT_RP} ({os.path.getsize(OUT_RP) // 1024} KB)")
    # Skript 데이터
    os.makedirs(OUT_SK, exist_ok=True)
    skgen.write_hud(os.path.join(OUT_SK, "a01-gen-hud.sk"), font)
    skgen.write_map(os.path.join(OUT_SK, "a02-gen-map.sk"), world)
    skgen.write_boss(os.path.join(OUT_SK, "a03-gen-boss.sk"), bmeta)
    # 리소스팩 파일 이름 검사: 마크는 [a-z0-9_.-/] 만 허용 (하나라도 틀리면 그 폰트/모델 파일 전체가 무시됨)
    import re as _re, zipfile as _zf
    _bad = [n for n in _zf.ZipFile(OUT_RP).namelist()
            if n.startswith("assets/") and not _re.fullmatch(r"assets/[a-z0-9_.-]+/[a-z0-9_./-]+", n)]
    for _fn in [n for n in _zf.ZipFile(OUT_RP).namelist() if n.endswith(".json") and "/font/" in n]:
        for _p in json.loads(_zf.ZipFile(OUT_RP).read(_fn)).get("providers", []):
            if "file" in _p and not _re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", _p["file"]):
                _bad.append(_fn + " → " + _p["file"])
    if _bad:
        raise SystemExit("[rp] 잘못된 파일 이름: " + ", ".join(_bad[:10]))
    # 리소스팩 주소 + sha1 → 접속할 때 서버가 최신 팩을 직접 보낸다 (sha1 이 없으면 클라이언트가 옛 팩을 계속 씀)
    import hashlib
    h = hashlib.sha1(open(OUT_RP, "rb").read()).hexdigest()
    url = f"https://raw.githubusercontent.com/za12ra3da4-bot/minecraft/claude/wonderful-cray-expxq7/arena/resourcepack/bg_arena_pack.zip?v={h[:12]}"
    with open(os.path.join(OUT_SK, "a04-gen-pack.sk"), "w", encoding="utf-8") as f:
        f.write("# 자동 생성 — 리소스팩 주소와 sha1 (arena/tools/build.py)\n"
                f'on load:\n    set {{-bg::pack::url}} to "{url}"\n    set {{-bg::pack::sha1}} to "{h}"\n')
    print(f"[rp] sha1 {h}")
    print(f"[done] {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
