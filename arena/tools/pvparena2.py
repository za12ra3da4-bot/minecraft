"""PvP 연습장 2 — 용암 투기장 (큰 팔각 흑요석 투기장, 기존 석영 연습장보다 북쪽 하늘)

 폭 ~112칸 (기존 석영 연습장 ~58칸의 약 2배) · 팔각형
 · 가운데 흑요석 제단 (우는 흑요석 · 네더라이트 · 화로 4) — 둘레 용암 해자 + 다리 4개 (밀려 떨어지면 용암!)
 · 현무암 기둥 무리 8 (높이 제각각, 엄폐) · 부서진 흑암 벽 조각 8 · 바닥 마그마 균열 줄
 · 대장간 탑 4 (대각선, 계단으로 올라감, 꼭대기 화로) · 성벽 안쪽 용암 창 (주황 유리 너머 용암)
 · 동서남북 입장문 = 팀 색 (부활 자리) · 관중석 4단 · 불타는 첨탑 · 아래는 현무암 · 마그마 화산섬
 · 둘레 보이지 않는 벽
"""
import math
import os

import numpy as np

N = 120           # 가로 · 세로
H = 50            # 높이
FL = 16           # 바닥 높이 (격자 안)
C = N // 2
# 전장 원점 기준 가운데 바닥 칸 (기존 석영 연습장 (128, 30, -70) 보다 북쪽)
CENTER = (128, 30, -178)
ARENA_OFF = (CENTER[0] - C, CENTER[1] - FL, CENTER[2] - C)
FLOOR_O = 44      # 바닥 (팔각 반지름)
SPAWN_O = 38      # 부활 자리 (입장문 안쪽)
EDGE_O = 57       # 보이지 않는 벽

TEAM_GATES = {270: "red", 0: "blue", 90: "lime", 180: "yellow"}   # 북 · 동 · 남 · 서

PAL = ["air", "polished_blackstone_bricks", "cracked_polished_blackstone_bricks", "chiseled_polished_blackstone",
       "polished_blackstone", "blackstone", "gilded_blackstone", "magma_block", "crying_obsidian", "obsidian",
       "netherite_block", "lava", "basalt[axis=y]", "polished_basalt[axis=y]", "smooth_basalt",
       "deepslate_tiles", "cracked_deepslate_tiles", "polished_deepslate", "chiseled_deepslate", "deepslate_bricks",
       "nether_bricks", "red_nether_bricks", "shroomlight", "soul_lantern[hanging=false,waterlogged=false]",
       "campfire[lit=true,signal_fire=false,waterlogged=false,facing=north]", "netherrack", "fire",
       "orange_stained_glass", "barrier",
       "polished_blackstone_brick_slab[type=bottom,waterlogged=false]",
       "deepslate_tile_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]",
       "deepslate_tile_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]",
       "red_concrete", "blue_concrete", "lime_concrete", "yellow_concrete",
       "red_stained_glass", "blue_stained_glass", "lime_stained_glass", "yellow_stained_glass",
       "red_glazed_terracotta", "blue_glazed_terracotta", "lime_glazed_terracotta", "yellow_glazed_terracotta",
       "raw_gold_block"]


def _key(s):
    b = s.split("[")[0]
    if "stairs" in s:
        b += "_" + s.split("facing=")[1].split(",")[0]
    return b


P = {_key(s): i for i, s in enumerate(PAL)}


def build():
    v = np.zeros((N, H, N), np.uint16)
    xx, zz = np.meshgrid(np.arange(N) + 0.5 - C, np.arange(N) + 0.5 - C, indexing="ij")
    ax, az = np.abs(xx), np.abs(zz)
    o = np.maximum(np.maximum(ax, az), (ax + az) * 0.7071)      # 팔각 거리
    r = np.hypot(xx, zz)
    ang = (np.degrees(np.arctan2(zz, xx)) + 360) % 360
    rng = np.random.default_rng(11)

    def adiff(a):
        return np.abs(((ang - a + 180) % 360) - 180)

    def band(y, o0, o1, blk, m=None):
        mm = (o >= o0) & (o < o1)
        if m is not None:
            mm &= m
        v[:, y, :][mm] = P[blk]

    def polar(a, rad):
        return C - 0.5 + math.cos(math.radians(a)) * rad, C - 0.5 + math.sin(math.radians(a)) * rad

    def ipolar(a, rad):
        x, z = polar(a, rad)
        return int(round(x)), int(round(z))

    def disc(cx, cz, rad):
        return np.hypot(xx + C - 0.5 - cx, zz + C - 0.5 - cz) < rad

    # 동서남북 다리 · 문 통로 (폭 5)
    card = (az <= 2.5) | (ax <= 2.5)

    # ── 화산섬 (아래로 좁아짐 · 현무암 / 흑암 / 마그마 점)
    for k in range(FL):
        y = FL - 1 - k
        rad = EDGE_O - k * 3.0 - (k ** 1.7) * 0.25
        if rad < 3:
            break
        wob = np.sin(np.radians(ang) * 6 + k) * 1.4 + np.sin(np.radians(ang) * 13 + k * 2) * 0.7
        m = o < rad + wob
        layer = np.where(np.sin(xx * 0.31 + k * 0.9) + np.cos(zz * 0.27 - k * 0.6) > 0, P["blackstone"], P["basalt"])
        v[:, y, :][m] = layer[m]
        if k >= 1:
            rim = m & (o > rad + wob - 2)
            v[:, y, :][rim & (rng.random((N, N)) < 0.08)] = P["magma_block"]
    # 섬 아래 매달린 현무암 기둥
    for i in range(40):
        a = rng.uniform(0, 360); rr = rng.uniform(4, 40)
        x, z = ipolar(a, rr)
        top = FL - 1
        while top > 0 and v[x, top, z] != 0:
            top -= 1
        L = int(rng.integers(2, 6))
        v[x, max(0, top - L):top + 1, z] = P["basalt"]

    # ── 바닥
    band(FL, 0, FLOOR_O + 1, "polished_blackstone_bricks")
    crack = rng.random((N, N)) < 0.14
    v[:, FL, :][(o < FLOOR_O) & crack] = P["cracked_polished_blackstone_bricks"]
    # 팔각 띠 (짙은 판암 타일)
    for o0, o1 in ((15, 17), (26, 27), (35, 36.2)):
        band(FL, o0, o1, "deepslate_tiles")
    band(FL, 16, 16.6, "gilded_blackstone")
    # 마그마 균열 (대각선 4줄, 지그재그)
    for a in (45, 135, 225, 315):
        jag = np.sin(r * 0.9) * 0.9
        m = (np.abs(adiff(a) * np.pi / 180 * r + jag) < 0.7) & (o > 13) & (o < FLOOR_O - 1)
        v[:, FL, :][m] = P["magma_block"]
    # 문 쪽 길 (판암 벽돌)
    v[:, FL, :][card & (o >= 13) & (o < FLOOR_O)] = P["deepslate_bricks"]
    v[:, FL, :][card & (o >= 13) & (o < FLOOR_O) & ((ax <= 0.6) | (az <= 0.6))] = P["chiseled_deepslate"]

    # ── 용암 해자 (팔각 9~12) + 다리
    moat = (o >= 9) & (o < 12.5) & ~card
    v[:, FL, :][moat] = P["lava"]
    v[:, FL - 1, :][moat] = P["lava"]
    v[:, FL - 2, :][moat] = P["obsidian"]
    v[:, FL, :][(o >= 12.5) & (o < 13.3)] = P["chiseled_polished_blackstone"]
    v[:, FL, :][(o >= 8.4) & (o < 9) & ~card] = P["obsidian"]
    # 다리: 가장자리 턱 (반 블록) + 가운데 금 줄
    brid = card & (o >= 8.4) & (o < 13.3)
    v[:, FL, :][brid] = P["polished_blackstone"]
    v[:, FL, :][brid & ((ax <= 0.6) | (az <= 0.6))] = P["gilded_blackstone"]
    curb = brid & (((ax > 1.6) & (az > 2.5)) | ((az > 1.6) & (ax > 2.5)))
    v[:, FL + 1, :][curb] = P["polished_blackstone_brick_slab"]

    # ── 가운데 제단
    band(FL, 0, 8.4, "polished_blackstone")
    band(FL + 1, 0, 7.5, "polished_blackstone_bricks")
    band(FL + 1, 6.7, 7.5, "chiseled_polished_blackstone")
    band(FL + 2, 0, 4.6, "crying_obsidian")
    band(FL + 2, 0, 3, "obsidian")
    band(FL + 2, 0, 1.2, "netherite_block")
    v[C - 1:C + 1, FL + 3, C - 1:C + 1] = P["raw_gold_block"]
    v[:, FL + 2, :][(o >= 4.6) & (o < 5.3)] = P["polished_blackstone_brick_slab"]
    for a in (45, 135, 225, 315):
        x, z = ipolar(a, 8.0)
        v[x, FL + 1:FL + 3, z] = P["polished_blackstone_bricks"]
        v[x, FL + 3, z] = P["campfire"]
    for a in (0, 90, 180, 270):
        x, z = ipolar(a, 6.2)
        v[x, FL + 2, z] = P["soul_lantern"]

    # ── 현무암 기둥 무리 (엄폐, 8곳)
    for i, a in enumerate(range(22, 360, 45)):
        cx, cz = polar(a + 0.5, 20.5)
        for j in range(7):
            dx, dz = rng.normal(0, 1.4, 2)
            x, z = int(round(cx + dx)), int(round(cz + dz))
            hgt = int(rng.integers(2, 8))
            v[x, FL + 1:FL + 1 + hgt, z] = P["basalt"]
            if rng.random() < 0.3:
                v[x, FL + hgt, z] = P["polished_basalt"]
        x, z = int(round(cx)), int(round(cz))
        v[x - 1:x + 2, FL + 1:FL + 3, z - 1:z + 2] = P["smooth_basalt"]
        v[x, FL + 1:FL + 9, z] = P["basalt"]
        v[x, FL + 9, z] = P["magma_block"]

    # ── 부서진 흑암 벽 조각 (팔각 30, 문 방향 비움)
    for a in range(0, 360, 45):
        d = adiff(a)
        seg = (o > 29.5) & (o < 31) & (d > 9) & (d < 20)
        hmap = (2 + (np.sin(r * 1.7 + a) > 0).astype(int) + (np.sin(r * 0.6 + a * 2) > 0.5).astype(int))
        for hh in range(1, 5):
            m = seg & (hmap >= hh)
            blk = "polished_blackstone_bricks" if hh < 3 else "cracked_polished_blackstone_bricks"
            v[:, FL + hh, :][m] = P[blk]
        v[:, FL + 1, :][seg & (rng.random((N, N)) < 0.2)] = P["gilded_blackstone"]

    # ── 대장간 탑 4개 (대각선, 팔각 35) + 계단
    th = 7
    for a in (45, 135, 225, 315):
        tx, tz = ipolar(a, 34)
        x0, x1, z0, z1 = tx - 3, tx + 3, tz - 3, tz + 3
        v[x0:x1 + 1, FL + 1:FL + th, z0:z1 + 1] = P["polished_blackstone_bricks"]
        v[x0:x1 + 1, FL + th, z0:z1 + 1] = P["deepslate_tiles"]
        # 마그마 창 (가운데 줄)
        for yy in (FL + 3, FL + 4):
            for (x, z) in ((tx, z0), (tx, z1), (x0, tz), (x1, tz)):
                v[x, yy, z] = P["magma_block"]
        # 모서리 기둥 + 톱니 성가퀴
        for (cx, cz) in ((x0, z0), (x0, z1), (x1, z0), (x1, z1)):
            v[cx, FL + 1:FL + th + 3, cz] = P["polished_basalt"]
            v[cx, FL + th + 3, cz] = P["chiseled_polished_blackstone"]
            v[cx, FL + th + 4, cz] = P["soul_lantern"]
        for x in range(x0 + 1, x1):
            if (x - x0) % 2 == 0:
                v[x, FL + th + 1, z0] = P["polished_blackstone_bricks"]
                v[x, FL + th + 1, z1] = P["polished_blackstone_bricks"]
        for z in range(z0 + 1, z1):
            if (z - z0) % 2 == 0:
                v[x0, FL + th + 1, z] = P["polished_blackstone_bricks"]
                v[x1, FL + th + 1, z] = P["polished_blackstone_bricks"]
        # 꼭대기 화로
        v[tx, FL + th + 1, tz] = P["netherrack"]
        v[tx, FL + th + 2, tz] = P["fire"]
        # 계단 (가운데 쪽 동서 방향으로 내려감, 폭 2)
        inward = -1 if tx > C else 1
        sx = x0 - 1 if inward < 0 else x1 + 1
        stair = "deepslate_tile_stairs_east" if inward < 0 else "deepslate_tile_stairs_west"
        for k in range(th):
            x = sx + inward * k
            top = FL + th - k
            for z in (tz - 1, tz):
                v[x, FL + 1:top, z] = P["polished_blackstone_bricks"]
                v[x, top, z] = P[stair]
        edge_x = x0 if inward < 0 else x1
        v[edge_x, FL + th + 1, tz - 1] = 0
        v[edge_x, FL + th + 1, tz] = 0

    # ── 성벽 (팔각 44~46) + 입장문 4 + 용암 창
    gate = card & (np.minimum(ax, az) <= 3.0)
    wall = (o >= FLOOR_O) & (o < FLOOR_O + 2)
    for y in range(FL, FL + 8):
        v[:, y, :][wall & ~gate] = P["polished_blackstone_bricks"]
    v[:, FL + 2, :][wall & ~gate] = P["red_nether_bricks"]
    v[:, FL + 8, :][wall & ~gate & ((np.round(ang * 2.2).astype(int) % 2) == 0)] = P["polished_blackstone_bricks"]
    v[:, FL, :][wall & gate] = P["deepslate_bricks"]
    # 용암 창: 안쪽 면 움푹 + 주황 유리, 뒤에 용암 (팔각 각 면 2개씩)
    for a in range(0, 360, 15):
        if min(abs(((a - g + 180) % 360) - 180) for g in (0, 90, 180, 270)) < 9:
            continue
        x, z = ipolar(a, FLOOR_O + 0.2)
        # 안쪽 면 칸 찾기 (팔각 벽의 가장 안쪽)
        xi, zi = x, z
        for t in range(6):
            xi2 = int(round(C - 0.5 + math.cos(math.radians(a)) * (FLOOR_O - 2 + t)))
            zi2 = int(round(C - 0.5 + math.sin(math.radians(a)) * (FLOOR_O - 2 + t)))
            if v[xi2, FL + 4, zi2] == P["polished_blackstone_bricks"]:
                xi, zi = xi2, zi2
                break
        xo = int(round(C - 0.5 + math.cos(math.radians(a)) * (FLOOR_O + 2.6)))
        zo = int(round(C - 0.5 + math.sin(math.radians(a)) * (FLOOR_O + 2.6)))
        for yy in range(FL + 3, FL + 7):
            v[xi, yy, zi] = P["orange_stained_glass"]
        # 뒤 칸 용암 (바깥쪽 한 칸)
        xb = int(round(C - 0.5 + math.cos(math.radians(a)) * (np.hypot(xi - C + 0.5, zi - C + 0.5) + 1)))
        zb = int(round(C - 0.5 + math.sin(math.radians(a)) * (np.hypot(xi - C + 0.5, zi - C + 0.5) + 1)))
        if (xb, zb) != (xi, zi) and v[xb, FL + 4, zb] == P["polished_blackstone_bricks"]:
            for yy in range(FL + 3, FL + 7):
                v[xb, yy, zb] = P["lava"]
        v[xi, FL + 7, zi] = P["chiseled_polished_blackstone"]
        v[xi, FL + 8, zi] = P["soul_lantern"]
        _ = (xo, zo)
    # 입장문 아치 + 팀 색
    for a in (0, 90, 180, 270):
        team = TEAM_GATES[a]
        for s_ in (-1, 1):
            # 문 양옆 기둥
            b = math.radians(a)
            px_ = C - 0.5 + math.cos(b) * (FLOOR_O + 1) - math.sin(b) * 3.6 * s_
            pz_ = C - 0.5 + math.sin(b) * (FLOOR_O + 1) + math.cos(b) * 3.6 * s_
            x, z = int(round(px_)), int(round(pz_))
            v[x, FL:FL + 11, z] = P["polished_basalt"]
            v[x, FL + 11, z] = P["chiseled_polished_blackstone"]
            v[x, FL + 12, z] = P["netherrack"]
            v[x, FL + 13, z] = P["fire"]
        lint = gate & wall
        lint &= (adiff(a) < 20)
        v[:, FL + 7, :][lint] = P["polished_blackstone_bricks"]
        v[:, FL + 8, :][lint] = P["chiseled_polished_blackstone"]
        v[:, FL + 6, :][lint] = P[team + "_stained_glass"]
        mid = lint & ((ax <= 0.6) | (az <= 0.6))
        v[:, FL + 8, :][mid] = P[team + "_glazed_terracotta"]
        v[:, FL + 9, :][mid] = P[team + "_concrete"]
        sx, sz = polar(a, SPAWN_O)
        v[:, FL, :][disc(sx, sz, 2.0) & ~disc(sx, sz, 1.1)] = P[team + "_concrete"]

    # ── 관중석 4단 (성벽 바깥)
    tiers = ((46, 48, FL + 4), (48, 50, FL + 5), (50, 52, FL + 6), (52, 54, FL + 7))
    for o0, o1, y in tiers:
        m = (o >= o0) & (o < o1) & ~gate
        for yy in range(FL, y + 1):
            v[:, yy, :][m] = P["deepslate_tiles" if yy == y else "polished_deepslate"]
        v[:, y, :][m & (o >= o1 - 0.8)] = P["deepslate_bricks"]
    rail = (o >= 54) & (o < 55) & ~gate
    for yy in range(FL, FL + 9):
        v[:, yy, :][rail] = P["polished_blackstone_bricks"]
    v[:, FL + 3, :][rail] = P["shroomlight"]
    v[:, FL + 9, :][rail & ((np.round(ang * 2).astype(int) % 2) == 0)] = P["polished_blackstone_bricks"]
    # 불타는 첨탑 (팔각 모서리마다 + 사이)
    for i in range(16):
        a = i * 22.5 + 11.25
        if min(abs(((a - g + 180) % 360) - 180) for g in (0, 90, 180, 270)) < 8:
            continue
        x, z = ipolar(a, 54.5 / max(math.cos(math.radians((a % 45) - 22.5)), 0.92))
        hgt = 17 if i % 2 == 0 else 13
        v[x, FL + 9:FL + hgt, z] = P["basalt"]
        v[x, FL + hgt - 3, z] = P["magma_block"]
        v[x, FL + hgt, z] = P["netherrack"]
        v[x, FL + hgt + 1, z] = P["fire"]
    # 문 바깥 통로
    v[:, FL, :][gate & (o >= FLOOR_O + 2) & (o < EDGE_O)] = P["deepslate_bricks"]

    # ── 보이지 않는 벽
    edge = (o >= EDGE_O - 0.5) & (o < EDGE_O + 0.7)
    for y in range(FL + 1, H):
        v[:, y, :][edge] = P["barrier"]
    _seal_lava(v)
    return v


def _seal_lava(v):
    """옆이나 아래가 비어 있는 용암은 흘러넘치므로 마그마로 바꾼다 (위가 열린 해자는 괜찮음)"""
    open_ = {0, P["fire"]}
    while True:
        xs, ys, zs = np.where(v == P["lava"])
        bad = []
        for x, y, z in zip(xs, ys, zs):
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0)):
                if v[x + dx, y + dy, z + dz] in open_:
                    bad.append((x, y, z))
                    break
        if not bad:
            return
        for x, y, z in bad:
            v[x, y, z] = P["magma_block"]


def commands(greedy_boxes):
    v = build()
    ox, oy, oz = ARENA_OFF
    cmds = []
    for pid, x0, y0, z0, x1, y1, z1 in greedy_boxes(v):
        st = "minecraft:" + PAL[pid]
        a = f"~{ox + x0} ~{oy + y0} ~{oz + z0}"
        if (x0, y0, z0) == (x1, y1, z1):
            cmds.append(f"$execute positioned $(x) $(y) $(z) run setblock {a} {st}")
        else:
            cmds.append(f"$execute positioned $(x) $(y) $(z) run fill {a} ~{ox + x1} ~{oy + y1} ~{oz + z1} {st}")
    return cmds


def forceload_range():
    ox, oy, oz = ARENA_OFF
    return (ox, oz, ox + N - 1, oz + N - 1)


DUSK = dict(sun=(-0.55, 0.42, -0.30), sun_col=(1.25, 0.72, 0.45), amb_col=(0.48, 0.40, 0.44),
            sky_top=(0.20, 0.12, 0.22), sky_hor=(0.96, 0.52, 0.30), fog_col=(0.62, 0.36, 0.30))


def preview(path):
    import render as R
    from PIL import Image, ImageDraw, ImageFont
    v = build()
    v2 = np.where(v == P["barrier"], 0, v)
    pal = R.Palette(PAL)
    W, Hh = 1000, 620
    shots = [
        ((C + 76, FL + 62, C + 80), (C, FL - 4, C), 52),
        ((C + 1.5, FL + 3, C + 39), (C - 1, FL + 3, C - 4), 72),
        ((C + 31, FL + 19, C - 31), (C - 4, FL + 1, C + 4), 66),
    ]
    ims = [R.render(v2, pal, W, Hh, cam, tgt, fov=fov, ss=2, fog_dist=700, **DUSK) for cam, tgt, fov in shots]
    labels = ["용암 투기장 — 폭 약 112칸 팔각 (석영 연습장 약 58칸)",
              "남쪽 초록 문(부활 자리)에서 — 용암 해자 · 다리 · 흑요석 제단",
              "대장간 탑 위에서 — 현무암 기둥 엄폐 · 마그마 균열"]
    font = None
    for fp in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",):
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, 26)
    out = Image.new("RGB", (W, Hh * len(ims)))
    for i, im in enumerate(ims):
        if font:
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, W, 44), fill=(24, 12, 10))
            d.text((14, 7), labels[i], font=font, fill=(255, 170, 80))
        out.paste(im, (0, Hh * i))
    out.save(path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview(sys.argv[1] if len(sys.argv) > 1 else "pvp_arena2.png")
