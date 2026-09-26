"""스팀펑크 RPG 1시즌 월드 — 마인크래프트 지도처럼 위에서 본 그림 (1픽셀 = 1블록, 2000 x 2000)

 지형: 높이맵(여러 겹 잡음) + 지역별 지면 블록 + 강 · 호수 · 바다
 구조물: 마을(길 · 집 · 지붕 · 시계탑 · 부두) · 풍차 · 고철 더미 · 채석장 · 철도 · 비행선 부두
 음영: 마크 지도 방식 (북쪽 블록보다 높으면 밝게, 낮으면 어둡게) + 물 깊이
 출력: rpg/preview/world_mc.png (전체), world_mc_labeled.png (이름 표시), world_mc_town.png (확대)
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "preview")
os.makedirs(OUT, exist_ok=True)
N = 2000                      # 월드 크기 (블록)
H0 = -1000                    # 좌표 시작 (x, z = -1000 ~ 999)
SEA = 62
R = np.random.default_rng(2024)

FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"


def font(n):
    return ImageFont.truetype(FONT, n)


def I(v):
    return int(v - H0)


def noise(scale, seed, octaves=5, persist=0.5):
    rng = np.random.default_rng(seed)
    out = np.zeros((N, N), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = max(3, int(N / scale * (2 ** o)))
        a = rng.random((n, n)).astype(np.float32)
        im = Image.fromarray(a, "F").resize((N, N), Image.BICUBIC)
        out += np.asarray(im) * amp
        tot += amp
        amp *= persist
    return out / tot


yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
X = xx + H0
Z = yy + H0


def dist(cx, cz):
    return np.sqrt((X - cx) ** 2 + (Z - cz) ** 2)


def soft(d, r, w):
    return np.clip((r - d) / w, 0, 1)


# ─────────────────────────────────────────────────────────────── 지역 가중치
n1 = noise(500, 1)
n2 = noise(160, 2)
n3 = noise(60, 3, 4)
wx = (noise(380, 41) - 0.5) * 520
wz = (noise(380, 42) - 0.5) * 520
WX, WZ = X + wx, Z + wz                                    # 왜곡된 좌표 (경계를 구불구불하게)


def wdist(cx, cz):
    return np.sqrt((WX - cx) ** 2 + (WZ - cz) ** 2)


warp = (noise(300, 4) - 0.5) * 260
coast_z = 770 + (noise(420, 5, 5) - 0.5) * 260 + np.where(np.abs(X) < 180, 60, 0) * (1 - np.abs(X) / 180).clip(0, 1)
land = np.clip((coast_z - Z) / 30, 0, 1)

w_hills = soft(wdist(-620, 140), 400, 220)
w_forest = soft(wdist(640, 160), 400, 220)
w_canyon = soft(wdist(-60, -470), 360, 200)
w_north = np.clip((-700 - Z + wx * 0.5) / 180, 0, 1)

# ─────────────────────────────────────────────────────────────── 높이
def ridged(scale, seed):
    r = 1 - np.abs(noise(scale, seed, 5) * 2 - 1)
    return r ** 2


h = SEA + 5 + (n1 - 0.5) * 16 + (n2 - 0.5) * 10 + (n3 - 0.5) * 3
h += w_hills * (14 + ridged(140, 6) * 70 + n3 * 6)
h += w_forest * (5 + n2 * 14)
mesa = 26 + noise(120, 61) * 26
h += w_canyon * mesa
h = np.where(w_canyon > 0.25, h - (h % 5) * np.clip(w_canyon * 2 - 0.5, 0, 1) * 0.9, h)     # 계단식 절벽
h += w_north * (30 + ridged(110, 7) * 110)
# 협곡: 강을 따라 깊게 파임
# 강 줄기: 북쪽 설산 → 협곡 → 평원 → 바다 (x 가 z 에 따라 굽이침)
river_x = 120 + np.sin((Z + 1000) / 260) * 140 + (noise(300, 8)[:, :1] - 0.5) * 60
dr = np.abs(X - river_x)
river_w = 7 + 5 * soft(-Z, 0, 400) + 12 * np.clip((Z - 500) / 300, 0, 1)
canyon_cut = w_canyon * np.clip(1 - dr / 70, 0, 1) ** 1.5 * 34
h -= canyon_cut
river = (dr < river_w) & (Z > -900)
h = np.where(river, np.minimum(h, SEA - 2 - (river_w - dr) * 0.25), h)
# 호수 두 곳
for cx, cz, r in ((-260, 360, 55), (430, -40, 40)):
    d = dist(cx, cz) + (n3 - 0.5) * 30
    h = np.where(d < r, np.minimum(h, SEA - 1 - (r - d) * 0.12), h)
# 바다
sea_depth = np.clip((Z - coast_z) / 6, 0, 30)
h = np.where(land < 1, np.minimum(h, SEA - 1 - sea_depth), h)
# 마을 터는 평평하게
TOWNS = {"brass": (-150, 690, 115), "cog": (-60, -560, 145)}
for k, (cx, cz, r) in TOWNS.items():
    t = soft(dist(cx, cz), r, 50)
    target = SEA + 5 if k == "brass" else SEA + 34
    h = h * (1 - t) + target * t
h = np.round(h).astype(np.int32)
water = h < SEA

# ─────────────────────────────────────────────────────────────── 지면 색 (블록)
C = {
    "wall": (118, 117, 119),
    "grass": (104, 158, 70), "grass_dry": (143, 160, 82), "grass_dark": (78, 128, 56),
    "sand": (219, 207, 163), "red_sand": (190, 103, 33), "gravel": (131, 125, 122),
    "stone": (125, 125, 125), "andesite": (136, 136, 137), "dirt": (134, 96, 67), "coarse": (119, 85, 59),
    "podzol": (91, 63, 24), "snow": (244, 250, 250), "ice": (145, 183, 253),
    "tc_orange": (161, 83, 37), "tc_white": (209, 178, 161), "tc_brown": (77, 51, 35), "tc": (152, 94, 67),
    "path": (148, 122, 74), "cobble": (122, 122, 122), "stonebrick": (122, 121, 122), "planks": (162, 130, 78),
    "dark_planks": (66, 43, 20), "brick": (150, 74, 60), "copper": (192, 107, 79), "copper_ox": (82, 162, 132),
    "deepslate": (70, 70, 72), "iron": (220, 220, 220), "hay": (166, 136, 38), "wheat": (170, 160, 60),
    "farmland": (110, 75, 45), "leaves": (58, 112, 38), "leaves_dark": (40, 88, 28), "spruce": (46, 72, 46),
    "water": (58, 92, 200), "lava": (207, 92, 20), "rail": (110, 104, 96), "black": (20, 20, 22),
}
img = np.zeros((N, N, 3), np.float32)
SURF_NAMES = list(C.keys())
SURF = np.zeros((N, N), np.int16)
TREES = []           # (x, z, r, kind)   배열 좌표
BUILDS = []          # (x, z, w, d, roof, ridge_x)  월드 좌표


def put(mask, name, var=0.06):
    SURF[mask] = SURF_NAMES.index(name)
    col = np.array(C[name], np.float32)
    jit = 1 + (R.random((N, N)).astype(np.float32) - 0.5) * 2 * var
    img[mask] = (col[None, :] * jit[mask][:, None])


slope = np.abs(np.gradient(h.astype(np.float32))[0]) + np.abs(np.gradient(h.astype(np.float32))[1])
put(np.ones((N, N), bool), "grass", 0.035)
gv = noise(90, 21, 4)
img *= (0.93 + gv * 0.14)[..., None]                                             # 풀 색 잔잔한 얼룩
put((noise(25, 9, 3) > 0.83) & (w_hills < 0.3) & (w_forest < 0.3) & (w_canyon < 0.2), "coarse")
put((noise(200, 22) > 0.7) & (w_hills < 0.2) & (w_forest < 0.2), "grass_dry", 0.04)
# 폐광산 언덕: 돌 · 자갈 · 안산암, 가파른 곳은 돌
hill = w_hills > 0.35
put(hill & (n3 > 0.45), "stone")
put(hill & (n3 <= 0.45) & (n2 > 0.5), "gravel")
put(hill & (n3 <= 0.45) & (n2 <= 0.5), "andesite")
put(hill & (slope < 1.2) & (noise(50, 10, 3) > 0.55), "grass_dry")
# 숲: 포드졸 · 어두운 풀
fr = w_forest > 0.35
put(fr, "grass_dark")
put(fr & (n3 > 0.62), "podzol")
# 협곡: 테라코타 층 (높이에 따라 줄무늬)
cy = (w_canyon > 0.35) & ~water
bands = ["tc_orange", "tc_white", "tc", "tc_brown", "tc_orange", "red_sand", "tc", "tc_white"]
for i, b in enumerate(bands):
    put(cy & ((h // 4) % len(bands) == i), b, 0.04)
put(cy & (slope < 0.6) & (n3 > 0.55), "red_sand", 0.05)
# 설산
put(w_north > 0.4, "stone")
put((w_north > 0.4) & (h > SEA + 70), "snow", 0.02)
# 모래 해변 · 강가
beach = (~water) & (h <= SEA + 2) & (land < 1.0 + 1) & ((Z > coast_z - 40) | (dr < river_w + 4))
put(beach, "sand")
put(water & (Z < coast_z), "gravel")          # 강 바닥 (물 아래)

# ─────────────────────────────────────────────────────────────── 나무
tree_layer = np.zeros((N, N), np.int8)       # 0 없음 1 참나무 2 짙은 3 가문비
tree_h = np.zeros((N, N), np.float32)


def stamp_tree(x, z, r, kind):
    TREES.append((x, z, r, kind))
    x0, x1 = max(0, x - r), min(N, x + r + 1)
    z0, z1 = max(0, z - r), min(N, z + r + 1)
    sub_y, sub_x = np.mgrid[z0:z1, x0:x1]
    d = np.sqrt((sub_x - x) ** 2 + (sub_y - z) ** 2)
    m = d <= r + 0.3
    tree_layer[z0:z1, x0:x1][m] = kind
    tree_h[z0:z1, x0:x1][m] = np.maximum(tree_h[z0:z1, x0:x1][m], (r + 0.5 - d[m]) / (r + 0.5) + 0.2)


def scatter(weight, density, rmin, rmax, kind_fn):
    n = int(N * N * density)
    xs = R.integers(0, N, n); zs = R.integers(0, N, n)
    for x, z in zip(xs, zs):
        if water[z, x] or R.random() > weight[z, x]:
            continue
        stamp_tree(int(x), int(z), int(R.integers(rmin, rmax + 1)), kind_fn(x, z))


scatter(np.clip(w_forest * 1.3, 0, 1) * (1 - w_canyon), 0.05, 2, 4, lambda x, z: 2 if R.random() < 0.6 else 1)
scatter(np.clip((noise(70, 23) - 0.62) * 4, 0, 1) * (1 - w_forest) * (1 - w_hills * 0.7) * (1 - w_canyon) * (1 - w_north), 0.03, 2, 3, lambda x, z: 1)
scatter(np.clip(w_north * (1 - np.clip((h - SEA - 70) / 20, 0, 1)) * 0.7 + w_hills * 0.25, 0, 1), 0.012, 1, 2, lambda x, z: 3)

# ─────────────────────────────────────────────────────────────── 구조물 그리기 도구
over = Image.new("RGBA", (N, N), (0, 0, 0, 0))
D = ImageDraw.Draw(over)
struct = np.zeros((N, N), bool)


def rect(x0, z0, x1, z1, name, outline=None):
    D.rectangle([I(x0), I(z0), I(x1), I(z1)], fill=C[name] + (255,), outline=(C[outline] + (255,)) if outline else None)


def building(x, z, w, d, roof, ridge_x=True):
    """집: 지붕 + 용마루(가운데 줄) + 처마 그림자"""
    BUILDS.append((x, z, w, d, roof, ridge_x))
    D.rectangle([I(x) + 1, I(z) + 1, I(x + w) + 1, I(z + d) + 1], fill=(0, 0, 0, 90))
    rect(x, z, x + w, z + d, roof)
    dark = tuple(int(c * 0.72) for c in C[roof]) + (255,)
    light = tuple(min(255, int(c * 1.15)) for c in C[roof]) + (255,)
    if ridge_x:
        D.rectangle([I(x), I(z), I(x + w), I(z + d / 2) - 1], fill=light)
        D.line([I(x), I(z + d / 2), I(x + w), I(z + d / 2)], fill=dark, width=1)
    else:
        D.rectangle([I(x), I(z), I(x + w / 2) - 1, I(z + d)], fill=light)
        D.line([I(x + w / 2), I(z), I(x + w / 2), I(z + d)], fill=dark, width=1)
    D.rectangle([I(x), I(z), I(x + w), I(z + d)], outline=dark)


def road(pts, name="path", w=4):
    D.line([(I(x), I(z)) for x, z in pts], fill=C[name] + (255,), width=w, joint="curve")


def rail(pts):
    P_ = [(I(x), I(z)) for x, z in pts]
    D.line(P_, fill=C["gravel"] + (255,), width=5, joint="curve")
    D.line(P_, fill=C["rail"] + (255,), width=3, joint="curve")
    D.line(P_, fill=(60, 45, 30, 255), width=1, joint="curve")


def town(cx, cz, r, rng, style="brass"):
    """둥근 성곽 도시: 성벽 + 성문 4 · 순환로 2겹 · 방사 도로 8 · 길을 따라 늘어선 집 · 가운데 광장과 시계탑"""
    roofs = ["dark_planks", "brick", "dark_planks", "copper", "brick", "deepslate", "copper_ox", "brick"]
    # 성벽 (돌벽돌 고리 + 망루)
    for rr, w in ((r, 5), (r - 2, 1)):
        D.ellipse([I(cx - rr), I(cz - rr), I(cx + rr), I(cz + rr)], outline=(C["wall"] if w > 1 else C["deepslate"]) + (255,), width=w)
    for k in range(12):
        a = k / 12 * 6.283
        tx, tz = cx + math.cos(a) * r, cz + math.sin(a) * r
        building(tx - 4, tz - 4, 8, 8, "deepslate")
    # 도로
    for rr in (r * 0.38, r * 0.72):
        D.ellipse([I(cx - rr), I(cz - rr), I(cx + rr), I(cz + rr)], outline=C["cobble"] + (255,), width=4)
    for k in range(8):
        a = k / 8 * 6.283 + 0.2
        road([(cx + math.cos(a) * 18, cz + math.sin(a) * 18), (cx + math.cos(a) * (r + 12), cz + math.sin(a) * (r + 12))], "cobble", 4)
    # 집: 순환로 사이 띠에 촘촘히 (길 방향으로 정렬)
    for ring_r0, ring_r1 in ((22, r * 0.36), (r * 0.40, r * 0.70), (r * 0.74, r * 0.95)):
        n = int(2 * math.pi * (ring_r0 + ring_r1) / 2 / 13)
        for i in range(n):
            a = i / n * 6.283 + rng.uniform(-0.05, 0.05)
            if min(abs(((a - 0.2) % (6.283 / 8)) - 0), abs(((a - 0.2) % (6.283 / 8)) - 6.283 / 8)) < 0.1:
                continue                                  # 방사 도로 자리 비움
            rr = rng.uniform(ring_r0 + 5, ring_r1 - 5)
            bx, bz = cx + math.cos(a) * rr, cz + math.sin(a) * rr
            if water[I(bz), I(bx)]:
                continue
            w = int(rng.integers(7, 12)); d = int(rng.integers(6, 10))
            building(bx - w / 2, bz - d / 2, w, d, roofs[int(rng.integers(0, len(roofs)))], abs(math.cos(a)) < 0.7)
    # 광장 + 시계탑 + 나무
    D.ellipse([I(cx - 18), I(cz - 18), I(cx + 18), I(cz + 18)], fill=C["stonebrick"] + (255,))
    building(cx - 6, cz - 6, 12, 12, "copper_ox", True)
    D.rectangle([I(cx - 2), I(cz - 2), I(cx + 2), I(cz + 2)], fill=C["iron"] + (255,))
    for k in range(6):
        a = k / 6 * 6.283
        D.ellipse([I(cx + math.cos(a) * 14 - 2), I(cz + math.sin(a) * 14 - 2), I(cx + math.cos(a) * 14 + 2), I(cz + math.sin(a) * 14 + 2)], fill=C["leaves"] + (255,))


# ─────────────────────────────────────────────────────────────── 길 · 철도
MAIN = [(-150, 575), (-60, 400), (40, 200), (60, 0), (20, -200), (-40, -415)]
WEST = [(40, 200), (-200, 150), (-420, 90), (-640, 40), (-720, 0)]
EAST = [(60, 0), (260, 40), (470, 90), (650, 70), (720, 40)]
road(MAIN, "gravel", 9); road(MAIN, "path", 6); road(WEST, "gravel", 7); road(WEST, "path", 5); road(EAST, "gravel", 7); road(EAST, "path", 5)
rail([(p[0] + 10, p[1]) for p in MAIN]); rail([(p[0], p[1] + 10) for p in WEST]); rail([(p[0], p[1] + 10) for p in EAST])
# 다리 (강 건너는 곳)
for z in (200, -200, 400):
    rx = 120 + math.sin((z + 1000) / 260) * 140
    rect(rx - 14, z - 4, rx + 14, z + 4, "planks")

# 브라스헤이븐: 항구 도시 + 부두 (바다까지) + 배
town(-150, 690, 115, np.random.default_rng(11))
for px in (-230, -185, -140, -95):
    z0 = 700
    cz_ = int(coast_z[0, I(px)]) if False else None
    zz = 700
    while zz < 960 and not water[I(zz), I(px)]:
        zz += 1
    rect(px - 3, 760, px + 3, zz + 60, "planks")
    rect(px - 8, zz + 54, px + 8, zz + 60, "dark_planks")
    D.ellipse([I(px + 8), I(zz + 20), I(px + 20), I(zz + 56)], fill=C["dark_planks"] + (255,))
    D.rectangle([I(px + 13), I(zz + 26), I(px + 15), I(zz + 50)], fill=(230, 225, 210, 255))

# 코그시티: 큰 공업 수도 + 파이프 + 비행선 부두 + 비행선
town(-60, -560, 140, np.random.default_rng(12))
for k in range(8):
    a = k / 8 * 6.28
    D.line([I(-60 + math.cos(a + 0.4) * 30), I(-560 + math.sin(a + 0.4) * 30), I(-60 + math.cos(a + 0.4) * 128), I(-560 + math.sin(a + 0.4) * 128)], fill=C["copper_ox"] + (255,), width=2)
rect(150, -640, 210, -600, "stonebrick", "deepslate")
D.ellipse([I(160), I(-660), I(200), I(-580)], fill=(170, 40, 40, 255))
for k in range(5):
    D.line([I(162 + k * 9), I(-655), I(162 + k * 9), I(-585)], fill=(235, 225, 200, 255), width=2)
rect(174, -600, 186, -588, "dark_planks")

# 녹슨 평원: 풍차 · 농장 · 고철 더미
wr = np.random.default_rng(13)
for k in range(9):
    fx, fz = float(wr.uniform(-320, 320)), float(wr.uniform(150, 520))
    if abs(fx - (120 + math.sin((fz + 1000) / 260) * 140)) < 40:
        continue
    for r_ in range(6):
        D.rectangle([I(fx), I(fz + r_ * 5), I(fx + 30), I(fz + r_ * 5 + 3)], fill=(C["wheat"] if r_ % 2 == 0 else C["farmland"]) + (255,))
    building(fx + 32, fz + 4, 8, 8, "dark_planks")
    cxm, czm = I(fx + 36), I(fz + 8)
    D.line([cxm - 9, czm - 9, cxm + 9, czm + 9], fill=(230, 220, 200, 255), width=2)
    D.line([cxm - 9, czm + 9, cxm + 9, czm - 9], fill=(230, 220, 200, 255), width=2)
for k in range(40):
    sx, sz = float(wr.uniform(-450, 450)), float(wr.uniform(-150, 560))
    if water[I(sz), I(sx)] or math.hypot(sx, sz - 640) < 150:
        continue
    for j in range(int(wr.integers(4, 12))):
        name = ["iron", "copper", "copper_ox", "deepslate", "cobble"][int(wr.integers(0, 5))]
        ox, oz = int(wr.integers(-4, 5)), int(wr.integers(-4, 5))
        rect(sx + ox, sz + oz, sx + ox + int(wr.integers(1, 3)), sz + oz + int(wr.integers(1, 3)), name)

# 폐광산: 채석장 (계단 모양 구덩이) + 입구 + 광차 레일
for qx, qz, qr in ((-560, 40, 55), (-760, 230, 40)):
    for k in range(6):
        rr = qr - k * 8
        if rr <= 0:
            break
        shade = int(125 - k * 12)
        D.ellipse([I(qx - rr), I(qz - rr * 0.8), I(qx + rr), I(qz + rr * 0.8)], fill=(shade, shade, shade - 2, 255))
D.ellipse([I(-736), I(-12), I(-704), I(12)], fill=C["black"] + (255,))
rect(-740, -16, -700, -12, "dark_planks"); rect(-740, 12, -700, 16, "dark_planks")

# 태엽 숲: 대성당 공터 (던전 입구)
D.ellipse([I(660), I(-10), I(760), I(90)], fill=C["grass_dark"] + (255,))
building(690, 10, 40, 60, "deepslate", False)
D.ellipse([I(704), I(30), I(716), I(42)], fill=C["copper_ox"] + (255,))

# 던전 입구 표시 (보라 차원문)
for x, z in ((-720, 0), (710, 40), (40, -760)):
    D.ellipse([I(x - 5), I(z - 5), I(x + 5), I(z + 5)], fill=(150, 60, 230, 255), outline=(40, 10, 70, 255))

ov = np.asarray(over, np.float32) / 255
struct = ov[..., 3] > 0.5
_cols = np.array([C[k] for k in SURF_NAMES], np.float32)
_px = ov[struct][:, :3] * 255
_idx = np.argmin(((_px[:, None, :] - _cols[None, :, :]) ** 2).sum(-1), axis=1)
OVER = np.full((N, N), -1, np.int16)
OVER[struct] = _idx

# ─────────────────────────────────────────────────────────────── 합성 + 음영
# 물
depth = np.clip(SEA - h, 0, 40).astype(np.float32)
wc = np.array(C["water"], np.float32)
shallow = np.array((70, 170, 190), np.float32)
tdep = np.clip(depth / 10, 0, 1)[..., None]
wimg = (shallow[None, None, :] * (1 - tdep) + wc[None, None, :] * tdep) * (1.05 - np.clip(depth / 40, 0, 0.5))[..., None]
wimg += (R.random((N, N, 1)).astype(np.float32) - 0.5) * 6
img = np.where(water[..., None], wimg, img)
# 나무
tcol = {1: C["leaves"], 2: C["leaves_dark"], 3: C["spruce"]}
for k, col in tcol.items():
    m = (tree_layer == k) & ~water
    c = np.array(col, np.float32)
    img[m] = c[None, :] * (0.75 + 0.45 * tree_h[m])[:, None] * (1 + (R.random(m.sum()).astype(np.float32) - 0.5) * 0.18)[:, None]
# 구조물
img = img * (1 - ov[..., 3:4]) + ov[..., :3] * 255 * ov[..., 3:4]

# 마크 지도 음영: 북쪽(위) 블록과 높이 비교
hh = h.astype(np.float32) + tree_layer.astype(np.float32) * 5 + struct * 4
north = np.vstack([hh[:1], hh[:-1]])
shade = np.where(hh > north, 1.08, np.where(hh < north, 0.80, 0.94))
shade = np.where(water, 1.0, shade)
# 부드러운 언덕 음영 (서북쪽 빛)
gx, gz = np.gradient(hh)
lam = np.clip(1 - (gx * 0.09 + gz * 0.12), 0.62, 1.3)
img = img * (shade * np.where(water, 1.0, lam))[..., None]
img = np.clip(img, 0, 255).astype(np.uint8)
base = Image.fromarray(img, "RGB")
base.save(os.path.join(OUT, "world_mc_raw.png"))

# ─────────────────────────────────────────────────────────────── 출력: 전체 (지도 테두리 + 이름)
def labeled(im, scale):
    W = im.width * scale
    big = im.resize((W, W), Image.NEAREST).convert("RGBA")
    d = ImageDraw.Draw(big)
    labels = [
        ("브라스헤이븐", "시작 항구 도시", -150, 545), ("녹슨 평원", "Lv.1–10", -150, 330),
        ("폐광산 언덕", "Lv.10–20", -620, 250), ("태엽 숲", "Lv.20–30", 560, 300),
        ("코그시티", "수도 · 비행선 부두", -60, -725), ("코그 협곡", "Lv.25–30", -330, -380),
        ("얼어붙은 북쪽 산맥", "2시즌에 열림", -200, -900),
    ]
    for nm, sub, x, z in labels:
        cx, cy = (x - H0) * scale, (z - H0) * scale
        f1, f2 = font(int(18 * scale)), font(int(11 * scale))
        for t, f, col in ((nm, f1, (255, 255, 255)), (sub, f2, (255, 230, 150))):
            w = d.textlength(t, font=f)
            d.text((cx - w / 2, cy), t, font=f, fill=col, stroke_width=max(2, scale), stroke_fill=(20, 15, 10))
            cy += f.size + 2
    for nm, x, z in (("폭주한 기관실", -720, 0), ("태엽 대성당", 710, 40), ("협곡 던전", 40, -760)):
        cx, cy = (x - H0) * scale, (z - H0) * scale
        d.text((cx + 8 * scale, cy - 6 * scale), nm, font=font(int(9 * scale)), fill=(230, 200, 255), stroke_width=2, stroke_fill=(30, 10, 40))
    # 액자 (마크 지도 느낌)
    fr = Image.new("RGBA", (W + 40, W + 40), (130, 94, 58, 255))
    ImageDraw.Draw(fr).rectangle([8, 8, W + 31, W + 31], fill=(90, 62, 36, 255))
    fr.paste(big, (20, 20))
    return fr


labeled(base, 1).convert("RGB").save(os.path.join(OUT, "world_mc_labeled.png"))
base.resize((1000, 1000), Image.LANCZOS).save(os.path.join(OUT, "world_mc_small.png"))
# 확대: 브라스헤이븐 · 코그시티 (1블록 = 5픽셀)
for nm, (cx, cz, r) in (("town", TOWNS["brass"]), ("cog", TOWNS["cog"])):
    x0, z0 = I(cx - 200), I(cz - 160)
    crop = base.crop((x0, z0, x0 + 400, z0 + 320)).resize((2000, 1600), Image.NEAREST)
    crop.save(os.path.join(OUT, f"world_mc_{nm}.png"))
np.savez_compressed(os.path.join(HERE, ".world_mc.npz"), h=h, surf=SURF, over=OVER, water=water,
                    trees=np.array(TREES, np.int32), names=np.array(SURF_NAMES))
import json
json.dump([list(map(lambda v: v if isinstance(v, str) else float(v), b)) for b in BUILDS], open(os.path.join(HERE, ".world_mc_builds.json"), "w"))
print("done", len(TREES), len(BUILDS))
