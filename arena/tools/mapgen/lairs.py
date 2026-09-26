"""보스 전용 투기장 4곳 (모서리)

 공통: 평평한 원형 바닥 (반지름 19, 가운데는 비워 보스가 잘 보이게), 테마 벽, 입구 3개,
       보스 소환 마법진 (리소스팩). 기둥은 탈로스(돌진 → 기둥 충돌 기절)만.
 뒤쪽(맵 모서리 방향)에는 투기장 밖에 큰 랜드마크 — 피라미드 / 황금 사과나무 / 거인의 동굴
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


# ───────────────────────────────────────── 공통 도우미
LEAF = "[distance=7,persistent=true,waterlogged=false]"


def outv(lid):
    out = LAIRS[lid][0]
    L = math.hypot(*out)
    return (out[0] / L, out[1] / L)


def cells(x0, z0, r0, r1):
    """r0 <= d < r1 인 칸: (x, z, d, a)"""
    R = int(r1) + 1
    for x in range(x0 - R, x0 + R + 1):
        for z in range(z0 - R, z0 + R + 1):
            d = math.hypot(x - x0, z - z0)
            if r0 <= d < r1:
                yield x, z, d, math.atan2(z - z0, x - x0)


def angdiff(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def h2(*k):
    """정수 해시 → 0..1 (칸/타일별 고정 난수)"""
    v = 2166136261
    for n in k:
        v = ((v ^ (int(n) & 0xffffffff)) * 16777619) & 0xffffffff
    v ^= v >> 13
    v = (v * 1274126177) & 0xffffffff
    return (v & 0xffff) / 65536.0


def local_rect(b, cx, cz, v, hw, hd, y0, y1, fn):
    """방향 v(단위) 기준 회전 사각형: 접선 |t|<=hw, 반지름 |r|<=hd → fn(x, y, z, t, r, k)"""
    R = int(max(hw(0) if callable(hw) else hw, hd(0) if callable(hd) else hd) + 2)
    for x in range(int(cx) - R, int(cx) + R + 1):
        for z in range(int(cz) - R, int(cz) + R + 1):
            dx, dz = x + 0.5 - cx, z + 0.5 - cz
            r = dx * v[0] + dz * v[1]
            t = -dx * v[1] + dz * v[0]
            for yy in range(y0, y1 + 1):
                k = yy - y0
                w_, d_ = (hw(k) if callable(hw) else hw), (hd(k) if callable(hd) else hd)
                if abs(t) <= w_ and abs(r) <= d_:
                    fn(x, yy, z, t, r, k)


def line_cells(ax, az, bx, bz):
    n = int(max(abs(bx - ax), abs(bz - az)) * 2) + 1
    seen = set()
    for i in range(n + 1):
        t = i / n
        c = (round(ax + (bx - ax) * t), round(az + (bz - az) * t))
        if c not in seen:
            seen.add(c)
            yield c


def palm(b, x, y, z, h, lean):
    """야자수: 휘어진 줄기 + 늘어진 잎 6장 (y = 지면 위 첫 칸)"""
    px, pz = x, z
    for k in range(h):
        f = (k / h) ** 2 * 3
        px, pz = round(x + lean[0] * f), round(z + lean[1] * f)
        b.set(px, y + k, pz, "jungle_log[axis=y]")
    ty = y + h
    b.set(px, ty, pz, "jungle_leaves" + LEAF)
    for i in range(7):
        a = i / 7 * 6.283 + h * 0.3
        for s in range(1, 5):
            qx, qz = round(px + math.cos(a) * s), round(pz + math.sin(a) * s)
            b.leaves(qx, ty - (s * s) // 6, qz, "jungle_leaves" + LEAF)


def cypress(b, x, y, z, h):
    b.set(x, y, z, "spruce_log[axis=y]")
    for k in range(1, h + 1):
        rr = 1.25 if 2 <= k <= h - 2 else 0.6
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx * dx + dz * dz <= rr * rr and not (k == h and (dx or dz)):
                    b.leaves(x + dx, y + k, z + dz, "spruce_leaves" + LEAF)
    b.set(x, y + h + 1, z, "spruce_leaves" + LEAF)


# ───────────────────────────────────────── 잊힌 모래 신전 (스핑크스)
def sands(b, x0, y, z0):
    lid = "sands"
    ov = outv(lid)
    back = math.atan2(ov[1], ov[0])
    SAND_R = lambda a: 17.2 + 1.1 * math.sin(a * 5 + 1.3) + 0.7 * math.sin(a * 13 + 0.4)
    # 바닥: 태양 문양 → 상형 띠 → 3x3 판석 → 청록 띠 → 모래 둔덕
    for x, z, d, a in cells(x0, z0, 0, LAIR_R + 0.3):
        sec = int((a + math.pi) / (2 * math.pi) * 24) % 24
        if d < 2.2:
            s_ = "chiseled_sandstone"
        elif d < 3.2:
            s_ = "cut_red_sandstone"
        elif d < 8.6:
            s_ = "cut_red_sandstone" if (sec % 2 == 0 and d > 3.2 + (sec % 4 == 0) * 0) else "smooth_sandstone"
            if sec % 2 == 0 and d > 7.4 and sec % 4 != 0:
                s_ = "smooth_sandstone"        # 짧은 광선 / 긴 광선 번갈아
        elif d < 9.4:
            s_ = "cut_red_sandstone"
        elif d < 10.4:
            s_ = "chiseled_sandstone"
        elif d < 11.2:
            s_ = "cut_red_sandstone"
        elif d < 16.4:
            tx, tz = (x - x0) // 3, (z - z0) // 3
            s_ = "smooth_sandstone" if (tx + tz) % 2 == 0 else "sandstone"
            if h2(tx, tz, 7) < 0.12:
                s_ = "cut_sandstone"
        elif d < 17.2:
            s_ = "gold_block" if sec % 6 == 0 and d < 16.9 else "cyan_terracotta"
        else:
            s_ = "smooth_sandstone"
        if d > SAND_R(a) or (d > 14 and h2(x, z, 3) < 0.10 * (d - 14)):
            s_ = "sand"
        b.set(x, y, z, s_)
        b.set(x, y - 1, z, "sandstone")
        b.air(x, y + 1, z, x, y + 16, z)
        if d > SAND_R(a) + 0.8 and h2(x, z, 9) < 0.5:
            b.set(x, y + 1, z, slab("sandstone"))          # 바람에 쌓인 모래 턱 (반 블록)
    # 벽: 판벽/벽기둥 교대, 상형 띠, 청록 코니스
    H = 12
    NPIL = 36
    for x, z, d, a in cells(x0, z0, LAIR_R + 0.4, LAIR_R + 4.5):
        if in_entrance(x, z, x0, z0, lid):
            continue
        ang = (a + math.pi) / (2 * math.pi) * NPIL
        pil = (ang % 1.0) < 0.3
        top = y + H
        for yy in range(y - 2, top + 1):
            k = yy - y
            if k <= 0:
                m = "smooth_sandstone"
            elif k == 1:
                m = "cut_red_sandstone"
            elif k in (3, 4):
                m = "chiseled_sandstone" if not pil else "cut_sandstone"
            elif k == H - 2:
                m = "gold_block" if pil else "cyan_terracotta"
            elif k == H - 1:
                m = "cut_red_sandstone"
            elif k == H:
                m = "smooth_sandstone"
            else:
                m = "cut_sandstone" if pil else "smooth_sandstone"
            if d > LAIR_R + 1.6 and 0 < k < H:
                m = "sandstone"
            b.set(x, yy, z, m)
        if d < LAIR_R + 1.4:
            b.set(x, top + 1, z, slab("smooth_sandstone"))
        b.air(x, top + 2, z, x, top + 6, z)
    # 입구: 이집트식 탑문 (기울어진 두 탑 + 날개 태양 상인방)
    for v in entrances(x0, z0, lid):
        gx, gz = x0 + 0.5 + v[0] * (LAIR_R + 2.2), z0 + 0.5 + v[1] * (LAIR_R + 2.2)
        tv = (-v[1], v[0])
        for sg in (-1, 1):
            cx, cz = gx + tv[0] * sg * 7.6, gz + tv[1] * sg * 7.6
            PH = 16

            def put(x, yy, z, t, r, k, PH=PH):
                if k == PH:
                    m = slab("smooth_sandstone")
                elif k == PH - 1:
                    m = "smooth_sandstone"
                elif k == PH - 2:
                    m = "cyan_terracotta"
                elif k == PH - 3:
                    m = "cut_red_sandstone"
                elif k in (5, 6) and abs(t) < 1.6:
                    m = "chiseled_sandstone"
                elif k <= 0:
                    m = "smooth_sandstone"
                else:
                    m = "cut_sandstone" if abs(t) > 2.2 or abs(r) > 1.6 else "smooth_sandstone"
                b.set(x, yy, z, m)
            local_rect(b, cx, cz, v, lambda k: 3.2 - min(k, 13) * 0.08, lambda k: 2.4 - min(k, 13) * 0.06, y - 2, y + PH, put)
            b.brazier(round(cx), y + PH + 1, round(cz), mat="polished_blackstone", tall=1)
        # 상인방 (탑 사이, 높이 10~11)

        def lintel(x, yy, z, t, r, k):
            if k == 0:
                b.set(x, yy, z, "cut_red_sandstone")
            else:
                b.set(x, yy, z, "gold_block" if abs(t) < 1.2 else ("cyan_terracotta" if abs(t) < 4.2 else "smooth_sandstone"))
        local_rect(b, gx, gz, v, 5.2, 0.9, y + 10, y + 11, lintel)
    # 오벨리스크 6개 (벽 앞, 1칸 기둥 = 엄폐)
    for i in range(6):
        a = i / 6 * 6.283 + 0.26
        px, pz = round(x0 + math.cos(a) * 15.5), round(z0 + math.sin(a) * 15.5)
        if in_entrance(px, pz, x0, z0, lid, 24) or angdiff(a, back) < 0.45:
            continue
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                b.set(px + dx, y + 1, pz + dz, "cut_red_sandstone" if dx == 0 and dz == 0 else slab("smooth_sandstone"))
        b.fill(px, y + 2, pz, px, y + 9, pz, "smooth_sandstone")
        b.set(px, y + 5, pz, "chiseled_sandstone")
        b.set(px, y + 7, pz, "chiseled_sandstone")
        b.set(px, y + 10, pz, "gold_block")
        b.set(px, y + 11, pz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    # 뒤쪽 제단 + 스핑크스 두상 (중심을 바라봄)
    sx, sz = x0 + 0.5 + ov[0] * 16.2, z0 + 0.5 + ov[1] * 16.2

    def dais(x, yy, z, t, r, k):
        if k == 0:
            b.set(x, yy, z, "cut_red_sandstone" if abs(t) > 3.4 or abs(r) > 1.6 else "smooth_sandstone")
        elif abs(t) <= 3.2 and abs(r) <= 1.4:
            b.set(x, yy, z, "chiseled_sandstone" if k == 1 and abs(t) > 2.4 else "smooth_sandstone")
    local_rect(b, sx, sz, ov, 4.2, 2.3, y + 1, y + 2, dais)
    b.w.display("item", sx + ov[0] * 0.4, y + 3, sz + ov[1] * 0.4, model="deco/sphinx_head", scale=5.0,
                yaw=math.degrees(math.atan2(ov[0], -ov[1])))
    # 뒤쪽 피라미드 (투기장 밖)
    px, pz = x0 + ov[0] * 31, z0 + ov[1] * 31
    base = min(b.gy(round(px + dx), round(pz + dz)) for dx in (-9, 0, 9) for dz in (-9, 0, 9)) - 1
    for k in range(12):
        hw = 11 - k
        m = "smooth_sandstone" if k % 3 else "cut_sandstone"
        b.fill(round(px) - hw, base + k * 2, round(pz) - hw, round(px) + hw, base + k * 2 + 1, round(pz) + hw, m)
    b.fill(round(px) - 1, base + 24, round(pz) - 1, round(px) + 1, base + 24, round(pz) + 1, "gold_block")
    b.set(round(px), base + 25, round(pz), "gold_block")
    # 테두리 위 야자수
    for i in range(9):
        a = i / 9 * 6.283 + 0.35
        if angdiff(a, back) < 0.6:
            continue
        dd = LAIR_R + 7 + (i % 3) * 2
        qx, qz = round(x0 + math.cos(a) * dd), round(z0 + math.sin(a) * dd)
        if in_entrance(qx, qz, x0, z0, lid, 24):
            continue
        g = b.top(qx, qz)
        if g < 0:
            continue
        palm(b, qx, g + 1, qz, 7 + i % 3, (math.cos(a + 2.2), math.sin(a + 2.2)))


# ───────────────────────────────────────── 거인의 채석장 (키클롭스)
QUARRY_CUT = [("stone", 5), ("andesite", 3), ("smooth_stone", 2), ("tuff", 1)]


def quarry(b, x0, y, z0):
    lid = "quarry"
    ov = outv(lid)
    back = math.atan2(ov[1], ov[0])

    def cut(x, yy, z, a, d):
        """잘라낸 암벽: 접선 3칸 x 높이 2칸 블록, 줄마다 엇갈림"""
        row = (yy - y) // 2
        col = int((a + math.pi) * d / 3 + (row % 2) * 0.5)
        r = h2(col, row, 11)
        acc = 0
        for m, w_ in QUARRY_CUT:
            acc += w_ / 11
            if r < acc:
                return m
        return "stone"
    # 바닥: 잘라낸 석판 (벽돌 쌓기처럼 엇갈린 4x3 판)
    for x, z, d, a in cells(x0, z0, 0, LAIR_R + 0.3):
        row = (z - z0) // 3
        tx = (x - x0 + (row % 2) * 2) // 4
        r = h2(tx, row, 5)
        s_ = "smooth_stone" if r < 0.34 else ("stone" if r < 0.72 else ("andesite" if r < 0.9 else "polished_andesite"))
        if d > 13.5 and h2(x, z, 1) < (d - 13.5) * 0.09:
            s_ = "gravel"
        if d < 1.6:
            s_ = "polished_andesite"
        b.set(x, y, z, s_)
        b.set(x, y - 1, z, "stone")
        b.air(x, y + 1, z, x, y + 20, z)
    # 계단식 채석 벽 (3단, 각 4칸 높이 3칸 폭) — 입구는 지형 경사로
    for x, z, d, a in cells(x0, z0, LAIR_R + 0.4, LAIR_R + 9.5):
        if in_entrance(x, z, x0, z0, lid):
            continue
        step = int((d - LAIR_R - 0.4) / 3)
        top = y + 4 * (step + 1)
        g = b.gy(x, z)
        for yy in range(y - 2, top + 1):
            b.set(x, yy, z, cut(x, yy, z, a, d))
        # 단 윗면: 가장자리 매끈한 턱, 안쪽 자갈·돌
        edge = (d - LAIR_R - 0.4) % 3 < 1.0
        b.set(x, top, z, "polished_andesite" if edge else ("gravel" if h2(x, z, 2) < 0.3 else "stone"))
        b.air(x, top + 1, z, x, max(g, top) + 4, z)
    # 바깥 테두리: 마지막 단 뒤를 막아 하늘이 뚫려 보이지 않게 (지형보다 낮은 곳만 채움)
    for x, z, d, a in cells(x0, z0, LAIR_R + 9.5, LAIR_R + 16):
        if in_entrance(x, z, x0, z0, lid, 18):
            continue
        t = b.top(x, z)
        rim = y + 16 + int(h2(x // 2, z // 2, 21) * 2)
        for yy in range(y - 2, max(t, rim)):
            if b.w.is_air(x, yy, z):
                b.set(x, yy, z, cut(x, yy, z, a, d))
        if t < rim:
            b.set(x, rim, z, "grass_block" if h2(x, z, 22) < 0.8 else "coarse_dirt")
    # 채석 블록 더미 (가장자리 엄폐물, 가운데 비움)
    for i in range(5):
        a = i / 5 * 6.283 + 0.5
        if angdiff(a, back) < 0.5:
            continue
        px, pz = round(x0 + math.cos(a) * 15.5), round(z0 + math.sin(a) * 15.5)
        if in_entrance(px, pz, x0, z0, lid, 24):
            continue
        b.fill(px - 1, y + 1, pz - 1, px, y + 2, pz, "smooth_stone")
        b.fill(px, y + 3, pz - 1, px, y + 3, pz, slab("smooth_stone"))
        b.set(px + 1, y + 1, pz, slab("stone"))
        b.set(px - 1, y + 1, pz + 1, "gravel")
    # 거인의 동굴 (뒤쪽 암벽을 파낸 입, 안쪽 뼈·건초)
    cx, cz = x0 + 0.5 + ov[0] * (LAIR_R + 0.5), z0 + 0.5 + ov[1] * (LAIR_R + 0.5)
    tv = (-ov[1], ov[0])
    for x in range(round(cx) - 16, round(cx) + 17):
        for z in range(round(cz) - 16, round(cz) + 17):
            dx, dz = x + 0.5 - cx, z + 0.5 - cz
            r = dx * ov[0] + dz * ov[1]
            t = dx * tv[0] + dz * tv[1]
            if not (-0.5 <= r <= 6.5):
                continue
            shrink = r * 0.18
            for yy in range(y + 1, y + 12):
                e = (t / (5.8 - shrink)) ** 2 + ((yy - y - 1) / (8.5 - shrink * 1.3)) ** 2
                if e < 1.0:
                    b.set(x, yy, z, "air")
                    if yy == y + 1:
                        b.set(x, y, z, "gravel" if h2(x, z, 4) < 0.5 else "stone")
                elif e < 1.25 and r > 0.5:
                    b.set(x, yy, z, "cobblestone" if h2(x, yy, z) < 0.4 else "stone")
    for i in range(7):
        qx, qz = round(cx + ov[0] * (2 + i * 0.6) + tv[0] * ((i % 3) - 1) * 2.4), round(cz + ov[1] * (2 + i * 0.6) + tv[1] * ((i % 3) - 1) * 2.4)
        b.set(qx, y + 1, qz, "bone_block[axis=y]" if i % 2 else "hay_block[axis=y]")
    for sg in (-1, 1):
        lx, lz = round(cx + tv[0] * sg * 6.5 - ov[0]), round(cz + tv[1] * sg * 6.5 - ov[1])
        b.fill(lx, y + 1, lz, lx, y + 4, lz, "spruce_fence")
        b.set(lx, y + 5, lz, "lantern[hanging=false,waterlogged=false]")
    b.w.display("item", cx + tv[0] * 4.2 - ov[0] * 1.2, y + 1, cz + tv[1] * 4.2 - ov[1] * 1.2, model="deco/giant_club", scale=4.0,
                yaw=math.degrees(math.atan2(ov[0], -ov[1])) + 20, tilt=62)
    # 기중기 2대 (3단 위, 붐이 투기장 가장자리 위로)
    for sg in (-1, 1):
        a = back + sg * 1.05
        mx, mz = round(x0 + math.cos(a) * (LAIR_R + 8)), round(z0 + math.sin(a) * (LAIR_R + 8))
        g = b.top(mx, mz)
        top = g + 14
        b.fill(mx, g + 1, mz, mx, top, mz, "spruce_log[axis=y]")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            b.set(mx + dx, g + 1, mz + dz, stairs("spruce", facing_to(-dx, -dz)))
        ex, ez = round(x0 + math.cos(a) * (LAIR_R - 3)), round(z0 + math.sin(a) * (LAIR_R - 3))
        ax_ = "x" if abs(ex - mx) > abs(ez - mz) else "z"
        for (qx, qz) in line_cells(mx, mz, ex, ez):
            b.set(qx, top, qz, f"stripped_spruce_log[axis={ax_}]")
        for (qx, qz) in list(line_cells(mx, mz, ex, ez))[1:4]:
            b.set(qx, top - 1, qz, "spruce_fence")
        for k in range(1, 6):
            b.set(ex, top - k, ez, "iron_chain[axis=y,waterlogged=false]")
        b.fill(ex, top - 7, ez, ex, top - 6, ez, "smooth_stone")
        b.set(mx, top + 1, mz, "lantern[hanging=false,waterlogged=false]")
    # 비계 (벽면 작업대)
    for i in range(4):
        a = back + math.pi + (i - 1.5) * 0.9
        px, pz = round(x0 + math.cos(a) * (LAIR_R + 1.2)), round(z0 + math.sin(a) * (LAIR_R + 1.2))
        if in_entrance(px, pz, x0, z0, lid, 22):
            continue
        for k in range(1, 5):
            b.set(px, y + k, pz, "scaffolding[bottom=false,distance=0,waterlogged=false]")
    # 단 가장자리 등불
    for i in range(14):
        a = i / 14 * 6.283
        for step in (0, 1):
            dd = LAIR_R + 1.0 + step * 3
            px, pz = round(x0 + math.cos(a) * dd), round(z0 + math.sin(a) * dd)
            if in_entrance(px, pz, x0, z0, lid, 20) or angdiff(a, back) < 0.4 or (i + step) % 2:
                continue
            t = y + 4 * (step + 1)
            b.set(px, t + 1, pz, "spruce_fence")
            b.set(px, t + 2, pz, "lantern[hanging=false,waterlogged=false]")


# ───────────────────────────────────────── 헤스페리데스의 정원 (라돈)
FLOWERS = ["poppy", "allium", "cornflower", "oxeye_daisy", "azure_bluet", "lily_of_the_valley", "orange_tulip", "pink_tulip", "dandelion"]


def garden(b, x0, y, z0):
    lid = "garden"
    ov = outv(lid)
    back = math.atan2(ov[1], ov[0])
    spokes = [math.atan2(v[1], v[0]) for v in entrances(x0, z0, lid)] + [back]

    def on_spoke(x, z, d):
        for sa in spokes:
            px, pz = x + 0.5 - x0 - 0.5, z + 0.5 - z0 - 0.5
            along = px * math.cos(sa) + pz * math.sin(sa)
            perp = abs(-px * math.sin(sa) + pz * math.cos(sa))
            if along > 0 and perp < 1.6:
                return True
        return False
    # 바닥: 대리석 중앙 광장 + 네 갈래 길 + 고리 길 + 잔디 화단
    for x, z, d, a in cells(x0, z0, 0, LAIR_R + 0.3):
        sec = int((a + math.pi) / (2 * math.pi) * 16) % 16
        deco = None
        if d < 2.0:
            s_ = "chiseled_quartz_block"
        elif d < 5.6:
            s_ = "calcite" if sec % 2 else "polished_diorite"
        elif d < 6.6:
            s_ = "quartz_bricks"
        elif 13.0 <= d < 15.2:
            s_ = "quartz_bricks" if (d < 13.6 or d > 14.6) else ("calcite" if h2(x, z) < 0.7 else "polished_diorite")
        elif on_spoke(x, z, d) and d < 19:
            s_ = "calcite" if h2(x, z, 2) < 0.75 else "polished_diorite"
        else:
            s_ = "moss_block" if h2(x // 3, z // 3, 8) < 0.12 else "grass_block"
            border = (6.6 <= d < 7.8) or (11.8 <= d < 13.0) or (15.2 <= d < 16.4)
            if border and h2(x, z, 5) < 0.75:
                deco = FLOWERS[int(h2(x, z, 6) * len(FLOWERS))] if h2(x, z, 7) < 0.7 else "pink_petals[facing=north,flower_amount=4]"
            elif h2(x, z, 9) < 0.18:
                deco = "short_grass"
        b.set(x, y, z, s_)
        b.set(x, y - 1, z, "dirt" if s_ in ("grass_block", "moss_block") else "stone_bricks")
        b.air(x, y + 1, z, x, y + 16, z)
        if deco:
            b.set(x, y + 1, z, deco)
    # 뒤쪽 반달 연못 (연꽃잎)
    for x, z, d, a in cells(x0, z0, 16.6, 18.8):
        if angdiff(a, back) < 0.5 and not on_spoke(x, z, d):
            if d < 17.0 or d > 18.4 or angdiff(a, back) > 0.44:
                b.set(x, y, z, "quartz_bricks")
                b.set(x, y + 1, z, "air")
            else:
                b.set(x, y, z, "water")
                b.set(x, y - 1, z, "calcite")
                if h2(x, z, 12) < 0.25:
                    b.set(x, y + 1, z, "lily_pad")
    # 사이프러스 (가늘어서 시야를 막지 않음)
    for i in range(8):
        a = i / 8 * 6.283 + 0.39
        px, pz = round(x0 + math.cos(a) * 17.6), round(z0 + math.sin(a) * 17.6)
        if in_entrance(px, pz, x0, z0, lid, 22) or angdiff(a, back) < 0.62 or on_spoke(px, pz, 17.6):
            continue
        b.set(px, y, pz, "grass_block")
        cypress(b, px, y + 1, pz, 6)
    # 열주랑: 받침 → 대리석 기둥 → 들보, 뒤는 진달래 산울타리
    NCOL = 32
    col_a = [k / NCOL * 2 * math.pi for k in range(NCOL)]
    for x, z, d, a in cells(x0, z0, LAIR_R + 0.4, LAIR_R + 4.2):
        if in_entrance(x, z, x0, z0, lid):
            continue
        b.fill(x, y - 2, z, x, y + 1, z, "mossy_stone_bricks" if h2(x, z, 3) < 0.35 else "stone_bricks")
        b.air(x, y + 2, z, x, y + 14, z)
        if d < LAIR_R + 1.0:
            b.set(x, y + 1, z, "quartz_bricks")
        if d >= LAIR_R + 2.6:
            for yy in range(y + 2, y + 9):
                b.set(x, yy, z, ("flowering_azalea_leaves" if h2(x, yy, z) < 0.3 else "azalea_leaves") + LEAF)
    for a in col_a:
        px, pz = round(x0 + math.cos(a) * (LAIR_R + 1.6)), round(z0 + math.sin(a) * (LAIR_R + 1.6))
        if in_entrance(px, pz, x0, z0, lid, 19):
            continue
        b.set(px, y + 2, pz, "quartz_bricks")
        b.fill(px, y + 3, pz, px, y + 6, pz, "quartz_pillar[axis=y]")
        b.set(px, y + 7, pz, "chiseled_quartz_block")
    for x, z, d, a in cells(x0, z0, LAIR_R + 1.0, LAIR_R + 2.4):
        if in_entrance(x, z, x0, z0, lid, 18):
            continue
        b.set(x, y + 8, z, "smooth_quartz")
        b.set(x, y + 9, z, slab("smooth_quartz"))
        if not b.w.get(x, y + 7, z).startswith("chiseled") and h2(x, z, 13) < 0.45:
            b.set(x, y + 7, z, "flowering_azalea_leaves" + LEAF)
    # 입구: 대리석 문기둥 + 들보 + 삼각 박공
    for v in entrances(x0, z0, lid):
        gx, gz = x0 + 0.5 + v[0] * (LAIR_R + 1.6), z0 + 0.5 + v[1] * (LAIR_R + 1.6)
        tv = (-v[1], v[0])
        tops = []
        for sg in (-1, 1):
            cx, cz = round(gx + tv[0] * sg * 5.6 - 0.5), round(gz + tv[1] * sg * 5.6 - 0.5)
            b.column(cx, cz, y + 1, 9, mat="quartz", width=3)
            tops.append((cx, cz))

        def beam(x, yy, z, t, r, k):
            if k == 0:
                b.set(x, yy, z, "smooth_quartz")
            elif k == 1:
                b.set(x, yy, z, "chiseled_quartz_block" if abs(t) < 1 else "quartz_bricks")
            elif abs(t) < 6.6 - (k - 2) * 2.2:
                b.set(x, yy, z, "smooth_quartz" if abs(t) > 6.6 - (k - 2) * 2.2 - 1.2 else ("gold_block" if abs(t) < 1 and k == 3 else "quartz_bricks"))
        local_rect(b, gx, gz, v, 7.4, 1.2, y + 10, y + 14, beam)
    # 황금 사과나무 (투기장 밖, 뒤쪽 언덕 — 열주 너머로 보임)
    tx, tz = round(x0 + ov[0] * 29), round(z0 + ov[1] * 29)
    g = b.top(tx, tz)
    for dx in range(-8, 9):
        for dz in range(-8, 9):
            if dx * dx + dz * dz <= 64:
                gg = b.top(tx + dx, tz + dz)
                if gg >= 0 and gg < g:
                    b.fill(tx + dx, gg, tz + dz, tx + dx, g, tz + dz, "grass_block" if True else "dirt")
    b.fill(tx - 1, g + 1, tz - 1, tx + 1, g + 10, tz + 1, "oak_wood[axis=y]")
    for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2), (2, 1), (-2, -1), (1, -2), (-1, 2)):
        b.fill(tx + dx, g + 1, tz + dz, tx + dx, g + 1 + (abs(dx) + abs(dz) == 2) * 2, tz + dz, "oak_wood[axis=y]")
        b.set(tx + dx * 2, g + 1, tz + dz * 2, "rooted_dirt")
    tips = [(tx, g + 13, tz)]
    for i in range(6):
        a = i / 6 * 6.283 + 0.4
        L = 6 + (i % 2) * 2
        by = g + 7 + (i % 3)
        for s in range(1, L + 1):
            qx, qz = round(tx + math.cos(a) * s), round(tz + math.sin(a) * s)
            ax_ = "x" if abs(math.cos(a)) > abs(math.sin(a)) else "z"
            b.set(qx, by + s // 2, qz, f"oak_log[axis={ax_}]")
        tips.append((round(tx + math.cos(a) * L), by + L // 2 + 1, round(tz + math.sin(a) * L)))
    for (qx, qy, qz) in tips:
        rr = 4.8 if (qx, qz) != (tx, tz) else 6.0
        b.blob(qx, qy, qz, rr, rr * 0.6, rr, "oak_leaves" + LEAF, 0.8)
        b.blob(qx, qy + 1, qz, rr * 0.8, rr * 0.5, rr * 0.8, "flowering_azalea_leaves" + LEAF, 0.55)
    rng = b.r
    for k in range(26):
        q = tips[k % len(tips)]
        aa = rng.uniform(0, 6.28); dd = rng.uniform(2.5, 4.8)
        b.w.display("item", q[0] + 0.5 + math.cos(aa) * dd, q[1] - 2.2 + rng.uniform(-0.4, 0.6), q[2] + 0.5 + math.sin(aa) * dd,
                    model="minecraft:golden_apple", scale=1.1, yaw=rng.uniform(0, 360), glow=True)
