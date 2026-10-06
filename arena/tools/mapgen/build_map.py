"""맵 전체 생성 → .cache/map.npz + map_meta.json"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import numpy as np

import blocks as B
from layout import *
from terrain import Terrain
from paint import paint
from world import World
from prims import Builder
import temple
import bases
import altars
import lairs
import midfield
import lobby

CACHE = os.path.join(os.path.dirname(HERE), ".cache")


def generate(seed=None, theme="olympus"):
    import themes
    t0 = time.time()
    if seed is None:
        seed = themes.THEMES[theme]["seed"]
    T = Terrain(seed, theme)
    T.generate()
    w = World(SIZE, HEIGHT, SIZE, ORIGIN)
    paint(w, T)
    b = Builder(w, T, seed + 4)
    lairs.build_lairs(b)
    altars.build_altars(b)
    bases.build_bases(b)
    temple.build_temple(b)
    midfield.build_midfield(b)
    lobby.build_lobby(b)
    # 길가 나무 치우기 (길이 트이게) — 되돌린 칸은 이미 지은 맵 고치기(map/patch)에도 씀
    w.road_tree_fix = midfield.clear_road_trees(w, T)
    # 테마 (블록 바꾸기 · 얼음/용암 · 눈 · 풍경)
    themes.world_post(w, T, theme)
    # 맵 경계: 보이지 않는 벽은 명령으로 (내보내기 단계)
    w.fix_connections()
    B.check_all(w.used_states())
    print(f"[map] 생성 {time.time() - t0:.1f}s, 팔레트 {len(w.pal)}, 비공기 {int((w.vox > 0).sum())}")
    return w, T


def _cname(theme, ext):
    return os.path.join(CACHE, ("map" if theme == "olympus" else f"map_{theme}") + ext)


def save(w, T, theme="olympus"):
    os.makedirs(CACHE, exist_ok=True)
    np.savez_compressed(_cname(theme, ".npz"), vox=w.vox, height=T.Hi)
    meta = {"palette": w.pal, "markers": w.markers, "displays": w.displays, "origin": ORIGIN, "size": [SIZE, HEIGHT, SIZE], "G": G}
    with open(_cname(theme, "_meta.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


def load(theme="olympus"):
    d = np.load(_cname(theme, ".npz"))
    meta = json.load(open(_cname(theme, "_meta.json")))
    w = World(*meta["size"], tuple(meta["origin"]))
    w.vox = d["vox"]
    w.pal = meta["palette"]
    w.pid = {s: i for i, s in enumerate(w.pal)}
    w.markers = meta["markers"]
    w.displays = meta["displays"]
    return w


if __name__ == "__main__":
    th = sys.argv[1] if len(sys.argv) > 1 else "olympus"
    w, T = generate(theme=th)
    save(w, T, th)
