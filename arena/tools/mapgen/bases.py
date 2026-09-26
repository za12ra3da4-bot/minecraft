"""팀 본진: 고원 위 성채 — 옹벽, 성벽+총안, 성문 망루 3개, 스폰 신전, 팀색 비콘, 직업 제단, 막사"""
import math

import numpy as np

from layout import *
from prims import Builder, stairs, slab, wall, DXZ, OPP, facing_to

WALL_R = 21.0
Y = BASE_H             # 고원 윗면 블록


def build_bases(b: Builder):
    for t in TEAM_ORDER:
        build_base(b, t)


def frame(t):
    B = team_base(t)
    d = TEAMS[t][0]
    f = (-d[0], -d[1])           # 앞 = 중앙 방향
    r = (-f[1], f[0])            # 오른쪽
    def at(fw, rt):
        return (B[0] + f[0] * fw + r[0] * rt, B[1] + f[1] * fw + r[1] * rt)
    return B, f, r, at


def build_base(b, t):
    B, f, r, at = frame(t)
    col = TEAMS[t][3]
    wool = f"{col}_wool"
    terr = f"{col}_terracotta"
    conc = f"{col}_concrete"
    glass = f"{col}_stained_glass"
    rng = b.r
    gate_angles = [0, 50, -50]
    fwd_ang = math.atan2(f[1], f[0])

    def ang_of(x, z):
        a = math.atan2(z - B[1], x - B[0]) - fwd_ang
        return (math.degrees(a) + 540) % 360 - 180

    def in_gate(x, z, width_deg=13):
        a = ang_of(x, z)
        return any(abs(a - g) < width_deg for g in gate_angles)

    # ── 옹벽 (고원 가장자리)
    for x in range(int(B[0] - BASE_R - 3), int(B[0] + BASE_R + 4)):
        for z in range(int(B[1] - BASE_R - 3), int(B[1] + BASE_R + 4)):
            d = math.hypot(x - B[0], z - B[1])
            if BASE_R - 1.2 <= d < BASE_R + 1.0 and not in_gate(x, z, 16):
                g = b.gy(x, z)
                lo = min(g, G) - 1
                for y in range(lo, Y + 1):
                    s = b.mix([("stone_bricks", 6), ("mossy_stone_bricks", 3), ("cracked_stone_bricks", 1)])
                    if y == Y:
                        s = "polished_andesite"
                    b.set(x, y, z, s)
            # 안쪽 바닥 포장
            if d < WALL_R - 1.5:
                gy = Y
                s = b.mix([("stone_bricks", 5), ("polished_andesite", 3), ("andesite", 1), ("cracked_stone_bricks", 1)])
                if d > 9 and b.rand() < 0.25:
                    s = b.mix([("grass_block", 3), ("coarse_dirt", 2), ("gravel", 1)])
                b.set(x, gy, z, s)
                b.air(x, gy + 1, z, x, gy + 12, z)
    # ── 성벽 (반지름 21~22, 높이 5, 총안)
    for x in range(int(B[0] - WALL_R - 2), int(B[0] + WALL_R + 3)):
        for z in range(int(B[1] - WALL_R - 2), int(B[1] + WALL_R + 3)):
            d = math.hypot(x - B[0], z - B[1])
            if not (WALL_R - 0.8 <= d < WALL_R + 1.0):
                continue
            if in_gate(x, z):
                continue
            for k in range(1, 6):
                s = b.mix([("stone_bricks", 7), ("mossy_stone_bricks", 2), ("cracked_stone_bricks", 1)])
                if k == 3:
                    s = terr
                b.set(x, Y + k, z, s)
            # 총안: 바깥 줄만 번갈아 솟음
            if d >= WALL_R + 0.1:
                if (x + z) % 2 == 0:
                    b.set(x, Y + 6, z, "stone_bricks")
                    b.set(x, Y + 7, z, slab("stone_brick"))
                else:
                    b.set(x, Y + 6, z, slab("stone_brick"))
            else:
                b.set(x, Y + 5, z, "polished_andesite")
    # 성벽 안쪽 걷는 발판 + 계단 (측면 두 곳)
    for side in (-1, 1):
        for k in range(5):
            fw, rt = -2 - k, side * (WALL_R - 2)
            x, z = at(fw, rt)
            x, z = round(x), round(z)
            b.fill(x, Y + 1, z, x, Y + k, z, "stone_bricks") if k > 0 else None
            b.set(x, Y + k + 1, z, stairs("stone_brick", facing_to(-f[0], -f[1])))
    # ── 성문 망루 (문마다 양쪽)
    for g in gate_angles:
        a = fwd_ang + math.radians(g)
        ux, uz = math.cos(a), math.sin(a)
        for s in (-1, 1):
            px = B[0] + ux * WALL_R - uz * s * 5.5
            pz = B[1] + uz * WALL_R + ux * s * 5.5
            tower(b, round(px), round(pz), Y + 1, 9 if g == 0 else 7, terr, t, g == 0)
        # 문 위 아치 (정문만)
        if g == 0:
            for k in range(-3, 4):
                x = round(B[0] + ux * WALL_R - uz * k); z = round(B[1] + uz * WALL_R + ux * k)
                for dd in (0, 1):
                    xx, zz = round(x + ux * dd * 0.9), round(z + uz * dd * 0.9)
                    b.fill(xx, Y + 6, zz, xx, Y + 8, zz, "stone_bricks")
                    b.set(xx, Y + 7, zz, terr)
                    if abs(k) == 3:
                        b.set(xx, Y + 5, zz, stairs("stone_brick", "north", "top"))
            b.w.display("item", B[0] + ux * (WALL_R + 1.1) + 0.5, Y + 7.5, B[1] + uz * (WALL_R + 1.1) + 0.5,
                        model=f"deco/crest_{t}", scale=2.4, yaw=math.degrees(math.atan2(-ux, uz)))
        # 문 앞 화로
        for s in (-1, 1):
            px = round(B[0] + ux * (WALL_R + 3) - uz * s * 4)
            pz = round(B[1] + uz * (WALL_R + 3) + ux * s * 4)
            if abs(b.gy(px, pz) - Y) <= 2:
                b.brazier(px, b.gy(px, pz) + 1, pz, tall=2)
    # ── 뒤·옆 망루
    for g in (180, 115, -115):
        a = fwd_ang + math.radians(g)
        px = B[0] + math.cos(a) * (WALL_R + 0.5)
        pz = B[1] + math.sin(a) * (WALL_R + 0.5)
        tower(b, round(px), round(pz), Y + 1, 11 if g == 180 else 9, terr, t, False)

    # ── 스폰 신전 (뒤쪽)
    sx, sz = at(-11, 0)
    shrine(b, round(sx), round(sz), f, r, t, glass, terr)
    # 스폰 지점
    for k, (fw, rt) in enumerate([(-5, 0), (-5, -3), (-5, 3), (-3, -5), (-3, 5), (-6, -6), (-6, 6)]):
        x, z = at(fw, rt)
        b.w.mark(f"base_{t}_spawn_{k}", round(x) + 0.5, Y + 1, round(z) + 0.5, yaw=math.degrees(math.atan2(-f[0], f[1])))
    b.w.mark(f"base_{t}", B[0] + 0.5, Y + 1, B[1] + 0.5, radius=WALL_R + 2)

    # ── 광장 중앙 문장 모자이크
    cxm, czm = at(2, 0)
    for x in range(round(cxm) - 5, round(cxm) + 6):
        for z in range(round(czm) - 5, round(czm) + 6):
            d = math.hypot(x - cxm, z - czm)
            if d <= 5.2:
                s = "polished_andesite"
                if 3.6 <= d <= 5.2:
                    s = conc
                if 2.2 <= d < 3.6:
                    s = "smooth_quartz"
                if d < 2.2:
                    s = "gold_block" if d < 1 else conc
                b.set(x, Y, z, s)
    # ── 직업 제단 3개 (Skript 가 상호작용 엔티티를 올린다)
    for k, rt in enumerate((-6, 0, 6)):
        x, z = at(7, rt)
        x, z = round(x), round(z)
        b.set(x, Y + 1, z, "chiseled_stone_bricks")
        b.set(x, Y + 2, z, slab("smooth_stone"))
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            b.set(x + dx, Y + 1, z + dz, stairs("stone_brick", facing_to(-dx, -dz)))
        b.w.mark(f"base_{t}_class_{k}", x + 0.5, Y + 2.5, z + 0.5)
    # ── 막사 천막 2동 + 소품
    for side in (-1, 1):
        x, z = at(-1, side * 12)
        tent(b, round(x), round(z), f, wool, t)
        x2, z2 = at(4, side * 13)
        props(b, round(x2), round(z2))
    # 우물
    x, z = at(-2, -7)
    well(b, round(x), round(z))
    # 팀 깃발 (리소스팩 천)
    for rt in (-9, 9):
        x, z = at(8, rt)
        x, z = round(x), round(z)
        b.fill(x, Y + 1, z, x, Y + 6, z, "spruce_fence")
        b.set(x, Y + 7, z, "lantern[hanging=false,waterlogged=false]")
        b.w.display("item", x + 0.5, Y + 5.2, z + 0.5, model=f"deco/flag_{t}", scale=2.6, yaw=math.degrees(math.atan2(-f[0], f[1])), sway=True)


def tower(b, x, z, y0, h, terr, t, gate):
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            corner = abs(dx) == 2 and abs(dz) == 2
            gy = b.gy(x + dx, z + dz)
            b.fill(x + dx, min(gy, y0 - 1), z + dz, x + dx, y0 - 1, z + dz, "stone_bricks")
            for k in range(h):
                s = "polished_andesite" if corner else b.mix([("stone_bricks", 7), ("mossy_stone_bricks", 2), ("cracked_stone_bricks", 1)])
                if k in (3, h - 2) and not corner:
                    s = terr
                if (abs(dx) < 2 and abs(dz) < 2) and k > 0:
                    s = "air"
                if k == 5 and not corner and (dx == 0 or dz == 0) and (abs(dx) == 2 or abs(dz) == 2):
                    s = "air"   # 창
                b.set(x + dx, y0 + k, z + dz, s)
    # 망루 바닥 + 흉벽
    b.fill(x - 2, y0 + h - 1, z - 2, x + 2, y0 + h - 1, z + 2, "spruce_planks")
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if max(abs(dx), abs(dz)) == 3:
                b.set(x + dx, y0 + h - 1, z + dz, stairs("stone_brick", facing_to(dx, dz) if abs(dx) != abs(dz) else facing_to(dx, 0), "top"))
                if (dx + dz) % 2 == 0:
                    b.set(x + dx, y0 + h, z + dz, "stone_brick_wall")
    # 사다리 대신 안쪽 나선 계단 흉내: 망루 안 계단 블록
    for k in range(h - 1):
        pts = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
        dx, dz = pts[k % 8]
        b.set(x + dx, y0 + k, z + dz, stairs("spruce", facing_to(pts[(k + 1) % 8][0] - dx, pts[(k + 1) % 8][1] - dz)))
    # 지붕: 기둥 네 개 위 계단식 뾰족 지붕 + 팀 깃발
    col = TEAMS[t][3]
    for dx, dz in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        b.fill(x + dx, y0 + h, z + dz, x + dx, y0 + h + 2, z + dz, "dark_oak_log[axis=y]")
    ry = y0 + h + 3
    for k in range(4):
        half = 3 - k
        for dx in range(-half, half + 1):
            for dz in range(-half, half + 1):
                if max(abs(dx), abs(dz)) != half:
                    continue
                if half == 0:
                    b.set(x, ry + k, z, f"{col}_wool")
                elif abs(dx) == abs(dz):
                    b.set(x + dx, ry + k, z + dz, "deepslate_tiles")
                else:
                    b.set(x + dx, ry + k, z + dz, stairs("deepslate_tile", facing_to(-dx, -dz)))
        if k == 0:
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    if max(abs(dx), abs(dz)) == 3 and (dx + dz) % 2 == 0 and abs(dx) != abs(dz):
                        b.set(x + dx, ry - 1, z + dz, f"{col}_wool")
    b.fill(x, ry + 4, z, x, ry + 6, z, "dark_oak_fence")
    b.w.display("item", x + 0.5, ry + 5.6, z + 0.5, model=f"deco/flag_{t}", scale=1.8, yaw=0, sway=True)


def shrine(b, x, z, f, r, t, glass, terr):
    """스폰 신전: 계단 기단 + 기둥 6 + 박공 지붕 + 팀색 비콘"""
    y = Y
    fwf = facing_to(f[0], f[1])
    hw, hd = 5, 4          # 반 너비(좌우), 반 깊이(앞뒤)

    def P(fw, rt):
        return (round(x + f[0] * fw + r[0] * rt), round(z + f[1] * fw + r[1] * rt))

    for fw in range(-hd, hd + 1):
        for rt in range(-hw, hw + 1):
            px, pz = P(fw, rt)
            b.set(px, y + 1, pz, "smooth_quartz" if abs(rt) < hw and abs(fw) < hd else "quartz_bricks")
            b.air(px, y + 2, pz, px, y + 10, pz)
    for rt in range(-hw, hw + 1):
        px, pz = P(hd + 1, rt)
        b.set(px, y + 1, pz, stairs("quartz", OPP[fwf]))
    for fw in (-hd + 1, hd - 1):
        for rt in (-hw + 1, 0, hw - 1):
            if fw == hd - 1 and rt == 0:
                continue
            px, pz = P(fw, rt)
            b.fill(px, y + 2, pz, px, y + 6, pz, "quartz_pillar[axis=y]")
            b.set(px, y + 7, pz, "chiseled_quartz_block")
    for fw in range(-hd, hd + 1):
        for rt in range(-hw, hw + 1):
            px, pz = P(fw, rt)
            b.set(px, y + 8, pz, "smooth_quartz")
    # 뒷벽
    for rt in range(-hw + 1, hw):
        px, pz = P(-hd + 1, rt)
        b.fill(px, y + 2, pz, px, y + 7, pz, "quartz_bricks")
        b.set(px, y + 4, pz, terr)
    # 박공 지붕 (좌우로 경사)
    for k in range(4):
        for fw in range(-hd, hd + 1):
            for rt in (-hw + k, hw - k):
                px, pz = P(fw, rt)
                side = facing_to(r[0], r[1]) if rt < 0 else facing_to(-r[0], -r[1])
                b.set(px, y + 9 + k, pz, stairs("dark_prismarine" if False else "deepslate_tile", side))
            if k == 3:
                for rt in range(-hw + 4, hw - 3):
                    px, pz = P(fw, rt)
                    b.set(px, y + 9 + k, pz, "deepslate_tiles")
        for rt in range(-hw + k + 1, hw - k):
            for fw in (-hd, hd):
                px, pz = P(fw, rt)
                b.set(px, y + 9 + k, pz, "quartz_bricks" if k < 3 else "chiseled_quartz_block")
    # 비콘: 신전 앞 (지붕 밖)
    bx, bz = P(hd + 3, 0)
    b.fill(bx - 1, y, bz - 1, bx + 1, y, bz + 1, "iron_block")
    b.set(bx, y + 1, bz, "beacon")
    b.set(bx, y + 2, bz, glass)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        b.set(bx + dx, y + 1, bz + dz, "chiseled_quartz_block")
        b.set(bx + dx, y + 2, bz + dz, "soul_lantern[hanging=false,waterlogged=false]" if False else "lantern[hanging=false,waterlogged=false]")
    b.w.mark(f"base_{t}_beacon", bx + 0.5, y + 1, bz + 0.5)
    # 신전 안 팀 문장 (리소스팩)
    px, pz = P(-hd + 1.6, 0)
    b.w.display("item", px + 0.5, y + 5, pz + 0.5, model=f"deco/crest_{t}", scale=3.0,
                yaw=math.degrees(math.atan2(-f[0], f[1])))


def tent(b, x, z, f, wool, t):
    """천막: 팀색 양털 박공"""
    axis_f = abs(f[0]) > 0
    for i in range(-3, 4):
        for k in range(4):
            for s in (-1, 1):
                off = (3 - k) * s
                px = x + (i if not axis_f else off)
                pz = z + (off if not axis_f else i)
                gy = b.top(px, pz)
                if k == 0:
                    b.set(px, Y + 1, pz, "spruce_fence")
                b.set(px, Y + 1 + k, pz, wool if (i + k) % 3 else "white_wool")
                if abs(i) == 3 and k < 3 and abs(off) < 3 and s == 1:
                    pass
        # 안쪽 비움
        for k in range(1, 3):
            for off in range(-2 + k - 1, 3 - k + 1):
                px = x + (i if not axis_f else off)
                pz = z + (off if not axis_f else i)
                if abs(i) < 3:
                    b.set(px, Y + k, pz, "air")
    for off in range(-2, 3):
        px = x + (0 if not axis_f else off)
        pz = z + (off if not axis_f else 0)
    for i in (-3, 3):
        px = x + (i if not axis_f else 0); pz = z + (0 if not axis_f else i)
        b.set(px, Y + 1, pz, "air"); b.set(px, Y + 2, pz, "air")
    px = x; pz = z
    b.set(px, Y + 1, pz, "red_bed[facing=north,occupied=false,part=foot]" if False else "white_carpet")


def props(b, x, z):
    items = ["barrel[facing=up,open=false]", "hay_block[axis=y]", "anvil[facing=north]", "smithing_table", "grindstone[face=floor,facing=north]"]
    b.set(x, Y + 1, z, "barrel[facing=up,open=false]")
    b.set(x + 1, Y + 1, z, "barrel[facing=up,open=false]")
    b.set(x, Y + 2, z, "barrel[facing=up,open=false]")
    b.set(x, Y + 1, z + 1, "hay_block[axis=y]")
    b.set(x - 1, Y + 1, z, "anvil[facing=north]")
    b.set(x + 1, Y + 1, z + 1, "smithing_table")
    b.set(x - 1, Y + 1, z - 1, "spruce_fence")
    b.set(x - 1, Y + 2, z - 1, "lantern[hanging=false,waterlogged=false]")


def well(b, x, z):
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            if dx == 0 and dz == 0:
                b.fill(x, Y - 3, z, x, Y, z, "water")
            else:
                b.set(x + dx, Y + 1, z + dz, "cobblestone_wall" if abs(dx) + abs(dz) == 1 else "mossy_cobblestone")
    for dx, dz in ((-1, -1), (1, 1)):
        b.fill(x + dx, Y + 2, z + dz, x + dx, Y + 3, z + dz, "spruce_fence")
    b.set(x - 1, Y + 4, z - 1, "spruce_slab[type=bottom,waterlogged=false]")
    b.set(x, Y + 4, z, "spruce_slab[type=bottom,waterlogged=false]")
    b.set(x + 1, Y + 4, z + 1, "spruce_slab[type=bottom,waterlogged=false]")
    b.set(x, Y + 3, z, "iron_chain[axis=y,waterlogged=false]")
