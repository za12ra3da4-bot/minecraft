"""일러스트 렌더러 — 곡선 윤곽 + 높이맵 조명으로 '그린 것 같은' 아이템 그림 (512 에서 그려 128 로)

도형 = (재질, 윤곽(0..1 좌표의 점들), 높이 모양, 무늬). 뒤에서 앞으로 겹친다.
조명: 왼쪽 위 키라이트 + 오른쪽 아래 림라이트 + 금속은 스튜디오 환경 반사 + 블린-퐁 하이라이트.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

R = 512
OUT = 128
LIGHT = np.array([-0.55, -0.62, 0.56])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
RIM = np.array([0.7, 0.55, 0.45])
RIM = RIM / np.linalg.norm(RIM)
VIEW = np.array([0, 0, 1.0])

rng = np.random.default_rng(3)


# ─────────────────────────────── 곡선 도우미 (좌표 0..1, y 아래로)
def bez(p0, p1, p2, p3=None, n=40):
    out = []
    for i in range(n + 1):
        t = i / n
        if p3 is None:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        else:
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]
        out.append((x, y))
    return out


def along(a, b, t, off=0.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    return (a[0] + dx * t + nx * off, a[1] + dy * t + ny * off)


def strip(a, b, prof, n=60):
    """a→b 축을 따라 반폭 prof(t) 인 매끈한 윤곽 (칼날 · 자루 · 활대)"""
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        w = prof(t)
        left.append(along(a, b, t, w))
        right.append(along(a, b, t, -w))
    return left + right[::-1]


def curve_strip(pts, prof):
    """곡선 pts 를 따라 반폭 prof(t)"""
    left, right = [], []
    n = len(pts)
    for i in range(n):
        p = pts[i]
        q = pts[min(n - 1, i + 1)] if i < n - 1 else pts[i]
        o = pts[max(0, i - 1)] if i > 0 else pts[i]
        dx, dy = q[0] - o[0], q[1] - o[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = prof(i / (n - 1))
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    return left + right[::-1]


def ellipse(c, rx, ry, n=64, rot=0.0):
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a) * rx, math.sin(a) * ry
        cr, sr = math.cos(rot), math.sin(rot)
        out.append((c[0] + x * cr - y * sr, c[1] + x * sr + y * cr))
    return out


# ─────────────────────────────── 재질
MAT = {
    #            albedo(어둠, 밝음)                    금속  광택  반사강도
    "steel": ((70, 78, 92), (206, 214, 226), 1.0, 60, 0.85),
    "dsteel": ((26, 26, 32), (96, 98, 112), 1.0, 50, 0.7),
    "silver": ((110, 118, 134), (236, 240, 248), 1.0, 80, 0.9),
    "bronze": ((92, 50, 18), (226, 156, 76), 1.0, 40, 0.7),
    "gold": ((120, 76, 8), (255, 214, 96), 1.0, 55, 0.8),
    "leather": ((38, 20, 10), (122, 74, 40), 0.0, 12, 0.08),
    "wood": ((52, 30, 14), (150, 98, 52), 0.0, 10, 0.06),
    "bone": ((150, 128, 94), (246, 236, 210), 0.0, 25, 0.15),
    "red": ((70, 8, 8), (206, 44, 34), 0.0, 14, 0.1),
    "purple": ((40, 12, 64), (170, 90, 220), 0.0, 20, 0.15),
    "green": ((16, 48, 20), (104, 176, 74), 0.0, 25, 0.2),
    "venom": ((30, 90, 10), (190, 255, 110), 0.0, 60, 0.4),
    "teal": ((12, 56, 60), (86, 192, 180), 0.0, 30, 0.25),
    "fur": ((96, 56, 16), (240, 190, 96), 0.0, 8, 0.05),
    "mane": ((70, 30, 8), (196, 116, 44), 0.0, 8, 0.05),
    "black": ((10, 10, 14), (70, 70, 84), 0.3, 35, 0.3),
    "skin": ((24, 70, 58), (130, 200, 170), 0.0, 20, 0.12),
    "string": ((150, 144, 128), (246, 242, 230), 0.0, 10, 0.05),
    "marble": ((168, 160, 146), (252, 250, 244), 0.0, 30, 0.2),
    "leaf": ((20, 64, 22), (110, 196, 90), 0.0, 20, 0.1),
    "gem_red": ((90, 0, 10), (255, 90, 90), 0.0, 120, 0.9),
    "gem_blue": ((10, 30, 110), (120, 190, 255), 0.0, 120, 0.9),
    "gem_purple": ((50, 0, 90), (220, 140, 255), 0.0, 120, 0.9),
    "gem_green": ((0, 70, 30), (140, 255, 170), 0.0, 120, 0.9),
    "gem_amber": ((120, 60, 0), (255, 220, 90), 0.0, 120, 0.9),
    "ember": None,   # 자체 발광
    "soulfire": None,
}


def studio(n):
    """금속 환경 반사: 위 하늘(밝음) · 지평선(어두운 띠) · 아래 따뜻한 바닥"""
    ry = -(n[..., 1] * 0.9 + n[..., 0] * 0.3)   # 반사가 위를 향할수록 +
    sky = np.clip((ry - 0.05) * 2.2, 0, 1)
    ground = np.clip((-ry - 0.25) * 1.6, 0, 1)
    band = np.exp(-((ry + 0.05) ** 2) / 0.012)
    v = 0.35 + sky * 0.65 - band * 0.35 + ground * 0.18
    return np.clip(v, 0, 1.1)


def albedo_tex(mat, h, w, direction, mask):
    """재질 무늬 (0..1 밝기 변조)"""
    ys, xs = np.mgrid[0:h, 0:w].astype(float) / R
    dx, dy = direction
    u = xs * dx + ys * dy          # 결 방향
    v = -xs * dy + ys * dx
    noise = rng.random((h, w))
    small = ndimage.gaussian_filter(noise, 1.2)
    mid = ndimage.gaussian_filter(noise, 5)
    big = ndimage.gaussian_filter(noise, 18)
    t = 0.5 + (big - 0.5) * 3.0 + (mid - 0.5) * 2.0
    if mat in ("steel", "dsteel", "silver"):
        brushed = ndimage.gaussian_filter1d(ndimage.gaussian_filter1d(noise, 0.6, axis=0), 12, axis=1)
        t = 0.62 + (brushed - 0.5) * 2.5 + (big - 0.5) * 1.5
    elif mat in ("bronze", "gold"):
        t = 0.6 + (mid - 0.5) * 2.2 + (big - 0.5) * 2.5
    elif mat == "leather":
        pebble = ndimage.gaussian_filter(noise, 1.6)
        t = 0.55 + (pebble - 0.5) * 3.5 + (big - 0.5) * 2
    elif mat == "wood":
        grain = np.sin(v * 180 + ndimage.gaussian_filter(noise, 8) * 14) * 0.5 + 0.5
        t = 0.35 + grain * 0.45 + (small - 0.5) * 1.2
    elif mat in ("fur", "mane"):
        strand = ndimage.gaussian_filter1d(ndimage.gaussian_filter1d(noise, 0.7, axis=1), 9, axis=0)
        t = 0.5 + (strand - 0.5) * 5
    elif mat in ("green", "teal", "skin"):
        cell = 0.018
        row = np.floor(v / (cell * 0.8))
        uu = ((u + (row % 2) * cell / 2) % cell) / cell
        vv = (v % (cell * 0.8)) / (cell * 0.8)
        d = np.hypot(uu - 0.5, (vv - 0.3) * 1.2)
        t = np.where(d < 0.5, 0.75 - d * 0.6, 0.25) + (big - 0.5)
    elif mat == "bone":
        t = 0.7 + (big - 0.5) * 2 + np.sin(u * 90) * 0.06
    elif mat == "marble":
        vein = np.abs(np.sin(u * 30 + v * 12 + ndimage.gaussian_filter(noise, 10) * 30))
        t = 0.85 - np.exp(-vein * 12) * 0.35
    return np.clip(t, 0, 1)


class Painting:
    def __init__(self):
        self.rgb = np.zeros((R, R, 3))
        self.a = np.zeros((R, R))
        self.h = np.full((R, R), -1.0)      # 앞 도형의 높이 (그림자 계산용)
        self.glow = np.zeros((R, R, 3))

    def mask(self, pts):
        im = Image.new("L", (R * 2, R * 2), 0)
        ImageDraw.Draw(im).polygon([(x * R * 2, y * R * 2) for x, y in pts], fill=255)
        return np.asarray(im.resize((R, R), Image.BOX), dtype=float) / 255.0

    def shape_mask(self, mat, cov, **kw):
        """다각형 대신 이미 그린 마스크(0..1, R x R)로 도형 하나"""
        self._cov = cov
        return self.shape(mat, None, **kw)

    def shape(self, mat, pts, profile="round", bevel=0.035, height=1.0, direction=(0.707, -0.707),
              grooves=None, engrave=None, tint=None, emissive=False, lift=0.0):
        """profile: round(둥근 볼륨) · blade(가운데 능선, 가장자리 연마) · flat(얇은 판, 가장자리만 둥글게)
        grooves: [(점들, 폭)] 파낸 홈 (칼날 홈 · 새김) / engrave: 마스크 함수 (x, y) → 0..1 파임"""
        cov = self.mask(pts) if pts is not None else self._cov
        m = cov > 0.02
        if not m.any():
            return
        inside = ndimage.distance_transform_edt(cov > 0.5) / R
        dmax = inside.max() or 1e-6
        if profile == "blade":
            # 2단 연마: 가운데 능선 + 가장자리 좁은 날 (날 선이 반짝인다)
            edge = 0.011
            hmap = np.clip(inside / dmax, 0, 1) * 0.62 + np.clip(inside / edge, 0, 1) * 0.38
        elif profile == "flat":
            hmap = np.clip(inside / bevel, 0, 1)
            hmap = np.sqrt(1 - (1 - hmap) ** 2) * 0.5
        else:
            b = min(bevel, dmax)
            hmap = np.clip(inside / b, 0, 1)
            hmap = np.sqrt(1 - (1 - hmap) ** 2)
            hmap = hmap * 0.7 + np.clip(inside / dmax, 0, 1) * 0.3
        hmap = hmap * height
        if grooves:
            for gp, gw in grooves:
                gm = self.mask(gp)
                gm = ndimage.gaussian_filter(gm, gw * R * 0.35)
                hmap = hmap - gm * 0.35 * height
        if engrave is not None:
            ys, xs = np.mgrid[0:R, 0:R] / R
            hmap = hmap - engrave(xs, ys) * 0.12 * height
        # 법선
        gy, gx = np.gradient(hmap)
        S = 11.0 * (R / 512)
        nrm = np.dstack([-gx * S, -gy * S, np.ones_like(hmap)])
        nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
        if MAT.get(mat) is None:                 # 발광
            core = np.clip(inside / (dmax * 0.9), 0, 1)
            if mat == "ember":
                c0, c1, c2 = np.array([180, 30, 0.]), np.array([255, 150, 20.]), np.array([255, 250, 200.])
            else:
                c0, c1, c2 = np.array([70, 20, 140.]), np.array([170, 90, 255.]), np.array([240, 220, 255.])
            col = np.where(core[..., None] < 0.5, c0 + (c1 - c0) * (core[..., None] * 2), c1 + (c2 - c1) * ((core[..., None] - 0.5) * 2))
            self.glow += np.dstack([m * c1[i] for i in range(3)]) * 0 + (cov[..., None] * c1)
        else:
            dark, light, metal, shin, refl = MAT[mat]
            dark, light = np.array(dark, float), np.array(light, float)
            if tint is not None:
                dark, light = dark * tint, np.clip(light * tint, 0, 255)
            tex = albedo_tex(mat, R, R, direction, m)
            diff = np.clip((nrm * LIGHT).sum(2), 0, 1)
            rim = np.clip((nrm * RIM).sum(2), 0, 1) ** 3
            hv = LIGHT + VIEW
            hv /= np.linalg.norm(hv)
            spec = np.clip((nrm * hv).sum(2), 0, 1) ** shin
            base = dark + (light - dark) * tex[..., None]
            if metal > 0.5:
                env = studio(nrm)
                lum = env * 0.75 + diff * 0.35
                col = dark + (light - dark) * np.clip(lum * (0.7 + tex * 0.5), 0, 1.2)[..., None]
            else:
                lum = 0.28 + diff * 0.8
                col = base * lum[..., None]
            col = col + spec[..., None] * 255 * refl + rim[..., None] * light * 0.35
            if mat.startswith("gem"):
                sparkle = (np.clip((nrm * hv).sum(2), 0, 1) ** 400)
                col = col + sparkle[..., None] * 255
            # 앞 도형 그림자: 이미 그려진 도형이 이 도형 위(아래쪽이 아닌)에 있으면 어둡게 — 여기선 뒤에서 앞으로 그리므로
            # 새 도형이 기존 도형 위에 드리우는 그림자를 기존 픽셀에 적용한다
        # 그림자: 새 도형이 아래 그림에 드리운다 (오른쪽 아래로 번짐)
        sh = ndimage.shift(ndimage.gaussian_filter(cov, R * 0.006), (R * 0.012, R * 0.012), order=1)
        sh = np.clip(sh - cov, 0, 1) * 0.55
        self.rgb *= (1 - sh[..., None] * (self.a[..., None] > 0))
        a = cov * (1 if not lift else 1)
        self.rgb = self.rgb * (1 - a[..., None]) + np.clip(col, 0, 255) * a[..., None]
        self.a = np.maximum(self.a, a)

    def finish(self, size=OUT, outline=True, glow=None):
        rgb = np.clip(self.rgb, 0, 255)
        img = np.dstack([rgb, self.a * 255]).astype(np.uint8)
        im = Image.fromarray(img, "RGBA")
        # 프리멀티플라이 축소 (가장자리 번짐 방지)
        pm = np.dstack([rgb * self.a[..., None], self.a * 255])
        pim = Image.fromarray(pm.astype(np.uint8), "RGBA").resize((size, size), Image.LANCZOS)
        p = np.asarray(pim, dtype=float)
        al = p[..., 3:4] / 255.0
        col = np.where(al > 0.01, p[..., :3] / np.maximum(al, 1e-3), 0)
        out = np.dstack([np.clip(col, 0, 255), p[..., 3]])
        if outline:
            A = out[..., 3] / 255.0
            ring = ndimage.maximum_filter(A, size=3) - A
            ring = np.clip(ring * 1.4, 0, 1) * 0.9
            dark = np.array([22, 14, 12.])
            tot = A + ring * (1 - A)
            c = (out[..., :3] * A[..., None] + dark * (ring * (1 - A))[..., None]) / np.maximum(tot, 1e-3)[..., None]
            out = np.dstack([c, tot * 255])
        im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
        im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=60, threshold=2))
        return im
