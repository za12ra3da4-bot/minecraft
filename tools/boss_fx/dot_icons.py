"""스킬 아이콘 34종 — 32x32 도트, 보스별 어두운 바탕 + 1픽셀 테두리

아이템 텍스처(인벤토리 · 머리 위 표시)와 폰트 글리프(보스바 · 자막 · 액션바)에 같은 그림을 쓴다.
"""
import math

import numpy as np

from dot import RAMPS, Dot, along, arc, bez, curve_strip, ellipse, hx, strip, xf
from dot_motifs import bull_head, dog_front, dog_side, end_tip, flame, labrys, lion_head, rock, snake_head, star, tentacle


def radial_lines(d, c, r0, r1, n, mat, w=0.6, off=0.0, lo=1, skip=()):
    for k in range(n):
        if k in skip:
            continue
        a = math.radians(off + 360 * k / n)
        d.stroke(mat, [(c[0] + math.cos(a) * r0, c[1] + math.sin(a) * r0), (c[0] + math.cos(a) * r1, c[1] + math.sin(a) * r1)],
                 lambda t: w * (0.4 + 0.6 * t), glow=False, lo=lo)


def ground(d, y0, y1, mat="rock", seed=1):
    pts = [(0, y0)] + [(x, y0 + math.sin(x * 0.7 + seed) * 0.8) for x in range(2, 31, 3)] + [(32, y1), (32, 32), (0, 32)]
    d.body(mat, pts, bevel=2.0)


# ───────────────────────── 미노타우로스
def minotaur_charge():
    d = Dot("minotaur")
    radial_lines(d, (16, 16), 11.5, 16.5, 16, "fire", w=0.9, off=11)
    for x, y, r in ((6, 27, 2.2), (26, 27, 2.4), (10, 29, 1.6), (22, 29.5, 1.8)):
        d.body("rock", ellipse((x, y), r, r * 0.8), lo=2, bevel=1.0)
    bull_head(d, (16, 17.5), 1.0, eye="hell")
    d.sparkle(27, 6, "fire")
    return d.finish()


def minotaur_frenzy():
    d = Dot("minotaur")
    c = (16, 16)
    d.stroke("fire", arc(c, 12.2, 200, 480, 56), lambda t: 0.5 + 2.0 * t)
    d.stroke("fire", arc(c, 8.0, 30, 300, 44), lambda t: 0.4 + 1.4 * t)
    labrys(d, (8.5, 25.5), (22.5, 9.5), 1.0)
    d.embers("fire", 14, (3, 3, 29, 29), seed=4)
    d.sparkle(25, 6, "fire", big=True)
    return d.finish()


def minotaur_quake():
    d = Dot("minotaur")
    ground(d, 23, 22, "rock", 2)
    for a in (192, 210, 330, 348):
        pass
    d.stroke("fire", arc((16, 23), 13, 195, 345, 40), lambda t: 0.4 + 0.5 * math.sin(t * math.pi), lo=2)
    d.stroke("fire", arc((16, 23), 8.5, 200, 340, 30), lambda t: 0.4 + 0.5 * math.sin(t * math.pi), lo=2)
    for pts in (((16, 24), (12, 26), (9, 25.5), (5, 28), (2, 28.5)), ((16, 24), (19.5, 26.5), (23, 26), (27, 29), (30, 29)),
                ((15, 25), (14, 28), (11, 31)), ((17.5, 25), (19, 28.5), (20, 31))):
        d.stroke("fire", list(pts)[::-1], lambda t: 0.45 + 0.35 * t, lo=2)
    d.glow_body("fire", ellipse((16, 23.4), 4.6, 1.6))
    # 주먹
    d.body("bull", strip((16, -1), (16, 12), lambda t: 3.2), bevel=2.0)
    d.body("gold", strip((16, 6.5), (16, 9.5), lambda t: 3.6), bevel=1.2)
    fist = [(11, 12), (21, 12), (21.8, 14), (21, 19.5), (11, 19.5), (10.2, 14)]
    d.body("bull", fist, bevel=2.2)
    for x in (13.5, 16, 18.5):
        d.line([(x, 17), (x, 19)], RAMPS["bull"][1])
    for i, (x, y, r) in enumerate(((6, 13, 1.8), (26, 11, 2.2), (9, 6, 1.4), (23.5, 4.5, 1.3), (4, 19, 1.2), (28, 18, 1.4))):
        rock(d, (x, y), r, seed=i + 3, mat="rock")
    return d.finish()


def minotaur_horn():
    d = Dot("minotaur")
    for off in (-5, 5):
        a, b = along((4, 30), (27, 5), 0.1, off), along((4, 30), (27, 5), 0.62, off)
        d.stroke("fire", [a, b], lambda t: 0.3 + 0.5 * t, glow=False, lo=1)
    h = bez((3, 31), (8, 20), (15, 13), (27, 4.5), n=36)
    d.body("bone", curve_strip(h, lambda t: 4.6 * (1 - t) ** 0.8), bevel=2.2, tips=[end_tip(h)])
    for q in (0.12, 0.24, 0.36, 0.48):
        i = int(q * 36)
        p, n2 = h[i], h[i + 1]
        dx, dy = n2[0] - p[0], n2[1] - p[1]
        Ln = math.hypot(dx, dy)
        w = 4.6 * (1 - q) ** 0.8 * 0.85
        d.line([(p[0] - dy / Ln * w, p[1] + dx / Ln * w), (p[0] + dy / Ln * w, p[1] - dx / Ln * w)], RAMPS["bone"][1])
    d.body("bull", ellipse((2, 31), 6, 5), bevel=2.0)
    radial_lines(d, (27, 5), 2.5, 6, 8, "fire", w=0.7, off=20, skip=(3,))
    d.sparkle(27, 5, "fire", big=True)
    return d.finish()


def minotaur_rage():
    d = Dot("minotaur")
    for x, h, w, l in ((5, 17, 3.2, -1), (27, 18, 3.2, 1), (10, 22, 3.8, -0.5), (22, 22, 3.8, 0.5), (16, 26, 4.2, 0)):
        flame(d, (x, 30), h, w, l, "fire")
    bull_head(d, (16, 18), 0.95, eye="fire")
    for f in (1, -1):
        e = (16 + f * 2.1 * 0.95, 18 + 0.2)
        d.stroke("fire", [(e[0] + f * 1, e[1]), (e[0] + f * 4, e[1] - 1.5)], lambda t: 0.5, glow=True, lo=3)
    d.embers("fire", 16, (2, 2, 30, 14), seed=5)
    return d.finish()


# ───────────────────────── 네메아의 사자
def nemean_lion_pounce():
    d = Dot("nemean_lion")
    for k, y in enumerate((12, 16.5, 21)):
        d.stroke("gold", [(2 + k, y + 3), (10 + k, y)], lambda t: 0.25 + 0.5 * t, glow=False, lo=1)
    # 도약하는 사자 (몸통 · 다리 · 꼬리 · 갈기)
    d.body("fur", strip((4, 11), (1.5, 6), lambda t: 0.7), bevel=0.8)
    d.body("mane", ellipse((1.8, 5.8), 1.6, 1.8), bevel=1.0)
    for a, b, w in (((10, 19), (3.5, 26), 1.4), ((12, 19), (7, 27.5), 1.3)):
        d.body("fur", strip(a, b, lambda t, w=w: w * (1 - 0.35 * t)), bevel=1.2)
    d.body("fur", ellipse((14.5, 15.5), 9, 4.6, rot=math.radians(-18)), bevel=2.6)
    for a, b, w in (((20, 15), (28.5, 21), 1.4), ((19, 17), (27, 24), 1.3)):
        d.body("fur", strip(a, b, lambda t, w=w: w * (1 - 0.3 * t)), bevel=1.2)
        for k in (-1, 0, 1):
            tip = along(a, b, 1.08, k * 0.9)
            d.px(tip[0], tip[1], RAMPS["bone"][-1])
    mane = []
    for k in range(20):
        a = 2 * math.pi * k / 20
        r = 6.2 if k % 2 == 0 else 4.8
        mane.append((22.5 + math.cos(a) * r, 9.5 + math.sin(a) * r))
    d.body("mane", mane, bevel=2.4)
    d.body("fur", [(22.5, 7), (27.5, 8.2), (29, 10.4), (27, 12.4), (23, 12.2)], bevel=1.4)
    d.px(26, 9, RAMPS["gem_amber"][-2])
    d.px(28.6, 10.0, RAMPS["mane"][0])
    d.flat(hx("3e0a14"), [(25.5, 11.6), (29, 11), (27, 13)])
    d.embers("gold", 8, (4, 24, 30, 30), seed=6)
    return d.finish()


def nemean_lion_roar():
    d = Dot("nemean_lion")
    for r in (12, 14.8):
        d.stroke("gold", arc((16, 16), r, -38, 38, 16), lambda t: 0.4 + 0.6 * math.sin(t * math.pi), lo=2)
        d.stroke("gold", arc((16, 16), r, 142, 218, 16), lambda t: 0.4 + 0.6 * math.sin(t * math.pi), lo=2)
    lion_head(d, (16, 15.5), 1.05, roar=True)
    return d.finish()


def nemean_lion_hunt():
    d = Dot("nemean_lion")
    for a0 in (20, 110, 200, 290):
        d.stroke("red", arc((16, 16), 12.5, a0, a0 + 50, 12), 0.6, glow=True, lo=2, core=False)
    for a in (0, 90, 180, 270):
        r = math.radians(a)
        d.stroke("red", [(16 + math.cos(r) * 14.5, 16 + math.sin(r) * 14.5), (16 + math.cos(r) * 10, 16 + math.sin(r) * 10)],
                 0.55, glow=False, lo=2)
    eye = bez((6, 16), (11, 8.5), (21, 8.5), (26, 16), n=20) + bez((26, 16), (21, 23.5), (11, 23.5), (6, 16), n=20)
    d.body("fur", eye, bevel=2.2)
    d.glow_body("gem_amber", ellipse((16, 16), 4.6, 5.2))
    d.flat(RAMPS["black"][0], [(15.4, 11.2), (16.6, 11.2), (17.1, 16), (16.6, 20.8), (15.4, 20.8), (14.9, 16)])
    d.px(18, 13, RAMPS["gem_amber"][-1])
    return d.finish()


def nemean_lion_claw():
    d = Dot("nemean_lion")
    slash = ["5c0e1c", "a22633", "e43b44", "f6757a", "fcb0a8", "ffffff"]
    RAMPS["slash"] = [hx(c) for c in slash]
    for k in range(3):
        o = (k - 1) * 6.0
        p = bez((25 + o, 3), (21 + o, 12), (13 + o, 20), (5 + o, 28), n=30)
        d.stroke("slash", p, lambda t: 0.3 + 1.7 * math.sin(t * math.pi) ** 0.8)
        d.body("bone", [(p[0][0] - 1.2, p[0][1] - 0.4), (p[0][0] + 1.4, p[0][1] - 1.8), (p[0][0] + 0.6, p[0][1] + 1.4)], bevel=0.8)
    for x, y in ((9, 8), (7, 13), (27, 21), (24, 26), (29, 16)):
        d.px(x, y, RAMPS["blood"][-1])
        d.px(x + 1, y + 1, RAMPS["blood"][2])
    return d.finish()


# ───────────────────────── 키메라
def chimera_breath():
    d = Dot("chimera")
    cone = bez((5, 18), (13, 13), (22, 5), (31, 3), n=20) + [(31, 29)] + bez((31, 29), (22, 27), (13, 22), (5, 21), n=20)
    d.glow_body("fire", cone, lo=1)
    for end in ((30, 6), (31, 16), (30, 26)):
        d.stroke("fire", [(5, 19.5), end], lambda t: 0.6 + 1.8 * t, lo=3)
    # 사자 머리 옆모습
    mane = [(4.5 + math.cos(a) * (6.2 if k % 2 == 0 else 4.8), 19 + math.sin(a) * (6.2 if k % 2 == 0 else 4.8))
            for k, a in enumerate(np.linspace(0, 2 * math.pi, 21)[:-1])]
    d.body("mane", mane, bevel=2.2)
    d.body("fur", [(4, 15.5), (9.5, 16.5), (11, 18.5), (8.2, 19.2), (11, 20.8), (8.5, 23), (4, 22.5)], bevel=1.4)
    d.px(7, 17.5, RAMPS["fire"][-1])
    d.embers("fire", 16, (12, 2, 31, 30), seed=3, size=2)
    return d.finish()


def chimera_venom():
    d = Dot("chimera")
    d.stroke("venom", bez((6, 27), (10, 22), (14, 18), (19.5, 12.5), n=24), lambda t: 0.3 + 3.0 * t ** 1.3, lo=1)
    d.glow_body("venom", ellipse((21.5, 10.5), 5.0, 5.0))
    for x, y, r in ((22, 18.5, 1.2), (26, 16.5, 0.9), (17.5, 20.5, 0.8)):
        d.glow_body("venom", [(x, y - r * 2.2)] + ellipse((x, y), r, r, 16)[1:8])
    d.px(19.5, 8.5, RAMPS["venom"][-1])
    d.px(20.5, 8.5, RAMPS["venom"][-2])
    snake_head(d, (6.5, 26), 1.1, ang=-45, open_=True, mat="green")
    d.embers("venom", 10, (10, 2, 30, 26), seed=8)
    return d.finish()


def chimera_spikes():
    d = Dot("chimera")
    ground(d, 25, 25, "rock", 3)
    for (x, y, tx, ty, w) in ((8, 27, 4.5, 10, 3.2), (24, 27, 27.5, 11, 3.2), (16, 28, 16.5, 4, 4.2)):
        pts = bez((x - w, y), (x - w * 0.6, (y + ty) / 2), ((x + tx) / 2 - 0.5, ty + 5), (tx, ty), n=16) + \
            bez((tx, ty), ((x + tx) / 2 + 1.2, ty + 5), (x + w * 0.6, (y + ty) / 2), (x + w, y), n=16)
        d.body("bone", pts, bevel=2.0, tips=[((tx, ty), (tx - x, ty - y))])
        for q in (0.3, 0.55):
            yy = y + (ty - y) * q
            xx = x + (tx - x) * q
            ww = w * (1 - q) * 0.9
            d.line([(xx - ww, yy + 0.5), (xx + ww, yy - 0.5)], RAMPS["bone"][1])
    for i, (x, y, r) in enumerate(((11, 20, 1.3), (21, 18, 1.5), (4, 23, 1.1), (29, 22, 1.2))):
        rock(d, (x, y), r, seed=i + 11, mat="rock")
    d.stroke("fire", [(2, 29), (7, 28), (12, 30)], 0.45, lo=2)
    d.stroke("fire", [(20, 30), (26, 28.5), (31, 29.5)], 0.45, lo=2)
    return d.finish()


def chimera_triple():
    d = Dot("chimera")
    d.stroke("fire", bez((2, 4), (6, 9), (11, 12), (15, 15), n=20), lambda t: 0.4 + 1.8 * t, lo=1)
    d.stroke("venom", bez((30, 4), (26, 9), (21, 12), (17, 15), n=20), lambda t: 0.4 + 1.8 * t, lo=1)
    d.stroke("silver", bez((16, 31), (15, 26), (17, 22), (16, 18), n=20), lambda t: 0.4 + 1.8 * t, lo=1)
    d.glow_body("gem_amber", star((16, 16), 6.5, 2.4, k=8, rot=-90))
    d.glow_body("fire", star((16, 16), 3.2, 1.6, k=4, rot=-45))
    d.px(16, 16, RAMPS["fire"][-1])
    for (x, y, m) in ((4, 5, "fire"), (28, 5, "venom"), (16, 29, "silver")):
        d.sparkle(x, y, m)
    return d.finish()


# ───────────────────────── 케르베로스
def cerberus_flame():
    d = Dot("cerberus")
    cone = [(15, 14.5)] + bez((15, 14.5), (21, 10), (26, 6), (31, 4), n=12) + [(31, 28)] + bez((31, 28), (26, 25), (21, 21), (15, 16), n=12)
    d.glow_body("hell", cone)
    for end in ((30, 8), (31, 16), (30, 24)):
        d.stroke("hell", [(15, 15.2), end], lambda t: 0.5 + 1.6 * t, lo=3)
    dog_side(d, (7.5, 15.5), 0.95, ang=0, open_=True, eye="hell")
    d.embers("hell", 16, (14, 2, 31, 30), seed=12, size=2)
    return d.finish()


def cerberus_howl():
    d = Dot("cerberus")
    mc = (19, 10)
    for r, w in ((5, 0.9), (9, 1.1), (13.5, 1.3)):
        d.stroke("soul", arc(mc, r, -160, 20, 30), lambda t, w=w: w * (0.5 + 0.5 * math.sin(t * math.pi)), lo=1)
    dog_side(d, (13, 22), 1.05, ang=-52, open_=True, eye="soul")
    d.embers("soul", 14, (2, 2, 30, 30), seed=7)
    return d.finish()


def cerberus_hunt():
    d = Dot("cerberus")
    d.glow_body("soul", ellipse((16, 16), 9, 3.2), lo=1)
    gum_up = bez((1, 3), (8, 12), (24, 12), (31, 3), n=24) + [(31, 0), (1, 0)]
    gum_dn = bez((1, 29), (8, 20), (24, 20), (31, 29), n=24) + [(31, 32), (1, 32)]
    d.body("dfur", gum_up, bevel=2.2)
    d.body("dfur", gum_dn, bevel=2.2)
    d.stroke("red", bez((2, 4), (8, 11.2), (24, 11.2), (30, 4), n=24), 0.8, glow=False, core=False, lo=2)
    d.stroke("red", bez((2, 28), (8, 20.8), (24, 20.8), (30, 28), n=24), 0.8, glow=False, core=False, lo=2)
    for k, x in enumerate((5.5, 10, 14, 18, 22, 26.5)):
        big = k in (0, 5)
        yb = 8.5 + 3.2 * math.sin((x - 1) / 30 * math.pi)
        h = 7.5 if big else 4.2
        w = 1.8 if big else 1.4
        d.body("bone", [(x - w, yb - 1), (x + w, yb - 1), (x + 0.3, yb + h)], bevel=1.0, tips=[((x + 0.3, yb + h), (0, 1))])
        yb2 = 23.5 - 3.2 * math.sin((x - 1) / 30 * math.pi)
        d.body("bone", [(x - w + 0.2, yb2 + 1), (x + w + 0.2, yb2 + 1), (x + 0.2, yb2 - h * 0.85)], bevel=1.0,
               tips=[((x + 0.2, yb2 - h * 0.85), (0, -1))])
    return d.finish()


def cerberus_gate():
    d = Dot("cerberus")
    inner = [(9.5, 29)] + bez((9.5, 12), (9.5, 5), (22.5, 5), (22.5, 12), n=20)[::-1][::-1] + [(22.5, 29)]
    inner = [(9.5, 29), (9.5, 12)] + bez((9.5, 12), (9.5, 4.5), (22.5, 4.5), (22.5, 12), n=20) + [(22.5, 29)]
    d.glow_body("soul", inner, lo=1)
    c = (16, 17)
    for k in range(2):
        pts = []
        for i in range(40):
            t = i / 39
            a = math.radians(k * 180 + t * 420)
            r = 6.0 * (1 - t) + 0.6
            pts.append((c[0] + math.cos(a) * r * 0.8, c[1] + math.sin(a) * r * 1.3))
        d.stroke("soul", pts, lambda t: 0.4 + 0.8 * t, lo=3, glow=False)
    for x0 in (4.5, 22.5):
        d.body("stone", [(x0, 30), (x0, 12), (x0 + 5, 12), (x0 + 5, 30)], bevel=1.6)
        for y in (16, 21, 26):
            d.line([(x0 + 0.5, y), (x0 + 4.5, y)], RAMPS["stone"][1])
    d.body("stone", curve_strip(bez((7, 13), (7, 1.5), (25, 1.5), (25, 13), n=30), lambda t: 2.6), bevel=1.6)
    d.body("gold", [(14.5, 1.5), (17.5, 1.5), (17, 5.5), (15, 5.5)], bevel=1.0)
    d.px(16, 3, RAMPS["hell"][-1])
    for x in (7, 25):
        flame(d, (x, 30), 6, 1.9, 0, "hell")
    d.embers("soul", 8, (10, 8, 22, 28), seed=21)
    return d.finish()


def cerberus_fury():
    d = Dot("cerberus")
    for x, h, w in ((4, 18, 3.4), (28, 18, 3.4), (10, 24, 3.6), (22, 24, 3.6), (16, 29, 4.6)):
        flame(d, (x, 31), h, w, 0, "hell")
    dog_front(d, (6.8, 19), 0.8, eye="hell")
    dog_front(d, (25.2, 19), 0.8, eye="hell")
    dog_front(d, (16, 16.5), 1.08, eye="fire")
    d.embers("hell", 12, (2, 2, 30, 12), seed=4)
    return d.finish()


# ───────────────────────── 히드라
def hydra_bite():
    d = Dot("hydra")
    for (hx_, hy, ang) in ((21, 6.5, -14), (25, 16, 0), (21, 25.5, 14)):
        neck = bez((-1, 16 + (hy - 16) * 0.3), (6, hy + (4 if hy < 16 else -4 if hy > 16 else 5)), (12, hy), (hx_ - 3, hy), n=24)
        d.body("emerald", curve_strip(neck, lambda t: 2.6 - 0.8 * t), bevel=1.8)
        for i in range(3, 22, 3):
            d.px(neck[i][0], neck[i][1] + 1.2, RAMPS["emerald"][-1])
        snake_head(d, (hx_, hy), 1.0, ang=ang, mat="emerald", open_=True)
        d.stroke("silver", [(hx_ + 5, hy - 3), (hx_ + 8, hy - 4)], 0.4, glow=False, lo=2)
    return d.finish()


def hydra_venom():
    d = Dot("hydra")
    for x, y, r in ((6, 4, 4.2), (13, 3, 4.8), (21, 3.5, 4.6), (27, 4.5, 3.8)):
        d.body("green", ellipse((x, y), r, r * 0.75), lo=1, hi=4, bevel=2.2)
    for i, (x, y, r) in enumerate(((7, 13, 1.3), (14, 17, 1.6), (22, 12, 1.3), (26, 20, 1.2), (10, 22, 1.1), (19, 23, 1.4), (4, 19, 0.9))):
        d.glow_body("venom", [(x, y - r * 2.4)] + ellipse((x, y), r, r, 16)[1:8])
    d.glow_body("venom", ellipse((16, 28.5), 12, 2.4))
    for x in (8, 19, 25):
        d.px(x, 25, RAMPS["venom"][-2])
        d.px(x - 1, 26, RAMPS["venom"][-3])
        d.px(x + 1, 26, RAMPS["venom"][-3])
    return d.finish()


def hydra_tempest():
    d = Dot("hydra")
    c = (16, 16)
    heads = []
    for k in range(3):
        pts = []
        for i in range(50):
            t = i / 49
            a = math.radians(k * 120 + 40 + t * 300)
            r = 1.5 + 11.5 * t
            pts.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
        d.stroke("venom", pts, lambda t: 0.4 + 1.3 * t, lo=1)
        heads.append(pts[-1] + (math.degrees(math.atan2(pts[-1][1] - pts[-3][1], pts[-1][0] - pts[-3][0])),))
    for x, y, a in heads:
        snake_head(d, (x, y), 0.85, ang=a, mat="emerald", open_=True)
    d.glow_body("venom", ellipse(c, 2.4, 2.4))
    d.embers("venom", 12, (2, 2, 30, 30), seed=15)
    return d.finish()


def hydra_regrow():
    d = Dot("hydra")
    d.body("emerald", strip((16, 32), (16, 21), lambda t: 3.6), bevel=2.0)
    for f in (1, -1):
        neck = bez((16 + f * 1.2, 22), (16 + f * 2, 14), (16 + f * 8, 13), (16 + f * 8.5, 7.5), n=20)
        d.body("emerald", curve_strip(neck, lambda t: 2.2 - 0.7 * t), bevel=1.6)
        snake_head(d, (16 + f * 8.5, 6.5), 0.9, ang=-90 + f * 12, mat="emerald", open_=f > 0)
    d.glow_body("venom", ellipse((16, 21.5), 3.2, 1.3))
    for (x, y) in ((6, 20), (26, 21), (16, 13)):
        d.glow_body("venom", [(x - 0.6, y - 2.4), (x + 0.6, y - 2.4), (x + 0.6, y - 0.6), (x + 2.4, y - 0.6), (x + 2.4, y + 0.6),
                              (x + 0.6, y + 0.6), (x + 0.6, y + 2.4), (x - 0.6, y + 2.4), (x - 0.6, y + 0.6), (x - 2.4, y + 0.6),
                              (x - 2.4, y - 0.6), (x - 0.6, y - 0.6)])
    d.embers("venom", 12, (4, 12, 28, 30), seed=16)
    return d.finish()


def hydra_sever():
    d = Dot("hydra")
    a, b = (1, 31), (27, 6)
    d.body("emerald", curve_strip([along(a, b, t) for t in np.linspace(0, 0.44, 12)], lambda t: 3.0), bevel=2.0)
    d.body("emerald", curve_strip([along(a, b, t, 1.2) for t in np.linspace(0.56, 0.86, 10)], lambda t: 2.7 - 0.5 * t), bevel=1.8)
    d.glow_body("blood", ellipse(along(a, b, 0.445), 2.6, 1.2, rot=math.radians(45)))
    snake_head(d, along(a, b, 0.92, 1.2), 1.0, ang=-44, mat="emerald", open_=True)
    d.stroke("silver", bez((4, 6), (12, 11), (20, 19), (29, 27), n=30), lambda t: 0.3 + 1.8 * math.sin(t * math.pi) ** 0.7, lo=1)
    for x, y in ((11, 17), (9, 14), (20, 20), (22, 23), (13, 21)):
        d.px(x, y, RAMPS["blood"][-1])
        d.px(x + 1, y, RAMPS["blood"][2])
    return d.finish()


# ───────────────────────── 메두사
def medusa_gaze():
    d = Dot("medusa")
    for ang in (-35, -12, 12, 35):
        for s in (1, -1):
            a = math.radians(s * (ang + 90))
            d.stroke("venom", [(16 + math.cos(a) * 15, 17 + math.sin(a) * 15), (16, 17)], lambda t: 0.4 + 0.9 * (1 - t), lo=1)
    for k, (x0, y0, x1, y1) in enumerate(((8, 10, 4, 3), (13, 8.5, 12, 1.5), (19, 8.5, 21, 1.5), (24, 10, 28, 3))):
        hair = bez((x0, y0), ((x0 + x1) / 2 + (2 if k % 2 else -2), (y0 + y1) / 2), (x1, y1), n=12)
        d.body("emerald", curve_strip(hair, lambda t: 1.1 - t * 0.4), bevel=0.8)
    eye = bez((3, 17), (9.5, 9), (22.5, 9), (29, 17), n=20) + bez((29, 17), (22.5, 25), (9.5, 25), (3, 17), n=20)
    d.body("marble", eye, bevel=2.5)
    d.glow_body("gem_amber", ellipse((16, 17), 5.2, 5.6))
    d.flat(RAMPS["black"][0], [(15.3, 12.2), (16.7, 12.2), (17.2, 17), (16.7, 21.8), (15.3, 21.8), (14.8, 17)])
    d.sparkle(19, 14, "gem_amber")
    return d.finish()


def medusa_zone():
    d = Dot("medusa")
    ring = [(16 + math.cos(a) * 13.5, 22 + math.sin(a) * 6.8) for a in np.linspace(0, 2 * math.pi, 64)]
    d.body("stone", ellipse((16, 22), 13, 6.4, 48), lo=1, hi=3, bevel=3.0, outline=False)
    d.stroke("venom", ring, 0.7, lo=3, core=False)
    for pts in (((16, 22), (12, 24), (8, 23.5)), ((16, 22), (20, 25), (24, 24)), ((16, 22), (17, 19), (21, 18))):
        d.line(list(pts), RAMPS["stone"][0])
    for (x, y, h, w) in ((9, 23, 9, 2.2), (22.5, 24, 11, 2.6), (15.5, 20, 7, 1.8)):
        d.body("stone", [(x - w, y), (x - w * 0.6, y - h * 0.7), (x + 0.3, y - h), (x + w * 0.7, y - h * 0.6), (x + w, y)], bevel=1.4,
               tips=[((x + 0.3, y - h), (0, -1))])
    eye = bez((9, 7), (13, 2.8), (19, 2.8), (23, 7), n=12) + bez((23, 7), (19, 11.2), (13, 11.2), (9, 7), n=12)
    d.glow_body("venom", eye)
    d.flat(RAMPS["black"][0], [(15.5, 4.2), (16.5, 4.2), (16.9, 7), (16.5, 9.8), (15.5, 9.8), (15.1, 7)])
    d.embers("venom", 10, (3, 12, 29, 28), seed=17)
    return d.finish()


def medusa_serpent():
    d = Dot("medusa")
    d.stroke("venom", bez((0, 32), (4, 27), (8, 24), (12, 20), n=16), lambda t: 0.3 + 1.2 * t, lo=1)
    a, b = (5, 27), (21, 11)
    d.body("wood", strip(a, b, lambda t: 0.7), bevel=0.8)
    for sgn in (1, -1):
        d.body("emerald", [along(a, b, 0.0), along(a, b, -0.05, sgn * 3), along(a, b, 0.18, sgn * 2.6), along(a, b, 0.22)], bevel=0.9)
    snake_head(d, (23, 9), 1.15, ang=-45, mat="emerald", open_=True)
    d.embers("venom", 8, (14, 2, 30, 18), seed=18)
    d.sparkle(29, 3, "venom")
    return d.finish()


def medusa_tail():
    d = Dot("medusa")
    c = (15, 15)
    pts = []
    for i in range(70):
        t = i / 69
        a = math.radians(70 + t * 600)
        r = 12.5 - 9.5 * t
        pts.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 0.95))
    pts = [(30, 31), (26, 29)] + pts
    d.body("emerald", curve_strip(pts, lambda t: 3.4 - 2.8 * t), bevel=2.0)
    for i in range(3, len(pts) - 6, 3):
        p, q = pts[i], pts[i + 1]
        dx, dy = q[0] - p[0], q[1] - p[1]
        Ln = math.hypot(dx, dy) or 1
        w = (3.4 - 2.8 * i / len(pts)) * 0.6
        d.px(p[0] + dy / Ln * w, p[1] - dx / Ln * w, RAMPS["gold"][4])
    for a in (30, 150, 250, 330):
        r = math.radians(a)
        d.stroke("silver", [(c[0] + math.cos(r) * 15, c[1] + math.sin(r) * 15), (c[0] + math.cos(r) * 13, c[1] + math.sin(r) * 13)],
                 0.45, glow=False, lo=2)
    return d.finish()


def medusa_mirror():
    d = Dot("medusa")
    d.stroke("venom", [(31, 1), (20, 12)], lambda t: 0.5 + 0.9 * t, lo=2)
    d.stroke("gold", [(20, 12), (31, 22)], lambda t: 0.5 + 1.2 * t, lo=2)
    c = (12.5, 17.5)
    d.body("gold", ellipse(c, 10, 10, 48), bevel=2.6)
    d.body("silver", ellipse(c, 7.4, 7.4, 48), bevel=3.2)
    d.line([(8, 20), (13, 13)], RAMPS["silver"][-1])
    d.line([(10, 22), (15, 15)], RAMPS["silver"][-2])
    for k in range(12):
        a = 2 * math.pi * k / 12
        d.px(c[0] + math.cos(a) * 8.8, c[1] + math.sin(a) * 8.8, RAMPS["gold"][1])
    d.sparkle(20, 12, "gem_amber", big=True)
    return d.finish()


# ───────────────────────── 스킬라
def scylla_slam():
    d = Dot("scylla")
    d.body("water", [(0, 26)] + [(x, 26 + math.sin(x * 0.8) * 0.9) for x in range(2, 31, 2)] + [(32, 26), (32, 32), (0, 32)],
           lo=1, hi=3, bevel=2.0)
    for a in (-160, -135, -110, -70, -45, -20):
        r = math.radians(a)
        d.stroke("water", [(15 + math.cos(r) * 5, 26 + math.sin(r) * 3), (15 + math.cos(r) * 13, 26 + math.sin(r) * 10)],
                 lambda t: 0.4 + 0.9 * t, lo=2)
    tent = bez((31, 1), (27, 4), (20, 8), (16, 24), n=30)
    tentacle(d, tent, 3.8, 1.4, "flesh", side=-1)
    d.glow_body("water", ellipse((15, 26), 5, 1.6))
    for x, y in ((6, 13), (25, 14), (9, 9), (21, 10)):
        d.px(x, y, RAMPS["water"][-2])
    return d.finish()


def scylla_hounds():
    d = Dot("scylla")
    for pts in ((16, 32, 7, 18), (16, 32, 16, 13), (16, 32, 25, 18)):
        x0, y0, x1, y1 = pts
        neck = bez((x0, y0), (x0, (y0 + y1) / 2 + 3), (x1, y1 + 3), (x1, y1), n=12)
        d.body("dsteel", curve_strip(neck, lambda t: 2.8 - 0.6 * t), bevel=1.6)
    dog_side(d, (7, 14), 0.8, ang=-40, flip=True, mat="dsteel", eye="fire", open_=True)
    dog_side(d, (25, 14), 0.8, ang=40, flip=False, mat="dsteel", eye="fire", open_=True)
    dog_side(d, (15, 9), 0.85, ang=-70, flip=False, mat="dsteel", eye="fire", open_=True)
    d.body("water", [(0, 28)] + [(x, 28 + math.sin(x) * 0.8) for x in range(1, 32, 2)] + [(32, 28), (32, 32), (0, 32)],
           lo=1, hi=3, bevel=1.6)
    return d.finish()


def scylla_cage():
    d = Dot("scylla")
    d.glow_body("water", ellipse((16, 27), 8, 2.2))
    for f in (1, -1):
        outer = bez((16 + f * 14, 31), (16 + f * 16, 18), (16 + f * 10, 6), (16 + f * 3, 3), n=28)
        tentacle(d, outer, 3.0, 0.8, "flesh", side=f)
        inner = bez((16 + f * 7, 31), (16 + f * 8.5, 22), (16 + f * 6, 12), (16 + f * 1.5, 9), n=22)
        tentacle(d, inner, 2.4, 0.7, "flesh", side=f)
    d.embers("water", 10, (8, 10, 24, 26), seed=19)
    return d.finish()


def scylla_maelstrom():
    d = Dot("scylla")
    c = (16, 16)
    for k in range(3):
        pts = []
        for i in range(60):
            t = i / 59
            a = math.radians(k * 120 + t * 330)
            r = 13.5 * (1 - t) + 1.5
            pts.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 0.85))
        d.stroke("ice", pts, lambda t: 0.5 + 1.3 * t, lo=0)
    d.glow_body("ice", ellipse(c, 2.4, 2.0))
    d.embers("ice", 18, (2, 2, 30, 30), seed=9)
    return d.finish()


# ───────────────────────── 공통
def common_warn():
    d = Dot("common")
    for r in (12, 14.5):
        d.stroke("fire", arc((16, 18), r, 200, 340, 20), lambda t: 0.3 + 0.6 * math.sin(t * math.pi), lo=2)
    d.body("gold", [(16, 4), (29, 27), (3, 27)], lo=4, bevel=2.4)
    d.flat(RAMPS["gold"][0], [(14.8, 10.5), (17.2, 10.5), (16.8, 19.5), (15.2, 19.5)])
    d.flat(RAMPS["gold"][0], [(14.9, 21.5), (17.1, 21.5), (17.1, 23.8), (14.9, 23.8)])
    return d.finish()


def common_stun():
    d = Dot("common")
    ring = [(16 + math.cos(a) * 12, 16 + math.sin(a) * 5) for a in np.linspace(0, 2 * math.pi, 48)]
    d.stroke("gold", ring, 0.55, lo=2, core=False)
    d.stroke("gold", [(16 + math.cos(a) * r, 17 + math.sin(a) * r) for a, r in
                      zip(np.linspace(0, 4 * math.pi, 40), np.linspace(0.5, 5, 40))], 0.5, lo=2, glow=False)
    for (x, y, r) in ((6.5, 13, 4.2), (24.5, 11, 4.8), (19, 22.5, 3.6)):
        d.body("gold", star((x, y), r, r * 0.45), bevel=1.4,
               tips=[(p, (p[0] - x, p[1] - y)) for p in star((x, y), r, r * 0.45)[::2]])
    d.sparkle(10, 24, "gold")
    d.sparkle(27, 22, "gold")
    return d.finish()


ICONS = {
    ("minotaur", "charge"): minotaur_charge, ("minotaur", "frenzy"): minotaur_frenzy, ("minotaur", "quake"): minotaur_quake,
    ("minotaur", "horn"): minotaur_horn, ("minotaur", "rage"): minotaur_rage,
    ("nemean_lion", "pounce"): nemean_lion_pounce, ("nemean_lion", "roar"): nemean_lion_roar,
    ("nemean_lion", "hunt"): nemean_lion_hunt, ("nemean_lion", "claw"): nemean_lion_claw,
    ("chimera", "breath"): chimera_breath, ("chimera", "venom"): chimera_venom, ("chimera", "spikes"): chimera_spikes,
    ("chimera", "triple"): chimera_triple,
    ("cerberus", "flame"): cerberus_flame, ("cerberus", "howl"): cerberus_howl, ("cerberus", "hunt"): cerberus_hunt,
    ("cerberus", "gate"): cerberus_gate, ("cerberus", "fury"): cerberus_fury,
    ("hydra", "bite"): hydra_bite, ("hydra", "venom"): hydra_venom, ("hydra", "tempest"): hydra_tempest,
    ("hydra", "regrow"): hydra_regrow, ("hydra", "sever"): hydra_sever,
    ("medusa", "gaze"): medusa_gaze, ("medusa", "zone"): medusa_zone, ("medusa", "serpent"): medusa_serpent,
    ("medusa", "tail"): medusa_tail, ("medusa", "mirror"): medusa_mirror,
    ("scylla", "slam"): scylla_slam, ("scylla", "hounds"): scylla_hounds, ("scylla", "cage"): scylla_cage,
    ("scylla", "maelstrom"): scylla_maelstrom,
    ("common", "warn"): common_warn, ("common", "stun"): common_stun,
}


def render(boss, key):
    return ICONS[(boss, key)]()


if __name__ == "__main__":
    import sys
    from PIL import Image
    S = "/tmp/claude-0/-home-user-minecraft/2d68590e-6d8d-5099-8a63-c0ef9e8e5738/scratchpad/"
    keys = list(ICONS)
    if len(sys.argv) > 1:
        keys = [k for k in keys if k[0] in sys.argv[1:] or k[1] in sys.argv[1:]]
    cols = 6
    Z = 5
    rows = (len(keys) + cols - 1) // cols
    W = Image.new("RGBA", (cols * (32 * Z + 8) + 8, rows * (32 * Z + 8) + 8), (30, 28, 34, 255))
    for i, k in enumerate(keys):
        im = ICONS[k]()
        W.alpha_composite(im.resize((32 * Z, 32 * Z), Image.NEAREST), (8 + (i % cols) * (32 * Z + 8), 8 + (i // cols) * (32 * Z + 8)))
    W.save(S + "dot_icons.png")
    print(len(keys))
