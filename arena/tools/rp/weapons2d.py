"""상점 전설 무기 — 2D 수묵 아이템 텍스처 (512 에 붓으로 그려 256 으로 줄임, 배경 투명)

 무기는 대각선(왼쪽 아래 손잡이 → 오른쪽 위 끝)으로 그린다 — 마인크래프트 손에 드는 아이템(handheld) 방향.
 표현: 먹 담채 채움(가장자리 고임) + 마른 붓 외곽선 + 붓 획(수술·번개·문양) + 색 먹 번짐 빛
"""
import math

import numpy as np
from PIL import Image
from scipy import ndimage

from ink import stroke, wash, colorize, line_path
from telegraphs import over

S = 512
A = np.array((64.0, 452.0))          # 자루 끝 (왼쪽 아래)
B = np.array((452.0, 60.0))          # 끝 (오른쪽 위)
D = (B - A) / np.linalg.norm(B - A)
N = np.array((D[1], -D[0])) * -1     # 날의 '위쪽' (왼쪽 위)
L = float(np.linalg.norm(B - A))
YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
U = (XX - A[0]) * D[0] + (YY - A[1]) * D[1]
V = (XX - A[0]) * N[0] + (YY - A[1]) * N[1]
INK = ((24, 20, 24), (4, 2, 6), (80, 74, 80))


def P(u, v):
    return tuple(A + D * u + N * v)


def path(pts, n=24):
    out = []
    for i in range(len(pts) - 1):
        out += line_path(P(*pts[i]), P(*pts[i + 1]), n)
    return out


def dense(pts, step=0.8):
    """캔버스 좌표 점들을 촘촘하게 (붓 도장이 끊기지 않게)"""
    out = []
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i], float), np.array(pts[i + 1], float)
        n = max(2, int(np.linalg.norm(b - a) / step))
        out += [tuple(a + (b - a) * k / n) for k in range(n)]
    out.append(tuple(pts[-1]))
    return out


def noise(seed, sigma=3.0):
    R = np.random.default_rng(seed)
    n = ndimage.gaussian_filter(R.random((S, S)).astype(np.float32), sigma)
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


def streak(seed):
    """붓 결 (날 방향으로 길게 늘어진 노이즈)"""
    R = np.random.default_rng(seed)
    n = R.random((S, S)).astype(np.float32)
    ang = math.degrees(math.atan2(D[1], D[0]))
    n = ndimage.rotate(ndimage.gaussian_filter(ndimage.rotate(n, ang, reshape=False, mode="wrap"), (0.6, 9)), -ang, reshape=False, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


def fill(mask, col, deep, light, seed, shade=None, strength=0.62, alpha=1.0, grain=0.25):
    """먹 담채 채움: 가장자리 고임 + 붓 결 + (선택) 명암 그라데이션"""
    m = mask.astype(np.float32)
    w = wash(m, seed, 0.5, 2.0)
    g = streak(seed + 1)
    dens = m * strength + w * 0.35 + (g - 0.5) * grain * m
    if shade is not None:
        dens = dens + shade * m
    dens = np.clip(dens, 0, 1) * np.clip(ndimage.gaussian_filter(m, 0.8) * 1.4, 0, 1)
    return colorize(dens, alpha, col, deep, light)


def edge(mask, w, seed, ink=INK, dry=0.35):
    """마른 붓 외곽선: 경계 띠 + 굵기 흔들림 + 갈라짐"""
    m = mask.astype(bool)
    din = ndimage.distance_transform_edt(m)
    dout = ndimage.distance_transform_edt(~m)
    nz = noise(seed, 5)
    ww = w * (0.65 + 0.7 * nz)
    band = np.clip(ww - np.where(m, din, dout * 1.6) + 0.5, 0, 1)
    br = streak(seed + 7)
    band *= np.where(br < dry * 0.5, 0.25, 1.0) * (0.8 + 0.3 * br)
    return colorize(np.clip(band * 1.1, 0, 1), 1.0, *ink)


def glow(dens, col, sigma=7, k=1.2):
    g = np.clip(ndimage.gaussian_filter(dens, sigma) * k, 0, 1)
    out = np.zeros((S, S, 4), np.float32)
    out[..., :3] = col
    out[..., 3] = g * 200
    return out


def brush(pts, width, seed, col=INK, alpha=1.0, **kw):
    d = stroke(S, path(pts), width, seed=seed, **kw)
    return colorize(d, alpha, *col), d


def band_mask(u0, u1, hw):
    return (U >= u0) & (U <= u1) & (np.abs(V) <= hw)


def taper_mask(pts):
    """(u, 반폭) 목록으로 좌우 대칭 윤곽"""
    us = np.array([p[0] for p in pts]); ws = np.array([p[1] for p in pts])
    hw = np.interp(U, us, ws, left=-1, right=-1)
    return (U >= us[0]) & (U <= us[-1]) & (np.abs(V) <= hw)


def poly_mask(pts):
    from PIL import ImageDraw
    im = Image.new("L", (S, S), 0)
    ImageDraw.Draw(im).polygon([P(u, v) for u, v in pts], fill=255)
    return np.asarray(im) > 127


def disc(u, v, r):
    c = P(u, v)
    return np.hypot(XX - c[0], YY - c[1]) <= r


def tassel(u0, seed, col=((200, 30, 34), (110, 8, 14), (250, 110, 90)), n=7, length=120, spread=26):
    layers = []
    R = np.random.default_rng(seed)
    for k in range(n):
        off = (k / (n - 1) - 0.5) * spread
        pts = [(u0, off * 0.2)]
        for i in range(1, 6):
            t = i / 5
            pts.append((u0 - length * t * (0.8 + 0.3 * R.random()), off * (0.4 + t) + math.sin(t * 3 + k) * 8))
        layers.append(brush(pts, 7 + R.random() * 4, seed + k, col, dry=0.55, pool=0.15, taper=(0.1, 0.5), bristles=10)[0])
    return layers


GOLD = ((214, 160, 52), (120, 70, 14), (255, 226, 140))
STEEL = ((168, 180, 198), (70, 80, 98), (236, 242, 250))
JADE = ((52, 150, 116), (14, 70, 52), (150, 230, 196))
LACQ = ((170, 28, 30), (80, 6, 10), (230, 90, 80))
BLACKL = ((46, 40, 46), (10, 8, 12), (110, 100, 110))
PAPER = ((226, 222, 204), (170, 160, 130), (250, 248, 238))


def gold_bands(us, hw, seed):
    L_ = []
    for i, u in enumerate(us):
        m = band_mask(u - 5, u + 5, hw)
        L_ += [fill(m, *GOLD, seed + i, shade=V / 40), edge(m, 1.6, seed + 50 + i)]
    return L_


# ─────────────────────────────────────────────────────────── 뇌정검
def thunder():
    Ls = tassel(96, 10, length=92, spread=22)
    pom = taper_mask([(80, 6), (88, 13), (100, 13), (106, 8)])
    grip = band_mask(104, 186, 9)
    guard = taper_mask([(186, 14), (192, 34), (198, 42), (204, 40), (210, 22), (214, 12)]) | disc(200, 38, 9) | disc(200, -38, 9)
    blade = taper_mask([(212, 15), (260, 16), (420, 13), (500, 10), (530, 5), (548, 0.5)])
    Ls += [fill(pom, *GOLD, 11, shade=V / 30), edge(pom, 2.2, 12)]
    Ls += [fill(grip, *BLACKL, 13, shade=V / 25)]
    for k in range(7):                                        # 끈 감기 (사선 획)
        u = 110 + k * 11
        Ls.append(brush([(u, -10), (u + 8, 10)], 4.5, 20 + k, ((70, 56, 90), (20, 14, 30), (140, 120, 170)), dry=0.3, pool=0, bristles=6)[0])
    Ls.append(edge(grip, 2.0, 14))
    Ls += [fill(blade, *STEEL, 15, shade=-V / 40 * 0.6), edge(blade, 2.6, 16)]
    Ls.append(brush([(222, 0), (505, 0)], 3.0, 17, dry=0.55, pool=0, bristles=5, taper=(0.05, 0.8))[0])   # 가운데 능선
    # 보랏빛 번개 (빛 번짐 + 획)
    R = np.random.default_rng(3)
    pts = [(236, 0)]
    for i in range(1, 11):
        pts.append((236 + i * 26, (6 if i % 2 else -6) + R.normal(0, 1.5)))
    d = stroke(S, path(pts, 10), 6, seed=18, dry=0.3, pool=0.2, taper=(0.05, 0.9), bristles=8)
    Ls += [glow(d, (170, 120, 255), 6, 0.9), colorize(d, 1.0, (190, 160, 255), (90, 50, 200), (250, 245, 255))]
    Ls += [fill(guard, *GOLD, 19, shade=V / 60), edge(guard, 2.4, 20)]
    for s in (-1, 1):                                          # 구름 소용돌이
        c = [(200 + 7 * math.cos(t), s * (34 + 7 * math.sin(t))) for t in np.linspace(0, 5, 20)]
        Ls.append(brush(c, 3.0, 21 + s, dry=0.4, pool=0, bristles=5)[0])
    gem = disc(200, 0, 8)
    Ls += [glow(gem.astype(np.float32), (120, 255, 200), 5, 1.2), fill(gem, *JADE, 22), edge(gem, 1.6, 23)]
    return Ls


# ─────────────────────────────────────────────────────────── 청룡언월도
def dragon():
    shaft = band_mask(22, 372, 8)
    butt = taper_mask([(4, 1), (12, 7), (24, 8)])
    Ls = [fill(butt, *GOLD, 30), edge(butt, 1.8, 31), fill(shaft, *LACQ, 32, shade=V / 22), edge(shaft, 2.0, 33)]
    Ls += gold_bands((40, 150, 260, 360), 9.5, 34)
    # 칼날: 등은 곧게(+v), 날은 아래(-v)로 완만하게 불룩, 끝은 등 쪽으로 휘어 뾰족 (날 뿌리에 홈)
    edge_pts = [(380, -9), (398, -14), (404, -8), (416, -22), (446, -36), (478, -42), (506, -38), (530, -24), (546, -4), (556, 16)]
    spine = [(380, 11), (470, 11), (520, 12), (544, 14), (556, 16)]
    blade = poly_mask(spine + edge_pts[::-1])
    shade_ = np.clip((V + 44) / 60, 0, 1) * 0.35 - 0.12
    Ls += [fill(blade, *STEEL, 35, shade=shade_), edge(blade, 2.6, 36)]
    Ls.append(brush([(392, 5), (520, 6), (540, 9)], 2.6, 39, dry=0.45, pool=0, bristles=4, taper=(0.1, 0.8))[0])   # 피홈
    d = stroke(S, path([(e[0], e[1] + 4) for e in edge_pts[3:-1]], 16), 4, seed=37, dry=0.25, pool=0, taper=(0.05, 0.9), bristles=6)
    Ls += [glow(d, (110, 255, 190), 4, 0.9), colorize(d, 1.0, (120, 240, 190), (30, 140, 100), (220, 255, 240))]
    # 칼등 톱니 + 구름 문양 획
    for k in range(3):
        u = 418 + k * 32
        m = poly_mask([(u, 10), (u + 12, 10), (u + 4, 22)])
        Ls += [fill(m, *STEEL, 38 + k), edge(m, 1.5, 41 + k)]
    # 청룡 머리
    head = (disc(378, 0, 22) | poly_mask([(372, -16), (412, -10), (416, 2), (400, 16), (372, 18)]))
    Ls += tassel(360, 50, ((196, 34, 30), (100, 8, 10), (250, 120, 90)), n=6, length=70, spread=30)
    Ls += [fill(head, *JADE, 45, shade=V / 50), edge(head, 2.6, 46)]
    Ls.append(brush([(368, 14), (346, 30), (330, 34)], 5, 47, dry=0.5, pool=0.1, bristles=6)[0])      # 뿔
    Ls.append(brush([(372, 16), (354, 26)], 4, 48, dry=0.5, pool=0.1, bristles=5)[0])
    eye = disc(392, 6, 4.5)
    Ls += [glow(eye.astype(np.float32), (255, 220, 100), 4, 1.5), colorize(eye.astype(np.float32), 1, (255, 214, 90), (160, 90, 10), (255, 250, 200))]
    Ls.append(brush([(396, -6), (410, -8)], 3, 49, dry=0.4, pool=0, bristles=4)[0])                   # 입
    return Ls


# ─────────────────────────────────────────────────────────── 풍혼선 (펼친 부채, 사선으로 기울임)
def wind():
    piv = np.array((138.0, 394.0))
    lo, hi = -106.0, -14.0                    # 펼친 각 (위 → 오른쪽): 손잡이 방향과 맞춘 대각선 부채
    R0, R1 = 92.0, 292.0
    ang = np.degrees(np.arctan2(YY - piv[1], XX - piv[0]))
    rr = np.hypot(XX - piv[0], YY - piv[1])
    inside = (ang >= lo) & (ang <= hi)
    paper = inside & (rr >= R0) & (rr <= R1)

    def pol(t, r):
        return tuple(piv + np.array((math.cos(math.radians(t)), math.sin(math.radians(t)))) * r)
    Ls = [fill(paper, *PAPER, 60, strength=0.45, grain=0.12)]
    # 먹 산 (부드러운 봉우리 + 담채), 뒤 산은 옅게
    Rg = np.random.default_rng(7)
    for k, (ca, h, wd, a_) in enumerate(((-86, 120, 70, 0.5), (-58, 150, 80, 0.8), (-34, 105, 60, 0.6))):
        cx, cy = pol(ca, 250)
        base = cy + 40
        ridge = base - h * np.clip(1 - np.abs(XX - cx) / wd, 0, 1) ** 1.4 - ndimage.gaussian_filter1d(Rg.normal(0, 1, S), 6)[None, :] * 6
        mnt = (YY > ridge) & paper & (YY < base + 30)
        Ls.append(colorize(np.clip(wash(mnt, 61 + k, 0.5, 3) * 1.15, 0, 1), a_, (46, 50, 58), (6, 6, 10), (150, 154, 162)))
    # 비취 물결 (붓 획)
    for k in range(3):
        r = 120 + k * 20
        pts = dense([pol(t, r + math.sin(t / 5) * 5) for t in np.linspace(lo + 4, hi - 4, 60)])
        d = stroke(S, pts, 5, seed=64 + k, dry=0.4, pool=0.05, bristles=6)
        Ls.append(colorize(d * paper, 1.0, (60, 170, 140), (10, 80, 60), (170, 240, 210)))
    # 살 (먹 획, 양 끝 굵게)
    for k in range(12):
        t = lo + (hi - lo) * k / 11
        w_ = 8 if k in (0, 11) else 3.6
        d = stroke(S, dense([pol(t, 10), pol(t, R1 + 6)]), w_, seed=70 + k, dry=0.25, pool=0.05, taper=(0.05, 0.95), bristles=6)
        Ls.append(colorize(d, 1.0, *INK))
    # 금테
    for r, w_, sd in ((R1, 7, 90), (R0, 4.5, 91)):
        d = stroke(S, dense([pol(t, r) for t in np.linspace(lo, hi, 90)]), w_, seed=sd, dry=0.35, pool=0.1, bristles=10)
        Ls += [glow(d, (255, 220, 120), 3, 0.5), colorize(d, 1.0, *GOLD)]
    Ls.append(edge(paper, 1.3, 92))
    # 사북 + 청록 수술 (왼쪽 아래로)
    hub = np.hypot(XX - piv[0], YY - piv[1]) <= 13
    Ls += [glow(hub.astype(np.float32), (120, 255, 210), 5, 1.0), fill(hub, *GOLD, 93), edge(hub, 2, 94)]
    for k in range(6):
        off = (k - 2.5) * 5
        pts = dense([(piv[0] - 6, piv[1] + 8)] + [(piv[0] - 70 * t + off * t + math.sin(t * 4 + k) * 5, piv[1] + 8 + 80 * t) for t in np.linspace(0.15, 1, 7)])
        d = stroke(S, pts, 7, seed=95 + k, dry=0.5, pool=0.1, taper=(0.1, 0.5), bristles=8)
        Ls.append(colorize(d, 1.0, (50, 160, 130), (10, 80, 60), (160, 240, 210)))
    return Ls


# ─────────────────────────────────────────────────────────── 방천화극
def phoenix():
    shaft = band_mask(20, 392, 7.5)
    butt = taper_mask([(4, 1), (12, 7), (22, 8)])
    Ls = [fill(butt, *GOLD, 100), edge(butt, 1.8, 101), fill(shaft, *BLACKL, 102, shade=V / 22), edge(shaft, 2.0, 103)]
    Ls += gold_bands((40, 160, 280, 384), 9, 104)
    # 봉황 깃 (주황 · 붉은 깃 흘러내림)
    R = np.random.default_rng(9)
    for k in range(8):
        off = (k / 7 - 0.5) * 34
        pts = [(392, off * 0.2)] + [(392 - 110 * t * (0.8 + 0.3 * R.random()), off * (0.5 + t) + math.sin(t * 4 + k) * 7) for t in np.linspace(0.2, 1, 5)]
        col = ((236, 110, 40), (150, 40, 10), (255, 200, 110)) if k % 2 else ((210, 40, 34), (110, 10, 10), (255, 140, 100))
        Ls.append(brush(pts, 9, 110 + k, col, dry=0.5, pool=0.1, taper=(0.1, 0.55), bristles=12)[0])
    collar = taper_mask([(388, 10), (396, 13), (410, 13), (416, 9)])
    Ls += [fill(collar, *GOLD, 120, shade=V / 30), edge(collar, 2, 121)]
    # 양쪽 초승달 날 (월아)
    for s in (-1, 1):
        c1 = P(440, s * 28); c2 = P(452, s * 16)
        moon = (np.hypot(XX - c1[0], YY - c1[1]) <= 34) & ~(np.hypot(XX - c2[0], YY - c2[1]) <= 30) & (V * s > 10)
        Ls += [fill(moon, *STEEL, 122 + s, shade=-np.abs(V) / 120), edge(moon, 2.4, 124 + s)]
        arc = [(440 + 32 * math.cos(t), s * (28 + 32 * math.sin(t) * 1.0)) for t in np.linspace(-1.2, 1.9, 30)]
        d = stroke(S, path([(a[0], a[1] if s > 0 else a[1]) for a in arc], 3), 3.5, seed=126 + s, dry=0.4, pool=0, bristles=5)
        Ls += [glow(d * moon, (255, 210, 90), 5, 1.4)]
    # 창날 (잎 모양)
    head = taper_mask([(414, 8), (440, 14), (480, 17), (515, 12), (538, 5), (552, 0.5)])
    Ls += [fill(head, *STEEL, 128, shade=-V / 40 * 0.6), edge(head, 2.6, 129)]
    d = stroke(S, path([(420, 0), (530, 0)]), 3.5, seed=130, dry=0.4, pool=0, taper=(0.05, 0.85), bristles=5)
    Ls += [glow(d, (255, 210, 90), 6, 1.6), colorize(d, 1.0, (255, 214, 100), (170, 100, 10), (255, 248, 210))]
    gem = disc(402, 0, 7)
    Ls += [glow(gem.astype(np.float32), (255, 100, 60), 5, 1.4), fill(gem, (220, 50, 40), (110, 10, 10), (255, 150, 120), 131), edge(gem, 1.4, 132)]
    return Ls


WEAPONS = {"thunder": thunder, "dragon": dragon, "wind": wind, "phoenix": phoenix}


# ─────────────────────────────────────────────────────────── 흑철대도 (넓은 외날 칼, 핏빛 날)
IRONB = ((70, 72, 80), (16, 16, 20), (150, 154, 166))


def blackiron():
    ring = disc(84, 0, 20) & ~disc(84, 0, 11)
    Ls = tassel(70, 200, length=80, spread=24)
    Ls += [fill(ring, *GOLD, 201), edge(ring, 2.2, 202)]
    grip = band_mask(104, 184, 10)
    Ls += [fill(grip, *LACQ, 203, shade=V / 25), edge(grip, 2, 204)]
    for k in range(6):
        u = 110 + k * 12
        Ls.append(brush([(u, -11), (u + 9, 11)], 4.5, 205 + k, ((40, 30, 30), (10, 6, 6), (100, 80, 80)), dry=0.3, pool=0, bristles=6)[0])
    guard = disc(192, 0, 20)
    Ls += [fill(guard, *GOLD, 212, shade=V / 50), edge(guard, 2.4, 213)]
    spine = [(200, 13), (470, 14), (530, 14), (556, 12)]
    edge_pts = [(200, -12), (300, -18), (400, -26), (470, -34), (515, -30), (545, -12), (556, 12)]
    blade = poly_mask(spine + edge_pts[::-1])
    Ls += [fill(blade, *IRONB, 214, shade=np.clip((V + 30) / 60, 0, 1) * 0.3 - 0.1), edge(blade, 2.6, 215)]
    d = stroke(S, path([(e[0], e[1] + 4) for e in edge_pts[1:-1]], 16), 4.5, seed=216, dry=0.3, pool=0, taper=(0.05, 0.9), bristles=6)
    Ls += [glow(d, (255, 60, 50), 5, 1.1), colorize(d, 1.0, (230, 40, 40), (120, 6, 10), (255, 150, 130))]
    Ls.append(brush([(214, 7), (500, 8)], 2.6, 217, ((170, 170, 180), (80, 80, 90), (230, 230, 240)), dry=0.5, pool=0, bristles=4)[0])
    return Ls


# ─────────────────────────────────────────────────────────── 백호조 (호랑이 발톱 수갑)
def tiger():
    Ls = []
    arm = taper_mask([(90, 30), (150, 34), (230, 36), (270, 30)])
    Ls += [fill(arm, *PAPER, 220, shade=V / 90, strength=0.65), edge(arm, 2.6, 221)]
    for k in range(6):                                  # 백호 줄무늬
        u = 110 + k * 26
        Ls.append(brush([(u, -34), (u + 10, -12), (u + 2, 4)], 7, 222 + k, dry=0.5, pool=0.2, taper=(0.1, 0.6), bristles=8)[0])
        Ls.append(brush([(u + 8, 34), (u + 16, 14)], 6, 230 + k, dry=0.5, pool=0.2, taper=(0.1, 0.6), bristles=8)[0])
    knuckle = taper_mask([(262, 38), (292, 40)])
    Ls += [fill(knuckle, *GOLD, 240, shade=V / 60), edge(knuckle, 2.2, 241)]
    for j, off in enumerate((-26, 0, 26)):
        pts = [(292, off - 6), (380, off - 8), (460, off - 2 + j), (530, off + 18), (552, off + 30)]
        back = [(292, off + 6), (380, off + 5), (460, off + 10), (530, off + 26), (552, off + 30)]
        cl = poly_mask(pts + back[::-1])
        Ls += [fill(cl, *STEEL, 242 + j, shade=-V / 90), edge(cl, 2.2, 245 + j)]
        d = stroke(S, path([(p[0], p[1] + 1) for p in pts[1:]], 14), 3, seed=248 + j, dry=0.3, pool=0, bristles=4)
        Ls += [glow(d, (140, 220, 255), 4, 0.9), colorize(d, 1.0, (170, 230, 255), (40, 120, 200), (240, 250, 255))]
    gem = disc(276, 0, 9)
    Ls += [glow(gem.astype(np.float32), (140, 220, 255), 5, 1.2), fill(gem, (120, 200, 250), (20, 80, 150), (220, 245, 255), 251), edge(gem, 1.6, 252)]
    return Ls


# ─────────────────────────────────────────────────────────── 여의봉 (붉은 옻칠 봉 + 금 머리)
def staff():
    shaft = band_mask(60, 500, 9)
    Ls = [fill(shaft, *LACQ, 260, shade=V / 22), edge(shaft, 2.2, 261)]
    for u0, u1 in ((14, 62), (498, 548)):
        cap = taper_mask([(u0, 11), (u0 + 6, 13), (u1 - 6, 13), (u1, 11)])
        Ls += [fill(cap, *GOLD, 262 + u0, shade=V / 40), edge(cap, 2.4, 263 + u0)]
        for k in range(3):
            u = u0 + 12 + k * 12
            Ls.append(brush([(u, -12), (u + 4, 0), (u, 12)], 2.6, 264 + u0 + k, ((140, 80, 14), (70, 36, 6), (220, 170, 80)), dry=0.4, pool=0, bristles=4)[0])
    for k in range(5):                                   # 금빛 경문 띠 (빛남)
        u = 130 + k * 75
        d = stroke(S, path([(u, -9), (u + 10, 9)], 8), 5, seed=280 + k, dry=0.3, pool=0.1, bristles=6)
        Ls += [glow(d, (255, 220, 110), 5, 1.0), colorize(d, 1.0, *GOLD)]
    Ls.append(brush([(80, -4), (480, -5)], 2.4, 290, ((255, 170, 150), (180, 60, 50), (255, 220, 210)), alpha=0.7, dry=0.6, pool=0, bristles=4)[0])
    return Ls


# ─────────────────────────────────────────────────────────── 도목검 (복숭아나무 부적검 + 노란 부적)
WOOD = ((176, 112, 70), (90, 48, 24), (226, 170, 120))
TALIS = ((236, 206, 90), (170, 130, 30), (252, 236, 170))


def peachwood():
    Ls = tassel(96, 300, length=84, spread=20)
    pom = taper_mask([(84, 8), (92, 12), (104, 10)])
    grip = band_mask(104, 182, 9)
    guard = taper_mask([(182, 12), (188, 30), (198, 30), (204, 12)])
    blade = taper_mask([(204, 16), (440, 15), (505, 12), (536, 6), (550, 0.5)])
    Ls += [fill(pom, *WOOD, 301), edge(pom, 2, 302), fill(grip, *WOOD, 303, shade=V / 30), edge(grip, 2, 304),
           fill(guard, *WOOD, 305), edge(guard, 2.2, 306), fill(blade, *WOOD, 307, shade=-V / 50), edge(blade, 2.6, 308)]
    # 주사(붉은) 부적 문양 (빛남)
    pts = [(220, 0)]
    for i in range(1, 12):
        pts.append((220 + i * 26, (7 if i % 3 == 0 else -5 if i % 3 == 1 else 2)))
    d = stroke(S, path(pts, 10), 4, seed=309, dry=0.3, pool=0.1, bristles=5)
    Ls += [glow(d, (255, 110, 60), 5, 1.0), colorize(d, 1.0, (220, 40, 30), (110, 10, 6), (255, 140, 110))]
    # 노란 부적 두 장 (가드에 매달림)
    for j, off in enumerate((-22, 22)):
        tal = poly_mask([(200, off - 9), (206, off + 9), (130, off + 16 + j * 4), (122, off - 2 + j * 4)])
        Ls += [fill(tal, *TALIS, 310 + j, strength=0.7), edge(tal, 1.6, 312 + j)]
        Ls.append(brush([(190, off), (150, off + 8), (136, off + 4 + j * 3)], 3, 314 + j, ((200, 30, 20), (110, 6, 6), (250, 120, 100)), dry=0.4, pool=0.1, bristles=4)[0])
    return Ls


WEAPONS.update({"blackiron": blackiron, "tiger": tiger, "staff": staff, "peachwood": peachwood})


def paint(wid, out=256):
    img = over(*WEAPONS[wid]())
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")
    return im.resize((out, out), Image.LANCZOS)


def export(pack):
    for wid in WEAPONS:
        ref = pack.texture(f"weapon/{wid}", paint(wid))
        pack.item_model(f"weapon/{wid}", {"parent": "minecraft:item/handheld", "textures": {"layer0": ref}})


def preview(path):
    ims = [paint(w) for w in WEAPONS]
    W = Image.new("RGBA", (256 * len(ims), 512), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        W.paste(Image.new("RGBA", (256, 256), (238, 232, 216, 255)), (i * 256, 0))
        W.paste(Image.new("RGBA", (256, 256), (46, 44, 50, 255)), (i * 256, 256))
        W.alpha_composite(im, (i * 256, 0))
        W.alpha_composite(im, (i * 256, 256))
    W.convert("RGB").save(path)
