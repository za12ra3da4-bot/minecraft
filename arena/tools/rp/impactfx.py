"""보스 스킬 타격 연출 그림 (경고 장판이 터지는 순간)

 종류(k)마다 세 장:
   shock_k  : 바닥 충격파 고리 (작게 생겨 크게 퍼지고 사라짐)            → bg:impact/shock_k  (평면)
   crater_k : 터진 자리에 잠깐 남는 자국 (균열 · 그을음 · 독 · 모래 물결)   → bg:impact/crater_k (평면)
   burst_k  : 세로로 솟는 폭발 기둥 (불기둥 · 흙먼지 · 독 물보라 · 돌풍 · 빛기둥) → bg:impact/burst_k (세로, 늘 플레이어를 봄)
 종류: fire(탈로스) · sand(스핑크스) · venom/gale(라돈) · stone(키클롭스) · holy(황금 사과)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from skillfx import Canvas, _crack, _noise, _radial, _dark_under, _rng

PAL = {
    # (번짐 색, 중간 색, 장식 색)
    "fire": ((255, 80, 10), (255, 165, 50), (255, 230, 150)),
    "sand": ((235, 160, 40), (255, 215, 120), (255, 245, 200)),
    "venom": ((60, 200, 30), (160, 255, 90), (220, 255, 160)),
    "gale": ((90, 180, 255), (195, 235, 255), (255, 255, 255)),
    "stone": ((150, 125, 95), (215, 195, 160), (250, 240, 220)),
    "holy": ((255, 190, 50), (255, 235, 140), (255, 255, 230)),
}
KINDS = list(PAL)


def _seed(k):
    return sum(ord(ch) * (i + 1) for i, ch in enumerate(k))   # hash() 는 실행마다 달라짐
S = 128            # Canvas 좌표 (최종 256)


# ─────────────────────────────────────────────────────────────── 충격파 고리
def shock(k):
    c = Canvas(S, S); R = _rng(_seed(k) % 997)
    cx = cy = S / 2
    c.circle("mid", cx, cy, 52, 9, 110)
    c.circle("core", cx, cy, 54, 2.6, 255)
    c.circle("gold", cx, cy, 47, 1.2, 150)
    # 퍼지는 속도선 (고리 안쪽에서 밖으로)
    for i in range(54):
        a = R.uniform(0, 2 * math.pi)
        r0 = R.uniform(30, 46); r1 = r0 + R.uniform(6, 14)
        c.line("gold" if i % 2 else "mid", [(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                                           (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], R.uniform(0.5, 1.2), int(R.uniform(90, 200)))
    if k in ("stone", "sand"):
        for i in range(70):
            a = R.uniform(0, 2 * math.pi); r = R.uniform(44, 58)
            c.disc("mid", cx + math.cos(a) * r, cy + math.sin(a) * r, R.uniform(0.8, 2.4), int(R.uniform(120, 220)))
    if k == "venom":
        for i in range(26):
            a = R.uniform(0, 2 * math.pi); r = R.uniform(48, 58)
            c.disc("core", cx + math.cos(a) * r, cy + math.sin(a) * r, R.uniform(1.2, 3.2), 230)
    g = c.render(PAL[k], bloom=0.75, core_white=0.6, tex=0.4)
    rr, _ = _radial(S * 2, S, S)
    dark = np.clip(1 - np.abs(rr - 104) / 22, 0, 1) * 0.18
    if k in ("fire", "stone"):
        return _dark_under(g, dark)
    return g


# ─────────────────────────────────────────────────────────────── 남는 자국
def crater(k):
    c = Canvas(S, S); R = _rng(_seed(k) % 991 + 7)
    cx = cy = S / 2
    rr, ang = _radial(S * 2, S, S)
    n = _noise(S * 2, 26, _seed(k) % 89, 5)
    edge = np.clip(1 - rr / (100 + 26 * (n - 0.5)), 0, 1)
    if k == "fire":
        for i in range(11):
            _crack(c, cx + R.normal(0, 2), cy + R.normal(0, 2), R.uniform(0, 2 * math.pi), R.uniform(30, 58), 2.4, R, "core")
        c.disc("mid", cx, cy, 11, 170)
        c.disc("core", cx, cy, 5, 255)
        for i in range(60):
            a = R.uniform(0, 2 * math.pi); r = R.uniform(10, 52)
            c.disc("gold", cx + math.cos(a) * r, cy + math.sin(a) * r, R.uniform(0.4, 1.1), int(R.uniform(120, 255)))
        g = c.render(PAL[k], bloom=0.7, core_white=0.5, tex=0.5)
        return _dark_under(g, edge ** 0.6 * (0.55 + 0.35 * n))
    if k == "stone":
        # 어두운 균열은 그을음 쪽에 그린다 (빛나지 않는 흙 균열)
        crack = Image.new("L", (S * 2, S * 2), 0)
        cc = Canvas(S, S)
        for i in range(12):
            _crack(cc, cx, cy, R.uniform(0, 2 * math.pi), R.uniform(34, 60), 3.2, R, "core")
        cl = np.asarray(cc.layers["core"].resize((S * 2, S * 2), Image.LANCZOS), np.float32) / 255
        cl = np.maximum(cl, np.asarray(cc.layers["mid"].resize((S * 2, S * 2), Image.LANCZOS), np.float32) / 255)
        # 가장자리 흙더미 (밝은 먼지 알갱이)
        for i in range(140):
            a = R.uniform(0, 2 * math.pi); r = R.uniform(36, 56)
            c.disc("mid", cx + math.cos(a) * r, cy + math.sin(a) * r, R.uniform(0.8, 2.6), int(R.uniform(60, 150)))
        c.circle("mid", cx, cy, 40, 7, 40)
        g = c.render(PAL[k], bloom=0.35, core_white=0.2, tex=0.7)
        dark = edge ** 0.8 * (0.42 + 0.3 * n) + cl * 0.75
        return _dark_under(g, np.clip(dark, 0, 0.92))
    if k == "sand":
        # 모래가 동심원 물결로 패임 + 가운데 소용돌이
        for i in range(6):
            r = 12 + i * 8
            pts = [(cx + math.cos(t) * (r + 2.5 * math.sin(t * 5 + i)), cy + math.sin(t) * (r + 2.5 * math.sin(t * 5 + i)))
                   for t in np.linspace(0, 2 * math.pi, 120)]
            c.line("mid", pts, 2.2, 150 - i * 12)
        for j in range(3):
            pts = [(cx + math.cos(t + j * 2.09) * t * 4.2, cy + math.sin(t + j * 2.09) * t * 4.2) for t in np.linspace(0.3, 9, 80)]
            c.line("gold", pts, 1.2, 200)
        g = c.render(PAL[k], bloom=0.5, core_white=0.3, tex=0.75)
        return _dark_under(g, edge ** 0.7 * (0.22 + 0.2 * n))
    if k == "venom":
        # 독 웅덩이 튄 자국 (덩어리 + 방울)
        for i in range(16):
            a = R.uniform(0, 2 * math.pi); r = R.uniform(0, 30)
            c.disc("mid", cx + math.cos(a) * r, cy + math.sin(a) * r, R.uniform(8, 17), int(R.uniform(110, 170)))
        for i in range(40):
            a = R.uniform(0, 2 * math.pi); r = R.uniform(30, 58)
            c.disc("core" if i % 3 == 0 else "mid", cx + math.cos(a) * r, cy + math.sin(a) * r, R.uniform(1, 4), int(R.uniform(150, 255)))
        for i in range(12):
            a = R.uniform(0, 2 * math.pi)
            c.line("gold", [(cx + math.cos(a) * 20, cy + math.sin(a) * 20), (cx + math.cos(a) * R.uniform(40, 60), cy + math.sin(a) * R.uniform(40, 60))], 1.4, 170)
        g = c.render(PAL[k], bloom=0.6, core_white=0.35, tex=0.6)
        return _dark_under(g, edge ** 0.7 * 0.3)
    if k == "gale":
        # 바람이 할퀸 소용돌이 자국
        for j in range(7):
            ph = j * 2 * math.pi / 7
            pts = [(cx + math.cos(t + ph) * (6 + t * 6.3), cy + math.sin(t + ph) * (6 + t * 6.3)) for t in np.linspace(0, 7.6, 90)]
            c.line("mid" if j % 2 else "core", pts, 1.8, 180)
        g = c.render(PAL[k], bloom=0.6, core_white=0.7, tex=0.5)
        return _dark_under(g, edge ** 0.7 * 0.16)
    # holy: 빛나는 별 문양
    c.circle("core", cx, cy, 50, 2, 230)
    c.circle("gold", cx, cy, 42, 1.2, 200)
    for i in range(12):
        a = i * math.pi / 6
        L = 58 if i % 2 == 0 else 40
        c.poly("mid", [(cx + math.cos(a) * L, cy + math.sin(a) * L), (cx + math.cos(a + 0.12) * 12, cy + math.sin(a + 0.12) * 12),
                       (cx, cy), (cx + math.cos(a - 0.12) * 12, cy + math.sin(a - 0.12) * 12)], 160)
    c.disc("core", cx, cy, 8, 255)
    return c.render(PAL[k], bloom=0.9, core_white=0.6, tex=0.3)


# ─────────────────────────────────────────────────────────────── 세로 폭발 기둥 (아래 가운데 = 땅)
def burst(k):
    W, H = 64, 128
    c = Canvas(W, H); R = _rng(_seed(k) % 983 + 3)
    cx, by = W / 2, H - 4
    if k == "fire":
        for j, (wd, ht, kk, v) in enumerate(((26, 118, "mid", 120), (18, 100, "mid", 190), (9, 80, "core", 255))):
            for s in range(5):
                x0 = cx + R.uniform(-wd * 0.5, wd * 0.5)
                h = ht * R.uniform(0.7, 1.0)
                pts = []
                for t in np.linspace(0, 1, 40):
                    w_ = wd * 0.5 * (1 - t) ** 0.8 * (0.8 + 0.3 * math.sin(t * 9 + s))
                    xx = x0 + math.sin(t * 6 + s * 1.7) * 4 * t
                    pts.append((xx - w_, by - t * h))
                for t in np.linspace(1, 0, 40):
                    w_ = wd * 0.5 * (1 - t) ** 0.8 * (0.8 + 0.3 * math.sin(t * 9 + s))
                    xx = x0 + math.sin(t * 6 + s * 1.7) * 4 * t
                    pts.append((xx + w_, by - t * h))
                c.poly(kk, pts, v)
        for i in range(70):
            c.disc("gold", cx + R.normal(0, 14), by - R.uniform(10, 124), R.uniform(0.5, 1.4), int(R.uniform(150, 255)))
        return c.render(PAL[k], bloom=0.8, core_white=0.55, tex=0.55)
    if k in ("stone", "sand"):
        # 흙먼지 기둥: 바닥에 퍼지는 먼지 + 위로 솟으며 가늘어지는 연기 + 튀는 돌 (부드럽게 번진 덩어리)
        for i in range(70):
            t = R.uniform(0, 1) ** 1.3
            y = by - 4 - t * 104
            r = (10 - 6 * t) * R.uniform(0.7, 1.2)
            c.disc("mid", cx + R.normal(0, 3 + 6 * (1 - t)), y, r, int(R.uniform(60, 120)))
        for i in range(16):
            c.disc("mid", cx + R.uniform(-22, 22), by - R.uniform(0, 12), R.uniform(5, 9), int(R.uniform(70, 120)))
        for k2 in ("mid",):
            c.layers[k2] = c.layers[k2].filter(ImageFilter.GaussianBlur(10))
            c.layers[k2] = c.layers[k2].point(lambda v: min(255, int(v * 1.7)))
        for i in range(40):
            a = R.uniform(-2.5, -0.65)
            r = R.uniform(8, 70)
            c.disc("gold", cx + math.cos(a) * r * 0.45, by + math.sin(a) * r, R.uniform(0.7, 1.8), int(R.uniform(150, 240)))
        img = c.render(PAL[k], bloom=0.5, core_white=0.15, tex=0.9)
        a = np.asarray(img).astype(np.float32)
        a[..., 3] *= 0.9
        return Image.fromarray(a.astype(np.uint8), "RGBA")
    if k == "venom":
        # 독 물보라: 위로 튀는 방울 줄기들
        for s in range(9):
            ang = math.radians(-90 + R.uniform(-16, 16))
            L = R.uniform(60, 116)
            pts = [(cx + math.cos(ang) * L * t + 3 * t * t * (1 if ang > -math.pi / 2 else -1), by + math.sin(ang) * L * t + 18 * t * t) for t in np.linspace(0, 1, 30)]
            for i in range(len(pts) - 1):
                c.line("mid", [pts[i], pts[i + 1]], 5 * (1 - i / len(pts)) + 0.8, 180)
            c.disc("core", pts[-1][0], pts[-1][1], R.uniform(2, 4), 255)
        c.disc("mid", cx, by - 6, 13, 150)
        for i in range(50):
            c.disc("gold", cx + R.normal(0, 8), by - R.uniform(4, 110), R.uniform(0.6, 2.2), int(R.uniform(140, 255)))
        return c.render(PAL[k], bloom=0.65, core_white=0.4, tex=0.5)
    if k == "gale":
        # 돌풍 회오리
        for j in range(12):
            y = by - j * 9.5
            r = 7 + j * 1.9
            c.d("mid")
            c.circle("mid" if j % 2 else "core", cx + math.sin(j) * 3, y, r, 1.4, 200)
        for i in range(30):
            t = R.uniform(0, 1)
            y = by - t * 112
            r = 7 + t * 22
            a0 = R.uniform(0, 6.28)
            pts = [(cx + math.cos(a0 + u) * r, y + math.sin(a0 + u) * r * 0.25) for u in np.linspace(0, 1.4, 12)]
            c.line("gold", pts, 0.9, 200)
        return c.render(PAL[k], bloom=0.7, core_white=0.7, tex=0.4)
    # holy: 빛기둥
    c.poly("mid", [(cx - 14, by), (cx + 14, by), (cx + 9, by - 124), (cx - 9, by - 124)], 130)
    c.poly("core", [(cx - 5, by), (cx + 5, by), (cx + 3, by - 124), (cx - 3, by - 124)], 255)
    for i in range(40):
        c.disc("gold", cx + R.normal(0, 12), by - R.uniform(0, 124), R.uniform(0.5, 1.5), 230)
    return c.render(PAL[k], bloom=1.0, core_white=0.7, tex=0.2)


# ─────────────────────────────────────────────────────────────── 모델
def flat_model(tex):
    return {"textures": {"0": tex, "particle": tex}, "elements": [{
        "from": [0, 8, 0], "to": [16, 8, 16], "shade": False, "light_emission": 15,
        "faces": {"up": {"uv": [0, 0, 16, 16], "texture": "#0"}, "down": {"uv": [0, 0, 16, 16], "texture": "#0"}}}]}


def tall_model(tex):
    """세로 판 1x2 블록, 가운데 기준 (y -1 ~ +1)"""
    return {"textures": {"0": tex, "particle": tex}, "elements": [{
        "from": [0, -8, 8], "to": [16, 24, 8], "shade": False, "light_emission": 15,
        "faces": {"north": {"uv": [16, 0, 0, 16], "texture": "#0"}, "south": {"uv": [0, 0, 16, 16], "texture": "#0"}}}]}


def export(pack):
    for k in KINDS:
        for part, fn, model in (("shock", shock, flat_model), ("crater", crater, flat_model), ("burst", burst, tall_model)):
            name = f"impact/{part}_{k}"
            pack.item_model(name, model(pack.texture(name, fn(k))))


def preview(path):
    tiles = []
    for k in KINDS:
        row = Image.new("RGBA", (256 * 2 + 128 + 30, 256), (52, 58, 52, 255))
        row.alpha_composite(shock(k), (0, 0))
        row.alpha_composite(crater(k), (266, 0))
        row.alpha_composite(burst(k), (532, 0))
        tiles.append(row)
    out = Image.new("RGBA", (tiles[0].width, 256 * len(tiles)), (0, 0, 0, 255))
    for i, t in enumerate(tiles):
        out.alpha_composite(t, (0, 256 * i))
    out.convert("RGB").save(path)


if __name__ == "__main__":
    preview(sys.argv[1] if len(sys.argv) > 1 else "impact_preview.png")
