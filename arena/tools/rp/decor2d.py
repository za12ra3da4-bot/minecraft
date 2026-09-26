"""맵 디스플레이 — 수묵 붓그림 (512 에 그려 줄임, 배경 투명)

 깃발 · 현판 · 인장 · 비석 · 석등 · 점령 고리 · 소환진 · 팔괘 고리 · 천도복숭아 …
 모두 먹 담채 + 마른 붓 외곽선 + 붓글씨(나눔붓) — 마인크래프트 블록 느낌 대신 그린 그림처럼
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

from ink import stroke, wash, colorize, line_path, circle_path
from telegraphs import over

S = 512
YY, XX = np.mgrid[0:S, 0:S].astype(np.float32)
FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache", "fonts", "NanumBrush.ttf")
INK = ((26, 22, 26), (4, 2, 6), (84, 78, 84))
WHITE = ((246, 242, 232), (200, 194, 180), (255, 255, 250))
GOLD = ((222, 170, 60), (126, 76, 14), (255, 230, 150))
STONE = ((150, 150, 146), (70, 70, 72), (214, 212, 204))
STONE_D = ((112, 112, 110), (48, 48, 50), (170, 168, 162))
JADE = ((60, 160, 120), (14, 70, 52), (160, 232, 200))
TEAM = {"red": ((196, 36, 34), (96, 8, 10), (250, 120, 100)), "blue": ((44, 92, 190), (12, 30, 90), (130, 170, 250)),
        "green": ((50, 150, 70), (12, 64, 24), (140, 220, 150)), "yellow": ((226, 176, 40), (130, 86, 8), (255, 226, 130)),
        "neutral": ((236, 232, 220), (150, 146, 136), (255, 255, 250))}
TEAM_WORD = {"red": "주작", "blue": "청룡", "green": "현무", "yellow": "황룡"}
ALTAR = {"ares": ("화염", ((236, 80, 36), (120, 16, 8), (255, 190, 110))), "athena": ("백옥", ((210, 226, 220), (96, 130, 120), (255, 255, 255))),
         "hermes": ("청풍", ((50, 190, 170), (8, 84, 76), (170, 255, 236))), "demeter": ("녹림", ((70, 160, 60), (16, 70, 18), (170, 236, 150)))}


def rng(seed):
    return np.random.default_rng(seed)


def noise(seed, sigma=3.0):
    n = ndimage.gaussian_filter(rng(seed).random((S, S)).astype(np.float32), sigma)
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


def streak(seed, ang=90):
    n = rng(seed).random((S, S)).astype(np.float32)
    n = ndimage.rotate(ndimage.gaussian_filter(ndimage.rotate(n, ang, reshape=False, mode="wrap"), (0.6, 10)), -ang, reshape=False, mode="wrap")
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


def poly(pts):
    im = Image.new("L", (S, S), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=255)
    return np.asarray(im) > 127


def ellipse(cx, cy, rx, ry):
    return ((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2 <= 1


def rect(x0, y0, x1, y1):
    return (XX >= x0) & (XX <= x1) & (YY >= y0) & (YY <= y1)


def fill(mask, col, seed, shade=None, strength=0.6, grain=0.25, alpha=1.0, ang=90):
    m = mask.astype(np.float32)
    dens = m * strength + wash(m, seed, 0.5, 2.0) * 0.35 + (streak(seed + 1, ang) - 0.5) * grain * m
    if shade is not None:
        dens = dens + shade * m
    dens = np.clip(dens, 0, 1) * np.clip(ndimage.gaussian_filter(m, 0.8) * 1.4, 0, 1)
    return colorize(dens, alpha, *col)


def edge(mask, w, seed, ink=INK, dry=0.35):
    m = mask.astype(bool)
    din = ndimage.distance_transform_edt(m)
    dout = ndimage.distance_transform_edt(~m)
    ww = w * (0.65 + 0.7 * noise(seed, 5))
    band = np.clip(ww - np.where(m, din, dout * 1.6) + 0.5, 0, 1)
    br = streak(seed + 7)
    band *= np.where(br < dry * 0.5, 0.25, 1.0) * (0.8 + 0.3 * br)
    return colorize(np.clip(band * 1.1, 0, 1), 1.0, *ink)


def dense(pts, step=0.8):
    out = []
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i], float), np.array(pts[i + 1], float)
        n = max(2, int(np.linalg.norm(b - a) / step))
        out += [tuple(a + (b - a) * k / n) for k in range(n)]
    out.append(tuple(pts[-1]))
    return out


def brush(pts, width, seed, col=INK, alpha=1.0, **kw):
    d = stroke(S, dense(pts), width, seed=seed, **kw)
    return colorize(d, alpha, *col), d


def glow(dens, col, sigma=7, k=1.2):
    g = np.clip(ndimage.gaussian_filter(dens.astype(np.float32), sigma) * k, 0, 1)
    out = np.zeros((S, S, 4), np.float32)
    out[..., :3] = col
    out[..., 3] = g * 210
    return out


def text_mask(txt, cx, cy, size, vertical=False, spacing=0.92):
    """붓글씨 글자 마스크 (나눔붓)"""
    ft = ImageFont.truetype(FONT, int(size))
    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    if vertical:
        n = len(txt)
        y0 = cy - size * spacing * n / 2
        for i, ch in enumerate(txt):
            bb = d.textbbox((0, 0), ch, font=ft)
            w, h = bb[2] - bb[0], bb[3] - bb[1]
            d.text((cx - w / 2 - bb[0], y0 + i * size * spacing + (size * spacing - h) / 2 - bb[1]), ch, font=ft, fill=255)
    else:
        bb = d.textbbox((0, 0), txt, font=ft)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        d.text((cx - w / 2 - bb[0], cy - h / 2 - bb[1]), txt, font=ft, fill=255)
    return np.asarray(im).astype(np.float32) / 255


def ink_text(txt, cx, cy, size, seed, col=INK, vertical=False, dry=0.5):
    m = text_mask(txt, cx, cy, size, vertical)
    br = streak(seed, 80 + (seed % 20))
    holes = (br < 0.18 * dry) & (ndimage.distance_transform_edt(m > 0.5) < size * 0.05)
    dens = np.clip(m * (0.86 + 0.22 * br) - holes * 0.7, 0, 1)
    dens = np.maximum(dens, ndimage.gaussian_filter(dens, 1.2) * 0.75)
    return colorize(dens, 1.0, *col), dens


def splatter(seed, cx, cy, rmin, rmax, n=30, big=3.0):
    R = rng(seed)
    m = np.zeros((S, S), np.float32)
    for _ in range(n):
        a = R.random() * 6.283
        r = rmin + (rmax - rmin) * R.random() ** 0.7
        x, y = cx + np.cos(a) * r, cy + np.sin(a) * r
        rad = 0.8 + R.random() ** 3 * big
        m = np.maximum(m, np.clip(1.4 - np.hypot(XX - x, YY - y) / rad, 0, 1))
    return m


def arc_pts(cx, cy, r, a0, a1, n=240):
    return [(cx + math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))) * r, cy + math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))) * r) for i in range(n)]


def to_img(layers, out=(256, 256), crop=None):
    arr = over(*layers)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    if crop:
        im = im.crop(crop)
    return im.resize(out, Image.LANCZOS)


# ═══════════════════════════════════════════════════════════ 천 · 깃발 · 현판
def cloth_shape(x0, y0, x1, y1, tail=60, notch=True):
    """늘어진 깃발 천: 윗변 곧게, 아래는 제비꼬리"""
    mid = (x0 + x1) / 2
    pts = [(x0, y0), (x1, y0), (x1, y1)]
    if notch:
        pts += [(mid + (x1 - mid) * 0.35, y1 - tail * 0.2), (mid, y1 - tail), (mid - (mid - x0) * 0.35, y1 - tail * 0.2)]
    pts += [(x0, y1)]
    return poly(pts)


def flag(team):
    """팀 깃발 (flag_model: 장대 = 왼쪽 가장자리) — 팀색 천 + 흰 원 안 붓글씨 두 글자"""
    col = TEAM[team]
    cl = cloth_shape(40, 70, 470, 470, 70)
    border = cl & ~cloth_shape(70, 100, 440, 440, 60)
    L = [fill(cl, col, 1, shade=(YY - 70) / 900, strength=0.7), fill(border, ((40, 34, 30), (8, 6, 6), (110, 100, 90)), 2, strength=0.75), edge(cl, 3, 3)]
    circ = ellipse(255, 250, 120, 120)
    L += [fill(circ, WHITE, 4, strength=0.8, grain=0.1), edge(circ, 2.4, 5)]
    L.append(ink_text(TEAM_WORD[team], 255, 252, 104, 6, vertical=True)[0])
    L.append(brush([(40, 60), (40, 490)], 14, 7, ((70, 44, 26), (20, 10, 6), (140, 96, 60)), dry=0.3, pool=0.1, bristles=10)[0])
    L += [brush([(34, 56), (46, 56)], 22, 8, GOLD, dry=0.2, pool=0.2, bristles=8)[0]]
    return to_img(L)


def banner_temple():
    """대전 기둥 긴 족자 깃발 (8x16) — 먹빛 비단 + 금테 + 세로 '천하쟁패'"""
    cl = cloth_shape(136, 20, 376, 500, 50)
    inner = cloth_shape(156, 40, 356, 470, 40)
    L = [fill(cl, ((40, 36, 44), (8, 6, 10), (100, 94, 110)), 11, strength=0.75), fill(cl & ~inner, GOLD, 12, strength=0.7), edge(cl, 3, 13)]
    t, d = ink_text("천하쟁패", 256, 238, 92, 14, col=GOLD, vertical=True)
    L += [glow(d, (255, 210, 120), 5, 0.6), t]
    seal = rect(226, 420, 286, 462)
    L += [fill(seal, ((200, 30, 30), (110, 8, 8), (250, 110, 90)), 15, strength=0.8), ink_text("印", 256, 441, 30, 16, WHITE)[0]]
    return to_img(L, (128, 256), crop=(128, 0, 384, 512))


def war_banner():
    """화염 제단 전쟁 깃발 (6x16) — 찢어진 붉은 천 + 먹 '화' + 불길 붓획"""
    R = rng(21)
    pts = [(166, 20), (346, 20), (346, 400)]
    for k in range(7):
        pts.append((346 - k * 30, 440 + R.random() * 60 * (k % 2)))
    pts.append((166, 420))
    cl = poly(pts)
    L = [fill(cl, TEAM["red"], 22, shade=(YY - 20) / 700, strength=0.72), edge(cl, 3, 23)]
    for k in range(5):
        x = 190 + k * 34
        L.append(brush([(x, 470), (x + 10, 420), (x - 6, 380), (x + 8, 330)], 10, 24 + k, ((255, 170, 60), (180, 60, 10), (255, 230, 150)), dry=0.6, pool=0.1, taper=(0.1, 0.6))[0])
    L.append(ink_text("화", 256, 200, 170, 30)[0])
    return to_img(L, (96, 256), crop=(160, 0, 352, 512))


def wind_ribbon():
    """청풍 제단 긴 바람 띠 (flag_model) — 비취 띠 물결 + '풍'"""
    L = []
    top, bot = [], []
    for i in range(60):
        x = 40 + i * 7.5
        w = 60 - i * 0.6
        y = 250 + math.sin(i / 7) * 40
        top.append((x, y - w)); bot.append((x, y + w))
    cl = poly(top + bot[::-1])
    L += [fill(cl, JADE, 31, strength=0.65, ang=0), edge(cl, 2.6, 32)]
    for k in range(3):
        L.append(brush([(60 + i * 7, 250 + math.sin(i / 7) * 40 + (k - 1) * 22) for i in range(0, 58, 3)], 3.5, 33 + k, ((200, 255, 236), (60, 160, 140), (255, 255, 255)), dry=0.6, pool=0)[0])
    L.append(ink_text("풍", 140, 250, 120, 36)[0])
    return to_img(L)


def crest(team):
    """본진 문장: 팀색 원판 + 금 붓 고리 + 흰 붓글씨 한 글자"""
    col = TEAM[team]
    disc = ellipse(256, 256, 200, 200)
    L = [fill(disc, col, 41, shade=(YY - 256) / 900, strength=0.72), edge(disc, 3.5, 42)]
    L.append(brush(arc_pts(256, 256, 214, -80, 260), 18, 43, GOLD, dry=0.5, pool=0.4, bristles=18)[0])
    L.append(brush(arc_pts(256, 256, 170, 100, 400), 5, 44, GOLD, dry=0.6, pool=0, bristles=6)[0])
    L.append(ink_text(TEAM_WORD[team][0], 256, 262, 250, 45, WHITE)[0])
    return to_img(L)


def plaque():
    """대전 현판 (eagle_relief 자리) — 검은 옻칠 판 + 금테 + 금 붓글씨 '천하제일'"""
    board = rect(26, 176, 486, 336)
    inner = rect(46, 192, 466, 320)
    L = [fill(board, GOLD, 51, strength=0.7), fill(inner, ((34, 28, 32), (6, 4, 6), (90, 80, 86)), 52, strength=0.8, ang=0), edge(board, 3, 53), edge(inner, 2, 54)]
    for x in (26, 486):
        L.append(brush([(x, 170), (x, 342)], 10, 55 + x, GOLD, dry=0.3, pool=0.2, bristles=8)[0])
    t, d = ink_text("천하제일", 256, 258, 104, 56, GOLD)
    L += [glow(d, (255, 210, 110), 5, 0.7), t]
    return to_img(L)


# ═══════════════════════════════════════════════════════════ 바닥 원 (점령 · 소환 · 팔괘)
def ring_ground(col, seed, marks=8, word=None):
    L = [brush(arc_pts(256, 256, 228, -70 + seed * 13, 262 + seed * 13), 22, seed, col, dry=0.55, pool=0.45, taper=(0.15, 0.9), bristles=24)[0],
         brush(arc_pts(256, 256, 192, 110, 430), 6, seed + 1, col, dry=0.6, pool=0.1, bristles=8)[0]]
    for k in range(marks):
        a = math.radians(k / marks * 360 + 11)
        L.append(brush([(256 + math.cos(a) * 150, 256 + math.sin(a) * 150), (256 + math.cos(a) * 178, 256 + math.sin(a) * 178)], 9, seed + 10 + k, col, dry=0.4, pool=0.3, bristles=8)[0])
    wash_ = wash(ellipse(256, 256, 190, 190), seed + 30, 0.18, 8)
    L.insert(0, colorize(wash_, 0.45, *col))
    if word:
        L.append(ink_text(word, 256, 256, 150, seed + 40, col)[0])
    return to_img(L)


TRIGRAMS = ["111", "110", "101", "100", "011", "010", "001", "000"]


def bagua_ring(seed=60, col=GOLD):
    """공중에서 도는 팔괘 고리"""
    L = [brush(arc_pts(256, 256, 236, 0, 358), 10, seed, col, dry=0.5, pool=0.2, bristles=12)[0],
         brush(arc_pts(256, 256, 150, 180, 538), 6, seed + 1, col, dry=0.6, pool=0.1, bristles=8)[0]]
    for k, tg in enumerate(TRIGRAMS):
        a = k / 8 * 2 * math.pi
        ca, sa = math.cos(a), math.sin(a)
        for j, bit in enumerate(tg):
            r = 170 + j * 20
            half = 34
            tx, ty = -sa, ca
            cx, cy = 256 + ca * r, 256 + sa * r
            segs = [(-half, half)] if bit == "1" else [(-half, -8), (8, half)]
            for s0, s1 in segs:
                L.append(brush([(cx + tx * s0, cy + ty * s0), (cx + tx * s1, cy + ty * s1)], 10, seed + 5 + k * 3 + j, col, dry=0.35, pool=0.2, bristles=8)[0])
    d = sum(l[..., 3] for l in L) / 255
    L.insert(0, glow(d, (255, 220, 130), 6, 0.6))
    return to_img(L)


def summon_circle(boss):
    col = {"talos": ((236, 110, 40), (120, 30, 8), (255, 200, 130)), "sphinx": ((70, 150, 230), (14, 50, 110), (170, 220, 255)),
           "ladon": ((80, 200, 110), (14, 80, 30), (180, 255, 190)), "cyclops": ((200, 150, 80), (100, 60, 20), (250, 220, 160))}[boss]
    word = {"talos": "거신", "sphinx": "석사자", "ladon": "구두룡", "cyclops": "산귀"}[boss]
    L = [colorize(wash(ellipse(256, 256, 236, 236), 70, 0.14, 10), 0.4, *col),
         brush(arc_pts(256, 256, 240, -60, 290), 16, 71, col, dry=0.55, pool=0.4, bristles=20)[0],
         brush(arc_pts(256, 256, 206, 120, 470), 7, 72, col, dry=0.5, pool=0.1, bristles=10)[0],
         brush(arc_pts(256, 256, 96, 30, 380), 8, 73, col, dry=0.5, pool=0.2, bristles=10)[0]]
    for k in range(12):
        a = math.radians(k * 30)
        L.append(brush([(256 + math.cos(a) * 110, 256 + math.sin(a) * 110), (256 + math.cos(a + 0.2) * 196, 256 + math.sin(a + 0.2) * 196)], 6, 74 + k, col, dry=0.5, pool=0.2, bristles=6)[0])
    t, d = ink_text(word, 256, 258, 70, 90, col)
    L += [t]
    return to_img(L)


# ═══════════════════════════════════════════════════════════ 인장 · 비석 · 석등 · 소품
def seal(word, col, seed, size=210):
    """공중에서 도는 빛나는 글자 인장 (제단 · 대전 꼭대기)"""
    L = [brush(arc_pts(256, 256, 226, -80 + seed, 250 + seed), 20, seed, col, dry=0.5, pool=0.5, bristles=22)[0]]
    t, d = ink_text(word, 256, 262, size, seed + 1, col)
    L += [t]
    dd = d + L[0][..., 3] / 255
    L.insert(0, glow(dd, col[2], 10, 0.9))
    return to_img(L)


def stele(word, col, seed, motif=None, broken=False):
    """비석: 지붕돌 + 몸돌(글자 새김) + 받침 — 아래쪽 = 발 (model 바닥)"""
    body = rect(176, 110, 336, 450)
    cap = poly([(150, 110), (362, 110), (340, 76), (256, 56), (172, 76)])
    base = poly([(140, 452), (372, 452), (386, 500), (126, 500)])
    if broken:
        R = rng(seed)
        cut = [(176, 170 + R.random() * 40)]
        for k in range(1, 8):
            cut.append((176 + k * 23, 150 + R.random() * 70))
        cut.append((336, 190))
        body = body & ~poly(cut + [(336, 100), (176, 100)])
        cap = np.zeros_like(body)
    L = [fill(base, STONE_D, seed, shade=(YY - 452) / 200, strength=0.7), edge(base, 2.6, seed + 1),
         fill(body, STONE, seed + 2, shade=-(XX - 176) / 900, strength=0.6, grain=0.3), edge(body, 3, seed + 3)]
    if cap.any():
        L += [fill(cap, STONE_D, seed + 4, strength=0.7, ang=0), edge(cap, 3, seed + 5)]
    # 이끼 · 금
    moss = (noise(seed + 6, 9) > 0.7) & (body | base)
    L.append(colorize(wash(moss, seed + 7, 0.4, 3), 0.8, (90, 130, 60), (30, 60, 20), (150, 190, 110)))
    L.append(brush([(250, 300), (262, 340), (252, 380), (268, 430)], 3, seed + 8, dry=0.6, pool=0, bristles=4)[0])
    if motif is not None:
        L += motif
    t, d = ink_text(word, 256, 290 if not broken else 320, 118 if len(word) <= 2 else 96, seed + 9, col, vertical=True)
    if col is not INK:
        L.append(glow(d, col[2], 5, 0.8))
    L.append(t)
    return to_img(L)


def flames(seed):
    out = []
    R = rng(seed)
    for k in range(9):
        x = 150 + k * 27 + R.random() * 10
        out.append(brush([(x, 500), (x + 12, 440), (x - 8, 380), (x + 10, 320 - (k % 3) * 30)], 12, seed + k, ((255, 150, 50), (190, 50, 10), (255, 230, 150)), dry=0.6, pool=0.1, taper=(0.1, 0.5), bristles=10)[0])
    return out


def pine(seed):
    out = []
    out.append(brush([(420, 500), (430, 380), (410, 260), (440, 150)], 16, seed, ((80, 56, 36), (20, 10, 6), (150, 110, 70)), dry=0.5, pool=0.2, bristles=14)[0])
    for k, (y, L_) in enumerate(((180, 90), (250, 110), (320, 80))):
        out.append(brush([(430, y), (430 + L_ * 0.5, y - 12)], 5, seed + 1 + k, ((80, 56, 36), (20, 10, 6), (150, 110, 70)), dry=0.5, pool=0, bristles=6)[0])
        m = ellipse(430 + L_ * 0.3, y - 20, L_ * 0.45, 18)
        out.append(colorize(wash(m, seed + 10 + k, 0.6, 3), 0.95, (50, 110, 60), (10, 40, 16), (120, 180, 110)))
    return out


def lantern():
    """석등: 받침 · 기둥 · 화사석(불빛) · 옥개(치켜든 처마) · 보주 — 아래 = 발"""
    L = []
    parts = [(poly([(186, 470), (326, 470), (340, 500), (172, 500)]), STONE_D), (rect(226, 330, 286, 470), STONE),
             (poly([(196, 300), (316, 300), (300, 332), (212, 332)]), STONE_D), (rect(202, 196, 310, 300), STONE)]
    for i, (m, c) in enumerate(parts):
        L += [fill(m, c, 100 + i, shade=-(XX - 200) / 800, strength=0.65), edge(m, 2.8, 110 + i)]
    win = rect(230, 218, 282, 280)
    L += [glow(win.astype(np.float32), (255, 190, 90), 16, 2.2), fill(win, ((255, 210, 120), (230, 130, 40), (255, 245, 200)), 120, strength=0.8, grain=0.1)]
    roof = poly([(140, 196), (372, 196), (390, 178), (330, 170), (292, 140), (220, 140), (182, 170), (122, 178)])
    L += [fill(roof, STONE_D, 121, strength=0.7, ang=0), edge(roof, 3, 122)]
    top = ellipse(256, 124, 18, 20)
    L += [fill(top, STONE, 123), edge(top, 2, 124)]
    moss = (noise(125, 9) > 0.72) & (roof | parts[0][0])
    L.append(colorize(wash(moss, 126, 0.4, 3), 0.8, (90, 130, 60), (30, 60, 20), (150, 190, 110)))
    return to_img(L)


def peach():
    """천도복숭아 (황금 사과 자리) — 분홍 · 금빛 담채 + 잎 두 장"""
    body = ellipse(256, 290, 150, 140) | ellipse(256, 230, 110, 100)
    shade = np.clip(1 - np.hypot(XX - 210, YY - 230) / 260, 0, 1)
    L = [glow(body.astype(np.float32), (255, 220, 140), 14, 0.8),
         fill(body, ((246, 170, 120), (200, 80, 60), (255, 236, 190)), 130, shade=-shade * 0.4, strength=0.6), edge(body, 3, 131)]
    L.append(brush([(256, 180), (262, 290), (250, 400)], 4, 132, ((200, 90, 70), (120, 30, 20), (250, 150, 120)), dry=0.6, pool=0, bristles=4)[0])
    for k, (a, b) in enumerate((((256, 150), (150, 90)), ((256, 150), (360, 110)))):
        leaf = poly([a, ((a[0] + b[0]) / 2, a[1] - 40), b, ((a[0] + b[0]) / 2, a[1] + 16)])
        L += [fill(leaf, JADE, 133 + k, strength=0.7), edge(leaf, 2, 135 + k)]
    L.append(brush([(256, 170), (256, 130)], 8, 137, ((90, 60, 36), (30, 16, 8), (150, 110, 70)), dry=0.3, pool=0.1)[0])
    return to_img(L)


def club():
    """거인의 곤봉 (세워 박힘) — 아래 = 땅"""
    body = poly([(236, 500), (276, 500), (300, 300), (330, 120), (256, 40), (182, 120), (212, 300)])
    L = [fill(body, ((120, 84, 50), (50, 28, 12), (180, 140, 96)), 140, shade=-(XX - 200) / 700, strength=0.65), edge(body, 3.5, 141)]
    R = rng(142)
    for k in range(9):
        y = 90 + k * 26
        x = 256 + (40 - k * 3) * (1 if k % 2 else -1)
        sp = poly([(x - 10, y), (x + 10, y + 4), (x + (26 if k % 2 else -26), y - 8)])
        L += [fill(sp, STONE_D, 150 + k), edge(sp, 1.6, 160 + k)]
    for y in (330, 400):
        band = rect(214, y, 298, y + 16) & body
        L += [fill(band, ((70, 70, 76), (20, 20, 24), (140, 140, 150)), 170 + y), edge(band, 1.8, 171 + y)]
    return to_img(L)


def shield():
    disc = ellipse(256, 256, 200, 200)
    L = [fill(disc, ((150, 100, 50), (70, 40, 14), (210, 170, 110)), 180, shade=(YY - 256) / 900, strength=0.7), edge(disc, 3.5, 181)]
    L.append(brush(arc_pts(256, 256, 186, 0, 358), 14, 182, GOLD, dry=0.4, pool=0.2, bristles=14)[0])
    yin = (ellipse(256, 256, 120, 120) & ((XX < 256) | ellipse(256, 196, 60, 60))) & ~ellipse(256, 316, 60, 60)
    L += [fill(ellipse(256, 256, 120, 120), WHITE, 183, strength=0.75), fill(yin, INK, 184, strength=0.8), edge(ellipse(256, 256, 120, 120), 2.5, 185)]
    L += [fill(ellipse(256, 196, 16, 16), WHITE, 186), fill(ellipse(256, 316, 16, 16), INK, 187)]
    return to_img(L)


def gear_debris():
    """부서진 청동 톱니 (거신 투기장)"""
    ang = np.degrees(np.arctan2(YY - 300, XX - 256))
    rr = np.hypot(XX - 256, YY - 300)
    teeth = (np.mod(ang + 360, 30) < 15) & (rr < 190)
    g = ((rr < 160) | teeth) & ~(rr < 60) & (ang < 110)
    L = [fill(g, ((190, 120, 50), (90, 50, 14), (240, 190, 120)), 190, shade=-(rr / 900), strength=0.7), edge(g, 3, 191)]
    patina = (noise(192, 8) > 0.66) & g
    L.append(colorize(wash(patina, 193, 0.5, 3), 0.85, (70, 150, 126), (20, 70, 56), (150, 220, 196)))
    return to_img(L)


def upright_weapon(wid):
    """상점 무기 그림을 세워서 (날이 위, 손잡이가 아래) — 투기장 · 제단에 꽂힌 무기"""
    import weapons2d
    im = weapons2d.paint(wid, 512).rotate(45, resample=Image.BICUBIC, expand=True)
    w, h = im.size
    im = im.crop((w / 2 - 256, h / 2 - 256, w / 2 + 256, h / 2 + 256))
    return im.resize((256, 256), Image.LANCZOS)


# ═══════════════════════════════════════════════════════════ 등록 (기존 모델 이름 그대로 → 맵 · 데이터팩 수정 없이 교체)
def upright_model(ref, x0, y0, x1, y1, glow=False):
    e = {"from": [x0, y0, 8], "to": [x1, y1, 8], "shade": False,
         "faces": {"north": {"uv": [16, 0, 0, 16], "texture": "#0"}, "south": {"uv": [0, 0, 16, 16], "texture": "#0"}}}
    if glow:
        e["light_emission"] = 15
    return {"textures": {"0": ref, "particle": ref}, "elements": [e]}


def flat_model(ref):
    e = {"from": [0, 8, 0], "to": [16, 8, 16], "shade": False, "light_emission": 15,
         "faces": {"up": {"uv": [0, 0, 16, 16], "texture": "#0"}, "down": {"uv": [0, 0, 16, 16], "texture": "#0"}}}
    return {"textures": {"0": ref, "particle": ref}, "elements": [e]}


def flag_model(ref):
    return {"textures": {"0": ref, "particle": ref}, "elements": [
        {"from": [0, 0, 8], "to": [8, 16, 8], "shade": False, "faces": {"north": {"uv": [8, 0, 0, 16], "texture": "#0"}, "south": {"uv": [0, 0, 8, 16], "texture": "#0"}}},
        {"from": [8, 0, 8], "to": [16, 16, 8], "shade": False, "rotation": {"axis": "y", "angle": 22.5, "origin": [8, 8, 8]},
         "faces": {"north": {"uv": [16, 0, 8, 16], "texture": "#0"}, "south": {"uv": [8, 0, 16, 16], "texture": "#0"}}},
    ]}


STATUE = (-15, -14, 31, 32)       # 신상 자리: 발 = 모델 y -14 (데이터팩이 22/16 올림)
GROUND0 = (-8, 0, 24, 32)         # 꽂힌 무기 · 곤봉: 땅 = 모델 y 0 (데이터팩이 8/16 올림)
PLANE_NAMES = set()
BILLBOARD = set()


def export(pack):
    def reg(name, img, kind, box=None, glow=False, bb=False):
        ref = pack.texture("decor2d/" + name.replace("/", "_"), img)
        if kind == "up":
            js = upright_model(ref, *box, glow=glow)
        elif kind == "flat":
            js = flat_model(ref)
        else:
            js = flag_model(ref)
        pack.item_model(name, js)
        PLANE_NAMES.add(name)
        if bb:
            BILLBOARD.add(name)
    for t in ("red", "blue", "green", "yellow"):
        reg(f"deco/flag_{t}", flag(t), "flag")
        reg(f"deco/crest_{t}", crest(t), "up", (0, 0, 16, 16))
        reg(f"deco/cap_ring_{t}", ring_ground(TEAM[t], 20 + len(t), word=TEAM_WORD[t][0]), "flat")
    reg("deco/cap_ring_neutral", ring_ground(((236, 230, 214), (130, 124, 110), (255, 255, 250)), 29), "flat")
    for b in ("talos", "sphinx", "ladon", "cyclops"):
        reg(f"deco/summon_circle_{b}", summon_circle(b), "flat")
    rr = bagua_ring()
    reg("deco/rune_ring", rr, "flat")
    reg("deco/rune_ring_big", rr, "flat")
    reg("deco/banner_olympus", banner_temple(), "up", (4, 0, 12, 16))
    reg("deco/war_banner", war_banner(), "up", (5, 0, 11, 16))
    reg("deco/wind_ribbon", wind_ribbon(), "flag")
    reg("deco/eagle_relief", plaque(), "up", (0, 0, 16, 16))
    for a, (word, col) in ALTAR.items():
        reg(f"deco/sigil_{a}", seal(word, col, 7 + len(a), 150), "up", (-4, -4, 20, 20), glow=True, bb=True)
    reg("deco/zeus_bolt", seal("천", GOLD, 3, 300), "up", (-4, -4, 20, 20), glow=True, bb=True)
    lan = lantern()
    reg("statue/hoplite", lan, "up", STATUE, bb=True)
    reg("statue/hoplite_broken", stele("천하", INK, 220, broken=True), "up", STATUE, bb=True)
    motif = {"ares": flames(300), "athena": [], "hermes": [], "demeter": pine(310)}
    for a, (word, col) in ALTAR.items():
        reg(f"statue/god_{a}", stele(word, col, 230 + len(a), motif[a]), "up", STATUE, bb=True)
    reg("deco/great_sword", upright_weapon("thunder"), "up", GROUND0)
    reg("deco/spear", upright_weapon("phoenix"), "up", GROUND0)
    reg("deco/giant_club", club(), "up", GROUND0)
    reg("deco/owl", lan, "up", (-6, 4, 22, 32), bb=True)
    reg("deco/shield", shield(), "up", (-4, 4, 20, 28))
    reg("deco/sphinx_head", stele("석사자", INK, 240), "up", (-4, 8, 20, 32), bb=True)
    reg("deco/bronze_debris", gear_debris(), "up", (-4, 8, 20, 32))
    reg("deco/peach", peach(), "up", (2, 2, 14, 14), glow=True, bb=True)
