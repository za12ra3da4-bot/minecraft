"""천공의 정원 파쿠르 (파쿠르 맵 2) — 구름 위 떠 있는 섬들을 지그재그로 오르는 60여 단 (허브 남쪽 하늘, 포털 파쿠르 더 남쪽)

 층 5개: 정원(이끼) → 대리석 → 구름 → 수정 → 황금 신전 · 층마다 동↔서로 가로지르고 끝 섬에서 사다리 탑으로 다음 층
 점프 종류: 블록 · 2×2 · 반 블록 · 기둥 · 울타리 기둥 (작은 발판) · 사다리 탑
 체크포인트 없음 (떨어지면 처음부터 · 코스는 위로만 감) · 꼭대기 황금 신전 = 결승
 장식: 아래 큰 떠 있는 섬 + 벚나무 · 작은 섬들 · 구름 · 무너진 기둥
 원점 = 시작 발판 가운데 바닥 칸 (데이터팩 storage bg:pk2 origin)
"""
import math

import numpy as np

N = 128
H = 96
FL = 20
C = N // 2
TIERS = 5
HALF = 22          # 층마다 x -22 ~ +22 를 가로지름

PAL = ["air"]
P = {"air": 0}


def pid(s):
    if s not in P:
        P[s] = len(PAL)
        PAL.append(s)
    return P[s]


# 층마다 (바탕, 곁들임, 빛)
SECT = [("moss_block", "mossy_stone_bricks", "verdant_froglight"),
        ("quartz_bricks", "smooth_quartz", "sea_lantern"),
        ("white_wool", "snow_block", "pearlescent_froglight"),
        ("amethyst_block", "purple_stained_glass", "pearlescent_froglight"),
        ("smooth_sandstone", "gold_block", "ochre_froglight")]
LADDER = "ladder[facing={f},waterlogged=false]"
FENCE = {0: "mangrove_fence", 1: "birch_fence", 2: "pale_oak_fence", 3: "crimson_fence", 4: "bamboo_fence"}


def course():
    """점프 자리: (x, y, z, 종류, 층) 목록 + 층 끝 섬 (x, y, z, 층) 목록. y = 발판 블록 높이 (FL 기준 0)"""
    rng = np.random.default_rng(23)
    pts, ends = [], []
    x, y, z = 0, 0, 0
    for t in range(TIERS):
        d = 1 if t % 2 == 0 else -1
        zc = z
        last = "start"
        while (x < HALF if d > 0 else x > -HALF):
            up = last != "fence" and rng.random() < 0.45
            dist = int(rng.integers(2, 4)) if up else int(rng.integers(3, 5))
            if last == "fence" or (t == 0 and len(pts) < 4):
                dist = min(dist, 3)
            dz = 0 if dist >= 4 else int(rng.integers(-1, 2))
            nz = max(zc - 2, min(zc + 2, z + dz))
            x += d * dist
            y += 1 if up else 0
            z = nz
            kind = pick_kind(rng, len(pts), last)
            pts.append((x, y, z, kind, t))
            last = kind
        # 끝 섬 (5×5) — 한 칸 더 가서
        x += d * 4
        ends.append((x, y, z, t))
        # 사다리 탑: 섬 남쪽 끝 기둥 (높이 5) · 북쪽 면 사다리 → 꼭대기 발판 (기둥 위 · 남쪽으로 5칸) 에서 다음 층
        y += 5
        z += 5
    return pts, ends


def pick_kind(rng, i, last):
    r = rng.random()
    if i < 4:
        return "block2"
    if r < 0.38:
        return "block"
    if r < 0.56:
        return "block2"
    if r < 0.72:
        return "slab"
    if r < 0.84:
        return "pillar"
    if last != "fence":
        return "fence"
    return "block"


def build():
    v = np.zeros((N, H, N), np.uint16)
    marks = {}
    taken = set()

    def put(x, y, z, blk, mark=False):
        gx, gz, yy = C + int(math.floor(x)), C + int(math.floor(z)), int(math.floor(y))
        if 0 <= gx < N and 0 <= yy < H and 0 <= gz < N:
            v[gx, yy, gz] = pid(blk)
            if mark:
                taken.add((gx, yy, gz))

    def free(x, y, z):
        gx, gz, yy = C + int(math.floor(x)), C + int(math.floor(z)), int(math.floor(y))
        return 0 <= gx < N and 0 <= yy < H and 0 <= gz < N and v[gx, yy, gz] == 0

    pts, ends = course()
    # 시작 발판 (5×5 이끼 · 빛 테두리) — 원점
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            edge = abs(dx) == 2 or abs(dz) == 2
            put(dx, FL, dz, "verdant_froglight" if edge else "moss_block", True)
            put(dx, FL - 1, dz, "mossy_stone_bricks", True)
    marks["start"] = (0.5, 1, 0.5, -90.0)
    # 코스 블록
    for x, y, z, kind, t in pts:
        base, acc, light = SECT[t]
        yy = FL + y
        if kind == "block":
            put(x, yy, z, base, True)
            put(x, yy - 1, z, light, True)
        elif kind == "block2":
            for dx in (0, 1):
                for dz in (0, 1):
                    put(x + dx, yy, z + dz, base if (dx + dz) % 2 == 0 else acc, True)
                    put(x + dx, yy - 1, z + dz, light, True)
        elif kind == "slab":
            put(x, yy, z, "smooth_quartz_slab[type=top,waterlogged=false]" if t != 4 else "smooth_sandstone_slab[type=top,waterlogged=false]", True)
            put(x, yy - 1, z, light, True)
        elif kind == "pillar":
            for k in range(0, 5):
                put(x, yy - k, z, base if k == 0 else acc, True)
            put(x, yy - 5, z, light, True)
        elif kind == "fence":
            # 울타리 기둥 꼭대기 (1.5칸) 가 발판 높이 + 0.5 → 한 칸 아래에 둠
            put(x, yy - 1, z, FENCE[t] + "[east=false,north=false,south=false,west=false,waterlogged=false]", True)
            put(x, yy - 2, z, acc, True)
            put(x, yy - 3, z, light, True)
    # 층 끝 섬 + 사다리 탑
    for i, (x, y, z, t) in enumerate(ends):
        base, acc, light = SECT[t]
        yy = FL + y
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                edge = abs(dx) == 2 or abs(dz) == 2
                put(x + dx, yy, z + dz, light if (edge and (dx + dz) % 2 == 0) else base, True)
                put(x + dx, yy - 1, z + dz, acc, True)
        # 섬 밑 (떠 있는 흙 고깔)
        for k in range(2, 7):
            r = 2.6 - k * 0.42
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    if dx * dx + dz * dz <= r * r:
                        put(x + dx, yy - k, z + dz, "dirt" if k < 4 else "coarse_dirt")
        if i == len(ends) - 1:
            continue
        # 사다리 탑: 기둥 (x, yy+1..yy+5, z+2) · 사다리 (z+1, 북쪽 면 = facing north) · 꼭대기 발판 (기둥 위 + 남쪽 2칸)
        nb, na, nl = SECT[t + 1]
        for k in range(1, 6):
            put(x, yy + k, z + 2, acc if k < 5 else nb, True)
            put(x, yy + k, z + 1, LADDER.format(f="north"), True)
        for dx in (-1, 0, 1):
            for dz in range(2, 7):
                if (dx, dz) != (0, 2):
                    put(x + dx, yy + 5, z + dz, nb if (dx + dz) % 2 == 0 else na, True)
                    put(x + dx, yy + 4, z + dz, nl, True)
        # 사다리 옆 빛 기둥 (탑 표시)
        for k in range(1, 9):
            put(x - 2, yy + k, z + 2, "end_rod[facing=up]" if k == 8 else "quartz_pillar[axis=y]")
            put(x + 2, yy + k, z + 2, "end_rod[facing=up]" if k == 8 else "quartz_pillar[axis=y]")
    # 결승: 마지막 섬에서 황금 신전 (7×7 금 발판 + 기둥 4 + 지붕 고리 + 신호 기둥)
    lx, ly, lz, _ = ends[-1]
    d = 1 if (TIERS - 1) % 2 == 0 else -1
    # 마지막 섬 → 신전까지 금 계단 (한 칸씩 위로 2번)
    for k in range(1, 3):
        put(lx + d * (2 + k * 2), FL + ly + k, lz, "gold_block", True)
        put(lx + d * (2 + k * 2), FL + ly + k - 1, lz, "ochre_froglight", True)
    fx, fz = lx + d * 10, lz
    fy = FL + ly + 3
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            edge = max(abs(dx), abs(dz)) == 3
            put(fx + dx, fy, fz + dz, "ochre_froglight" if edge else ("gold_block" if (dx + dz) % 2 == 0 else "smooth_sandstone"), True)
            put(fx + dx, fy - 1, fz + dz, "cut_sandstone", True)
    for cx, cz in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        for k in range(1, 7):
            put(fx + cx, fy + k, fz + cz, "quartz_pillar[axis=y]", True)
        put(fx + cx, fy + 7, fz + cz, "chiseled_quartz_block", True)
    for t in range(0, 360, 6):
        a = math.radians(t)
        put(fx + math.cos(a) * 4.2, fy + 8, fz + math.sin(a) * 4.2, "gold_block", True)
        put(fx + math.cos(a) * 3.4, fy + 8.6, fz + math.sin(a) * 3.4, "ochre_froglight", True)
    put(fx, fy + 1, fz, "gold_block", True)
    put(fx, fy + 2, fz, "beacon", True)
    put(fx, fy + 3, fz, "end_rod[facing=up]", True)
    marks["finish"] = (fx + 0.5, fy - FL + 1, fz + 2.5, 0.0)
    # 장식 ─ 아래 큰 떠 있는 섬 (풀 · 흙 고깔) + 벚나무
    rng = np.random.default_rng(31)
    cpts = list(taken)

    def near_course(x, y, z, r):
        gx, gy, gz = C + x, y, C + z
        return any(abs(a - gx) <= r and abs(b - gy) <= r and abs(c - gz) <= r for a, b, c in cpts)

    def island(cx, cy, cz, rad, tree=True):
        for dx in range(-rad - 1, rad + 2):
            for dz in range(-rad - 1, rad + 2):
                rr = math.hypot(dx, dz)
                if rr > rad + 0.4:
                    continue
                depth = int((rad - rr) * 1.3 + 2 + rng.random() * 1.5)
                if free(cx + dx, cy, cz + dz):
                    put(cx + dx, cy, cz + dz, "moss_block" if rng.random() < 0.25 else "grass_block[snowy=false]")
                for k in range(1, depth):
                    if free(cx + dx, cy - k, cz + dz):
                        put(cx + dx, cy - k, cz + dz, "dirt" if k < 3 else ("stone" if rng.random() < 0.7 else "andesite"))
                if rr < rad - 1 and rng.random() < 0.12 and free(cx + dx, cy + 1, cz + dz):
                    put(cx + dx, cy + 1, cz + dz, rng.choice(["pink_petals[facing=north,flower_amount=4]", "short_grass", "azalea", "flowering_azalea"]))
        if tree:
            th = 5 + int(rng.integers(0, 3))
            for k in range(1, th + 1):
                put(cx, cy + k, cz, "cherry_log[axis=y]")
            for dx in range(-3, 4):
                for dy in range(-1, 3):
                    for dz in range(-3, 4):
                        if dx * dx + (dy * 1.6) ** 2 + dz * dz <= 10 and free(cx + dx, cy + th + dy, cz + dz):
                            put(cx + dx, cy + th + dy, cz + dz, "cherry_leaves[distance=7,persistent=true,waterlogged=false]")

    island(4, FL - 12, 14, 12)
    island(-8, FL - 10, 30, 6)
    for _ in range(14):
        for _try in range(30):
            cx, cz = int(rng.integers(-52, 53)), int(rng.integers(-40, 70))
            cy = FL + int(rng.integers(-8, 62))
            rad = int(rng.integers(3, 6))
            if not near_course(cx, cy, cz, rad + 6):
                island(cx, cy, cz, rad, tree=rng.random() < 0.7)
                break
    # 구름 (양털 · 눈 덩이 · 납작)
    for _ in range(26):
        for _try in range(30):
            cx, cz = int(rng.integers(-58, 59)), int(rng.integers(-50, 64))
            cy = FL + int(rng.integers(-14, 70))
            if near_course(cx, cy, cz, 8):
                continue
            for b in range(int(rng.integers(3, 6))):
                bx, bz = cx + int(rng.integers(-5, 6)), cz + int(rng.integers(-3, 4))
                r = rng.uniform(2.0, 3.6)
                for dx in range(-4, 5):
                    for dy in range(-2, 3):
                        for dz in range(-4, 5):
                            if (dx / r) ** 2 + (dy / (r * 0.45)) ** 2 + (dz / r) ** 2 <= 1 and free(bx + dx, cy + dy, bz + dz):
                                put(bx + dx, cy + dy, bz + dz, "white_wool" if dy >= 0 else "snow_block")
            break
    # 무너진 기둥 (떠 있는 신전 조각)
    for _ in range(10):
        for _try in range(30):
            cx, cz = int(rng.integers(-50, 51)), int(rng.integers(-40, 66))
            cy = FL + int(rng.integers(0, 60))
            if near_course(cx, cy, cz, 6):
                continue
            hh = int(rng.integers(3, 8))
            for k in range(hh):
                put(cx, cy + k, cz, "quartz_pillar[axis=y]" if k else "chiseled_quartz_block")
            put(cx, cy - 1, cz, "smooth_quartz")
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(cx + dx, cy - 1, cz + dz, "smooth_quartz_slab[type=top,waterlogged=false]")
            break
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


DAY = dict(sun=(0.4, 0.8, 0.45), sun_col=(1.0, 0.95, 0.85), amb_col=(0.75, 0.8, 0.95),
           sky_top=(0.32, 0.55, 0.95), sky_hor=(0.85, 0.9, 1.0), fog_col=(0.85, 0.9, 1.0))


def preview(path):
    import render as R
    from PIL import Image, ImageDraw, ImageFont
    v, marks = build()
    pal = R.Palette(PAL)
    W, Hh = 1000, 560
    shots = [((C + 10, FL + 46, C - 62), (C + 2, FL + 26, C + 12), 66, "천공의 정원 — 떠 있는 섬을 지그재그로 오르는 5층 · 사다리 탑 · 꼭대기 황금 신전"),
             ((C + 0.5, FL + 3, C + 0.5), (C + 14, FL + 3, C + 0.5), 80, "시작 발판에서 (동쪽으로 출발)")]
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
    out = Image.new("RGB", (W, Hh * len(shots)))
    for i, (cam, tgt, fov, lab) in enumerate(shots):
        im = R.render(v, pal, W, Hh, cam, tgt, fov=fov, ss=2, fog_dist=900, **DAY)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, 40), fill=(20, 40, 70))
        d.text((14, 6), lab, font=font, fill=(255, 235, 170))
        out.paste(im, (0, Hh * i))
    out.save(path)


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview(sys.argv[1] if len(sys.argv) > 1 else "parkour2.png")
