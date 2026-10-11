"""양과 늑대 — 1:1 공성전 맵 (미리보기 · 블록 + 블록 디스플레이)

 서쪽 = 양 진영 「하얀 목장 왕국」: 해자 · 도개교 · 쌍둥이 성문탑 · 하얀 성벽 (버팀벽 · 걸린 깃발) · 원뿔 지붕 망루 6
         본성 (3단 · 첨탑) 안 황금 양털 제단 · 분수 광장 · 목조 집 · 시장 천막 · 풍차 · 헛간 · 밀밭 · 양 우리 · 양 떼 (디플)
 동쪽 = 늑대 진영 「달그림자 굴」: 바위 절벽 · 죽은 숲 · 뾰족 통나무 울타리 + 망대 · 거대 늑대 해골 성문 (디플)
         천막 · 토템 · 뼈 무더기 · 굴 (붉은 눈) · 달의 제단 + 거대 하울링 늑대 석상 (디플) · 떠 있는 달 (디플) · 늑대 무리 (디플)
 가운데 = 굽이치는 강 · 아치 돌다리 2 · 폐허 망루 섬 다리 · 갈대 · 연잎 · 생울타리 · 바위 · 무너진 벽
 x: 서(-) → 동(+) · z: 북(-) → 남(+) · 바닥 FL · 블록 디스플레이 모델 = bdkit (픽셀 단위 · 16px = 1칸)
"""
import math
import os

import numpy as np

NX, NZ, H = 228, 150, 100
FL = 20
CX, CZ = NX // 2, NZ // 2

PAL = ["air"]
P = {"air": 0}
DISPLAYS = []          # (모델, x, y, z, yaw, scale) — 블록 디스플레이 (미리보기에서 메쉬로)


def pid(s):
    if s not in P:
        P[s] = len(PAL)
        PAL.append(s)
    return P[s]


# ─────────────────────────────────────────────────────────── 블록 디스플레이 모델
def sheep_model(wool="white_wool"):
    import bdkit as K
    m = K.Model()
    m.box(wool, -6, 9, -9, 6, 19, 8)                     # 몸통
    for sx in (-6.8, 5.8):
        m.box(wool, sx, 10, -7, sx + 1, 18, 6)            # 옆 털 뭉치
    m.box(wool, -5, 18, -8, 5, 20, 7)                     # 등 털
    m.box(wool, -5, 10, 8, 5, 18, 9.5)                    # 엉덩이 털
    m.box("smooth_sandstone", -3, 13, -14, 3, 19, -8)     # 얼굴
    m.box(wool, -3.6, 18, -13, 3.6, 21, -8)               # 머리 털
    m.box("black_concrete", -2.2, 16, -14.2, -1, 17.2, -13.8)
    m.box("black_concrete", 1, 16, -14.2, 2.2, 17.2, -13.8)
    m.box("pink_terracotta", -1, 13.5, -14.3, 1, 14.5, -13.9)
    for sx in (-4.5, 2.5):
        m.box("smooth_sandstone", sx, 17, -11, sx + 2, 18, -9) if False else None
        m.box("smooth_sandstone", sx - 1.2 if sx < 0 else sx + 1.2, 17, -11, sx + 0.8 if sx < 0 else sx + 3.2, 18.2, -9.5)
    for lx, lz in ((-4.5, -6), (2, -6), (-4.5, 4), (2, 4)):
        m.box("smooth_sandstone", lx, 0, lz, lx + 2.5, 9, lz + 2.5)
        m.box("gray_concrete", lx - 0.1, 0, lz - 0.1, lx + 2.6, 1.6, lz + 2.6)
    return m


def wolf_model(fur="light_gray_concrete", sit=False):
    import bdkit as K
    m = K.Model()
    if sit:
        m.cbox(fur, (0, 9, 3), (8, 9, 12), pitch=-35)
        m.box(fur, -4, 9, -7, 4, 18, -1)                   # 가슴
        for lx in (-3.5, 1.5):
            m.box(fur, lx, 0, -6, lx + 2, 10, -4)          # 앞다리
            m.box(fur, lx - 0.5, 0, 4, lx + 2.5, 4, 9)     # 뒷다리 접음
        hy, hz = 19, -5
    else:
        m.box(fur, -4, 8, -8, 4, 16, 9)                    # 몸통
        m.box("gray_concrete", -4.5, 9, -9, 4.5, 17, -3)   # 갈기
        for lx, lz in ((-3.5, -7), (1.5, -7), (-3.5, 6), (1.5, 6)):
            m.box(fur, lx, 0, lz, lx + 2, 8, lz + 2)
        hy, hz = 14, -9
    m.box(fur, -3.5, hy, hz - 6, 3.5, hy + 6.5, hz)        # 머리
    m.box("gray_concrete", -2, hy, hz - 10, 2, hy + 3, hz - 5)   # 주둥이
    m.box("black_concrete", -1, hy + 2, hz - 10.3, 1, hy + 3.2, hz - 9.8)
    m.box("red_concrete", -2.6, hy + 4, hz - 6.2, -1.2, hy + 5, hz - 5.8, glow=True)
    m.box("red_concrete", 1.2, hy + 4, hz - 6.2, 2.6, hy + 5, hz - 5.8, glow=True)
    for ex in (-3.2, 1.2):
        m.box("gray_concrete", ex, hy + 6.5, hz - 3, ex + 2, hy + 9, hz - 1.5)
    m.rod(fur, (0, 13 if not sit else 4, 9 if not sit else 9), (0, 9 if not sit else 1, 17 if not sit else 16), 2.5)
    return m


def howling_wolf():
    """거대 하울링 늑대 석상 (앉아서 달을 보고 울부짖음) — 심층암 · 붉은 눈"""
    import bdkit as K
    m = K.Model()
    B1, B2, B3 = "polished_deepslate", "deepslate_tiles", "cobbled_deepslate"
    m.cbox(B1, (0, 10, 6), (14, 13, 18), pitch=-30)        # 엉덩이 · 허리
    m.cbox(B2, (0, 20, -2), (13, 16, 11), pitch=-55)       # 가슴 (위로 젖힘)
    m.cbox(B3, (0, 22, -5), (15, 10, 8), pitch=-60)        # 갈기
    for lx in (-4, 4):
        m.rod(B1, (lx, 16, -5), (lx, 0, -7), 4, 4)         # 앞다리
        m.cbox(B1, (lx, 1, -9), (5, 2.5, 6))               # 앞발
        m.cbox(B1, (lx * 1.7, 4, 10), (5, 8, 12), pitch=10)    # 뒷다리 접음
        m.cbox(B2, (lx * 1.5, 1.2, 3), (5, 2.5, 6))        # 뒷발
    m.rod(B2, (0, 26, -6), (0, 35, -10), 8, 8)             # 목 (위로)
    m.cbox(B1, (0, 37, -11), (9, 9, 9), pitch=-60)         # 머리
    m.rod(B2, (0, 39, -13), (0, 46, -17), 4.5, 4)          # 주둥이 (하늘로)
    m.cbox("black_concrete", (0, 46.4, -17.5), (2, 1, 2), pitch=-60)
    m.rod(B3, (0, 38, -15), (0, 43, -19), 3.5, 2.5)        # 벌린 아래턱
    for ex in (-3, 3):
        m.cbox("red_concrete", (ex * 1.05, 39.5, -14), (1.6, 1, 1.2), pitch=-60, glow=True)
        m.rod(B3, (ex, 40, -8), (ex * 1.2, 46, -6), 2.5, 1.5)  # 귀
    m.rod(B1, (0, 6, 14), (6, 3, 22), 4)                   # 꼬리
    m.rod(B1, (6, 3, 22), (10, 7, 20), 3)
    return m


def moon_model():
    """떠 있는 달 (빛남) — 원판 층을 쌓아 공 모양 · 분화구"""
    import bdkit as K
    m = K.Model()
    R = 48
    for k in range(-R, R + 1, 6):
        r = math.sqrt(max(0, R * R - k * k))
        if r < 3:
            continue
        for a in (0, 45):
            m.cbox("white_concrete", (0, k, 0), (r * 1.9, 6.2, r * 0.8), yaw=a, glow=True)
            m.cbox("white_concrete", (0, k, 0), (r * 0.8, 6.2, r * 1.9), yaw=a, glow=True)
    for cx, cy, cz, s in ((12, 18, -40, 12), (-20, -10, -38, 16), (6, -26, -36, 9), (-8, 26, -38, 8)):
        m.cbox("light_gray_concrete", (cx, cy, cz), (s, s, 6), glow=True)
    return m


def banner_model(base, emblem, trim):
    """성벽에 거는 긴 깃발 (2칸 × 4칸) — 문양 + 금 테두리"""
    import bdkit as K
    m = K.Model()
    m.box(trim, -17, 64, -1, 17, 66, 1)                     # 가로대
    m.box(base, -15, 4, -0.6, 15, 64, 0.6)
    m.box(trim, -15, 4, -0.8, -13, 64, 0.8)
    m.box(trim, 13, 4, -0.8, 15, 64, 0.8)
    for i, (x0, x1) in enumerate(((-15, -5), (-5, 5), (5, 15))):
        m.box(base, x0, 4 - (6 if i == 1 else 2), -0.6, x1, 4, 0.6)   # 제비꼬리
    m.box(emblem, -7, 30, -0.9, 7, 42, 0.9)                 # 문양 (양 = 흰 털 / 늑대 = 해골)
    m.box(emblem, -9, 34, -0.9, -7, 40, 0.9)
    m.box(emblem, 7, 32, -0.9, 10, 38, 0.9)
    m.box(trim, -4, 46, -0.9, 4, 50, 0.9)                   # 위 금 장식
    return m


def flag_model(c1, c2):
    import bdkit as K
    m = K.Model()
    m.box("iron_block", -0.8, 0, -0.8, 0.8, 40, 0.8)
    m.box(c1, 0.8, 26, -0.4, 22, 38, 0.4)
    m.box(c2, 0.8, 30, -0.5, 22, 34, 0.5)
    m.box("gold_block", -1.5, 40, -1.5, 1.5, 43, 1.5)
    return m


def windmill_blades():
    import bdkit as K
    m = K.Model()
    m.cbox("spruce_log", (0, 0, 0), (8, 8, 10))
    for a in (45, 135, 225, 315):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        m.rod("spruce_planks", (0, 0, -4), (0, sa * 150, -4 + 0) if False else (ca * 150, sa * 150, -4), 3, 3)
        for t in range(30, 150, 14):
            px_, py_ = ca * t, sa * t
            nx_, ny_ = -sa, ca
            m.rod("dark_oak_planks", (px_, py_, -5), (px_ + nx_ * 28, py_ + ny_ * 28, -5), 1.5, 1.5)
        mid = 90
        m.cbox("white_wool", (ca * mid + -sa * 15, sa * mid + ca * 15, -6), (26, 112, 1.2), roll=a - 90)
    return m


def wolf_skull():
    """늑대 해골 성문 장식 (뼈 · 붉게 빛나는 눈구멍 · 송곳니)"""
    import bdkit as K
    m = K.Model()
    m.cbox("bone_block", (0, 40, 0), (60, 40, 46))          # 머리뼈
    m.cbox("bone_block", (0, 22, -26), (30, 20, 40))        # 주둥이
    m.cbox("bone_block", (0, 62, 6), (40, 8, 34))
    for ex in (-16, 16):
        m.cbox("black_concrete", (ex, 42, -23.2), (14, 12, 2))
        m.cbox("redstone_block", (ex, 42, -23.6), (6, 6, 2), glow=True)
        m.rod("bone_block", (ex * 1.2, 56, -6), (ex * 2.0, 84, 4), 10, 7)  # 귀뼈
    m.cbox("black_concrete", (0, 26, -46.2), (10, 6, 1.5))  # 콧구멍
    for fx in (-11, -4, 4, 11):
        ln = 26 if abs(fx) == 11 else 14
        m.rod("smooth_quartz", (fx, 13, -40), (fx * 0.9, 13 - ln, -42), 3.2, 3.2)
    m.cbox("bone_block", (0, 6, -20), (26, 5, 34), pitch=12)  # 아래턱
    return m


def awning(c1, c2):
    import bdkit as K
    m = K.Model()
    for i in range(6):
        m.cbox(c1 if i % 2 == 0 else c2, (-30 + i * 10 + 5, 52, 0), (10, 1.2, 40), roll=0, pitch=18)
    for x in (-29, 29):
        for z in (-17, 17):
            m.box("spruce_fence", x - 1, 0, z - 1, x + 1, 50, z + 1) if False else m.box("spruce_planks", x - 1, 0, z - 1, x + 1, 50, z + 1)
    m.box("spruce_planks", -28, 14, -14, 28, 18, 4)
    for i, c in enumerate(("red_wool", "orange_wool", "yellow_wool", "lime_wool")):
        m.box(c if i % 2 else "hay_block", -24 + i * 13, 18, -12, -16 + i * 13, 24, 0)
    return m


def chains_model(length, drop):
    import bdkit as K
    m = K.Model()
    for z in (-36, 36):
        m.rod("iron_block", (0, 0, z), (-length * 16, -drop * 16, z), 1.6, 1.6)
    return m


# ─────────────────────────────────────────────────────────── 맵
def build():
    v = np.zeros((NX, H, NZ), np.uint16)
    rng = np.random.default_rng(11)
    DISPLAYS.clear()

    def put(x, y, z, b):
        gx, gz, yy = CX + int(math.floor(x)), CZ + int(math.floor(z)), int(math.floor(y))
        if 0 <= gx < NX and 0 <= yy < H and 0 <= gz < NZ:
            v[gx, yy, gz] = pid(b)

    def get(x, y, z):
        gx, gz, yy = CX + int(math.floor(x)), CZ + int(math.floor(z)), int(math.floor(y))
        if 0 <= gx < NX and 0 <= yy < H and 0 <= gz < NZ:
            return PAL[v[gx, yy, gz]]
        return "air"

    def box(x0, y0, z0, x1, y1, z1, b):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    put(x, y, z, b)

    def disp(model, x, y, z, yaw=0.0, scale=1.0):
        DISPLAYS.append((model, x, y, z, yaw, scale))

    X0, X1, Z0, Z1 = -CX, NX - CX - 1, -CZ, NZ - CZ - 1

    def river_off(z):
        return 2.6 * math.sin(z * 0.055) + 1.2 * math.sin(z * 0.13 + 1)

    # ══════════ 지형 — 가장자리 산 (북 · 남) · 서쪽 언덕 · 동쪽 바위 절벽
    hmap = {}
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            h = 1.1 * math.sin(x * 0.07) * math.cos(z * 0.09) + 0.9 * math.sin(x * 0.031 + z * 0.05) + 0.5 * math.sin(x * 0.17 + z * 0.13)
            dz = abs(z) - 56
            if dz > 0:
                h += dz ** 1.35 * 0.95 + 2.5 * math.sin(x * 0.11 + z * 0.3) * min(1, dz / 6)
            if x < -102:
                h += (-102 - x) ** 1.3 * 0.9
            if x > 104:                                    # 늑대 뒤 바위 절벽
                h += (x - 104) ** 1.25 * 1.6 + 3 * abs(math.sin(z * 0.21))
            if 30 < x < 104:                               # 늑대 쪽 바위 언덕들
                for hx, hz, hr, hh in ((80, -46, 14, 10), (88, 44, 12, 8), (40, -50, 9, 5)):
                    d = math.hypot(x - hx, z - hz) / hr
                    h += max(0, hh * (1 - d * d))
            ro = river_off(z)
            if abs(x - ro) < 10:
                h -= (10 - abs(x - ro)) * 0.3
            hmap[x, z] = int(round(h))

    def ground(x, z):
        return FL + hmap.get((int(math.floor(x)), int(math.floor(z))), 0)

    for (x, z), h in hmap.items():
        top = FL + h
        slope = max(abs(h - hmap.get((x + 1, z), h)), abs(h - hmap.get((x, z + 1), h)), abs(h - hmap.get((x - 1, z), h)), abs(h - hmap.get((x, z - 1), h)))
        for y in range(FL - 8, top):
            put(x, y, z, "dirt" if y > top - 3 else "stone")
        if slope >= 2 or top > FL + 22:
            east = x > 20
            g = ("tuff" if rng.random() < 0.35 else ("andesite" if rng.random() < 0.5 else "stone")) if east else ("stone" if rng.random() < 0.6 else "andesite")
            if top > FL + 30:
                g = "snow_block" if not east else "calcite"
            for y in range(top - 2, top):
                put(x, y, z, g)
        elif x < -6:
            r = rng.random()
            g = "grass_block" if r < 0.9 else ("moss_block" if r < 0.95 else "coarse_dirt")
        elif x > 6:
            r = rng.random()
            g = "podzol" if r < 0.3 else ("coarse_dirt" if r < 0.42 else ("moss_block" if r < 0.5 else ("rooted_dirt" if r < 0.56 else "grass_block")))
        else:
            g = "grass_block"
        put(x, top, z, g)

    # ══════════ 강 (굽이침 · 깊이 3 · 모래 · 자갈 · 진흙 강가 · 갈대 · 연잎)
    for z in range(Z0, Z1 + 1):
        ro = river_off(z)
        for x in range(int(ro) - 8, int(ro) + 9):
            d = abs(x - ro)
            g = ground(x, z)
            if d <= 4.2:
                for y in range(FL - 5, g + 3):
                    put(x, y, z, "air")
                depth = 3 if d < 3 else 2
                for y in range(FL - 1 - depth, FL):
                    put(x, y, z, "water")
                put(x, FL - 2 - depth, z, "gravel" if rng.random() < 0.6 else "clay")
                if d > 3.2 and rng.random() < 0.1:
                    put(x, FL, z, "lily_pad")
            elif d <= 6.5:
                put(x, g, z, "sand" if rng.random() < 0.7 else ("gravel" if rng.random() < 0.5 else "mud"))
                if 4.5 < d < 6 and rng.random() < 0.16:
                    for k in range(1, int(rng.integers(2, 4))):
                        put(x, g + k, z, "sugar_cane")
        if abs(z) > 56:
            continue

    # ══════════ 아치 돌다리 (북 · 남) — 가운데가 솟은 다리 + 물속 기둥 + 아치
    def arch_bridge(zc):
        ro = river_off(zc)
        for x in range(int(ro) - 11, int(ro) + 12):
            t = (x - ro) / 11
            rise = int(round(2.4 * (1 - t * t)))
            yd = FL + rise
            for z in range(zc - 2, zc + 3):
                put(x, yd, z, "stone_bricks" if abs(z - zc) < 2 else "mossy_stone_bricks")
                for y in range(FL + 1, yd):
                    put(x, y, z, "air")
            put(x, yd + 1, zc - 2, "stone_brick_wall")
            put(x, yd + 1, zc + 2, "stone_brick_wall")
            if abs(x - ro) <= 4:
                ah = int(round(2.2 * math.sqrt(max(0, 1 - ((x - ro) / 4.3) ** 2))))
                for z in range(zc - 2, zc + 3):
                    for y in range(FL - 4, FL + rise - ah):
                        put(x, y, z, "stone_bricks" if y > FL - 2 else "mossy_stone_bricks")
            if int(ro) - 11 == x or int(ro) + 11 == x:
                for z in (zc - 2, zc + 2):
                    put(x, yd + 2, z, "lantern")
        for z in range(zc - 3, zc + 4):
            for y in range(FL - 5, FL - 1):
                for x in (int(ro) - 5, int(ro) + 5):
                    put(x, y, z, "stone_bricks")
    arch_bridge(-42)
    arch_bridge(42)

    # ══════════ 가운데: 섬 + 넓은 다리 + 폐허 망루 (부서진 꼭대기 · 덩굴 · 횃대)
    ro0 = river_off(0)
    for z in range(-7, 8):
        for x in range(int(ro0) - 11, int(ro0) + 12):
            put(x, FL, z, "cobblestone" if rng.random() < 0.25 else ("mossy_cobblestone" if rng.random() < 0.2 else "stone_bricks"))
            for y in range(FL + 1, FL + 4):
                put(x, y, z, "air")
    for x in range(int(ro0) - 11, int(ro0) + 12):
        for z in (-7, 7):
            if rng.random() < 0.82:
                put(x, FL + 1, z, "cobblestone_wall")
    tx, tz = int(ro0), 0
    for y in range(FL + 1, FL + 19):
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                d = max(abs(dx), abs(dz))
                if d == 3:
                    keep = y < FL + 12 or rng.random() < (FL + 19 - y) / 7.5
                    if dx == 3 and abs(dz) <= 1 and y < FL + 4:
                        keep = False
                    if dx == -3 and abs(dz) <= 1 and y < FL + 4:
                        keep = False
                    if keep:
                        put(tx + dx, y, tz + dz, "mossy_stone_bricks" if rng.random() < 0.45 else ("cracked_stone_bricks" if rng.random() < 0.5 else "stone_bricks"))
                elif d < 3 and y in (FL + 7, FL + 13):
                    if rng.random() < 0.85:
                        put(tx + dx, y, tz + dz, "spruce_planks")
        if y % 4 == 0:
            for dz in (-3, 3):
                put(tx, y, tz + dz, "iron_bars")
    for dx, dz in ((-3, -3), (3, 3), (-3, 3), (3, -3)):
        for y in range(FL + 1, FL + 15):
            if rng.random() < 0.35:
                put(tx + dx + (1 if dx > 0 else -1), y, tz + dz, "vine") if False else None
    put(tx, FL + 14, tz, "campfire")

    # ══════════ 들판: 생울타리 · 바위 · 무너진 벽 · 수레
    def hedge(x0, z0, x1, z1, leaf="oak_leaves"):
        n = max(abs(x1 - x0), abs(z1 - z0))
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            z = round(z0 + (z1 - z0) * i / n)
            g = ground(x, z)
            put(x, g + 1, z, leaf)
            if rng.random() < 0.7:
                put(x, g + 2, z, leaf)
            if rng.random() < 0.15:
                put(x, g + 2, z, "flowering_azalea_leaves")
    for a in [(-30, -52, -30, -30), (-24, 14, -24, 34), (-18, -12, -10, -12), (-36, 22, -30, 22)]:
        hedge(*a)
    for a in [(26, -26, 26, -12), (22, 30, 22, 50), (14, 16, 18, 16)]:
        hedge(*a, leaf="dark_oak_leaves")

    def boulder(x, z, r, mats):
        g = ground(x, z)
        for dx in range(-r - 1, r + 2):
            for dy in range(-1, r + 1):
                for dz in range(-r - 1, r + 2):
                    if dx * dx + (dy * 1.35) ** 2 + dz * dz <= r * r + 0.6 + rng.random():
                        put(x + dx, g + dy, z + dz, str(rng.choice(mats)))
        if rng.random() < 0.6:
            put(x, g + r + 1, z, "moss_carpet")
    for x, z, r in [(-20, -32, 2), (-14, 46, 3), (-38, 4, 2), (-44, -40, 2)]:
        boulder(x, z, r, ["stone", "andesite", "mossy_cobblestone", "stone"])
    for x, z, r in [(16, -50, 3), (18, 6, 2), (30, 46, 2), (36, -8, 2), (44, 24, 3)]:
        boulder(x, z, r, ["tuff", "andesite", "stone", "cobbled_deepslate"])

    def ruin_wall(x, z, ln, axis):
        for i in range(ln):
            xx, zz = (x + i, z) if axis == "x" else (x, z + i)
            hh = int(1 + 3.5 * abs(math.sin(i * 0.9 + 0.4)))
            for y in range(hh):
                put(xx, ground(xx, zz) + 1 + y, zz, "mossy_stone_bricks" if rng.random() < 0.5 else "cracked_stone_bricks")
    ruin_wall(-18, 24, 7, "x")
    ruin_wall(13, -34, 8, "z")
    ruin_wall(32, 10, 5, "x")

    # ══════════ 나무
    def oak(x, z, log="oak_log", leaf="oak_leaves", hh=None):
        g = ground(x, z)
        hh = hh or int(rng.integers(5, 8))
        for y in range(1, hh + 1):
            put(x, g + y, z, log)
        for dx in range(-3, 4):
            for dy in range(-2, 3):
                for dz in range(-3, 4):
                    if dx * dx + (dy * 1.5) ** 2 + dz * dz <= 9 + rng.random() * 2:
                        if get(x + dx, g + hh + dy, z + dz) == "air":
                            put(x + dx, g + hh + dy, z + dz, leaf)

    def spruce(x, z, hh):
        g = ground(x, z)
        for y in range(1, hh + 1):
            put(x, g + y, z, "spruce_log")
        for k in range(hh):
            y = g + 3 + k
            r = int(max(0, (hh - k) * 0.45))
            if k % 2 == 1:
                r = max(0, r - 1)
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if abs(dx) + abs(dz) <= r + (1 if r > 2 else 0) and (dx or dz) and get(x + dx, y, z + dz) == "air":
                        put(x + dx, y, z + dz, "spruce_leaves")
        put(x, g + hh + 1, z, "spruce_leaves")
        put(x, g + hh + 2, z, "spruce_leaves")

    def dead_tree(x, z):
        g = ground(x, z)
        hh = int(rng.integers(5, 9))
        for y in range(1, hh + 1):
            put(x, g + y, z, "dark_oak_log" if y < hh - 1 else "stripped_dark_oak_log")
        for a in rng.choice(4, 2, replace=False):
            dx, dz = [(1, 0), (-1, 0), (0, 1), (0, -1)][a]
            for k in range(1, 3):
                put(x + dx * k, g + hh - 2 + k, z + dz * k, "dark_oak_log")

    # ══════════════════════════════════════════════════ 양 진영 — 하얀 목장 왕국
    SX0, SX1, SZ0, SZ1 = -100, -52, -34, 34
    MOAT = 4
    # 해자 · 평탄한 마당
    for x in range(SX0 - MOAT - 2, SX1 + MOAT + 3):
        for z in range(SZ0 - MOAT - 2, SZ1 + MOAT + 3):
            inside = SX0 <= x <= SX1 and SZ0 <= z <= SZ1
            dist = max(SX0 - x, x - SX1, SZ0 - z, z - SZ1)
            for y in range(FL + 1, FL + 12):
                if get(x, y, z) not in ("air",) and not inside:
                    put(x, y, z, "air")
            if inside:
                for y in range(FL - 3, FL):
                    put(x, y, z, "dirt")
                for y in range(FL + 1, FL + 10):
                    put(x, y, z, "air")
                put(x, FL, z, "grass_block")
            elif 1 <= dist <= MOAT:
                for y in range(FL - 4, FL + 1):
                    put(x, y, z, "air")
                for y in range(FL - 3, FL):
                    put(x, y, z, "water")
                put(x, FL - 4, z, "gravel")
                if dist == MOAT:
                    for y in range(FL - 3, FL + 1):
                        put(x, y, z, "stone_bricks" if y < FL else "smooth_stone")
            else:
                put(x, FL, z, "grass_block")
    # 길 (성문 → 본성) · 광장 길 무늬
    for x in range(SX0, SX1 + 1):
        for z in range(-2, 3):
            put(x, FL, z, "dirt_path" if abs(z) < 2 else "gravel")
    for z in range(SZ0 + 2, SZ1 - 1):
        put(-70, FL, z, "dirt_path")
    # 성벽 (높이 9): 돌 받침 2 · 방해석 몸 · 석영 띠 · 톱니 · 버팀벽
    WH = 9
    for x in range(SX0, SX1 + 1):
        for z in range(SZ0, SZ1 + 1):
            if not (x in (SX0, SX1) or z in (SZ0, SZ1)):
                continue
            for y in range(FL - 3, FL + WH + 1):
                if y <= FL + 1:
                    b = "stone_bricks" if (x + z + y) % 5 else "mossy_stone_bricks"
                elif y == FL + 5:
                    b = "smooth_quartz"
                elif y == FL + WH:
                    b = "quartz_bricks"
                else:
                    b = "calcite" if (x * 3 + z * 7 + y) % 9 else "white_concrete"
                put(x, y, z, b)
            if (x + z) % 2 == 0:
                put(x, FL + WH + 1, z, "quartz_bricks")
                put(x, FL + WH + 2, z, "smooth_quartz_slab[type=bottom,waterlogged=false]")
    # 버팀벽 (바깥 · 6칸마다)
    for x in range(SX0 + 3, SX1 - 2, 6):
        for z, oz in ((SZ0, -1), (SZ1, 1)):
            for y in range(FL - 3, FL + WH - 1):
                put(x, y, z + oz, "stone_bricks" if y < FL + 3 else "polished_andesite")
            put(x, FL + WH - 1, z + oz, "stone_brick_slab[type=bottom,waterlogged=false]")
    for z in range(SZ0 + 3, SZ1 - 2, 6):
        for x, ox in ((SX0, -1), (SX1, 1)):
            if abs(z) <= 6:
                continue
            for y in range(FL - 3, FL + WH - 1):
                put(x + ox, y, z, "stone_bricks" if y < FL + 3 else "polished_andesite")
            put(x + ox, FL + WH - 1, z, "stone_brick_slab[type=bottom,waterlogged=false]")
    # 성벽 위 통로 + 안쪽 받침
    for x in range(SX0 + 1, SX1):
        for z in (SZ0 + 1, SZ1 - 1):
            put(x, FL + WH - 1, z, "spruce_planks")
            if x % 4 == 0:
                for y in range(FL + 1, FL + WH - 1):
                    put(x, y, z, "spruce_log")
    for z in range(SZ0 + 1, SZ1):
        for x in (SX0 + 1, SX1 - 1):
            put(x, FL + WH - 1, z, "spruce_planks")
            if z % 4 == 0 and abs(z) > 6:
                for y in range(FL + 1, FL + WH - 1):
                    put(x, y, z, "spruce_log")
    # 걸린 깃발 (바깥 벽 · 버팀벽 사이) — 파랑 바탕 · 흰 양털 문양 · 금 테두리
    bm = banner_model("blue_wool", "white_wool", "gold_block")
    for x in range(SX0 + 6, SX1 - 2, 12):
        disp(bm, x + 0.5, FL + 2, SZ0 - 1.08, 180, 1.0)
        disp(bm, x + 0.5, FL + 2, SZ1 + 1.08, 0, 1.0)
    for z in (-18, 18):
        disp(bm, SX1 + 1.08, FL + 2, z + 0.5, -90, 1.0)
        disp(bm, SX0 - 1.08, FL + 2, z + 0.5, 90, 1.0)

    # 망루: 둥근 탑 · 화살 구멍 · 톱니 고리 · 원뿔 지붕 (하늘색 · 테두리) · 금 첨탑 깃발 (디플)
    fm = flag_model("light_blue_wool", "white_wool")

    def tower(cx, cz, r, hgt, wall="calcite"):
        for y in range(FL - 3, FL + hgt + 1):
            for dx in range(-r - 1, r + 2):
                for dz in range(-r - 1, r + 2):
                    d = math.hypot(dx, dz)
                    if r - 0.85 <= d <= r + 0.35:
                        b = wall if (y - FL) % 6 else "smooth_quartz"
                        if y <= FL + 1:
                            b = "stone_bricks"
                        put(cx + dx, y, cz + dz, b)
                    elif d < r - 0.85 and y > FL:
                        put(cx + dx, y, cz + dz, "air")
        for y in range(FL + 4, FL + hgt - 2, 5):
            for a in range(0, 360, 90):
                put(cx + round(math.cos(math.radians(a + 45)) * r), y, cz + round(math.sin(math.radians(a + 45)) * r), "iron_bars")
                put(cx + round(math.cos(math.radians(a + 45)) * r), y + 1, cz + round(math.sin(math.radians(a + 45)) * r), "iron_bars")
        top = FL + hgt
        for dx in range(-r - 1, r + 2):
            for dz in range(-r - 1, r + 2):
                d = math.hypot(dx, dz)
                if d <= r + 1.35:
                    put(cx + dx, top, cz + dz, "spruce_planks" if d < r + 0.4 else "quartz_bricks")
                if r + 0.4 <= d <= r + 1.35 and (dx + dz) % 2 == 0:
                    put(cx + dx, top + 1, cz + dz, "quartz_bricks")
        # 원뿔 지붕
        k = 0
        while True:
            rr = r + 0.9 - k * 0.62
            if rr < 0.35:
                break
            y = top + 2 + k
            for dx in range(-r - 2, r + 3):
                for dz in range(-r - 2, r + 3):
                    d = math.hypot(dx, dz)
                    if d <= rr:
                        put(cx + dx, y, cz + dz, "cyan_concrete" if rr - d < 0.9 and k % 3 == 0 else "light_blue_concrete")
            k += 1
        put(cx, top + 2 + k, cz, "gold_block")
        disp(fm, cx + 0.5, top + 3 + k, cz + 0.5, rng.uniform(0, 360) if False else 90, 1.0)
        return top + 3 + k

    for cx, cz in ((SX0, SZ0), (SX0, SZ1), (SX1, SZ0), (SX1, SZ1)):
        tower(cx, cz, 4, 16)
    for cz in (-14, 14):
        tower(SX0, cz, 3, 13)
    # 성문탑 (쌍둥이 · 동쪽) + 아치 성문 + 내리닫이 창살 + 도개교 (내려진) + 사슬 (디플)
    for cz in (-6, 6):
        tower(SX1, cz, 3, 15)
    for z in range(-3, 4):
        for y in range(FL + 1, FL + 7):
            if y < FL + 6 or abs(z) < 3:
                put(SX1, y, z, "air")
        put(SX1, FL + 7, z, "chiseled_quartz_block")
        put(SX1 + 1, FL + 7, z, "quartz_pillar")
        put(SX1 - 1, FL + 6, z, "iron_bars")
    for x in range(SX1 + 1, SX1 + MOAT + 2):
        for z in range(-3, 4):
            put(x, FL, z, "spruce_planks" if abs(z) < 3 else "stripped_spruce_log")
    disp(chains_model(MOAT + 0.5, 6.5), SX1 + 0.6, FL + 7.5, 0.5, 0, 1.0)
    # 본성 (3단): 아래 큰 홀 · 둘째 단 · 가운데 높은 탑 + 첨탑
    KX0, KX1, KZ0, KZ1 = -94, -72, -11, 11

    def hall(x0, x1, z0, z1, y0, hh, wall, roof_a, roof_b, ridge="z"):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                corner = x in (x0, x1) and z in (z0, z1)
                for y in range(y0, y0 + hh):
                    if corner:
                        put(x, y, z, "quartz_pillar")
                    elif edge:
                        put(x, y, z, wall if (y - y0) % 5 else "polished_diorite")
                    else:
                        put(x, y, z, "air")
                put(x, y0 - 1, z, "smooth_quartz")
        # 창 (스테인드글라스 세로)
        for x in range(x0 + 2, x1 - 1, 3):
            for y in range(y0 + 2, y0 + hh - 2):
                put(x, y, z0, "light_blue_stained_glass")
                put(x, y, z1, "light_blue_stained_glass")
        for z in range(z0 + 2, z1 - 1, 3):
            for y in range(y0 + 2, y0 + hh - 2):
                put(x0, y, z, "light_blue_stained_glass")
                put(x1, y, z, "light_blue_stained_glass")
        # 박공 지붕
        if ridge == "z":
            w = (x1 - x0) // 2 + 1
            for k in range(w + 1):
                for z in range(z0 - 1, z1 + 2):
                    for x in (x0 - 1 + k, x1 + 1 - k):
                        put(x, y0 + hh + k, z, roof_a if k % 2 == 0 else roof_b)
                for x in range(x0 + k, x1 - k + 1):
                    put(x, y0 + hh + k, z0, wall)
                    put(x, y0 + hh + k, z1, wall)
        else:
            w = (z1 - z0) // 2 + 1
            for k in range(w + 1):
                for x in range(x0 - 1, x1 + 2):
                    for z in (z0 - 1 + k, z1 + 1 - k):
                        put(x, y0 + hh + k, z, roof_a if k % 2 == 0 else roof_b)
                for z in range(z0 + k, z1 - k + 1):
                    put(x0, y0 + hh + k, z, wall)
                    put(x1, y0 + hh + k, z, wall)

    hall(KX0, KX1, KZ0, KZ1, FL + 1, 10, "white_concrete", "light_blue_concrete", "cyan_concrete", "z")
    for z in range(-2, 3):
        for y in range(FL + 1, FL + 6):
            put(KX1, y, z, "air")
    for z in (-3, 3):
        for y in range(FL + 1, FL + 8):
            put(KX1 + 1, y, z, "quartz_pillar")
    # 가운데 높은 탑 (본성 뒤쪽)
    ktx, ktz = -88, 0
    top = tower(ktx, ktz, 4, 30, wall="white_concrete")
    # 황금 양털 제단 (본성 안)
    ax, az = -80, 0
    box(ax - 2, FL + 1, az - 2, ax + 2, FL + 1, az + 2, "chiseled_quartz_block")
    box(ax - 1, FL + 2, az - 1, ax + 1, FL + 2, az + 1, "gold_block")
    disp(sheep_model("yellow_wool"), ax + 0.5, FL + 3, az + 0.5, -90, 1.6)
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        box(ax + dx * 3, FL + 1, az + dz * 3, ax + dx * 3, FL + 5, az + dz * 3, "quartz_pillar")
        put(ax + dx * 3, FL + 6, az + dz * 3, "lantern")
    # 분수 광장
    fx, fz = -64, 0
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            d = math.hypot(dx, dz)
            if d <= 4.5:
                put(fx + dx, FL, fz + dz, "smooth_stone" if d > 3.4 else "quartz_bricks")
            if 2.5 <= d <= 3.4:
                put(fx + dx, FL + 1, fz + dz, "quartz_bricks")
            elif d < 2.5:
                put(fx + dx, FL + 1, fz + dz, "water")
    for y in range(FL + 1, FL + 4):
        put(fx, y, fz, "quartz_pillar")
    put(fx, FL + 4, fz, "water")
    # 목조 집 (흰 벽 · 가문비 뼈대 · 파란 지붕) 4채
    def house(x0, z0, w, d, roofc="blue_terracotta"):
        hh = 5
        for x in range(x0, x0 + w):
            for z in range(z0, z0 + d):
                edge = x in (x0, x0 + w - 1) or z in (z0, z0 + d - 1)
                for y in range(FL + 1, FL + hh + 1):
                    if edge:
                        frame = x in (x0, x0 + w - 1) and z in (z0, z0 + d - 1) or y in (FL + 1, FL + 3, FL + hh)
                        put(x, y, z, "spruce_log" if frame else "white_terracotta")
                    else:
                        put(x, y, z, "air")
        for x in range(x0 + 2, x0 + w - 2, 2):
            put(x, FL + 2, z0, "glass_pane")
            put(x, FL + 4, z0, "glass_pane")
            put(x, FL + 2, z0 + d - 1, "glass_pane")
        put(x0 + w // 2, FL + 1, z0 + d - 1, "air")
        put(x0 + w // 2, FL + 2, z0 + d - 1, "air")
        for k in range(d // 2 + 2):
            for x in range(x0 - 1, x0 + w + 1):
                put(x, FL + hh + 1 + k, z0 - 1 + k, roofc)
                put(x, FL + hh + 1 + k, z0 + d - k, roofc)
            for x in (x0, x0 + w - 1):
                for z in range(z0 + k, z0 + d - k):
                    put(x, FL + hh + 1 + k, z, "white_terracotta")
        put(x0 + 1, FL + hh + d // 2 + 3, z0 + d // 2, "bricks")
        put(x0 + 1, FL + hh + d // 2 + 4, z0 + d // 2, "campfire")
    house(-68, -30, 8, 7)
    house(-60, -30, 7, 7, "light_blue_terracotta")
    house(-68, 22, 8, 7, "light_blue_terracotta")
    house(-58, 22, 6, 7)
    # 시장 천막 (디플)
    for i, (sx, sz) in enumerate(((-62, -12), (-62, 12), (-56, -8), (-56, 8))):
        disp(awning(["red_wool", "blue_wool", "yellow_wool", "lime_wool"][i], "white_wool"), sx + 0.5, FL + 1, sz + 0.5, 90 if sz < 0 else -90, 1.0)
    # 헛간 (빨강 · 흰 X 문) · 건초
    bx0, bz0 = -96, 18
    for x in range(bx0, bx0 + 11):
        for z in range(bz0, bz0 + 12):
            edge = x in (bx0, bx0 + 10) or z in (bz0, bz0 + 11)
            for y in range(FL + 1, FL + 7):
                if edge:
                    put(x, y, z, "red_terracotta" if (x + z) % 4 else "red_nether_bricks")
                else:
                    put(x, y, z, "air")
    for k in range(7):
        for z in range(bz0 - 1, bz0 + 13):
            put(bx0 - 1 + k, FL + 7 + k, z, "dark_oak_planks")
            put(bx0 + 11 - k, FL + 7 + k, z, "dark_oak_planks")
        for z in (bz0, bz0 + 11):
            for x in range(bx0 + k, bx0 + 11 - k):
                put(x, FL + 7 + k, z, "red_terracotta")
    for y in range(FL + 1, FL + 6):
        for z in range(bz0 + 4, bz0 + 8):
            put(bx0 + 10, y, z, "white_concrete" if (y - FL + z) % 3 == 0 else "spruce_planks")
    for (hx, hz) in ((-83, 22), (-83, 24), (-82, 23), (-84, 26), (-82, 26)):
        put(hx, FL + 1, hz, "hay_block")
    put(-83, FL + 2, 23, "hay_block")
    # 풍차 (돌 받침 · 흰 탑 · 디플 날개)
    mx, mz = -94, -24
    for y in range(FL + 1, FL + 17):
        r = 3.3 - (y - FL) * 0.09
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                d = math.hypot(dx, dz)
                if r - 0.9 <= d <= r + 0.25:
                    put(mx + dx, y, mz + dz, "cobblestone" if y < FL + 4 else ("smooth_quartz" if (y - FL) % 5 else "spruce_planks"))
                elif d < r - 0.9:
                    put(mx + dx, y, mz + dz, "air")
    for k in range(4):
        for dx in range(-3 + k, 4 - k):
            for dz in range(-3 + k, 4 - k):
                put(mx + dx, FL + 17 + k, mz + dz, "dark_oak_planks")
    disp(windmill_blades(), mx + 4.3, FL + 14.5, mz + 0.5, -90, 1.0)
    # 양 우리 + 양 떼 (디플)
    def pen(x0, z0, x1, z1, n):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                put(x, ground(x, z) + 1, z, "oak_fence")
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                put(x, ground(x, z) + 1, z, "oak_fence")
        put((x0 + x1) // 2, ground((x0 + x1) // 2, z1) + 1, z1, "air")
        for _ in range(n):
            sx, sz = rng.uniform(x0 + 1.5, x1 - 1), rng.uniform(z0 + 1.5, z1 - 1)
            c = str(rng.choice(["white_wool"] * 6 + ["light_gray_wool", "brown_wool", "black_wool"]))
            disp(sheep_model(c), sx, ground(sx, sz) + 1, sz, rng.uniform(0, 360), 1.0)
    pen(-92, -14, -84, -4, 4)
    pen(-60, -22, -54, -16, 2)
    # 성 밖 목장 · 밀밭 · 양 떼
    pen(-44, -30, -34, -16, 6)
    pen(-46, 30, -36, 44, 5)
    for x in range(-48, -36):
        for z in range(4, 14):
            if x in (-48, -37) or z in (4, 13):
                put(x, ground(x, z) + 1, z, "oak_fence")
            else:
                put(x, ground(x, z), z, "farmland" if False else "grass_block")
                put(x, ground(x, z) + 1, z, "wheat[age=7]" if (z % 3) else "air")
        if x % 3 == 0:
            put(x, ground(x, 9), 9, "water") if False else None
    for _ in range(9):
        sx, sz = rng.uniform(-48, -24), rng.uniform(-50, 50)
        disp(sheep_model(), sx, ground(sx, sz) + 1, sz, rng.uniform(0, 360), 1.0)
    # 꽃 · 풀 (양 쪽)
    for _ in range(900):
        x, z = int(rng.integers(-110, -8)), int(rng.integers(-56, 57))
        g = ground(x, z)
        if SX0 - MOAT - 1 <= x <= SX1 + MOAT + 1 and SZ0 - MOAT - 1 <= z <= SZ1 + MOAT + 1:
            if not (SX0 < x < SX1 and SZ0 < z < SZ1):
                continue
            g = FL
        if get(x, g, z) == "grass_block" and get(x, g + 1, z) == "air":
            put(x, g + 1, z, str(rng.choice(["short_grass"] * 5 + ["tall_grass", "dandelion", "poppy", "azure_bluet", "oxeye_daisy", "cornflower", "allium", "pink_petals[facing=north,flower_amount=4]"])))
    for _ in range(26):
        x, z = int(rng.integers(-116, -26)), int(rng.integers(-62, 62))
        if SX0 - MOAT - 4 <= x <= SX1 + MOAT + 4 and SZ0 - MOAT - 4 <= z <= SZ1 + MOAT + 4:
            continue
        if ground(x, z) > FL + 8:
            continue
        r = rng.random()
        if r < 0.45:
            oak(x, z, "birch_log", "birch_leaves")
        elif r < 0.75:
            oak(x, z)
        else:
            oak(x, z, "cherry_log", "cherry_leaves")
    # 길가 등 (성문 → 강)
    for x in range(-46, -10, 7):
        for zz in (-3, 3):
            g = ground(x, zz)
            put(x, g + 1, zz, "oak_fence")
            put(x, g + 2, zz, "oak_fence")
            put(x, g + 3, zz, "lantern")
    for x in range(SX1 + MOAT + 2, -10):
        for z in range(-1, 2):
            g = ground(x, z)
            put(x, g, z, "dirt_path")

    # ══════════════════════════════════════════════════ 늑대 진영 — 달그림자 굴
    WX0, WX1, WZ0, WZ1 = 54, 104, -34, 34
    # 숲 (가문비 · 짙은 참나무 · 죽은 나무) — 진영 밖
    for _ in range(170):
        x, z = int(rng.integers(20, 112)), int(rng.integers(-64, 64))
        if WX0 - 4 <= x <= WX1 + 4 and WZ0 - 4 <= z <= WZ1 + 4:
            continue
        if abs(z) < 4 and x < WX0:
            continue
        if ground(x, z) > FL + 20:
            continue
        r = rng.random()
        if r < 0.6:
            spruce(x, z, int(rng.integers(8, 15)))
        elif r < 0.85:
            oak(x, z, "dark_oak_log", "dark_oak_leaves", int(rng.integers(5, 8)))
        else:
            dead_tree(x, z)
    for _ in range(700):
        x, z = int(rng.integers(8, 112)), int(rng.integers(-60, 60))
        g = ground(x, z)
        if get(x, g + 1, z) == "air" and get(x, g, z) in ("grass_block", "podzol", "moss_block", "coarse_dirt", "rooted_dirt"):
            put(x, g + 1, z, str(rng.choice(["fern", "fern", "large_fern", "short_grass", "dead_bush", "brown_mushroom", "red_mushroom", "sweet_berry_bush"])))
    # 진영 바닥
    for x in range(WX0, WX1 + 1):
        for z in range(WZ0, WZ1 + 1):
            for y in range(FL + 1, FL + 14):
                put(x, y, z, "air")
            for y in range(FL - 3, FL):
                put(x, y, z, "dirt")
            r = rng.random()
            put(x, FL, z, "podzol" if r < 0.35 else ("coarse_dirt" if r < 0.6 else ("rooted_dirt" if r < 0.75 else ("mud" if r < 0.82 else "packed_mud"))))
    for x in range(WX0, WX1 + 1):
        for z in range(-2, 3):
            put(x, FL, z, "mud" if abs(z) < 2 else "packed_mud")
    for x in range(WX0 - 8, WX0):
        for z in range(-2, 3):
            put(x, ground(x, z), z, "coarse_dirt")
    # 뾰족 통나무 울타리 (높낮이 · 기울기 · 위는 뾰족)
    for x in range(WX0, WX1 + 1):
        for z in range(WZ0, WZ1 + 1):
            if not (x in (WX0, WX1) or z in (WZ0, WZ1)):
                continue
            if x == WX0 and -4 <= z <= 4:
                continue
            hh = 7 + int(3 * abs(math.sin(x * 1.7 + z * 2.3)))
            for y in range(FL - 1, FL + hh + 1):
                put(x, y, z, "dark_oak_log" if (x + z) % 3 else "stripped_dark_oak_log")
            put(x, FL + hh + 1, z, "dark_oak_fence")
            if (x + z) % 2 == 0:
                put(x, FL + hh + 2, z, "dark_oak_fence")
    # 안쪽 걷는 단 + 망대 (울타리 위 지붕 있는 망루)
    for x in range(WX0 + 1, WX1):
        for z in (WZ0 + 1, WZ1 - 1):
            put(x, FL + 6, z, "dark_oak_planks")
    for z in range(WZ0 + 1, WZ1):
        for x in (WX0 + 1, WX1 - 1):
            put(x, FL + 6, z, "dark_oak_planks")

    def watch(cx, cz):
        for dx in (-2, 2):
            for dz in (-2, 2):
                for y in range(FL + 1, FL + 13):
                    put(cx + dx, y, cz + dz, "dark_oak_log")
        box(cx - 2, FL + 12, cz - 2, cx + 2, FL + 12, cz + 2, "spruce_planks")
        for dx in range(-2, 3):
            for dz in (-2, 2):
                put(cx + dx, FL + 13, cz + dz, "dark_oak_fence")
                put(cx + dz, FL + 13, cz + dx, "dark_oak_fence")
        for k in range(3):
            for dx in range(-3 + k, 4 - k):
                for dz in range(-3 + k, 4 - k):
                    put(cx + dx, FL + 16 + k, cz + dz, "brown_wool" if (dx + dz) % 2 else "dark_oak_planks")
        put(cx, FL + 15, cz, "soul_lantern")
    for cx, cz in ((WX0, WZ0), (WX0, WZ1), (WX1, WZ0), (WX1, WZ1), (WX0 + 25, WZ0), (WX0 + 25, WZ1)):
        watch(cx, cz)
    # 성문 (서쪽): 블랙스톤 문틀 + 거대 늑대 해골 (디플) + 붉은 깃발 (디플)
    for z in (-6, 6):
        for y in range(FL + 1, FL + 13):
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if max(abs(dx), abs(dz)) == 2:
                        put(WX0 + dx, y, z + dz, "polished_blackstone_bricks" if (y - FL) % 4 else "gilded_blackstone" if (y - FL) == 8 else "blackstone")
                    else:
                        put(WX0 + dx, y, z + dz, "air")
        box(WX0 - 2, FL + 13, z - 2, WX0 + 2, FL + 13, z + 2, "polished_blackstone")
        for dx in (-2, 2):
            for dz in (-2, 2):
                put(WX0 + dx, FL + 14, z + dz, "polished_blackstone_wall")
                put(WX0 + dx, FL + 15, z + dz, "soul_lantern")
    for z in range(-4, 5):
        put(WX0, FL + 11, z, "polished_blackstone_bricks")
        put(WX0, FL + 12, z, "polished_blackstone_bricks")
    disp(wolf_skull(), WX0 - 1.5, FL + 10.5, 0.5, -90, 1.6)
    rb = banner_model("red_wool", "bone_block", "black_concrete")
    for z in (-6, 6):
        disp(rb, WX0 - 3.1, FL + 4, z + 0.5, -90, 1.0)
    for z in range(-26, 27, 13):
        if abs(z) > 8:
            disp(rb, WX0 - 1.1, FL + 2, z + 0.5, -90, 0.9)
    # 천막 (A자 · 짐승 가죽 색)
    def tent(x, z, c):
        for k in range(4):
            for zz in range(z - 3, z + 4):
                put(x - 3 + k, FL + 1 + k, zz, c)
                put(x + 3 - k, FL + 1 + k, zz, c)
        for zz in (z - 4, z + 4):
            put(x, FL + 1, zz, "spruce_fence")
            put(x, FL + 2, zz, "spruce_fence")
            put(x, FL + 3, zz, "spruce_fence")
            put(x, FL + 4, zz, "spruce_fence")
        put(x, FL + 1, z, "campfire") if False else None
    for x, z, c in ((64, -24, "brown_wool"), (74, -24, "gray_wool"), (64, 24, "gray_wool"), (74, 24, "brown_wool"), (96, 26, "black_wool")):
        tent(x, z, c)
    # 토템 (줄무늬 통나무 · 해골 꼭대기 = 뼈 · 붉은 눈)
    for x, z in ((62, -10), (62, 10), (90, -14), (90, 14)):
        for y in range(FL + 1, FL + 7):
            put(x, y, z, "stripped_dark_oak_log" if y % 2 else "dark_oak_log")
        put(x, FL + 7, z, "bone_block")
        put(x, FL + 8, z, "bone_block")
        put(x - 1, FL + 7, z, "redstone_block")
        put(x, FL + 9, z, "soul_lantern")
    # 모닥불 광장 + 뼈 무더기
    for dx in range(-5, 6):
        for dz in range(-5, 6):
            d = math.hypot(dx, dz)
            if d < 5.5:
                put(76 + dx, FL, dz, "blackstone" if d < 2 else ("packed_mud" if d < 4 else "mud_bricks"))
            if 4.4 < d < 5.5 and (dx * 3 + dz) % 4 == 0:
                put(76 + dx, FL + 1, dz, "polished_blackstone_wall")
    put(76, FL + 1, 0, "campfire")
    for x, z in ((70, -16), (82, 18), (68, 14)):
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if rng.random() < 0.7:
                    put(x + dx, FL + 1, z + dz, "bone_block")
        put(x, FL + 2, z, "bone_block")
    # 굴 (북동 바위 언덕 안쪽 · 붉은 눈)
    for dz in range(-3, 4):
        for y in range(FL + 1, FL + 6):
            if abs(dz) + max(0, y - FL - 4) <= 3:
                for dx in range(0, 7):
                    put(96 + dx, y, WZ0 - 3 + dz + 0, "air") if False else None
    # 늑대 무리 (디플)
    for _ in range(12):
        wx, wz = rng.uniform(58, 100), rng.uniform(-28, 28)
        if abs(wz) < 3:
            continue
        disp(wolf_model(str(rng.choice(["light_gray_concrete", "gray_concrete", "light_gray_concrete", "black_concrete"])), sit=rng.random() < 0.35),
             wx, FL + 1, wz, rng.uniform(0, 360), 1.15)
    for _ in range(6):                                 # 숲속 늑대
        wx, wz = rng.uniform(26, 50), rng.uniform(-50, 50)
        disp(wolf_model("gray_concrete"), wx, ground(wx, wz) + 1, wz, rng.uniform(0, 360), 1.15)
    # 달의 제단 (동쪽) — 심층암 원형 단 3층 · 돌기둥 고리 · 우는 흑요석 · 거대 하울링 늑대 석상 (디플) · 떠 있는 달 (디플)
    ex, ez = 92, 0
    for lvl, rad, mat in ((0, 9.5, "polished_deepslate"), (1, 7.5, "deepslate_tiles"), (2, 5.5, "deepslate_bricks")):
        for dx in range(-10, 11):
            for dz in range(-10, 11):
                if math.hypot(dx, dz) <= rad:
                    put(ex + dx, FL + 1 + lvl, ez + dz, mat)
    for a in range(0, 360, 30):
        px_, pz_ = ex + round(math.cos(math.radians(a)) * 9), ez + round(math.sin(math.radians(a)) * 9)
        hh = 5 + (a // 30) % 3 * 2
        for y in range(FL + 2, FL + 2 + hh):
            put(px_, y, pz_, "chiseled_deepslate" if y % 3 else "polished_deepslate")
        put(px_, FL + 2 + hh, pz_, "crying_obsidian")
    for dz in (-3, 3):
        for y in range(FL + 4, FL + 7):
            put(ex - 4, y, ez + dz, "crying_obsidian")
    disp(howling_wolf(), ex + 0.5, FL + 4, ez + 0.5, 90, 5.0)
    disp(moon_model(), ex + 0.5, FL + 58, ez + 0.5, 0, 6.0)
    # 진영 안 영혼 등 기둥
    for x, z in ((60, -18), (60, 18), (84, -28), (84, 28), (102, -12), (102, 12)):
        for y in range(FL + 1, FL + 4):
            put(x, y, z, "dark_oak_fence")
        put(x, FL + 4, z, "soul_lantern")
    return v


def label(img, xy, text, col, font):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    x, y = xy
    tw = d.textlength(text, font=font)
    d.rounded_rectangle((x - tw / 2 - 12, y - 19, x + tw / 2 + 12, y + 19), 9, fill=(10, 14, 24))
    d.text((x - tw / 2, y - 15), text, font=font, fill=col)


def make_mesh(sun):
    import render as R
    import bdkit as K
    mesh = R.Mesh()
    for model, x, y, z, yaw, sc in DISPLAYS:
        K.add_to_mesh(mesh, model, np.array([CX + x, y, CZ + z]), yaw, sc, sun)
    return mesh


def preview(path):
    import render as R
    from PIL import Image, ImageDraw, ImageFont
    v = build()
    pal = R.Palette(PAL)
    W, Hh = 1280, 720
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 28)
    fs = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 22)
    GOLD = dict(sun=(-0.55, 0.55, -0.4), sun_col=(1.15, 0.95, 0.74), amb_col=(0.55, 0.58, 0.72),
                sky_top=(0.30, 0.46, 0.80), sky_hor=(0.96, 0.80, 0.62), fog_col=(0.86, 0.80, 0.74))
    sun = np.array(GOLD["sun"], float); sun /= np.linalg.norm(sun)
    mesh = make_mesh(sun)
    shots = [
        ((CX - 6, FL + 120, CZ + 168), (CX, FL - 4, CZ - 4), 50, "양과 늑대 — 1:1 공성전 맵  ·  서: 하얀 목장 왕국   ·   가운데: 강과 다리 3개   ·   동: 달그림자 굴"),
        ((CX - 40, FL + 34, CZ + 56), (CX - 80, FL + 6, CZ), 60, "양 진영 — 해자 · 도개교 · 쌍둥이 성문탑 · 하얀 성벽과 깃발 · 원뿔 지붕 망루 · 본성과 높은 탑"),
        ((CX - 60, FL + 14, CZ + 16), (CX - 82, FL + 5, CZ), 66, "양 진영 안 — 황금 양털 제단 · 분수 광장 · 시장 천막 · 목조 집 · 양 우리"),
        ((CX + 36, FL + 32, CZ + 52), (CX + 78, FL + 6, CZ), 60, "늑대 진영 — 뾰족 통나무 울타리 · 망대 · 거대 늑대 해골 성문 · 천막 · 토템 · 늑대 무리"),
        ((CX + 62, FL + 12, CZ + 30), (CX + 92, FL + 22, CZ), 64, "달의 제단 — 거대 하울링 늑대 석상 · 떠 있는 달 · 우는 흑요석 기둥 고리"),
        ((CX + 18, FL + 14, CZ + 30), (CX, FL + 5, CZ), 62, "가운데 — 폐허 망루 섬의 넓은 다리 · 아치 돌다리 · 갈대와 연잎 (부딪히는 곳)"),
    ]
    out = Image.new("RGB", (W, Hh * (len(shots) + 1)))
    for i, (cam, tgt, fov, lab) in enumerate(shots):
        im = R.render(v, pal, W, Hh, cam, tgt, fov=fov, mesh=mesh, ss=2, fog_dist=900, **GOLD)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, 48), fill=(12, 16, 30))
        d.text((16, 10), lab, font=fs, fill=(255, 232, 170))
        out.paste(im, (0, Hh * i))
    sc = W / (NX * 1.02)
    im = R.render(v, pal, W, Hh, (CX + 0.01, FL + 160, CZ + 0.5), (CX, FL, CZ), ortho_scale=sc, mesh=mesh, ss=2, fog_dist=3000, **GOLD)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 48), fill=(12, 16, 30))
    d.text((16, 10), "위에서 본 지도  (왼쪽 = 양 · 오른쪽 = 늑대)", font=fs, fill=(255, 232, 170))

    def px(x, z):
        return (W / 2 + x * sc, Hh / 2 + z * sc)
    label(im, px(-80, -20), "황금 양털 제단", (255, 236, 150), font)
    label(im, px(-76, 46), "양 진영 · 하얀 목장 왕국", (235, 245, 255), font)
    label(im, px(0, -54), "북쪽 아치 다리", (225, 232, 240), fs)
    label(im, px(0, 16), "폐허 망루 섬", (225, 232, 240), fs)
    label(im, px(0, 54), "남쪽 아치 다리", (225, 232, 240), fs)
    label(im, px(92, -20), "달의 제단", (255, 170, 170), font)
    label(im, px(78, 46), "늑대 진영 · 달그림자 굴", (255, 205, 205), font)
    out.paste(im, (0, Hh * len(shots)))
    out.save(path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview(sys.argv[1] if len(sys.argv) > 1 else "sheepwolf.png")
