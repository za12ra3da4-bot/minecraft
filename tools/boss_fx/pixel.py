"""작은 픽셀아트 엔진 — 슈퍼샘플로 모양을 그리고 32px 로 내려 음영·외곽선을 입힌다.

아이콘(스킬)과 이펙트 텍스처가 같은 명암 규칙(좌상단 광원, 1px 어두운 외곽선)을 쓰게 하려고 분리했다.
"""
from PIL import Image, ImageDraw
import math
import random

SS = 8  # 슈퍼샘플 배율

# 재질 램프: (그림자, 중간, 밝음, 하이라이트)
RAMP = {
    "bronze": ["#5a3a1a", "#8a5a2a", "#c08a40", "#f0c870"],
    "steel": ["#343842", "#646a78", "#a4acb8", "#e8eef4"],
    "bone": ["#6a5a40", "#a89468", "#d8c8a0", "#f8f0d8"],
    "fire": ["#8a1a08", "#d8480c", "#f89820", "#fff070"],
    "hellfire": ["#4a0606", "#a81c0c", "#e85a14", "#ffc850"],
    "soul": ["#2a0a40", "#6a24a0", "#b060e0", "#f0c8ff"],
    "poison": ["#1a4a10", "#3a8a20", "#78c838", "#d0f880"],
    "stone": ["#3a3a38", "#686864", "#9a9a92", "#d4d4ca"],
    "eye": ["#5a4a00", "#c8a000", "#f8e040", "#ffffc8"],
    "blood": ["#4a0808", "#8a1010", "#c82020", "#f86050"],
    "wave": ["#6a7884", "#aab8c2", "#dde6ec", "#ffffff"],
    "water": ["#0a2a5a", "#1a5aa0", "#40a0e0", "#b8f4ff"],
    "flesh": ["#2a1040", "#5a2a78", "#9050b0", "#dca8ec"],
    "fur": ["#6a4010", "#b07820", "#e0b040", "#fff0a0"],
    "dark": ["#0e0e12", "#24242e", "#44444f", "#70707e"],
    "scale": ["#0e3a1e", "#1e6a34", "#3aa050", "#9ae080"],
    "jade": ["#0c3a34", "#1a6a5c", "#3aa890", "#a8f0dc"],
    "red": ["#5a0a0a", "#a01414", "#e03020", "#ff9070"],
    "white": ["#8a8a8a", "#c8c8c8", "#f0f0f0", "#ffffff"],
    "gold": ["#6a4a08", "#b08018", "#e8c040", "#fff8b0"],
}

OUTLINE = (18, 12, 14, 255)


def micro(mat, n):
    """재질 질감 (톤 단계에 더하는 값, 대략 -0.6..0.6)"""
    import numpy as np
    ys, xs = np.mgrid[0:n, 0:n].astype(float)
    k = n / 32.0
    r = np.random.default_rng(hash(mat) % 1000)
    noise = r.random((n, n)) - 0.5
    if mat in ("scale", "jade", "poison"):
        cell = 3 * k
        row = np.floor(ys / cell)
        u = (xs + (row % 2) * cell / 2) % cell / cell
        v = ys % cell / cell
        return np.where((v > 0.72) | ((np.abs(u - 0.5) > 0.42) & (v > 0.4)), -0.9, 0.15)
    if mat in ("fur", "gold") and mat == "fur":
        return np.sin((xs * 0.7 + ys * 1.9) / k * 1.3 + noise * 2) * 0.45
    if mat in ("steel", "bronze", "gold", "white"):
        return (np.sin(ys / k * 2.3) * 0.12 + noise * 0.12) * (1 if mat != "white" else 0.5)
    if mat in ("fire", "hellfire", "soul"):
        return np.sin(xs / k * 1.7 + np.sin(ys / k * 0.9) * 2) * 0.35
    if mat in ("stone", "dark", "bone"):
        return noise * 0.55
    if mat in ("flesh", "red", "blood", "water"):
        return noise * 0.3
    return noise * 0.2


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


class Sheet:
    """재질별 마스크 레이어를 모아 32px 로 굽는다."""

    K = SS

    def __init__(self, size=32):
        self.size = size
        self.big = size * SS
        self.layers = []  # (material, Image L)
        Sheet.K = self.big / 32.0   # 그리는 좌표는 언제나 0..32

    def layer(self, material):
        im = Image.new("L", (self.big, self.big), 0)
        self.layers.append((material, im))
        return ImageDraw.Draw(im)

    # 좌표는 0..size 기준 (소수 허용)
    @staticmethod
    def s(v):
        return v * Sheet.K

    def bake(self, outline=True, shade=True, gloss=True, mode="bevel"):
        if mode == "bevel":
            return self.bake_bevel(outline)
        return self.bake_flat(outline, shade, gloss)

    def bake_bevel(self, outline=True):
        """거리장 베벨 음영: 모양마다 가장자리에서 안쪽으로 둥글게 솟은 높이 → 좌상단 광원 램버트 + 반사광.
        재질 램프 5단 사이를 순서 디더링으로 섞고, 외곽선은 재질의 가장 어두운 색(바깥 실루엣만 검정)."""
        import numpy as np
        from scipy import ndimage
        n = self.size
        out = np.zeros((n, n, 4))
        owner = -np.ones((n, n), dtype=int)
        bay = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.5
        L = np.array([-0.55, -0.65, 0.52])
        L = L / np.linalg.norm(L)
        for li, (mat, im) in enumerate(self.layers):
            big = np.asarray(im, dtype=float) / 255.0
            small = np.asarray(im.resize((n, n), Image.BOX), dtype=float) / 255.0
            m = small >= 0.5
            if not m.any():
                continue
            # 고해상도 거리장 → 높이 (반지름 R 픽셀 베벨)
            dist = ndimage.distance_transform_edt(big >= 0.5) / SS
            R = max(1.2, min(3.2, dist.max() * 0.8))
            h = np.clip(dist / R, 0, 1)
            h = np.sqrt(1 - (1 - h) ** 2)
            hs = np.asarray(Image.fromarray((h * 255).astype(np.uint8)).resize((n, n), Image.BOX), dtype=float) / 255.0
            gy, gx = np.gradient(hs * 2.2)
            nz = np.ones_like(hs)
            nrm = np.sqrt(gx ** 2 + gy ** 2 + nz ** 2)
            dot = (-gx * L[0] - gy * L[1] + nz * L[2]) / nrm
            shade = 0.18 + 0.82 * np.clip(dot, 0, 1)
            spec = np.clip(dot, 0, 1) ** 14
            ramp = [np.array(hexc(c)[:3], dtype=float) for c in RAMP[mat]]
            dark = ramp[0] * 0.62
            tones = [dark, ramp[0], (ramp[0] + ramp[1]) / 2, ramp[1], (ramp[1] + ramp[2]) / 2, ramp[2], ramp[3]]
            ys, xs = np.nonzero(m)
            dith = 0.12 if n <= 32 else 0.18
            mt = micro(mat, n)
            for y, x in zip(ys, xs):
                t = 0.6 + shade[y, x] * 4.9 + spec[y, x] * 1.6 + bay[y % 4, x % 4] * dith + mt[y, x]
                k = int(np.clip(round(t), 1, 6))
                out[y, x, :3] = tones[k]
                out[y, x, 3] = 255
                owner[y, x] = li
            # 재질 안쪽 경계선: 다른 레이어와 닿는 쪽을 그 재질의 가장 어두운 색으로
            edge = m & ~ndimage.binary_erosion(m, structure=np.ones((3, 3)), border_value=0)
            for y, x in zip(*np.nonzero(edge)):
                nb = [owner[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                      if 0 <= yy < n and 0 <= xx < n]
                if any(o != li and o >= 0 for o in nb) and (y + x) % 1 == 0:
                    out[y, x, :3] = dark
        if outline:
            filled = out[..., 3] > 0
            ring = ndimage.binary_dilation(filled, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])) & ~filled
            out[ring] = OUTLINE
        img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
        return img

    def bake_flat(self, outline=True, shade=True, gloss=True):
        n = self.size
        out = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        union = [[False] * n for _ in range(n)]
        px = out.load()
        for mat, im in self.layers:
            small = im.resize((n, n), Image.BOX)
            sp = small.load()
            m = [[sp[x, y] >= 128 for x in range(n)] for y in range(n)]
            ramp = [hexc(c) for c in RAMP[mat]]
            # 위→아래 기본 명암
            ys = [y for y in range(n) for x in range(n) if m[y][x]]
            if not ys:
                continue
            y0, y1 = min(ys), max(ys)
            for y in range(n):
                for x in range(n):
                    if not m[y][x]:
                        continue
                    t = (y - y0) / max(1, (y1 - y0))
                    c = ramp[2] if t < 0.45 else ramp[1]
                    if shade:
                        up = y > 0 and m[y - 1][x]
                        lf = x > 0 and m[y][x - 1]
                        dn = y < n - 1 and m[y + 1][x]
                        rt = x < n - 1 and m[y][x + 1]
                        if not up or not lf:
                            c = ramp[3] if (not up and not lf) and gloss else ramp[2]
                            if not up and gloss and t < 0.5:
                                c = ramp[3]
                        if not dn or not rt:
                            c = ramp[0]
                    px[x, y] = c
                    union[y][x] = True
        if outline:
            add = []
            for y in range(n):
                for x in range(n):
                    if union[y][x]:
                        continue
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        xx, yy = x + dx, y + dy
                        if 0 <= xx < n and 0 <= yy < n and union[yy][xx]:
                            add.append((x, y))
                            break
            for x, y in add:
                px[x, y] = OUTLINE
        return out


def bayer(x, y):
    m = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    return m[y % 4][x % 4] / 16.0


def plate(field, size=32, seed=0):
    """청동 테두리 + 보스색 바탕 (디더링 방사 그라디언트). 크기에 맞춰 테 두께를 늘린다"""
    rnd = random.Random(seed)
    n = size
    k = n / 32.0
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = im.load()
    f = [hexc(c) for c in field]
    br = [hexc(c) for c in RAMP["bronze"]]
    cx = (n - 1) / 2
    rim = int(round(2 * k))
    for y in range(n):
        for x in range(n):
            corner = min(x, n - 1 - x) + min(y, n - 1 - y)
            if corner < round(2 * k):
                continue
            edge = min(x, y, n - 1 - x, n - 1 - y)
            if edge == 0 or corner == round(2 * k):
                px[x, y] = OUTLINE
                continue
            if edge <= rim:
                tl = (x + y) < n - 1
                if edge == 1:
                    c = br[3] if tl else br[0]
                elif edge == rim:
                    c = br[1] if tl else br[3]
                else:
                    c = br[2] if tl else br[1]
                # 메안더 눈금
                if (x + y) % max(4, int(4 * k)) == 0 and edge == max(2, rim - 1):
                    c = br[0]
                px[x, y] = c
                continue
            if edge == rim + 1:
                px[x, y] = OUTLINE
                continue
            d = math.hypot(x - cx, y - (cx - 3 * k)) / (n * 0.62)
            v = 1 - d + (rnd.random() - 0.5) * 0.06
            b = bayer(x, y) * 0.3
            if v > 0.64 + b:
                c = f[2]
            elif v > 0.32 + b:
                c = f[1]
            else:
                c = f[0]
            px[x, y] = c
    return im


def compose(bg, fg):
    out = bg.copy()
    out.alpha_composite(fg)
    return out
