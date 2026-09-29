"""상점 화면 배경 (6줄 상자 176x222 → 2배 352x444) — 인벤토리 제목의 폰트 글리프로 화면 전체를 덮는다

 칸 배치 (Skript a50 과 같아야 함)
   1줄: 머리띠 (제목 · 코인)                          2~3줄 + 4줄 앞 2칸: 전설 무기 16 (보라)
   4줄: 30 독 물약 · 31~34 보스 무기 (진홍) · 35 도약    5줄: 37~44 장비 · 소모품 (청동)
   6줄: 45~48 · 50~52 소모품, 49 광물 일괄 판매 (초록), 53 보유 코인 (금)
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

K = 2
W, H = 176, 222
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

LEGEND = set(range(10, 17)) | set(range(19, 26)) | {28, 29}
BOSS = {31, 32, 33, 34}
GEAR = set(range(37, 45)) | {30, 35, 45, 46, 47, 48, 50, 51, 52}
SELL = {49}
COIN = {53}

FRAME = {"legend": ((150, 90, 230), (70, 30, 120)), "boss": ((220, 60, 50), (110, 16, 16)),
         "gear": ((200, 150, 80), (100, 64, 30)), "sell": ((90, 210, 110), (20, 90, 40)), "coin": ((255, 210, 80), (140, 90, 10)),
         "inv": ((150, 120, 90), (70, 52, 38))}


def noise(w, h, s, seed):
    r = np.random.default_rng(seed)
    a = r.random((max(2, h // s), max(2, w // s))).astype(np.float32)
    return np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255


def wood(w, h, seed=1):
    """짙은 호두나무 판"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n = noise(w, h, 6, seed) * 0.6 + noise(w, h, 24, seed + 1) * 0.4
    grain = np.sin((yy * 0.9 + n * 18) * 0.55) * 0.5 + 0.5
    base = np.array((58, 38, 26), np.float32)
    col = base[None, None] * (0.75 + 0.35 * grain[..., None]) * (0.85 + 0.3 * n[..., None])
    return col


def stone(w, h, seed=2):
    n = noise(w, h, 4, seed) * 0.5 + noise(w, h, 16, seed + 3) * 0.5
    base = np.array((44, 40, 52), np.float32)
    return base[None, None] * (0.8 + 0.45 * n[..., None])


ART = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))), "art", "weapons")


def art(name, size, alpha=1.0, glow=None, rot=0):
    """사용자 무기 그림 (128px) → size 픽셀, 빛 번짐 추가"""
    import os
    f = os.path.join(ART, f"{name}.png")
    im = Image.open(f).convert("RGBA") if os.path.exists(f) else Image.new("RGBA", (128, 128))
    if rot:
        im = im.rotate(rot, resample=Image.NEAREST, expand=True)
    im = im.resize((size, size), Image.NEAREST)
    if alpha < 1:
        a = np.asarray(im).astype(np.float32).copy(); a[..., 3] *= alpha
        im = Image.fromarray(a.astype(np.uint8))
    if glow:
        g = Image.new("RGBA", im.size, glow + (0,))
        m = im.split()[3].filter(ImageFilter.GaussianBlur(size / 16))
        g.putalpha(m.point(lambda v: min(255, int(v * 1.3))))
        out = Image.new("RGBA", im.size); out.alpha_composite(g); out.alpha_composite(im)
        return out
    return im


def build():
    S = K
    Wp, Hp = W * S, H * S
    im = Image.fromarray(np.clip(wood(Wp, Hp), 0, 255).astype(np.uint8)).convert("RGBA")

    def paste(src, x, y):
        im.alpha_composite(src, (int(x), int(y)))

    # ── 상자 영역 배경: 어두운 무기고 + 가운데 보라 마력 빛 + 흐릿한 거대 무기 그림들
    area = Image.fromarray(np.clip(stone(162 * S, 110 * S), 0, 255).astype(np.uint8)).convert("RGBA")
    glow = Image.new("RGBA", area.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([20 * S, -10 * S, 142 * S, 70 * S], fill=(140, 70, 230, 120))
    gd.ellipse([40 * S, 50 * S, 122 * S, 90 * S], fill=(230, 60, 50, 90))
    area.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18 * S)))
    for name, x, y, sz, rot in (("blackiron", -8, -20, 110, 0), ("dragon", 70, -18, 104, 90), ("b_talos", 20, 30, 96, 0), ("b_cyclops", 90, 36, 96, 90)):
        area.alpha_composite(art(name, sz * S, 0.22, rot=rot), (x * S, y * S))
    paste(area, 7 * S, 16 * S)
    d = ImageDraw.Draw(im)

    def R(x0, y0, x1, y1, fill=None, outline=None, width=1):
        d.rectangle([x0 * S, y0 * S, x1 * S - 1, y1 * S - 1], fill=fill, outline=outline, width=width * S if width else 0)

    # ── 머리띠: 왕실 보라 휘장 + 금 테 + 양쪽에 전설 무기 그림 교차 + 가운데 왕관
    ban = np.zeros((36 * S, W * S, 3), np.float32)
    n = noise(W * S, 36 * S, 5, 9)
    yy = np.mgrid[0:36 * S, 0:W * S][0].astype(np.float32) / (36 * S)
    ban[:] = np.array((60, 26, 96), np.float32)[None, None] * (0.7 + 0.4 * n[..., None]) * (1.15 - 0.4 * yy[..., None])
    im.paste(Image.fromarray(np.clip(ban, 0, 255).astype(np.uint8)).convert("RGBA"), (0, 0))
    for name, x, rot in (("thunder", -6, 0), ("phoenix", 10, 90), ("peachwood", 142, 0), ("tiger", 128, 90)):
        paste(art(name, 44 * S, 1.0, glow=(255, 210, 120), rot=rot), x * S, -6 * S)
    d = ImageDraw.Draw(im)
    R(0, 34, W, 36, fill=(214, 168, 70))
    R(0, 36, W, 37, fill=(110, 70, 20))
    # 왕관
    cx, cy = W * S / 2, 10 * S
    crown = [(cx - 16 * S, cy + 8 * S), (cx - 16 * S, cy - 2 * S), (cx - 9 * S, cy + 3 * S), (cx, cy - 7 * S), (cx + 9 * S, cy + 3 * S), (cx + 16 * S, cy - 2 * S), (cx + 16 * S, cy + 8 * S)]
    d.polygon(crown, fill=(240, 190, 60), outline=(90, 50, 10), width=S)
    for gx, gc in ((-9, (200, 30, 50)), (0, (60, 120, 230)), (9, (40, 180, 90))):
        d.ellipse([cx + (gx - 2) * S, cy + 3 * S, cx + (gx + 2) * S, cy + 7 * S], fill=gc)
    f = ImageFont.truetype(FONT, 12 * S)
    t = "왕국 무기고"
    tw = d.textlength(t, font=f)
    x = (W * S - tw) / 2
    for dx in range(-2, 3, 2):
        for dy in range(-2, 3, 2):
            d.text((x + dx, 19 * S + dy), t, font=f, fill=(30, 10, 40))
    d.text((x, 19 * S), t, font=f, fill=(255, 222, 120))
    # ── 테두리 (금 이중 테 + 모서리 보석)
    R(0, 0, W, H, outline=(24, 14, 8), width=1)
    R(1, 1, W - 1, H - 1, outline=(214, 168, 70), width=1)
    R(2, 2, W - 2, H - 2, outline=(110, 70, 20), width=1)
    for (gx, gy) in ((4, 4), (W - 5, 4), (4, H - 5), (W - 5, H - 5)):
        d.ellipse([(gx - 3) * S, (gy - 3) * S, (gx + 3) * S, (gy + 3) * S], fill=(214, 168, 70))
        d.ellipse([(gx - 2) * S, (gy - 2) * S, (gx + 2) * S, (gy + 2) * S], fill=(190, 30, 50))

    def slot(x, y, kind, a=210):
        hi, lo = FRAME[kind]
        R(x, y, x + 18, y + 18, fill=lo)
        R(x, y, x + 17, y + 1, fill=hi)
        R(x, y, x + 1, y + 17, fill=hi)
        inner = Image.new("RGBA", (16 * S, 16 * S), (14, 10, 18, a))
        ig = ImageDraw.Draw(inner)
        ig.ellipse([1 * S, 1 * S, 15 * S, 15 * S], fill=tuple(int(v * 0.35) for v in hi) + (a,))
        inner = inner.filter(ImageFilter.GaussianBlur(2 * S))
        im.alpha_composite(inner, ((x + 1) * S, (y + 1) * S))
        # 모서리 금 못
        for ox, oy in ((1, 1), (16, 1), (1, 16), (16, 16)):
            d.point([((x + ox) * S, (y + oy) * S)], fill=(255, 230, 150))

    # ── 상자 칸 + 빈 칸 장식 (구역 표시 그림)
    side = {9: ("thunder", (180, 220, 255)), 17: ("wind", (140, 255, 170)), 18: ("staff", (200, 150, 255)), 26: ("blackiron", (255, 110, 110)),
            27: ("b_sphinx", (255, 220, 120)), 36: (None, None)}
    for idx in range(9, 54):
        r, c = divmod(idx, 9)
        x, y = 7 + 18 * c, 17 + 18 * r
        kind = "legend" if idx in LEGEND else "boss" if idx in BOSS else "sell" if idx in SELL else "coin" if idx in COIN else "gear" if idx in GEAR else None
        if kind:
            slot(x, y, kind)
        elif idx in side and side[idx][0]:
            paste(art(side[idx][0], 20 * S, 1.0, glow=side[idx][1]), (x - 1) * S, (y - 1) * S)
        else:
            # 물약 병 그림 (장비 줄 표시)
            px, py = (x + 9) * S, (y + 10) * S
            d.ellipse([px - 5 * S, py - 3 * S, px + 5 * S, py + 7 * S], fill=(200, 50, 60), outline=(240, 230, 220), width=S)
            d.rectangle([px - 2 * S, py - 8 * S, px + 2 * S, py - 3 * S], fill=(210, 220, 230))
            d.rectangle([px - 3 * S, py - 9 * S, px + 3 * S, py - 7 * S], fill=(150, 100, 60))
    # 구역 나누는 금선 + 이름표
    fs = ImageFont.truetype(FONT, 5 * S)
    for yline, label, col in ((71, "보스 전용", (255, 120, 110)), (89, "장비 · 물약", (255, 210, 140))):
        R(8, yline, 168, yline + 1, fill=(214, 168, 70))
    # ── 플레이어 가방 (아래): 양피지
    parch = np.zeros((90 * S, 166 * S, 3), np.float32)
    n2 = noise(166 * S, 90 * S, 6, 21)
    parch[:] = np.array((70, 52, 36), np.float32)[None, None] * (0.85 + 0.3 * n2[..., None])
    paste(Image.fromarray(np.clip(parch, 0, 255).astype(np.uint8)).convert("RGBA"), 5 * S, 127 * S)
    d = ImageDraw.Draw(im)
    R(5, 127, 171, 128, fill=(214, 168, 70))
    for r in range(3):
        for c in range(9):
            slot(7 + 18 * c, 139 + 18 * r, "inv", 235)
    for c in range(9):
        slot(7 + 18 * c, 197, "inv", 235)
    return im


def preview(path):
    im = build()
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    bg.convert("RGB").resize((im.width * 2, im.height * 2), Image.NEAREST).save(path)


if __name__ == "__main__":
    import sys
    preview(sys.argv[1])
