"""보스 전용 투기장 4곳 (모서리)

 공통: 평평한 원형 바닥 (반지름 19), 벽/절벽 테두리, 입구 3개,
       탈로스 돌진 기절용 기둥 4개 (모든 투기장에 엄폐 기둥), 보스 소환 마법진 (리소스팩)
"""
import math

import numpy as np

from layout import *
from prims import Builder, stairs, slab, wall, DXZ, OPP, facing_to


def build_lairs(b: Builder):
    for lid in LAIRS:
        c = lair_pos(lid)
        x0, z0 = int(c[0]), int(c[1])
        y = b.gy(x0, z0)
        {"forge": forge, "sands": sands, "quarry": quarry, "garden": garden}[lid](b, x0, y, z0)
        b.w.mark(f"lair_{lid}", x0 + 0.5, y + 1, z0 + 0.5, radius=LAIR_R, boss=LAIRS[lid][1])
        b.w.display("item", x0 + 0.5, y + 1.03, z0 + 0.5, model=f"deco/summon_circle_{LAIRS[lid][1]}", scale=14, flat=True, tag=f"bg_lair_{lid}")


def entrances(x0, z0, lid):
    dirv = LAIRS[lid][0]
    t = (C[0] - x0, C[1] - z0)
    L = math.hypot(*t)
    return [(t[0] / L, t[1] / L), (-dirv[0], 0), (0, -dirv[1])]


def in_entrance(x, z, x0, z0, lid, deg=16):
    a = math.degrees(math.atan2(z - z0, x - x0))
    for v in entrances(x0, z0, lid):
        b = math.degrees(math.atan2(v[1], v[0]))
        if abs((a - b + 540) % 360 - 180) < deg:
            return True
    return False


def floor_disc(b, x0, y, z0, mats, r=LAIR_R, pattern=None):
    for x in range(x0 - r - 1, x0 + r + 2):
        for z in range(z0 - r - 1, z0 + r + 2):
            d = math.hypot(x - x0, z - z0)
            if d <= r + 0.3:
                s = b.mix(mats)
                if pattern:
                    s = pattern(x - x0, z - z0, d) or s
                b.set(x, y, z, s)
                b.air(x, y + 1, z, x, y + 14, z)


def ring_wall(b, x0, y, z0, lid, h, mats, r0=LAIR_R + 0.6, r1=LAIR_R + 2.6, cap=None):
    for x in range(x0 - LAIR_R - 4, x0 + LAIR_R + 5):
        for z in range(z0 - LAIR_R - 4, z0 + LAIR_R + 5):
            d = math.hypot(x - x0, z - z0)
            if r0 <= d < r1 and not in_entrance(x, z, x0, z0, lid):
                gy = b.gy(x, z)
                top = y + h + int(b.r.integers(-1, 2))
                b.fill(x, y - 2, z, x, max(top, y + 2), z, b.mix(mats))
                if cap and d >= r1 - 1:
                    b.set(x, max(top, y + 2) + 1, z, cap)


def pillars(b, x0, y, z0, mat, band, r=11, h=9, n=4, off=0.785):
    for i in range(n):
        a = i / n * 2 * math.pi + off
        px, pz = round(x0 + math.cos(a) * r), round(z0 + math.sin(a) * r)
        b.fill(px - 1, y + 1, pz - 1, px + 1, y + h, pz + 1, mat)
        b.fill(px - 1, y + 3, pz - 1, px + 1, y + 3, pz + 1, band)
        b.fill(px - 1, y + h - 1, pz - 1, px + 1, y + h - 1, pz + 1, band)
        b.w.mark(f"pillar_{x0}_{z0}_{i}", px + 0.5, y + 1, pz + 0.5)


def gate_arches(b, x0, y, z0, lid, mat, st, h=9):
    for v in entrances(x0, z0, lid):
        cxg = round(x0 + v[0] * (LAIR_R + 1.6)); czg = round(z0 + v[1] * (LAIR_R + 1.6))
        axis = "z" if abs(v[0]) > abs(v[1]) else "x"
        if abs(abs(v[0]) - abs(v[1])) < 0.3:
            # 대각 입구: 기둥 두 개만
            for s in (-1, 1):
                px = round(cxg - v[1] * s * 4.5); pz = round(czg + v[0] * s * 4.5)
                b.fill(px, y + 1, pz, px, y + h, pz, mat)
                b.set(px, y + h + 1, pz, "lantern[hanging=false,waterlogged=false]")
            continue
        b.arch(cxg, czg, y + 1, 7, h, axis, mat, st, depth=2)


# ───────────────────────────────────────── 헤파이스토스의 대장간 (탈로스)
def forge(b, x0, y, z0):
    lid = "forge"
    def pat(dx, dz, d):
        if 6.5 < d < 7.5 or 14.5 < d < 15.5:
            return "polished_blackstone"
        if abs(dx) < 1 or abs(dz) < 1:
            return "copper_grate" if d < 6 else None
        if d < 3:
            return "chiseled_polished_blackstone"
        return None
    floor_disc(b, x0, y, z0, [("polished_blackstone_bricks", 6), ("cracked_polished_blackstone_bricks", 2), ("blackstone", 1), ("basalt[axis=y]", 1)], pattern=pat)
    ring_wall(b, x0, y, z0, lid, 12, [("basalt[axis=y]", 4), ("blackstone", 3), ("polished_blackstone_bricks", 2), ("smooth_basalt", 1)])
    pillars(b, x0, y, z0, "polished_blackstone_bricks", "waxed_oxidized_cut_copper")
    gate_arches(b, x0, y, z0, lid, "polished_blackstone_bricks", "polished_blackstone_brick", 10)
    # 용광로 (바깥쪽 모서리 방향 벽에 붙여)
    out = LAIRS[lid][0]
    L = math.hypot(*out); ov = (out[0] / L, out[1] / L)
    fx, fz = round(x0 + ov[0] * (LAIR_R - 2)), round(z0 + ov[1] * (LAIR_R - 2))
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            if max(abs(dx), abs(dz)) <= 4:
                h = 12 - max(abs(dx), abs(dz))
                b.fill(fx + dx, y + 1, fz + dz, fx + dx, y + h, fz + dz, "polished_blackstone_bricks" if max(abs(dx), abs(dz)) > 2 else "blackstone")
    b.fill(fx - 1, y + 1, fz - 1, fx + 1, y + 4, fz + 1, "air")
    b.fill(fx - 1, y + 1, fz - 1, fx + 1, y + 1, fz + 1, "magma_block")
    b.set(fx, y + 2, fz, "lava")
    b.fill(fx - 1, y + 5, fz - 1, fx + 1, y + 5, fz + 1, "waxed_copper_grate" if False else "copper_grate")
    # 용암 수로 (벽 안쪽 1칸, 쇠창살 덮개)
    for i in range(360):
        a = i / 360 * 6.28
        px, pz = round(x0 + math.cos(a) * (LAIR_R - 0.2)), round(z0 + math.sin(a) * (LAIR_R - 0.2))
        if in_entrance(px, pz, x0, z0, lid, 20):
            continue
        b.set(px, y, pz, "lava")
        b.set(px, y - 1, pz, "blackstone")
        b.set(px, y + 1, pz, "iron_bars")
    # 모루 · 사슬 · 부서진 청동 조각
    for k in range(8):
        a = k / 8 * 6.28 + 0.2
        px, pz = round(x0 + math.cos(a) * 16.5), round(z0 + math.sin(a) * 16.5)
        if in_entrance(px, pz, x0, z0, lid, 20):
            continue
        b.set(px, y + 1, pz, "anvil[facing=north]" if k % 2 else "smithing_table")
    for i in range(4):
        a = i / 4 * 6.28 + 0.785
        px, pz = round(x0 + math.cos(a) * 11), round(z0 + math.sin(a) * 11)
        for s in range(1, 4):
            qx = round(px + (x0 - px) * s / 11); qz = round(pz + (z0 - pz) * s / 11)
    b.w.display("item", x0 + 0.5 + ov[0] * 12, y + 1, z0 + 0.5 + ov[1] * 12, model="deco/bronze_debris", scale=3.0, yaw=45)


# ───────────────────────────────────────── 잊힌 모래 신전 (스핑크스)
def sands(b, x0, y, z0):
    lid = "sands"
    def pat(dx, dz, d):
        if 8.5 < d < 9.5 or 16.5 < d < 17.5:
            return "cut_sandstone"
        if d < 4 and (abs(dx) + abs(dz)) % 3 == 0:
            return "chiseled_sandstone"
        return None
    floor_disc(b, x0, y, z0, [("sand", 5), ("smooth_sandstone", 3), ("sandstone", 2)], pattern=pat)
    ring_wall(b, x0, y, z0, lid, 10, [("sandstone", 4), ("cut_sandstone", 3), ("smooth_sandstone", 2), ("orange_terracotta", 1)], cap=slab("smooth_sandstone"))
    pillars(b, x0, y, z0, "cut_sandstone", "chiseled_sandstone", h=10)
    gate_arches(b, x0, y, z0, lid, "cut_sandstone", "sandstone", 9)
    # 오벨리스크 6개 (벽 앞)
    for i in range(6):
        a = i / 6 * 6.28 + 0.26
        px, pz = round(x0 + math.cos(a) * 16.5), round(z0 + math.sin(a) * 16.5)
        if in_entrance(px, pz, x0, z0, lid, 22):
            continue
        b.fill(px, y + 1, pz, px, y + 7, pz, "chiseled_sandstone" if False else "cut_sandstone")
        b.set(px, y + 4, pz, "chiseled_sandstone")
        b.set(px, y + 8, pz, "gold_block")
        b.set(px, y + 9, pz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # 벽 위 계단식 피라미드 모서리 (바깥 모서리)
    out = LAIRS[lid][0]
    L = math.hypot(*out); ov = (out[0] / L, out[1] / L)
    px, pz = round(x0 + ov[0] * (LAIR_R + 5)), round(z0 + ov[1] * (LAIR_R + 5))
    for k in range(8):
        b.fill(px - 7 + k, y + 1 + k * 2, pz - 7 + k, px + 7 - k, y + 2 + k * 2, pz + 7 - k, "sandstone" if k % 2 else "cut_sandstone")
    b.w.display("item", x0 + 0.5 + ov[0] * 15, y + 1, z0 + 0.5 + ov[1] * 15, model="deco/sphinx_head", scale=4.0,
                yaw=math.degrees(math.atan2(ov[0], -ov[1])))


# ───────────────────────────────────────── 거인의 채석장 (키클롭스)
def quarry(b, x0, y, z0):
    lid = "quarry"
    floor_disc(b, x0, y, z0, [("stone", 5), ("cobblestone", 2), ("gravel", 2), ("andesite", 2), ("coarse_dirt", 1)])
    rng = b.r
    # 채석 계단 벽 (지형이 만든 단 위에 절단면)
    for x in range(x0 - LAIR_R - 7, x0 + LAIR_R + 8):
        for z in range(z0 - LAIR_R - 7, z0 + LAIR_R + 8):
            d = math.hypot(x - x0, z - z0)
            if LAIR_R + 0.4 <= d < LAIR_R + 7 and not in_entrance(x, z, x0, z0, lid):
                gy = b.gy(x, z)
                if (gy - y) % 4 == 0:
                    b.set(x, gy, z, "polished_andesite")
    # 거대한 바위 (기둥 역할) — 둥근 덩어리
    for i in range(4):
        a = i / 4 * 6.28 + 0.785
        px, pz = x0 + math.cos(a) * 11, z0 + math.sin(a) * 11
        b.blob(px, y + 2.5, pz, 2.3, 2.6, 2.3, "stone", 0.95)
        b.blob(px + 0.8, y + 4.2, pz - 0.5, 1.4, 1.3, 1.4, "andesite", 0.9)
        b.w.mark(f"pillar_{x0}_{z0}_{i}", round(px) + 0.5, y + 1, round(pz) + 0.5)
    # 나무 기중기 2대
    for i in range(2):
        a = i * 3.14 + 1.9
        px, pz = round(x0 + math.cos(a) * 16), round(z0 + math.sin(a) * 16)
        b.fill(px, y + 1, pz, px, y + 11, pz, "spruce_log[axis=y]")
        for s in range(1, 7):
            qx = round(px + (x0 - px) * s / 16); qz = round(pz + (z0 - pz) * s / 16)
            b.set(qx, y + 11, qz, "spruce_log[axis=x]" if abs(x0 - px) > abs(z0 - pz) else "spruce_log[axis=z]")
        qx = round(px + (x0 - px) * 6 / 16); qz = round(pz + (z0 - pz) * 6 / 16)
        for k in range(1, 5):
            b.set(qx, y + 11 - k, qz, "iron_chain[axis=y,waterlogged=false]")
        b.set(qx, y + 6, qz, "cobblestone")
    # 양 우리 (폴리페모스)
    out = LAIRS[lid][0]
    L = math.hypot(*out); ov = (out[0] / L, out[1] / L)
    px, pz = round(x0 + ov[0] * 15), round(z0 + ov[1] * 15)
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if max(abs(dx), abs(dz)) == 3:
                b.set(px + dx, y + 1, pz + dz, "oak_fence")
            else:
                b.set(px + dx, y, pz + dz, "hay_block[axis=y]" if (dx + dz) % 3 == 0 else "coarse_dirt")
    b.w.display("item", x0 + 0.5 + ov[0] * 17, y + 1, z0 + 0.5 + ov[1] * 17, model="deco/giant_club", scale=3.5, yaw=30, tilt=70)
    # 흩어진 돌 조각 (엄폐)
    for k in range(10):
        a = rng.uniform(0, 6.28); d = rng.uniform(4, 17)
        qx, qz = round(x0 + math.cos(a) * d), round(z0 + math.sin(a) * d)
        b.set(qx, y + 1, qz, b.mix([("cobblestone", 3), ("stone", 2), ("mossy_cobblestone", 1)]))


# ───────────────────────────────────────── 헤스페리데스의 정원 (라돈)
def garden(b, x0, y, z0):
    lid = "garden"
    def pat(dx, dz, d):
        if 5.5 < d < 6.5 or 13.5 < d < 14.5:
            return "moss_block"
        if d < 2.5:
            return "gold_block" if d < 1 else "smooth_quartz"
        return None
    floor_disc(b, x0, y, z0, [("grass_block", 7), ("moss_block", 2), ("podzol", 1)], pattern=pat)
    ring_wall(b, x0, y, z0, lid, 6, [("mossy_stone_bricks", 5), ("stone_bricks", 3), ("cracked_stone_bricks", 1)])
    # 벽 위 산울타리
    for x in range(x0 - LAIR_R - 4, x0 + LAIR_R + 5):
        for z in range(z0 - LAIR_R - 4, z0 + LAIR_R + 5):
            d = math.hypot(x - x0, z - z0)
            if LAIR_R + 0.6 <= d < LAIR_R + 2.6 and not in_entrance(x, z, x0, z0, lid):
                t = b.top(x, z)
                b.set(x, t + 1, z, "azalea_leaves[distance=7,persistent=true,waterlogged=false]")
                if b.rand() < 0.5:
                    b.set(x, t + 2, z, "flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]")
    gate_arches(b, x0, y, z0, lid, "mossy_stone_bricks", "mossy_stone_brick", 7)
    # 황금 사과나무 4그루 (기둥 역할 → 나무 줄기 3x3)
    rng = b.r
    for i in range(4):
        a = i / 4 * 6.28 + 0.785
        px, pz = round(x0 + math.cos(a) * 11), round(z0 + math.sin(a) * 11)
        b.fill(px - 1, y + 1, pz - 1, px + 1, y + 5, pz + 1, "oak_wood[axis=y]")
        b.fill(px, y + 6, pz, px, y + 9, pz, "oak_log[axis=y]")
        b.blob(px, y + 10, pz, 4.5, 2.8, 4.5, "flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]", 0.75)
        b.blob(px, y + 9, pz, 3.5, 2.0, 3.5, "azalea_leaves[distance=7,persistent=true,waterlogged=false]", 0.7)
        b.w.mark(f"pillar_{x0}_{z0}_{i}", px + 0.5, y + 1, pz + 0.5)
        for k in range(6):
            aa = rng.uniform(0, 6.28); dd = rng.uniform(2, 4)
            b.w.display("item", px + 0.5 + math.cos(aa) * dd, y + 8.2 + rng.uniform(-0.5, 0.8), pz + 0.5 + math.sin(aa) * dd,
                        model="minecraft:golden_apple", scale=0.9, yaw=rng.uniform(0, 360), glow=True)
    # 꽃 고리
    flowers = ["poppy", "dandelion", "allium", "azure_bluet", "oxeye_daisy", "cornflower", "lily_of_the_valley", "orange_tulip"]
    for k in range(220):
        a = rng.uniform(0, 6.28); d = rng.uniform(15, 18.5)
        px, pz = round(x0 + math.cos(a) * d), round(z0 + math.sin(a) * d)
        if b.w.get(px, y, pz).startswith("grass_block") and b.w.is_air(px, y + 1, pz):
            b.set(px, y + 1, pz, flowers[k % len(flowers)])
    # 분수 (바깥 모서리 쪽)
    out = LAIRS[lid][0]
    L = math.hypot(*out); ov = (out[0] / L, out[1] / L)
    fx, fz = round(x0 + ov[0] * 16), round(z0 + ov[1] * 16)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2:
                b.set(fx + dx, y + 1, fz + dz, "mossy_stone_bricks")
            else:
                b.set(fx + dx, y + 1, fz + dz, "water")
                b.set(fx + dx, y, fz + dz, "mossy_stone_bricks")
    b.fill(fx, y + 1, fz, fx, y + 3, fz, "mossy_stone_brick_wall")
    b.set(fx, y + 4, fz, "gold_block")
