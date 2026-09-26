"""맵 디스플레이 · 상점 GUI · 무기 스킬 효과 — 서양 판타지 2D (icon2d, 글자 없음)"""
import math

import numpy as np
from PIL import Image
from scipy import ndimage

from icon2d import *
from icon2d import S, XX, YY

TEAM_CLOTH = {"red": CLOTH_R, "blue": CLOTH_B, "green": CLOTH_G, "yellow": CLOTH_Y}
TEAM_GLOW = {"red": (255, 70, 60), "blue": (80, 140, 255), "green": (80, 230, 110), "yellow": (255, 210, 70)}
ALTAR_GLOW = {"ares": (255, 110, 40), "athena": (200, 230, 255), "hermes": (80, 240, 210), "demeter": (110, 230, 90)}


def R(x0, y0, x1, y1):
    return (XX >= x0) & (XX <= x1) & (YY >= y0) & (YY <= y1)


def D(x, y, r):
    return np.hypot(XX - x, YY - y) <= r


def PL(pts):
    return poly(pts, local=False)


def SP(pts, n=16):
    return smooth_poly(pts, n, local=False)


def LN(pts, w):
    return line_dens(pts, w, local=False)


def cloth_folds(x0, x1, k=5, amp=5.0):
    return np.sin((XX - x0) / (x1 - x0) * math.pi * k) * amp


# ─────────────────────────────────────────── 문장 (팀 상징)
def charge(c, kind, cx, cy, s, seed, mat=GOLD):
    """문장 그림: swords 교차 검 · tower 성탑 · tree 참나무 · crown 왕관 · flame 불꽃 · shield 방패 · wind 소용돌이 · leaf 잎 · sun 태양"""
    if kind == "swords":
        for sg in (-1, 1):
            dx, dy = sg * math.sin(math.radians(45)), -math.cos(math.radians(45))
            px, py = -dy, dx
            tip = (cx + dx * s, cy + dy * s)
            g = (cx - dx * s * 0.42, cy - dy * s * 0.42)
            butt = (cx - dx * s * 0.85, cy - dy * s * 0.85)
            w = s * 0.1
            c.part(PL([(g[0] + px * w, g[1] + py * w), tip, (g[0] - px * w, g[1] - py * w)]), STEEL, seed + sg, shape="blade", height=1.0)
            c.part(LN([(g[0] + px * s * 0.26, g[1] + py * s * 0.26), (g[0] - px * s * 0.26, g[1] - py * s * 0.26)], s * 0.09) > 0.5, mat, seed + 3 + sg, bevel=5)
            c.part(LN([g, butt], s * 0.08) > 0.5, LEATHER, seed + 5 + sg, bevel=4)
            c.part(D(butt[0], butt[1], s * 0.08), mat, seed + 7 + sg, bevel=5)
    elif kind == "tower":
        body = R(cx - s * 0.42, cy - s * 0.35, cx + s * 0.42, cy + s * 0.75)
        for k in range(4):
            x = cx - s * 0.5 + k * s * 0.33
            body |= R(x, cy - s * 0.6, x + s * 0.18, cy - s * 0.3)
        body &= ~(D(cx, cy + s * 0.35, s * 0.18) | R(cx - s * 0.18, cy + s * 0.35, cx + s * 0.18, cy + s * 0.76))
        c.part(body, mat, seed, bevel=7)
        c.part(R(cx - s * 0.08, cy - s * 0.12, cx + s * 0.08, cy + s * 0.08), DSTEEL, seed + 1, bevel=3)
    elif kind == "tree":
        c.part(PL([(cx - s * 0.12, cy + s * 0.8), (cx + s * 0.12, cy + s * 0.8), (cx + s * 0.08, cy), (cx - s * 0.08, cy)]), WOOD, seed, bevel=5)
        crown = D(cx, cy - s * 0.25, s * 0.5) | D(cx - s * 0.38, cy - s * 0.05, s * 0.3) | D(cx + s * 0.38, cy - s * 0.05, s * 0.3) | D(cx, cy - s * 0.62, s * 0.28)
        c.part(crown, mat, seed + 1, bevel=10)
    elif kind == "crown":
        pts = [(cx - s * 0.7, cy + s * 0.45), (cx + s * 0.7, cy + s * 0.45), (cx + s * 0.75, cy - s * 0.35), (cx + s * 0.38, cy + s * 0.02),
               (cx, cy - s * 0.6), (cx - s * 0.38, cy + s * 0.02), (cx - s * 0.75, cy - s * 0.35)]
        c.part(PL(pts), mat, seed, bevel=8)
        c.part(R(cx - s * 0.7, cy + s * 0.3, cx + s * 0.7, cy + s * 0.5), mat, seed + 1, bevel=5)
        for k, g in enumerate((RUBY, SAPPHIRE, EMERALD)):
            c.part(D(cx + (k - 1) * s * 0.42, cy + s * 0.2, s * 0.1), g, seed + 2 + k, bevel=5)
        for x in (-0.75, 0, 0.75):
            c.part(D(cx + x * s, cy - (0.6 if x == 0 else 0.35) * s, s * 0.09), mat, seed + 6 + int(x * 4), bevel=5)
    elif kind == "flame":
        f = SP([(cx, cy - s * 0.95), (cx + s * 0.25, cy - s * 0.35), (cx + s * 0.55, cy - s * 0.55), (cx + s * 0.6, cy + s * 0.2), (cx + s * 0.35, cy + s * 0.7),
                (cx, cy + s * 0.8), (cx - s * 0.35, cy + s * 0.7), (cx - s * 0.6, cy + s * 0.2), (cx - s * 0.45, cy - s * 0.3), (cx - s * 0.2, cy - s * 0.1)])
        c.part(f, Mat((250, 120, 30), spec=0.5, shin=20, rough=0.05, glow=(255, 140, 40)), seed, bevel=16)
        c.part(SP([(cx, cy - s * 0.3), (cx + s * 0.28, cy + s * 0.2), (cx, cy + s * 0.65), (cx - s * 0.28, cy + s * 0.2)]), Mat((255, 230, 120), spec=0.4, shin=20, glow=(255, 220, 120)), seed + 1, bevel=10)
    elif kind == "shield":
        sh = SP([(cx - s * 0.6, cy - s * 0.6), (cx + s * 0.6, cy - s * 0.6), (cx + s * 0.55, cy + s * 0.1), (cx, cy + s * 0.8), (cx - s * 0.55, cy + s * 0.1)], 10)
        c.part(sh, mat, seed, bevel=10)
        c.part(SP([(cx - s * 0.38, cy - s * 0.42), (cx + s * 0.38, cy - s * 0.42), (cx + s * 0.34, cy + s * 0.05), (cx, cy + s * 0.55), (cx - s * 0.34, cy + s * 0.05)], 10), STEEL, seed + 1, bevel=8)
        c.part(D(cx, cy - s * 0.02, s * 0.14), SAPPHIRE, seed + 2, bevel=6)
    elif kind == "wind":
        dens = np.zeros((S, S), np.float32)
        for k in range(3):
            pts = [(cx + math.cos(t + k * 2.09) * s * (0.12 + 0.13 * t), cy + math.sin(t + k * 2.09) * s * (0.12 + 0.13 * t)) for t in np.linspace(0, 5.5, 60)]
            dens = np.maximum(dens, LN(pts, s * 0.12))
        c.part(dens > 0.5, mat, seed, bevel=6)
    elif kind == "leaf":
        lf = SP([(cx, cy - s * 0.85), (cx + s * 0.5, cy - s * 0.3), (cx + s * 0.42, cy + s * 0.3), (cx, cy + s * 0.7), (cx - s * 0.42, cy + s * 0.3), (cx - s * 0.5, cy - s * 0.3)])
        c.part(lf, Mat((90, 190, 70), spec=0.3, shin=16, rough=0.05, glow=(120, 240, 100)), seed, bevel=12)
        c.part(LN([(cx, cy + s * 0.9), (cx, cy - s * 0.6)], 5) > 0.5, WOOD, seed + 1, bevel=3)
    elif kind == "sun":
        rays = np.zeros((S, S), bool)
        for k in range(12):
            a = k / 12 * 2 * math.pi
            rays |= PL([(cx + math.cos(a - 0.14) * s * 0.45, cy + math.sin(a - 0.14) * s * 0.45), (cx + math.cos(a) * s * 0.95, cy + math.sin(a) * s * 0.95),
                        (cx + math.cos(a + 0.14) * s * 0.45, cy + math.sin(a + 0.14) * s * 0.45)])
        c.part(rays, mat, seed, bevel=5)
        c.part(D(cx, cy, s * 0.5), mat, seed + 1, bevel=14)
        c.part(D(cx, cy, s * 0.22), TOPAZ, seed + 2, bevel=8)


TEAM_CHARGE = {"red": "swords", "blue": "tower", "green": "tree", "yellow": "crown"}
ALTAR_CHARGE = {"ares": "flame", "athena": "shield", "hermes": "wind", "demeter": "leaf"}


def banner_cloth(c, x0, y0, x1, y1, mat, seed, tail="swallow"):
    mid = (x0 + x1) / 2
    pts = [(x0, y0), (x1, y0), (x1, y1)]
    if tail == "swallow":
        pts += [(mid + (x1 - mid) * 0.3, y1 - 10), (mid, y1 - 60), (mid - (mid - x0) * 0.3, y1 - 10)]
    elif tail == "point":
        pts += [(mid, y1 + 50)]
    pts += [(x0, y1)]
    m = PL(pts)
    c.part(m, mat, seed, shape="flat", bevel=10, extra_h=cloth_folds(x0, x1, 4, 7), ang=90)
    trim = m & ~ndimage.binary_erosion(m, iterations=10)
    c.part(trim, GOLD, seed + 1, bevel=4, ang=90)
    return m


def flag(team):
    """팀 깃발 (장대 = 왼쪽): 팀색 천 + 금테 + 문장"""
    c = Canvas()
    banner_cloth(c, 44, 60, 470, 440, TEAM_CLOTH[team], 1)
    charge(c, TEAM_CHARGE[team], 257, 235, 130, 10)
    c.part(R(28, 40, 48, 500), WOOD_D, 20, bevel=8, ang=90)
    c.part(D(38, 36, 16), GOLD, 21, bevel=10)
    return c.image()


def crest(team):
    """본진 문장 방패"""
    c = Canvas()
    sh = SP([(70, 60), (442, 60), (430, 280), (256, 470), (82, 280)], 12)
    c.part(sh, GOLD, 1, bevel=12)
    inner = SP([(96, 84), (416, 84), (406, 272), (256, 438), (106, 272)], 12)
    c.part(inner, TEAM_CLOTH[team], 2, shape="flat", bevel=8)
    charge(c, TEAM_CHARGE[team], 256, 240, 120, 10)
    return c.image()


def royal_banner():
    """대전 기둥 긴 깃발 (8x16): 진보라 + 금 왕관 + 금 술"""
    c = Canvas()
    banner_cloth(c, 140, 20, 372, 470, Mat((80, 30, 110), spec=0.08, shin=6, grain="cloth", rough=0.2), 1, tail="point")
    charge(c, "crown", 256, 200, 80, 10)
    charge(c, "sun", 256, 360, 50, 20)
    im = c.image(out=512)
    return im.crop((128, 0, 384, 512)).resize((128, 256), Image.LANCZOS)


def war_banner():
    c = Canvas()
    R_ = rng(4)
    pts = [(170, 20), (342, 20), (342, 400)]
    for k in range(7):
        pts.append((342 - k * 29, 430 + R_.random() * 60 * (k % 2)))
    pts.append((170, 420))
    m = PL(pts)
    c.part(m, CLOTH_R, 1, shape="flat", bevel=10, extra_h=cloth_folds(170, 342, 3, 7))
    charge(c, "flame", 256, 200, 70, 10)
    im = c.image(out=512)
    return im.crop((160, 0, 352, 512)).resize((96, 256), Image.LANCZOS)


def pennant():
    """바람 제단 긴 삼각기 (flag_model)"""
    c = Canvas()
    top, bot = [], []
    for i in range(50):
        x = 40 + i * 9
        w = 70 * (1 - i / 55)
        y = 250 + math.sin(i / 7) * 30
        top.append((x, y - w)); bot.append((x, y + w))
    m = PL(top + bot[::-1])
    c.part(m, Mat((30, 140, 130), spec=0.08, shin=6, grain="cloth", rough=0.2), 1, shape="flat", bevel=8, extra_h=np.sin(XX / 30) * 6)
    trim = m & ~ndimage.binary_erosion(m, iterations=7)
    c.part(trim, GOLD, 2, bevel=3)
    charge(c, "wind", 140, 250, 70, 5)
    return c.image()


def plaque():
    """대전 박공 장식판: 돌판 + 금 월계관 + 왕관"""
    c = Canvas()
    c.part(R(30, 150, 482, 362), STONE, 1, bevel=12)
    c.part(R(50, 168, 462, 344), Mat((96, 94, 90), spec=0.08, shin=6, grain="stone", rough=0.35), 2, shape="flat", bevel=6)
    for sg in (-1, 1):
        for k in range(7):
            a = math.radians(200 + k * 20) if sg < 0 else math.radians(-20 - k * 20)
            x, y = 256 + math.cos(a) * 88 * sg * -1 if False else 256 + math.cos(a) * 88, 256 - math.sin(a) * 74
            lf = SP([(x - 16, y), (x, y - 8), (x + 16, y), (x, y + 8)], 6)
            c.part(lf, GOLD, 10 + k + (sg + 1) * 10, bevel=5)
    charge(c, "crown", 256, 250, 58, 40)
    return c.image()


# ─────────────────────────────────────────── 바닥 마법진 (빛나는 룬 고리)
def magic_circle(color, seed, rings=(236, 200, 120), spokes=12, glyphs=True, center=None):
    c = Canvas()
    dens = np.zeros((S, S), np.float32)
    for k, r in enumerate(rings):
        dens = np.maximum(dens, LN([(256 + math.cos(t) * r, 256 + math.sin(t) * r) for t in np.linspace(0, 2 * math.pi, 240)], 4 if k == 0 else 2.5))
    R_ = rng(seed)
    if glyphs:
        for k in range(24):
            a = k / 24 * 2 * math.pi
            r = (rings[0] + rings[1]) / 2
            x, y = 256 + math.cos(a) * r, 256 + math.sin(a) * r
            ta, tb = -math.sin(a), math.cos(a)
            g = R_.integers(0, 4)
            s = 9
            if g == 0:
                pts = [(x - ta * s, y - tb * s), (x + ta * s, y + tb * s)]
            elif g == 1:
                pts = [(x - ta * s + math.cos(a) * s, y - tb * s + math.sin(a) * s), (x, y), (x + ta * s + math.cos(a) * s, y + tb * s + math.sin(a) * s)]
            elif g == 2:
                pts = [(x - ta * s, y - tb * s), (x + math.cos(a) * s, y + math.sin(a) * s), (x + ta * s, y + tb * s)]
            else:
                pts = [(x - math.cos(a) * s, y - math.sin(a) * s), (x + math.cos(a) * s, y + math.sin(a) * s)]
            dens = np.maximum(dens, LN(pts, 2.4))
    for k in range(spokes):
        a = k / spokes * 2 * math.pi
        dens = np.maximum(dens, LN([(256 + math.cos(a) * rings[2], 256 + math.sin(a) * rings[2]), (256 + math.cos(a + math.pi / spokes) * rings[1], 256 + math.sin(a + math.pi / spokes) * rings[1])], 2.2))
    if spokes:
        # 별 모양 (중심 원 안)
        n = 6
        for k in range(n):
            a0 = k / n * 2 * math.pi; a1 = (k + 2) / n * 2 * math.pi
            dens = np.maximum(dens, LN([(256 + math.cos(a0) * rings[2], 256 + math.sin(a0) * rings[2]), (256 + math.cos(a1) * rings[2], 256 + math.sin(a1) * rings[2])], 2.2))
    c.emissive(dens, color, 1.6)
    if center:
        charge(c, center, 256, 256, 60, seed + 50)
    return c.image(glow_strength=1.2, outline=False)


# ─────────────────────────────────────────── 조각상 · 소품 (아래 = 발)
def obelisk(emblem=None, glow=None, broken=False, seed=1):
    c = Canvas()
    c.part(PL([(150, 450), (362, 450), (380, 505), (132, 505)]), STONE, seed, bevel=10)
    c.part(R(166, 420, 346, 452), Mat((120, 118, 112), spec=0.08, shin=6, grain="stone", rough=0.35), seed + 1, bevel=6)
    body = PL([(190, 420), (322, 420), (304, 110), (256, 50), (208, 110)])
    if broken:
        R_ = rng(seed)
        cut = [(170, 230 + R_.random() * 40)] + [(190 + k * 20, 200 + R_.random() * 70) for k in range(7)] + [(342, 250)]
        body &= ~PL(cut + [(342, 0), (170, 0)])
    c.part(body, STONE, seed + 2, bevel=14)
    moss = (noise(seed + 3, 8) > 0.68) & body
    c.part(moss, Mat((80, 120, 50), spec=0.05, shin=4, grain="stone", rough=0.3), seed + 4, shape="flat", bevel=3)
    if emblem:
        c.part(D(256, 250, 44), GOLD, seed + 5, bevel=10)
        c.part(D(256, 250, 34), Mat((50, 44, 50), spec=0.2, shin=10), seed + 6, shape="flat", bevel=4)
        charge(c, emblem, 256, 250, 28, seed + 10)
    if glow is not None:
        c.glow += np.array(glow, np.float32)[None, None, :] * (ndimage.gaussian_filter(D(256, 250, 30).astype(np.float32), 14))[..., None] * 1.5
    return c.image(glow_strength=1.0)


def brazier():
    """돌기둥 위 쇠 화로 + 불꽃"""
    c = Canvas()
    c.part(PL([(186, 470), (326, 470), (340, 505), (172, 505)]), STONE, 1, bevel=10)
    c.part(PL([(214, 470), (298, 470), (286, 250), (226, 250)]), STONE, 2, bevel=12)
    for y in (300, 420):
        c.part(R(210, y, 302, y + 14), GOLD, 3 + y, bevel=5)
    bowl = SP([(150, 200), (362, 200), (330, 262), (182, 262)], 10)
    c.part(bowl, DSTEEL, 10, bevel=12)
    c.part(R(150, 192, 362, 206), GOLD, 11, bevel=5)
    fire = SP([(180, 196), (200, 120), (226, 150), (240, 70), (262, 130), (284, 60), (300, 140), (320, 110), (334, 196)], 10)
    c.part(fire, Mat((255, 130, 30), spec=0.3, shin=10, rough=0.02, glow=(255, 150, 40)), 12, bevel=30)
    c.part(SP([(210, 196), (236, 140), (258, 170), (284, 120), (304, 196)], 10), Mat((255, 230, 140), spec=0.3, shin=10, glow=(255, 220, 120)), 13, bevel=20)
    return c.image(glow_strength=1.4)


def golden_apple():
    c = Canvas()
    body = D(256, 290, 150) | D(210, 240, 110) | D(302, 240, 110)
    body &= ~D(256, 150, 40)
    c.glow += np.array((255, 210, 80), np.float32)[None, None, :] * ndimage.gaussian_filter(body.astype(np.float32), 16)[..., None] * 0.9
    c.part(body, Mat((240, 190, 50), spec=1.0, shin=50, env=0.45, rough=0.03, glow=None, sky=(255, 245, 200), ground=(120, 70, 10)), 1, bevel=120)
    c.part(PL([(250, 180), (262, 180), (272, 110), (260, 108)]), WOOD_D, 2, bevel=5)
    c.part(SP([(266, 130), (330, 96), (380, 120), (322, 146)], 10), Mat((70, 170, 60), spec=0.3, shin=16, rough=0.05), 3, bevel=10)
    return c.image()


def spiked_club():
    c = Canvas()
    body = PL([(236, 505), (276, 505), (300, 300), (330, 110), (256, 40), (182, 110), (212, 300)])
    c.part(body, WOOD, 1, bevel=24, ang=90)
    for y in (330, 410):
        c.part(R(212, y, 300, y + 16) & body, DSTEEL, 2 + y, bevel=6)
    R_ = rng(3)
    for k in range(10):
        y = 80 + k * 22
        x = 256 + (46 - k * 3) * (1 if k % 2 else -1)
        sp = PL([(x - 9, y - 5), (x + 9, y + 5), (x + (30 if k % 2 else -30), y - 6)])
        c.part(sp, STEEL, 10 + k, shape="blade", height=1)
    return c.image()


def round_shield():
    c = Canvas()
    c.part(D(256, 256, 210), DSTEEL, 1, bevel=10)
    c.part(D(256, 256, 190), WOOD, 2, shape="flat", bevel=6, ang=90)
    for k in range(6):
        x = 76 + k * 72
        c.part(R(x - 2, 70, x + 2, 442) & D(256, 256, 188), WOOD_D, 3 + k, shape="flat", bevel=1)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        c.part(D(256 + math.cos(a) * 200, 256 + math.sin(a) * 200, 9), STEEL, 20 + k, bevel=6)
    c.part(D(256, 256, 70), STEEL, 40, bevel=40)
    c.part(D(256, 256, 22), GOLD, 41, bevel=12)
    return c.image()


def bronze_gear():
    c = Canvas()
    ang = np.degrees(np.arctan2(YY - 300, XX - 256))
    rr = np.hypot(XX - 256, YY - 300)
    teeth = (np.mod(ang + 360, 30) < 15) & (rr < 190)
    g = ((rr < 160) | teeth) & ~(rr < 60) & (ang < 110)
    c.part(g, BRONZE, 1, bevel=14)
    pat = (noise(2, 8) > 0.66) & g
    c.part(pat, Mat((70, 150, 126), spec=0.2, shin=10, grain="stone", rough=0.2), 3, shape="flat", bevel=3)
    return c.image()


def upright_weapon(wid):
    import weapons_w
    im = weapons_w.paint(wid, 512).rotate(45, resample=Image.BICUBIC, expand=True)
    w, h = im.size
    return im.crop((w / 2 - 256, h / 2 - 256, w / 2 + 256, h / 2 + 256)).resize((256, 256), Image.LANCZOS)


def medallion(kind, color):
    """공중에 뜬 빛나는 문장 원판 (제단 · 대전 꼭대기)"""
    c = Canvas()
    c.glow += np.array(color, np.float32)[None, None, :] * ndimage.gaussian_filter(D(256, 256, 180).astype(np.float32), 24)[..., None] * 1.3
    c.part(D(256, 256, 190), GOLD, 1, bevel=14)
    c.part(D(256, 256, 160), Mat((40, 36, 44), spec=0.4, shin=20, env=0.2), 2, shape="flat", bevel=6)
    ring = np.zeros((S, S), np.float32)
    for k in range(16):
        a = k / 16 * 2 * math.pi
        ring = np.maximum(ring, LN([(256 + math.cos(a) * 168, 256 + math.sin(a) * 168), (256 + math.cos(a) * 182, 256 + math.sin(a) * 182)], 3))
    c.emissive(ring, color, 1.2)
    charge(c, kind, 256, 256, 110, 10)
    return c.image(glow_strength=1.2)


# ─────────────────────────────────────────── 무기 스킬 효과 (빛나는 마법진)
WFX = {"wfx_thunder": ((110, 180, 255), "sun"), "wfx_crescent": ((255, 80, 60), None), "wfx_wind": ((80, 255, 180), None),
       "wfx_barrier": ((255, 210, 90), "shield"), "wfx_blood": ((230, 30, 40), None), "wfx_claw": ((170, 110, 255), None),
       "wfx_staff": ((190, 110, 255), None), "wfx_fire": ((255, 130, 40), "flame")}


def skill_fx(name):
    color, center = WFX[name]
    if name == "wfx_crescent":
        c = Canvas()
        dens = np.zeros((S, S), np.float32)
        for k in range(6):
            r = 200 - k * 12
            dens = np.maximum(dens, LN([(256 + math.cos(t) * r, 330 + math.sin(t) * r) for t in np.linspace(math.radians(200 + k * 3), math.radians(340 - k * 3), 80)], 14 - k * 2))
        c.emissive(dens, color, 1.6)
        return c.image(glow_strength=1.3, outline=False)
    if name == "wfx_blood":
        c = Canvas()
        dens = np.maximum(LN([(256, 500), (256, 12)], 22), LN([(236, 470), (240, 60)], 5))
        c.emissive(dens, color, 1.6)
        return c.image(glow_strength=1.3, outline=False)
    if name == "wfx_claw":
        c = Canvas()
        dens = np.zeros((S, S), np.float32)
        for k in range(3):
            x = 160 + k * 96
            dens = np.maximum(dens, LN([(x - 40 + 80 * t + math.sin(t * 3) * 10, 80 + 360 * t) for t in np.linspace(0, 1, 40)], 16))
        c.emissive(dens, color, 1.6)
        return c.image(glow_strength=1.3, outline=False)
    if name == "wfx_wind":
        c = Canvas()
        dens = np.zeros((S, S), np.float32)
        for k in range(3):
            dens = np.maximum(dens, LN([(256 + math.cos(t + k * 2.09) * (20 + 34 * t), 256 + math.sin(t + k * 2.09) * (20 + 34 * t)) for t in np.linspace(0, 6.2, 120)], 12))
        c.emissive(dens, color, 1.6)
        return c.image(glow_strength=1.3, outline=False)
    if name == "wfx_staff":
        return magic_circle(color, 77, rings=(236, 190, 90), spokes=8)
    return magic_circle(color, 60 + len(name), center=center)


# ─────────────────────────────────────────── 상점 GUI (3줄 상자 176x168, 2배)
def shop_panel():
    k = 2
    W_, H_ = 176 * k, 168 * k
    c = Canvas()
    frame = R(0, 0, W_ - 1, H_ - 1)
    c.part(frame, Mat((110, 70, 40), spec=0.1, shin=6, grain="wood", rough=0.3), 1, bevel=8, ang=0)
    parch = R(6, 6, W_ - 7, H_ - 7)
    c.part(parch, Mat((226, 208, 170), spec=0.03, shin=4, grain="stone", rough=0.08), 2, shape="flat", bevel=6)
    for (x, y) in ((6, 6), (W_ - 30, 6), (6, H_ - 30), (W_ - 30, H_ - 30)):
        c.part(R(x, y, x + 24, y + 24) & ~R(x + 6, y + 6, x + 18, y + 18), GOLD, 3 + x + y, bevel=4)
        c.part(D(x + 12, y + 12, 5), RUBY, 4 + x + y, bevel=4)

    def slot(x, y, mat, seed):
        x0, y0 = x * k, y * k
        c.part(R(x0, y0, x0 + 18 * k - 1, y0 + 18 * k - 1) & ~R(x0 + 3, y0 + 3, x0 + 18 * k - 4, y0 + 18 * k - 4), mat, seed, bevel=2)
        c.part(R(x0 + 3, y0 + 3, x0 + 18 * k - 4, y0 + 18 * k - 4), Mat((70, 56, 44), spec=0.02, shin=4, grain="leather", rough=0.1), seed + 1, shape="flat", bevel=2, outline=0)
    for r in range(3):
        for col in range(9):
            i = r * 9 + col
            mat = GOLD if i <= 7 else (Mat((60, 150, 120), spec=0.6, shin=30, env=0.3, rough=0.05) if 10 <= i <= 16 else BRONZE)
            slot(7 + col * 18, 17 + r * 18, mat, 100 + i * 2)
    for r in range(3):
        for col in range(9):
            slot(7 + col * 18, 83 + r * 18, BRONZE, 200 + (r * 9 + col) * 2)
    for col in range(9):
        slot(7 + col * 18, 141, BRONZE, 300 + col * 2)
    c.part(R(14, 145, W_ - 15, 150), GOLD, 400, bevel=2)
    im = c.image(out=512, outline=False)
    return im.crop((0, 0, W_, H_))


# ─────────────────────────────────────────── 등록 (기존 모델 이름 그대로)
def export(pack):
    import decor2d as D2
    for n in list(D2.BILLBOARD):
        pass

    def reg(name, img, kind, box=None, glow=False):
        ref = pack.texture("decor_w/" + name.replace("/", "_"), img)
        if kind == "up":
            js = D2.upright_model(ref, *box, glow=glow)
        elif kind == "flat":
            js = D2.flat_model(ref)
        else:
            js = D2.flag_model(ref)
        pack.item_model(name, js)
    for t in ("red", "blue", "green", "yellow"):
        reg(f"deco/flag_{t}", flag(t), "flag")
        reg(f"deco/crest_{t}", crest(t), "up", (0, 0, 16, 16))
        reg(f"deco/cap_ring_{t}", magic_circle(TEAM_GLOW[t], 20 + len(t)), "flat")
    reg("deco/cap_ring_neutral", magic_circle((230, 226, 210), 29, glyphs=False), "flat")
    for b, col in (("talos", (255, 120, 40)), ("sphinx", (80, 160, 255)), ("ladon", (90, 230, 120)), ("cyclops", (230, 170, 90))):
        reg(f"deco/summon_circle_{b}", magic_circle(col, 30 + len(b), rings=(240, 206, 110), spokes=16), "flat")
    rr = magic_circle((255, 210, 100), 50, rings=(236, 206, 176), spokes=0)
    reg("deco/rune_ring", rr, "flat")
    reg("deco/rune_ring_big", rr, "flat")
    reg("deco/banner_olympus", royal_banner(), "up", (4, 0, 12, 16))
    reg("deco/war_banner", war_banner(), "up", (5, 0, 11, 16))
    reg("deco/wind_ribbon", pennant(), "flag")
    reg("deco/eagle_relief", plaque(), "up", (0, 0, 16, 16))
    for a, kind in ALTAR_CHARGE.items():
        reg(f"deco/sigil_{a}", medallion(kind, ALTAR_GLOW[a]), "up", (-4, -4, 20, 20), glow=True)
        reg(f"statue/god_{a}", obelisk(kind, ALTAR_GLOW[a], seed=5 + len(a)), "up", D2.STATUE)
    reg("deco/zeus_bolt", medallion("crown", (255, 220, 120)), "up", (-4, -4, 20, 20), glow=True)
    br = brazier()
    reg("statue/hoplite", br, "up", D2.STATUE)
    reg("statue/hoplite_broken", obelisk(None, None, broken=True, seed=3), "up", D2.STATUE)
    reg("deco/great_sword", upright_weapon("thunder"), "up", D2.GROUND0)
    reg("deco/spear", upright_weapon("peachwood"), "up", D2.GROUND0)
    reg("deco/giant_club", spiked_club(), "up", D2.GROUND0)
    reg("deco/owl", br, "up", (-6, 4, 22, 32))
    reg("deco/shield", round_shield(), "up", (-4, 4, 20, 28))
    reg("deco/sphinx_head", obelisk("sun", (255, 200, 90), seed=9), "up", (-4, 8, 20, 32))
    reg("deco/bronze_debris", bronze_gear(), "up", (-4, 8, 20, 32))
    reg("deco/peach", golden_apple(), "up", (2, 2, 14, 14), glow=True)
    for name in WFX:
        ref = pack.texture(f"tele/{name}", skill_fx(name))
