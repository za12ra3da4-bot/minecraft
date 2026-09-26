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


# 암석층: 두께 3 칸 띠 (가까운 색끼리) — 줄무늬가 튀지 않게
STRATA = {
    "default": ["stone", "stone", "andesite", "stone", "tuff", "stone"],
    "ares": ["terracotta", "brown_terracotta", "terracotta", "packed_mud", "terracotta", "brown_terracotta"],
    "athena": ["calcite", "calcite", "diorite", "calcite", "stone"],
    "hermes": ["stone", "andesite", "stone", "tuff", "stone"],
    "demeter": ["stone", "mossy_cobblestone", "stone", "andesite"],
    "forge": ["basalt[axis=y]", "blackstone", "basalt[axis=y]", "smooth_basalt", "blackstone", "deepslate[axis=y]"],
    "sands": ["sandstone", "sandstone", "smooth_sandstone", "sandstone", "cut_sandstone"],
    "quarry": ["stone", "stone", "andesite", "stone", "tuff", "stone"],
    "garden": ["stone", "mossy_cobblestone", "stone", "andesite"],
    "mount": ["stone", "andesite", "stone", "tuff", "stone", "stone"],
}
BAND = 3

# 윗면: 기본 재질 + 저주파 노이즈 군락 (한 칸짜리 점박이 없음)
#   (재질, 노이즈, 하한, 상한)  노이즈: a = 7칸, b = 13칸, c = 29칸 주기
TOPS = {
    "default": ("grass_block", [("moss_block", "b", 0.80, 1.1), ("rooted_dirt", "c", 0.0, 0.07)]),
    "ares": ("coarse_dirt", [("blackstone", "b", 0.70, 1.1), ("gravel", "a", 0.0, 0.22), ("packed_mud", "c", 0.75, 1.1)]),
    "athena": ("grass_block", [("moss_block", "b", 0.84, 1.1)]),
    "hermes": ("grass_block", [("stone", "b", 0.84, 1.1), ("andesite", "c", 0.0, 0.08)]),
    "demeter": ("grass_block", [("moss_block", "b", 0.70, 1.1), ("rooted_dirt", "c", 0.0, 0.1)]),
    "plaza": ("grass_block", [("moss_block", "b", 0.82, 1.1)]),
    "base": ("grass_block", [("moss_block", "b", 0.84, 1.1)]),
    "forge": ("blackstone", [("basalt[axis=y]", "b", 0.62, 1.1), ("smooth_basalt", "a", 0.0, 0.2), ("gravel", "c", 0.0, 0.12)]),
    "sands": ("sand", [("sandstone", "b", 0.80, 1.1), ("smooth_sandstone", "c", 0.0, 0.08)]),
    "quarry": ("stone", [("andesite", "b", 0.64, 1.1), ("gravel", "c", 0.0, 0.14), ("tuff", "a", 0.0, 0.14)]),
    "garden": ("grass_block", [("moss_block", "b", 0.72, 1.1)]),
    "mount": ("grass_block", [("moss_block", "b", 0.82, 1.1)]),
}


def top_pick(k, na, nb, nc):
    base, patches = TOPS.get(k, TOPS["default"])
    nz = {"a": na, "b": nb, "c": nc}
    for m, key, lo, hi in patches:
        if lo <= nz[key] < hi:
            return m
    return base


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
    strata_off = (value_noise(S, 24, seed + 3) * 5).astype(int)
    n3 = value_noise(S, 29, seed + 4)
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
                s = strata[((y + strata_off[x, z]) // BAND) % len(strata)]
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
            top = top_pick(k, n1[x, z], n2[x, z], n3[x, z])
            if k in ("default", "mount", "hermes") and sl >= 2 and n1[x, z] < 0.45:
                top = "stone" if n2[x, z] < 0.6 else "andesite"
            # 물가 모래/자갈
            if k not in ("ares", "forge", "sands"):
                near_w = False
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        xx, zz = x + dx, z + dz
                        if 0 <= xx < S and 0 <= zz < S and T.water[xx, zz] >= 0 and T.water[xx, zz] >= h:
                            near_w = True
                if near_w:
                    top = "gravel" if n1[x, z] < 0.5 else ("sand" if n2[x, z] < 0.5 else "grass_block")
            sub = SUB.get(k, "dirt")
            if top in ("sand", "red_sand"):
                sub = "sandstone" if top == "sand" else "red_sandstone"
            w.vox[x, h, z] = w.id(top)
            if top in ("grass_block", "podzol", "coarse_dirt", "rooted_dirt", "moss_block", "dirt_path", "mud"):
                w.vox[x, max(floor, h - 3):h, z] = w.id(sub)
