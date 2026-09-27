"""상점 아이템 그림 (리소스팩 bg:shop/<id>) — 물약 · 화살 · 장비 · 음식 · 부적 · 판매 버튼 (128px, 무기 그림과 같은 톤)"""
import math

import numpy as np
from PIL import Image

from icon2d import *
from icon2d import S, XX, YY
from weapons_legend2 import M, Aura, finish, stroke, curve, cdisc, ring_mask, GOLD2, DGOLD, SILVER

GLASS = Mat((215, 230, 240), spec=1.0, shin=90, env=0.6, rough=0.01, sky=(255, 255, 255), ground=(110, 130, 150))
CORK = Mat((150, 105, 60), spec=0.15, shin=8, grain="wood", rough=0.3)
STEEL2 = Mat((190, 198, 212), spec=1.0, shin=60, env=0.55, grain="brushed", sky=(255, 255, 255), ground=(40, 44, 54))
STEEL_D = Mat((110, 116, 130), spec=0.9, shin=50, env=0.45, grain="brushed", sky=(200, 210, 230), ground=(20, 22, 28))
DIA = Mat((80, 225, 225), spec=1.0, shin=70, env=0.5, rough=0.02, sky=(220, 255, 255), ground=(10, 70, 80))
DIA_D = Mat((30, 150, 160), spec=0.9, shin=60, env=0.4, rough=0.03)
WOODL = Mat((150, 100, 56), spec=0.15, shin=10, grain="wood", rough=0.3)
FEATH = Mat((240, 240, 235), spec=0.1, shin=6, grain="fur", rough=0.2)
MEAT = Mat((150, 70, 40), spec=0.35, shin=14, grain="stone", rough=0.25)
FAT = Mat((235, 205, 170), spec=0.3, shin=12, rough=0.1)
BONE3 = Mat((236, 228, 206), spec=0.4, shin=20, rough=0.08)
APPLE = Mat((250, 200, 50), spec=1.0, shin=60, env=0.5, rough=0.03, sky=(255, 250, 200), ground=(140, 80, 0), glow=(255, 210, 80))
LEAF2 = Mat((80, 170, 60), spec=0.4, shin=20, rough=0.05)
LEATHER2 = Mat((120, 70, 40), spec=0.2, shin=10, grain="leather", rough=0.25)
AQUA = gem((60, 220, 230))


def liquid(col):
    c = np.array(col, float)
    return Mat(tuple(int(v) for v in c), spec=1.0, shin=70, env=0.35, rough=0.02,
               sky=tuple(int(min(255, v * 1.5 + 60)) for v in c), ground=tuple(int(v * 0.3) for v in c), glow=tuple(int(v) for v in c))


def emblem(c, kind, cx, cy, s, col=(255, 250, 230)):
    """물약 라벨 문양 (밝은 선)"""
    L = lambda pts, w=3.2: c.emissive(line_dens(pts, w * s, local=False), col, 0.8)
    if kind == "speed":      # 날개
        for k in range(3):
            L([(cx - 18 * s, cy + (k * 8 - 8) * s), (cx + 14 * s, cy + (k * 6 - 14) * s)])
    elif kind == "str":      # 주먹 · 칼
        L([(cx, cy - 20 * s), (cx, cy + 16 * s)], 4)
        L([(cx - 10 * s, cy + 6 * s), (cx + 10 * s, cy + 6 * s)], 4)
    elif kind == "regen":    # 하트
        pts = [(cx + 16 * s * math.sin(t) ** 3, cy - s * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))) for t in np.linspace(0, 2 * math.pi, 40)]
        L(pts)
    elif kind == "fire":     # 불꽃
        L([(cx, cy + 16 * s), (cx - 12 * s, cy), (cx - 4 * s, cy - 8 * s), (cx, cy - 22 * s), (cx + 8 * s, cy - 6 * s), (cx + 12 * s, cy + 4 * s), (cx, cy + 16 * s)])
    elif kind == "poison":   # 해골
        c.emissive(cdisc(cx, cy - 4 * s, 12 * s).astype(np.float32) * 0.9, col, 0.6)
        c.ink(cdisc(cx - 5 * s, cy - 5 * s, 3.5 * s).astype(np.float32), (30, 50, 20), 1)
        c.ink(cdisc(cx + 5 * s, cy - 5 * s, 3.5 * s).astype(np.float32), (30, 50, 20), 1)
        L([(cx - 7 * s, cy + 12 * s), (cx + 7 * s, cy + 12 * s)], 4)
    elif kind == "leap":     # 위 화살표
        L([(cx, cy + 18 * s), (cx, cy - 18 * s)], 4)
        L([(cx - 12 * s, cy - 6 * s), (cx, cy - 20 * s), (cx + 12 * s, cy - 6 * s)], 4)
    elif kind == "heal":     # 십자
        L([(cx, cy - 16 * s), (cx, cy + 16 * s)], 6)
        L([(cx - 16 * s, cy), (cx + 16 * s, cy)], 6)


def potion(col, kind, splash=False):
    c, au, r = Canvas(), Aura(), np.random.default_rng(len(kind) * 7 + (3 if splash else 0))
    cx = 256
    liq = liquid(col)
    if splash:
        # 던지는 병: 둥근 몸 + 짧은 목 + 금 고리 (살짝 기울임)
        body = cdisc(cx, 300, 128)
        c.part(body, GLASS, 1, bevel=30)
        c.part(cdisc(cx, 312, 112) & (YY > 222), liq, 2, bevel=26)
        c.part(stroke([(cx - 36, 150), (cx + 36, 150)], 90, 90, local=False) & (YY > 120) & (YY < 186), GLASS, 3, bevel=14)
        c.part(stroke([(cx - 60, 176), (cx + 60, 176)], 22, 22, local=False), GOLD2, 4, bevel=6)
        c.part(stroke([(cx - 30, 108), (cx + 30, 108)], 46, 46, local=False), CORK, 5, bevel=10)
        # 가시 금테 (던지는 병 표시)
        for k in range(8):
            a = math.radians(k * 45 + 22.5)
            x, y = cx + math.cos(a) * 128, 300 + math.sin(a) * 128
            c.part(poly([(x - math.sin(a) * 10, y + math.cos(a) * 10), (x + math.cos(a) * 26, y + math.sin(a) * 26), (x + math.sin(a) * 10, y - math.cos(a) * 10)], local=False), GOLD2, 10 + k, shape="blade")
        cy = 318
    else:
        # 마시는 병: 둥근 바닥 + 긴 목 + 코르크 + 금 목걸이
        c.part(cdisc(cx, 318, 120), GLASS, 1, bevel=30)
        c.part(stroke([(cx, 190), (cx, 110)], 70, 70, local=False), GLASS, 2, bevel=14)
        c.part(cdisc(cx, 328, 104) & (YY > 250), liq, 3, bevel=24)
        c.part(stroke([(cx - 48, 204), (cx + 48, 204)], 20, 20, local=False), GOLD2, 4, bevel=6)
        c.part(stroke([(cx - 30, 92), (cx + 30, 92)], 50, 50, local=False), CORK, 5, bevel=10)
        c.part(stroke([(cx - 42, 118), (cx + 42, 118)], 14, 14, local=False), DGOLD, 6, bevel=4)
        cy = 336
    # 거품 · 반짝임
    for k in range(6):
        c.part(cdisc(cx + r.uniform(-60, 60), cy + r.uniform(-30, 50), r.uniform(5, 11)), Mat((255, 255, 255), spec=1, shin=80, rough=0.01), 20 + k, bevel=4, outline=0)
    c.part(stroke(curve([(cx - 80, cy - 30), (cx - 92, cy + 10), (cx - 74, cy + 60)], 8), 12, 6, local=False), Mat((255, 255, 255), spec=1, shin=80), 30, bevel=3, outline=0)
    # 금 라벨 + 문양
    c.part(cdisc(cx + 20, cy + 16, 44), GOLD2, 40, bevel=10)
    c.part(cdisc(cx + 20, cy + 16, 34), Mat((250, 240, 215), spec=0.2, shin=10, rough=0.1), 41, bevel=6)
    emblem(c, kind, cx + 20, cy + 16, 1.2, tuple(int(v * 0.55) for v in col))
    au.glow(c.sil, col, 14, 0.55)
    for k in range(5):
        a = math.radians(r.uniform(200, 340))
        x0, y0 = cx + math.cos(a) * 150, 300 + math.sin(a) * 150
        au.wisp([(x0, y0), (x0 + math.cos(a) * 40, y0 + math.sin(a) * 40 - 20), (x0 + math.cos(a) * 60, y0 + math.sin(a) * 50 - 50)], r.uniform(10, 16), col, local=False)
    return c, au, dict(outline_col=(20, 16, 22), sparkle=tuple(min(255, int(v * 0.5 + 128)) for v in col))


def arrows(n=3, tip=STEEL2, fletch=FEATH, glow=None, drip=None, quiver=False):
    c, au, r = Canvas(), Aura(), np.random.default_rng(n + (7 if quiver else 0))
    if quiver:
        # 화살통 (가죽 + 금테) 에 화살 여러 대
        for k in range(7):
            x = 200 + k * 26
            c.part(stroke([(x, 330), (x + 60, 60)], 9, 9, local=False), WOODL, 50 + k, bevel=3)
            c.part(poly([(x + 60 - 14, 76), (x + 62, 34), (x + 60 + 14, 70)], local=False), tip, 60 + k, shape="blade")
        c.part(stroke([(180, 410), (360, 130)], 120, 150, local=False), LEATHER2, 1, bevel=24)
        c.part(stroke([(200, 150), (370, 180)], 18, 18, local=False), GOLD2, 2, bevel=6)
        c.part(stroke([(160, 370), (300, 400)], 16, 16, local=False), GOLD2, 3, bevel=6)
        c.part(stroke([(140, 250), (410, 270)], 10, 10, local=False), Mat((90, 50, 30), spec=0.2, shin=10), 4, bevel=3)
        c.part(cdisc(236, 330, 22), GOLD2, 5, bevel=8)
        c.part(cdisc(236, 330, 12), RUBY, 6, bevel=5)
    else:
        for k in range(n):
            off = (k - (n - 1) / 2) * 34
            pts = [(40, off), (500, off)]
            c.part(stroke([(40 + off * 0.4, off), (470 + off * 0.4, off)], 11, 11), WOODL, 10 + k, bevel=3)
            c.part(poly([(462 + off * 0.4, off - 20), (540 + off * 0.4, off), (462 + off * 0.4, off + 20), (476 + off * 0.4, off)]), tip, 20 + k, shape="blade", height=1.0)
            for s_ in (-1, 1):
                c.part(poly([(40 + off * 0.4, off), (110 + off * 0.4, off + s_ * 4), (100 + off * 0.4, off + s_ * 26), (30 + off * 0.4, off + s_ * 24)]), fletch, 30 + k * 2 + s_, bevel=4)
            if glow:
                c.emissive(line_dens([(470 + off * 0.4, off), (540 + off * 0.4, off)], 5), glow, 1.3)
            if drip:
                for j in range(2):
                    c.part(disc(500 + off * 0.4 - j * 20, off + 22 + j * 12, 7 - j * 2), drip, 40 + k * 3 + j, bevel=4)
    col = glow or ((120, 200, 90) if drip else (220, 200, 160))
    au.glow(c.sil, col, 12, 0.45)
    swirl = np.random.default_rng(5)
    return c, au, dict(outline_col=(20, 14, 10), sparkle=(255, 250, 220))


def chestplate(mat, mat_d, trim=GOLD2, gemm=SAPPHIRE):
    c, au = Canvas(), Aura()
    cx = 256
    body = [(cx - 150, 150), (cx - 70, 100), (cx - 40, 140), (cx + 40, 140), (cx + 70, 100), (cx + 150, 150), (cx + 130, 250), (cx + 100, 250), (cx + 96, 430), (cx - 96, 430), (cx - 100, 250), (cx - 130, 250)]
    c.part(smooth_poly(body, 4, local=False), mat, 1, bevel=24)
    c.part(smooth_poly([(cx - 70, 170), (cx + 70, 170), (cx + 64, 400), (cx - 64, 400)], 4, local=False), mat_d, 2, bevel=14)
    for y in (230, 290, 350):
        c.part(stroke([(cx - 66, y), (cx + 66, y)], 8, 8, local=False), trim, 3 + y, bevel=3)
    c.part(stroke([(cx - 150, 150), (cx - 70, 100)], 12, 12, local=False), trim, 10, bevel=4)
    c.part(stroke([(cx + 150, 150), (cx + 70, 100)], 12, 12, local=False), trim, 11, bevel=4)
    c.part(cdisc(cx, 200, 22), trim, 12, bevel=8)
    c.part(cdisc(cx, 200, 13), gemm, 13, bevel=5)
    au.glow(c.sil, (200, 220, 255), 10, 0.3)
    return c, au, dict(outline_col=(16, 16, 22))


def sword_icon():
    c, au = Canvas(), Aura()
    c.part(profile([(20, 11), (120, 11)]), LEATHER2, 1, bevel=6, ang=AX_ANG)
    c.part(disc(18, 0, 16), GOLD2, 2, bevel=8)
    c.part(profile([(120, 60), (140, 60)]), GOLD2, 3, bevel=8)
    c.part(disc(130, 0, 12), SAPPHIRE, 4, bevel=6)
    c.part(profile([(140, 22), (440, 18), (520, 6), (540, 0.5)]), STEEL2, 5, shape="blade", height=1.1, ang=AX_ANG)
    c.part(profile([(150, 5), (470, 3)]), STEEL_D, 6, bevel=2)
    au.glow(c.sil, (200, 220, 255), 10, 0.35)
    return c, au, dict(outline_col=(16, 16, 22))


def steak():
    c, au, r = Canvas(), Aura(), np.random.default_rng(9)
    c.part(smooth_poly([(120, 250), (210, 150), (360, 140), (430, 230), (400, 350), (260, 400), (140, 360)], 8, local=False), FAT, 1, bevel=20)
    c.part(smooth_poly([(145, 255), (220, 172), (350, 165), (405, 235), (380, 330), (262, 376), (160, 340)], 8, local=False), MEAT, 2, bevel=22)
    for k in range(5):
        c.ink(line_dens([(200 + k * 40, 180), (160 + k * 40, 360)], 5, local=False), (60, 26, 14), 0.8)
    c.part(stroke([(330, 250), (470, 120)], 30, 26, local=False), BONE3, 3, bevel=10)
    c.part(cdisc(478, 112, 22), BONE3, 4, bevel=8)
    c.part(cdisc(460, 96, 18), BONE3, 5, bevel=8)
    au.glow(c.sil, (255, 160, 80), 10, 0.3)
    return c, au, dict(outline_col=(30, 12, 8))


def gapple():
    c, au = Canvas(), Aura()
    c.part(smooth_poly([(256, 150), (340, 120), (410, 190), (400, 330), (320, 420), (256, 400), (192, 420), (112, 330), (102, 190), (172, 120)], 10, local=False), APPLE, 1, bevel=40)
    c.part(stroke([(256, 150), (270, 70)], 16, 10, local=False), WOODL, 2, bevel=4)
    c.part(smooth_poly([(275, 100), (340, 60), (380, 80), (330, 120)], 8, local=False), LEAF2, 3, bevel=8)
    c.part(cdisc(180, 210, 20), Mat((255, 255, 240), spec=1, shin=80), 4, bevel=6, outline=0)
    au.glow(c.sil, (255, 210, 80), 16, 0.7)
    return c, au, dict(outline_col=(40, 26, 4), n_sparkle=10)


def ward():
    c, au = Canvas(), Aura()
    c.part(stroke(curve([(160, 60), (256, 30), (352, 60)], 10), 10, 10, local=False), GOLD2, 1, bevel=3)
    c.part(smooth_poly([(256, 100), (380, 200), (340, 380), (256, 460), (172, 380), (132, 200)], 8, local=False), DGOLD, 2, bevel=16)
    c.part(smooth_poly([(256, 130), (350, 210), (320, 360), (256, 420), (192, 360), (162, 210)], 8, local=False), Mat((30, 50, 70), spec=0.6, shin=30, env=0.3), 3, bevel=10)
    c.part(cdisc(256, 270, 50), AQUA, 4, bevel=16)
    for k in range(8):
        a = math.radians(k * 45)
        c.emissive(line_dens([(256 + math.cos(a) * 64, 270 + math.sin(a) * 64), (256 + math.cos(a) * 84, 270 + math.sin(a) * 84)], 3, local=False), (120, 240, 255), 1.0)
    au.glow(c.sil, (80, 220, 240), 14, 0.6)
    return c, au, dict(outline_col=(8, 24, 30), n_sparkle=8, sparkle=(210, 255, 255))


def ore_sell():
    c, au, r = Canvas(), Aura(), np.random.default_rng(12)
    # 가죽 주머니 + 쏟아진 원석 · 보석 + 금화
    c.part(smooth_poly([(150, 250), (200, 180), (312, 180), (362, 250), (380, 400), (256, 450), (132, 400)], 8, local=False), LEATHER2, 1, bevel=24)
    c.part(stroke([(190, 190), (322, 190)], 20, 20, local=False), GOLD2, 2, bevel=6)
    c.part(smooth_poly([(200, 180), (230, 130), (282, 130), (312, 180)], 6, local=False), LEATHER2, 3, bevel=10)
    for k, (x, y, m) in enumerate(((330, 420, DIA), (380, 380, EMERALD), (160, 430, APPLE), (410, 440, Mat((200, 150, 110), spec=0.3, shin=10, grain="stone")), (120, 380, STEEL2))):
        c.part(smooth_poly([(x - 26, y), (x - 8, y - 26), (x + 22, y - 18), (x + 26, y + 10), (x, y + 26), (x - 20, y + 18)], 5, local=False), m, 10 + k, shape="blade", height=0.9)
    for k in range(4):
        c.part(cdisc(220 + k * 30, 470 - k * 4, 22), GOLD2, 20 + k, bevel=8)
    c.emissive(line_dens([(230, 300), (282, 300)], 5, local=False), (255, 230, 120), 1.0)
    au.glow(c.sil, (255, 210, 90), 14, 0.5)
    return c, au, dict(outline_col=(30, 18, 8), n_sparkle=8)


ICONS = {
    "pspeed": lambda: potion((110, 190, 230), "speed"),
    "pstr": lambda: potion((200, 40, 40), "str"),
    "pregen": lambda: potion((220, 90, 180), "regen"),
    "pfire": lambda: potion((240, 150, 40), "fire"),
    "pleap": lambda: potion((60, 230, 90), "leap"),
    "ppoison": lambda: potion((90, 170, 50), "poison", True),
    "heal": lambda: potion((240, 50, 60), "heal", True),
    "arrows": lambda: arrows(3),
    "arrows64": lambda: arrows(quiver=True),
    "spectral": lambda: arrows(3, tip=GOLD2, fletch=Mat((250, 220, 120), spec=0.2, shin=10, grain="fur"), glow=(255, 230, 120)),
    "parrow": lambda: arrows(3, tip=Mat((90, 170, 50), spec=0.8, shin=40, env=0.3), fletch=Mat((120, 200, 80), spec=0.1, shin=6, grain="fur"), drip=gem((90, 200, 50))),
    "iron": lambda: chestplate(STEEL2, STEEL_D),
    "diamond": lambda: chestplate(DIA, DIA_D, SILVER, RUBY),
    "sword": sword_icon,
    "food": steak,
    "gapple": gapple,
    "ward": ward,
    "sell": ore_sell,
}


def paint(k, out=128):
    c, au, opt = ICONS[k]()
    return finish(c, au, out, seed=sum(map(ord, k)), **opt)


def export(pack):
    for k in ICONS:
        ref = pack.texture(f"shop/{k}", paint(k))
        pack.item_model(f"shop/{k}", {"parent": "minecraft:item/generated", "textures": {"layer0": ref}})


def preview(path):
    ks = list(ICONS)
    cols = 6
    rows = (len(ks) + cols - 1) // cols
    sh = Image.new("RGBA", (cols * 272 + 16, rows * 272 + 16), (58, 58, 62, 255))
    for i, k in enumerate(ks):
        sh.alpha_composite(paint(k).resize((256, 256), Image.NEAREST), (16 + (i % cols) * 272, 16 + (i // cols) * 272))
    sh.convert("RGB").save(path)


if __name__ == "__main__":
    import sys
    preview(sys.argv[1])
