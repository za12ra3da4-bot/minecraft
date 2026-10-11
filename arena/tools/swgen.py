"""양과 늑대 — 1:1 공성전 맵 (미리보기 전용)

 서쪽 = 양 진영: 하얀 성벽 목장 요새 · 성문 · 망루 · 본성(황금 양털 제단 = 지켜야 할 것) · 풍차 · 헛간 · 양 우리 · 꽃밭
 동쪽 = 늑대 진영: 어두운 숲 · 뾰족 통나무 울타리 · 굴 언덕 (붉은 눈) · 모닥불 · 달의 제단 (늑대 본거지)
 가운데 = 강 (다리 3개: 북 · 가운데(폐허 망루 섬) · 남) · 들판 · 생울타리 · 바위 · 무너진 벽
 x: 서(-) 양 → 동(+) 늑대 · z: 북(-) ~ 남(+) · 바닥 높이 FL
"""
import math
import os

import numpy as np

NX, NZ, H = 200, 120, 64
FL = 14
CX, CZ = NX // 2, NZ // 2

PAL = ["air"]
P = {"air": 0}


def pid(s):
    if s not in P:
        P[s] = len(PAL)
        PAL.append(s)
    return P[s]


def build():
    v = np.zeros((NX, H, NZ), np.uint16)
    rng = np.random.default_rng(7)

    def put(x, y, z, b):
        gx, gz, yy = CX + int(math.floor(x)), CZ + int(math.floor(z)), int(math.floor(y))
        if 0 <= gx < NX and 0 <= yy < H and 0 <= gz < NZ:
            v[gx, yy, gz] = pid(b)

    def get(x, y, z):
        gx, gz, yy = CX + int(math.floor(x)), CZ + int(math.floor(z)), int(math.floor(y))
        if 0 <= gx < NX and 0 <= yy < H and 0 <= gz < NZ:
            return PAL[v[gx, yy, gz]]
        return "air"

    def box(x0, y0, z0, x1, y1, z1, b):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    put(x, y, z, b)

    X0, X1, Z0, Z1 = -CX, NX - CX - 1, -CZ, NZ - CZ - 1

    # ── 지형: 높이 (부드러운 언덕) · 늑대 쪽은 숲 바닥 (흙 · 이끼 · 포드졸)
    hmap = {}
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            h = 1.2 * math.sin(x * 0.07) * math.cos(z * 0.09) + 0.8 * math.sin(x * 0.031 + z * 0.05)
            if x > 40:                       # 늑대 굴 언덕 (북동쪽 큰 언덕)
                d = math.hypot((x - 78) / 18, (z + 30) / 16)
                h += max(0, 9 * (1 - d * d))
            if abs(x) < 8:                   # 강가로 낮아짐
                h -= (8 - abs(x)) * 0.35
            hmap[x, z] = int(round(h))
    for (x, z), h in hmap.items():
        top = FL + h
        for y in range(FL - 6, top):
            put(x, y, z, "dirt" if y > top - 4 else "stone")
        if x < -6:
            g = "grass_block"
        elif x > 6:
            r = rng.random()
            g = "podzol" if r < 0.35 else ("coarse_dirt" if r < 0.45 else ("moss_block" if r < 0.55 else "grass_block"))
        else:
            g = "grass_block"
        put(x, top, z, g)

    def ground(x, z):
        return FL + hmap.get((int(x), int(z)), 0)

    # ── 강 (x -3..3 · 살짝 굽이침) + 모래 강가
    for z in range(Z0, Z1 + 1):
        off = int(round(2.2 * math.sin(z * 0.06)))
        for x in range(-6 + off, 7 + off):
            g = ground(x, z)
            if abs(x - off) <= 3:
                for y in range(FL - 4, FL):
                    put(x, y, z, "water" if y >= FL - 3 else "gravel")
                for y in range(FL, g + 1):
                    put(x, y, z, "air")
                put(x, FL - 1, z, "water")
            elif abs(x - off) <= 5:
                put(x, g, z, "sand")

    # ── 다리 3개 (돌벽돌 · 난간 · 등)
    def bridge(zc, w):
        for z in range(zc - w, zc + w + 1):
            for x in range(-8, 9):
                off = int(round(2.2 * math.sin(z * 0.06)))
                put(x, FL, z, "stone_bricks" if abs(z - zc) < w else "mossy_stone_bricks")
                if abs(x - off) <= 3:
                    put(x, FL - 1, z, "stone_brick_slab[type=top,waterlogged=false]")
            for x in range(-8, 9, 1):
                pass
        for x in range(-8, 9):
            put(x, FL + 1, zc - w, "stone_brick_wall")
            put(x, FL + 1, zc + w, "stone_brick_wall")
        for x in (-8, 8):
            for zz in (zc - w, zc + w):
                put(x, FL + 2, zz, "lantern")
    bridge(-38, 2)
    bridge(38, 2)
    # 가운데: 넓은 다리 + 강 가운데 작은 섬의 무너진 망루
    for z in range(-6, 7):
        for x in range(-9, 10):
            put(x, FL, z, "cobblestone" if rng.random() < 0.3 else "stone_bricks")
    for x in range(-9, 10):
        if rng.random() < 0.8:
            put(x, FL + 1, -6, "cobblestone_wall")
        if rng.random() < 0.8:
            put(x, FL + 1, 6, "cobblestone_wall")
    # 폐허 망루 (가운데)
    for y in range(FL + 1, FL + 11):
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if max(abs(dx), abs(dz)) == 2:
                    if y < FL + 7 or rng.random() < (FL + 11 - y) / 6:
                        put(dx, y, dz, "mossy_stone_bricks" if rng.random() < 0.4 else "cracked_stone_bricks")
    for dx in (-2, 2):
        box(dx, FL + 1, 0, dx, FL + 3, 0, "air")
    put(0, FL + 7, 0, "chiseled_stone_bricks")
    put(0, FL + 8, 0, "white_banner") if False else None

    # ── 들판 장식: 생울타리 · 바위 · 꽃 · 무너진 벽
    def hedge(x0, z0, x1, z1):
        n = max(abs(x1 - x0), abs(z1 - z0))
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            z = round(z0 + (z1 - z0) * i / n)
            g = ground(x, z)
            put(x, g + 1, z, "oak_leaves")
            if rng.random() < 0.6:
                put(x, g + 2, z, "oak_leaves")
    for (a, b, c, d) in [(-26, -50, -26, -28), (-20, 14, -20, 30), (24, -24, 24, -10), (20, 30, 20, 52), (-14, -14, -8, -14), (12, 18, 16, 18)]:
        hedge(a, b, c, d)

    def boulder(x, z, r):
        g = ground(x, z)
        for dx in range(-r, r + 1):
            for dy in range(0, r + 1):
                for dz in range(-r, r + 1):
                    if dx * dx + (dy * 1.4) ** 2 + dz * dz <= r * r + 0.5:
                        put(x + dx, g + dy, z + dz, "mossy_cobblestone" if rng.random() < 0.3 else ("andesite" if rng.random() < 0.5 else "stone"))
    for x, z, r in [(-18, -30, 2), (14, -48, 2), (-12, 44, 3), (16, 6, 2), (28, 46, 2), (-30, 2, 2)]:
        boulder(x, z, r)

    def ruin_wall(x, z, ln, axis):
        g = ground(x, z)
        for i in range(ln):
            xx, zz = (x + i, z) if axis == "x" else (x, z + i)
            hh = int(1 + 3 * abs(math.sin(i * 0.9)))
            for y in range(hh):
                put(xx, ground(xx, zz) + 1 + y, zz, "mossy_stone_bricks" if rng.random() < 0.5 else "cracked_stone_bricks")
    ruin_wall(-16, 22, 6, "x")
    ruin_wall(12, -32, 7, "z")

    # ══════════════════════════════════════════ 양 진영 (서쪽) — 하얀 목장 요새
    SX0, SX1, SZ0, SZ1 = -92, -50, -30, 30
    # 성 마당 바닥 (자갈길 + 잔디)
    for x in range(SX0, SX1 + 1):
        for z in range(SZ0, SZ1 + 1):
            g = ground(x, z)
            for y in range(g + 1, FL + 1):
                put(x, y, z, "dirt")
            for y in range(FL + 1, g + 1):
                put(x, y, z, "air")
            put(x, FL, z, "grass_block")
    for x in range(SX0, SX1 + 1):                   # 가운데 길 (성문 → 본성)
        for z in range(-2, 3):
            put(x, FL, z, "dirt_path" if abs(z) < 2 else "gravel")
    # 성벽: 하얀 (석회암 · 방해석) + 회색 받침 · 톱니 · 성문 (동쪽 가운데)
    WH = 7
    for x in range(SX0, SX1 + 1):
        for z in range(SZ0, SZ1 + 1):
            edge = x in (SX0, SX1) or z in (SZ0, SZ1)
            if not edge:
                continue
            for y in range(FL + 1, FL + WH + 1):
                put(x, y, z, "polished_andesite" if y <= FL + 1 else ("calcite" if (x + z + y) % 7 else "white_concrete"))
            if (x + z) % 2 == 0:
                put(x, FL + WH + 1, z, "white_concrete")
            put(x, FL + WH, z, "smooth_quartz")
    # 성벽 위 통로 (안쪽 1칸)
    for x in range(SX0 + 1, SX1):
        for z in (SZ0 + 1, SZ1 - 1):
            put(x, FL + WH - 1, z, "spruce_planks")
    for z in range(SZ0 + 1, SZ1):
        for x in (SX0 + 1, SX1 - 1):
            put(x, FL + WH - 1, z, "spruce_planks")
    # 성문 (동쪽 벽 가운데 5칸) + 문 위 아치 + 내리닫이 쇠창살
    for z in range(-2, 3):
        for y in range(FL + 1, FL + 5):
            put(SX1, y, z, "air")
        put(SX1, FL + 5, z, "chiseled_quartz_block")
        put(SX1 + 1, FL + 4, z, "iron_bars")
    # 망루 4 (모서리 · 둥근 지붕 = 하늘색)
    def tower(cx, cz, r, hgt, wall, roof):
        for y in range(FL + 1, FL + hgt + 1):
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    d = math.hypot(dx, dz)
                    if r - 0.9 <= d <= r + 0.3:
                        put(cx + dx, y, cz + dz, wall if (y - FL) % 5 else "polished_andesite")
                    elif d < r - 0.9:
                        put(cx + dx, y, cz + dz, "air")
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if math.hypot(dx, dz) <= r + 0.3:
                    put(cx + dx, FL + hgt, cz + dz, "spruce_planks")
        for k in range(0, r + 3):
            rr = r + 1 - k * 0.75
            if rr < 0.3:
                put(cx, FL + hgt + 1 + k, cz, roof)
                break
            for dx in range(-r - 1, r + 2):
                for dz in range(-r - 1, r + 2):
                    if math.hypot(dx, dz) <= rr:
                        put(cx + dx, FL + hgt + 1 + k, cz + dz, roof)
        for a in range(0, 360, 90):
            put(cx + round(math.cos(math.radians(a)) * r), FL + hgt - 3, cz + round(math.sin(math.radians(a)) * r), "glass_pane")
    for cx, cz in ((SX0, SZ0), (SX0, SZ1), (SX1, SZ0), (SX1, SZ1)):
        tower(cx, cz, 3, 12, "calcite", "light_blue_concrete")
    for cz in (-6, 6):
        tower(SX1, cz, 2, 10, "calcite", "light_blue_concrete")
    # 본성 (가운데 서쪽) — 하얀 벽 · 하늘색 지붕 · 황금 양털 제단
    KX0, KX1, KZ0, KZ1 = -86, -70, -9, 9
    for x in range(KX0, KX1 + 1):
        for z in range(KZ0, KZ1 + 1):
            edge = x in (KX0, KX1) or z in (KZ0, KZ1)
            for y in range(FL + 1, FL + 11):
                if edge:
                    put(x, y, z, "white_concrete" if (y - FL) % 4 else "polished_diorite")
            put(x, FL, z, "smooth_quartz")
    for z in range(-1, 2):
        for y in range(FL + 1, FL + 5):
            put(KX1, y, z, "air")
    for z in range(KZ0 + 2, KZ1 - 1, 3):
        for y in (FL + 4, FL + 5, FL + 8):
            put(KX1, y, z, "light_blue_stained_glass")
            put(KX0, y, z, "light_blue_stained_glass")
    for x in range(KX0 + 2, KX1 - 1, 3):
        for y in (FL + 5, FL + 8):
            put(x, y, KZ0, "light_blue_stained_glass")
            put(x, y, KZ1, "light_blue_stained_glass")
    # 박공 지붕 (북-남 용마루)
    for k in range(0, 11):
        for z in range(KZ0 - 1, KZ1 + 2):
            for x in (KX0 - 1 + k, KX1 + 1 - k):
                if KX0 - 1 + k <= KX1 + 1 - k:
                    put(x, FL + 11 + k, z, "light_blue_concrete" if (z % 2) else "cyan_concrete")
        if KX0 - 1 + k >= KX1 + 1 - k:
            break
    for z in (KZ0, KZ1):
        for k in range(0, 9):
            for x in range(KX0 + k, KX1 - k + 1):
                put(x, FL + 11 + k, z, "white_concrete")
    # 황금 양털 제단 (본성 안 · 지켜야 할 것)
    ax, az = -78, 0
    box(ax - 1, FL + 1, az - 1, ax + 1, FL + 1, az + 1, "chiseled_quartz_block")
    put(ax, FL + 2, az, "gold_block")
    put(ax, FL + 3, az, "yellow_wool")
    put(ax, FL + 4, az, "yellow_wool")
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        box(ax + dx * 3, FL + 1, az + dz * 3, ax + dx * 3, FL + 4, az + dz * 3, "quartz_pillar")
        put(ax + dx * 3, FL + 5, az + dz * 3, "lantern")
    # 헛간 (빨간) · 건초
    bx0, bz0 = -66, -26
    box(bx0, FL + 1, bz0, bx0 + 9, FL + 5, bz0 + 7, "red_terracotta")
    box(bx0 + 1, FL + 1, bz0 + 1, bx0 + 8, FL + 5, bz0 + 6, "air")
    for k in range(5):
        box(bx0 - 1 + k, FL + 6 + k, bz0 - 1, bx0 - 1 + k, FL + 6 + k, bz0 + 8, "dark_oak_planks")
        box(bx0 + 10 - k, FL + 6 + k, bz0 - 1, bx0 + 10 - k, FL + 6 + k, bz0 + 8, "dark_oak_planks")
    box(bx0 + 4, FL + 1, bz0 + 7, bx0 + 5, FL + 4, bz0 + 7, "air")
    for (hx, hz) in ((-58, -22), (-58, -20), (-57, -21), (-60, -24)):
        put(hx, FL + 1, hz, "hay_block")
    put(-58, FL + 2, -21, "hay_block")
    # 풍차 (남서쪽 · 하얀 탑 + 양털 날개)
    mx, mz = -84, 20
    for y in range(FL + 1, FL + 15):
        r = 3 - (y - FL) * 0.1
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                d = math.hypot(dx, dz)
                if r - 0.9 <= d <= r + 0.2:
                    put(mx + dx, y, mz + dz, "smooth_quartz" if (y - FL) % 4 else "birch_planks")
    for k in range(4):
        put(mx, FL + 15 + k, mz, "spruce_planks") if k < 1 else None
    hub = (mx + 3, FL + 13, mz)
    put(*hub, "spruce_log")
    for a in (45, 135, 225, 315):
        for t in range(1, 10):
            yy = hub[1] + round(math.sin(math.radians(a)) * t)
            zz = hub[2] + round(math.cos(math.radians(a)) * t)
            put(hub[0] + 1, yy, zz, "spruce_planks" if t < 3 else "white_wool")
            if t > 2:
                put(hub[0] + 1, yy, zz + (1 if a in (45, 315) else -1), "white_wool")
    # 양 우리 (울타리 · 하얀 양털 = 양 대신)
    def pen(x0, z0, x1, z1):
        for x in range(x0, x1 + 1):
            put(x, FL + 1, z0, "oak_fence")
            put(x, FL + 1, z1, "oak_fence")
        for z in range(z0, z1 + 1):
            put(x0, FL + 1, z, "oak_fence")
            put(x1, FL + 1, z, "oak_fence")
        for _ in range(5):
            sx, sz = int(rng.integers(x0 + 1, x1)), int(rng.integers(z0 + 1, z1))
            put(sx, FL + 1, sz, "white_wool")
    pen(-66, 12, -56, 24)
    pen(-88, -26, -78, -16)
    # 꽃밭 · 나무 (자작)
    for _ in range(140):
        x, z = int(rng.integers(SX0 + 2, SX1 - 1)), int(rng.integers(SZ0 + 2, SZ1 - 1))
        if PAL[v[CX + x, FL + 1, CZ + z]] == "air" and get(x, FL, z) == "grass_block" and abs(z) > 3:
            put(x, FL + 1, z, str(rng.choice(["dandelion", "poppy", "azure_bluet", "oxeye_daisy", "cornflower", "short_grass", "short_grass"])))

    def tree(x, z, log, leaf, hh):
        g = ground(x, z) if not (SX0 <= x <= SX1 and SZ0 <= z <= SZ1) else FL
        for y in range(1, hh + 1):
            put(x, g + y, z, log)
        for dx in range(-2, 3):
            for dy in range(-1, 2):
                for dz in range(-2, 3):
                    if abs(dx) + abs(dz) + abs(dy) <= 3:
                        put(x + dx, g + hh + dy, z + dz, leaf)
        put(x, g + hh + 2, z, leaf)
    # 양 진영 바깥: 자작나무 · 들판 꽃
    for _ in range(14):
        x, z = int(rng.integers(-98, -32)), int(rng.integers(-58, 58))
        if not (SX0 - 3 <= x <= SX1 + 3 and SZ0 - 3 <= z <= SZ1 + 3):
            tree(x, z, "birch_log", "birch_leaves", int(rng.integers(5, 7)))
    for _ in range(260):
        x, z = int(rng.integers(-99, -8)), int(rng.integers(-59, 59))
        if SX0 - 1 <= x <= SX1 + 1 and SZ0 - 1 <= z <= SZ1 + 1:
            continue
        g = ground(x, z)
        if get(x, g, z) == "grass_block" and get(x, g + 1, z) == "air":
            put(x, g + 1, z, str(rng.choice(["short_grass", "short_grass", "dandelion", "poppy", "oxeye_daisy"])))

    # ══════════════════════════════════════════ 늑대 진영 (동쪽) — 어두운 숲 · 뾰족 울타리 · 굴 · 달의 제단
    WX0, WX1, WZ0, WZ1 = 50, 94, -30, 30
    # 숲 (가문비 · 짙은 참나무) — 진영 밖 동쪽 절반 전체
    def spruce(x, z, hh):
        g = ground(x, z)
        for y in range(1, hh + 1):
            put(x, g + y, z, "spruce_log")
        for k in range(hh - 1):
            r = max(0, (hh - k) // 3)
            y = g + 3 + k
            if y > g + hh + 1:
                break
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if abs(dx) + abs(dz) <= r and (dx or dz or y > g + hh):
                        put(x + dx, y, z + dz, "spruce_leaves")
        put(x, g + hh + 1, z, "spruce_leaves")
    for _ in range(90):
        x, z = int(rng.integers(26, 99)), int(rng.integers(-59, 60))
        if WX0 - 3 <= x <= WX1 + 3 and WZ0 - 3 <= z <= WZ1 + 3:
            continue
        if abs(z) < 4:
            continue
        if rng.random() < 0.7:
            spruce(x, z, int(rng.integers(7, 12)))
        else:
            tree(x, z, "dark_oak_log", "dark_oak_leaves", int(rng.integers(5, 7)))
    for _ in range(200):
        x, z = int(rng.integers(10, 99)), int(rng.integers(-59, 59))
        g = ground(x, z)
        if get(x, g + 1, z) == "air" and get(x, g, z) in ("grass_block", "podzol", "moss_block"):
            put(x, g + 1, z, str(rng.choice(["fern", "short_grass", "large_fern", "dead_bush", "brown_mushroom", "sweet_berry_bush"])) if rng.random() < 0.5 else "fern")
    # 진영 바닥 평탄 (흙 · 포드졸)
    for x in range(WX0, WX1 + 1):
        for z in range(WZ0, WZ1 + 1):
            g = ground(x, z)
            if (x - 78) ** 2 / 18 ** 2 + (z + 30) ** 2 / 16 ** 2 < 1.0 and z < -12:
                continue                                      # 북동 굴 언덕은 그대로
            for y in range(FL + 1, g + 1):
                put(x, y, z, "air")
            put(x, FL, z, "podzol" if rng.random() < 0.4 else ("coarse_dirt" if rng.random() < 0.5 else "rooted_dirt"))
    for x in range(WX0, WX1 + 1):
        for z in range(-2, 3):
            put(x, FL, z, "mud" if abs(z) < 2 else "coarse_dirt")
    # 뾰족 통나무 울타리 (높낮이 다른 짙은 참나무 통나무 · 끝은 울타리로 뾰족하게)
    for x in range(WX0, WX1 + 1):
        for z in range(WZ0, WZ1 + 1):
            edge = x in (WX0, WX1) or z in (WZ0, WZ1)
            if not edge:
                continue
            if x == WX0 and -3 <= z <= 3:
                continue                                      # 늑대 굴 입구 (서쪽 가운데)
            if (x - 78) ** 2 / 18 ** 2 + (z + 30) ** 2 / 16 ** 2 < 0.8 and z <= WZ0:
                continue
            hh = 6 + int(2 * abs(math.sin(x * 1.7 + z * 2.3)))
            g = FL
            for y in range(g + 1, g + hh + 1):
                put(x, y, z, "dark_oak_log" if (x + z) % 3 else "stripped_dark_oak_log")
            put(x, g + hh + 1, z, "dark_oak_fence")
    # 입구 양옆 해골 망루 (블랙스톤)
    for cz in (-6, 6):
        for y in range(FL + 1, FL + 11):
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if max(abs(dx), abs(dz)) == 2:
                        put(WX0 + dx, y, cz + dz, "polished_blackstone_bricks" if (y - FL) % 4 else "blackstone")
                    else:
                        put(WX0 + dx, y, cz + dz, "air")
        box(WX0 - 2, FL + 11, cz - 2, WX0 + 2, FL + 11, cz + 2, "polished_blackstone")
        for dx in (-2, 2):
            for dz in (-2, 2):
                put(WX0 + dx, FL + 12, cz + dz, "polished_blackstone_wall")
                put(WX0 + dx, FL + 13, cz + dz, "soul_lantern")
        put(WX0 - 2, FL + 8, cz, "redstone_block")
    # 입구 위 다리 (해골 → 통나무)
    for z in range(-4, 5):
        put(WX0, FL + 9, z, "dark_oak_planks")
        put(WX0, FL + 10, z, "dark_oak_fence")
    # 굴 언덕 (북동) 입구 — 어두운 구멍 + 붉은 눈 2쌍
    cx_, cz_ = 72, -16
    for dz in range(-2, 3):
        for y in range(FL + 1, FL + 5):
            for dx in range(0, 10):
                if abs(dz) + max(0, y - FL - 3) <= 2:
                    put(cx_ + dx, y, cz_ - dx * 0 - 1 + dz, "air")
    for dz in range(-3, 4):
        put(cx_ - 1, FL + 5, cz_ - 1 + dz, "blackstone")
    put(cx_ + 6, FL + 3, cz_ - 2, "redstone_block")
    put(cx_ + 6, FL + 3, cz_, "redstone_block")
    # 늑대 굴 (진영 안 작은 굴 막사들 — 둥근 흙 · 이끼 언덕)
    def den(x, z, r):
        for dx in range(-r, r + 1):
            for dy in range(0, r + 1):
                for dz in range(-r, r + 1):
                    d = math.sqrt(dx * dx + (dy * 1.3) ** 2 + dz * dz)
                    if d <= r + 0.4:
                        put(x + dx, FL + dy, z + dz, "moss_block" if dy == r or d > r - 0.6 and rng.random() < 0.5 else "rooted_dirt")
        for dx in range(-r, 1):
            for dy in range(1, 3):
                put(x + dx, FL + dy, z, "air")
        for dx in range(-r + 1, r):
            for dz in range(-r + 1, r):
                for dy in range(1, r - 1):
                    if dx * dx + (dy * 1.3) ** 2 + dz * dz < (r - 1) ** 2:
                        put(x + dx, FL + dy, z + dz, "air")
        put(x, FL + 1, z, "campfire")
    for x, z in ((60, 18), (68, 24), (86, 20), (62, -20)):
        den(x, z, 4)
    # 모닥불 광장 (가운데 · 짐승 뼈 = 뼈 블록)
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            if math.hypot(dx, dz) < 4.5:
                put(70 + dx, FL, dz, "packed_mud" if math.hypot(dx, dz) > 2 else "blackstone")
    put(70, FL + 1, 0, "campfire")
    for a in range(0, 360, 60):
        put(70 + round(math.cos(math.radians(a)) * 4), FL + 1, round(math.sin(math.radians(a)) * 4), "bone_block")
    # 달의 제단 (동쪽 끝 · 늑대 본거지 = 늑대의 핵심)
    ex, ez = 86, 0
    for dx in range(-5, 6):
        for dz in range(-5, 6):
            d = math.hypot(dx, dz)
            if d <= 5.4:
                put(ex + dx, FL + 1, ez + dz, "polished_deepslate" if d > 3.5 else "deepslate_tiles")
            if d <= 3.6:
                put(ex + dx, FL + 2, ez + dz, "deepslate_bricks")
    for a in range(0, 360, 45):
        px, pz = ex + round(math.cos(math.radians(a)) * 5), ez + round(math.sin(math.radians(a)) * 5)
        hh = 4 + (a // 45) % 2 * 2
        for y in range(FL + 2, FL + 2 + hh):
            put(px, y, pz, "deepslate_tile_wall" if y > FL + 2 + hh - 2 else "chiseled_deepslate")
    for y in range(FL + 3, FL + 6):
        put(ex, y, ez, "crying_obsidian" if y < FL + 5 else "obsidian")
    put(ex, FL + 6, ez, "sea_lantern")       # 달빛 (제단 꼭대기)
    put(ex, FL + 7, ez, "end_rod")
    # 진영 안 횃불 · 영혼 등
    for x, z in ((56, -10), (56, 10), (66, -26), (80, 26), (92, -10), (92, 10)):
        put(x, FL + 1, z, "dark_oak_fence")
        put(x, FL + 2, z, "dark_oak_fence")
        put(x, FL + 3, z, "soul_lantern")
    # 양 진영 길가 등
    for x in range(-48, -10, 8):
        g = ground(x, 3)
        put(x, g + 1, 3, "oak_fence")
        put(x, g + 2, 3, "lantern")
    return v


def label(img, xy, text, col, font):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    x, y = xy
    tw = d.textlength(text, font=font)
    d.rounded_rectangle((x - tw / 2 - 10, y - 18, x + tw / 2 + 10, y + 18), 8, fill=(10, 14, 24))
    d.text((x - tw / 2, y - 15), text, font=font, fill=col)


def preview(path):
    import render as R
    from PIL import Image, ImageDraw, ImageFont
    v = build()
    pal = R.Palette(PAL)
    W, Hh = 1100, 620
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 26)
    fs = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 20)
    DAY = dict(sun=(-0.35, 0.8, -0.45), sun_col=(1.05, 0.97, 0.85), amb_col=(0.62, 0.66, 0.74),
               sky_top=(0.34, 0.55, 0.88), sky_hor=(0.80, 0.86, 0.94), fog_col=(0.78, 0.84, 0.92))
    shots = [
        ((CX - 2, FL + 120, CZ + 150), (CX, FL - 6, CZ), 52, "양과 늑대 — 1:1 공성전 맵 (서: 양의 하얀 목장 요새 · 가운데: 강과 다리 3개 · 동: 늑대의 어두운 숲 굴)"),
        ((CX - 38, FL + 30, CZ + 46), (CX - 74, FL + 4, CZ), 58, "양 진영 — 하얀 성벽 · 하늘색 망루 · 본성 안 황금 양털 제단 · 풍차 · 헛간 · 양 우리"),
        ((CX + 34, FL + 30, CZ + 44), (CX + 74, FL + 3, CZ), 58, "늑대 진영 — 뾰족 통나무 울타리 · 해골 망루 입구 · 굴 막사 · 모닥불 광장 · 달의 제단"),
        ((CX + 22, FL + 16, CZ + 26), (CX, FL + 5, CZ), 62, "가운데 — 강 위 넓은 다리와 무너진 망루 (서로 부딪히는 곳)"),
    ]
    out = Image.new("RGB", (W, Hh * (len(shots) + 1)))
    for i, (cam, tgt, fov, lab) in enumerate(shots):
        im = R.render(v, pal, W, Hh, cam, tgt, fov=fov, ss=2, fog_dist=700, **DAY)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, 44), fill=(12, 18, 32))
        d.text((14, 8), lab, font=fs, fill=(250, 235, 180))
        out.paste(im, (0, Hh * i))
    # 위에서 본 지도 (정사영) + 이름표
    im = R.render(v, pal, W, Hh, (CX + 0.01, FL + 140, CZ + 0.5), (CX, FL, CZ), ortho_scale=W / (NX * 1.04), ss=2, fog_dist=2000, **DAY)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 44), fill=(12, 18, 32))
    d.text((14, 8), "위에서 본 지도 (왼쪽 = 양 · 오른쪽 = 늑대 · 위 = 북)", font=fs, fill=(250, 235, 180))
    sc = W / (NX * 1.04)

    def px(x, z):
        return (W / 2 + x * sc, Hh / 2 + z * sc)
    label(im, px(-78, -14), "양 본성 (황금 양털)", (255, 240, 160), font)
    label(im, px(-71, 34), "양 진영", (240, 248, 255), font)
    label(im, px(0, -46), "북쪽 다리", (220, 230, 240), fs)
    label(im, px(0, 13), "가운데 다리 · 폐허 망루", (220, 230, 240), fs)
    label(im, px(0, 46), "남쪽 다리", (220, 230, 240), fs)
    label(im, px(86, -9), "늑대 달의 제단", (255, 160, 160), font)
    label(im, px(72, 36), "늑대 진영", (255, 200, 200), font)
    out.paste(im, (0, Hh * len(shots)))
    out.save(path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview(sys.argv[1] if len(sys.argv) > 1 else "sheepwolf.png")
