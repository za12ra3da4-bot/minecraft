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

# 페이지별 칸 배치 (Skript a50 과 같아야 함)
PAGES = {
    1: dict(title="전설 무기", legend=set(range(9, 17)) | set(range(18, 26)), boss={29, 30, 31, 32}, gear=set(), sell={34},
            coin={49}, nav={53: "next"}, banners=[(151, 35, 65)], caption=(89, "보스 무기 — 보스를 쓰러뜨리면 보상 상자에서")),
    2: dict(title="장비 · 소모품", legend=set(), boss=set(), gear={10, 11, 12, 13} | set(range(19, 26)) | {28, 29, 30, 31, 33, 34},
            sell={40}, coin={49}, nav={45: "prev", 53: "next"}, banners=[(151, 35, 83)], icons={9: "armor", 18: "potion", 27: "arrow"},
            caption=None),
    3: dict(title="팀 강화 · 함정", legend=set(), boss=set(), gear=set(), sell=set(), team={10, 11, 12, 13, 14, 15, 16}, trap={28, 29, 30},
            coin={49}, nav={45: "prev"}, banners=[],
            icons={9: "up", 27: "trap"},
            caption=[(53, "팀 강화 — 한 명이 사면 팀 전체 적용"), (89, "기지 함정 — 적이 본진에 들어오면 자동 발동")]),
}
FRAME = {"legend": ((150, 90, 230), (70, 30, 120)), "boss": ((220, 60, 50), (110, 16, 16)),
         "gear": ((200, 150, 80), (100, 64, 30)), "sell": ((90, 210, 110), (20, 90, 40)), "coin": ((255, 210, 80), (140, 90, 10)),
         "inv": ((150, 120, 90), (70, 52, 38)), "nav": ((255, 220, 120), (120, 80, 20)),
         "team": ((90, 210, 240), (16, 70, 100)), "trap": ((240, 110, 60), (110, 30, 16))}


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


def build(page=1):
    P = PAGES[page]
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
    t = P["title"]
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

    # ── 상자 칸 (종류별 테)
    for idx in range(9, 54):
        r, c = divmod(idx, 9)
        x, y = 7 + 18 * c, 17 + 18 * r
        kind = ("legend" if idx in P["legend"] else "boss" if idx in P["boss"] else "sell" if idx in P["sell"]
                else "coin" if idx in P["coin"] else "gear" if idx in P["gear"] else "nav" if idx in P["nav"]
                else "team" if idx in P.get("team", ()) else "trap" if idx in P.get("trap", ()) else None)
        if kind:
            slot(x, y, kind)
        if idx in P["nav"]:
            # 넘기기 화살표 (빈칸이어도 눌러짐)
            cx, cy = (x + 9) * S, (y + 9) * S
            if P["nav"][idx] == "next":
                d.polygon([(cx - 4 * S, cy - 5 * S), (cx + 5 * S, cy), (cx - 4 * S, cy + 5 * S)], fill=(255, 226, 130), outline=(60, 30, 6))
            else:
                d.polygon([(cx + 4 * S, cy - 5 * S), (cx - 5 * S, cy), (cx + 4 * S, cy + 5 * S)], fill=(255, 226, 130), outline=(60, 30, 6))

    # 빈 세로줄은 이어진 깃발 장식
    def banner(x, y0, y1):
        R(x + 1, y0 + 1, x + 17, y1, fill=(64, 26, 96))
        cloth = Image.fromarray((noise(16 * S, (y1 - y0) * S, 3, y0 + x) * 60).astype(np.uint8)).convert("L")
        dark = Image.new("RGBA", cloth.size, (20, 6, 34, 0)); dark.putalpha(cloth)
        im.alpha_composite(dark, ((x + 1) * S, (y0 + 1) * S))
        R(x + 1, y0 + 1, x + 2, y1, fill=(214, 168, 70))
        R(x + 16, y0 + 1, x + 17, y1, fill=(214, 168, 70))
        R(x, y0, x + 18, y0 + 2, fill=(150, 100, 40))
        d.polygon([((x + 1) * S, y1 * S), ((x + 17) * S, y1 * S), ((x + 17) * S, (y1 + 5) * S), ((x + 9) * S, (y1 + 1) * S), ((x + 1) * S, (y1 + 5) * S)], fill=(64, 26, 96))
        cx = (x + 9) * S
        for cy in range(y0 + 12, y1 - 6, 24):
            cy *= S
            d.polygon([(cx - 5 * S, cy + 3 * S), (cx - 5 * S, cy - 2 * S), (cx - 2 * S, cy), (cx, cy - 4 * S), (cx + 2 * S, cy), (cx + 5 * S, cy - 2 * S), (cx + 5 * S, cy + 3 * S)], fill=(240, 190, 60))
            d.line([(cx - 5 * S, cy + 6 * S), (cx + 5 * S, cy + 14 * S)], fill=(220, 225, 235), width=S)
            d.line([(cx + 5 * S, cy + 6 * S), (cx - 5 * S, cy + 14 * S)], fill=(220, 225, 235), width=S)
    for bx, y0, y1 in P["banners"]:
        banner(bx, y0, y1)
    # 줄 이름 그림 (2쪽 왼쪽 칸: 갑옷 · 물약 · 화살)
    for idx, kind in P.get("icons", {}).items():
        r, c = divmod(idx, 9)
        cx, cy = (7 + 18 * c + 9) * S, (17 + 18 * r + 9) * S
        if kind == "armor":
            d.polygon([(cx - 7 * S, cy - 5 * S), (cx - 3 * S, cy - 7 * S), (cx - 1 * S, cy - 5 * S), (cx + 1 * S, cy - 5 * S), (cx + 3 * S, cy - 7 * S), (cx + 7 * S, cy - 5 * S),
                       (cx + 5 * S, cy - 1 * S), (cx + 4 * S, cy - 1 * S), (cx + 4 * S, cy + 7 * S), (cx - 4 * S, cy + 7 * S), (cx - 4 * S, cy - 1 * S), (cx - 5 * S, cy - 1 * S)],
                      fill=(190, 198, 212), outline=(40, 30, 20))
        elif kind == "potion":
            d.ellipse([cx - 6 * S, cy - 2 * S, cx + 6 * S, cy + 8 * S], fill=(200, 60, 90), outline=(240, 230, 220), width=S)
            d.rectangle([cx - 2 * S, cy - 7 * S, cx + 2 * S, cy - 2 * S], fill=(210, 220, 230))
            d.rectangle([cx - 3 * S, cy - 8 * S, cx + 3 * S, cy - 6 * S], fill=(150, 100, 60))
        elif kind == "up":
            # 금빛 위 화살표 (강화)
            d.polygon([(cx, cy - 8 * S), (cx + 7 * S, cy - 1 * S), (cx + 3 * S, cy - 1 * S), (cx + 3 * S, cy + 7 * S),
                       (cx - 3 * S, cy + 7 * S), (cx - 3 * S, cy - 1 * S), (cx - 7 * S, cy - 1 * S)], fill=(255, 214, 90), outline=(70, 40, 6))
            d.line([(cx - 1 * S, cy - 5 * S), (cx - 1 * S, cy + 5 * S)], fill=(255, 246, 200), width=S)
        elif kind == "trap":
            # 종 (경보)
            d.polygon([(cx - 6 * S, cy + 5 * S), (cx - 4 * S, cy - 3 * S), (cx - 2 * S, cy - 6 * S), (cx + 2 * S, cy - 6 * S),
                       (cx + 4 * S, cy - 3 * S), (cx + 6 * S, cy + 5 * S)], fill=(230, 170, 50), outline=(70, 30, 6))
            d.rectangle([cx - 7 * S, cy + 5 * S, cx + 7 * S, cy + 6 * S], fill=(180, 110, 30))
            d.ellipse([cx - 2 * S, cy + 6 * S, cx + 2 * S, cy + 9 * S], fill=(120, 60, 20))
            d.line([(cx - 9 * S, cy - 4 * S), (cx - 7 * S, cy - 6 * S)], fill=(255, 90, 60), width=S)
            d.line([(cx + 9 * S, cy - 4 * S), (cx + 7 * S, cy - 6 * S)], fill=(255, 90, 60), width=S)
        elif kind == "arrow":
            d.line([(cx - 6 * S, cy + 6 * S), (cx + 6 * S, cy - 6 * S)], fill=(160, 110, 60), width=S * 2)
            d.polygon([(cx + 7 * S, cy - 7 * S), (cx + 1 * S, cy - 5 * S), (cx + 5 * S, cy - 1 * S)], fill=(210, 215, 225))
            d.polygon([(cx - 7 * S, cy + 7 * S), (cx - 7 * S, cy + 2 * S), (cx - 2 * S, cy + 7 * S)], fill=(240, 240, 235))
    # 설명 글씨 한 줄
    caps = P.get("caption")
    if caps and not isinstance(caps, list):
        caps = [caps]
    for cy, text in caps or []:
        fs = ImageFont.truetype(FONT, 7 * S)
        tw = d.textlength(text, font=fs)
        tx = (W * S - tw) / 2
        d.text((tx + S, (cy + 5) * S + S), text, font=fs, fill=(20, 10, 20))
        d.text((tx, (cy + 5) * S), text, font=fs, fill=(255, 200, 150))
    # 쪽 번호
    fs = ImageFont.truetype(FONT, 7 * S)
    pg = f"{page} / {len(PAGES)}"
    d.text(((7 + 18 * 2 + 3) * S, (17 + 18 * 5 + 5) * S), pg, font=fs, fill=(255, 226, 150))
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


def preview(path, page=1):
    im = build(page)
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    bg.convert("RGB").resize((im.width * 2, im.height * 2), Image.NEAREST).save(path)


if __name__ == "__main__":
    import sys
    preview(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
