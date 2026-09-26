"""외곽 제단 4곳 — 공통 거점 구조 + 테마별 지형 장식"""
import math

import numpy as np

from layout import *
from prims import Builder, stairs, slab, wall, DXZ, OPP, facing_to

THEME = {
    # 기단/기둥/포인트 재질
    "ares": dict(floor="polished_blackstone_bricks", floor2="cracked_polished_blackstone_bricks", edge="polished_blackstone",
                 st="polished_blackstone_brick", col="blackstone", accent="red_nether_bricks", glass_neutral="white_stained_glass"),
    "athena": dict(floor="calcite", floor2="polished_diorite", edge="smooth_quartz",
                   st="quartz", col="quartz", accent="light_blue_terracotta", glass_neutral="white_stained_glass"),
    "hermes": dict(floor="polished_andesite", floor2="andesite", edge="smooth_stone",
                   st="polished_andesite", col="stone", accent="cyan_terracotta", glass_neutral="white_stained_glass"),
    "demeter": dict(floor="mossy_stone_bricks", floor2="stone_bricks", edge="smooth_sandstone",
                    st="mossy_stone_brick", col="sandstone", accent="yellow_terracotta", glass_neutral="white_stained_glass"),
}


def build_altars(b: Builder):
    for a in ALTARS:
        build_altar(b, a)


def build_altar(b, aid):
    A = altar_pos(aid)
    x0, z0 = int(A[0]), int(A[1])
    y = b.gy(x0, z0)
    th = THEME[aid]
    out = (A[0] - C[0], A[1] - C[1])
    L = math.hypot(*out)
    ov = (out[0] / L, out[1] / L)              # 바깥 방향
    # 테마 지형 먼저
    {"ares": ares, "athena": athena, "hermes": hermes, "demeter": demeter}[aid](b, A, y, ov)
    core(b, aid, x0, y, z0, th, ov)


def core(b, aid, x0, y, z0, th, ov):
    R = 6 if aid != "hermes" else 5
    # 기단 (지면 +1)
    for x in range(x0 - R - 1, x0 + R + 2):
        for z in range(z0 - R - 1, z0 + R + 2):
            d = math.hypot(x - x0, z - z0)
            if d <= R - 0.5:
                s = b.mix([(th["floor"], 6), (th["floor2"], 2)])
                if R - 1.7 < d:
                    s = th["edge"]
                if 2.7 < d < 3.6:
                    s = th["accent"]
                b.fill(x, y - 2, z, x, y + 1, z, s)
                b.air(x, y + 2, z, x, y + 12, z)
            elif d <= R + 0.5:
                b.fill(x, y - 2, z, x, y, z, th["floor2"])
                b.set(x, y + 1, z, stairs(th["st"], facing_to(x0 - x, z0 - z)))
                b.air(x, y + 2, z, x, y + 12, z)
    # 중앙: 비콘 (철 3x3 은 기단 속)
    b.fill(x0 - 1, y, z0 - 1, x0 + 1, y, z0 + 1, "iron_block")
    b.fill(x0 - 1, y + 1, z0 - 1, x0 + 1, y + 1, z0 + 1, th["edge"])
    b.set(x0, y + 1, z0, "iron_block")
    b.set(x0, y + 2, z0, "beacon")
    b.set(x0, y + 3, z0, "white_stained_glass")
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        b.set(x0 + dx, y + 2, z0 + dz, stairs(th["st"], facing_to(-dx, -dz)))
    b.w.mark(f"altar_{aid}", x0 + 0.5, y + 2, z0 + 0.5, radius=R + 1.5)
    b.w.mark(f"altar_{aid}_beacon", x0, y + 3, z0)
    # 기둥 고리
    n = 6 if aid != "hermes" else 4
    for i in range(n):
        a = i / n * 2 * math.pi + math.pi / n
        px = round(x0 + math.cos(a) * (R + 3)); pz = round(z0 + math.sin(a) * (R + 3))
        py = b.top(px, pz)
        if abs(py - y) > 4:
            continue
        broken = None if (i % 3 != 1) else int(b.r.integers(2, 5))
        b.column(px, pz, py + 1, 8, th["col"] if th["col"] != "stone" else "stone", broken=broken, width=3 if aid in ("ares", "athena") else 1)
    # 리소스팩 장식: 거점 링 · 떠 있는 문장 · 신상
    b.w.display("item", x0 + 0.5, y + 2.03, z0 + 0.5, model="deco/cap_ring_neutral", scale=(R + 1.5) * 2, flat=True, tag=f"bg_cap_{aid}")
    b.w.display("item", x0 + 0.5, y + 8.5, z0 + 0.5, model=f"deco/sigil_{aid}", scale=3.2, spin=True, glow=True, tag="bg_spin")
    b.w.display("item", x0 + 0.5, y + 6.0, z0 + 0.5, model="deco/rune_ring", scale=4.2, spin=True, tilt=15, tag="bg_spin")
    # 신상: 바깥쪽 받침 위
    sx = round(x0 + ov[0] * (R + 7)); sz = round(z0 + ov[1] * (R + 7))
    sy = b.top(sx, sz)
    if aid == "hermes":
        sx = round(x0 + ov[0] * 3.5); sz = round(z0 + ov[1] * 3.5); sy = y + 1
    b.fill(sx - 1, sy + 1, sz - 1, sx + 1, sy + 2, sz + 1, th["edge"])
    b.fill(sx - 1, sy + 3, sz - 1, sx + 1, sy + 3, sz + 1, th["floor"])
    yaw = math.degrees(math.atan2(-(x0 - sx), (z0 - sz)))
    b.w.display("statue", sx + 0.5, sy + 4, sz + 0.5, model=f"god_{aid}", yaw=yaw, scale=2.6 if aid != "hermes" else 1.8)
    # 화로 4개
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        px = round(x0 + math.cos(a) * (R + 1.2)); pz = round(z0 + math.sin(a) * (R + 1.2))
        if aid == "hermes":
            continue
        b.brazier(px, b.top(px, pz) + 1, pz, soul=(aid == "hermes"), tall=1)


# ───────────────────────────────────────────── 아레스: 전쟁의 메사
def ares(b, A, y, ov):
    x0, z0 = int(A[0]), int(A[1])
    rng = b.r
    # 용암 균열 (메사 윗면)
    for k in range(5):
        a = rng.uniform(0, 6.28)
        px, pz = x0 + math.cos(a) * 9, z0 + math.sin(a) * 9
        for s in range(8):
            a += rng.uniform(-0.5, 0.5)
            px += math.cos(a); pz += math.sin(a)
            gx, gz = round(px), round(pz)
            gy = b.gy(gx, gz)
            if abs(gy - y) <= 1 and math.hypot(gx - x0, gz - z0) > 8:
                b.set(gx, gy, gz, "magma_block")
                if rng.random() < 0.3:
                    b.set(gx, gy - 1, gz, "lava")
                    b.set(gx, gy, gz, "magma_block")
    # 부러진 무기 (리소스팩) + 방패 무더기
    for k in range(7):
        a = k / 7 * 6.28 + rng.uniform(-0.2, 0.2)
        d = rng.uniform(10, 14)
        px, pz = x0 + math.cos(a) * d, z0 + math.sin(a) * d
        gy = b.gy(round(px), round(pz))
        if abs(gy - y) > 2:
            continue
        model = ["deco/great_sword", "deco/spear", "deco/great_sword", "deco/shield"][k % 4]
        b.w.display("item", px + 0.5, gy + 1.0, pz + 0.5, model=model, scale=2.2, yaw=rng.uniform(0, 360), tilt=rng.uniform(-18, 18))
        b.set(round(px), gy + 1, round(pz), b.mix([("blackstone", 2), ("gilded_blackstone", 1), ("basalt[axis=y]", 1)]))
    # 해골/뼈 더미
    for k in range(4):
        a = rng.uniform(0, 6.28); d = rng.uniform(15, 20)
        px, pz = round(x0 + math.cos(a) * d), round(z0 + math.sin(a) * d)
        b.rubble(px, 0, pz, 1, [("bone_block[axis=y]", 3), ("skeleton_skull[rotation=0]", 1), ("coarse_dirt", 1)])
    # 전쟁 깃발 (찢어진 붉은 천)
    for k in range(4):
        a = k / 4 * 6.28 + 0.4
        px, pz = round(x0 + math.cos(a) * 12), round(z0 + math.sin(a) * 12)
        gy = b.gy(px, pz)
        if abs(gy - y) > 2:
            continue
        b.fill(px, gy + 1, pz, px, gy + 7, pz, "dark_oak_fence")
        b.set(px, gy + 8, pz, "iron_chain[axis=y,waterlogged=false]")
        b.w.display("item", px + 0.5, gy + 6.0, pz + 0.5, model="deco/war_banner", scale=2.4, yaw=math.degrees(a) + 90, sway=True)
    # 죽은 나무
    for k in range(3):
        a = rng.uniform(0, 6.28); d = rng.uniform(22, 30)
        px, pz = round(x0 + math.cos(a) * d), round(z0 + math.sin(a) * d)
        b.tree(px, b.gy(px, pz) + 1, pz, "dead")


# ───────────────────────────────────────────── 아테나: 지혜의 테라스
def athena(b, A, y, ov):
    x0, z0 = int(A[0]), int(A[1])
    rng = b.r
    # 넓은 대리석 테라스 (반지름 15)
    for x in range(x0 - 16, x0 + 17):
        for z in range(z0 - 16, z0 + 17):
            d = math.hypot(x - x0, z - z0)
            if d < 15.5:
                s = b.mix([("calcite", 5), ("polished_diorite", 2), ("smooth_quartz", 2), ("diorite", 1)])
                if d > 13 and rng.random() < 0.3:
                    s = "grass_block"
                b.set(x, y, z, s)
                b.air(x, y + 1, z, x, y + 8, z)
            elif d < 16.5:
                b.set(x, y, z, "quartz_bricks")
                if rng.random() < 0.55:
                    b.set(x, y + 1, z, wall("diorite"))
    # 반사 연못 (중앙 방향 앞)
    fx, fz = x0 - ov[0] * 11, z0 - ov[1] * 11
    for x in range(round(fx) - 6, round(fx) + 7):
        for z in range(round(fz) - 6, round(fz) + 7):
            px, pz = x - fx, z - fz
            along = px * ov[0] + pz * ov[1]
            side = -px * ov[1] + pz * ov[0]
            if abs(along) <= 2.2 and abs(side) <= 6:
                b.set(x, y, z, "water")
                b.set(x, y - 1, z, "prismarine_bricks")
                if rng.random() < 0.08:
                    b.set(x, y + 1, z, "lily_pad")
            elif abs(along) <= 3.2 and abs(side) <= 7:
                b.set(x, y, z, "smooth_quartz")
    # 뒤쪽 주랑 (스토아): 바깥쪽 호
    for i in range(-5, 6):
        a = math.atan2(ov[1], ov[0]) + i * 0.16
        px, pz = round(x0 + math.cos(a) * 14), round(z0 + math.sin(a) * 14)
        b.column(px, pz, y + 1, 7, "quartz", broken=None if i % 4 else int(rng.integers(2, 5)), width=1)
        if i < 5:
            a2 = math.atan2(ov[1], ov[0]) + (i + 1) * 0.16
            qx, qz = round(x0 + math.cos(a2) * 14), round(z0 + math.sin(a2) * 14)
            if i % 4 and (i + 1) % 4:
                steps = max(abs(qx - px), abs(qz - pz))
                for s in range(steps + 1):
                    b.set(round(px + (qx - px) * s / max(1, steps)), y + 8, round(pz + (qz - pz) * s / max(1, steps)), "smooth_quartz")
    # 올리브 나무 + 부엉이 석상 (리소스팩)
    for k in range(9):
        a = rng.uniform(0, 6.28); d = rng.uniform(17, 27)
        px, pz = round(x0 + math.cos(a) * d), round(z0 + math.sin(a) * d)
        gy = b.gy(px, pz)
        if b.T.road[px, pz] > 0.1:
            continue
        b.tree(px, gy + 1, pz, "olive", 1.0)
    for s in (-1, 1):
        px = round(x0 - ov[0] * 15 - ov[1] * s * 8); pz = round(z0 - ov[1] * 15 + ov[0] * s * 8)
        gy = b.top(px, pz)
        b.fill(px, gy + 1, pz, px, gy + 2, pz, "chiseled_quartz_block")
        b.w.display("item", px + 0.5, gy + 3, pz + 0.5, model="deco/owl", scale=1.8, yaw=math.degrees(math.atan2(ov[0], -ov[1])))
    # 대리석 벤치
    for k in range(6):
        a = k / 6 * 6.28 + 0.3
        px, pz = round(x0 + math.cos(a) * 10.5), round(z0 + math.sin(a) * 10.5)
        b.set(px, y + 1, pz, stairs("quartz", facing_to(px - x0, pz - z0)))


# ───────────────────────────────────────────── 헤르메스: 바람의 첨탑
def hermes(b, A, y, ov):
    x0, z0 = int(A[0]), int(A[1])
    rng = b.r
    # 첨탑 둘레 옹벽 (협곡 벽을 층 무늬 암석으로)
    # 다리 3개: 그린 본진 / 옐로 본진 / 중앙 방향
    targets = [team_base("green"), team_base("yellow"), C]
    for k, tgt in enumerate(targets):
        v = (tgt[0] - x0, tgt[1] - z0)
        L = math.hypot(*v); v = (v[0] / L, v[1] / L)
        stone = (k == 2)
        for s in range(6, 19):
            for w_ in (-2, -1, 0, 1, 2) if stone else (-1, 0, 1):
                px = round(x0 + v[0] * s - v[1] * w_)
                pz = round(z0 + v[1] * s + v[0] * w_)
                # 다리 높이: 첨탑 y → 바깥 y 로 완만히
                outer = b.gy(round(x0 + v[0] * 20), round(z0 + v[1] * 20))
                t = (s - 6) / 12
                hy = round(y + (outer - y) * t)
                edge = abs(w_) == (2 if stone else 1)
                if stone:
                    b.set(px, hy, pz, "stone_bricks" if not edge else "polished_andesite")
                    b.set(px, hy - 1, pz, stairs("stone_brick", facing_to(-v[1] * w_, v[0] * w_) if edge else "north", "top") if edge else "stone_bricks")
                    if edge:
                        b.set(px, hy + 1, pz, wall("stone_brick"))
                else:
                    b.set(px, hy, pz, "spruce_planks" if not edge else "spruce_log[axis=y]")
                    if edge:
                        b.set(px, hy + 1, pz, "spruce_fence")
                        if s % 4 == 0:
                            b.set(px, hy + 2, pz, "spruce_fence")
                            b.set(px, hy + 3, pz, "lantern[hanging=false,waterlogged=false]")
                b.air(px, hy + 1 + (1 if edge else 0), pz, px, hy + 6, pz) if not edge else None
        # 석교 아치 받침
        if stone:
            for s in (9, 15):
                px, pz = round(x0 + v[0] * s), round(z0 + v[1] * s)
                bot = b.gy(px, pz)
                hy = b.top(px, pz)
                b.fill(px, bot, pz, px, hy - 2, pz, "stone_bricks")
    # 협곡 탈출 사다리 계단 (물 → 바깥)
    for k in range(3):
        a = k / 3 * 6.28 + 1.0
        for s in range(0, 12):
            d = 16.2
            aa = a + s * 0.09
            px, pz = round(x0 + math.cos(aa) * d), round(z0 + math.sin(aa) * d)
            hy = G - 7 + s
            if hy > b.gy(px, pz) + 1:
                break
            b.set(px, hy, pz, "cobblestone")
            b.air(px, hy + 1, pz, px, hy + 3, pz)
    # 바람 깃발 (리소스팩 리본)
    for k in range(4):
        a = k / 4 * 6.28 + 0.8
        px, pz = round(x0 + math.cos(a) * 20), round(z0 + math.sin(a) * 20)
        gy = b.gy(px, pz)
        b.fill(px, gy + 1, pz, px, gy + 6, pz, "birch_fence")
        b.w.display("item", px + 0.5, gy + 5.5, pz + 0.5, model="deco/wind_ribbon", scale=2.2, yaw=math.degrees(a), sway=True)
    # 첨탑 가장자리 방어 난간
    for i in range(180):
        a = i / 180 * 6.28
        px, pz = round(x0 + math.cos(a) * 7.6), round(z0 + math.sin(a) * 7.6)
        if b.top(px, pz) == y and not any(abs(((math.degrees(a) - math.degrees(math.atan2(t[1] - z0, t[0] - x0)) + 540) % 360) - 180) < 14 for t in targets):
            b.set(px, y + 1, pz, wall("stone_brick"))


# ───────────────────────────────────────────── 데메테르: 풍요의 분지
def demeter(b, A, y, ov):
    x0, z0 = int(A[0]), int(A[1])
    rng = b.r
    # 밀밭 구획 4곳
    for k in range(4):
        a = k / 4 * 6.28 + 0.6
        fx, fz = x0 + math.cos(a) * 14, z0 + math.sin(a) * 14
        for x in range(round(fx) - 3, round(fx) + 4):
            for z in range(round(fz) - 2, round(fz) + 3):
                gy = b.gy(x, z)
                if b.T.road[x, z] > 0.2 or b.T.water[x, z] >= 0:
                    continue
                if abs(x - round(fx)) == 3 or abs(z - round(fz)) == 2:
                    b.set(x, gy + 1, z, "oak_fence")
                else:
                    b.set(x, gy, z, "farmland[moisture=7]")
                    b.set(x, gy + 1, z, "wheat[age=7]")
    # 건초 더미 · 도자기
    for k in range(6):
        a = rng.uniform(0, 6.28); d = rng.uniform(9, 12)
        px, pz = round(x0 + math.cos(a) * d), round(z0 + math.sin(a) * d)
        gy = b.top(px, pz)
        b.set(px, gy + 1, pz, "hay_block[axis=y]" if k % 2 else "decorated_pot[cracked=false,facing=north,waterlogged=false]")
    # 넝쿨 퍼걸러 (길 위 아치)
    for k in range(3):
        a = k / 3 * 6.28 + 0.2
        px, pz = round(x0 + math.cos(a) * 19), round(z0 + math.sin(a) * 19)
        gy = b.gy(px, pz)
        for s in (-2, 2):
            qx, qz = round(px - math.sin(a) * s), round(pz + math.cos(a) * s)
            b.fill(qx, gy + 1, qz, qx, gy + 4, qz, "oak_log[axis=y]")
        for s in range(-3, 4):
            qx, qz = round(px - math.sin(a) * s), round(pz + math.cos(a) * s)
            b.set(qx, gy + 5, qz, "oak_planks" if abs(s) < 3 else "oak_slab[type=bottom,waterlogged=false]")
            b.blob(qx, gy + 6, qz, 1.2, 0.6, 1.2, "flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]", 0.6)
    # 오래된 거목 (분지 뒤쪽)
    tx, tz = round(x0 + ov[0] * 14), round(z0 + ov[1] * 14)
    b.tree(tx, b.gy(tx, tz) + 1, tz, "dark_oak", 1.4)
    # 꽃밭
    flowers = ["poppy", "dandelion", "cornflower", "oxeye_daisy", "allium", "azure_bluet", "red_tulip", "lily_of_the_valley"]
    for k in range(260):
        a = rng.uniform(0, 6.28); d = rng.uniform(7, 24)
        px, pz = round(x0 + math.cos(a) * d), round(z0 + math.sin(a) * d)
        gy = b.gy(px, pz)
        if b.w.get(px, gy, pz).startswith("grass_block") and b.w.is_air(px, gy + 1, pz):
            b.set(px, gy + 1, pz, flowers[k % len(flowers)] if rng.random() < 0.6 else "short_grass")
