"""중간 지대: 차로 관문 초소, 폐허 산포, 식생, 길가 등불"""
import math

import numpy as np

from layout import *
from noise import value_noise
from prims import Builder, stairs, slab, wall, DXZ, OPP, facing_to


def build_midfield(b: Builder):
    for t in TEAM_ORDER:
        outpost(b, t)
    road_lamps(b)
    ruins(b)
    vegetation(b)


# ───────────────────────────────────────── 차로 관문 (본진~중앙 사이)
def outpost(b, t):
    d = TEAMS[t][0]
    D = 64
    ox, oz = C[0] + d[0] * D, C[1] + d[1] * D
    f = (-d[0], -d[1])
    r = (-f[1], f[0])
    y = b.gy(round(ox), round(oz))
    rng = b.r

    def P(fw, rt):
        return (round(ox + f[0] * fw + r[0] * rt), round(oz + f[1] * fw + r[1] * rt))

    # 양쪽 탑 (5x5) — 한쪽은 무너짐
    for side, hgt in ((-1, 12), (1, int(rng.integers(5, 8)))):
        cxp, czp = P(0, side * 7)
        gy = b.gy(cxp, czp)
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                edge = max(abs(dx), abs(dz)) == 2
                g2 = b.gy(cxp + dx, czp + dz)
                b.fill(cxp + dx, g2 - 1, czp + dz, cxp + dx, gy, czp + dz, "stone_bricks")
                top = gy + hgt + (int(rng.integers(-2, 1)) if hgt < 10 else 0)
                for yy in range(gy + 1, top + 1):
                    if not edge:
                        b.set(cxp + dx, yy, czp + dz, "air")
                        continue
                    if (yy - gy) % 4 == 2 and (dx == 0 or dz == 0):
                        continue  # 창
                    b.set(cxp + dx, yy, czp + dz, b.mix([("stone_bricks", 5), ("mossy_stone_bricks", 3), ("cracked_stone_bricks", 2)]))
        if hgt >= 10:
            b.fill(cxp - 2, gy + hgt - 1, czp - 2, cxp + 2, gy + hgt - 1, czp + 2, "spruce_planks")
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if max(abs(dx), abs(dz)) == 2 and (dx + dz) % 2 == 0:
                        b.set(cxp + dx, gy + hgt + 1, czp + dz, "stone_bricks")
            # 사다리 대신 안쪽 계단
            pts = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
            for k in range(hgt - 2):
                dx, dz = pts[k % 8]
                nx, nz = pts[(k + 1) % 8]
                b.set(cxp + dx, gy + 1 + k, czp + dz, stairs("spruce", facing_to(nx - dx, nz - dz)))
        else:
            b.rubble(cxp + side * 0, 0, czp, 3, [("stone_bricks", 3), ("mossy_stone_bricks", 2), ("cobblestone", 2), (slab("stone_brick"), 2)])
    # 길 위 아치 (중앙 부분 무너짐)
    for rt in range(-5, 6):
        for fw in (0, 1):
            px, pz = P(fw, rt)
            gy = b.gy(px, pz)
            if abs(rt) >= 4:
                b.fill(px, gy + 1, pz, px, y + 9, pz, "stone_bricks")
            elif abs(rt) >= 1 or fw == 1:
                if rt == 1 and fw == 0:
                    continue
                b.fill(px, y + 7, pz, px, y + 9, pz, "stone_bricks")
                b.set(px, y + 6, pz, stairs("stone_brick", facing_to(*((-r[0], -r[1]) if rt > 0 else r)), "top") if abs(rt) == 3 else "air")
    # 성벽 잔해 (양옆으로)
    for side in (-1, 1):
        a0 = P(0, side * 10); a1 = P(0, side * 18)
        b.ruin_wall(a0[0], a0[1], a1[0], a1[1], b.gy(*a0) + 1, 4,
                    [("stone_bricks", 5), ("mossy_stone_bricks", 3), ("cracked_stone_bricks", 2), ("cobblestone", 1)])
    # 바리케이드 · 상자
    for k in range(3):
        px, pz = P(rng.integers(-8, -3), rng.integers(-4, 5))
        gy = b.top(px, pz)
        b.set(px, gy + 1, pz, "barrel[facing=up,open=false]" if k != 1 else "hay_block[axis=y]")
    b.w.mark(f"outpost_{t}", ox + 0.5, y + 1, oz + 0.5)


# ───────────────────────────────────────── 길가 등불
def road_lamps(b):
    T = b.T
    for kind, pts, width in T.paths:
        if kind != "paved":
            continue
        a, e = pts[0], pts[-1]
        L = dist(a, e)
        v = ((e[0] - a[0]) / L, (e[1] - a[1]) / L)
        n = (-v[1], v[0])
        s = 6
        while s < L - 4:
            for side in (-1, 1):
                px = round(a[0] + v[0] * s + n[0] * side * (width / 2 + 1))
                pz = round(a[1] + v[1] * s + n[1] * side * (width / 2 + 1))
                gy = b.top(px, pz)
                if T.water[min(px, SIZE - 1), min(pz, SIZE - 1)] >= 0:
                    continue
                if abs(gy - b.gy(px, pz)) > 1:
                    continue
                b.set(px, gy + 1, pz, "stone_brick_wall")
                b.set(px, gy + 2, pz, "stone_brick_wall")
                b.set(px, gy + 3, pz, "chiseled_stone_bricks")
                b.set(px, gy + 4, pz, "lantern[hanging=false,waterlogged=false]")
            s += 14


# ───────────────────────────────────────── 폐허 산포
def free_spot(b, x, z, clear=6):
    T = b.T
    if not (8 < x < SIZE - 8 and 8 < z < SIZE - 8):
        return False
    if T.zone[x, z] not in ("", "ares", "athena", "demeter", "hermes"):
        return False
    x0, x1 = x - clear, x + clear
    z0, z1 = z - clear, z + clear
    if T.road[x0:x1, z0:z1].max() > 0.1:
        return False
    if (T.water[x0:x1, z0:z1] >= 0).any():
        return False
    if T.slope[x0:x1, z0:z1].max() > 2:
        return False
    for a in ALTARS:
        if dist((x, z), altar_pos(a)) < 16:
            return False
    if dist((x, z), C) < MOAT_OUT + 6:
        return False
    for t in TEAMS:
        if dist((x, z), team_base(t)) < BASE_R + 6:
            return False
    for l in LAIRS:
        if dist((x, z), lair_pos(l)) < LAIR_R + 10:
            return False
    if max(abs(x - C[0]), abs(z - C[1])) > 112:
        return False
    return True


def ruins(b):
    rng = b.r
    placed = []
    kinds = ["colonnade", "wall_l", "shrine", "rubble", "statue", "camp", "colonnade", "wall_l"]
    tries = 0
    while len(placed) < 34 and tries < 4000:
        tries += 1
        x = int(rng.integers(10, SIZE - 10)); z = int(rng.integers(10, SIZE - 10))
        if not free_spot(b, x, z, 5):
            continue
        if any(math.hypot(x - px, z - pz) < 16 for px, pz in placed):
            continue
        k = kinds[len(placed) % len(kinds)]
        y = b.gy(x, z)
        mats = [("stone_bricks", 5), ("mossy_stone_bricks", 3), ("cracked_stone_bricks", 2), ("cobblestone", 1)]
        zone = b.T.zone[x, z]
        if zone == "ares":
            mats = [("polished_blackstone_bricks", 4), ("cracked_polished_blackstone_bricks", 3), ("blackstone", 2)]
        if zone == "athena":
            mats = [("quartz_bricks", 4), ("calcite", 3), ("polished_diorite", 2)]
        if k == "colonnade":
            n = int(rng.integers(3, 6))
            ang = rng.uniform(0, 3.14)
            for i in range(n):
                px = round(x + math.cos(ang) * (i - n / 2) * 4); pz = round(z + math.sin(ang) * (i - n / 2) * 4)
                gy = b.gy(px, pz)
                br = None if rng.random() < 0.35 else int(rng.integers(2, 7))
                b.column(px, pz, gy + 1, 8, "quartz" if zone != "ares" else "blackstone", broken=br)
            fx = round(x + math.sin(ang) * 3); fz = round(z - math.cos(ang) * 3)
            b.fallen_column(fx, b.gy(fx, fz) + 1, fz, int(rng.integers(4, 7)), "x" if abs(math.cos(ang)) > 0.7 else "z")
        elif k == "wall_l":
            L1 = int(rng.integers(6, 11)); L2 = int(rng.integers(4, 8))
            sx, sz = (1 if rng.random() < 0.5 else -1), (1 if rng.random() < 0.5 else -1)
            b.ruin_wall(x, z, x + L1 * sx, z, y + 1, int(rng.integers(3, 6)), mats)
            b.ruin_wall(x, z, x, z + L2 * sz, y + 1, int(rng.integers(3, 6)), mats)
            b.rubble(x + L1 * sx // 2, 0, z + 2 * sz, 2, mats + [(slab("stone_brick"), 2)])
        elif k == "shrine":
            for dx in (-2, 2):
                for dz in (-2, 2):
                    b.column(x + dx, z + dz, b.gy(x + dx, z + dz) + 1, 5, "quartz" if zone != "ares" else "blackstone", width=1,
                             broken=None if rng.random() < 0.7 else 3)
            b.fill(x - 2, y + 7, z - 2, x + 2, y + 7, z + 2, slab("smooth_quartz", "top"))
            b.fill(x - 1, y + 7, z - 1, x + 1, y + 7, z + 1, "air") if rng.random() < 0.5 else None
            b.set(x, y + 1, z, "chiseled_stone_bricks")
            b.set(x, y + 2, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        elif k == "rubble":
            b.rubble(x, 0, z, 3, mats + [(slab("stone_brick"), 2), ("gravel", 1)])
            b.fallen_column(x - 3, b.gy(x - 3, z + 3) + 1, z + 3, 5, "x")
        elif k == "statue":
            b.fill(x - 1, y + 1, z - 1, x + 1, y + 2, z + 1, "stone_bricks")
            b.w.display("statue", x + 0.5, y + 3, z + 0.5, model="hoplite_broken", yaw=rng.uniform(0, 360), scale=2.2)
            b.rubble(x + 2, 0, z + 2, 1, mats)
        elif k == "camp":
            b.set(x, y + 1, z, "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
            for dx, dz in ((2, 0), (-2, 0), (0, 2)):
                b.set(x + dx, y + 1, z + dz, "spruce_log[axis=x]" if dz == 0 else "spruce_log[axis=z]")
            b.set(x + 3, y + 1, z - 2, "barrel[facing=up,open=false]")
        placed.append((x, z))


# ───────────────────────────────────────── 식생
def vegetation(b):
    T = b.T
    rng = b.r
    forest = value_noise(SIZE, 20, 77)
    flowers = ["poppy", "dandelion", "cornflower", "oxeye_daisy", "azure_bluet", "allium"]
    trees = 0
    for x in range(4, SIZE - 4):
        for z in range(4, SIZE - 4):
            zone = T.zone[x, z]
            if zone.startswith("base") or zone.startswith("lair") or zone == "plaza":
                continue
            if T.no_veg[x, z] or T.road[x, z] > 0.05:
                continue
            gy = T.Hi[x, z]
            top = b.w.get(x, gy, z)
            if not (top.startswith("grass_block") or top.startswith("podzol") or top.startswith("moss_block") or top.startswith("coarse_dirt")):
                continue
            if not b.w.is_air(x, gy + 1, z):
                continue
            f = forest[x, z]
            r = rng.random()
            near_feature = T.feature[x, z]
            # 숲
            tree_p = 0.0
            if f > 0.62 and near_feature < 0.4:
                tree_p = 0.028
            elif f > 0.52:
                tree_p = 0.006
            if zone == "ares":
                tree_p *= 0.1
            if zone == "demeter":
                tree_p *= 1.8
            if r < tree_p and top.startswith(("grass_block", "podzol", "moss_block")):
                if b.w.get(x, gy + 1, z) == "air" and T.slope[x, z] <= 1:
                    kind = b.choice(["oak", "oak", "birch", "spruce", "dark_oak"], [4, 3, 2, 2, 1])
                    if zone == "athena":
                        kind = "olive"
                    if gy > G + 12:
                        kind = "spruce"
                    b.tree(x, gy + 1, z, kind, 0.8 + rng.random() * 0.5)
                    trees += 1
                    continue
            r2 = rng.random()
            if top.startswith("grass_block"):
                if r2 < 0.2 + f * 0.25:
                    b.set(x, gy + 1, z, "short_grass")
                elif r2 < 0.24 + f * 0.25:
                    b.set(x, gy + 1, z, "fern")
                elif r2 < 0.255 + f * 0.25:
                    b.set(x, gy + 1, z, flowers[int(rng.integers(0, len(flowers)))])
                elif r2 < 0.262 + f * 0.25 and f > 0.5:
                    b.bush(x, gy + 1, z, "oak_leaves" if rng.random() < 0.6 else "azalea_leaves")
                elif r2 < 0.27 + f * 0.25:
                    b.set(x, gy + 1, z, "bush")
            elif top.startswith("podzol") and r2 < 0.2:
                b.set(x, gy + 1, z, "fern")
            elif top.startswith("coarse_dirt") and r2 < 0.06 and zone == "ares":
                b.set(x, gy + 1, z, "dead_bush")
    return trees
