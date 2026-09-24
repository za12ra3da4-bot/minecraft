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


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


class Sheet:
    """재질별 마스크 레이어를 모아 32px 로 굽는다."""

    def __init__(self, size=32):
        self.size = size
        self.big = size * SS
        self.layers = []  # (material, Image L)

    def layer(self, material):
        im = Image.new("L", (self.big, self.big), 0)
        self.layers.append((material, im))
        return ImageDraw.Draw(im)

    # 좌표는 0..size 기준 (소수 허용)
    @staticmethod
    def s(v):
        return v * SS

    def bake(self, outline=True, shade=True, gloss=True):
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
    """청동 테두리 + 보스색 바탕 (디더링 방사 그라디언트)."""
    rnd = random.Random(seed)
    n = size
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = im.load()
    f = [hexc(c) for c in field]
    br = [hexc(c) for c in RAMP["bronze"]]
    r_out = 1  # 바깥 외곽선 두께
    cx = cy = (n - 1) / 2
    for y in range(n):
        for x in range(n):
            # 모서리 둥글게 (2px)
            corner = min(x, n - 1 - x) + min(y, n - 1 - y)
            if corner < 2:
                continue
            edge = min(x, y, n - 1 - x, n - 1 - y)
            if edge == 0 or corner == 2:
                px[x, y] = OUTLINE
                continue
            if edge <= 2:
                # 청동 테 — 좌상단 밝고 우하단 어둡다
                if edge == 1:
                    c = br[3] if (x + y) < n - 1 else br[1]
                    if x == 1 or y == 1:
                        c = br[3] if (x < n - 3 and y < n - 3) else br[2]
                    if x == n - 2 or y == n - 2:
                        c = br[0]
                else:
                    c = br[2] if (x + y) < n - 1 else br[1]
                    # 메안더 느낌의 눈금
                    if (x + y) % 4 == 0 and (x in (2, n - 3) or y in (2, n - 3)):
                        c = br[0]
                px[x, y] = c
                continue
            if edge == 3:
                px[x, y] = OUTLINE[:3] + (255,)
                continue
            d = math.hypot(x - cx, y - (cy - 3)) / (n * 0.62)
            v = 1 - d + (rnd.random() - 0.5) * 0.08
            b = bayer(x, y) * 0.34
            if v > 0.62 + b:
                c = f[2]
            elif v > 0.30 + b:
                c = f[1]
            else:
                c = f[0]
            px[x, y] = c
    return im


def compose(bg, fg):
    out = bg.copy()
    out.alpha_composite(fg)
    return out
