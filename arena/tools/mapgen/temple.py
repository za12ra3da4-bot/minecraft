"""중앙 대신전 + 광장 + 신성 수로 + 다리"""
import math

import numpy as np

from layout import *
from prims import Builder, stairs, slab, wall, DXZ, OPP, facing_to

cx, cz = C
FLOOR = G + 7          # 신전 바닥 블록 y (서는 곳 = G+8)
COL_Y = G + 8
COL_H = 14


def build_temple(b: Builder):
    plaza(b)
    moat(b)
    platform(b)
    peristyle(b)
    cella(b)
    altar(b)
    plaza_decor(b)
    decor_displays(b)


# ─────────────────────────────────────────────────────────────── 광장
def plaza(b):
    r = b.r
    y = G + 1
    for x in range(cx - PLAZA_R - 1, cx + PLAZA_R + 2):
        for z in range(cz - PLAZA_R - 1, cz + PLAZA_R + 2):
            dx, dz = x - cx, z - cz
            d = math.hypot(dx, dz)
            if d > PLAZA_R + 0.5:
                continue
            ang = (math.degrees(math.atan2(dz, dx)) + 360) % 45
            spoke = min(ang, 45 - ang) * math.pi / 180 * d < 1.2
            s = b.mix([("stone_bricks", 50), ("cracked_stone_bricks", 14), ("mossy_stone_bricks", 12), ("polished_andesite", 12), ("andesite", 6), ("cobblestone", 6)])
            if 20.5 <= d < 21.7 or 28.5 <= d < 29.7:
                s = b.mix([("polished_andesite", 7), ("smooth_stone", 3), ("andesite", 1)])
            elif PLAZA_R - 1.2 <= d:
                s = b.mix([("calcite", 6), ("polished_diorite", 3), ("mossy_cobblestone", 1)])
            elif spoke and d > 22:
                s = b.mix([("smooth_stone", 5), ("polished_diorite", 3), ("calcite", 2)])
            # 외곽은 풀이 먹어 들어온다
            if d > 29.8 and d < PLAZA_R - 1.2 and b.rand() < (d - 29.8) / 12:
                s = b.mix([("grass_block", 6), ("moss_block", 2), ("coarse_dirt", 2)])
            b.set(x, y, z, s)
            b.fill(x, y - 3, z, x, y - 1, z, "stone")
            b.air(x, y + 1, z, x, y + 8, z)


# ─────────────────────────────────────────────────────────────── 수로 + 다리
def moat(b):
    y = G + 1
    for x in range(cx - MOAT_OUT - 3, cx + MOAT_OUT + 4):
        for z in range(cz - MOAT_OUT - 3, cz + MOAT_OUT + 4):
            d = math.hypot(x - cx, z - cz)
            # 안쪽 부두벽
            if MOAT_IN - 1.5 <= d < MOAT_IN - 0.4:
                b.fill(x, G - 3, z, x, y, z, b.mix([("stone_bricks", 6), ("mossy_stone_bricks", 3), ("cracked_stone_bricks", 1)]))
                b.set(x, y, z, b.mix([("polished_andesite", 5), ("stone_bricks", 3)]))
            # 바깥 부두벽
            if MOAT_OUT + 0.4 <= d < MOAT_OUT + 1.6:
                gy = b.gy(x, z)
                top = max(y, gy)
                b.fill(x, G - 3, z, x, top, z, b.mix([("stone_bricks", 6), ("mossy_stone_bricks", 3), ("cracked_stone_bricks", 1)]))
                b.set(x, top, z, b.mix([("polished_andesite", 5), ("stone_bricks", 3)]))
    # 안쪽 난간 (군데군데 끊김)
    n = 0
    for i in range(720):
        a = i / 720 * 2 * math.pi
        x = round(cx + math.cos(a) * (MOAT_IN - 1)); z = round(cz + math.sin(a) * (MOAT_IN - 1))
        deg = math.degrees(a) % 45
        if min(deg, 45 - deg) < 9:
            continue  # 다리 자리
        if (i // 30) % 5 == 3:
            continue  # 끊긴 구간
        b.set(x, y + 1, z, wall("stone_brick"))
    for f in DXZ:
        grand_bridge(b, f)
    for k in (1, 3, 5, 7):
        ford(b, k * math.pi / 4)


def grand_bridge(b, f):
    """수로 대교: 폭 9, 가운데 아치 개구부, 양쪽 3단 계단, 난간 기둥 + 등불"""
    ux, uz = DXZ[f]
    top = G + 4                       # 다리 윗면 블록
    mid = (MOAT_IN + MOAT_OUT) / 2    # 46
    fo = f                            # 바깥을 향한 facing
    fi = OPP[f]

    def P(al, s):
        return (cx + ux * al + (s if ux == 0 else 0), cz + uz * al + (s if uz == 0 else 0))

    for al in range(MOAT_IN - 5, MOAT_OUT + 6):
        for s in range(-4, 5):
            x, z = P(al, s)
            edge = abs(s) == 4
            # 높이: 안쪽 계단 38~40, 바깥 계단 51~53
            if al <= MOAT_IN - 2:
                step = al - (MOAT_IN - 5)          # 0,1,2 → 계단
                h = G + 1 + step
                b.fill(x, G - 1, z, x, h - 1, z, "stone_bricks")
                b.set(x, h, z, stairs("stone_brick", fo) if not edge else b.mix([("stone_bricks", 3), ("polished_andesite", 1)]))
                if edge:
                    b.set(x, h + 1, z, wall("stone_brick"))
                b.air(x, h + (2 if edge else 1), z, x, h + 6, z)
                continue
            if al >= MOAT_OUT + 2:
                step = (MOAT_OUT + 5) - al
                h = G + 1 + step
                gy = b.gy(x, z)
                b.fill(x, min(gy, G - 1), z, x, h - 1, z, "stone_bricks")
                b.set(x, h, z, stairs("stone_brick", fi) if not edge else b.mix([("stone_bricks", 3), ("polished_andesite", 1)]))
                if edge:
                    b.set(x, h + 1, z, wall("stone_brick"))
                b.air(x, h + (2 if edge else 1), z, x, h + 6, z)
                continue
            # 다리 상판
            dd = abs(al - mid)
            deck = "polished_andesite" if abs(s) <= 1 else b.mix([("stone_bricks", 6), ("mossy_stone_bricks", 2), ("cracked_stone_bricks", 1)])
            if edge:
                deck = "stone_bricks"
            b.set(x, top, z, deck)
            b.air(x, top + 1, z, x, top + 6, z)
            # 아치 아랫면: 가운데 2칸 비고, 어깨는 거꾸로 계단
            if dd <= 1.5:
                under = top - 1
                b.set(x, under, z, "stone_bricks")
                for yy in range(G - 3, under):
                    b.set(x, yy, z, "water" if yy <= G else "air")
                b.set(x, top - 1, z, "chiseled_stone_bricks" if (dd < 0.6 and edge) else "stone_bricks")
            elif dd <= 2.5:
                b.set(x, top - 1, z, "stone_bricks")
                b.set(x, top - 2, z, stairs("stone_brick", fi if al < mid else fo, "top"))
                for yy in range(G - 3, top - 2):
                    b.set(x, yy, z, "water" if yy <= G else "air")
            elif dd <= 3.5:
                b.fill(x, top - 2, z, x, top - 1, z, "stone_bricks")
                b.set(x, G + 1, z, stairs("stone_brick", fi if al < mid else fo, "top"))
                for yy in range(G - 3, G + 1):
                    b.set(x, yy, z, "water")
            else:
                # 교대 (부두 위)
                b.fill(x, G - 3, z, x, top - 1, z, b.mix([("stone_bricks", 6), ("mossy_stone_bricks", 3)]))
            if edge:
                b.set(x, top + 1, z, wall("stone_brick"))
    # 난간 기둥 (양 끝 + 가운데) + 등불, 아치 머릿돌
    for al in (MOAT_IN - 1, int(mid), MOAT_OUT + 1):
        for s in (-4, 4):
            x, z = P(al, s)
            b.fill(x, top + 1, z, x, top + 2, z, "chiseled_stone_bricks")
            b.set(x, top + 3, z, "lantern[hanging=false,waterlogged=false]")
    # 다리 옆면 장식 띠
    for al in range(MOAT_IN - 1, MOAT_OUT + 2):
        for s in (-5, 5):
            x, z = P(al, s)
            if b.w.is_air(x, top, z) or b.w.get(x, top, z) == "water":
                b.set(x, top, z, stairs("stone_brick", facing_to(-(x - P(al, 0)[0]), -(z - P(al, 0)[1])), "top"))


def ford(b, a):
    """대각선: 무너진 옛 다리 잔해 + 징검돌"""
    ux, uz = math.cos(a), math.sin(a)
    px_, pz_ = -uz, ux
    rng = b.r
    # 잔해 교각 (양쪽 부두 옆)
    for r in (MOAT_IN + 0.8, MOAT_OUT - 0.8):
        for s in (-2.5, 2.5):
            x = round(cx + ux * r + px_ * s); z = round(cz + uz * r + pz_ * s)
            h = G + int(rng.integers(1, 4))
            b.fill(x, G - 3, z, x, h, z, b.mix([("stone_bricks", 4), ("mossy_stone_bricks", 4), ("cracked_stone_bricks", 2)]))
            if rng.random() < 0.6:
                b.set(x, h + 1, z, slab("mossy_stone_brick"))
    # 징검돌
    r = MOAT_IN - 0.2
    i = 0
    while r <= MOAT_OUT + 0.4:
        x = round(cx + ux * r); z = round(cz + uz * r)
        if b.w.get(x, G, z) == "water" or i == 0:
            b.fill(x, G - 3, z, x, G + 1, z, b.mix([("mossy_stone_bricks", 3), ("mossy_cobblestone", 2), ("stone_bricks", 2)]))
            b.set(x, G + 1, z, b.mix([("mossy_cobblestone", 3), ("stone_bricks", 2), ("chiseled_stone_bricks", 1)]))
        r += 1.45
        i += 1
    # 물에 빠진 잔해
    for k in range(5):
        r = rng.uniform(MOAT_IN + 1, MOAT_OUT - 1)
        s = rng.uniform(-4, 4)
        x = round(cx + ux * r + px_ * s); z = round(cz + uz * r + pz_ * s)
        if b.w.get(x, G, z) == "water" and abs(s) > 1.5:
            b.set(x, G - 2, z, b.mix([("mossy_stone_bricks", 2), ("cracked_stone_bricks", 1)]))
            b.set(x, G - 1, z, stairs("mossy_stone_brick", ["north", "east", "south", "west"][k % 4]))


# ─────────────────────────────────────────────────────────────── 기단
def platform(b):
    tiers = [(19, G + 1, G + 3, [("stone_bricks", 6), ("cracked_stone_bricks", 2), ("mossy_stone_bricks", 2)]),
             (18, G + 4, G + 5, [("quartz_bricks", 6), ("calcite", 3), ("polished_diorite", 1)]),
             (17, G + 6, FLOOR, [("smooth_quartz", 8), ("quartz_bricks", 2)])]
    for half, y0, y1, mats in tiers:
        for x in range(cx - half, cx + half + 1):
            for z in range(cz - half, cz + half + 1):
                for y in range(y0, y1 + 1):
                    b.set(x, y, z, b.mix(mats))
    # 층 모서리 장식띠 (상단 반 블록 돌출)
    for half, yy in ((19, G + 3), (18, G + 5)):
        for i in range(-half, half + 1):
            for (x, z) in ((cx + i, cz - half), (cx + i, cz + half), (cx - half, cz + i), (cx + half, cz + i)):
                b.set(x, yy, z, b.mix([("polished_andesite", 3), ("calcite", 2)]) if half == 19 else b.mix([("chiseled_quartz_block", 1), ("quartz_bricks", 4)]))
    # 바닥 무늬
    for x in range(cx - 17, cx + 18):
        for z in range(cz - 17, cz + 18):
            dx, dz = x - cx, z - cz
            m = max(abs(dx), abs(dz))
            if m >= 15:
                s = b.mix([("quartz_bricks", 6), ("chiseled_quartz_block", 1)])
            elif m <= 9:
                s = "polished_diorite" if (dx + dz) % 2 == 0 else "calcite"
                d = math.hypot(dx, dz)
                if 6.5 <= d < 7.5:
                    s = "gold_block" if (int(math.degrees(math.atan2(dz, dx))) // 15) % 2 == 0 else "smooth_quartz"
            else:
                s = "smooth_quartz" if (dx % 4 and dz % 4) else "quartz_bricks"
            if b.rand() < 0.07:
                s = b.mix([("andesite", 2), ("cobblestone", 1), ("mossy_cobblestone", 1), ("gravel", 1)])
            b.set(x, FLOOR, z, s)
    # 대계단 4면
    for f, (ux, uz) in DXZ.items():
        for k in range(1, 7):          # k=6 이 가장 높은 계단
            y = G + 1 + k
            dist = 17 + (7 - k)
            for s in range(-5, 6):
                x = cx + ux * dist + (s if ux == 0 else 0)
                z = cz + uz * dist + (s if uz == 0 else 0)
                b.fill(x, G + 1, z, x, y - 1, z, "stone_bricks")
                b.set(x, y, z, stairs("quartz" if k > 2 else "stone_brick", OPP[f]))
                b.air(x, y + 1, z, x, y + 6, z)
            # 계단 옆 볼 (cheek)
            for s in (-6, 6):
                x = cx + ux * dist + (s if ux == 0 else 0)
                z = cz + uz * dist + (s if uz == 0 else 0)
                b.fill(x, G + 1, z, x, y + 1, z, b.mix([("quartz_bricks", 4), ("calcite", 1)]))
                b.set(x, y + 2, z, slab("quartz") if k < 6 else "chiseled_quartz_block")
        # 계단 아래 받침 + 화로
        for s in (-6, 6):
            x = cx + ux * 24 + (s if ux == 0 else 0)
            z = cz + uz * 24 + (s if uz == 0 else 0)
            b.fill(x, G + 2, z, x, G + 3, z, "chiseled_quartz_block")
            b.set(x, G + 4, z, "gold_block")
            b.set(x, G + 5, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


# ─────────────────────────────────────────────────────────────── 열주 회랑
def col_positions():
    ps = []
    for i in (-15, -10, -5, 0, 5, 10, 15):
        for j in (-15, 15):
            ps.append((i, j)); ps.append((j, i))
    ps = sorted(set(ps))
    return [p for p in ps if not (p[0] == 0 or p[1] == 0)]


def peristyle(b):
    rng = b.r
    intact = {}
    for (dx, dz) in col_positions():
        broken = None
        # 동/서쪽 일부 무너짐 → 사선과 엄폐가 생긴다
        roll = rng.random()
        if (dx > 0 and dz > 0 and roll < 0.55) or (dx < 0 and dz < 0 and roll < 0.45) or roll < 0.18:
            broken = int(rng.integers(2, 9))
        b.column(cx + dx, cz + dz, COL_Y, COL_H, "quartz", broken=broken)
        intact[(dx, dz)] = broken is None
        if broken is not None and broken < 6:
            # 무너진 기둥 조각이 바닥에 누워 있다
            ax = "x" if abs(dz) == 15 else "z"
            ox = (int(np.sign(dx)) * 3 if ax == "z" else 0)
            oz = (int(np.sign(dz)) * 3 if ax == "x" else 0)
            if abs(dx) == 15 and ax == "z":
                ox = int(np.sign(dx)) * 5
            if abs(dz) == 15 and ax == "x":
                oz = int(np.sign(dz)) * 5
            L = int(rng.integers(4, 8))
            if ax == "x":
                b.fallen_column(cx + dx - L // 2, G + 2 if abs(dz) + 5 > 17 else COL_Y, cz + dz + oz, L, "x")
            else:
                b.fallen_column(cx + dx + ox, G + 2 if abs(dx) + 5 > 17 else COL_Y, cz + dz - L // 2, L, "z")
    # 엔타블러처: 양쪽 기둥이 멀쩡한 구간만
    top = COL_Y + COL_H
    sides = []
    for j in (-15, 15):
        sides.append([(i, j) for i in (-15, -10, -5, 0, 5, 10, 15)])
        sides.append([(j, i) for i in (-15, -10, -5, 0, 5, 10, 15)])
    for seq in sides:
        for a, c in zip(seq, seq[1:]):
            ok_a = intact.get(a, True if (a[0] == 0 or a[1] == 0) else False)
            ok_c = intact.get(c, True if (c[0] == 0 or c[1] == 0) else False)
            if a[0] == 0 or a[1] == 0:
                ok_a = intact.get((a[0] - 5 if a[1] in (-15, 15) else a[0], a[1] - 5 if a[0] in (-15, 15) else a[1]), False) and intact.get((a[0] + 5 if a[1] in (-15, 15) else a[0], a[1] + 5 if a[0] in (-15, 15) else a[1]), False)
            if c[0] == 0 or c[1] == 0:
                ok_c = ok_a
            if not (ok_a and ok_c) or rng.random() < 0.12:
                continue
            x0, z0 = cx + a[0], cz + a[1]
            x1, z1 = cx + c[0], cz + c[1]
            horiz = (a[1] == c[1])
            for t in range(0, 6):
                x = x0 + (t if horiz else 0)
                z = z0 + (0 if horiz else t)
                for w_ in (-1, 0, 1):
                    xx = x + (0 if horiz else w_)
                    zz = z + (w_ if horiz else 0)
                    b.set(xx, top + 1, zz, "smooth_quartz")
                    if w_ == 0 or t % 5 == 0:
                        b.set(xx, top + 2, zz, "chiseled_quartz_block" if t % 5 == 0 else ("blue_terracotta" if t % 2 else "gold_block"))
                    else:
                        b.set(xx, top + 2, zz, "quartz_bricks")
                # 코니스 (바깥으로 돌출)
                if horiz:
                    oz = z + (2 if a[1] > 0 else -2)
                    b.set(x, top + 3, oz, stairs("quartz", "north" if a[1] > 0 else "south", "top"))
                    b.set(x, top + 3, z + (1 if a[1] > 0 else -1), "smooth_quartz")
                    b.set(x, top + 3, z, slab("smooth_quartz"))
                else:
                    ox = x + (2 if a[0] > 0 else -2)
                    b.set(ox, top + 3, z, stairs("quartz", "west" if a[0] > 0 else "east", "top"))
                    b.set(x + (1 if a[0] > 0 else -1), top + 3, z, "smooth_quartz")
                    b.set(x, top + 3, z, slab("smooth_quartz"))
    # 박공 (북쪽 온전, 남쪽 절반 붕괴)
    for sgn, keep in ((-1, 1.0), (1, 0.55)):
        zf = cz + sgn * 16
        for i in range(-16, 17):
            hgt = int((16 - abs(i)) / 2)
            if keep < 1.0 and i > 16 * (keep * 2 - 1):
                hgt = max(0, hgt - int(rng.integers(3, 8)))
            for k in range(hgt + 1):
                y = top + 4 + k
                s = "quartz_bricks"
                if k == hgt:
                    s = stairs("quartz", "east" if i < 0 else "west") if i != 0 else "chiseled_quartz_block"
                b.set(cx + i, y, zf, s)
            # 지붕 (산화 구리)
            depth = 6 if keep == 1.0 else 3
            for dd in range(1, depth + 1):
                z = zf - sgn * dd
                if rng.random() < 0.15 * dd:
                    continue
                y = top + 4 + hgt
                if hgt > 0:
                    b.set(cx + i, y, z, stairs("weathered_cut_copper", "east" if i < 0 else "west") if i != 0 else "weathered_cut_copper")
                    b.set(cx + i, y - 1, z, "weathered_cut_copper")
    # 무너진 지붕 조각 (바닥 위)
    for _ in range(9):
        x = cx + int(rng.integers(-13, 14)); z = cz + int(rng.integers(-13, 14))
        if max(abs(x - cx), abs(z - cz)) <= 10:
            continue
        b.rubble(x, 0, z, 1, [("weathered_cut_copper", 3), (stairs("weathered_cut_copper", "north"), 2), ("quartz_bricks", 3), (slab("smooth_quartz"), 2)])


# ─────────────────────────────────────────────────────────────── 내실 (cella)
def cella(b):
    rng = b.r
    y0 = COL_Y
    H = 10
    half = 9
    prof = {}
    for i in range(-half, half + 1):
        for (x, z, side) in ((cx + i, cz - half, "n"), (cx + i, cz + half, "s"), (cx - half, cz + i, "w"), (cx + half, cz + i, "e")):
            prof[(x, z)] = (i, side)
    # 붕괴 윤곽
    for (x, z), (i, side) in prof.items():
        h = H
        # 북동·남서 모서리는 크게 무너짐
        if (side in ("n", "e") and ((side == "n" and i > 3) or (side == "e" and i < -3))):
            h = int(np.clip(2 + rng.integers(0, 3) + abs(i - (6 if side == "n" else -6)) // 2, 1, H))
        if (side in ("s", "w") and ((side == "s" and i < -4) or (side == "w" and i > 4))):
            h = int(np.clip(1 + rng.integers(0, 3), 1, H))
        if rng.random() < 0.1:
            h = max(1, h - int(rng.integers(1, 4)))
        door = abs(i) <= 2
        for k in range(h):
            y = y0 + k
            if door and k < 7:
                continue
            s = b.mix([("quartz_bricks", 7), ("smooth_quartz", 2), ("calcite", 1)])
            if k == 0:
                s = "polished_diorite"
            if k in (4,) :
                s = "chiseled_quartz_block" if abs(i) % 3 == 0 else s
            if abs(i) == half:
                s = "quartz_pillar[axis=y]"
            b.set(x, y, z, s)
        if door and h > 7:
            b.set(x, y0 + 7, z, "chiseled_quartz_block" if abs(i) == 0 else "smooth_quartz")
        if h == H:
            b.set(x, y0 + H, z, slab("smooth_quartz"))
    # 문설주 장식 + 금 등
    for f, (ux, uz) in DXZ.items():
        for s in (-3, 3):
            x = cx + ux * half + (s if ux == 0 else 0)
            z = cz + uz * half + (s if uz == 0 else 0)
            b.fill(x, y0, z, x, y0 + 7, z, "quartz_pillar[axis=y]")
            ox, oz = x + ux, z + uz
            b.set(ox, y0 + 5, oz, "lantern[hanging=false,waterlogged=false]")
            b.set(ox, y0 + 4, oz, "chiseled_quartz_block")
    # 무너진 잔해
    for (x, z) in ((cx + 9, cz - 9), (cx - 9, cz + 9)):
        b.rubble(x + int(np.sign(x - cx)) * 2, 0, z + int(np.sign(z - cz)) * 2, 3,
                 [("quartz_bricks", 5), (slab("smooth_quartz"), 3), ("calcite", 1), (stairs("quartz", "north"), 1)])


# ─────────────────────────────────────────────────────────────── 중앙 제단 (거점)
def altar(b):
    y = COL_Y
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            d = math.hypot(x - cx, z - cz)
            if d <= 3.6:
                b.set(x, y, z, "chiseled_quartz_block" if d > 2.2 else "iron_block")
            elif d <= 4.6:
                f = facing_to(cx - x, cz - z)
                b.set(x, y, z, stairs("quartz", f))
    b.set(cx, y + 1, cz, "beacon")
    b.set(cx, y + 2, cz, "white_stained_glass")
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        b.set(cx + dx, y + 1, cz + dz, "gold_block")
        b.set(cx + dx, y + 2, cz + dz, "end_rod[facing=up]")
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        b.set(cx + dx, y + 1, cz + dz, stairs("quartz", facing_to(-dx, 0), "bottom"))
    # 네 모서리 화로
    for dx, dz in ((-6, -6), (6, -6), (-6, 6), (6, 6)):
        b.brazier(cx + dx, y, cz + dz, tall=1, mat="polished_blackstone")
    b.w.mark("temple_core", cx + 0.5, y + 1, cz + 0.5, radius=8)


# ─────────────────────────────────────────────────────────────── 광장 장식
def plaza_decor(b):
    rng = b.r
    y = G + 2
    # 둥근 열주 잔해 (반지름 31)
    n = 40
    for i in range(n):
        a = i / n * 2 * math.pi
        deg = math.degrees(a) % 45
        if min(deg, 45 - deg) < 8:
            continue
        x = round(cx + math.cos(a) * 31); z = round(cz + math.sin(a) * 31)
        roll = rng.random()
        if roll < 0.2:
            continue
        h = 6 if roll > 0.5 else int(rng.integers(1, 5))
        b.set(x, y - 1, z, "chiseled_stone_bricks")
        b.fill(x, y, z, x, y + h - 1, z, "quartz_pillar[axis=y]")
        if h == 6:
            b.set(x, y + h, z, "smooth_quartz")
            # 들보 (다음 기둥까지)
            if rng.random() < 0.6:
                a2 = (i + 1) / n * 2 * math.pi
                x2 = round(cx + math.cos(a2) * 31); z2 = round(cz + math.sin(a2) * 31)
                steps = max(abs(x2 - x), abs(z2 - z))
                for s in range(1, steps):
                    bx = round(x + (x2 - x) * s / steps); bz = round(z + (z2 - z) * s / steps)
                    b.set(bx, y + h, bz, slab("smooth_quartz", "top"))
        else:
            b.set(x, y + h, z, slab("quartz"))
    # 대로 입구 대형 화로
    for k in range(4):
        a = k * math.pi / 2
        ux, uz = math.cos(a), math.sin(a)
        for s in (-1, 1):
            x = round(cx + ux * 34 - uz * s * 6); z = round(cz + uz * 34 + ux * s * 6)
            b.big_brazier(x, y, z)
    # 누운 기둥 · 잔해 (엄폐물)
    for k in range(8):
        a = (k + 0.5) * math.pi / 4 + rng.uniform(-0.15, 0.15)
        d = rng.uniform(24, 29)
        x = round(cx + math.cos(a) * d); z = round(cz + math.sin(a) * d)
        if k % 2 == 0:
            b.fallen_column(x, y, z, int(rng.integers(4, 7)), "x" if rng.random() < 0.5 else "z")
        else:
            b.rubble(x, 0, z, 2, [("quartz_bricks", 3), ("stone_bricks", 3), ("cracked_stone_bricks", 2), (slab("stone_brick"), 2)])
    # 석상 받침 (리소스팩 석상이 올라간다)
    for k in range(4):
        a = (k + 0.5) * math.pi / 2
        x = round(cx + math.cos(a) * 25.5); z = round(cz + math.sin(a) * 25.5)
        b.fill(x - 1, y - 1, z - 1, x + 1, y + 1, z + 1, "quartz_bricks")
        b.fill(x - 1, y + 2, z - 1, x + 1, y + 2, z + 1, "smooth_quartz")
        for f, (ux, uz) in DXZ.items():
            for s in (-1, 0, 1):
                b.set(x + ux * 2 + (s if ux == 0 else 0), y - 1, z + uz * 2 + (s if uz == 0 else 0), stairs("quartz", OPP[f]))
        b.w.display("statue", x + 0.5, y + 3, z + 0.5, model="hoplite", yaw=math.degrees(math.atan2(-(x - cx), (z - cz))) , scale=3.0)
        b.w.mark(f"temple_statue_{k}", x + 0.5, y + 3, z + 0.5)


def decor_displays(b):
    w = b.w
    y = COL_Y
    w.display("item", cx + 0.5, y + 13, cz + 0.5, model="deco/zeus_bolt", scale=4.0, spin=True, glow=True, tag="bg_spin")
    w.display("item", cx + 0.5, y + 9, cz + 0.5, model="deco/rune_ring_big", scale=9.0, spin=True, tilt=12, tag="bg_spin")
    w.display("item", cx + 0.5, y + 11, cz + 0.5, model="deco/rune_ring", scale=6.0, spin=True, tilt=-18, tag="bg_spin")
    w.display("item", cx + 0.5, y + 0.03, cz + 0.5, model="deco/cap_ring_neutral", scale=17.0, flat=True, tag="bg_cap_temple")
    # 박공 부조 (제우스 독수리)
    for sgn in (-1, 1):
        w.display("item", cx + 0.5, COL_Y + COL_H + 6.5, cz + sgn * 16.5 + sgn * 0.02 + 0.5, model="deco/eagle_relief", scale=5.0,
                  yaw=0 if sgn > 0 else 180)
    # 내실 벽 걸개 (올림포스 문장)
    for f, (ux, uz) in DXZ.items():
        for s in (-6, 6):
            x = cx + ux * 9.5 + (s if ux == 0 else 0) + 0.5 + ux * 0.08
            z = cz + uz * 9.5 + (s if uz == 0 else 0) + 0.5 + uz * 0.08
            yaw = {"north": 180, "south": 0, "east": 270, "west": 90}[f]
            w.display("item", x - ux * 0.0, y + 5.5, z, model="deco/banner_olympus", scale=3.2, yaw=yaw)
