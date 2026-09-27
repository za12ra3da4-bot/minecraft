"""PvP 연습장 — 석영 원형 투기장 (전장 맵 북쪽 바깥 하늘에 떠 있는 섬)

 지름 ~58칸: 석영 바닥 (금 문양 · 바다 랜턴 조명) · 엄폐 기둥 4 · 낮은 벽 조각 · 석영 벽 + 기둥 열주 · 관중석 3단
 · 동서남북 입장문 (부활 자리) · 아래는 뒤집힌 석영 섬 (층층이 좁아짐) · 둘레 보이지 않는 벽
 원점(전장 원점) 기준 위치: ARENA_OFF (가운데 바닥)
"""
import math
import os

import numpy as np

N = 64            # 가로 · 세로
H = 30            # 높이
FL = 12           # 바닥 높이 (격자 안)
C = N // 2
# 전장 원점 기준: 가운데 바닥 칸 = (128, 30, -70)
ARENA_OFF = (128 - C, 30 - FL, -70 - C)
SPAWN_R = 17

PAL = ["air", "smooth_quartz", "quartz_bricks", "chiseled_quartz_block", "quartz_pillar[axis=y]", "quartz_block",
       "gold_block", "sea_lantern", "smooth_quartz_slab[type=bottom,waterlogged=false]", "barrier",
       "lantern[hanging=false,waterlogged=false]", "calcite", "diorite", "polished_diorite", "white_concrete",
       "light_blue_stained_glass", "quartz_slab[type=bottom,waterlogged=false]", "end_rod[facing=up]"]
P = {s.split("[")[0]: i for i, s in enumerate(PAL)}


def build():
    v = np.zeros((N, H, N), np.uint16)
    xx, zz = np.meshgrid(np.arange(N) + 0.5 - C, np.arange(N) + 0.5 - C, indexing="ij")
    r = np.hypot(xx, zz)
    ang = (np.degrees(np.arctan2(zz, xx)) + 360) % 360
    rng = np.random.default_rng(5)

    def ring(y, r0, r1, blk):
        m = (r >= r0) & (r < r1)
        v[:, y, :][m] = P[blk]

    # ── 떠 있는 섬 (아래로 좁아지는 석영 · 방해석 층)
    for k in range(FL):
        y = FL - 1 - k
        rad = 29.5 - k * 2.1 - (k ** 1.6) * 0.25
        if rad < 2:
            break
        m = r < rad + (np.sin(np.radians(ang) * 5 + k) * 0.8)
        blk = "quartz_bricks" if k < 2 else ("calcite" if k % 3 else "diorite")
        v[:, y, :][m] = P[blk]
        if k >= 2:
            rim = m & (r > rad - 1.2)
            v[:, y, :][rim & (rng.random((N, N)) < 0.5)] = P["polished_diorite"]
    # ── 바닥
    ring(FL, 0, 21, "smooth_quartz")
    ring(FL, 20, 21, "quartz_bricks")
    # 방사형 줄 (8방향 조각 석영)
    for a in range(0, 360, 45):
        d = np.abs(((ang - a + 180) % 360) - 180)
        m = (d * np.pi / 180 * r < 0.6) & (r > 5) & (r < 20)
        v[:, FL, :][m] = P["chiseled_quartz_block"]
    # 가운데 문양: 금 고리 + 조각 석영 + 바다 랜턴
    ring(FL, 3.5, 4.6, "gold_block")
    ring(FL, 0, 1.6, "sea_lantern")
    ring(FL, 8.6, 9.4, "quartz_bricks")
    ring(FL, 14.5, 15.3, "gold_block")
    # 조명: 바다 랜턴 (바닥에 박음, 30° 마다)
    for a in range(15, 360, 30):
        x = int(round(C - 0.5 + math.cos(math.radians(a)) * 12))
        z = int(round(C - 0.5 + math.sin(math.radians(a)) * 12))
        v[x, FL, z] = P["sea_lantern"]
    # ── 엄폐물: 두꺼운 석영 기둥 4개 (45°, 반지름 10) + 낮은 벽 조각 (반지름 16)
    for a in (45, 135, 225, 315):
        cx = C - 0.5 + math.cos(math.radians(a)) * 10
        cz = C - 0.5 + math.sin(math.radians(a)) * 10
        m = np.hypot(xx + C - 0.5 - cx, zz + C - 0.5 - cz) < 1.6
        for y in range(FL + 1, FL + 6):
            v[:, y, :][m] = P["quartz_pillar"]
        v[:, FL + 6, :][m] = P["chiseled_quartz_block"]
        v[:, FL + 1, :][np.hypot(xx + C - 0.5 - cx, zz + C - 0.5 - cz) < 2.4] = P["quartz_bricks"]
        v[:, FL + 1, :][m] = P["quartz_pillar"]
    for a in range(0, 360, 90):
        d = np.abs(((ang - a + 180) % 360) - 180)
        seg = (r > 15.5) & (r < 16.6) & (d > 14) & (d < 34)
        v[:, FL + 1, :][seg] = P["quartz_bricks"]
        v[:, FL + 2, :][seg] = P["smooth_quartz_slab"]
    # ── 벽 (반지름 21~23) + 입장문 4개
    gate = np.zeros((N, N), bool)
    for a in (0, 90, 180, 270):
        d = np.abs(((ang - a + 180) % 360) - 180)
        gate |= (d * np.pi / 180 * r < 2.2)
    wall = (r >= 21) & (r < 23)
    for y in range(FL, FL + 5):
        v[:, y, :][wall & ~gate] = P["quartz_bricks"]
    v[:, FL + 5, :][wall & ~gate] = P["smooth_quartz_slab"]
    v[:, FL, :][wall & gate] = P["smooth_quartz"]
    # 입장문 아치 (문 양옆 기둥 + 위 인방 + 금 장식)
    for a in (0, 90, 180, 270):
        for s_ in (-1, 1):
            b = math.radians(a + s_ * 6.5)
            x = int(round(C - 0.5 + math.cos(b) * 22)); z = int(round(C - 0.5 + math.sin(b) * 22))
            v[x, FL:FL + 8, z] = P["quartz_pillar"]
            v[x, FL + 8, z] = P["chiseled_quartz_block"]
        d = np.abs(((ang - a + 180) % 360) - 180)
        lint = (d * np.pi / 180 * r < 3.2) & (r >= 21) & (r < 23.2)
        v[:, FL + 6, :][lint] = P["quartz_block"]
        v[:, FL + 7, :][lint] = P["chiseled_quartz_block"]
        top = (d * np.pi / 180 * r < 0.8) & (r >= 21) & (r < 23.2)
        v[:, FL + 8, :][top] = P["gold_block"]
    # 열주: 벽 위로 솟은 기둥 (15° 마다, 문 자리 빼고) + 위에 등불
    for a in range(0, 360, 15):
        if a % 90 == 0:
            continue
        x = int(round(C - 0.5 + math.cos(math.radians(a)) * 22)); z = int(round(C - 0.5 + math.sin(math.radians(a)) * 22))
        v[x, FL:FL + 8, z] = P["quartz_pillar"]
        v[x, FL + 8, z] = P["chiseled_quartz_block"]
        v[x, FL + 9, z] = P["lantern"]
    # ── 관중석 3단 (벽 바깥, 문 자리 빼고)
    for k, (r0, r1, y) in enumerate(((23, 25, FL + 4), (25, 27, FL + 5), (27, 29, FL + 6))):
        m = (r >= r0) & (r < r1) & ~gate
        for yy in range(FL, y + 1):
            v[:, yy, :][m] = P["quartz_bricks" if yy == y else "smooth_quartz"]
        v[:, y, :][m & (r >= r1 - 0.8)] = P["quartz_block"]
    # 관중석 뒤 난간 + 금 띠
    rail = (r >= 28.2) & (r < 29) & ~gate
    v[:, FL + 7, :][rail] = P["smooth_quartz_slab"]
    band = (r >= 28.2) & (r < 29) & ~gate
    v[:, FL + 2, :][band] = P["gold_block"]
    # 관중석 뒤 기둥 + 끝 막대 빛 (22.5° 마다)
    for a in range(0, 360, 30):
        if a % 90 == 0:
            continue
        x = int(round(C - 0.5 + math.cos(math.radians(a + 7.5)) * 28.5)); z = int(round(C - 0.5 + math.sin(math.radians(a + 7.5)) * 28.5))
        v[x, FL + 7:FL + 11, z] = P["quartz_pillar"]
        v[x, FL + 11, z] = P["chiseled_quartz_block"]
        v[x, FL + 12, z] = P["end_rod"]
    # 문 바깥 통로 (섬 가장자리까지)
    v[:, FL, :][gate & (r >= 23) & (r < 30)] = P["smooth_quartz"]
    # ── 보이지 않는 벽 (둘레, 떨어지지 않게) + 천장 없음
    edge = (r >= 29) & (r < 30.2)
    for y in range(FL + 1, H):
        v[:, y, :][edge] = P["barrier"]
    return v


def spawns():
    """연습장 원점 기준 부활 자리 (가운데 바닥 = 0,0,0)"""
    out = []
    for a in (0, 90, 180, 270):
        out.append((math.cos(math.radians(a)) * SPAWN_R, 1, math.sin(math.radians(a)) * SPAWN_R))
    return out


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


def preview(path):
    import render as R
    v = build()
    v2 = np.where(v == P["barrier"], 0, v)
    pal = R.Palette(PAL)
    shots = [((C + 40, FL + 26, C + 44), (C, FL + 2, C)), ((C + 3, FL + 4, C + 17), (C - 6, FL + 3, C - 8))]
    from PIL import Image
    ims = [R.render(v2, pal, 900, 560, cam, tgt, fov=58, ss=2, fog_dist=500) for cam, tgt in shots]
    W = Image.new("RGB", (900, 1120))
    W.paste(ims[0], (0, 0)); W.paste(ims[1], (0, 560))
    W.save(path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview(sys.argv[1] if len(sys.argv) > 1 else "pvp_arena.png")
