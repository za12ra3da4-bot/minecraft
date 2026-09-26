"""서양 판타지 2D 아이콘 렌더러 — 입체 명암 · 금속 광택 · 재질 질감

 부품 = 마스크 + 재질 + 높이 모양(둥근 베벨 / 날 능선 / 평면)
 → 높이 → 법선 → 빛(왼쪽 위) · 반사 · 스페큘러 · 주변 가림 → 외곽선
 512 에 그리고 256 으로 줄여 가장자리를 부드럽게
"""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

S = 512
YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
LIGHT = np.array((-0.55, -0.65, 0.52)); LIGHT /= np.linalg.norm(LIGHT)


def rng(seed):
    return np.random.default_rng(seed)


def noise(seed, sigma=3.0, shape=(S, S)):
    n = ndimage.gaussian_filter(rng(seed).random(shape).astype(np.float32), sigma)
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


def aniso(seed, ang, sx=0.7, sy=14):
    """방향성 결 (금속 헤어라인 · 나뭇결)"""
    n = rng(seed).random((S, S)).astype(np.float32)
    n = ndimage.rotate(ndimage.gaussian_filter(ndimage.rotate(n, ang, reshape=False, mode="wrap"), (sx, sy)), -ang, reshape=False, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


# ─────────────────────────────────────────────── 재질
class Mat:
    def __init__(self, base, spec=0.3, shin=20, env=0.0, grain=None, rough=0.1, glow=None, sky=(210, 220, 235), ground=(60, 50, 44)):
        self.base = np.array(base, np.float32)
        self.spec, self.shin, self.env, self.grain, self.rough = spec, shin, env, grain, rough
        self.glow = glow
        self.sky = np.array(sky, np.float32); self.ground = np.array(ground, np.float32)


STEEL = Mat((168, 176, 190), spec=0.9, shin=60, env=0.55, grain="brushed", rough=0.08)
DSTEEL = Mat((70, 72, 82), spec=0.8, shin=50, env=0.45, grain="brushed", rough=0.1, sky=(150, 160, 180), ground=(20, 20, 26))
GOLD = Mat((222, 170, 60), spec=0.9, shin=40, env=0.5, grain="brushed", rough=0.06, sky=(255, 236, 170), ground=(90, 50, 10))
BRONZE = Mat((176, 110, 52), spec=0.7, shin=30, env=0.4, grain="brushed", rough=0.1, sky=(240, 200, 150), ground=(60, 30, 10))
LEATHER = Mat((96, 56, 32), spec=0.15, shin=8, grain="leather", rough=0.25)
LEATHER_D = Mat((52, 32, 22), spec=0.12, shin=8, grain="leather", rough=0.25)
WOOD = Mat((118, 76, 42), spec=0.12, shin=10, grain="wood", rough=0.3)
WOOD_D = Mat((72, 44, 26), spec=0.12, shin=10, grain="wood", rough=0.3)
CLOTH_R = Mat((150, 24, 30), spec=0.08, shin=6, grain="cloth", rough=0.2)
CLOTH_B = Mat((30, 60, 150), spec=0.08, shin=6, grain="cloth", rough=0.2)
CLOTH_G = Mat((30, 110, 50), spec=0.08, shin=6, grain="cloth", rough=0.2)
CLOTH_Y = Mat((210, 160, 30), spec=0.08, shin=6, grain="cloth", rough=0.2)
STONE = Mat((140, 138, 132), spec=0.08, shin=6, grain="stone", rough=0.35)
BONE = Mat((226, 216, 190), spec=0.3, shin=16, grain="stone", rough=0.15)
FUR = Mat((210, 206, 196), spec=0.05, shin=4, grain="fur", rough=0.3)


def gem(color):
    return Mat(color, spec=1.0, shin=80, env=0.3, grain=None, rough=0.02, glow=tuple(min(255, int(c * 1.2)) for c in color),
               sky=tuple(min(255, int(c * 1.6 + 60)) for c in color), ground=tuple(int(c * 0.3) for c in color))


RUBY, SAPPHIRE, EMERALD, TOPAZ, AMETHYST = gem((200, 20, 40)), gem((30, 80, 220)), gem((20, 170, 90)), gem((240, 170, 30)), gem((150, 60, 220))


def texture(mat, seed, ang):
    """재질 결 → 알베도 배율 (0.7..1.3) 와 높이 요철"""
    one = np.ones((S, S), np.float32)
    if mat.grain == "brushed":
        g = aniso(seed, ang, 0.5, 18)
        return 0.9 + 0.2 * g, (g - 0.5) * 0.4
    if mat.grain == "wood":
        g = aniso(seed, ang, 1.2, 30)
        rings = np.sin(g * 40) * 0.5 + 0.5
        return 0.72 + 0.4 * rings * 0.7 + 0.15 * g, (rings - 0.5) * 0.8
    if mat.grain == "leather":
        n = noise(seed, 1.2) * 0.6 + noise(seed + 1, 4) * 0.4
        return 0.8 + 0.4 * n, (n - 0.5) * 1.2
    if mat.grain == "cloth":
        w = (np.sin(XX * 1.3) * np.sin(YY * 1.3)) * 0.5 + 0.5
        n = noise(seed, 6)
        return 0.82 + 0.18 * w + 0.15 * n, (w - 0.5) * 0.5
    if mat.grain == "stone":
        n = noise(seed, 2) * 0.5 + noise(seed + 1, 7) * 0.5
        return 0.75 + 0.5 * n, (n - 0.5) * 2.0
    if mat.grain == "fur":
        g = aniso(seed, ang, 0.6, 6)
        return 0.7 + 0.5 * g, (g - 0.5) * 1.5
    return one, np.zeros((S, S), np.float32)


# ─────────────────────────────────────────────── 부품
class Canvas:
    def __init__(self):
        self.rgb = np.zeros((S, S, 3), np.float32)
        self.a = np.zeros((S, S), np.float32)
        self.sil = np.zeros((S, S), bool)
        self.glow = np.zeros((S, S, 3), np.float32)

    def part(self, mask, mat, seed=1, shape="round", bevel=8.0, height=1.0, ang=0.0, ridge=None, ao=True, outline=1.6, extra_h=None):
        m = mask.astype(bool)
        if not m.any():
            return
        d = ndimage.distance_transform_edt(m).astype(np.float32)
        if shape == "round":
            t = np.clip(d / bevel, 0, 1)
            h = np.sqrt(1 - (1 - t) ** 2) * bevel * height
        elif shape == "blade":                      # 날: 가장자리 → 능선으로 곧게 오름
            h = d * height
        elif shape == "flat":
            t = np.clip(d / bevel, 0, 1)
            h = t * bevel * 0.4 * height
        else:
            h = d * 0
        if ridge is not None:
            h = h + ridge
        alb, bump = texture(mat, seed, ang)
        h = h + bump * mat.rough * 6
        if extra_h is not None:
            h = h + extra_h
        h = ndimage.gaussian_filter(h * m, 0.7)
        gy, gx = np.gradient(h)
        n = np.stack([-gx, -gy, np.ones_like(h) * 1.0], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        diff = np.clip((n * LIGHT).sum(-1), 0, 1)
        r = 2 * (n * LIGHT).sum(-1)[..., None] * n - LIGHT
        spec = np.clip(r[..., 2], 0, 1) ** mat.shin * mat.spec
        base = mat.base[None, None, :] * alb[..., None]
        col = base * (0.28 + 0.8 * diff[..., None])
        if mat.env > 0:
            up = np.clip(-n[..., 1] * 0.5 + 0.5, 0, 1)[..., None]
            env = mat.sky * up + mat.ground * (1 - up)
            col = col * (1 - mat.env) + env * mat.env * (0.55 + 0.45 * diff[..., None]) * alb[..., None]
        col = col + spec[..., None] * 255
        if ao:
            occ = ndimage.gaussian_filter(self.sil.astype(np.float32), 5) * (~m)
            col = col * (1 - 0.0 * occ[..., None])
            # 부품 가장자리 안쪽 어둡게 (접합부 음영)
            col = col * (0.72 + 0.28 * np.clip(d / 3.0, 0, 1))[..., None]
        if mat.glow is not None:
            self.glow += np.array(mat.glow, np.float32)[None, None, :] * m[..., None] * 0.6
        if shape == "blade":
            hone = (d > 0) & (d < 5)
            col[hone] = col[hone] * 0.6 + np.array((238, 244, 252), np.float32) * 0.4
        if mat.glow is not None and mat.shin >= 80:
            # 보석 반짝임 (왼쪽 위 작은 흰 점)
            ys, xs = np.nonzero(m)
            if len(ys):
                cy, cx = ys.mean(), xs.mean()
                rr_ = max(2.0, math.sqrt(m.sum() / math.pi))
                sp = np.hypot(XX - (cx - rr_ * 0.35), YY - (cy - rr_ * 0.35)) < rr_ * 0.22
                col[sp & m] = col[sp & m] * 0.2 + 255 * 0.8
        # 외곽선: 부품 경계 어둡게
        if outline > 0:
            ring = (d > 0) & (d <= outline)
            col[ring] = col[ring] * 0.35
        self.rgb[m] = col[m]
        self.a[m] = 1.0
        self.sil |= m

    def emissive(self, dens, color, glow=1.0, core=None):
        """빛나는 선 · 룬 (밑에 번짐 + 밝은 심)"""
        c = np.array(color, np.float32)
        self.glow += c[None, None, :] * ndimage.gaussian_filter(dens, 5)[..., None] * glow
        core_c = np.array(core if core else [min(255, v + 120) for v in color], np.float32)
        k = np.clip(dens, 0, 1)[..., None]
        self.rgb = self.rgb * (1 - k) + (c * 0.5 + core_c * 0.5) * k
        self.a = np.maximum(self.a, dens)
        self.sil |= dens > 0.5

    def image(self, out=256, glow_strength=1.0, outline=True):
        rgb = self.rgb.copy()
        a = self.a.copy()
        if outline:
            dil = ndimage.binary_dilation(self.sil, iterations=3)
            ol = dil & ~self.sil
            rgb[ol] = (18, 14, 16)
            a[ol] = 1.0
        g = ndimage.gaussian_filter(self.glow, (9, 9, 0)) * glow_strength
        ga = np.clip(g.max(-1) / 255, 0, 1)
        rgb = rgb + g * 0.5 * (a[..., None] > 0)
        out_rgb = np.where(a[..., None] > 0, rgb, g / np.maximum(ga[..., None], 1e-3))
        out_a = np.maximum(a, ga * 0.75)
        arr = np.dstack([np.clip(out_rgb, 0, 255), np.clip(out_a * 255, 0, 255)]).astype(np.uint8)
        return Image.fromarray(arr, "RGBA").resize((out, out), Image.LANCZOS)


# ─────────────────────────────────────────────── 모양 도우미 (대각선 무기 축: u = 손잡이→끝, v = 좌우)
A = np.array((70.0, 446.0)); B = np.array((446.0, 70.0))
D = (B - A) / np.linalg.norm(B - A)
N = np.array((-D[1], D[0])) * -1
U = (XX - A[0]) * D[0] + (YY - A[1]) * D[1]
V = (XX - A[0]) * N[0] + (YY - A[1]) * N[1]
AX_ANG = math.degrees(math.atan2(D[1], D[0]))


def P(u, v):
    return tuple(A + D * u + N * v)


def profile(pts):
    """(u, 반폭) 목록 → 좌우 대칭 마스크"""
    us = np.array([p[0] for p in pts]); ws = np.array([p[1] for p in pts])
    hw = np.interp(U, us, ws, left=-1, right=-1)
    return (U >= us[0]) & (U <= us[-1]) & (np.abs(V) <= hw)


def poly(pts, local=True):
    im = Image.new("L", (S, S), 0)
    ImageDraw.Draw(im).polygon([P(u, v) if local else (u, v) for u, v in pts], fill=255)
    return np.asarray(im) > 127


def disc(u, v, r, local=True):
    c = P(u, v) if local else (u, v)
    return np.hypot(XX - c[0], YY - c[1]) <= r


def smooth_poly(pts, n=24, local=True):
    """점들을 캣멀롬으로 둥글게 이은 닫힌 도형"""
    P_ = np.array(pts, float)
    out = []
    k = len(P_)
    for i in range(k):
        p0, p1, p2, p3 = P_[(i - 1) % k], P_[i], P_[(i + 1) % k], P_[(i + 2) % k]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return poly([tuple(p) for p in out], local)


def line_dens(pts, width, local=True, n=40):
    """굵기 있는 선 (발광 룬 · 새김)"""
    im = Image.new("L", (S * 2, S * 2), 0)
    d = ImageDraw.Draw(im)
    Q = [P(*p) if local else p for p in pts]
    d.line([(x * 2, y * 2) for x, y in Q], fill=255, width=int(width * 2), joint="curve")
    return np.asarray(im.resize((S, S), Image.LANCZOS)).astype(np.float32) / 255
