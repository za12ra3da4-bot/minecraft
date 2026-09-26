"""지형 → 블록 기둥"""
import numpy as np
from scipy import ndimage

from layout import *
from noise import value_noise

S = SIZE


def pick(r, table):
    """r(0..1) → 가중 테이블에서 선택"""
    tot = sum(w for _, w in table)
    acc = 0
    for b, w in table:
        acc += w / tot
        if r < acc:
            return b
    return table[-1][0]


STRATA = {
    "default": ["stone", "stone", "andesite", "stone", "tuff", "stone", "andesite", "cobblestone", "stone"],
    "ares": ["terracotta", "terracotta", "brown_terracotta", "terracotta", "red_terracotta", "terracotta", "brown_terracotta", "basalt[axis=y]", "blackstone"],
    "athena": ["calcite", "calcite", "diorite", "polished_diorite", "calcite", "stone", "calcite"],
    "hermes": ["stone", "andesite", "stone", "tuff", "stone", "stone", "andesite", "gravel"],
    "demeter": ["mossy_cobblestone", "stone", "moss_block", "stone", "mossy_cobblestone", "andesite"],
    "forge": ["basalt[axis=y]", "blackstone", "basalt[axis=y]", "smooth_basalt", "blackstone", "deepslate[axis=y]", "tuff"],
    "sands": ["sandstone", "sandstone", "cut_sandstone", "smooth_sandstone", "orange_terracotta", "sandstone", "yellow_terracotta"],
    "quarry": ["stone", "stone", "andesite", "stone", "cobblestone", "stone", "polished_andesite"],
    "garden": ["mossy_stone_bricks", "stone", "mossy_cobblestone", "stone"],
    "mount": ["stone", "andesite", "stone", "stone", "tuff", "stone", "granite", "stone", "diorite", "stone"],
}

TOPS = {
    "default": [("grass_block", 74), ("coarse_dirt", 7), ("podzol", 5), ("moss_block", 3), ("rooted_dirt", 3), ("gravel", 2)],
    "ares": [("coarse_dirt", 40), ("blackstone", 18), ("basalt[axis=y]", 12), ("gravel", 12), ("tuff", 8), ("packed_mud", 6), ("magma_block", 1)],
    "athena": [("grass_block", 88), ("moss_block", 4), ("coarse_dirt", 3), ("calcite", 5)],
    "hermes": [("grass_block", 72), ("stone", 10), ("andesite", 8), ("gravel", 5), ("coarse_dirt", 5)],
    "demeter": [("grass_block", 58), ("moss_block", 24), ("rooted_dirt", 8), ("podzol", 10)],
    "plaza": [("grass_block", 90), ("coarse_dirt", 6), ("moss_block", 4)],
    "base": [("grass_block", 80), ("coarse_dirt", 12), ("gravel", 8)],
    "forge": [("blackstone", 34), ("basalt[axis=y]", 18), ("smooth_basalt", 10), ("gravel", 12), ("coarse_dirt", 14), ("magma_block", 4), ("tuff", 8)],
    "sands": [("sand", 62), ("sandstone", 18), ("smooth_sandstone", 10), ("coarse_dirt", 4), ("red_sand", 6)],
    "quarry": [("stone", 38), ("cobblestone", 18), ("gravel", 18), ("andesite", 16), ("coarse_dirt", 10)],
    "garden": [("grass_block", 80), ("moss_block", 14), ("podzol", 6)],
    "mount": [("grass_block", 55), ("stone", 20), ("coarse_dirt", 10), ("andesite", 10), ("gravel", 5)],
}
SUB = {"ares": "red_terracotta", "sands": "sandstone", "forge": "blackstone", "quarry": "stone", "athena": "dirt"}


def zkey(z):
    if z.startswith("base_"):
        return "base"
    if z.startswith("lair_"):
        return z[5:]
    return z or "default"


def paint(w, T, seed=3):
    Hi = T.Hi
    rs = np.random.default_rng(seed)
    rnd = rs.random((S, S))
    rnd2 = rs.random((S, S))
    n1 = value_noise(S, 7, seed + 1)
    n2 = value_noise(S, 13, seed + 2)
    strata_off = (value_noise(S, 24, seed + 3) * 4).astype(int)
    lowN = ndimage.minimum_filter(Hi, size=3, mode="nearest")
    hiN = ndimage.maximum_filter(Hi, size=3, mode="nearest")
    slope = np.maximum(Hi - lowN, hiN - Hi)
    T.slope = slope
    for x in range(S):
        for z in range(S):
            h = int(Hi[x, z])
            zone = T.zone[x, z]
            k = zkey(zone)
            mount = (zone == "" and h > G + 9)
            if mount:
                k = "mount"
            strata = STRATA.get(k, STRATA["default"])
            floor = max(0, min(h - 4, int(lowN[x, z]) - 1))
            # 암석층
            for y in range(floor, h + 1):
                s = strata[(y + strata_off[x, z]) % len(strata)]
                w.vox[x, y, z] = w.id(s)
            wl = T.water[x, z]
            rk = T.road_kind[x, z]
            sl = slope[x, z]
            if wl >= 0 and wl > h:
                # 물 바닥
                bot = pick(rnd[x, z], [("gravel", 3), ("sand", 3), ("clay", 2), ("dirt", 2)])
                if zone == "plaza":
                    bot = pick(rnd[x, z], [("stone_bricks", 5), ("mossy_stone_bricks", 3), ("gravel", 2)])
                if k == "hermes":
                    bot = pick(rnd[x, z], [("gravel", 4), ("stone", 3), ("andesite", 2)])
                w.vox[x, h, z] = w.id(bot)
                w.vox[x, h + 1:wl + 1, z] = w.id("water")
                continue
            if sl >= 3 and rk == 0 and k not in ("plaza",):
                continue  # 절벽: 암석 노출
            if rk == 1:
                top = pick(rnd[x, z], [("stone_bricks", 40), ("polished_andesite", 18), ("cracked_stone_bricks", 14),
                                       ("mossy_stone_bricks", 12), ("andesite", 8), ("cobblestone", 8)])
                if T.road[x, z] < 0.75:
                    top = pick(rnd[x, z], [("gravel", 3), ("coarse_dirt", 3), ("mossy_cobblestone", 2), ("grass_block", 2)])
                w.vox[x, h, z] = w.id(top)
                w.vox[x, max(floor, h - 2):h, z] = w.id("cobblestone")
                # 반 블록 경사
                fr = T.H[x, z] - h
                if fr >= 0.25 and top in ("stone_bricks", "cracked_stone_bricks", "mossy_stone_bricks", "polished_andesite", "andesite", "cobblestone"):
                    base_mat = {"stone_bricks": "stone_brick", "cracked_stone_bricks": "stone_brick", "mossy_stone_bricks": "mossy_stone_brick",
                                "polished_andesite": "polished_andesite", "andesite": "andesite", "cobblestone": "cobblestone"}[top]
                    w.vox[x, h + 1, z] = w.id(base_mat + "_slab[type=bottom,waterlogged=false]")
                continue
            if rk == 2:
                top = pick(rnd[x, z], [("dirt_path", 62), ("coarse_dirt", 18), ("gravel", 8), ("rooted_dirt", 6), ("packed_mud", 6)])
                if k in ("ares", "forge"):
                    top = pick(rnd[x, z], [("coarse_dirt", 50), ("gravel", 25), ("blackstone", 25)])
                if k == "sands":
                    top = pick(rnd[x, z], [("smooth_sandstone", 50), ("sandstone", 30), ("sand", 20)])
                if T.road[x, z] < 0.75 and rnd2[x, z] < 0.5:
                    top = "grass_block" if k not in ("ares", "forge", "sands", "quarry", "hermes") else top
                w.vox[x, h, z] = w.id(top)
                w.vox[x, max(floor, h - 3):h, z] = w.id("dirt")
                continue
            if rk == 3:
                top = pick(rnd[x, z], [("gravel", 38), ("cobblestone", 20), ("andesite", 14), ("dirt_path", 16), ("mossy_cobblestone", 12)])
                if T.road[x, z] < 0.75 and rnd2[x, z] < 0.5:
                    top = "grass_block" if k not in ("ares", "forge", "sands") else "gravel"
                w.vox[x, h, z] = w.id(top)
                w.vox[x, max(floor, h - 3):h, z] = w.id("dirt")
                continue
            table = TOPS.get(k, TOPS["default"])
            r = (n1[x, z] * 0.6 + rnd[x, z] * 0.4) if k not in ("ares", "forge", "sands", "quarry", "hermes") else (n1[x, z] * 0.85 + rnd[x, z] * 0.15)
            top = pick(r, table)
            if k in ("default", "mount") and sl >= 2 and rnd2[x, z] < 0.45:
                top = pick(rnd[x, z], [("stone", 4), ("andesite", 2), ("coarse_dirt", 2), ("gravel", 1)])
            # 물가 모래/자갈
            if k not in ("ares", "forge", "sands"):
                near_w = False
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        xx, zz = x + dx, z + dz
                        if 0 <= xx < S and 0 <= zz < S and T.water[xx, zz] >= 0 and T.water[xx, zz] >= h:
                            near_w = True
                if near_w:
                    top = pick(rnd[x, z], [("gravel", 3), ("coarse_dirt", 2), ("grass_block", 3), ("mud", 1)])
            sub = SUB.get(k, "dirt")
            if top in ("sand", "red_sand"):
                sub = "sandstone" if top == "sand" else "red_sandstone"
            w.vox[x, h, z] = w.id(top)
            if top in ("grass_block", "podzol", "coarse_dirt", "rooted_dirt", "moss_block", "dirt_path", "mud"):
                w.vox[x, max(floor, h - 3):h, z] = w.id(sub)
