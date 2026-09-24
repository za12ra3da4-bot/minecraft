"""도트(픽셀아트) 엔진 — 32x32 원본 해상도에서 직접 찍는다

- 팔레트: Endesga 32 계열 램프 (그림자는 차갑게 · 하이라이트는 따뜻하게 색조 이동)
- 덩어리 음영: 모양의 거리장 → 법선 → 램프 단계 (디더링 잡음 없음)
- 외곽선: 그 재질의 가장 어두운 색 (선택적 외곽선)
- 이펙트 궤적: 꼬리 어둡고 머리 밝게, 가운데 밝게 / 발광: 1~2 픽셀 단계로 번짐 / 불티 · 반짝이
좌표는 0..32 (소수 허용), y 는 아래로.
"""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SS = 8
N = 32


def hx(h):
    h = h.lstrip("#")
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)], dtype=float)


# 램프: [외곽선, 어둠 … 밝음]
RAMPS = {
    "steel": ["181425", "262b44", "3a4466", "5a6988", "8b9bb4", "c0cbdc", "ffffff"],
    "dsteel": ["0d0b14", "181425", "262b44", "3a4466", "5a6988", "8b9bb4"],
    "silver": ["262b44", "3a4466", "5a6988", "8b9bb4", "c0cbdc", "e8f0ff", "ffffff"],
    "gold": ["3e2731", "733e39", "b86f50", "e4a672", "feae34", "fee761", "fff8d0"],
    "bronze": ["3e2731", "5c2e24", "733e39", "b86f50", "e4a672", "ead4aa"],
    "wood": ["2a1a1c", "3e2731", "5c3a2e", "733e39", "9e5b3e", "c28569"],
    "leather": ["1f1418", "3e2731", "5c3328", "733e39", "9e5b3e", "c28569"],
    "bone": ["3e2731", "733e39", "c28569", "e8b796", "ead4aa", "fff4e0"],
    "red": ["3e1a24", "68182a", "a22633", "e43b44", "f6757a", "fcb0a8"],
    "fire": ["5a1020", "a22633", "e43b44", "f77622", "feae34", "fee761", "ffffff"],
    "hell": ["2a0818", "68182a", "a22633", "e43b44", "f77622", "feae34", "fee761"],
    "green": ["0f2a24", "193c3e", "265c42", "3e8948", "63c74d", "a8e05a", "e8f5a0"],
    "venom": ["123020", "265c42", "3e8948", "63c74d", "a8e05a", "e8ff9a", "ffffff"],
    "teal": ["0b1f2e", "124e89", "0f6e8a", "0099db", "2ce8f5", "b8fbff", "ffffff"],
    "ice": ["124e89", "0099db", "2ce8f5", "b8fbff", "ffffff"],
    "purple": ["181425", "3a1e4a", "68386c", "b55088", "f6757a", "fcc0d0"],
    "soul": ["1a0d33", "3d1d6b", "6a2fb0", "a24de8", "d48cff", "f2d4ff", "ffffff"],
    "black": ["0a0810", "181425", "262b44", "3a4466", "5a6988"],
    "skin": ["0f2a24", "193c3e", "2a6d5c", "3e9a7a", "6fcf9e", "b8f0cc"],
    "fur": ["3e2731", "733e39", "b86f50", "d8944a", "feae34", "fee761"],
    "mane": ["2a1418", "5c2418", "8a3a1e", "b8562a", "d8803a", "f0a860"],
    "marble": ["3a4466", "8b9bb4", "c0cbdc", "e6ecf4", "ffffff"],
    "leaf": ["0f2a24", "265c42", "3e8948", "63c74d", "a8e05a"],
    "string": ["5a6988", "c0cbdc", "ffffff"],
    "gem_red": ["3e1a24", "a22633", "e43b44", "f6757a", "ffffff"],
    "gem_blue": ["0b1f2e", "124e89", "0099db", "2ce8f5", "ffffff"],
    "gem_purple": ["181425", "68386c", "a24de8", "d48cff", "ffffff"],
    "gem_green": ["0f2a24", "265c42", "63c74d", "e8ff9a", "ffffff"],
    "gem_amber": ["3e2731", "b86f50", "feae34", "fee761", "ffffff"],
    "stone": ["16141c", "2e2c38", "4a4854", "6e6a72", "96929a", "c4c0c4"],
    "rock": ["1a1210", "3a2a22", "5a4232", "7e5e44", "a8845c"],
    "bull": ["140808", "2e1614", "4a221c", "6a3426", "8e4c34", "b0704a"],
    "flesh": ["1e0a22", "3e1640", "6a2a62", "9c4280", "cc6c9a", "f0a8c0"],
    "water": ["0b1f2e", "124e89", "1f7ac8", "3eb0f0", "9ae0ff", "ffffff"],
    "dfur": ["0c0a12", "1a1624", "2c2638", "443a52", "625470"],
    "blood": ["2a0610", "5c0e1c", "8e1a26", "c42a30", "f05a50"],
    "brass": ["2a1a14", "5c3a1c", "8a5a24", "b88a38", "e0b85a", "fff0a0"],
    "emerald": ["0a1f18", "124030", "1e6a44", "2ea05a", "5ad07a", "b4f5b0"],
}
RAMPS = {k: [hx(c) for c in v] for k, v in RAMPS.items()}
GLOWING = {"fire", "hell", "soul", "venom", "ice", "teal", "water"}

# 보스별 스킬 아이콘 바탕 (깊음, 중간, 테두리)
BG = {
    "minotaur": ("140608", "2a0c10", "7a2a24"),
    "nemean_lion": ("140c04", "2e1c08", "8a5a1c"),
    "chimera": ("160806", "301208", "8a3a1a"),
    "cerberus": ("0c0616", "1c0e30", "5a2a8a"),
    "hydra": ("040f0a", "0a2414", "2e6a3a"),
    "medusa": ("041210", "0a2a26", "2a7a6a"),
    "scylla": ("040a18", "0a1a36", "2a5a9a"),
    "common": ("100c08", "241a10", "7a5a2a"),
}

L = np.array([-0.62, -0.62, 0.48])
L = L / np.linalg.norm(L)


def along(a, b, t, off=0.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    Ln = math.hypot(dx, dy) or 1
    return (a[0] + dx * t - dy / Ln * off, a[1] + dy * t + dx / Ln * off)


def bez(p0, p1, p2, p3=None, n=30):
    out = []
    for i in range(n + 1):
        t = i / n
        if p3 is None:
            out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                        (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
        else:
            out.append(((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0],
                        (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def arc(c, r, a0, a1, n=40):
    return [(c[0] + math.cos(math.radians(a0 + (a1 - a0) * i / n)) * r, c[1] + math.sin(math.radians(a0 + (a1 - a0) * i / n)) * r)
            for i in range(n + 1)]


def strip(a, b, prof, n=40):
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        w = prof(t)
        left.append(along(a, b, t, w))
        right.append(along(a, b, t, -w))
    return left + right[::-1]


def curve_strip(pts, prof):
    left, right = [], []
    n = len(pts)
    for i, p in enumerate(pts):
        q = pts[min(n - 1, i + 1)]
        o = pts[max(0, i - 1)]
        dx, dy = q[0] - o[0], q[1] - o[1]
        Ln = math.hypot(dx, dy) or 1
        w = prof(i / max(1, n - 1))
        left.append((p[0] - dy / Ln * w, p[1] + dx / Ln * w))
        right.append((p[0] + dy / Ln * w, p[1] - dx / Ln * w))
    return left + right[::-1]


def xf(pts, c, s=1.0, ang=0.0, flip=False):
    """지역 좌표 도형 → 그림 좌표 (좌우 뒤집기 · 회전(도) · 크기)"""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    out = []
    for x, y in pts:
        if flip:
            x = -x
        out.append((c[0] + (x * ca - y * sa) * s, c[1] + (x * sa + y * ca) * s))
    return out


def ellipse(c, rx, ry, n=48, rot=0.0):
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a) * rx, math.sin(a) * ry
        out.append((c[0] + x * math.cos(rot) - y * math.sin(rot), c[1] + x * math.sin(rot) + y * math.cos(rot)))
    return out


class Dot:
    def __init__(self, boss=None):
        self.rgb = np.zeros((N, N, 3))
        self.a = np.zeros((N, N), dtype=bool)
        self.boss = boss
        self.solid = np.zeros((N, N), dtype=bool)        # 외곽선을 둘러줄 몸체
        self.outc = np.zeros((N, N, 3))
        self.glowq = []                                  # (마스크, 색)
        self.tips = []                                   # 뾰족한 끝 (점, 방향, 재질, 색)
        if boss:
            deep, mid, border = (hx(c) for c in BG[boss])
            ys, xs = np.mgrid[0:N, 0:N] + 0.5
            d = np.hypot(xs - 16, ys - 14) / 22
            t = np.clip(1 - d, 0, 1)
            self.rgb[:] = deep
            self.rgb[t > 0.42] = mid * 0.55 + deep * 0.45
            self.rgb[t > 0.62] = mid
            self.a[:] = True
            self.border = (border, deep)

    # ── 마스크
    def mask(self, pts):
        im = Image.new("L", (N * SS, N * SS), 0)
        ImageDraw.Draw(im).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
        return im

    def cov(self, im):
        return np.asarray(im.resize((N, N), Image.BOX), dtype=float) / 255.0

    # ── 덩어리 (금속 · 가죽 · 뼈 …): 거리장 음영, 외곽선
    def body(self, mat, pts, lo=1, hi=None, bevel=2.2, outline=True, flat=False, spec=True, tips=()):
        for p, u in tips:
            self.tip(p, u, mat)
        im = self.mask(pts)
        c = self.cov(im)
        m = c >= 0.5
        if not m.any():
            return m
        ramp = RAMPS[mat]
        hi = len(ramp) - 1 if hi is None else hi
        big = np.asarray(im, dtype=float) / 255.0 >= 0.5
        dist = ndimage.distance_transform_edt(big) / SS
        h = np.clip(dist / bevel, 0, 1)
        h = np.sqrt(1 - (1 - h) ** 2)
        hs = np.asarray(Image.fromarray((h * 255).astype(np.uint8)).resize((N, N), Image.BOX), dtype=float) / 255.0
        gy, gx = np.gradient(hs * 2.4)
        nrm = np.dstack([-gx, -gy, np.ones_like(hs)])
        nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
        lum = np.clip((nrm * L).sum(2), 0, 1)
        if flat:
            lum = lum * 0.4 + 0.45
        idx = np.clip(np.round(lo + (hi - lo) * (lum ** 1.2) * 1.05), lo, hi).astype(int)
        if spec:
            idx = np.where(lum > 0.94, hi, idx)
        col = np.array(ramp)[idx]
        self.rgb[m] = col[m]
        self.a[m] = True
        if outline:
            self.solid |= m
            self.outc[m] = ramp[0]
        else:
            self.solid &= ~m
        return m

    # ── 이펙트 궤적: 꼬리(t=0) 어둡고 머리(t=1) 밝게, 가운데 밝게
    def stroke(self, mat, pts, width, glow=True, core=True, lo=0):
        ramp = RAMPS[mat]
        P = np.array(pts)
        seg_len = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
        cum = np.concatenate([[0], np.cumsum(seg_len)])
        total = cum[-1] or 1
        m = np.zeros((N, N), dtype=bool)
        val = np.zeros((N, N))
        for y in range(N):
            for x in range(N):
                px, py = x + 0.5, y + 0.5
                best = 1e9
                bt = 0
                for i in range(len(P) - 1):
                    ax, ay = P[i]
                    bx, by = P[i + 1]
                    dx, dy = bx - ax, by - ay
                    l2 = dx * dx + dy * dy or 1e-9
                    u = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / l2))
                    qx, qy = ax + dx * u, ay + dy * u
                    dd = math.hypot(px - qx, py - qy)
                    if dd < best:
                        best = dd
                        bt = (cum[i] + seg_len[i] * u) / total
                w = width(bt) if callable(width) else width
                if best <= w:
                    m[y, x] = True
                    e = 1 - best / max(w, 1e-6)
                    val[y, x] = bt * 0.75 + (e if core else 0) * 0.55
        idx = np.clip(np.round(lo + val * (len(ramp) - 1 - lo)), lo, len(ramp) - 1).astype(int)
        col = np.array(ramp)[idx]
        self.rgb[m] = col[m]
        self.a[m] = True
        self.solid &= ~m
        if glow:
            self.glowq.append((m, ramp[max(1, len(ramp) // 2)]))
        return m

    # ── 발광 덩어리 (불꽃 · 보석 빛): 가장자리 어둡고 속이 밝다
    def glow_body(self, mat, pts, lo=1):
        im = self.mask(pts)
        m = self.cov(im) >= 0.5
        if not m.any():
            return m
        ramp = RAMPS[mat]
        dist = ndimage.distance_transform_edt(m)
        v = dist / max(1, dist.max())
        idx = np.clip(np.round(lo + v * (len(ramp) - 1 - lo)), lo, len(ramp) - 1).astype(int)
        col = np.array(ramp)[idx]
        self.rgb[m] = col[m]
        self.a[m] = True
        self.solid &= ~m
        self.glowq.append((m, ramp[max(1, len(ramp) // 2)]))
        return m

    # ── 칼날: 빛 받는 쪽 밝게 · 반대쪽 어둡게 · 가운데 능선 · 날 끝 반짝
    def blade(self, mat, a, b, prof, n=60, lo=1, hi=None, ridge=0.18, fuller=None, sharp=True):
        if sharp:
            self.tip(b, (b[0] - a[0], b[1] - a[1]), mat, col=RAMPS[mat][-1])
        pts = strip(a, b, prof, n)
        m = self.cov(self.mask(pts)) >= 0.5
        if not m.any():
            return m
        ramp = RAMPS[mat]
        hi = len(ramp) - 1 if hi is None else hi
        dx, dy = b[0] - a[0], b[1] - a[1]
        Ln = math.hypot(dx, dy) or 1
        ux, uy = dx / Ln, dy / Ln
        nx, ny = -uy, ux
        lit = 1 if (nx * L[0] + ny * L[1]) > 0 else -1
        ys, xs = np.mgrid[0:N, 0:N] + 0.5
        t = np.clip(((xs - a[0]) * ux + (ys - a[1]) * uy) / Ln, 0, 1)
        w = np.vectorize(lambda q: max(prof(q), 0.35))(t)
        u = ((xs - a[0]) * nx + (ys - a[1]) * ny) * lit / w
        mid = (lo + hi) / 2
        idx = np.where(u > ridge, hi - 1, np.where(u < -ridge, lo + 1, hi)).astype(float)
        edge = m & ~ndimage.binary_erosion(m)
        idx = np.where(edge & (u > ridge), hi, idx)
        idx = np.where(edge & (u < -ridge), max(lo, round(mid) - 1), idx)
        if fuller is not None:                              # 피홈: 가운데 어두운 줄
            f0, f1 = fuller
            idx = np.where((np.abs(u) < 0.3) & (t > f0) & (t < f1), lo + 1, idx)
        idx = np.clip(np.round(idx), lo, hi).astype(int)
        col = np.array(ramp)[idx]
        self.rgb[m] = col[m]
        self.a[m] = True
        self.solid |= m
        self.outc[m] = ramp[0]
        return m

    def tip(self, p, u, mat, col=None):
        """뾰족한 끝: 덮개 비율로 잘린 끝 픽셀을 채우고, 외곽선이 끝을 둥글게 감싸지 않게 한 점으로 모은다"""
        Ln = math.hypot(u[0], u[1]) or 1
        self.tips.append((p, (u[0] / Ln, u[1] / Ln), mat, col))

    def _tip_px(self, p, u):
        return int(math.floor(p[0] - u[0] * 0.5)), int(math.floor(p[1] - u[1] * 0.5))

    def _tips_fill(self):
        for p, u, mat, col in self.tips:
            ramp = RAMPS[mat]
            tx, ty = self._tip_px(p, u)
            for k in np.arange(0, 3.01, 0.5):
                x, y = int(math.floor(tx + 0.5 - u[0] * k)), int(math.floor(ty + 0.5 - u[1] * k))
                if 0 <= x < N and 0 <= y < N and not self.solid[y, x]:
                    self.rgb[y, x] = ramp[-2]
                    self.a[y, x] = True
                    self.solid[y, x] = True
                    self.outc[y, x] = ramp[0]
            if col is not None and 0 <= tx < N and 0 <= ty < N:
                self.rgb[ty, tx] = hx(col) if isinstance(col, str) else col

    def _tips_ring(self, ring):
        extra = {}
        for p, u, mat, col in self.tips:
            tx, ty = self._tip_px(p, u)
            # 끝 픽셀 앞 · 옆의 외곽선을 걷어 내 끝이 한 픽셀로 끝나게 한다
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                x, y = tx + dx, ty + dy
                if 0 <= x < N and 0 <= y < N and dx * u[0] + dy * u[1] > -0.3:
                    ring[y, x] = False
        return extra

    def flat(self, col, pts, outline=None):
        m = self.cov(self.mask(pts)) >= 0.5
        c = hx(col) if isinstance(col, str) else col
        self.rgb[m] = c
        self.a[m] = True
        if outline is not None:
            self.solid |= m
            self.outc[m] = hx(outline) if isinstance(outline, str) else outline
        else:
            self.solid &= ~m
        return m

    def line(self, pts, col):
        """1픽셀 선 (브레젠험)"""
        c = hx(col) if isinstance(col, str) else col
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
            dx, dy = abs(x1 - x0), -abs(y1 - y0)
            sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
            err = dx + dy
            while True:
                self.px(x0, y0, c)
                if x0 == x1 and y0 == y1:
                    break
                e2 = 2 * err
                if e2 >= dy:
                    err += dy
                    x0 += sx
                if e2 <= dx:
                    err += dx
                    y0 += sy

    def px(self, x, y, col):
        x, y = int(x), int(y)
        if 0 <= x < N and 0 <= y < N:
            self.rgb[y, x] = col
            self.a[y, x] = True

    def sparkle(self, x, y, mat="gold", big=False):
        r = RAMPS[mat]
        self.px(x, y, r[-1])
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            self.px(x + dx, y + dy, r[-2])
        if big:
            for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                self.px(x + dx, y + dy, r[-3])

    def embers(self, mat, n, box, seed=1, size=1):
        rs = np.random.default_rng(seed)
        r = RAMPS[mat]
        for _ in range(n):
            x = rs.uniform(box[0], box[2])
            y = rs.uniform(box[1], box[3])
            c = r[rs.integers(len(r) // 2, len(r))]
            self.px(x, y, c)
            if size > 1 and rs.random() < 0.4:
                self.px(x + 1, y, r[len(r) // 2])

    def finish(self):
        self._tips_fill()
        out = self.rgb.copy()
        a = self.a.copy()
        # 발광 번짐: 1픽셀 (강) · 2픽셀 (약) — 바탕이 있으면 섞고, 없으면 반투명
        for m, col in self.glowq:
            d1 = ndimage.binary_dilation(m) & ~m
            d2 = ndimage.binary_dilation(m, iterations=2) & ~ndimage.binary_dilation(m)
            for ring, k in ((d1, 0.45), (d2, 0.2)):
                sel = ring & ~self.solid
                if self.boss:
                    out[sel] = out[sel] * (1 - k) + col * k
                else:
                    empty = sel & ~a
                    out[empty] = col
                    a[empty] = True if k > 0.3 else a[empty]
                    blend = sel & self.a
                    out[blend] = out[blend] * (1 - k * 0.6) + col * k * 0.6
        # 선택적 외곽선: 몸체 바깥 1픽셀을 그 재질의 가장 어두운 색으로
        ring = ndimage.binary_dilation(self.solid, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]]) & ~self.solid
        extra = self._tips_ring(ring)
        for y, x in zip(*np.nonzero(ring)):
            if (y, x) in extra:
                out[y, x] = extra[(y, x)]
                a[y, x] = True
                continue
            nb = [self.outc[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                  if 0 <= yy < N and 0 <= xx < N and self.solid[yy, xx]]
            if not nb:
                continue
            c = np.mean(nb, axis=0)
            if self.boss or not self.a[y, x] or True:
                out[y, x] = c
                a[y, x] = True
        if self.boss:
            border, deep = self.border
            out[0, :] = out[-1, :] = border * 0.9
            out[:, 0] = out[:, -1] = border * 0.9
            out[0, 0] = out[0, -1] = out[-1, 0] = out[-1, -1] = deep
            out[1, 1:-1] = np.minimum(out[1, 1:-1], border * 0.55 + deep * 0.45) if False else out[1, 1:-1]
        img = np.dstack([np.clip(out, 0, 255), a * 255]).astype(np.uint8)
        return Image.fromarray(img, "RGBA")
