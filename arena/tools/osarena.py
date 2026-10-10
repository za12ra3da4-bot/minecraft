"""온리소드 전용 경기장 — 밤하늘에 떠 있는 네온 아레나 (허브 PvP 오락기로 입장, 신화쟁탈전 연습장과 별개)

 · 팔각 경기장 (폭 61) — 검은 바닥 + 빛나는 하늘색 격자 · 가운데 바닥에 거대한 다이아 검 문양
 · 둘레 4칸 유리벽 (빛 난간) · 꼭짓점 네온 탑 8 · 엄폐: 네모 기둥 4 + ㄱ자 낮은 벽 4 · 가운데 낮은 단
 · 머리 위 떠 있는 네온 고리 · 섬 바닥 (허브와 같은 바위)
 원점 = 경기장 가운데 바닥 칸 (데이터팩 storage bg:os origin)
"""
import math
import os

import numpy as np

N = 84
H = 44
FL = 12
C = N // 2
R_OCT = 30          # 팔각 반폭
WALL_H = 4

PAL = ["air", "black_concrete", "gray_concrete", "white_concrete", "light_gray_concrete", "polished_blackstone",
       "sea_lantern", "pearlescent_froglight", "ochre_froglight", "shroomlight",
       "light_blue_stained_glass", "magenta_stained_glass", "cyan_stained_glass", "white_stained_glass",
       "black_stained_glass", "orange_stained_glass", "yellow_stained_glass",
       "smooth_quartz", "smooth_quartz_slab[type=bottom,waterlogged=false]",
       "polished_blackstone_slab[type=bottom,waterlogged=false]", "blue_terracotta", "dark_prismarine",
       "cyan_terracotta", "brown_concrete", "end_rod[facing=up]", "barrier", "diamond_block"]
P = {s.split("[")[0]: i for i, s in enumerate(PAL)}


def octagon(x, z, r):
    return max(abs(x), abs(z)) <= r and abs(x) + abs(z) <= r * 1.42


def build():
    v = np.zeros((N, H, N), np.uint16)
    xx, zz = np.meshgrid(np.arange(N) - C + 0.5, np.arange(N) - C + 0.5, indexing="ij")
    r = np.hypot(xx, zz)
    ang = (np.degrees(np.arctan2(zz, xx)) + 360) % 360

    def put(hx, y, hz, blk):
        gx, gz, y = C + int(math.floor(hx)), C + int(math.floor(hz)), int(y)
        if 0 <= gx < N and 0 <= y < H and 0 <= gz < N:
            v[gx, y, gz] = P[blk]

    def glow(hx, hz, glass, light="sea_lantern"):
        put(hx, FL, hz, glass)
        put(hx, FL - 1, hz, light)

    oct_in = (np.maximum(np.abs(xx), np.abs(zz)) <= R_OCT) & (np.abs(xx) + np.abs(zz) <= R_OCT * 1.42)
    oct_wall = (np.maximum(np.abs(xx), np.abs(zz)) <= R_OCT + 1) & (np.abs(xx) + np.abs(zz) <= (R_OCT + 1) * 1.42) & ~oct_in
    oct_rim = (np.maximum(np.abs(xx), np.abs(zz)) <= R_OCT + 3) & (np.abs(xx) + np.abs(zz) <= (R_OCT + 3) * 1.42)

    # ── 섬 바닥 (허브와 같은 밤바다 바위)
    for k in range(FL):
        y = FL - 1 - k
        rad = (R_OCT + 6) - k * 3.0 - (k ** 1.6) * 0.3
        if rad < 3:
            break
        wob = np.sin(np.radians(ang) * 5 + k) * 1.5
        m = r < rad + wob
        layer = np.where(np.sin(xx * 0.25 + k) + np.cos(zz * 0.3 - k * 0.5) > 0.3, P["dark_prismarine"], P["blue_terracotta"])
        v[:, y, :][m] = layer[m]
    v[:, FL, :][oct_rim] = P["polished_blackstone"]
    v[:, FL - 1, :][oct_rim] = P["polished_blackstone"]

    # ── 바닥: 검은 바닥 + 6칸 네온 격자 (가운데 문양 자리는 비움)
    v[:, FL, :][oct_in] = P["black_concrete"]
    ix = np.floor(xx).astype(int); iz = np.floor(zz).astype(int)
    grid = oct_in & ((np.mod(ix, 6) == 0) | (np.mod(iz, 6) == 0)) & (r > 9.5)
    v[:, FL, :][grid] = P["sea_lantern"]
    # 둘레 안쪽 분홍 네온 줄
    inner = oct_in & ~((np.maximum(np.abs(xx), np.abs(zz)) <= R_OCT - 1) & (np.abs(xx) + np.abs(zz) <= (R_OCT - 1) * 1.42))
    v[:, FL, :][inner] = P["magenta_stained_glass"]
    v[:, FL - 1, :][inner] = P["pearlescent_froglight"]

    # ── 가운데 낮은 단 (반지름 9, 반 칸 + 한 칸) + 거대한 다이아 검 문양
    v[:, FL + 1, :][(r < 9.5) & (r >= 8.5)] = P["polished_blackstone_slab"]
    v[:, FL + 1, :][r < 8.5] = P["black_concrete"]
    for x in range(-9, 10):
        for z in range(-9, 10):
            u = (x - z) / math.sqrt(2)          # 검 길이 방향 (북동 → 남서 대각선)
            w = (x + z) / math.sqrt(2)
            blk = None
            if -1.5 <= u <= 6.8 and abs(w) <= 1.25 - max(0, u - 5.0) * 0.7:
                blk = "diamond_block" if abs(w) > 0.55 else "sea_lantern"
            elif abs(u + 2.4) <= 0.8 and abs(w) <= 3.3:
                blk = "ochre_froglight"
            elif -6.2 <= u <= -3.1 and abs(w) <= 0.6:
                blk = "brown_concrete"
            elif math.hypot(u + 6.9, w) <= 1.15:
                blk = "ochre_froglight"
            if blk and math.hypot(x + 0.5, z + 0.5) < 8.6:
                put(x, FL + 1, z, blk)

    # ── 둘레 유리벽 (4칸) + 위 빛 난간 · 꼭짓점 네온 탑 8
    for y in range(FL + 1, FL + 1 + WALL_H):
        v[:, y, :][oct_wall] = P["black_stained_glass"] if y == FL + 1 else P["light_blue_stained_glass"]
    v[:, FL + 1 + WALL_H, :][oct_wall] = P["sea_lantern"]
    v[:, FL + 1, :][oct_rim & ~oct_wall & ~oct_in] = P["polished_blackstone_slab"]
    a = R_OCT + 1
    b = round((R_OCT + 1) * 0.42)
    corners = [(a, b), (a, -b), (-a, b), (-a, -b), (b, a), (-b, a), (b, -a), (-b, -a)]
    heads = ["sea_lantern", "pearlescent_froglight"]
    for i, (cx, cz) in enumerate(corners):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for y in range(FL + 1, FL + 11):
                    edge = abs(dx) + abs(dz) == 2
                    put(cx + dx, y, cz + dz, "black_concrete" if edge or y % 3 else heads[i % 2])
        for y in range(FL + 11, FL + 13):
            put(cx, y, cz, heads[i % 2])
        put(cx, FL + 13, cz, "end_rod")

    # ── 엄폐: 네모 기둥 4 (동서남북) · ㄱ자 낮은 벽 4 (대각선)
    for cx, cz in ((0, 19), (0, -19), (19, 0), (-19, 0)):
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                for y in range(FL + 1, FL + 6):
                    put(cx + dx, y, cz + dz, "black_concrete")
                put(cx + dx, FL + 6, cz + dz, "polished_blackstone_slab")
        for y in range(FL + 1, FL + 6):
            for dx, dz in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                put(cx + dx, y, cz + dz, "cyan_stained_glass" if y in (FL + 2, FL + 4) else "black_concrete")
                if y in (FL + 2, FL + 4):
                    put(cx + dx * 0.5, y, cz + dz * 0.5, "sea_lantern")
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * 15, sz * 15
            for t in range(0, 6):
                for y in range(FL + 1, FL + 3):
                    put(cx + sx * t, y, cz, "polished_blackstone")
                    put(cx, y, cz + sz * t, "polished_blackstone")
                put(cx + sx * t, FL + 3, cz, "polished_blackstone_slab")
                put(cx, FL + 3, cz + sz * t, "polished_blackstone_slab")
            put(cx, FL + 3, cz, "pearlescent_froglight")

    # ── 머리 위 네온 고리 2 (빛)
    for rr, yy, blk in ((22, FL + 20, "sea_lantern"), (17, FL + 24, "pearlescent_froglight")):
        for t in range(0, 360, 1):
            put(math.cos(math.radians(t)) * rr, yy, math.sin(math.radians(t)) * rr, blk)
    return v


def markers():
    """원점 기준: 가운데 · 부활 자리 8 (가운데를 봄) · 관전 자리"""
    out = {"center": (0.5, 2, 0.5, 0.0)}
    for i in range(8):
        a = i * 45 + 22.5
        x = math.cos(math.radians(a)) * 24
        z = math.sin(math.radians(a)) * 24
        yaw = (math.degrees(math.atan2(-x, z)) + 180) % 360 - 180      # 가운데를 보는 방향
        out[f"spawn_{i}"] = (round(x + 0.5, 2), 1, round(z + 0.5, 2), round(yaw, 1))
    return out


def commands(greedy_boxes):
    v = build()
    cmds = []
    for pid, x0, y0, z0, x1, y1, z1 in greedy_boxes(v):
        st = "minecraft:" + PAL[pid]
        a = f"~{x0 - C} ~{y0 - FL} ~{z0 - C}"
        if (x0, y0, z0) == (x1, y1, z1):
            cmds.append(f"$execute positioned $(x) $(y) $(z) run setblock {a} {st}")
        else:
            cmds.append(f"$execute positioned $(x) $(y) $(z) run fill {a} ~{x1 - C} ~{y1 - FL} ~{z1 - C} {st}")
    return cmds


def forceload_range():
    return (-C, -C, N - 1 - C, N - 1 - C)


def preview(path):
    import render as R
    import hubgen
    from PIL import Image, ImageDraw, ImageFont
    v = build()
    v2 = np.where(v == P["barrier"], 0, v)
    pal = R.Palette(PAL)
    W, Hh = 1000, 560
    shots = [
        ((C + 22.7, FL + 3.0, C + 9.7), (C, FL + 2, C), 95, "온리소드 경기장 — 부활 자리에서 (네온 격자 · 엄폐 기둥 · 유리벽)"),
        ((C + 44, FL + 34, C + 44), (C, FL + 2, C), 60, "하늘에서 — 팔각 경기장 · 가운데 다이아 검 문양"),
    ]
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
    out = Image.new("RGB", (W, Hh * len(shots)))
    for i, (cam, tgt, fov, lab) in enumerate(shots):
        im = R.render(v2, pal, W, Hh, cam, tgt, fov=fov, ss=2, fog_dist=900, **hubgen.NIGHT)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, 40), fill=(4, 12, 28))
        d.text((14, 6), lab, font=font, fill=(140, 220, 255))
        out.paste(im, (0, Hh * i))
    out.save(path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview(sys.argv[1] if len(sys.argv) > 1 else "osarena.png")
