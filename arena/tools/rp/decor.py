"""맵 장식 모델 (아이템 디스플레이) — 신상 · 문장 · 점령 링 · 깃발 · 무기 · 소환진

 3D 모델 = modelkit 박스 (한 모델 안에서 22.5° 단위 회전만 사용)
 평면 모델 = 텍스처 한 장 (투명) — 링/깃발/부조/소환진
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import gfx
from modelkit import *

# ── 재질
MARBLE = Mat((226, 222, 212), var=0.05, edge_dark=0.24, top_light=0.18, spots=((196, 192, 186), 0.14, 2))
MARBLE_D = Mat((196, 192, 184), var=0.05, edge_dark=0.24, top_light=0.18, spots=((168, 164, 160), 0.14, 2))
MOSS_MARBLE = Mat((214, 212, 198), var=0.05, edge_dark=0.24, top_light=0.18, spots=((96, 140, 70), 0.22, 2))
GILT = Mat((238, 190, 70), var=0.05, edge_dark=0.36, top_light=0.32, pattern=metal((170, 110, 30), 0.35, 0.0))
BRONZE = Mat((196, 126, 56), var=0.06, edge_dark=0.34, top_light=0.3, pattern=metal((70, 150, 126), 0.3, 0.04))
STEEL = Mat((196, 204, 214), var=0.05, edge_dark=0.3, top_light=0.35, pattern=metal((120, 130, 150), 0.4, 0.0))
IRON_D = Mat((70, 70, 78), var=0.05, edge_dark=0.3, top_light=0.25)
WOOD = Mat((122, 84, 48), var=0.05, edge_dark=0.3, top_light=0.2, pattern=stripes((122, 84, 48), (92, 60, 32), 1, vertical=False))
LEATHER = Mat((110, 66, 36), var=0.05, edge_dark=0.3, top_light=0.2)
RED = Mat((170, 30, 34), var=0.05, edge_dark=0.3, top_light=0.25)
GLOW_GOLD = Mat((255, 222, 110), var=0.05, edge_dark=0.0, top_light=0.0)
GLOW_BLUE = Mat((150, 220, 255), var=0.05, edge_dark=0.0, top_light=0.0)
SAND = Mat((222, 196, 140), var=0.06, edge_dark=0.26, top_light=0.2, spots=((200, 170, 116), 0.2, 2))
LAPIS = Mat((40, 70, 156), var=0.05, edge_dark=0.28, top_light=0.2)
WHEAT = Mat((236, 200, 90), var=0.06, edge_dark=0.3, top_light=0.25, pattern=stripes((236, 200, 90), (200, 150, 50), 1))
LEAF = Mat((90, 150, 60), var=0.05, edge_dark=0.3, top_light=0.2)
FEATHER_W = Mat((244, 244, 236), var=0.04, edge_dark=0.28, top_light=0.2, pattern=stripes((244, 244, 236), (200, 204, 210), 1))


def T(boxes, dx=0, dy=0, dz=0):
    for b in boxes:
        b.frm = b.frm + np.array((dx, dy, dz))
        b.to = b.to + np.array((dx, dy, dz))
        if b.rot:
            ax, ang, org = b.rot
            b.rot = (ax, ang, (org[0] + dx, org[1] + dy, org[2] + dz))
    return boxes


def face_marble(a, w, h):
    cx = w // 2
    ey = int(h * 0.45)
    a[ey, cx - 3:cx - 1, :3] *= 0.6
    a[ey, cx + 1:cx + 3, :3] *= 0.6
    a[ey + 2:ey + 4, cx:cx + 1, :3] *= 0.85
    a[int(h * 0.75), cx - 1:cx + 2, :3] *= 0.7


# ─────────────────────────────────────────────────────────────── 인간형 신상
def humanoid(body=MARBLE, robe=False, helmet=None, head=True, arm_l=True, arm_r=True, raise_r=False):
    """중심 (0,0,0) = 발 가운데. 높이 ~40. 앞 = +Z"""
    b = []
    # 받침 위 발
    if robe:
        b += rbox((-5.5, 0, -3.6), (5.5, 18, 3.6), body, r=1.0)                 # 긴 옷
        b += rbox((-6.2, 0, -4.2), (6.2, 3, 4.2), body, r=0.8)                  # 옷자락
    else:
        b += rbox((-4.2, 0, -2.4), (-0.4, 15, 2.4), body, r=0.8)                # 다리
        b += rbox((0.4, 0, -2.4), (4.2, 15, 2.4), body, r=0.8)
        b += rbox((-4.8, 10, -3.0), (4.8, 17, 3.0), body, r=0.8)               # 가리개(치마)
    b += rbox((-5.2, 16, -3.0), (5.2, 28, 3.2), body, r=1.2)                   # 몸통
    b += rbox((-5.6, 24, -3.3), (5.6, 28.5, 3.5), body, r=0.8)                 # 가슴
    if arm_l:
        b += rbox((5.2, 17, -1.8), (8.4, 28, 1.8), body, r=0.8)
    if arm_r:
        if raise_r:
            b += rbox((-8.4, 26, -1.8), (-5.2, 37, 1.8), body, r=0.8)
        else:
            b += rbox((-8.4, 17, -1.8), (-5.2, 28, 1.8), body, r=0.8)
    if head:
        b += rbox((-2.8, 28.5, -2.8), (2.8, 35, 3.0), body, {"south": face_marble}, r=0.9)
        if helmet == "hoplite":
            b += rbox((-3.2, 31, -3.2), (3.2, 36, 3.4), BRONZE, r=0.8)
            b += [Box((-0.7, 35.5, -4.4), (0.7, 39.5, 3.6), RED)]
        elif helmet == "athena":
            b += rbox((-3.2, 31, -3.2), (3.2, 36, 3.4), GILT, r=0.8)
            b += [Box((-0.7, 35.5, -5.4), (0.7, 41, 3.8), Mat((40, 70, 156)))]
        elif helmet == "ares":
            b += rbox((-3.2, 31, -3.2), (3.2, 36, 3.4), BRONZE, r=0.8)
            b += [Box((-0.7, 35.5, -5.0), (0.7, 40.5, 3.8), RED), Box((-3.3, 29, 1.2), (-2.2, 33, 3.4), BRONZE), Box((2.2, 29, 1.2), (3.3, 33, 3.4), BRONZE)]
        elif helmet == "hermes":
            b += rbox((-3.6, 34, -3.6), (3.6, 36.5, 3.8), GILT, r=0.6)
            b += [Box((-5.2, 34, -1.5), (-3.4, 38.5, 0.5), FEATHER_W, rot=("z", 22.5, (-3.6, 34, 0))),
                  Box((3.4, 34, -1.5), (5.2, 38.5, 0.5), FEATHER_W, rot=("z", -22.5, (3.6, 34, 0)))]
        elif helmet == "demeter":
            for k in range(5):
                x = -2.8 + k * 1.4
                b += [Box((x - 0.4, 34.5, -0.5), (x + 0.4, 38 + (1 if k == 2 else 0), 0.5), WHEAT)]
            b += [Box((-3.0, 34, -3.0), (3.0, 35, 3.2), GILT)]
    return b


def pedestal_none():
    return []


def statue_hoplite(broken=False):
    body = MOSS_MARBLE if broken else MARBLE
    b = humanoid(body, helmet=None if broken else "hoplite", head=not broken, arm_r=True, arm_l=not broken)
    # 창 (오른손, 세움)
    if not broken:
        b += [Box((-7.4, 2, 0.6), (-6.2, 44, 1.8), WOOD), Box((-7.9, 44, 0.1), (-5.7, 47, 2.3), BRONZE)]
        # 둥근 방패 (왼팔 앞)
        b += rbox((5.6, 14, 3.0), (14.6, 30, 4.4), BRONZE, r=2.6)
        b += [Box((8.6, 20, 4.4), (11.6, 24, 5.0), GILT)]
    else:
        b += rbox((6, 0, 3), (13, 6, 4.4), BRONZE, r=1.5)       # 떨어진 방패
    return b


def statue_god(aid):
    if aid == "ares":
        b = humanoid(MARBLE, helmet="ares", raise_r=True)
        b += [Box((-7.4, 24, 0.2), (-6.2, 46, 1.4), WOOD), Box((-7.9, 46, -0.3), (-5.7, 49.5, 1.9), BRONZE)]       # 치켜든 창
        b += rbox((5.6, 14, 3.0), (14.6, 30, 4.4), BRONZE, r=2.6) + [Box((8.2, 19.4, 4.4), (12.0, 24.6, 5.0), RED)]
        b += [Box((-5.4, 18, -3.6), (5.4, 27, -3.0), RED)]          # 망토
    elif aid == "athena":
        b = humanoid(MARBLE, robe=True, helmet="athena")
        b += [Box((-7.4, 2, 0.6), (-6.2, 44, 1.8), GILT), Box((-7.9, 44, 0.1), (-5.7, 47, 2.3), STEEL)]
        b += rbox((5.6, 12, 2.6), (15.0, 28, 4.2), GILT, r=2.6) + [Box((8.8, 18, 4.2), (11.8, 22, 4.8), LAPIS)]
        b += owl_boxes(dx=-10, dy=28, dz=-1, s=0.45)                # 어깨 부엉이
    elif aid == "hermes":
        b = humanoid(MARBLE, helmet="hermes", raise_r=True)
        # 케리케이온 (지팡이 + 뱀 + 날개)
        b += [Box((-7.4, 22, 0.4), (-6.4, 44, 1.4), GILT)]
        for k in range(4):
            y = 25 + k * 4
            b += [Box((-8.6 + (k % 2) * 2.2, y, 0.1), (-6.6 + (k % 2) * 2.2, y + 2, 1.7), LEAF)]
        b += [Box((-11.5, 42, 0.4), (-7.4, 44.4, 1.4), FEATHER_W, rot=("z", 22.5, (-7.4, 43, 1))),
              Box((-6.4, 42, 0.4), (-2.3, 44.4, 1.4), FEATHER_W, rot=("z", -22.5, (-6.4, 43, 1)))]
        # 날개 달린 샌들
        for x in (-2.3, 2.3):
            b += [Box((x - 3.2, 1, -1.6), (x - 2.0, 4.4, 1.4), FEATHER_W, rot=("z", 22.5, (x - 2.0, 1, 0))) if x < 0 else
                  Box((x + 2.0, 1, -1.6), (x + 3.2, 4.4, 1.4), FEATHER_W, rot=("z", -22.5, (x + 2.0, 1, 0)))]
    else:  # demeter
        b = humanoid(MARBLE, robe=True, helmet="demeter")
        # 밀단 (왼팔)
        for k in range(6):
            x = 8.0 + (k % 3) * 1.4
            b += [Box((x - 0.5, 20, 1.6 + (k // 3) * 1.2), (x + 0.5, 35 + (k % 3), 2.6 + (k // 3) * 1.2), WHEAT)]
        b += [Box((7.2, 24, 1.2), (12.0, 25.2, 4.6), GILT)]
        # 횃불 (오른손)
        b += [Box((-7.4, 14, 0.6), (-6.2, 32, 1.8), WOOD), Box((-8.2, 31, -0.2), (-5.4, 34, 2.6), GILT), Box((-7.6, 34, 0.4), (-6.0, 37, 2.0), GLOW_GOLD, glow=True)]
    return b


def owl_boxes(dx=0, dy=0, dz=0, s=1.0, mat=MARBLE):
    b = []
    b += rbox((-4 * s, 0, -3 * s), (4 * s, 9 * s, 3 * s), mat, r=1.2 * s)
    b += rbox((-4.4 * s, 8 * s, -3.4 * s), (4.4 * s, 14 * s, 3.4 * s), mat, r=1.4 * s)
    b += [Box((-3.0 * s, 10.4 * s, 3.3 * s), (-0.6 * s, 12.8 * s, 3.8 * s), GILT), Box((0.6 * s, 10.4 * s, 3.3 * s), (3.0 * s, 12.8 * s, 3.8 * s), GILT),
          Box((-0.5 * s, 9 * s, 3.3 * s), (0.5 * s, 10.6 * s, 4.2 * s), GILT),
          Box((-4.2 * s, 13 * s, -1 * s), (-2.6 * s, 15.6 * s, 1 * s), mat), Box((2.6 * s, 13 * s, -1 * s), (4.2 * s, 15.6 * s, 1 * s), mat)]
    return T(b, dx, dy, dz)


# ─────────────────────────────────────────────────────────────── 문장 (떠 있는 상징)
def bolt(mat=GLOW_GOLD, core=GILT):
    b = []
    segs = [((-1.5, 10, -1), (2.5, 18, 1), 22.5), ((-3.5, 2, -1), (0.5, 11, 1), -22.5), ((-1.0, -6, -1), (3.0, 3, 1), 22.5), ((-2.5, -14, -1), (1.0, -5, 1), -22.5)]
    for lo, hi, ang in segs:
        c = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0)
        b.append(Box(lo, hi, mat, rot=("z", ang, c), glow=True))
    b.append(Box((-0.6, 16, -0.6), (0.6, 20, 0.6), mat, glow=True))
    return b


def sigil(aid):
    if aid == "ares":
        b = rbox((-7, -7, -1), (7, 7, 1), BRONZE, r=2.0)
        b += [Box((-0.6, -14, -0.4), (0.6, 14, 2.2), STEEL, rot=("z", 45, (0, 0, 0))),
              Box((-0.6, -14, -0.4), (0.6, 14, 2.2), STEEL, rot=("z", -45, (0, 0, 0))),
              Box((-2.5, -3, 1), (2.5, 3, 2.4), RED)]
    elif aid == "athena":
        b = owl_boxes(0, -7, 0, 1.0, Mat((200, 220, 240), var=0.03, edge_dark=0.25, top_light=0.2))
        b += [Box((-3.0, 3.4, 2.6), (-0.6, 5.8, 3.4), GLOW_BLUE, glow=True), Box((0.6, 3.4, 2.6), (3.0, 5.8, 3.4), GLOW_BLUE, glow=True)]
    elif aid == "hermes":
        b = [Box((-0.7, -14, -0.7), (0.7, 12, 0.7), GILT)]
        for k in range(5):
            y = -10 + k * 4.4
            b += [Box((-2.4 + (k % 2) * 2.4, y, -1.0), (0.0 + (k % 2) * 2.4, y + 2.4, 1.0), LEAF)]
        b += [Box((-11, 8, -0.5), (-0.7, 12, 0.5), FEATHER_W, rot=("z", 22.5, (-0.7, 10, 0))),
              Box((0.7, 8, -0.5), (11, 12, 0.5), FEATHER_W, rot=("z", -22.5, (0.7, 10, 0))),
              Box((-1.6, 12, -1.6), (1.6, 15, 1.6), GLOW_GOLD, glow=True)]
    else:
        b = []
        for k in range(7):
            x = -4.5 + k * 1.5
            b += [Box((x - 0.4, -12, -0.4), (x + 0.4, 6 + (2 if k == 3 else 0), 0.4), WHEAT, rot=("z", (k - 3) * 7.5 if False else 0, (x, -12, 0)))]
            b += [Box((x - 0.8, 4 + (2 if k == 3 else 0), -0.8), (x + 0.8, 11 + (2 if k == 3 else 0), 0.8), WHEAT)]
        b += [Box((-5.4, -4, -1.2), (5.4, -2, 1.2), GILT), Box((-1.2, 13, -1.2), (1.2, 15.4, 1.2), GLOW_GOLD, glow=True)]
    return b


# ─────────────────────────────────────────────────────────────── 무기 · 소품
def great_sword():
    b = [Box((-1.4, 0, -0.35), (1.4, 26, 0.35), STEEL), Box((-0.3, 0, -0.45), (0.3, 26, 0.45), Mat((230, 236, 244)))]
    b += rbox((-5, 26, -1.2), (5, 28, 1.2), GILT, r=0.5) + [Box((-0.9, 28, -0.9), (0.9, 35, 0.9), LEATHER), Box((-1.4, 35, -1.4), (1.4, 37.2, 1.4), GILT)]
    return T(b, 0, -8, 0)


def spear():
    b = [Box((-0.6, -8, -0.6), (0.6, 30, 0.6), WOOD), Box((-1.6, 30, -0.4), (1.6, 36, 0.4), BRONZE), Box((-0.6, 36, -0.3), (0.6, 39, 0.3), BRONZE)]
    b += [Box((-1.0, 22, -1.0), (1.0, 23, 1.0), RED)]
    return b


def shield():
    b = rbox((-8, -8, -1.2), (8, 8, 1.2), BRONZE, r=3.0)
    b += rbox((-3, -3, 1.0), (3, 3, 2.0), GILT, r=1.0)
    return b


def giant_club():
    b = rbox((-1.4, -2, -1.4), (1.4, 14, 1.4), WOOD, r=0.5) + rbox((-4.2, 12, -4.2), (4.2, 30, 4.2), WOOD, r=1.8)
    b += [Box((-4.5, 16, -4.5), (4.5, 18, 4.5), IRON_D), Box((-4.5, 24, -4.5), (4.5, 26, 4.5), IRON_D)]
    return T(b, 0, -8, 0)


def sphinx_head():
    b = rbox((-9, -6, -8), (9, 12, 8), SAND, r=2.5)                       # 두건 뒤
    b += rbox((-6, -6, 4), (6, 8, 10), SAND, {"south": face_marble}, r=1.8)  # 얼굴 (코 부서짐)
    b += [Box((-9.5, -14, -2), (-6, 4, 6), SAND), Box((6, -14, -2), (9.5, 4, 6), SAND)]   # 두건 자락
    b += [Box((-9, 2, -8.5), (9, 4, 8.5), LAPIS), Box((-9, 7, -8.5), (9, 9, 8.5), LAPIS)]
    return T(b, 0, 2, 0)


def bronze_debris():
    b = rbox((-10, 0, -6), (2, 4, 6), BRONZE, r=1.4)
    b += rbox((0, 0, -3), (9, 10, 5), BRONZE, r=2.0)
    b += [Box((-4, 3, -2), (-1, 6, 1), Mat((255, 170, 60)), glow=True)]
    b += [Box((3, 9, -1), (8, 14, 3), BRONZE, rot=("z", 22.5, (5, 9, 1)))]
    return b


# ─────────────────────────────────────────────────────────────── 평면 텍스처
TEAM_RGB = {"red": (230, 50, 44), "blue": (60, 120, 240), "green": (80, 210, 70), "yellow": (250, 206, 40), "neutral": (240, 230, 200)}


def cap_ring(color, size=256):
    """점령 링: 금빛 이중 원 + 그리스 뇌문 띠 + 팀색 발광"""
    ss = 2
    S = size * ss
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    col = color
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([c - S * 0.47, c - S * 0.47, c + S * 0.47, c + S * 0.47], outline=col + (220,), width=int(S * 0.05))
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.02))
    im.alpha_composite(glow)
    for r, wd, a in ((0.47, 0.012, 255), (0.40, 0.008, 255)):
        d.ellipse([c - S * r, c - S * r, c + S * r, c + S * r], outline=(255, 226, 140, a), width=int(S * wd))
    # 뇌문 (원 둘레)
    n = 40
    for i in range(n):
        a0 = i / n * 2 * math.pi
        for (ra, rb, da) in ((0.415, 0.455, 0), (0.455, 0.455, 0.5), (0.415, 0.415, 0.5)):
            pa = (c + math.cos(a0 + da * 2 * math.pi / n * 0) * S * ra, c + math.sin(a0) * S * ra)
        r1, r2 = S * 0.418, S * 0.452
        a1 = a0 + 2 * math.pi / n * 0.55
        pts = [(c + math.cos(a0) * r1, c + math.sin(a0) * r1), (c + math.cos(a0) * r2, c + math.sin(a0) * r2),
               (c + math.cos(a1) * r2, c + math.sin(a1) * r2), (c + math.cos(a1) * (r1 + (r2 - r1) * 0.45), c + math.sin(a1) * (r1 + (r2 - r1) * 0.45))]
        d.line(pts, fill=col + (255,), width=int(S * 0.006))
    # 안쪽 옅은 채움
    inner = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(inner).ellipse([c - S * 0.39, c - S * 0.39, c + S * 0.39, c + S * 0.39], fill=col + (38,))
    im.alpha_composite(inner)
    # 방위 표식 4
    for k in range(4):
        a = k * math.pi / 2
        x, y = c + math.cos(a) * S * 0.43, c + math.sin(a) * S * 0.43
        r = S * 0.022
        d.polygon([(x, y - r * 1.6), (x + r, y), (x, y + r * 1.6), (x - r, y)], fill=(255, 240, 180, 255))
    return im.resize((size, size), Image.LANCZOS)


def rune_ring(size=256, color=(255, 214, 120)):
    ss = 2
    S = size * ss
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    d.ellipse([c - S * 0.48, c - S * 0.48, c + S * 0.48, c + S * 0.48], outline=color + (255,), width=int(S * 0.01))
    d.ellipse([c - S * 0.40, c - S * 0.40, c + S * 0.40, c + S * 0.40], outline=color + (255,), width=int(S * 0.006))
    f = gfx.font("Galmuri11-Bold.ttf", int(S * 0.05))
    greek = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    n = 24
    for i in range(n):
        a = i / n * 2 * math.pi
        ch = greek[i % len(greek)]
        tile = Image.new("RGBA", (int(S * 0.08), int(S * 0.08)), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((tile.size[0] / 2, tile.size[1] / 2), ch, font=f, fill=color + (255,), anchor="mm")
        tile = tile.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
        x, y = c + math.cos(a) * S * 0.44, c + math.sin(a) * S * 0.44
        im.alpha_composite(tile, (int(x - tile.size[0] / 2), int(y - tile.size[1] / 2)))
    glow = im.filter(ImageFilter.GaussianBlur(S * 0.008))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.alpha_composite(glow); out.alpha_composite(im)
    return out.resize((size, size), Image.LANCZOS)


def summon_circle(color, size=256, seed=1):
    ss = 2
    S = size * ss
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    col = color + (230,)
    for r, wd in ((0.48, 0.012), (0.42, 0.006), (0.30, 0.008), (0.16, 0.006)):
        d.ellipse([c - S * r, c - S * r, c + S * r, c + S * r], outline=col, width=int(S * wd))
    # 별 (7각)
    pts = []
    for i in range(7):
        a = i / 7 * 2 * math.pi * 3 - math.pi / 2
        pts.append((c + math.cos(a) * S * 0.42, c + math.sin(a) * S * 0.42))
    d.line(pts + [pts[0]], fill=col, width=int(S * 0.006))
    rng = np.random.default_rng(seed)
    for i in range(16):
        a = i / 16 * 2 * math.pi
        x, y = c + math.cos(a) * S * 0.36, c + math.sin(a) * S * 0.36
        r = S * 0.018
        d.rectangle([x - r, y - r, x + r, y + r], outline=col, width=int(S * 0.004))
    glow = im.filter(ImageFilter.GaussianBlur(S * 0.01))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.alpha_composite(glow); out.alpha_composite(im)
    a = np.asarray(out).astype(np.float32)
    a[..., 3] *= 0.8
    return Image.fromarray(a.astype(np.uint8)).resize((size, size), Image.LANCZOS)


def cloth(w, h, base, trim, emblem=None, tatter=False, seed=1):
    """깃발/걸개 천 텍스처"""
    ss = 2
    W, H = w * ss, h * ss
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    arr = np.zeros((H, W, 4), np.float32)
    rng = np.random.default_rng(seed)
    for y in range(H):
        t = y / H
        arr[y, :, :3] = np.array(base) * (1.1 - 0.25 * t)
        arr[y, :, 3] = 255
    # 주름 (세로 음영)
    for x in range(W):
        arr[:, x, :3] *= 0.9 + 0.1 * math.sin(x / W * math.pi * 6)
    # 테두리
    b = int(W * 0.06)
    arr[:, :b, :3] = trim; arr[:, -b:, :3] = trim; arr[:int(H * 0.05), :, :3] = trim
    # 아래 제비꼬리 / 찢김
    for x in range(W):
        cut = int(H * 0.12 * (1 - abs(x - W / 2) / (W / 2))) if not tatter else int(rng.integers(0, int(H * 0.25)))
        if cut:
            arr[H - cut:, x, 3] = 0
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    if emblem:
        im.alpha_composite(emblem.resize((int(W * 0.6), int(W * 0.6)), Image.LANCZOS), (int(W * 0.2), int(H * 0.28)))
    return im.resize((w, h), Image.LANCZOS)


def emblem(kind, color):
    S = 256
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    if kind == "bolt":
        pts = [(c + 10, 20), (c - 40, c + 10), (c, c + 10), (c - 20, S - 20), (c + 45, c - 20), (c + 5, c - 20), (c + 30, 20)]
        d.polygon(pts, fill=color + (255,), outline=(60, 30, 10, 255))
    elif kind == "shield":
        d.polygon([(40, 30), (S - 40, 30), (S - 40, 130), (c, S - 20), (40, 130)], fill=color + (255,), outline=(255, 226, 140, 255))
        d.line([(40, 30), (S - 40, 30), (S - 40, 130), (c, S - 20), (40, 130), (40, 30)], fill=(255, 226, 140, 255), width=10)
        star = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = 50 if i % 2 == 0 else 20
            star.append((c + math.cos(a) * r, 115 + math.sin(a) * r))
        d.polygon(star, fill=(255, 246, 210, 255))
    elif kind == "laurel":
        for s in (-1, 1):
            for k in range(8):
                a = math.radians(200 + k * 17) if s < 0 else math.radians(-20 - k * 17)
                x, y = c + math.cos(a) * 80, c - math.sin(a) * 80
                d.ellipse([x - 14, y - 7, x + 14, y + 7], fill=color + (255,))
        pts = [(c + 8, 50), (c - 26, c + 8), (c, c + 8), (c - 12, S - 60), (c + 30, c - 14), (c + 4, c - 14), (c + 22, 50)]
        d.polygon(pts, fill=(255, 226, 120, 255))
    return im


def eagle_relief(S=256):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    col = (232, 226, 214, 255)
    sh = (170, 164, 156, 255)
    for s in (-1, 1):
        for k in range(6):
            x0 = c + s * (18 + k * 16)
            d.polygon([(c + s * 10, 110), (x0 + s * 16, 60 + k * 6), (x0 + s * 22, 150 - k * 4), (c + s * 10, 150)], fill=col if k % 2 else sh)
    d.ellipse([c - 22, 80, c + 22, 170], fill=col)
    d.ellipse([c - 14, 56, c + 14, 90], fill=col)
    d.polygon([(c + 10, 68), (c + 26, 76), (c + 10, 80)], fill=(238, 190, 70, 255))
    pts = [(c + 4, 170), (c - 16, 200), (c, 200), (c - 10, 236), (c + 18, 192), (c + 2, 192), (c + 14, 170)]
    d.polygon(pts, fill=(238, 190, 70, 255))
    return im.filter(ImageFilter.SMOOTH)


# ─────────────────────────────────────────────────────────────── 모델 등록
def plane_model(tex, uv_w=16, uv_h=16, upright=False, both=True, sx=16, sy=16, glow=False):
    if upright:
        e = {"from": [8 - sx / 2, 8 - sy / 2, 8], "to": [8 + sx / 2, 8 + sy / 2, 8],
             "faces": {"north": {"uv": [16, 0, 0, 16], "texture": "#0"}, "south": {"uv": [0, 0, 16, 16], "texture": "#0"}}}
    else:
        e = {"from": [0, 8, 0], "to": [16, 8, 16], "faces": {"up": {"uv": [0, 0, 16, 16], "texture": "#0"}, "down": {"uv": [0, 0, 16, 16], "texture": "#0"}}}
    e["shade"] = False
    if glow:
        e["light_emission"] = 15
    return {"textures": {"0": tex, "particle": tex}, "elements": [e]}


def flag_model(tex):
    """두 장으로 살짝 꺾인 깃발 (장대 = 모델 x=0)"""
    return {"textures": {"0": tex, "particle": tex}, "elements": [
        {"from": [0, 0, 8], "to": [8, 16, 8], "shade": False, "faces": {"north": {"uv": [8, 0, 0, 16], "texture": "#0"}, "south": {"uv": [0, 0, 8, 16], "texture": "#0"}}},
        {"from": [8, 0, 8], "to": [16, 16, 8], "shade": False, "rotation": {"axis": "y", "angle": 22.5, "origin": [8, 8, 8]},
         "faces": {"north": {"uv": [16, 0, 8, 16], "texture": "#0"}, "south": {"uv": [8, 0, 16, 16], "texture": "#0"}}},
    ]}


def box_model(pack, name, boxes, seed=7):
    part = Part(name.replace("/", "_"), boxes)
    at = bake_parts([part], tpu=2, atlas_size=128, seed=seed)
    img = at.image()
    ref = pack.texture(f"decor/{name.replace('/', '_')}", img)
    # 요소 범위를 모델 좌표(-16..32)에 맞게: 전체를 가운데로 (피벗 = 원점)
    js = model_json(part, ref, img.size[0], img.size[1])
    return js, part, img


def box_models():
    """3D 장식 모델 목록: [(이름, 박스, 시드)] — 원점 = 받침 (디스플레이 위치)"""
    L = [("statue/hoplite", T(statue_hoplite(), 0, -22, 0), 11),
         ("statue/hoplite_broken", T(statue_hoplite(True), 0, -22, 0), 12)]
    for a in ("ares", "athena", "hermes", "demeter"):
        L.append((f"statue/god_{a}", T(statue_god(a), 0, -22, 0), 20 + len(a)))
        L.append((f"deco/sigil_{a}", sigil(a), 40 + len(a)))
    L += [("deco/zeus_bolt", bolt(), 50), ("deco/great_sword", great_sword(), 51),
          ("deco/spear", T(spear(), 0, -8, 0), 52), ("deco/shield", shield(), 53),
          ("deco/owl", T(owl_boxes(0, 0, 0, 1.2), 0, -4, 0), 54), ("deco/giant_club", giant_club(), 55),
          ("deco/sphinx_head", sphinx_head(), 56), ("deco/bronze_debris", bronze_debris(), 57)]
    return L


def fit_boxes(boxes, lim=23.5):
    """모델 좌표 범위(±24)에 맞춤: p' = (p + s) * k.  반환 (k, s)"""
    lo = np.min([b.frm for b in boxes], axis=0) - 0.6
    hi = np.max([b.to for b in boxes], axis=0) + 0.6
    s = np.where((lo < -lim) | (hi > lim), -(lo + hi) / 2, 0.0)
    k = min(1.0, (2 * lim) / float(np.max(hi - lo)))
    return k, s


def apply_fit(boxes, k, s):
    for b in boxes:
        b.frm = (b.frm + s) * k
        b.to = (b.to + s) * k
        if b.rot:
            ax, ang, org = b.rot
            b.rot = (ax, ang, tuple((np.array(org, float) + s) * k))
    return boxes


_FIT = {}
DECOR2D_NAMES = {f"deco/{n}_{t}" for n in ("flag", "crest", "cap_ring") for t in ("red", "blue", "green", "yellow")} | {
    "deco/cap_ring_neutral", "deco/rune_ring", "deco/rune_ring_big", "deco/banner_olympus", "deco/war_banner", "deco/wind_ribbon",
    "deco/eagle_relief", "deco/zeus_bolt", "deco/great_sword", "deco/spear", "deco/giant_club", "deco/owl", "deco/shield",
    "deco/sphinx_head", "deco/bronze_debris", "deco/peach", "statue/hoplite", "statue/hoplite_broken"} | {
    f"deco/sigil_{a}" for a in ("ares", "athena", "hermes", "demeter")} | {f"statue/god_{a}" for a in ("ares", "athena", "hermes", "demeter")}
BILLBOARD = {"statue/hoplite", "statue/hoplite_broken", "deco/owl", "deco/sphinx_head", "deco/peach", "deco/zeus_bolt"} | {
    f"deco/sigil_{a}" for a in ("ares", "athena", "hermes", "demeter")} | {f"statue/god_{a}" for a in ("ares", "athena", "hermes", "demeter")}


def model_fit(name):
    """dp 가 디스플레이 변환을 보정할 때 쓴다: (k, s[px])  — 2D 그림(decor2d)으로 바뀐 모델은 보정 없음"""
    import decor2d
    if name in DECOR2D_NAMES:
        return (1.0, np.zeros(3))
    if not _FIT:
        for n, bx, _ in box_models():
            _FIT[n] = fit_boxes(bx)
    return _FIT.get(name, (1.0, np.zeros(3)))


def export(pack):
    """반환: {이름: (종류, 데이터)} 미리보기용 (박스는 원래 좌표)"""
    out = {}
    for name, boxes, seed in box_models():
        k, s = fit_boxes(boxes)
        _FIT[name] = (k, s)
        import copy
        fitted = apply_fit(copy.deepcopy(boxes), k, s)
        js, part, img = box_model(pack, name, fitted, seed)
        pack.item_model(name, js)
        out[name] = ("box", Part(name.replace("/", "_"), boxes), img)
    # 평면
    for team, col in TEAM_RGB.items():
        ref = pack.texture(f"decor/cap_ring_{team}", cap_ring(col))
        pack.item_model(f"deco/cap_ring_{team}", plane_model(ref, glow=True))
    ref = pack.texture("decor/rune_ring", rune_ring())
    pack.item_model("deco/rune_ring", plane_model(ref, glow=True))
    pack.item_model("deco/rune_ring_big", plane_model(ref, glow=True))
    for boss, col in (("talos", (255, 150, 60)), ("sphinx", (120, 200, 255)), ("ladon", (150, 255, 120)), ("cyclops", (255, 200, 120))):
        ref = pack.texture(f"decor/summon_{boss}", summon_circle(col, seed=len(boss)))
        pack.item_model(f"deco/summon_circle_{boss}", plane_model(ref, glow=True))
    ref = pack.texture("decor/eagle_relief", eagle_relief())
    pack.item_model("deco/eagle_relief", plane_model(ref, upright=True))
    olym = cloth(64, 128, (84, 36, 120), (236, 190, 70), emblem("laurel", (236, 200, 90)), seed=3)
    ref = pack.texture("decor/banner_olympus", olym)
    pack.item_model("deco/banner_olympus", plane_model(ref, upright=True, sx=8, sy=16))
    for team, col in TEAM_RGB.items():
        if team == "neutral":
            continue
        em = emblem("shield", col)
        ref = pack.texture(f"decor/crest_{team}", em)
        pack.item_model(f"deco/crest_{team}", plane_model(ref, upright=True))
        fl = cloth(64, 96, tuple(int(v * 0.85) for v in col), (240, 220, 160), emblem("shield", tuple(min(255, v + 40) for v in col)), seed=len(team))
        ref = pack.texture(f"decor/flag_{team}", fl)
        pack.item_model(f"deco/flag_{team}", flag_model(ref))
    wb = cloth(48, 128, (150, 20, 24), (40, 20, 16), emblem("shield", (60, 20, 16)), tatter=True, seed=9)
    ref = pack.texture("decor/war_banner", wb)
    pack.item_model("deco/war_banner", plane_model(ref, upright=True, sx=6, sy=16))
    rb = cloth(32, 128, (120, 220, 230), (250, 250, 250), None, tatter=True, seed=10)
    ref = pack.texture("decor/wind_ribbon", rb)
    pack.item_model("deco/wind_ribbon", flag_model(ref))
    return out

STATUE_Y = 22 / 16      # 신상 모델 원점 → 발바닥 (배율 1 기준 블록)
