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
HALF = 24          # 층마다 x -24 ~ +24 를 가로지름

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


# 층마다 난이도: (올라가는 점프 확률, 평지 틈(가장자리 사이 빈칸) 범위, 발판 종류 가중치)
#  발판 = 큼직한 떠 있는 섬 (isle5 = 둥근 5칸 · sq3 = 3×3 · slab3 = 3×3 반블록) · 작은 발판 (single · pillar · fence)
#  1층: 큰 섬 · 1~2칸 틈 → 5층: 1칸 발판 · 울타리 기둥 · 3칸 틈
DIFF = [(0.35, (1, 2), {"isle5": 6, "sq3": 4}),
        (0.40, (2, 2), {"sq3": 5, "isle5": 2, "slab3": 3}),
        (0.40, (2, 3), {"sq3": 4, "single": 3, "pillar": 3}),
        (0.45, (2, 3), {"single": 4, "pillar": 3, "sq3": 2, "fence": 2}),
        (0.45, (3, 3), {"single": 5, "fence": 3, "sq3": 1, "pillar": 2})]
HALFSZ = {"isle5": 2, "sq3": 1, "slab3": 1, "single": 0, "pillar": 0, "fence": 0}
TIER_NAME = ["정원", "대리석", "구름", "수정", "황금"]
ZSTEP = 9          # 층마다 남쪽으로 (다리 길이)
END_R = 3          # 층 끝 섬 반지름 (둥근 7칸)


def course():
    """점프 자리: (x, y, z, 종류, 층) 목록 + 층 끝 섬 (x, y, z, 층) 목록. y = 발판 블록 높이 (FL 기준 0)"""
    rng = np.random.default_rng(29)
    pts, ends = [], []
    x, y, z = 0, 0, 0
    hprev = 2                      # 시작 발판 5×5
    for t in range(TIERS):
        pup, (glo, ghi), wts = DIFF[t]
        kinds, w = list(wts), np.array(list(wts.values()), float)
        d = 1 if t % 2 == 0 else -1
        zc = z
        last = "start"
        while (x < HALF if d > 0 else x > -HALF):
            kind = str(rng.choice(kinds, p=w / w.sum()))
            if kind == "fence" and last == "fence":
                kind = "single"
            up = last != "fence" and rng.random() < pup
            gap = int(rng.integers(glo, ghi + 1))
            if up or kind == "fence" or last == "fence":
                gap = min(gap, 2)
            h = HALFSZ[kind]
            dz = 0 if gap >= 3 else int(rng.integers(-1, 2))
            x += d * (hprev + h + gap + 1)
            y += 1 if up else 0
            z = max(zc - 1, min(zc + 1, z + dz))
            pts.append((x, y, z, kind, t))
            last, hprev = kind, h
        # 끝 섬 (둥근 7칸) — 틈 1칸
        x += d * (hprev + END_R + 2)
        ends.append((x, y, z, t))
        # 사다리 탑 (섬 남쪽 끝) → 꼭대기 다리 (3칸 폭 · 남쪽으로) 끝에서 다음 층
        y += 5
        z += ZSTEP
        hprev = 1
    return pts, ends


# 층마다 발판 밑 매달린 작은 섬 (위 → 아래) · 매단 등
UNDER = [["dirt", "dirt", "coarse_dirt"],
         ["smooth_quartz", "quartz_bricks", "chiseled_quartz_block"],
         ["snow_block", "white_wool", "white_wool"],
         ["amethyst_block", "budding_amethyst", "purple_stained_glass"],
         ["cut_sandstone", "smooth_sandstone", "gold_block"]]
HANG = ["lantern[hanging=true,waterlogged=false]", "lantern[hanging=true,waterlogged=false]",
        "soul_lantern[hanging=true,waterlogged=false]", "amethyst_cluster[facing=down,waterlogged=false]",
        "lantern[hanging=true,waterlogged=false]"]


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
    # 코스 발판
    rngd = np.random.default_rng(41)
    TOP0 = ["grass_block[snowy=false]", "grass_block[snowy=false]", "moss_block"]

    def isle(x, yy, z, t, rad, slab=False):
        """둥근 / 네모 떠 있는 섬 발판: 윗면 (층 재료 · 가장자리 곁들임) + 아래로 좁아지는 고깔 + 매단 등"""
        base, acc, light = SECT[t]
        ud = UNDER[t]
        r = int(math.ceil(rad))
        cells = [(dx, dz) for dx in range(-r, r + 1) for dz in range(-r, r + 1) if dx * dx + dz * dz <= rad * rad + 0.3]
        for dx, dz in cells:
            edge = any((dx + ex) ** 2 + (dz + ez) ** 2 > rad * rad + 0.3 for ex, ez in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if slab:
                top = "smooth_quartz_slab[type=top,waterlogged=false]"
            elif t == 0:
                top = TOP0[int(rngd.integers(0, 3))]
            elif t == 2:
                top = "white_wool" if not edge else "snow_block"
            else:
                top = acc if edge else (base if (dx + dz) % 2 == 0 else (light if (dx, dz) == (0, 0) else base))
            put(x + dx, yy, z + dz, top, True)
            put(x + dx, yy - 1, z + dz, (light if edge and t in (1, 3, 4) and (dx + dz) % 2 == 0 else ud[0]), True)
        # 고깔
        depth = int(rad * 2) + 2
        for k in range(2, depth + 1):
            rr = rad * (1 - (k - 1) / (depth + 0.5))
            for dx, dz in cells:
                if dx * dx + dz * dz <= rr * rr + 0.2:
                    put(x + dx, yy - k, z + dz, ud[min(2, (k - 2) * 3 // max(1, depth - 1))], True)
        put(x, yy - depth - 1, z, "iron_chain[axis=y,waterlogged=false]", True)
        put(x, yy - depth - 2, z, HANG[t], True)
        # 윗면 장식 (밟아도 되는 것만: 꽃잎 · 꽃 · 촛불)
        for dx, dz in cells:
            if (dx, dz) == (0, 0) or rngd.random() > 0.22:
                continue
            if t == 0:
                deco = str(rngd.choice(["pink_petals[facing=north,flower_amount=4]", "pink_petals[facing=east,flower_amount=3]",
                                        "short_grass", "allium", "azure_bluet", "cornflower"]))
            elif t == 2 or slab:
                continue
            else:
                deco = ["", "white_candle", "", "magenta_candle", "yellow_candle"][t] + "[candles=2,lit=true,waterlogged=false]"
            put(x + dx, yy + 1, z + dz, deco, True)
        # 구름 층: 옆으로 구름 덩이
        if t == 2:
            for dx, dz in cells:
                for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (dx + ox) ** 2 + (dz + oz) ** 2 > rad * rad + 0.3 and rngd.random() < 0.5 and free(x + dx + ox, yy - 1, z + dz + oz):
                        put(x + dx + ox, yy - 1, z + dz + oz, "white_wool", True)
        # 수정 층: 밑에 자수정 결정
        if t == 3:
            for dx, dz in cells:
                if rngd.random() < 0.3 and free(x + dx, yy - 2, z + dz):
                    put(x + dx, yy - 2, z + dz, "amethyst_cluster[facing=down,waterlogged=false]", True)

    for x, y, z, kind, t in pts:
        base, acc, light = SECT[t]
        yy = FL + y
        if kind == "isle5":
            isle(x, yy, z, t, 2.4)
        elif kind == "sq3":
            isle(x, yy, z, t, 1.5)
        elif kind == "slab3":
            isle(x, yy, z, t, 1.5, slab=True)
        elif kind == "single":
            put(x, yy, z, "grass_block[snowy=false]" if t == 0 else (acc if t == 4 else base), True)
            put(x, yy - 1, z, light, True)
            put(x, yy - 2, z, UNDER[t][1], True)
            put(x, yy - 3, z, "iron_chain[axis=y,waterlogged=false]", True)
            put(x, yy - 4, z, HANG[t], True)
        elif kind == "pillar":
            for k in range(0, 6):
                put(x, yy - k, z, base if k == 0 else ("quartz_pillar[axis=y]" if t != 3 else "purpur_pillar[axis=y]"), True)
            put(x, yy - 6, z, light, True)
            put(x, yy - 7, z, HANG[t], True)
        elif kind == "fence":
            # 울타리 기둥 꼭대기 (1.5칸) 가 발판 높이 + 0.5 → 한 칸 아래에 둠
            put(x, yy - 1, z, FENCE[t] + "[east=false,north=false,south=false,west=false,waterlogged=false]", True)
            put(x, yy - 2, z, acc, True)
            put(x, yy - 3, z, light, True)
            put(x, yy - 4, z, HANG[t], True)
    # 층 끝 섬 + 사다리 탑
    for i, (x, y, z, t) in enumerate(ends):
        base, acc, light = SECT[t]
        yy = FL + y
        isle(x, yy, z, t, END_R + 0.3)
        # 북쪽 모서리 가로등 (울타리 2 + 등)
        for cx in (-2, 2):
            put(x + cx, yy + 1, z - 2, FENCE[t] + "[east=false,north=false,south=false,west=false,waterlogged=false]", True)
            put(x + cx, yy + 2, z - 2, FENCE[t] + "[east=false,north=false,south=false,west=false,waterlogged=false]", True)
            put(x + cx, yy + 3, z - 2, "lantern[hanging=false,waterlogged=false]", True)
        if i == len(ends) - 1:
            continue
        # 사다리 탑: 기둥 (x, yy+1..yy+5, z+3) · 사다리 (z+2, 북쪽 면) · 꼭대기 다리 (3칸 폭 · z+3 ~ 다음 층 시작 + 1)
        nb, na, nl = SECT[t + 1]
        zt = z + 3
        for k in range(1, 6):
            put(x, yy + k, zt, acc if k < 5 else nb, True)
            put(x, yy + k, zt - 1, LADDER.format(f="north"), True)
        for dx in (-1, 0, 1):
            for dz in range(0, ZSTEP - 1):
                if (dx, dz) != (0, 0):
                    put(x + dx, yy + 5, zt + dz, nb if (dx + dz) % 2 == 0 else na, True)
                    put(x + dx, yy + 4, zt + dz, nl if dx == 0 else UNDER[t + 1][0], True)
            # 다리 난간 기둥 (양옆 · 2칸마다 등)
        for dz in range(1, ZSTEP - 1, 2):
            for sx in (-2, 2):
                put(x + sx, yy + 5, zt + dz, FENCE[t + 1] + "[east=false,north=false,south=false,west=false,waterlogged=false]", True)
                put(x + sx, yy + 6, zt + dz, "lantern[hanging=false,waterlogged=false]" if dz % 4 == 1 else FENCE[t + 1] + "[east=false,north=false,south=false,west=false,waterlogged=false]", True)
        # 탑 옆 빛 기둥
        for k in range(1, 9):
            put(x - 2, yy + k, zt, "end_rod[facing=up]" if k == 8 else "quartz_pillar[axis=y]")
            put(x + 2, yy + k, zt, "end_rod[facing=up]" if k == 8 else "quartz_pillar[axis=y]")
    # 결승: 마지막 섬에서 황금 신전 (7×7 금 발판 + 기둥 4 + 지붕 고리 + 신호 기둥)
    lx, ly, lz, _ = ends[-1]
    d = 1 if (TIERS - 1) % 2 == 0 else -1
    # 마지막 섬 → 신전까지 금 계단 (한 칸씩 위로 2번)
    for k in range(1, 3):
        for dz in (-1, 0, 1):
            put(lx + d * (2 + k * 2), FL + ly + k, lz + dz, "gold_block" if dz == 0 else "smooth_sandstone", True)
            put(lx + d * (2 + k * 2), FL + ly + k - 1, lz + dz, "ochre_froglight", True)
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
             ((C - 5, FL + 7, C - 6), (C + 16, FL + 2, C + 2), 75, "시작 발판에서 (동쪽으로 출발) · 큼직한 떠 있는 섬 발판")]
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
