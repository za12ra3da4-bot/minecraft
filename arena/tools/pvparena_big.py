"""PvP 연습장 (큰 버전) — 석영 원형 대투기장

 지름 ~104칸 (기존 연습장 ~58칸의 약 2배)
 · 가운데 2단 제단 (금 고리 · 바다 랜턴) · 안쪽 엄폐 기둥 8 · 중간 낮은 벽 조각 8
 · 저격 탑 4 (계단으로 올라감) · 바닥 금 문양 3겹 · 방사형 조각 석영 줄 · 바다 랜턴 조명
 · 석영 벽 + 열주 · 입장문 8개 (동서남북 문은 팀 색 장식 · 부활 자리) · 관중석 4단 + 끝 막대 탑
 · 아래는 뒤집힌 석영 섬 (층층이 좁아짐) · 둘레 보이지 않는 벽
"""
import math
import os

import numpy as np

N = 124           # 가로 · 세로
H = 46            # 높이
FL = 16           # 바닥 높이 (격자 안)
C = N // 2
SPAWN_R = 35
FLOOR_R = 40      # 바닥 반지름 (벽 안쪽)

PAL = ["air", "smooth_quartz", "quartz_bricks", "chiseled_quartz_block", "quartz_pillar[axis=y]", "quartz_block",
       "gold_block", "sea_lantern", "smooth_quartz_slab[type=bottom,waterlogged=false]", "barrier",
       "lantern[hanging=false,waterlogged=false]", "calcite", "diorite", "polished_diorite",
       "end_rod[facing=up]",
       "quartz_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]",
       "quartz_stairs[facing=west,half=bottom,shape=straight,waterlogged=false]",
       "red_concrete", "blue_concrete", "lime_concrete", "yellow_concrete",
       "red_stained_glass", "blue_stained_glass", "lime_stained_glass", "yellow_stained_glass",
       "red_glazed_terracotta", "blue_glazed_terracotta", "lime_glazed_terracotta", "yellow_glazed_terracotta"]
P = {s.split("[")[0] if "stairs" not in s else s.split("[")[0] + "_" + s.split("facing=")[1].split(",")[0]: i
     for i, s in enumerate(PAL)}

# 동(0°) · 남(90°) · 서(180°) · 북(270°)  →  팀 색
TEAM_GATES = {270: "red", 0: "blue", 90: "lime", 180: "yellow"}


def build():
    v = np.zeros((N, H, N), np.uint16)
    xx, zz = np.meshgrid(np.arange(N) + 0.5 - C, np.arange(N) + 0.5 - C, indexing="ij")
    r = np.hypot(xx, zz)
    ang = (np.degrees(np.arctan2(zz, xx)) + 360) % 360
    rng = np.random.default_rng(7)

    def adiff(a):
        return np.abs(((ang - a + 180) % 360) - 180)

    def ring(y, r0, r1, blk, extra=None):
        m = (r >= r0) & (r < r1)
        if extra is not None:
            m &= extra
        v[:, y, :][m] = P[blk]

    def disc_at(cx, cz, rad):
        return np.hypot(xx + C - 0.5 - cx, zz + C - 0.5 - cz) < rad

    def polar(a, rad):
        return C - 0.5 + math.cos(math.radians(a)) * rad, C - 0.5 + math.sin(math.radians(a)) * rad

    def ipolar(a, rad):
        x, z = polar(a, rad)
        return int(round(x)), int(round(z))

    # ── 떠 있는 섬 (아래로 좁아짐)
    for k in range(FL):
        y = FL - 1 - k
        rad = 53.5 - k * 2.9 - (k ** 1.7) * 0.22
        if rad < 3:
            break
        m = r < rad + np.sin(np.radians(ang) * 7 + k * 0.7) * 1.1
        blk = "quartz_bricks" if k < 2 else ("calcite" if k % 3 else "diorite")
        v[:, y, :][m] = P[blk]
        if k >= 2:
            rim = m & (r > rad - 1.5)
            v[:, y, :][rim & (rng.random((N, N)) < 0.5)] = P["polished_diorite"]

    # ── 바닥 + 문양
    ring(FL, 0, FLOOR_R + 1, "smooth_quartz")
    for a in range(0, 360, 45):
        m = (adiff(a) * np.pi / 180 * r < 0.6) & (r > 9) & (r < FLOOR_R)
        v[:, FL, :][m] = P["chiseled_quartz_block"]
    for a in range(22, 360, 45):
        m = (adiff(a + 0.5) * np.pi / 180 * r < 0.55) & (r > 28) & (r < FLOOR_R)
        v[:, FL, :][m] = P["quartz_bricks"]
    ring(FL, 10.5, 11.5, "gold_block")
    ring(FL, 18.5, 19.3, "quartz_bricks")
    ring(FL, 27.4, 28.3, "gold_block")
    ring(FL, 37.5, 38.3, "quartz_bricks")
    for a in range(0, 360, 15):
        x, z = ipolar(a + 7.5, 24)
        v[x, FL, z] = P["sea_lantern"]
    for a in range(0, 360, 10):
        x, z = ipolar(a + 5, 33)
        v[x, FL, z] = P["sea_lantern"]

    # ── 가운데 2단 제단 (반 블록 계단으로 걸어 올라감)
    ring(FL + 1, 0, 8, "quartz_bricks")
    ring(FL + 1, 8, 9, "smooth_quartz_slab")
    ring(FL + 2, 0, 5, "smooth_quartz")
    ring(FL + 2, 5, 6, "smooth_quartz_slab")
    ring(FL + 1, 6.6, 7.4, "gold_block")
    ring(FL + 2, 2.4, 3.3, "gold_block")
    ring(FL + 2, 0, 1.5, "sea_lantern")
    for a in range(45, 360, 90):
        x, z = ipolar(a, 7.2)
        v[x, FL + 2, z] = P["lantern"]

    # ── 안쪽 엄폐 기둥 8개 (반지름 14)
    for a in range(0, 360, 45):
        cx, cz = polar(a + 22.5, 14.5)
        m = disc_at(cx, cz, 1.6)
        v[:, FL + 1, :][disc_at(cx, cz, 2.5)] = P["quartz_bricks"]
        for y in range(FL + 1, FL + 6):
            v[:, y, :][m] = P["quartz_pillar"]
        v[:, FL + 6, :][m] = P["chiseled_quartz_block"]
        v[:, FL + 7, :][disc_at(cx, cz, 0.7)] = P["end_rod"]

    # ── 중간 낮은 벽 조각 8개 (반지름 22, 문 방향은 비움)
    for a in range(0, 360, 45):
        d = adiff(a)
        seg = (r > 21.4) & (r < 22.6) & (d > 7) & (d < 22)
        v[:, FL + 1, :][seg] = P["quartz_bricks"]
        v[:, FL + 2, :][seg] = P["smooth_quartz_slab"]

    # ── 바깥 엄폐 블록 (반지름 30, 2칸 높이 상자)
    for a in range(0, 360, 30):
        if a % 90 == 45:
            continue
        x, z = ipolar(a + 15, 30.5)
        v[x - 1:x + 1, FL + 1:FL + 3, z - 1:z + 1] = P["quartz_block"]
        v[x - 1:x + 1, FL + 3, z - 1:z + 1] = P["smooth_quartz_slab"]

    # ── 저격 탑 4개 (45°, 반지름 32) + 계단
    th = 6
    for a in (45, 135, 225, 315):
        tx, tz = ipolar(a, 32)
        x0, x1, z0, z1 = tx - 3, tx + 3, tz - 3, tz + 3
        v[x0:x1 + 1, FL + 1:FL + th, z0:z1 + 1] = P["quartz_bricks"]
        v[x0:x1 + 1, FL + th, z0:z1 + 1] = P["smooth_quartz"]
        for (cx, cz) in ((x0, z0), (x0, z1), (x1, z0), (x1, z1)):
            v[cx, FL + 1:FL + th + 3, cz] = P["quartz_pillar"]
            v[cx, FL + th + 3, cz] = P["chiseled_quartz_block"]
            v[cx, FL + th + 4, cz] = P["lantern"]
        # 난간 (반 블록), 모서리 · 계단 쪽 비움
        for x in range(x0 + 1, x1):
            v[x, FL + th + 1, z0] = P["smooth_quartz_slab"]
            v[x, FL + th + 1, z1] = P["smooth_quartz_slab"]
        for z in range(z0 + 1, z1):
            v[x0, FL + th + 1, z] = P["smooth_quartz_slab"]
            v[x1, FL + th + 1, z] = P["smooth_quartz_slab"]
        v[tx, FL + th, tz] = P["gold_block"]
        # 계단: 가운데 쪽(동서 방향)으로 내려감, 폭 2
        inward = -1 if tx > C else 1
        sx = x0 - 1 if inward < 0 else x1 + 1
        stair = "quartz_stairs_east" if inward < 0 else "quartz_stairs_west"
        for k in range(th):
            x = sx + inward * k
            top = FL + th - k
            for z in (tz - 1, tz):
                v[x, FL + 1:top, z] = P["quartz_bricks"]
                v[x, top, z] = P[stair]
        # 계단 쪽 난간 터 주기
        edge_x = x0 if inward < 0 else x1
        v[edge_x, FL + th + 1, tz - 1] = 0
        v[edge_x, FL + th + 1, tz] = 0

    # ── 벽 (반지름 40~42) + 입장문 8개
    gate = np.zeros((N, N), bool)
    for a in range(0, 360, 45):
        gate |= (adiff(a) * np.pi / 180 * r < 2.6)
    wall = (r >= FLOOR_R) & (r < FLOOR_R + 2)
    for y in range(FL, FL + 6):
        v[:, y, :][wall & ~gate] = P["quartz_bricks"]
    v[:, FL + 6, :][wall & ~gate] = P["smooth_quartz_slab"]
    v[:, FL + 3, :][(r >= FLOOR_R - 0.1) & (r < FLOOR_R + 0.7) & ~gate] = P["gold_block"]
    v[:, FL, :][wall & gate] = P["smooth_quartz"]
    for a in range(0, 360, 45):
        team = TEAM_GATES.get(a)
        for s_ in (-1, 1):
            b = a + s_ * 4.6
            x, z = ipolar(b, FLOOR_R + 1)
            v[x, FL:FL + 9, z] = P["quartz_pillar"]
            v[x, FL + 9, z] = P["chiseled_quartz_block"]
            v[x, FL + 10, z] = P["lantern"]
        d = adiff(a)
        lint = (d * np.pi / 180 * r < 3.6) & (r >= FLOOR_R) & (r < FLOOR_R + 2.2)
        v[:, FL + 7, :][lint] = P["quartz_block"]
        v[:, FL + 8, :][lint] = P["chiseled_quartz_block"]
        top = (d * np.pi / 180 * r < 0.9) & (r >= FLOOR_R) & (r < FLOOR_R + 2.2)
        if team:
            v[:, FL + 8, :][top] = P[team + "_glazed_terracotta"]
            v[:, FL + 9, :][top] = P[team + "_concrete"]
            v[:, FL + 6, :][lint & (d * np.pi / 180 * r < 2.6)] = P[team + "_stained_glass"]
            # 문 앞 바닥 팀 색 표시 (부활 자리)
            sx, sz = polar(a, SPAWN_R)
            v[:, FL, :][disc_at(sx, sz, 1.8) & ~disc_at(sx, sz, 1.0)] = P[team + "_concrete"]
        else:
            v[:, FL + 9, :][top] = P["gold_block"]
    # 열주 (벽 위로 솟은 기둥, 7.5°마다, 문 자리 빼고) + 등불
    for i in range(48):
        a = i * 7.5
        if min(abs(((a - g + 180) % 360) - 180) for g in range(0, 360, 45)) < 6:
            continue
        x, z = ipolar(a, FLOOR_R + 1)
        v[x, FL:FL + 9, z] = P["quartz_pillar"]
        v[x, FL + 9, z] = P["chiseled_quartz_block"]
        v[x, FL + 10, z] = P["lantern"]

    # ── 관중석 4단 (벽 바깥, 문 자리 빼고)
    tiers = ((42, 44, FL + 4), (44, 46, FL + 5), (46, 48, FL + 6), (48, 50, FL + 7))
    for r0, r1, y in tiers:
        m = (r >= r0) & (r < r1) & ~gate
        for yy in range(FL, y + 1):
            v[:, yy, :][m] = P["quartz_bricks" if yy == y else "smooth_quartz"]
        v[:, y, :][m & (r >= r1 - 0.8)] = P["quartz_block"]
    rail = (r >= 49.2) & (r < 50) & ~gate
    v[:, FL + 8, :][rail] = P["smooth_quartz_slab"]
    v[:, FL + 2, :][rail] = P["gold_block"]
    v[:, FL + 5, :][rail] = P["gold_block"]
    # 관중석 뒤 높은 탑 (15°마다) + 끝 막대 빛
    for i in range(24):
        a = i * 15 + 7.5
        if min(abs(((a - g + 180) % 360) - 180) for g in range(0, 360, 45)) < 6:
            continue
        x, z = ipolar(a, 49.5)
        hgt = 15 if i % 2 else 12
        v[x, FL + 8:FL + hgt, z] = P["quartz_pillar"]
        v[x, FL + hgt, z] = P["chiseled_quartz_block"]
        v[x, FL + hgt + 1, z] = P["end_rod"]
    # 문 바깥 통로
    v[:, FL, :][gate & (r >= FLOOR_R + 2) & (r < 52)] = P["smooth_quartz"]
    for a in range(0, 360, 45):
        d = adiff(a)
        side = (d * np.pi / 180 * r >= 2.6) & (d * np.pi / 180 * r < 3.4) & (r >= FLOOR_R + 2) & (r < 52)
        v[:, FL + 1, :][side] = P["smooth_quartz_slab"]

    # ── 보이지 않는 벽
    edge = (r >= 51.5) & (r < 52.7)
    for y in range(FL + 1, H):
        v[:, y, :][edge] = P["barrier"]
    return v


def preview(path):
    import render as R
    from PIL import Image, ImageDraw, ImageFont
    v = build()
    v2 = np.where(v == P["barrier"], 0, v)
    pal = R.Palette(PAL)
    W, Hh = 1000, 620
    shots = [
        ((C + 70, FL + 58, C + 76), (C, FL - 2, C), 55),       # 하늘에서 비스듬히
        ((C + 2, FL + 3, C + 37), (C - 2, FL + 3, C - 4), 70),   # 남쪽(초록) 문에서 안쪽
        ((C + 25, FL + 14, C - 25), (C - 6, FL + 1, C + 6), 70),  # 북동 저격 탑 위에서
    ]
    ims = [R.render(v2, pal, W, Hh, cam, tgt, fov=fov, ss=2, fog_dist=700) for cam, tgt, fov in shots]
    out = Image.new("RGB", (W, Hh * len(ims)))
    labels = ["전체 모습 — 지름 약 104칸 (기존 연습장 약 58칸)",
              "남쪽 초록 문(부활 자리)에서 본 안쪽 — 가운데 제단 · 엄폐 기둥",
              "북동 저격 탑 위에서 내려다본 모습 (계단으로 올라감)"]
    font = None
    for fp in ("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
               "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
               "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"):
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, 26)
            break
    for i, im in enumerate(ims):
        if font:
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, W, 44), fill=(20, 22, 30))
            d.text((14, 7), labels[i], font=font, fill=(255, 230, 140))
        out.paste(im, (0, Hh * i))
    out.save(path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview(sys.argv[1] if len(sys.argv) > 1 else "pvp_arena_big.png")
