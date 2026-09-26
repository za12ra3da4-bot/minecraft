"""1시즌 월드 전체를 1/4 크기 블록 월드로 쌓아 3D 렌더 → rpg/preview/world3d_*.png

 world_mc.py 가 만든 높이 · 지면 · 나무 · 건물 기록(.world_mc.npz)을 쓴다.
 1복셀 = 실제 4블록.  렌더러는 전장 맵 미리보기와 같은 것 (arena/tools/render.py)
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "arena", "tools"))
import render as R

OUT = os.path.join(HERE, "..", "preview")
SC = 4
N = 2000
H0 = -1000
SEA = 62

STATE = {
    "grass": "grass_block", "grass_dry": "grass_block", "grass_dark": "grass_block", "sand": "sand",
    "red_sand": "red_sand", "gravel": "gravel", "stone": "stone", "andesite": "andesite", "dirt": "dirt",
    "coarse": "coarse_dirt", "podzol": "podzol", "snow": "snow_block", "ice": "packed_ice",
    "tc_orange": "orange_terracotta", "tc_white": "white_terracotta", "tc_brown": "brown_terracotta", "tc": "terracotta",
    "path": "dirt_path", "cobble": "cobblestone", "stonebrick": "stone_bricks", "wall": "stone_bricks",
    "planks": "spruce_planks", "dark_planks": "dark_oak_planks", "brick": "bricks", "copper": "cut_copper",
    "copper_ox": "oxidized_cut_copper", "deepslate": "deepslate_tiles", "iron": "iron_block", "hay": "hay_block",
    "wheat": "hay_block", "farmland": "farmland", "leaves": "oak_leaves", "leaves_dark": "dark_oak_leaves",
    "spruce": "spruce_leaves", "water": "water", "lava": "lava", "rail": "polished_andesite", "black": "black_concrete",
}
# 덮개 중 위로 쌓는 것 (높이)
RAISE = {"wall": 3, "iron": 1, "copper": 1, "copper_ox": 1, "deepslate": 1}


def main():
    t0 = time.time()
    d = np.load(os.path.join(HERE, ".world_mc.npz"))
    h, surf, over, water = d["h"], d["surf"], d["over"], d["water"]
    names = [str(n) for n in d["names"]]
    trees = d["trees"]
    builds = json.load(open(os.path.join(HERE, ".world_mc_builds.json")))
    n = N // SC
    c = SC // 2
    # 칸 가운데 표본 (배열은 [z, x])
    hs = h[c::SC, c::SC].astype(np.float32) / SC
    su = surf[c::SC, c::SC]
    ov = over[c::SC, c::SC]
    wt = water[c::SC, c::SC]
    y0 = int(np.floor(hs.min())) - 2
    top = np.round(hs).astype(np.int32) - y0
    sea = int(round(SEA / SC)) - y0
    Y = int(max(top.max(), sea) + 12)
    pal_states = ["air"]
    pid = {"air": 0}

    def P(s):
        if s not in pid:
            pid[s] = len(pal_states); pal_states.append(s)
        return pid[s]

    vox = np.zeros((n, Y, n), np.uint16)
    yy = np.arange(Y)[None, :, None]
    T = top.T[:, None, :]                              # [x, 1, z]
    # 땅: 돌 → 흙 → 지면
    vox[yy <= T] = P("stone")
    vox[(yy <= T) & (yy >= T - 2)] = P("dirt")
    surf_state = np.vectorize(lambda i: P(STATE[names[i]]))(su).T      # [x, z]
    ovs = np.where(ov >= 0, ov, 0)
    over_state = np.vectorize(lambda i: P(STATE[names[i]]))(ovs).T
    top_state = np.where((ov.T >= 0), over_state, surf_state)
    xi, zi = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    vox[xi, top.T, zi] = top_state
    # 물
    wmask = (yy > T) & (yy <= sea)
    vox[wmask] = P("water")
    # 덮개 중 위로 쌓는 것 (성벽 · 고철 · 망루)
    for k, dh in RAISE.items():
        ki = names.index(k)
        m = (ov.T == ki)
        for j in range(1, dh + 1):
            vox[xi[m], top.T[m] + j, zi[m]] = P(STATE[k])
    # 부두 · 배 (물 위 덮개)
    for k in ("planks", "dark_planks"):
        ki = names.index(k)
        m = (ov.T == ki) & wt.T
        vox[xi[m], np.full(m.sum(), sea + 1), zi[m]] = P(STATE[k])
    # 건물: 벽 2칸 + 박공 지붕
    roof_state = {"dark_planks": "dark_oak_planks", "brick": "bricks", "copper": "cut_copper",
                  "copper_ox": "oxidized_cut_copper", "deepslate": "deepslate_tiles"}
    for x, z, w, dd, roof, ridge in builds:
        ax0 = int((x - H0) / SC); az0 = int((z - H0) / SC)
        ax1 = max(ax0, int((x + w - H0) / SC)); az1 = max(az0, int((z + dd - H0) / SC))
        if not (0 <= ax0 < n and 0 <= az1 < n):
            continue
        base = int(top[min(n - 1, az0), min(n - 1, ax0)])
        tower = roof == "deepslate" and w <= 8 and dd <= 8
        wall_h = 4 if tower else 2
        wall = "stone_bricks" if tower else ("spruce_planks" if roof != "copper_ox" else "polished_andesite")
        vox[ax0:ax1 + 1, base + 1:base + 1 + wall_h, az0:az1 + 1] = P(wall)
        rs = P(roof_state.get(roof, "dark_oak_planks"))
        vox[ax0:ax1 + 1, base + 1 + wall_h, az0:az1 + 1] = rs
        # 용마루 한 칸 더
        if ridge and az1 - az0 >= 2:
            mz = (az0 + az1) // 2
            vox[ax0:ax1 + 1, base + 2 + wall_h, mz] = rs
        elif not ridge and ax1 - ax0 >= 2:
            mx = (ax0 + ax1) // 2
            vox[mx, base + 2 + wall_h, az0:az1 + 1] = rs
    # 나무: 줄기 1~2 + 잎
    leaf_state = {1: P("oak_leaves"), 2: P("dark_oak_leaves"), 3: P("spruce_leaves")}
    log_state = {1: P("oak_log"), 2: P("dark_oak_log"), 3: P("spruce_log")}
    rng = np.random.default_rng(3)
    for tx, tz, r, kind in trees:
        ax, az = int(tx // SC), int(tz // SC)
        if not (1 <= ax < n - 1 and 1 <= az < n - 1) or wt[az, ax]:
            continue
        b = int(top[az, ax])
        th = 1 + int(r >= 3)
        vox[ax, b + 1:b + 1 + th, az] = log_state[kind]
        cy = b + th + 1
        L = leaf_state[kind]
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if vox[ax + dx, cy, az + dz] == 0:
                    vox[ax + dx, cy, az + dz] = L
        if r >= 3 or kind == 3:
            vox[ax, cy + 1, az] = L
    print(f"[3d] 복셀 {vox.shape}, 팔레트 {len(pal_states)}, {time.time() - t0:.1f}s")
    pal = R.Palette(pal_states)
    shots = {
        "south": dict(cam=(n * 0.5, Y + n * 0.8, n * 1.5), target=(n * 0.5, 0, n * 0.52), fov=50),
        "angle": dict(cam=(n * 1.25, Y + n * 0.5, n * 1.2), target=(n * 0.45, 0, n * 0.45), fov=44),
    }
    for nm, sh in shots.items():
        t = time.time()
        im = R.render(vox, pal, 1600, 1000, sh["cam"], sh["target"], fov=sh["fov"], ss=2, fog_dist=2000)
        im.save(os.path.join(OUT, f"world3d_{nm}.png"))
        print(nm, f"{time.time() - t:.1f}s")


if __name__ == "__main__":
    main()
