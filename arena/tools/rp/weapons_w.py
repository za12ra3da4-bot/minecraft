"""상점 전설 무기 8종 — 서양 판타지 2D 아이콘 (icon2d 렌더러)"""
import math

import numpy as np
from PIL import Image

from icon2d import *


def wrap(c, u0, u1, hw, mat, seed, step=11, tilt=7):
    """손잡이 가죽 감기: 비스듬한 띠 여러 장"""
    for k, u in enumerate(np.arange(u0, u1, step)):
        m = poly([(u, -hw), (u + step * 0.9, -hw), (u + step * 0.9 + tilt, hw), (u + tilt, hw)]) & profile([(u0, hw), (u1, hw)])
        c.part(m, mat, seed + k, shape="round", bevel=4, ang=AX_ANG + 30)


def runes(c, u0, u1, v, color, seed, size=9, width=2.2):
    """룬 문자 (짧은 획 조합)"""
    R = rng(seed)
    dens = np.zeros((S, S), np.float32)
    u = u0
    while u < u1:
        kind = R.integers(0, 5)
        s = size
        if kind == 0:
            pts = [(u, v - s), (u, v + s)]; pts2 = [(u, v), (u + s * 0.8, v - s * 0.7)]
        elif kind == 1:
            pts = [(u, v + s), (u + s * 0.5, v - s), (u + s, v + s)]; pts2 = None
        elif kind == 2:
            pts = [(u, v - s), (u + s, v), (u, v + s)]; pts2 = None
        elif kind == 3:
            pts = [(u, v - s), (u, v + s)]; pts2 = [(u, v - s), (u + s * 0.8, v - s * 0.3), (u, v + s * 0.1)]
        else:
            pts = [(u, v + s), (u + s * 0.5, v - s), (u + s, v + s)]; pts2 = [(u + s * 0.2, v + s * 0.2), (u + s * 0.8, v + s * 0.2)]
        dens = np.maximum(dens, line_dens(pts, width))
        if pts2:
            dens = np.maximum(dens, line_dens(pts2, width))
        u += s * 1.7
    c.emissive(dens, color, 1.4)


def thunder():
    """폭풍의 검: 푸른 번개 룬 롱소드, 금 가드 + 사파이어"""
    c = Canvas()
    pom = disc(58, 0, 17)
    c.part(pom, GOLD, 1, bevel=10)
    c.part(disc(58, 0, 8), SAPPHIRE, 2, bevel=6)
    c.part(profile([(68, 10), (76, 12), (150, 12), (158, 10)]), LEATHER_D, 3, bevel=6)
    wrap(c, 76, 150, 12, LEATHER, 10)
    for u in (74, 152):
        c.part(profile([(u - 3, 13.5), (u + 3, 13.5)]), GOLD, 20 + u, bevel=3)
    guard = smooth_poly([(152, 0), (156, 20), (150, 44), (160, 56), (172, 50), (166, 34), (172, 14), (178, 0),
                         (172, -14), (166, -34), (172, -50), (160, -56), (150, -44), (156, -20)], 10)
    c.part(guard, GOLD, 30, bevel=9)
    c.part(disc(165, 0, 10), SAPPHIRE, 31, bevel=7)
    blade = profile([(178, 17), (200, 19), (420, 16), (480, 12), (515, 6), (530, 0.5)])
    c.part(blade, STEEL, 40, shape="blade", height=1.3, ang=AX_ANG)
    fuller = profile([(190, 4), (430, 3.5), (445, 0.5)])
    c.part(fuller, DSTEEL, 41, shape="flat", bevel=3, ang=AX_ANG)
    runes(c, 200, 420, 0, (90, 170, 255), 42, size=6, width=2.0)
    return c.image(glow_strength=0.9)


def dragon():
    """처형자의 대도끼: 초승달 도끼날 + 뒷날 가시 + 가죽 감은 자루"""
    c = Canvas()
    c.part(profile([(8, 6), (20, 11), (30, 11)]), DSTEEL, 1, bevel=5)
    c.part(profile([(30, 10), (420, 10)]), WOOD_D, 2, bevel=8, ang=AX_ANG)
    wrap(c, 60, 170, 11, LEATHER, 5)
    for u in (56, 172, 330, 400):
        c.part(profile([(u - 4, 12.5), (u + 4, 12.5)]), DSTEEL, 30 + u, bevel=4)
    c.part(profile([(420, 8), (440, 11), (450, 3), (452, 0.5)]), DSTEEL, 3, bevel=6)
    # 도끼날: 자루에서 v- 쪽으로 넓게 퍼지는 수염 도끼날 (위아래로 휘어 뾰족)
    blade = smooth_poly([(352, -10), (340, -30), (318, -62), (312, -96), (330, -120), (372, -112), (412, -118), (448, -104), (452, -72), (440, -34), (424, -10)], 16)
    c.part(blade, STEEL, 40, shape="blade", height=0.45, ang=AX_ANG + 90)
    c.part(smooth_poly([(362, -14), (372, -44), (400, -46), (412, -14)], 8), DSTEEL, 41, shape="flat", bevel=4)
    # 뒷날 가시
    spike = poly([(360, 8), (410, 8), (385, 56)])
    c.part(spike, STEEL, 42, shape="blade", height=0.8)
    c.part(profile([(345, 13), (425, 13)]), GOLD, 43, bevel=6)
    c.part(disc(385, 0, 9), RUBY, 44, bevel=6)
    runes(c, 355, 405, -70, (255, 90, 50), 45, size=7)
    return c.image(glow_strength=0.7)


def ndimage_erode(m, it):
    from scipy import ndimage as nd
    return nd.binary_erosion(m, iterations=it)


def wind():
    """질풍의 단검: 휘어진 은빛 날 + 깃털 가드 + 에메랄드"""
    c = Canvas()
    c.part(disc(96, 0, 14), STEEL, 1, bevel=8)
    c.part(disc(96, 0, 7), EMERALD, 2, bevel=5)
    c.part(profile([(106, 9), (190, 10)]), LEATHER_D, 3, bevel=6)
    wrap(c, 110, 188, 10, Mat((40, 90, 70), spec=0.15, shin=8, grain="leather", rough=0.25), 4, step=10)
    for s in (-1, 1):
        for k in range(4):
            f = smooth_poly([(200 - k * 6, s * 8), (192 - k * 10, s * (26 + k * 8)), (170 - k * 12, s * (46 + k * 9)), (176 - k * 9, s * (30 + k * 7)), (188 - k * 6, s * 10)], 8)
            c.part(f, STEEL if k % 2 == 0 else Mat((200, 210, 222), spec=0.9, shin=60, env=0.5, grain="brushed", rough=0.08), 10 + k + (s + 1) * 5, bevel=4)
    c.part(profile([(190, 16), (204, 16)]), STEEL, 30, bevel=6)
    blade = smooth_poly([(204, -13), (300, -16), (380, -8), (440, 10), (470, 28), (430, 16), (360, 16), (280, 14), (204, 13)], 10)
    c.part(blade, STEEL, 40, shape="blade", height=1.2, ang=AX_ANG)
    c.emissive(line_dens([(215, 0), (300, 0), (370, 4), (425, 16)], 2.6), (80, 255, 170), 1.4)
    return c.image(glow_strength=0.8)


def phoenix():
    """성기사의 전투망치: 금테 망치머리 + 빛나는 태양 문장 + 토파즈"""
    c = Canvas()
    c.part(disc(20, 0, 14), GOLD, 1, bevel=8)
    c.part(profile([(28, 9), (400, 9)]), DSTEEL, 2, bevel=6, ang=AX_ANG)
    wrap(c, 40, 160, 10, LEATHER, 3)
    for u in (36, 164, 300):
        c.part(profile([(u - 4, 12), (u + 4, 12)]), GOLD, 20 + u, bevel=4)
    head = profile([(380, 60), (470, 60)])
    c.part(head, STEEL, 30, bevel=12)
    for u in (380, 462):
        c.part(profile([(u, 64), (u + 8, 64)]), GOLD, 31 + u, bevel=5)
    c.part(profile([(470, 18), (500, 10), (512, 0.5)]), STEEL, 33, shape="blade", height=1)
    sun = disc(425, 0, 26)
    c.part(sun, GOLD, 34, bevel=10)
    ray = np.zeros((S, S), np.float32)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        ray = np.maximum(ray, line_dens([(425 + math.cos(a) * 30, math.sin(a) * 30), (425 + math.cos(a) * 44, math.sin(a) * 44)], 3.5))
    c.emissive(ray, (255, 210, 90), 1.3)
    c.part(disc(425, 0, 11), TOPAZ, 35, bevel=7)
    return c.image(glow_strength=0.8)


def blackiron():
    """흑기사의 대검: 넓고 톱니진 검은 날 + 붉은 룬 + 뿔 가드 + 루비"""
    c = Canvas()
    c.part(disc(40, 0, 16), DSTEEL, 1, bevel=9)
    c.part(disc(40, 0, 7), RUBY, 2, bevel=5)
    c.part(profile([(52, 11), (150, 12)]), LEATHER_D, 3, bevel=6)
    wrap(c, 56, 148, 12, Mat((70, 20, 22), spec=0.15, shin=8, grain="leather", rough=0.25), 4)
    horns = smooth_poly([(150, 0), (152, 26), (138, 62), (150, 70), (166, 36), (170, 0), (166, -36), (150, -70), (138, -62), (152, -26)], 10)
    c.part(horns, DSTEEL, 10, bevel=8)
    c.part(disc(160, 0, 10), RUBY, 11, bevel=6)
    pts = [(170, 26)]
    for k in range(9):
        u = 190 + k * 34
        pts += [(u, 28 - k * 0.8), (u + 17, 22 - k * 0.8)]
    pts += [(500, 16), (530, 0)]
    pts2 = [(u, -v) for u, v in pts[::-1]]
    blade = poly(pts + pts2)
    c.part(blade, DSTEEL, 20, shape="blade", height=1.0, ang=AX_ANG)
    runes(c, 190, 440, 0, (255, 50, 40), 21, size=8, width=2.4)
    return c.image(glow_strength=0.9)


def tiger():
    """늑대 발톱 건틀릿: 털 소매 + 판금 손등 + 강철 발톱 셋"""
    c = Canvas()
    cuff = smooth_poly([(60, -48), (150, -52), (160, 0), (150, 52), (60, 48), (50, 0)], 10)
    c.part(cuff, FUR, 1, bevel=14, ang=AX_ANG + 90)
    arm = profile([(150, 42), (250, 46), (290, 40)])
    c.part(arm, LEATHER, 2, bevel=12)
    for k in range(3):
        u = 170 + k * 38
        c.part(profile([(u, 48), (u + 30, 50)]) & ~profile([(u, 20), (u + 30, 20)]) | profile([(u, 50), (u + 30, 50)]) & (V < -18), STEEL, 10 + k, bevel=6)
    plate = smooth_poly([(250, -40), (300, -44), (318, 0), (300, 44), (250, 40)], 8)
    c.part(plate, STEEL, 20, bevel=12)
    c.part(disc(284, 0, 11), AMETHYST, 21, bevel=7)
    for j, off in enumerate((-28, 0, 28)):
        cl = smooth_poly([(310, off - 8), (400, off - 10), (470, off + 2), (520, off + 26), (470, off + 12), (400, off + 8), (310, off + 8)], 8)
        c.part(cl, STEEL, 30 + j, shape="blade", height=0.9, ang=AX_ANG)
    return c.image(glow_strength=0.7)


def staff():
    """대마법사의 지팡이: 비틀린 나무 + 금 세공 머리 + 빛나는 자수정 구슬"""
    c = Canvas()
    shaft = profile([(10, 7), (40, 9), (380, 11), (410, 13)])
    tw = np.sin(U * 0.12 + V * 0.25) * 2.5
    c.part(shaft, WOOD, 1, bevel=9, ang=AX_ANG, extra_h=tw)
    for u in (60, 200, 330):
        c.part(profile([(u - 5, 13), (u + 5, 13)]), GOLD, 10 + u, bevel=5)
    orb = disc(470, 0, 34)
    glowd = orb.astype(np.float32)
    c.glow += np.array((180, 90, 255), np.float32)[None, None, :] * ndimage_blur(glowd, 18)[..., None] * 1.6
    c.part(orb, Mat((160, 80, 240), spec=1, shin=90, env=0.35, rough=0.02, glow=(200, 120, 255), sky=(240, 200, 255), ground=(40, 10, 80)), 20, bevel=34)
    for s in (-1, 1):
        prong = smooth_poly([(400, s * 10), (430, s * 36), (470, s * 44), (505, s * 30), (515, s * 14), (500, s * 26), (470, s * 34), (438, s * 26), (412, s * 4)], 8)
        c.part(prong, GOLD, 30 + s, bevel=5)
    c.part(profile([(395, 16), (420, 18)]), GOLD, 33, bevel=7)
    c.part(profile([(505, 6), (525, 3), (535, 0.5)]), GOLD, 34, bevel=4)
    return c.image(glow_strength=1.0)


def ndimage_blur(a, s):
    from scipy import ndimage as nd
    return nd.gaussian_filter(a, s)


def peachwood():
    """불사조의 창: 불꽃 모양 금·강철 창날 + 붉은 리본 + 루비"""
    c = Canvas()
    c.part(profile([(8, 5), (20, 9), (30, 9)]), GOLD, 1, bevel=5)
    c.part(profile([(30, 8), (380, 8)]), WOOD_D, 2, bevel=7, ang=AX_ANG)
    wrap(c, 150, 240, 9, LEATHER, 3)
    for s in (-1, 1):
        rib = smooth_poly([(380, s * 6), (340, s * 30), (290, s * 50), (250, s * 44), (300, s * 26), (350, s * 12)], 8)
        c.part(rib, CLOTH_R, 10 + s, bevel=6, ang=AX_ANG)
    c.part(profile([(375, 13), (398, 13)]), GOLD, 12, bevel=6)
    flame = smooth_poly([(398, 0), (405, 22), (430, 34), (425, 18), (450, 26), (470, 14), (500, 10), (535, 0), (500, -10), (470, -14), (450, -26), (425, -18), (430, -34), (405, -22)], 10)
    c.part(flame, GOLD, 13, bevel=8)
    tip = profile([(420, 10), (500, 9), (530, 0.5)])
    c.part(tip, STEEL, 14, shape="blade", height=1.2, ang=AX_ANG)
    c.part(disc(412, 0, 9), RUBY, 15, bevel=6)
    c.emissive(line_dens([(430, 0), (505, 0)], 2.4), (255, 120, 40), 1.4)
    return c.image(glow_strength=0.9)


WEAPONS = {"thunder": thunder, "dragon": dragon, "wind": wind, "phoenix": phoenix,
           "blackiron": blackiron, "tiger": tiger, "staff": staff, "peachwood": peachwood}


def paint(wid, out=256):
    im = WEAPONS[wid]()
    return im if out == 256 else im.resize((out, out), Image.LANCZOS)


def export(pack):
    for wid in WEAPONS:
        ref = pack.texture(f"weapon/{wid}", paint(wid))
        pack.item_model(f"weapon/{wid}", {"parent": "minecraft:item/handheld", "textures": {"layer0": ref}})


def preview(path):
    ims = [paint(w) for w in WEAPONS]
    W = Image.new("RGBA", (256 * len(ims), 512), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        W.paste(Image.new("RGBA", (256, 256), (70, 64, 60, 255)), (i * 256, 0))
        W.paste(Image.new("RGBA", (256, 256), (139, 139, 139, 255)), (i * 256, 256))
        W.alpha_composite(im, (i * 256, 0))
        W.alpha_composite(im, (i * 256, 256))
    W.convert("RGB").save(path)
