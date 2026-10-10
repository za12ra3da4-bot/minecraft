"""포털 파쿠르 — 허브 로봇의 고리(포털)로 들어가면 오는 우주 네온 파쿠르 (허브 남쪽 하늘)

 가운데 빛나는 행성 둘레를 나선으로 돌며 올라가는 50단 점프 · 구간마다 색이 바뀜 (하늘 → 보라 → 분홍 → 주황 → 금)
 체크포인트 없음 (떨어지면 처음부터) · 10단마다 큰 발판 + 빛 고리 아치 · 둘레 행성 7 · 별가루 · 꼭대기 트로피
 원점 = 시작 발판 가운데 바닥 칸 (데이터팩 storage bg:pk origin)
"""
import math
import os

import numpy as np

N = 128
H = 96
FL = 20
C = N // 2
JUMPS = 50
CP_EVERY = 10

PAL = ["air"]
P = {"air": 0}


def pid(s):
    if s not in P:
        P[s] = len(PAL)
        PAL.append(s)
    return P[s]


SECT = [("light_blue_concrete", "light_blue_stained_glass", "sea_lantern"),
        ("purple_concrete", "magenta_stained_glass", "pearlescent_froglight"),
        ("pink_concrete", "pink_stained_glass", "pearlescent_froglight"),
        ("orange_concrete", "orange_stained_glass", "shroomlight"),
        ("yellow_concrete", "yellow_stained_glass", "ochre_froglight")]


def course():
    """점프 자리 목록: (x, y, z, 종류) — 나선 (반지름 18~26) 으로 돌며 올라감"""
    rng = np.random.default_rng(5)
    pts = []
    ang, rad, y = 90.0, 22.0, 0
    x, z = math.cos(math.radians(ang)) * rad, math.sin(math.radians(ang)) * rad
    for i in range(JUMPS):
        dy = 1 if rng.random() < 0.55 else 0
        dist = 3 if dy else int(rng.integers(3, 5))
        rad = max(16, min(28, rad + rng.uniform(-1.5, 1.5)))
        ang -= math.degrees(dist / rad) * 1.15
        nx, nz = math.cos(math.radians(ang)) * rad, math.sin(math.radians(ang)) * rad
        y += dy
        kind = "big" if (i + 1) % CP_EVERY == 0 else pick_kind(rng, i)
        pts.append((round(nx), y, round(nz), kind))
    return pts


def pick_kind(rng, i):
    r = rng.random()
    if i < 5:
        return "block2"
    if r < 0.45:
        return "block"
    if r < 0.65:
        return "block2"
    if r < 0.8:
        return "slab"
    if r < 0.9:
        return "pillar"
    return "glass"


def build():
    v = np.zeros((N, H, N), np.uint16)
    marks = {}

    def put(x, y, z, blk):
        gx, gz, y = C + int(math.floor(x)), C + int(math.floor(z)), int(y)
        if 0 <= gx < N and 0 <= y < H and 0 <= gz < N:
            v[gx, y, gz] = pid(blk)

    # 시작 발판 (5×5, 빛 테두리) — 원점
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            edge = abs(dx) == 2 or abs(dz) == 2
            put(dx, FL, dz, "sea_lantern" if edge else "white_concrete")
            put(dx, FL - 1, dz, "light_gray_concrete")
    marks["start"] = (0.5, 1, 0.5, 0.0)
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if max(abs(dx), abs(dz)) == 3:
                put(dx, FL, dz, "light_blue_stained_glass")
                put(dx, FL - 1, dz, "sea_lantern")
    # 시작 → 첫 점프는 남쪽 (z+), 코스는 시작 발판 기준 (sx, sz) 만큼 옮김
    pts = course()
    sx, sz = 0 - pts[0][0], 4 - pts[0][2]
    cp = 0
    for i, (x, y, z, kind) in enumerate(pts):
        x += sx; z += sz
        base, glass, light = SECT[min(len(SECT) - 1, i * len(SECT) // JUMPS)]
        yy = FL + y
        if kind == "big":
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    put(x + dx, yy, z + dz, glass if dx or dz else light)
                    put(x + dx, yy - 1, z + dz, light)
            # 머리 위 빛 고리 (지나가는 문)
            for t in range(0, 360, 8):
                a = math.radians(t)
                gx, gy = math.cos(a) * 3.2, math.sin(a) * 3.2
                if gy > -0.5:
                    put(x + gx, yy + 1 + gy, z, light)
        elif kind == "block":
            put(x, yy, z, base)
            put(x, yy - 1, z, glass)
            put(x, yy - 2, z, light)
        elif kind == "block2":
            for dx in (0, 1):
                for dz in (0, 1):
                    put(x + dx, yy, z + dz, base if (dx + dz) % 2 == 0 else glass)
                    put(x + dx, yy - 1, z + dz, light)
        elif kind == "slab":
            put(x, yy, z, f"smooth_quartz_slab[type=top,waterlogged=false]")
            put(x, yy - 1, z, light)
        elif kind == "pillar":
            for k in range(0, 6):
                put(x, yy - k, z, base if k == 0 else glass)
            put(x, yy - 6, z, light)
        else:
            put(x, yy, z, glass)
            put(x, yy - 1, z, light)
    # 결승 발판 (마지막 점프 다음, 5×5 금) + 트로피
    lx, ly, lz, _ = pts[-1]
    lx += sx; lz += sz
    fx, fz = lx + (2 if lx < 0 else -2), lz
    fx = int(round(fx * 0.6)); fz = int(round(fz * 0.6))
    fy = FL + ly + 1
    # 마지막 점프 → 결승까지 빛 계단 (2칸 간격)
    steps = max(1, int(math.hypot(fx - lx, fz - lz) // 3))
    for k in range(1, steps):
        px = lx + (fx - lx) * k / steps
        pz = lz + (fz - lz) * k / steps
        put(px, FL + ly, pz, "yellow_concrete")
        put(px, FL + ly - 1, pz, "ochre_froglight")
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            edge = max(abs(dx), abs(dz)) == 3
            put(fx + dx, fy, fz + dz, "ochre_froglight" if edge else "gold_block")
            put(fx + dx, fy - 1, fz + dz, "yellow_concrete")
    for y in range(fy + 1, fy + 3):
        put(fx, y, fz, "gold_block")
    put(fx, fy + 3, fz, "beacon")
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        put(fx + dx, fy + 3, fz + dz, "gold_block")
    put(fx, fy + 4, fz, "end_rod[facing=up]")
    marks["finish"] = (fx + 0.5, fy - FL + 1, fz + 2.5, 0.0)
    # 가운데 행성 (빛 · 고리) — 코스가 그 둘레를 돎
    pcx, pcz = sx, sz
    pcy = FL + 14
    for x in range(-9, 10):
        for y in range(-9, 10):
            for z in range(-9, 10):
                d = math.sqrt(x * x + y * y + z * z)
                if d <= 8.5:
                    band = math.sin(y * 0.9 + x * 0.2) > 0.1
                    put(pcx + x, pcy + y, pcz + z, ("pearlescent_froglight" if band else "purple_stained_glass") if d > 6.5 else "sea_lantern")
    for t in range(0, 360, 2):
        for rr in (12, 13):
            x = math.cos(math.radians(t)) * rr
            z = math.sin(math.radians(t)) * rr
            put(pcx + x, pcy + x * 0.25, pcz + z, "light_blue_stained_glass" if rr == 12 else "sea_lantern")
    # 우주 배경: 빛나는 행성들 (겉 띠 + 색유리 · 안쪽 빛) · 고리 행성 · 별가루
    rng = np.random.default_rng(11)

    def sphere(cx, cy, cz, rad, light, glass, band, ring=None):
        for x in range(int(-rad) - 1, int(rad) + 2):
            for y in range(int(-rad) - 1, int(rad) + 2):
                for z in range(int(-rad) - 1, int(rad) + 2):
                    d = math.sqrt(x * x + y * y + z * z)
                    if d <= rad:
                        blk = light if d < rad - 2 else (band if math.sin(y * 1.1 + x * 0.2) > 0.15 else glass)
                        put(cx + x, cy + y, cz + z, blk)
        if ring:
            for t in range(0, 360, 2):
                for rr in (rad + 3, rad + 4):
                    x = math.cos(math.radians(t)) * rr
                    z = math.sin(math.radians(t)) * rr
                    put(cx + x, cy + x * 0.3, cz + z, ring if rr == rad + 3 else "sea_lantern")
    planets = [(-48, 30, -40, 7, "sea_lantern", "cyan_stained_glass", "sea_lantern", "light_blue_stained_glass"),
               (50, 46, -10, 8, "shroomlight", "orange_stained_glass", "shroomlight", "yellow_stained_glass"),
               (-40, 62, 30, 5, "pearlescent_froglight", "magenta_stained_glass", "pearlescent_froglight", None),
               (40, 18, 40, 4, "verdant_froglight", "lime_stained_glass", "verdant_froglight", None),
               (8, 72, -50, 6, "pearlescent_froglight", "purple_stained_glass", "pearlescent_froglight", "pink_stained_glass"),
               (-55, 8, 10, 3, "ochre_froglight", "yellow_stained_glass", "glowstone", None),
               (30, 70, 45, 3, "sea_lantern", "blue_stained_glass", "sea_lantern", None)]
    # 코스와 겹치면 (행성 겉 + 고리 + 5칸 안에 점프 자리) 가운데에서 바깥쪽으로 밀어냄
    cpts = [(x + sx, FL + y, z + sz) for x, y, z, _ in pts] + [(fx, fy, fz)]
    for cx, cy, cz, rad, li, gl, bd, rg in planets:
        clear = rad + (4 if rg else 0) + 5
        for _ in range(40):
            near = min(math.dist((sx + cx, FL + cy, sz + cz), q) for q in cpts)
            if near >= clear:
                break
            k = math.hypot(cx, cz) or 1.0
            cx, cz = cx + cx / k * 2, cz + cz / k * 2
        sphere(sx + cx, FL + cy, sz + cz, rad, li, gl, bd, rg)
    for _ in range(260):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(34, 60)
        x, z = sx + math.cos(a) * rr, sz + math.sin(a) * rr
        y = FL + rng.uniform(-10, 74)
        put(x, y, z, "end_rod[facing=up]" if rng.random() < 0.5 else ("sea_lantern" if rng.random() < 0.7 else "pearlescent_froglight"))
    return v, marks


def markers():
    return build()[1]


def commands(greedy_boxes):
    v, _ = build()
    cmds = []
    for p, x0, y0, z0, x1, y1, z1 in greedy_boxes(v):
        st = "minecraft:" + PAL[p]
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
    v, marks = build()
    pal = R.Palette(PAL)
    W, Hh = 1000, 560
    shots = [((C + 62, FL + 50, C + 64), (C, FL + 16, C - 10), 62, "포털 파쿠르 — 행성 둘레를 돌며 올라가는 50단 · 우주 배경 행성 · 꼭대기 트로피"),
             ((C + 0.5, FL + 3, C - 4), (C + 0.5, FL + 3, C + 12), 80, "시작 발판에서")]
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
    out = Image.new("RGB", (W, Hh * len(shots)))
    for i, (cam, tgt, fov, lab) in enumerate(shots):
        im = R.render(v, pal, W, Hh, cam, tgt, fov=fov, ss=2, fog_dist=900, **hubgen.NIGHT)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, 40), fill=(4, 12, 28))
        d.text((14, 6), lab, font=font, fill=(140, 220, 255))
        out.paste(im, (0, Hh * i))
    out.save(path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview(sys.argv[1] if len(sys.argv) > 1 else "parkour.png")
