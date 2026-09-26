"""추가 전설 무기 8종 + 보스 전용 무기 4종 — 128px 픽셀 판타지 (사용자 그림 톤에 맞춤)

 그리는 법: icon2d 캔버스(512px)에 부품을 쌓고 → 뒤에 빛 소용돌이(오라) → 128px 로 줄여
 1px 테두리 · 색 줄이기 · 반짝이 점을 얹는다.  무기 축: 왼쪽 아래(손잡이) → 오른쪽 위(끝)
"""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from icon2d import *
from icon2d import S, XX, YY, U, V, A as AX0, D as AXD, N as AXN


_part0 = Canvas.part
Canvas.part = lambda self, mask, mat, seed=1, *a, **k: _part0(self, mask, mat, abs(int(seed)) % 100000, *a, **k)

# ─────────────────────────────────────────────── 재질
def M(base, **k):
    d = dict(spec=0.8, shin=40, env=0.35, rough=0.05)
    d.update(k)
    return Mat(base, **d)


ICE_B = M((150, 215, 255), spec=1.0, shin=70, env=0.5, rough=0.02, sky=(235, 250, 255), ground=(30, 80, 160))
ICE_D = M((70, 130, 210), spec=0.9, shin=60, env=0.4, rough=0.03, sky=(170, 220, 255), ground=(10, 30, 80))
SILVER = M((200, 210, 225), spec=1.0, shin=60, env=0.55, grain="brushed", sky=(255, 255, 255), ground=(50, 60, 80))
GOLD2 = M((236, 180, 60), spec=1.0, shin=45, env=0.5, grain="brushed", sky=(255, 244, 190), ground=(110, 56, 8))
DGOLD = M((170, 110, 30), spec=0.8, shin=35, env=0.4, grain="brushed", sky=(240, 200, 120), ground=(60, 30, 4))
NAVY = M((40, 56, 110), spec=0.7, shin=40, env=0.3, sky=(120, 150, 230), ground=(8, 10, 30))
STORM = M((70, 120, 200), spec=1.0, shin=60, env=0.5, rough=0.03, sky=(200, 230, 255), ground=(10, 30, 80))
DARKM = M((46, 44, 56), spec=0.9, shin=50, env=0.4, grain="brushed", sky=(140, 140, 170), ground=(8, 8, 12))
GHOST = M((170, 230, 215), spec=1.0, shin=70, env=0.45, rough=0.02, sky=(240, 255, 250), ground=(20, 70, 70))
BONE2 = M((232, 222, 196), spec=0.4, shin=20, env=0.2, grain="stone", rough=0.1, sky=(255, 250, 235), ground=(90, 70, 50))
PEARL = M((250, 246, 232), spec=1.0, shin=60, env=0.5, rough=0.02, sky=(255, 255, 255), ground=(150, 130, 90))
TWIST = M((70, 44, 50), spec=0.3, shin=14, env=0.1, grain="wood", rough=0.3)
TOXIC = gem((90, 230, 60))
SUN = M((255, 160, 40), spec=1.0, shin=50, env=0.5, rough=0.03, sky=(255, 240, 180), ground=(140, 40, 0), glow=(255, 150, 40))
CRIM = M((170, 24, 34), spec=0.7, shin=35, env=0.3, grain="leather", rough=0.15, sky=(255, 140, 140), ground=(40, 0, 6))
STONE2 = M((120, 116, 112), spec=0.3, shin=12, env=0.15, grain="stone", rough=0.3, sky=(220, 215, 205), ground=(40, 36, 32))
LAVA = M((255, 120, 30), spec=0.4, shin=20, env=0.2, rough=0.05, glow=(255, 120, 30))
BRONZE2 = M((196, 124, 56), spec=1.0, shin=40, env=0.5, grain="brushed", sky=(255, 214, 160), ground=(70, 30, 8))
LAPIS = gem((40, 80, 200))
SAND = M((236, 200, 120), spec=0.2, shin=10, env=0.2, grain="stone", rough=0.1, glow=(255, 210, 120))
SCALE_G = M((60, 150, 60), spec=0.9, shin=50, env=0.35, rough=0.04, sky=(200, 255, 170), ground=(10, 40, 10))
SCALE_D = M((26, 80, 36), spec=0.8, shin=40, env=0.3, rough=0.05)
OAK = M((110, 70, 40), spec=0.15, shin=10, env=0.05, grain="wood", rough=0.3)
IRON = M((120, 124, 134), spec=0.9, shin=50, env=0.45, grain="brushed", sky=(210, 220, 235), ground=(30, 30, 36))
EYEW = M((250, 240, 225), spec=1.0, shin=70, env=0.3, rough=0.02)
EYER = gem((230, 70, 20))


# ─────────────────────────────────────────────── 도형 도우미
def curve(pts, n=16):
    """열린 캣멀롬 곡선 → 점 목록"""
    P_ = np.array(pts, float)
    P_ = np.vstack([P_[0] * 2 - P_[1], P_, P_[-1] * 2 - P_[-2]])
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P_[-2])
    return [tuple(p) for p in out]


def stroke(pts, w0, w1=None, local=True):
    """굵기가 w0 → w1 로 변하는 붓질 마스크"""
    w1 = w0 if w1 is None else w1
    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    Q = [P(*p) if local else p for p in pts]
    n = len(Q)
    for i, (x, y) in enumerate(Q):
        r = (w0 + (w1 - w0) * i / max(1, n - 1)) / 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
        if i:
            px, py = Q[i - 1]
            d.line([(px, py), (x, y)], fill=255, width=max(1, int(r * 2)))
    return np.asarray(im) > 127


def cdisc(x, y, r):
    return np.hypot(XX - x, YY - y) <= r


def ring_mask(x, y, r0, r1):
    d = np.hypot(XX - x, YY - y)
    return (d >= r0) & (d <= r1)


def local_pts(pts):
    return [P(u, v) for u, v in pts]


def filigree(c, u, v, s, side=1, mat=None, seed=0):
    """금 덩굴 장식 (소용돌이 두 개)"""
    mat = mat or GOLD2
    pts = [(u, v), (u + 10 * s, v + side * 14 * s), (u + 4 * s, v + side * 26 * s), (u - 8 * s, v + side * 24 * s), (u - 6 * s, v + side * 16 * s)]
    c.part(stroke(curve(pts, 10), 6 * s, 3 * s), mat, seed, bevel=3)


# ─────────────────────────────────────────────── 오라 (뒤에 깔리는 빛 소용돌이)
class Aura:
    def __init__(self):
        self.col = np.zeros((S, S, 3), np.float32)
        self.a = np.zeros((S, S), np.float32)

    def wisp(self, pts, w, color, core=None, alpha=0.85, local=True):
        """끝이 가늘어지는 빛 붓질 (가장자리 = 색, 속 = 밝은 색)"""
        m = stroke(curve(pts, 14), w, 1.0, local).astype(np.float32)
        m = ndimage.gaussian_filter(m, 1.2)
        core = core or tuple(min(255, int(c_ * 0.4 + 255 * 0.6)) for c_ in color)
        d = ndimage.distance_transform_edt(m > 0.3)
        t = np.clip(d / (w * 0.35 + 1e-3), 0, 1)
        col = np.array(color, np.float32)[None, None] * (1 - t[..., None]) + np.array(core, np.float32)[None, None] * t[..., None]
        k = m * alpha
        self.col = self.col * (1 - k[..., None]) + col * k[..., None]
        self.a = np.maximum(self.a, k)

    def glow(self, mask, color, sigma=14, k=0.55):
        g = ndimage.gaussian_filter(mask.astype(np.float32), sigma) * k
        c = np.array(color, np.float32)
        self.col = np.where((g > self.a)[..., None], c[None, None], self.col)
        self.a = np.maximum(self.a, np.clip(g, 0, 1))


def swirls(au, rng, color, n, u0, u1, spread, w=(10, 18), local=True, curl=1.0):
    """무기 축을 따라 바깥으로 휘어 나가는 불꽃 · 바람 소용돌이"""
    for i in range(n):
        u = rng.uniform(u0, u1)
        side = 1 if i % 2 == 0 else -1
        L = rng.uniform(0.6, 1.0) * spread
        pts = [(u, side * 10), (u + L * 0.25, side * L * 0.55), (u + L * 0.05 * curl, side * L * 0.95),
               (u - L * 0.35 * curl, side * L * 0.8), (u - L * 0.3 * curl, side * L * 0.55)]
        au.wisp(pts, rng.uniform(*w), color)


# ─────────────────────────────────────────────── 마무리 (128px 픽셀 느낌)
def finish(c, au, out=128, outline_col=(16, 12, 18), sparkle=(255, 255, 230), n_sparkle=6, seed=1, colors=56):
    # 1) 무기 몸통 (512 → out)
    rgb = c.rgb.copy()
    g = ndimage.gaussian_filter(c.glow, (6, 6, 0))
    rgb = np.clip(rgb + g * 0.45 * (c.a[..., None] > 0), 0, 255)
    body = Image.fromarray(np.dstack([rgb, c.a * 255]).astype(np.uint8), "RGBA").resize((out, out), Image.LANCZOS)
    b = np.asarray(body).astype(np.float32)
    ba = b[..., 3] / 255
    solid = ba > 0.45
    # 2) 오라 (512 → out, 부드럽게)
    auim = Image.fromarray(np.dstack([np.clip(au.col, 0, 255), np.clip(au.a * 255, 0, 255)]).astype(np.uint8), "RGBA").resize((out, out), Image.LANCZOS)
    A_ = np.asarray(auim).astype(np.float32)
    # 3) 몸통 색 줄이기 (픽셀 그림 느낌)
    brgb = b[..., :3] / np.maximum(ba[..., None], 1e-3)
    brgb = np.clip(brgb, 0, 255)
    q = Image.fromarray(brgb.astype(np.uint8), "RGB").quantize(colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    brgb = np.asarray(q).astype(np.float32)
    # 4) 합치기: 오라 → 테두리 → 몸통
    res = np.zeros((out, out, 4), np.float32)
    res[..., :3] = A_[..., :3]
    res[..., 3] = A_[..., 3]
    ol = ndimage.binary_dilation(solid, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])) & ~solid
    res[ol, :3] = outline_col
    res[ol, 3] = 255
    res[solid, :3] = brgb[solid]
    res[solid, 3] = 255
    # 5) 반짝이 (4갈래 별)
    r = np.random.default_rng(seed)
    free = (res[..., 3] < 60)
    ys, xs = np.nonzero(free[4:-4, 4:-4])
    for _ in range(n_sparkle if len(ys) else 0):
        k = r.integers(len(ys))
        y, x = ys[k] + 4, xs[k] + 4
        near = res[max(0, y - 10):y + 10, max(0, x - 10):x + 10, 3].max() > 100
        if not near:
            continue
        big = r.random() < 0.4
        pts = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)] + ([(2, 0), (-2, 0), (0, 2), (0, -2)] if big else [])
        for dx, dy in pts:
            yy, xx = y + dy, x + dx
            f = 1.0 if (dx, dy) == (0, 0) else 0.75
            res[yy, xx, :3] = np.array(sparkle) * f + res[yy, xx, :3] * (1 - f)
            res[yy, xx, 3] = max(res[yy, xx, 3], 255 * f)
    return Image.fromarray(np.clip(res, 0, 255).astype(np.uint8), "RGBA")


# ─────────────────────────────────────────────── 무기들
def frost():
    """서리 여왕의 장궁 — 얼음 결정 활대 + 은 손잡이 + 눈꽃 보석 + 끝의 얼음 가시"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(11)
    bend = lambda u: -58 * math.sin(math.pi * (u - 40) / 460)
    limb = [(u, bend(u)) for u in range(40, 501, 20)]
    # 시위
    c.part(stroke([(40, bend(40) + 2), (500, bend(500) + 2)], 2.6), SILVER, 1, bevel=1, outline=0.6)
    # 활대 (가운데 굵고 끝 가늘게) — 두 겹
    up, lo = limb[:12], limb[11:]
    c.part(stroke(up[::-1], 22, 8), ICE_D, 2, bevel=6)
    c.part(stroke(lo, 22, 8), ICE_D, 3, bevel=6)
    c.part(stroke([(u, v - 3) for u, v in up[::-1]], 12, 4), ICE_B, 4, bevel=5)
    c.part(stroke([(u, v - 3) for u, v in lo], 12, 4), ICE_B, 5, bevel=5)
    # 활대 가시 (바깥쪽)
    for u in (110, 170, 350, 410):
        v = bend(u)
        c.part(poly([(u - 9, v - 6), (u + 9, v - 6), (u + 16, v - 30)]), ICE_B, 10 + u, shape="blade", height=0.9)
    # 끝 장식: 얼음 결정 촉
    for u, s_ in ((40, -1), (500, 1)):
        v = bend(u)
        c.part(poly([(u - 14 * s_, v - 10), (u + 30 * s_, v - 4), (u - 14 * s_, v + 6)]), ICE_B, 30 + u, shape="blade", height=1.0)
        c.part(disc(u, v, 7), GOLD2, 40 + u, bevel=4)
    # 손잡이 (은 + 금 감싸개) + 날개 모양 금장식
    mid = 270
    vm = bend(mid)
    c.part(stroke([(mid - 36, vm), (mid + 36, vm)], 26, 26), SILVER, 50, bevel=8)
    for du in (-30, -10, 10, 30):
        c.part(stroke([(mid + du - 3, vm - 13), (mid + du + 3, vm + 13)], 5), GOLD2, 60 + du, bevel=3)
    for s_ in (1, -1):
        filigree(c, mid + s_ * 38, vm - 12, 1.3, side=-1, seed=70 + s_)
        filigree(c, mid + s_ * 30, vm + 12, 1.0, side=1, seed=80 + s_)
    # 눈꽃 보석
    c.part(disc(mid, vm, 13), GOLD2, 90, bevel=6)
    c.part(disc(mid, vm, 9), gem((120, 200, 255)), 91, bevel=6)
    c.emissive(line_dens([(40, bend(40)), (270, vm - 4), (500, bend(500))], 1.6), (190, 235, 255), 0.8)
    # 오라: 얼음 바람
    swirls(au, r, (90, 170, 255), 7, 60, 480, 70, (9, 16))
    for u in (140, 400):
        au.wisp([(u, -40), (u + 30, -80), (u + 70, -90), (u + 90, -70)], 8, (150, 210, 255))
    au.glow(c.sil, (120, 190, 255), 10, 0.5)
    return c, au, dict(outline_col=(10, 20, 50), sparkle=(230, 250, 255))


def storm():
    """폭풍의 삼지창 — 남색 창대 + 금 고리 + 번개 무늬 세 갈래 날"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(12)
    c.part(profile([(10, 7), (400, 9)]), NAVY, 1, bevel=6, ang=AX_ANG)
    for u in (70, 170, 270, 370):
        c.part(profile([(u - 6, 12), (u + 6, 12)]), GOLD2, 2 + u, bevel=4)
    c.part(disc(12, 0, 11), GOLD2, 3, bevel=6)
    c.part(disc(12, 0, 6), SAPPHIRE, 4, bevel=4)
    # 가로대 (파도 모양)
    c.part(smooth_poly([(392, -40), (410, -46), (420, 0), (410, 46), (392, 40), (402, 0)], 8), GOLD2, 5, bevel=6)
    c.part(disc(410, 0, 12), GOLD2, 6, bevel=6)
    c.part(disc(410, 0, 8), SAPPHIRE, 7, bevel=5)
    # 세 갈래
    c.part(profile([(418, 11), (470, 12), (520, 7), (552, 0.5)]), STORM, 10, shape="blade", height=1.1, ang=AX_ANG)
    for s_ in (1, -1):
        prong = smooth_poly([(400, s_ * 30), (430, s_ * 50), (480, s_ * 52), (520, s_ * 40), (490, s_ * 38), (450, s_ * 34), (420, s_ * 24)], 8)
        c.part(prong, STORM, 20 + s_, shape="blade", height=0.9)
        c.part(poly([(470, s_ * 50), (500, s_ * 62), (484, s_ * 44)]), STORM, 30 + s_, shape="blade", height=0.8)
    # 번개 무늬
    for pts in ([(424, 0), (450, 4), (470, -4), (500, 3), (530, 0)], [(420, 26), (445, 34), (470, 40), (500, 42)], [(420, -26), (445, -34), (470, -40), (500, -42)]):
        c.emissive(line_dens(pts, 2.0), (255, 240, 120), 1.2)
    # 오라: 번개 가닥 + 푸른 폭풍
    swirls(au, r, (60, 120, 255), 6, 120, 440, 60, (8, 14))
    for k in range(6):
        u0 = r.uniform(380, 540); v0 = r.uniform(-60, 60)
        pts = [(u0, v0)]
        for j in range(5):
            pts.append((pts[-1][0] + r.uniform(-18, 18), pts[-1][1] + r.uniform(8, 16) * (1 if v0 > 0 else -1)))
        au.wisp(pts, 4, (255, 230, 90), (255, 255, 220), 1.0)
    au.glow(c.sil, (90, 140, 255), 10, 0.5)
    return c, au, dict(outline_col=(8, 12, 40), sparkle=(255, 250, 190))


def scythe():
    """망자의 낫 — 검은 뼈 창대 + 해골 이음새 + 크게 휘어진 유령빛 낫날"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(13)
    c.part(profile([(10, 7), (440, 9)]), DARKM, 1, bevel=6, ang=AX_ANG)
    for u in range(40, 420, 34):
        c.part(profile([(u, 11), (u + 7, 11)]), BONE2, 2 + u, bevel=3)
    c.part(poly([(0, 0), (20, -12), (34, 0), (20, 12)]), BONE2, 3, shape="blade")
    # 낫날 (축 위쪽에서 크게 휘어 아래로)
    blade = smooth_poly([(430, 6), (470, -30), (480, -100), (450, -170), (400, -205), (420, -160), (436, -100), (426, -44), (410, -8)], 10)
    c.part(blade, GHOST, 10, shape="blade", height=0.8)
    edge = curve([(468, -34), (474, -100), (446, -165), (404, -200)], 12)
    c.emissive(line_dens(edge, 3.0), (120, 255, 200), 1.3)
    c.part(smooth_poly([(420, 10), (455, -24), (446, -30), (414, 0)], 6), DARKM, 11, bevel=4)
    # 뒤쪽 가시
    c.part(poly([(430, 8), (470, 30), (440, 16)]), DARKM, 12, shape="blade")
    # 해골
    c.part(smooth_poly([(412, -18), (440, -22), (452, 0), (440, 22), (412, 18), (404, 0)], 8), BONE2, 20, bevel=8)
    for s_ in (1, -1):
        c.part(disc(436, s_ * 8, 5), DARKM, 21 + s_, bevel=2, outline=0)
        c.emissive(disc(437, s_ * 8, 2.4).astype(np.float32), (120, 255, 190), 1.0)
    # 오라: 영혼 불꽃
    swirls(au, r, (40, 200, 160), 8, 60, 440, 64, (9, 16))
    for k in range(4):
        u = r.uniform(420, 480)
        au.wisp([(u, -120 - k * 20), (u + 30, -150 - k * 20), (u + 20, -190), (u - 10, -200)], 8, (90, 240, 190))
    au.glow(c.sil, (60, 220, 170), 10, 0.45)
    return c, au, dict(outline_col=(6, 20, 18), sparkle=(210, 255, 235))


def lance():
    """성광의 기병창 — 흰 진주빛 원뿔 창 + 금 나선 + 손 가리개(원뿔) + 빛살"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(14)
    c.part(profile([(10, 8), (130, 9)]), CRIM, 1, bevel=6, ang=AX_ANG)
    for u in range(20, 130, 16):
        c.part(stroke([(u, -9), (u + 8, 9)], 4), GOLD2, 2 + u, bevel=2)
    c.part(disc(10, 0, 10), GOLD2, 3, bevel=6)
    # 손 가리개 (원뿔 방패)
    c.part(profile([(130, 16), (150, 48), (160, 52), (166, 30)]), GOLD2, 4, bevel=8)
    c.part(profile([(136, 14), (150, 40), (158, 44), (162, 26)]), PEARL, 5, bevel=6)
    c.part(disc(152, 0, 9), RUBY, 6, bevel=5)
    # 창 몸통 (긴 원뿔)
    c.part(profile([(160, 24), (300, 17), (440, 9), (540, 1)]), PEARL, 10, shape="round", bevel=14, ang=AX_ANG)
    # 금 나선
    for k in range(9):
        u = 180 + k * 38
        w_ = 24 - (u - 160) / 380 * 22
        c.part(stroke([(u, -w_), (u + 18, w_)], max(2.5, 6 - k * 0.4)), GOLD2, 20 + k, bevel=2)
    c.emissive(line_dens([(170, -6), (520, -1)], 1.6), (255, 250, 210), 0.9)
    # 오라: 성스러운 빛살 + 날개 깃
    for k in range(9):
        a = -80 + k * 20
        au.wisp([(300, 0), (300 + 120 * math.cos(math.radians(a)), 120 * math.sin(math.radians(a)))], 10, (255, 220, 110), alpha=0.35)
    for s_ in (1, -1):
        for k in range(4):
            au.wisp([(150 + k * 10, s_ * 40), (180 + k * 22, s_ * (70 + k * 10)), (230 + k * 26, s_ * (80 + k * 6))], 12 - k, (255, 236, 160), (255, 255, 240), 0.9)
    au.glow(c.sil, (255, 220, 120), 12, 0.55)
    return c, au, dict(outline_col=(40, 26, 6), sparkle=(255, 255, 220), n_sparkle=10)


def skull():
    """저주받은 해골 지팡이 — 뒤틀린 검은 나무 + 해골 머리 + 초록 눈빛 + 독 방울"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(15)
    shaft = curve([(10, 0), (120, 6), (240, -6), (360, 6), (430, 0)], 12)
    c.part(stroke(shaft, 15, 17), TWIST, 1, bevel=7)
    for u in (90, 200, 310):
        c.part(profile([(u - 6, 13), (u + 6, 13)]), DGOLD, 2 + u, bevel=4)
    # 뿔 가지 (해골을 감싼다)
    for s_ in (1, -1):
        c.part(stroke(curve([(420, s_ * 8), (446, s_ * 44), (490, s_ * 58), (530, s_ * 44)], 10), 11, 3), TWIST, 10 + s_, bevel=5)
    # 해골
    sk = smooth_poly([(450, -30), (500, -34), (526, -10), (526, 12), (500, 32), (450, 30), (440, 0)], 8)
    c.part(sk, BONE2, 20, bevel=12)
    c.part(smooth_poly([(446, -18), (430, -16), (426, 0), (430, 16), (446, 18)], 6), BONE2, 21, bevel=6)
    for s_ in (1, -1):
        c.part(disc(492, s_ * 14, 8), DARKM, 22 + s_, bevel=2, outline=0)
        c.emissive(disc(493, s_ * 14, 4).astype(np.float32), (120, 255, 80), 1.4)
    for k in range(4):
        c.ink(line_dens([(438, -9 + k * 6), (452, -9 + k * 6)], 1.5), (40, 30, 20), 0.7)
    c.ink(line_dens([(470, -2), (478, 0), (470, 3)], 1.8), (40, 30, 20), 0.9)
    # 독 방울
    for u, v in ((470, 40), (440, 46), (400, 34)):
        c.part(disc(u, v, 5), TOXIC, 30 + u, bevel=4)
    # 오라: 독 연기
    swirls(au, r, (80, 200, 40), 9, 380, 540, 70, (10, 18))
    swirls(au, r, (120, 60, 160), 4, 150, 380, 44, (7, 12))
    au.glow(c.sil, (100, 220, 60), 10, 0.45)
    return c, au, dict(outline_col=(10, 20, 6), sparkle=(210, 255, 170))


def chakram():
    """태양의 원반 — 날 선 금 고리 + 해 모양 가시 + 가운데 손잡이 막대 + 불꽃"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(16)
    cx, cy = 256, 256
    # 가시 (해살 12개)
    for k in range(12):
        a = math.radians(k * 30 + 15)
        pts = [(cx + math.cos(a - 0.12) * 150, cy + math.sin(a - 0.12) * 150), (cx + math.cos(a) * (212 if k % 2 == 0 else 190), cy + math.sin(a) * (212 if k % 2 == 0 else 190)),
               (cx + math.cos(a + 0.2) * 150, cy + math.sin(a + 0.2) * 150)]
        c.part(poly(pts, local=False), SUN, 10 + k, shape="blade", height=0.9)
    c.part(ring_mask(cx, cy, 104, 160), GOLD2, 1, bevel=14)
    c.part(ring_mask(cx, cy, 138, 158), SILVER, 2, shape="blade", height=0.7)
    c.part(ring_mask(cx, cy, 112, 124), DGOLD, 3, bevel=4)
    for k in range(8):
        a = math.radians(k * 45)
        c.part(cdisc(cx + math.cos(a) * 118, cy + math.sin(a) * 118, 10), RUBY if k % 2 else TOPAZ, 30 + k, bevel=5)
    # 가운데 손잡이
    c.part(poly([(cx - 104, cy - 14), (cx + 104, cy - 14), (cx + 104, cy + 14), (cx - 104, cy + 14)], local=False), CRIM, 40, bevel=8)
    for dx in (-60, -20, 20, 60):
        c.part(poly([(cx + dx - 5, cy - 16), (cx + dx + 5, cy - 16), (cx + dx + 5, cy + 16), (cx + dx - 5, cy + 16)], local=False), GOLD2, 41 + dx, bevel=3)
    c.part(cdisc(cx, cy, 24), GOLD2, 50, bevel=8)
    c.part(cdisc(cx, cy, 15), SUN, 51, bevel=6)
    c.emissive(ring_mask(cx, cy, 148, 152).astype(np.float32), (255, 230, 150), 0.8)
    # 오라: 도는 불꽃
    for k in range(10):
        a0 = math.radians(k * 36 + r.uniform(-8, 8))
        pts = [(cx + math.cos(a0 + t * 0.12) * (180 + t * 12), cy + math.sin(a0 + t * 0.12) * (180 + t * 12)) for t in range(6)]
        au.wisp(pts, r.uniform(12, 20), (255, 110, 30), (255, 230, 120), 0.9, local=False)
    au.glow(c.sil, (255, 150, 40), 14, 0.6)
    return c, au, dict(outline_col=(40, 16, 4), sparkle=(255, 250, 200))


def chain():
    """사냥꾼의 사슬낫 — 붉은 끈 손잡이 + 휘어진 낫날 + 휘감긴 사슬 + 추"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(17)
    # 사슬 (손잡이 끝에서 크게 휘어 추로)
    path = curve([(200, 4), (140, 60), (60, 90), (10, 50), (30, -20), (90, -60)], 14)
    for i in range(0, len(path) - 1, 2):
        x0, y0 = P(*path[i]); x1, y1 = P(*path[min(i + 2, len(path) - 1)])
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        m = np.hypot(XX - mx, YY - my)
        link = (m <= 10) & (m >= 5) if (i // 2) % 2 == 0 else (np.abs((XX - mx) * (y1 - y0) - (YY - my) * (x1 - x0)) / (np.hypot(x1 - x0, y1 - y0) + 1e-3) <= 3.5) & (m <= 11)
        c.part(link, IRON, 100 + i, bevel=3)
    # 추 (가시 달린 쇳덩이)
    wx, wy = P(90, -60)
    c.part(cdisc(wx, wy, 20), DARKM, 5, bevel=10)
    for k in range(6):
        a = math.radians(k * 60)
        c.part(poly([(wx + math.cos(a - 0.3) * 18, wy + math.sin(a - 0.3) * 18), (wx + math.cos(a) * 32, wy + math.sin(a) * 32), (wx + math.cos(a + 0.3) * 18, wy + math.sin(a + 0.3) * 18)], local=False), IRON, 6 + k, shape="blade")
    # 손잡이
    c.part(profile([(200, 10), (380, 11)]), CRIM, 20, bevel=6, ang=AX_ANG)
    for u in range(210, 380, 18):
        c.part(stroke([(u, -11), (u + 9, 11)], 3.5), (DGOLD), 21 + u, bevel=2)
    c.part(disc(200, 0, 13), GOLD2, 22, bevel=6)
    c.part(profile([(378, 16), (396, 16)]), GOLD2, 23, bevel=5)
    # 낫날
    blade = smooth_poly([(392, 10), (430, 30), (500, 30), (550, -10), (520, 4), (470, 8), (420, 0)], 10)
    c.part(blade, SILVER, 30, shape="blade", height=0.9)
    c.emissive(line_dens(curve([(430, 26), (500, 26), (546, -8)], 10), 2.0), (255, 120, 110), 1.0)
    c.part(poly([(396, -10), (410, -36), (420, -8)]), SILVER, 31, shape="blade")
    # 오라: 붉은 사냥 기운
    swirls(au, r, (220, 40, 40), 6, 220, 520, 56, (8, 14))
    au.wisp(curve([(40, 110), (0, 70), (0, 0)], 6), 10, (200, 30, 30))
    au.glow(c.sil, (200, 40, 40), 10, 0.4)
    return c, au, dict(outline_col=(24, 6, 6), sparkle=(255, 220, 210))


def gauntlet():
    """거인의 건틀렛 — 청동 · 돌 판갑 주먹 + 마디 가시 + 빛나는 용암 룬"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(18)
    # 손목 (아래 왼쪽) → 주먹 (위 오른쪽)
    c.part(smooth_poly([(90, 330), (160, 260), (230, 330), (170, 410), (120, 430)], 8, local=False), STONE2, 1, bevel=14)
    for k in range(3):
        c.part(stroke([(110 + k * 22, 360 - k * 22), (170 + k * 22, 420 - k * 22)], 12, 12, local=False), BRONZE2, 2 + k, bevel=5)
    # 손등 판
    c.part(smooth_poly([(170, 250), (260, 170), (340, 230), (320, 330), (240, 340)], 8, local=False), STONE2, 10, bevel=18)
    c.part(smooth_poly([(200, 250), (264, 196), (318, 238), (300, 306), (244, 314)], 8, local=False), BRONZE2, 11, bevel=12)
    # 손가락 마디 4개
    for k in range(4):
        x, y = 280 + k * 22, 150 + k * 26
        c.part(smooth_poly([(x - 30, y + 10), (x + 10, y - 30), (x + 40, y - 6), (x + 6, y + 34)], 6, local=False), STONE2, 20 + k, bevel=12)
        c.part(poly([(x - 2, y - 8), (x + 30, y - 40), (x + 16, y + 4)], local=False), IRON, 30 + k, shape="blade", height=1.0)
    # 엄지
    c.part(smooth_poly([(330, 300), (380, 300), (400, 340), (360, 360), (320, 340)], 6, local=False), STONE2, 40, bevel=10)
    # 용암 룬
    for pts in ([(225, 262), (262, 230), (298, 262)], [(262, 230), (262, 300)], [(240, 290), (284, 290)]):
        c.emissive(line_dens(pts, 3.0, local=False), (255, 140, 40), 1.3)
    c.part(cdisc(262, 262, 12), LAVA, 50, bevel=6)
    # 오라: 먼지 · 불씨
    for k in range(9):
        a = math.radians(r.uniform(180, 360))
        x0, y0 = 260 + math.cos(a) * 120, 240 + math.sin(a) * 120
        au.wisp([(x0, y0), (x0 + math.cos(a) * 50, y0 + math.sin(a) * 50 - 20), (x0 + math.cos(a) * 80 + 20, y0 + math.sin(a) * 70 - 40)], r.uniform(10, 18), (255, 120, 30), local=False)
    au.glow(c.sil, (255, 140, 50), 12, 0.5)
    return c, au, dict(outline_col=(30, 14, 6), sparkle=(255, 230, 170))


def b_talos():
    """탈로스의 청동 대검 — 넓은 청동 날 + 용광로 심지 + 톱니 가드 + 증기"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(19)
    c.part(profile([(8, 9), (120, 11)]), M((60, 40, 30), spec=0.2, shin=10, grain="leather", rough=0.25), 1, bevel=6, ang=AX_ANG)
    for u in range(16, 120, 14):
        c.part(profile([(u, 13), (u + 5, 13)]), BRONZE2, 2 + u, bevel=3)
    c.part(disc(8, 0, 13), BRONZE2, 3, bevel=7)
    c.part(disc(8, 0, 7), LAVA, 4, bevel=4)
    # 톱니 가드
    gx, gy = P(135, 0)
    c.part(cdisc(gx, gy, 34), BRONZE2, 5, bevel=10)
    for k in range(10):
        a = math.radians(k * 36)
        c.part(cdisc(gx + math.cos(a) * 34, gy + math.sin(a) * 34, 8), BRONZE2, 6 + k, bevel=4)
    c.part(cdisc(gx, gy, 16), DGOLD, 20, bevel=6)
    c.part(cdisc(gx, gy, 9), LAVA, 21, bevel=5)
    # 날 (넓고 두꺼운)
    blade = profile([(150, 30), (200, 36), (420, 32), (500, 22), (548, 0.5)])
    c.part(blade, BRONZE2, 30, shape="blade", height=0.9, ang=AX_ANG)
    c.part(profile([(170, 10), (480, 7), (520, 1)]), M((90, 50, 24), spec=0.6, shin=30, env=0.3), 31, bevel=4)
    c.emissive(line_dens([(180, 0), (500, 0)], 3.4), (255, 150, 40), 1.4)
    for u in (230, 300, 370, 440):
        c.part(disc(u, 22, 4), DGOLD, 40 + u, bevel=2)
        c.part(disc(u, -22, 4), DGOLD, 41 + u, bevel=2)
    # 오라: 증기 + 불씨
    swirls(au, r, (255, 130, 40), 6, 180, 500, 60, (8, 14))
    for k in range(5):
        u = r.uniform(200, 480)
        au.wisp([(u, 40), (u - 20, 70), (u + 10, 100), (u - 10, 130)], 14, (200, 190, 180), (240, 236, 230), 0.55)
    au.glow(c.sil, (255, 140, 50), 12, 0.55)
    return c, au, dict(outline_col=(34, 16, 4), sparkle=(255, 220, 150))


def b_sphinx():
    """스핑크스의 모래시계 — 금 틀 + 청금석 기둥 + 흐르는 모래 + 지혜의 눈"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(20)
    cx = 256
    # 위 · 아래 뚜껑
    for y0 in (70, 402):
        c.part(smooth_poly([(cx - 120, y0), (cx + 120, y0), (cx + 110, y0 + 40), (cx - 110, y0 + 40)], 4, local=False), GOLD2, y0, bevel=10)
        c.part(poly([(cx - 90, y0 + 12), (cx + 90, y0 + 12), (cx + 90, y0 + 28), (cx - 90, y0 + 28)], local=False), LAPIS, y0 + 1, bevel=4)
    # 유리
    top = smooth_poly([(cx - 88, 112), (cx + 88, 112), (cx + 70, 200), (cx + 10, 250), (cx - 10, 250), (cx - 70, 200)], 8, local=False)
    bot = smooth_poly([(cx - 10, 262), (cx + 10, 262), (cx + 70, 312), (cx + 88, 400), (cx - 88, 400), (cx - 70, 312)], 8, local=False)
    glass = Mat((200, 220, 230), spec=1.0, shin=80, env=0.6, rough=0.01, sky=(255, 255, 255), ground=(90, 110, 130))
    c.part(top | bot, glass, 1, bevel=10, alpha=0.8)
    # 모래 (위 조금 · 아래 더미 · 흐름)
    c.part(top & (YY > 190), SAND, 2, bevel=4)
    c.part(bot & (YY > 340) & (np.abs(XX - cx) < (YY - 330) * 1.5 + 10), SAND, 3, bevel=6)
    c.emissive(line_dens([(cx, 250), (cx, 350)], 3.0, local=False), (255, 220, 130), 1.0)
    # 기둥 (청금석 + 금)
    for dx in (-112, 112):
        c.part(poly([(cx + dx - 10, 106), (cx + dx + 10, 106), (cx + dx + 10, 406), (cx + dx - 10, 406)], local=False), LAPIS, 10 + dx, bevel=5)
        for y in (150, 256, 360):
            c.part(poly([(cx + dx - 13, y - 6), (cx + dx + 13, y - 6), (cx + dx + 13, y + 6), (cx + dx - 13, y + 6)], local=False), GOLD2, 20 + dx + y, bevel=3)
    # 지혜의 눈 (위 뚜껑 위)
    c.part(smooth_poly([(cx - 60, 50), (cx, 20), (cx + 60, 50), (cx, 76)], 6, local=False), GOLD2, 40, bevel=8)
    c.part(smooth_poly([(cx - 40, 50), (cx, 34), (cx + 40, 50), (cx, 64)], 6, local=False), EYEW, 41, bevel=5)
    c.part(cdisc(cx, 50, 10), LAPIS, 42, bevel=5)
    # 날개
    for s_ in (1, -1):
        for k in range(4):
            y = 110 + k * 26
            c.part(smooth_poly([(cx + s_ * 124, y), (cx + s_ * (170 + k * 12), y - 14), (cx + s_ * (200 + k * 8), y + 4), (cx + s_ * 130, y + 20)], 6, local=False), GOLD2, 50 + k * 2 + s_, bevel=5)
    # 오라: 모래 폭풍
    for k in range(9):
        a0 = math.radians(k * 40 + r.uniform(-10, 10))
        pts = [(cx + math.cos(a0 + t * 0.2) * (150 + t * 14), 256 + math.sin(a0 + t * 0.2) * (170 + t * 10)) for t in range(6)]
        au.wisp(pts, r.uniform(10, 16), (230, 180, 80), (255, 240, 190), 0.85, local=False)
    au.glow(c.sil, (240, 190, 90), 12, 0.5)
    return c, au, dict(outline_col=(40, 26, 6), sparkle=(255, 250, 210), n_sparkle=9)


def b_ladon():
    """히드라의 삼두 채찍 — 금 · 초록 비늘 손잡이 + 세 갈래 뱀 채찍"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(21)
    c.part(profile([(10, 10), (150, 12)]), SCALE_D, 1, bevel=7, ang=AX_ANG)
    for u in range(20, 150, 12):
        c.part(stroke([(u, -12), (u + 6, 0), (u, 12)], 3), SCALE_G, 2 + u, bevel=2)
    c.part(disc(10, 0, 13), GOLD2, 3, bevel=6)
    c.part(disc(10, 0, 7), EMERALD, 4, bevel=4)
    c.part(profile([(148, 22), (170, 22)]), GOLD2, 5, bevel=6)
    for s_ in (1, -1):
        filigree(c, 160, s_ * 20, 1.4, side=s_, seed=6 + s_)
    # 세 갈래 (S자로 휘는 뱀 몸 + 머리)
    tails = [[(170, 0), (260, 30), (340, -20), (430, 10), (500, 0)],
             [(170, 6), (230, 70), (300, 110), (370, 90), (420, 130)],
             [(170, -6), (240, -60), (330, -70), (380, -130), (450, -150)]]
    for i, tp in enumerate(tails):
        pts = curve(tp, 14)
        c.part(stroke(pts, 18, 11), SCALE_G, 10 + i, bevel=6)
        for j in range(4, len(pts) - 2, 4):
            c.ink(line_dens([pts[j - 1], pts[j]], 2.0), (20, 60, 20), 0.6)
        # 머리
        hu, hv = pts[-1]
        pu, pv = pts[-4]
        du, dv = hu - pu, hv - pv
        L = math.hypot(du, dv) or 1
        du, dv = du / L, dv / L
        nu, nv = -dv, du
        head = [(hu - du * 6 + nu * 14, hv - dv * 6 + nv * 14), (hu + du * 30 + nu * 8, hv + dv * 30 + nv * 8), (hu + du * 40, hv + dv * 40),
                (hu + du * 30 - nu * 8, hv + dv * 30 - nv * 8), (hu - du * 6 - nu * 14, hv - dv * 6 - nv * 14)]
        c.part(smooth_poly(head, 6), SCALE_G, 20 + i, bevel=8)
        for s_ in (1, -1):
            c.part(poly([(hu - du * 2 + nu * s_ * 12, hv - dv * 2 + nv * s_ * 12), (hu - du * 20 + nu * s_ * 22, hv - dv * 20 + nv * s_ * 22), (hu + du * 6 + nu * s_ * 8, hv + dv * 6 + nv * s_ * 8)]), SCALE_D, 30 + i * 2 + s_, shape="blade")
            c.emissive(disc(hu + du * 16 + nu * s_ * 6, hv + dv * 16 + nv * s_ * 6, 3).astype(np.float32), (255, 220, 40), 1.0)
    # 오라: 독 기운
    swirls(au, r, (70, 200, 40), 8, 180, 480, 60, (9, 15))
    au.glow(c.sil, (90, 220, 60), 10, 0.45)
    return c, au, dict(outline_col=(6, 24, 6), sparkle=(220, 255, 170))


def b_cyclops():
    """외눈 거인의 곤봉 — 굵은 참나무 몸통 + 쇠띠 + 돌 가시 + 가운데 거인의 눈"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(22)
    c.part(profile([(8, 11), (120, 13)]), M((70, 44, 30), spec=0.2, shin=10, grain="leather", rough=0.25), 1, bevel=6, ang=AX_ANG)
    for u in range(16, 120, 16):
        c.part(stroke([(u, -13), (u + 8, 13)], 4), IRON, 2 + u, bevel=2)
    c.part(disc(6, 0, 14), IRON, 3, bevel=7)
    # 몸통 (점점 굵어짐, 울퉁불퉁)
    c.part(profile([(110, 16), (200, 30), (340, 50), (470, 56), (530, 44), (548, 20)]), OAK, 10, bevel=18, ang=AX_ANG,
           extra_h=np.sin(U * 0.09) * 3 + np.sin(V * 0.2 + U * 0.03) * 2)
    for u in (220, 400):
        w_ = np.interp(u, [110, 200, 340, 470, 530], [16, 30, 50, 56, 44]) + 3
        c.part(profile([(u - 9, w_), (u + 9, w_)]), IRON, 20 + u, bevel=5)
        for s_ in (1, -1):
            c.part(disc(u, s_ * (w_ - 5), 3), DARKM, 21 + u + s_, bevel=2)
    # 돌 가시
    for k, (u, s_) in enumerate(((270, 1), (300, -1), (350, 1), (450, -1), (480, 1), (520, -1), (430, 1))):
        w_ = np.interp(u, [110, 200, 340, 470, 530, 548], [16, 30, 50, 56, 44, 20])
        c.part(poly([(u - 10, s_ * (w_ - 4)), (u + 10, s_ * (w_ - 4)), (u + 4, s_ * (w_ + 24))]), STONE2, 30 + k, shape="blade", height=1.0)
    # 끝 가시
    c.part(poly([(530, -16), (548, 0), (530, 16), (570, 0)]), STONE2, 40, shape="blade")
    # 거인의 눈
    c.part(disc(420, 0, 30), IRON, 50, bevel=8)
    c.part(smooth_poly([(396, 0), (420, -22), (444, 0), (420, 22)], 8), EYEW, 51, bevel=6)
    c.part(disc(420, 0, 11), EYER, 52, bevel=6)
    c.part(disc(420, 0, 4), DARKM, 53, bevel=2, outline=0)
    # 오라: 대지 먼지 + 불씨
    swirls(au, r, (210, 120, 50), 7, 200, 540, 70, (10, 18))
    au.glow(c.sil, (230, 120, 50), 12, 0.45)
    return c, au, dict(outline_col=(26, 14, 6), sparkle=(255, 220, 170))


WEAPONS2 = {"frost": frost, "storm": storm, "scythe": scythe, "lance": lance, "skull": skull, "chakram": chakram, "chain": chain,
            "gauntlet": gauntlet, "b_talos": b_talos, "b_sphinx": b_sphinx, "b_ladon": b_ladon, "b_cyclops": b_cyclops}


def paint(wid, out=128):
    c, au, opt = WEAPONS2[wid]()
    return finish(c, au, out, seed=sum(map(ord, wid)), **opt)


def preview(path, scale=2):
    ims = [paint(w) for w in WEAPONS2]
    n = len(ims)
    cols = 6
    rows = (n + cols - 1) // cols
    cell = 128 * scale + 16
    W = Image.new("RGBA", (cols * cell + 16, rows * cell + 16), (58, 58, 62, 255))
    for i, im in enumerate(ims):
        x, y = 16 + (i % cols) * cell, 16 + (i // cols) * cell
        W.alpha_composite(im.resize((128 * scale, 128 * scale), Image.NEAREST), (x, y))
    W.convert("RGB").save(path)


if __name__ == "__main__":
    import sys
    preview(sys.argv[1] if len(sys.argv) > 1 else "weapons2.png")
