"""전설 무기 스킬 효과 — 직접 그리는 빛 효과 (서양 판타지)

 무기마다 두 장:
   ground : 256x256 바닥 마법진 (위에서 본 원형)      → tele/wfx_* 를 덮어씀
   burst  : 256x512 세로 효과 (번개 · 베기 · 회오리 · 빛기둥 · 불기둥 ...) → fx/<무기> (스킬 쓸 때 잠깐 솟음)

 그리는 법: 4배 크게 선/면을 '빛의 세기' 로 그린 뒤 → 여러 크기로 번지게(블룸) → 색 입히기
   세기가 강한 곳은 흰색에 가깝고, 약한 곳은 무기 색으로 번진다. 알파 = 밝기.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 4                                   # 슈퍼샘플

PAL = {
    # (번짐 색, 중간 색, 금 장식 색)
    "thunder": ((70, 150, 255), (170, 225, 255), (255, 214, 120)),
    "dragon": ((255, 70, 20), (255, 170, 60), (255, 220, 140)),
    "wind": ((40, 220, 190), (170, 255, 235), (220, 255, 250)),
    "phoenix": ((255, 170, 40), (255, 230, 140), (255, 250, 210)),
    "blackiron": ((200, 20, 60), (255, 90, 110), (200, 120, 255)),
    "tiger": ((150, 60, 255), (215, 170, 255), (255, 255, 255)),
    "staff": ((90, 90, 255), (170, 170, 255), (255, 220, 140)),
    "peachwood": ((255, 60, 10), (255, 150, 40), (255, 235, 150)),
}


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.W, self.H = w * SS, h * SS
        self.layers = {k: Image.new("L", (self.W, self.H), 0) for k in ("core", "mid", "gold")}

    def d(self, k):
        return ImageDraw.Draw(self.layers[k])

    # 좌표는 최종 픽셀 기준
    def line(self, k, pts, width, val=255):
        self.d(k).line([(x * SS, y * SS) for x, y in pts], fill=val, width=max(1, int(width * SS)), joint="curve")

    def circle(self, k, cx, cy, r, width, val=255):
        self.d(k).ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], outline=val, width=max(1, int(width * SS)))

    def disc(self, k, cx, cy, r, val=255):
        self.d(k).ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=val)

    def poly(self, k, pts, val=255):
        self.d(k).polygon([(x * SS, y * SS) for x, y in pts], fill=val)

    def render(self, pal, bloom=1.0, core_white=0.85):
        glow_c, mid_c, gold_c = (np.array(c, np.float32) / 255 for c in pal)
        out = np.zeros((self.h, self.w, 3), np.float32)
        alpha = np.zeros((self.h, self.w), np.float32)
        for k, col in (("mid", mid_c), ("core", mid_c), ("gold", gold_c)):
            L = self.layers[k].resize((self.w, self.h), Image.LANCZOS)
            a = np.asarray(L, np.float32) / 255
            # 블룸: 여러 반지름으로 번짐
            g = np.zeros_like(a)
            for r, wgt in ((2, 0.75), (5, 0.6), (11, 0.42), (24, 0.26)):
                b = np.asarray(L.filter(ImageFilter.GaussianBlur(r * bloom)), np.float32) / 255
                g += b * wgt
            g = np.clip(g, 0, 1.4)
            if k == "core":
                c_core = col * (1 - core_white) + core_white
            else:
                c_core = col
            out += g[..., None] * glow_c * (0.9 if k != "gold" else 0.55)
            out += a[..., None] * c_core * (1.25 if k == "core" else 1.0)
            alpha = np.maximum(alpha, np.clip(a * 1.0 + g * 0.85, 0, 1))
        # 밝기 → 색 (흰 심지)
        lum = out.max(2, keepdims=True)
        col = np.where(lum > 1e-4, out / np.maximum(lum, 1e-4), 0)
        hot = np.clip(lum - 1.0, 0, 1)
        col = col * (1 - hot * 0.7) + hot * 0.7
        a = np.clip(np.maximum(alpha, np.clip(lum[..., 0], 0, 1)), 0, 1)
        rgb = np.clip(col * np.clip(lum, 0, 1) / np.maximum(a[..., None], 1e-4), 0, 1)
        img = np.dstack([rgb, a])
        return Image.fromarray((img * 255).astype(np.uint8), "RGBA")


def _rng(seed):
    return np.random.default_rng(seed)


# ─────────────────────────────────────────────────────────────── 바닥 마법진
def _rune_ring(c, cx, cy, r, n, size, k="gold", seed=0):
    """작은 룬 문양 (직선 조합) 을 원 위에 n 개"""
    R = _rng(seed)
    shapes = []
    for _ in range(6):
        segs = []
        for _ in range(R.integers(2, 4)):
            segs.append(((R.uniform(-1, 1), R.uniform(-1, 1)), (R.uniform(-1, 1), R.uniform(-1, 1))))
        shapes.append(segs)
    for i in range(n):
        a = 2 * math.pi * i / n
        ox, oy = cx + math.cos(a) * r, cy + math.sin(a) * r
        ca, sa = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
        for (x0, y0), (x1, y1) in shapes[i % len(shapes)]:
            p0 = (ox + (x0 * ca - y0 * sa) * size, oy + (x0 * sa + y0 * ca) * size)
            p1 = (ox + (x1 * ca - y1 * sa) * size, oy + (x1 * sa + y1 * ca) * size)
            c.line(k, [p0, p1], 1.3)


def _star(c, cx, cy, r, n, step, k, width):
    pts = [(cx + math.cos(2 * math.pi * i / n - math.pi / 2) * r, cy + math.sin(2 * math.pi * i / n - math.pi / 2) * r) for i in range(n)]
    for i in range(n):
        c.line(k, [pts[i], pts[(i + step) % n]], width)


def ground(wid):
    S = 256
    c = Canvas(S, S)
    cx = cy = S / 2
    R = S / 2 - 8
    # 공통 틀: 이중 원 + 룬 띠 + 안쪽 원
    c.circle("core", cx, cy, R, 3.0)
    c.circle("mid", cx, cy, R - 6, 1.2, 200)
    _rune_ring(c, cx, cy, R - 15, 28, 5, "gold", seed=sum(map(ord, wid)))
    c.circle("mid", cx, cy, R - 24, 2.2, 230)
    for i in range(48):
        a = 2 * math.pi * i / 48
        r0, r1 = R - 24, R - (28 if i % 4 else 34)
        c.line("mid", [(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], 1.0, 180)
    rin = R - 38
    if wid == "thunder":                          # 육망성 + 번개 여섯 갈래
        _star(c, cx, cy, rin, 6, 2, "core", 2.0)
        c.circle("gold", cx, cy, rin * 0.5, 1.4)
        for i in range(6):
            a = 2 * math.pi * i / 6 + math.pi / 6
            pts = [(cx + math.cos(a) * rin * 0.5, cy + math.sin(a) * rin * 0.5)]
            for j in range(1, 5):
                rr = rin * (0.5 + j * 0.12)
                aa = a + (0.12 if j % 2 else -0.12)
                pts.append((cx + math.cos(aa) * rr, cy + math.sin(aa) * rr))
            c.line("core", pts, 1.8)
        c.disc("core", cx, cy, 7)
    elif wid == "dragon":                         # 용의 발톱: 세 겹 삼각 + 비늘 호
        _star(c, cx, cy, rin, 3, 1, "core", 2.2)
        _star(c, cx, cy, rin * 0.62, 3, 1, "gold", 1.4)
        for i in range(3):
            a0 = 2 * math.pi * i / 3 + math.pi / 3
            for j in range(4):
                rr = rin * (0.35 + j * 0.13)
                c.d("mid").arc([(cx - rr) * SS, (cy - rr) * SS, (cx + rr) * SS, (cy + rr) * SS],
                                math.degrees(a0) - 20, math.degrees(a0) + 20, fill=220, width=int(1.6 * SS))
        c.disc("core", cx, cy, 6)
    elif wid == "wind":                           # 회오리 팔 여섯
        for i in range(6):
            a0 = 2 * math.pi * i / 6
            pts = [(cx + math.cos(a0 + t * 2.4) * (8 + t * rin * 0.95), cy + math.sin(a0 + t * 2.4) * (8 + t * rin * 0.95)) for t in np.linspace(0, 1, 40)]
            c.line("core" if i % 2 == 0 else "mid", pts, 2.2 if i % 2 == 0 else 1.4)
        c.circle("gold", cx, cy, rin * 0.28, 1.2)
    elif wid == "phoenix":                        # 성스러운 결계: 팔각 + 십자 + 깃털
        _star(c, cx, cy, rin, 8, 3, "gold", 1.4)
        c.circle("core", cx, cy, rin * 0.72, 1.8)
        for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
            c.line("core", [(cx, cy), (cx + math.cos(a) * rin, cy + math.sin(a) * rin)], 2.4)
        for i in range(16):
            a = 2 * math.pi * i / 16
            p = (cx + math.cos(a) * rin * 0.86, cy + math.sin(a) * rin * 0.86)
            q = (cx + math.cos(a + 0.12) * rin * 0.6, cy + math.sin(a + 0.12) * rin * 0.6)
            c.line("mid", [p, q], 1.2, 200)
        c.disc("core", cx, cy, 9)
    elif wid == "blackiron":                      # 뒤집힌 가시 + 핏빛 원
        for i in range(12):
            a = 2 * math.pi * i / 12
            p0 = (cx + math.cos(a - 0.1) * rin * 0.45, cy + math.sin(a - 0.1) * rin * 0.45)
            p1 = (cx + math.cos(a) * rin, cy + math.sin(a) * rin)
            p2 = (cx + math.cos(a + 0.1) * rin * 0.45, cy + math.sin(a + 0.1) * rin * 0.45)
            c.poly("mid" if i % 2 else "core", [p0, p1, p2], 150 if i % 2 else 230)
        c.circle("gold", cx, cy, rin * 0.42, 1.6)
        _star(c, cx, cy, rin * 0.42, 5, 2, "core", 1.6)
    elif wid == "tiger":                          # 세 줄 발톱 자국
        for j in (-1, 0, 1):
            pts = []
            for t in np.linspace(-1, 1, 30):
                x = cx + t * rin * 0.95 + j * 20
                y = cy + t * rin * 0.8 - j * 20 + math.sin(t * 2.5) * 8
                pts.append((x, y))
            c.line("core", pts, 3.2 - abs(j) * 0.6)
            c.line("mid", pts, 7)
        c.circle("gold", cx, cy, rin * 0.95, 1.0, 160)
    elif wid == "staff":                          # 오망성 + 궤도 원 세 개
        _star(c, cx, cy, rin, 5, 2, "core", 2.0)
        c.circle("mid", cx, cy, rin, 1.4, 220)
        for i in range(5):
            a = 2 * math.pi * i / 5 - math.pi / 2
            c.circle("gold", cx + math.cos(a) * rin, cy + math.sin(a) * rin, 9, 1.4)
            c.disc("core", cx + math.cos(a) * rin, cy + math.sin(a) * rin, 3)
        c.circle("gold", cx, cy, rin * 0.38, 1.4)
    elif wid == "peachwood":                      # 불꽃 고리: 바깥으로 솟는 불 혀
        R_ = _rng(9)
        for i in range(36):
            a = 2 * math.pi * i / 36
            L = rin * R_.uniform(0.25, 0.42)
            base = rin * 0.6
            p0 = (cx + math.cos(a - 0.08) * base, cy + math.sin(a - 0.08) * base)
            p1 = (cx + math.cos(a + 0.05) * (base + L), cy + math.sin(a + 0.05) * (base + L))
            p2 = (cx + math.cos(a + 0.08) * base, cy + math.sin(a + 0.08) * base)
            c.poly("mid", [p0, p1, p2], int(R_.uniform(150, 240)))
        c.circle("core", cx, cy, rin * 0.6, 2.4)
        _star(c, cx, cy, rin * 0.5, 7, 3, "gold", 1.2)
    return c.render(PAL[wid])


# ─────────────────────────────────────────────────────────────── 세로 효과
def _bolt(c, x0, y0, x1, y1, R, width, k="core", depth=0):
    pts = [(x0, y0)]
    n = 14
    for i in range(1, n):
        t = i / n
        pts.append((x0 + (x1 - x0) * t + R.normal(0, 10), y0 + (y1 - y0) * t))
    pts.append((x1, y1))
    c.line(k, pts, width)
    if depth < 2:
        for i in range(2, int(n * 0.7), 3):
            if R.random() < 0.8:
                x, y = pts[i]
                _bolt(c, x, y, x + R.normal(0, 50), y + R.uniform(40, 110), R, width * 0.5, "mid", depth + 1)


def burst(wid):
    W, H = 256, 512
    c = Canvas(W, H)
    R = _rng(sum(map(ord, wid)))
    cx = W / 2
    if wid == "thunder":                          # 하늘에서 내리꽂는 번개
        _bolt(c, cx + 10, 0, cx, H - 40, _rng(5), 16, "mid")       # 같은 모양으로 굵은 번짐 + 가는 심지
        _bolt(c, cx + 10, 0, cx, H - 40, _rng(5), 6)
        c.disc("core", cx, H - 40, 22)
        c.d("mid").ellipse([(cx - 90) * SS, (H - 52) * SS, (cx + 90) * SS, (H - 28) * SS], outline=220, width=3 * SS)
        for i in range(10):
            a = R.uniform(0, math.pi)
            c.line("mid", [(cx, H - 40), (cx + math.cos(a) * 60, H - 40 - math.sin(a) * 40)], 1.6, 200)
    elif wid in ("dragon", "blackiron"):         # 거대한 초승달 베기 (가운데 두껍고 끝이 뾰족)
        tilt = -0.3 if wid == "dragon" else 0.45
        r = 118
        cy0 = H * 0.56

        def crescent(k, thick, val, rr):
            outer, inner = [], []
            for t in np.linspace(0, 1, 70):
                a = math.pi * (0.04 + 0.92 * t) + tilt
                th = thick * math.sin(math.pi * t) ** 0.8
                outer.append((cx + math.cos(a) * rr, cy0 - math.sin(a) * rr * 0.72))
                inner.append((cx + math.cos(a) * (rr - th), cy0 - math.sin(a) * (rr - th) * 0.72))
            c.poly(k, outer + inner[::-1], val)
            return outer
        crescent("mid", 46, 150, r)
        crescent("mid", 30, 220, r)
        edge = crescent("core", 13, 255, r)
        c.line("gold", edge, 2.0)
        for i in range(60):
            t = R.random()
            a = math.pi * (0.04 + 0.92 * t) + tilt
            rr = r + R.normal(4, 10)
            x = cx + math.cos(a) * rr; y = cy0 - math.sin(a) * rr * 0.72
            c.disc("gold" if i % 3 else "core", x, y, R.uniform(1.0, 2.8))
    elif wid == "wind":                           # 회오리
        for i in range(9):
            y = H - 30 - i * 48
            rx = 26 + i * 11
            c.d("core" if i % 2 == 0 else "mid").arc([(cx - rx) * SS, (y - 12) * SS, (cx + rx) * SS, (y + 12) * SS],
                                                    200 + i * 17, 200 + i * 17 + 250, fill=235, width=int((2.8 - i * 0.15) * SS))
        for i in range(30):
            y = R.uniform(40, H - 20); x = cx + R.normal(0, 18 + (H - y) * 0.12)
            c.line("mid", [(x, y), (x + R.uniform(10, 30), y - R.uniform(2, 8))], 1.2, 200)
    elif wid in ("phoenix", "staff"):             # 빛기둥 (+ 날개 / 룬)
        for i, (wd, k, v) in enumerate(((46, "mid", 110), (24, "mid", 200), (8, "core", 255))):
            c.poly(k, [(cx - wd, H - 20), (cx + wd, H - 20), (cx + wd * 0.35, 0), (cx - wd * 0.35, 0)], v)
        c.d("core").ellipse([(cx - 70) * SS, (H - 34) * SS, (cx + 70) * SS, (H - 6) * SS], outline=255, width=3 * SS)
        if wid == "phoenix":
            for s in (-1, 1):
                for j in range(7):
                    y0 = H * 0.42 + j * 9
                    L = 95 - j * 9
                    c.line("gold", [(cx + s * 14, y0), (cx + s * (14 + L), y0 - 40 + j * 10)], 2.2 - j * 0.15)
        else:
            for j in range(10):
                y = H - 60 - j * 42
                a = j * 1.3
                c.circle("gold", cx + math.cos(a) * 40, y, 7, 1.3)
                c.disc("core", cx + math.cos(a) * 40, y, 2)
        for i in range(40):
            c.disc("gold", cx + R.normal(0, 30), R.uniform(10, H - 30), R.uniform(0.6, 1.8))
    elif wid == "tiger":                          # 세 줄 발톱 베기
        for j in (-1, 0, 1):
            x0 = cx - 80 + j * 34; y0 = H * 0.25 + j * 10
            x1 = cx + 80 + j * 34; y1 = H * 0.75 + j * 10
            pts = [(x0 + (x1 - x0) * t + math.sin(t * math.pi) * 18, y0 + (y1 - y0) * t) for t in np.linspace(0, 1, 30)]
            for i in range(len(pts) - 1):
                t = i / (len(pts) - 1)
                c.line("mid", [pts[i], pts[i + 1]], max(1.0, 20 * math.sin(math.pi * t)))
                c.line("core", [pts[i], pts[i + 1]], max(0.8, 7 * math.sin(math.pi * t)))
    elif wid == "peachwood":                      # 불기둥: 굽이치는 불 혀 여러 겹
        def tongue(k, x, h, wd, val, ph):
            left, right = [], []
            for t in np.linspace(0, 1, 26):
                y = H - 12 - t * h
                w_ = wd * (1 - t) ** 0.7
                sway = math.sin(t * 5 + ph) * 10 * t
                left.append((x + sway - w_, y)); right.append((x + sway + w_, y))
            c.poly(k, left + right[::-1], val)
        for i in range(14):
            tongue("mid", cx + R.normal(0, 26), R.uniform(0.5, 0.95) * H, R.uniform(16, 30), int(R.uniform(110, 200)), R.uniform(0, 6))
        for i in range(8):
            tongue("mid", cx + R.normal(0, 14), R.uniform(0.35, 0.7) * H, R.uniform(10, 18), 235, R.uniform(0, 6))
        for i in range(5):
            tongue("core", cx + R.normal(0, 8), R.uniform(0.2, 0.45) * H, R.uniform(6, 11), 255, R.uniform(0, 6))
        for i in range(40):
            c.disc("gold", cx + R.normal(0, 44), R.uniform(10, H * 0.65), R.uniform(0.8, 2.2))
    return c.render(PAL[wid])


WEAPONS = ["thunder", "dragon", "wind", "phoenix", "blackiron", "tiger", "staff", "peachwood"]


def preview(path):
    cell = 256
    sheet = Image.new("RGB", (cell * 8, cell + cell * 2), (14, 12, 18))
    for i, w in enumerate(WEAPONS):
        g = ground(w)
        b = burst(w)
        bg = Image.new("RGBA", (cell, cell), (22, 20, 28, 255)); bg.alpha_composite(g)
        sheet.paste(bg.convert("RGB"), (i * cell, 0))
        bg2 = Image.new("RGBA", (256, 512), (22, 20, 28, 255)); bg2.alpha_composite(b)
        sheet.paste(bg2.convert("RGB"), (i * cell, cell))
    sheet.save(path)


if __name__ == "__main__":
    preview(os.path.join(os.path.dirname(__file__), "..", "..", "preview", "skill_fx_new.png"))
