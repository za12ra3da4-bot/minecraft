"""맵만 다시 만들기 (리소스팩 · 보스는 그대로): python3 build_maps.py [olympus] [frost] [volcano]
   → 데이터팩 bg:map/* (올림포스) · bg:maps/<id>/* + Skript a02-gen-map*.sk
   build.py 는 전체 (리소스팩 포함) — 맵만 바꿀 때는 이것이 빠르다"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "rp"), os.path.join(HERE, "mapgen")]

import dp
import skgen
import build_map
import escape

OUT_DP = os.path.join(os.path.dirname(HERE), "datapack", "bg_arena")
OUT_SK = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Skript", "scripts", "arena")


def sk_name(mid):
    return "a02-gen-map.sk" if mid == "olympus" else f"a02-gen-map-{mid}.sk"


def build_one(mid):
    prefix, run_id = dp.MAPS[mid]
    world, T = build_map.generate(theme=mid)
    build_map.save(world, T, mid)
    seeds = [m["pos"] for n, m in world.markers.items() if n.startswith("base_") and "_spawn_" in n]
    fixes = escape.fix(world, seeds)
    F = os.path.join(OUT_DP, "data", "bg", "function", *prefix.split("/"))
    if os.path.exists(os.path.join(F, "build")):
        shutil.rmtree(os.path.join(F, "build"))
    ncmd, nparts = dp.map_functions(OUT_DP, world, prefix=prefix, run_id=run_id)
    ndeco = dp.decor_functions(OUT_DP, world, fixes, prefix=prefix)
    skgen.write_map(os.path.join(OUT_SK, sk_name(mid)), world, mid)
    print(f"[{mid}] 맵 명령 {ncmd} ({nparts} 단계), 장식 {ndeco} → bg:{prefix}/*")
    return world


def patch_tick():
    """bg:tick 에 맵마다 건설 진행 줄이 있게 (core_functions 와 같은 줄)"""
    p = os.path.join(OUT_DP, "data", "bg", "function", "tick.mcfunction")
    L = [l for l in open(p, encoding="utf-8").read().split("\n") if l and "bg_build matches" not in l]
    L += [f"execute if score #run bg_build matches {rid} run function bg:{fn}/build/step with storage bg:map origin" for fn, rid in dp.MAPS.values()]
    open(p, "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    ids = sys.argv[1:] or list(dp.MAPS)
    for mid in ids:
        build_one(mid)
    patch_tick()
