"""플레이어 아이템 — 32x32 도트, 투명 바탕 (바닐라와 같은 방향: 손잡이 왼쪽 아래 → 끝 오른쪽 위)"""
import math

import numpy as np

from dot import RAMPS, Dot, along, bez, curve_strip, ellipse, hx, strip
from dot_motifs import end_tip, labrys as labrys_m, lion_head, snake_head, star


def grip(d, a, b, t0, t1, w=1.2, mat="leather", bands=4):
    d.body(mat, strip(along(a, b, t0), along(a, b, t1), lambda t: w), bevel=1.0)
    for k in range(bands):
        q = t0 + (t1 - t0) * (k + 0.5) / bands
        p0, p1 = along(a, b, q, w), along(a, b, q + (t1 - t0) / bands * 0.5, -w)
        d.line([p0, p1], RAMPS[mat][1])


def sword(blade_mat="steel", guard="bronze", pommel="bronze", gem=None, prof=None, fuller=(0.05, 0.62), glow=None):
    d = Dot()
    a, b = (4, 28), (29, 3)
    grip(d, a, b, 0.05, 0.22, 1.25)
    d.body(pommel, ellipse(along(a, b, 0.035), 2.1, 2.1), bevel=1.3)
    prof = prof or (lambda t: 2.1 if t < 0.64 else 2.1 * max(0.0, 1 - (t - 0.64) / 0.36))
    bs = along(a, b, 0.24)
    d.blade(blade_mat, bs, b, prof, fuller=fuller)
    if glow:
        d.stroke(glow, [along(bs, b, 0.05), along(bs, b, 0.8)], 0.5, lo=3, core=False)
    d.body(guard, strip(along(a, b, 0.235, 4.8), along(a, b, 0.235, -4.8), lambda t: 0.9 + 0.5 * math.sin(t * math.pi)), bevel=1.0)
    if gem:
        g = along(a, b, 0.235)
        d.body(gem, ellipse(g, 1.1, 1.1), bevel=0.8, outline=False)
        d.px(g[0] - 0.5, g[1] - 0.5, RAMPS[gem][-1])
    return d


def infantry_sword():
    d = sword("steel", "bronze", "bronze", gem="gem_red")
    d.sparkle(24, 8, "silver")
    return d.finish()


def xiphos():
    def prof(t):
        w = 1.5 + 1.6 * math.sin(min(1, t * 1.25) * math.pi) ** 1.1
        if t > 0.66:
            w *= max(0.0, 1 - (t - 0.66) / 0.34)
        return w
    d = sword("gold", "gold", "gold", gem="gem_blue", prof=prof, fuller=(0.04, 0.55))
    d.sparkle(21, 10, "gold")
    return d.finish()


def kopis():
    d = Dot()
    a, b = (5, 28), (28, 5)
    grip(d, a, b, 0.05, 0.22, 1.2, bands=3)
    hook = bez(along(a, b, 0.06), along(a, b, -0.04, 1.5), along(a, b, -0.02, 4.0), n=10)
    d.body("bronze", curve_strip(hook, lambda t: 1.4 - 0.6 * t), bevel=1.0)

    def L(t, o):
        return along(a, b, t, o)
    spine = [L(0.24, 1.3), L(0.45, 1.8), L(0.66, 1.4), L(0.84, 0.2), L(0.97, -1.4), L(1.0, -2.2)]
    edge = [L(1.0, -2.2), L(0.93, -4.4), L(0.8, -5.2), L(0.62, -4.4), L(0.44, -2.8), L(0.24, -1.4)]
    blade = bez(spine[0], spine[1], spine[2], spine[3], n=14) + bez(spine[3], spine[4], spine[5], n=6) + \
        bez(edge[0], edge[1], edge[2], edge[3], n=14) + bez(edge[3], edge[4], edge[5], n=8)
    d.body("steel", blade, bevel=2.6, lo=2, tips=[(L(1.0, -2.2), (b[0] - a[0] + 3, b[1] - a[1] + 3))])
    e = bez(L(0.95, -3.0), L(0.82, -4.4), L(0.62, -3.6), L(0.4, -1.8), n=16)
    d.line(e, RAMPS["steel"][-1])
    d.line(bez(L(0.28, 0.5), L(0.5, 0.6), L(0.72, 0.0), n=10), RAMPS["steel"][3])
    d.body("bronze", strip(L(0.235, 3.0), L(0.235, -3.4), lambda t: 0.9), bevel=0.9)
    d.sparkle(*L(0.78, -3.4), "silver")
    return d.finish()


def dagger():
    d = Dot()
    a, b = (6, 26), (27, 5)
    grip(d, a, b, 0.06, 0.3, 1.2, bands=3)
    ring = ellipse(along(a, b, 0.02), 2.0, 2.0)
    d.body("steel", ring, bevel=1.0, lo=2)
    d.px(*along(a, b, 0.02), RAMPS["steel"][0])
    d.blade("steel", along(a, b, 0.33), b, lambda t: 1.9 if t < 0.6 else 1.9 * max(0.05, 1 - (t - 0.6) / 0.4), fuller=(0.05, 0.5))
    d.body("dsteel", strip(along(a, b, 0.32, 3.4), along(a, b, 0.32, -3.4), lambda t: 0.9), bevel=0.9)
    return d.finish()


def hephaestus_sword():
    d = sword("dsteel", "gold", "gold", gem="gem_amber", glow="fire",
              prof=lambda t: 2.4 if t < 0.64 else 2.4 * max(0.0, 1 - (t - 0.64) / 0.36), fuller=None)
    a, b = (4, 28), (29, 3)
    for q in (0.4, 0.55, 0.7):
        p = along(a, b, q)
        for s in (1, -1):
            d.px(*along(a, b, q + 0.03, s * 1.6), RAMPS["fire"][4])
    d.embers("fire", 12, (12, 1, 31, 20), seed=2)
    d.sparkle(27, 5, "fire")
    return d.finish()


def hydra_fang():
    d = Dot()
    a, b = (4, 28), (29, 3)
    grip(d, a, b, 0.05, 0.22, 1.3, mat="emerald")
    d.body("emerald", ellipse(along(a, b, 0.03), 2.0, 2.0), bevel=1.2)
    fang = bez(along(a, b, 0.24), along(a, b, 0.5, -2.2), along(a, b, 0.8, -2.0), along(a, b, 1.0, 1.2), n=30)
    d.body("bone", curve_strip(fang, lambda t: 2.9 * (1 - t) ** 0.9), bevel=2.2, tips=[end_tip(fang)])
    d.stroke("venom", fang[2:22], 0.45, lo=3, core=False)
    for s in (1, -1):
        d.body("emerald", [along(a, b, 0.23, s * 1.2), along(a, b, 0.2, s * 5.2), along(a, b, 0.3, s * 3.0), along(a, b, 0.27, s * 1.2)],
               bevel=0.8)
    tip = fang[-1]
    for k, (dx, dy) in enumerate(((0.5, 3), (-1.0, 6))):
        d.glow_body("venom", [(tip[0] + dx, tip[1] + dy - 1.6)] + ellipse((tip[0] + dx, tip[1] + dy), 0.9, 0.9, 12)[1:6])
    return d.finish()


def labrys():
    d = Dot()
    labrys_m(d, (3.5, 29), (23.5, 9), 1.08)
    tas = bez(along((3.5, 29), (23.5, 9), 0.4, 1.3), along((3.5, 29), (23.5, 9), 0.34, 4.6), along((3.5, 29), (23.5, 9), 0.26, 4.2), n=10)
    d.body("red", curve_strip(tas, lambda t: 0.6 + t * 1.0), bevel=1.0)
    return d.finish()


def siege_hammer():
    d = Dot()
    a, b = (3.5, 29), (22, 10.5)
    d.body("wood", strip(a, b, lambda t: 1.15), bevel=1.0)
    grip(d, a, b, 0.04, 0.3, 1.35, bands=5)
    for q in (0.5, 0.72):
        d.body("bronze", strip(along(a, b, q), along(a, b, q + 0.04), lambda t: 1.5), bevel=0.8)
    h0, h1 = along(a, b, 0.97, 8.0), along(a, b, 0.97, -8.0)
    d.body("steel", strip(h0, h1, lambda t: 3.3 + 0.6 * (abs(t - 0.5) > 0.38)), bevel=2.2)
    for t in (0.22, 0.78):
        d.body("bronze", strip(along(h0, h1, t - 0.05), along(h0, h1, t + 0.05), lambda q: 3.8), bevel=1.0)
    d.body("steel", [along(a, b, 1.1, 1.0), along(a, b, 1.1, -1.0), along(a, b, 1.34)], bevel=0.9, tips=[(along(a, b, 1.34), (1, -1))])
    d.px(*along(h0, h1, 0.5), RAMPS["gem_red"][2])
    return d.finish()


def scylla_trident():
    d = Dot()
    a, b = (2.5, 29.5), (22, 10)
    d.body("bronze", strip(a, b, lambda t: 1.05), bevel=1.0)
    pts = [along(a, b, 0.15 + 0.5 * i / 30, 1.4 * math.sin(i * 0.9)) for i in range(31)]
    d.body("flesh", curve_strip(pts, lambda t: 0.8), bevel=0.8)
    cb0, cb1 = along(a, b, 0.97, 5.8), along(a, b, 0.97, -5.8)
    d.body("silver", strip(cb0, cb1, lambda t: 1.2), bevel=1.0)
    for off, ln in ((0, 1.42), (5.0, 1.3), (-5.0, 1.3)):
        base = along(a, b, 0.97, off)
        tip = along(a, b, ln, off * 0.9)
        d.blade("silver", base, tip, lambda t: 0.75 if t < 0.55 else 1.4 * (1 - (t - 0.55) / 0.45), fuller=None)
        if off:
            barb = along(base, tip, 0.62, -0.8 if off > 0 else 0.8)
            d.px(*barb, RAMPS["silver"][2])
    d.glow_body("water", ellipse(along(a, b, 0.97), 1.5, 1.5))
    d.px(*along(a, b, 0.97), RAMPS["water"][-1])
    return d.finish()


def spear(tip_left=False):
    d = Dot()
    if tip_left:
        a, b = (29.5, 29.5), (3, 3)
    else:
        a, b = (2.5, 29.5), (29, 3)
    d.body("bronze", strip(a, along(a, b, 0.07), lambda t: 0.5 + 0.6 * t), bevel=0.8)
    d.body("wood", strip(along(a, b, 0.06), along(a, b, 0.72), lambda t: 0.95), bevel=0.9)
    grip(d, a, b, 0.38, 0.5, 1.2, bands=3)
    d.body("bronze", strip(along(a, b, 0.7), along(a, b, 0.76), lambda t: 1.3), bevel=0.8)
    d.blade("steel", along(a, b, 0.75), b, lambda t: 0.9 + 1.5 * t / 0.3 if t < 0.3 else 2.4 * (1 - (t - 0.3) / 0.7), fuller=None)
    return d.finish()


def dory():
    return spear(False)


def dory_in_hand():
    return spear(True)


def helmet(metal="bronze", crest="red", eye=None, trim="gold"):
    d = Dot()
    arc = bez((9, 8), (11, 0.5), (25, 0.5), (28.5, 10), n=30)
    d.body(crest, curve_strip(arc, lambda t: 1.6 + 1.6 * math.sin(t * math.pi)), bevel=1.6)
    for i in range(3, 28, 3):
        p = arc[i]
        d.line([(p[0], p[1] - 1.5), (p[0] + 0.8, p[1] + 1.6)], RAMPS[crest][1])
    shell = [(6.5, 17), (7, 11), (10, 6.5), (15, 5), (21, 5.5), (25, 9), (26.5, 14), (26, 20), (27.8, 25), (25, 27.8), (21, 26.8),
             (19, 23.2), (17, 22.8), (16.2, 27.8), (13, 29.3), (9.6, 28.2), (7.6, 25), (6.6, 21)]
    d.body(metal, shell, bevel=3.0)
    if eye:
        d.glow_body(eye, [(6.8, 15.6), (9, 13.8), (14.2, 14), (13.4, 16.4), (9, 16.8)])
    else:
        d.flat(RAMPS["black"][0], [(6.8, 15.6), (9, 13.8), (14.2, 14), (13.4, 16.4), (9, 16.8)])
    d.flat(RAMPS["black"][0], [(6.6, 17), (9.2, 17), (9.6, 24.5), (7.8, 25.2)])
    d.line([(8, 12.6), (15, 12.2)], RAMPS[trim][-2])
    d.line(bez((16.4, 27.4), (17, 23), (19, 23.4), (21.2, 26.4), n=8), RAMPS[trim][-2])
    d.line([(10, 28), (13, 28.6)], RAMPS[trim][-3])
    d.line(bez((21, 6.6), (24, 9), (25.2, 13), n=8), RAMPS[metal][-1])
    return d


def corinthian():
    return helmet("brass", "red").finish()


def hades_helm():
    d = helmet("dsteel", "soul", eye="soul", trim="silver")
    d.stroke("soul", bez((27, 26), (30, 22), (28, 18), (31, 14), n=12), lambda t: 0.3 + 0.5 * (1 - t), lo=2, glow=False)
    d.embers("soul", 8, (2, 2, 30, 30), seed=5)
    return d.finish()


def lion_pelt():
    d = Dot()
    cloak = [(8, 11), (24, 11)] + bez((24, 11), (29, 17), (29.5, 24), n=10) + \
        [(28, 29), (25.5, 27), (23, 30.5), (20, 27.8), (16, 31), (12, 27.8), (9, 30.5), (6.5, 27), (4, 29)] + \
        bez((2.5, 24), (3, 17), (8, 11), n=10)
    d.body("fur", cloak, bevel=3.2)
    for x in (9, 13, 19, 23):
        d.line([(x, 20), (x - 0.5, 26)], RAMPS["fur"][2])
    for f in (1, -1):
        paw = bez((16 + f * 7, 12), (16 + f * 5, 17), (16 + f * 1.5, 18.5), n=10)
        d.body("fur", curve_strip(paw, lambda t: 1.6), lo=2, bevel=1.2)
        for k in (-1, 0, 1):
            d.px(16 + f * 1.2, 18.5 + k, RAMPS["bone"][-1])
    d.body("gold", ellipse((16, 18.5), 1.8, 1.8), bevel=1.0)
    lion_head(d, (16, 9.5), 0.78)
    return d.finish()


def cerberus_collar():
    d = Dot()
    c = (16, 15)
    for k in range(10):
        a = k / 10 * 2 * math.pi + 0.3
        base = (c[0] + math.cos(a) * 9.5, c[1] + math.sin(a) * 9.5)
        tip = (c[0] + math.cos(a) * 14.6, c[1] + math.sin(a) * 14.6)
        nx, ny = -math.sin(a), math.cos(a)
        if 1.2 < a < 2.0:
            continue
        d.body("steel", [(base[0] + nx * 1.6, base[1] + ny * 1.6), tip, (base[0] - nx * 1.6, base[1] - ny * 1.6)], bevel=1.0,
               tips=[(tip, (tip[0] - base[0], tip[1] - base[1]))])
    ring = ellipse(c, 11.5, 11.5, 64) + [ellipse(c, 11.5, 11.5, 64)[0]] + ellipse(c, 7.2, 7.2, 64)[::-1] + [ellipse(c, 7.2, 7.2, 64)[-1]]
    d.body("leather", ring, bevel=1.8, lo=1, hi=4)
    for k in range(14):
        a = k / 14 * 2 * math.pi
        d.px(c[0] + math.cos(a) * 9.4, c[1] + math.sin(a) * 9.4, RAMPS["gold"][5])
    # 방울 (영혼석)
    d.body("gold", ellipse((16, 27.5), 3.2, 3.2), bevel=1.4)
    d.glow_body("soul", ellipse((16, 27.5), 1.9, 1.9))
    d.px(15, 26.5, RAMPS["soul"][-1])
    for a in (math.pi * 0.2, math.pi * 0.8):
        q = (c[0] + math.cos(a) * 9.4, c[1] + math.sin(a) * 9.4)
        d.glow_body("soul", ellipse(q, 1.6, 1.6))
    return d.finish()


def medusa_head():
    d = Dot()
    for k in range(9):
        a = math.radians(200 + k * 17.5)
        s0 = (16 + math.cos(a) * 5, 14 + math.sin(a) * 5)
        s3 = (16 + math.cos(a) * 13.5, 14 + math.sin(a) * 12)
        mid = (16 + math.cos(a + 0.35 * (1 if k % 2 else -1)) * 9.5, 14 + math.sin(a + 0.35 * (1 if k % 2 else -1)) * 9)
        hair = bez(s0, mid, s3, n=12)
        d.body("emerald", curve_strip(hair, lambda t: 1.5 - t * 0.5), bevel=0.9)
        ang = math.degrees(math.atan2(s3[1] - mid[1], s3[0] - mid[0]))
        snake_head(d, s3, 0.55, ang=ang, mat="emerald", eye="fire")
    face = [(10.5, 12), (16, 9.5), (21.5, 12), (22, 18), (19.5, 24), (16, 26), (12.5, 24), (10, 18)]
    d.body("skin", face, bevel=3.0)
    d.body("gold", curve_strip(bez((10, 11.5), (16, 7.5), (22, 11.5), n=14), lambda t: 0.9), bevel=0.8)
    d.px(16, 9, RAMPS["gem_red"][2])
    for f in (1, -1):
        e = (16 + f * 2.8, 16)
        d.glow_body("gem_amber", ellipse(e, 1.4, 0.9))
        d.line([(16 + f * 1.4, 14.2), (16 + f * 4.2, 14.8)], RAMPS["skin"][0])
    d.flat(hx("3e0a14"), [(14.3, 21), (17.7, 21), (17, 22.8), (15, 22.8)])
    d.px(14.6, 21.3, RAMPS["bone"][-1])
    d.px(17.3, 21.3, RAMPS["bone"][-1])
    for x, y in ((14, 27.5), (17.5, 28.5), (16, 30)):
        d.px(x, y, RAMPS["blood"][-1])
    return d.finish()


def golden_apple():
    d = Dot()
    body = bez((16, 9), (8, 4), (1.5, 15), (8, 27), n=30) + bez((8, 27), (11, 30.5), (14, 29), (16, 28.5), n=10) + \
        bez((16, 28.5), (18, 29), (21, 30.5), (24, 27), n=10) + bez((24, 27), (30.5, 15), (24, 4), (16, 9), n=30)
    d.body("gold", body, lo=2, bevel=6.0)
    d.body("wood", curve_strip(bez((16, 10), (16, 6), (17.5, 3), n=10), lambda t: 0.9 - t * 0.3), bevel=0.8)
    leaf = bez((17.5, 5), (21, 1), (26, 2.5), n=12) + bez((26, 2.5), (23, 6.5), (17.5, 5), n=12)
    d.body("leaf", leaf, bevel=1.2)
    d.line([(18.5, 4.8), (24, 3)], RAMPS["leaf"][1])
    d.line([(8, 14), (9.5, 11.5)], RAMPS["gold"][-1])
    d.sparkle(24, 20, "gold", big=True)
    d.sparkle(6, 7, "gold")
    return d.finish()


def menu():
    d = Dot()
    for f in (1, -1):
        stem = [(16 + f * math.cos(a) * 12.5, 17 + math.sin(a) * 12.5) for a in np.linspace(math.pi * 0.55, math.pi * 1.4, 30)]
        d.body("gold", curve_strip(stem, lambda t: 0.6), bevel=0.6)
        for k in range(7):
            p = stem[3 + k * 4]
            a = math.atan2(p[1] - 17, p[0] - 16)
            for s in (1, -1):
                rot = a + s * 0.55 + (math.pi / 2) * -f
                d.body("leaf" if False else "gold", ellipse((p[0] + math.cos(a + s * 0.5) * 1.6, p[1] + math.sin(a + s * 0.5) * 1.6),
                                                            2.2, 0.9, 16, rot=a + s * 0.9), bevel=0.8)
    bolt = [(18.5, 4), (11, 17), (15.5, 17), (13, 28), (21.5, 13), (16.8, 13), (20, 4)]
    d.glow_body("ice", bolt, lo=2)
    d.sparkle(24, 6, "ice")
    return d.finish()


def hero():
    d = Dot()
    c = (16, 16)
    rim = [(c[0] + math.cos(a) * (14.2 + 0.8 * (i % 2)), c[1] + math.sin(a) * (14.2 + 0.8 * (i % 2))) for i, a in
           enumerate(np.linspace(0, 2 * math.pi, 33)[:-1])]
    d.body("gold", rim, bevel=2.2)
    d.body("red", ellipse(c, 11, 11, 48), bevel=3.0, lo=1, hi=4)
    crest = bez((11, 12), (12, 5.5), (20, 5.5), (22, 11), n=16)
    d.body("gold", curve_strip(crest, lambda t: 0.9 + 0.9 * math.sin(t * math.pi)), lo=3, bevel=0.9)
    hel = [(10.5, 17), (11, 13), (13.5, 10.5), (18.5, 10.5), (21.5, 13.5), (21.8, 18), (22.8, 22), (20, 23.5), (18.5, 20.5),
           (16.8, 20.5), (16.2, 24), (13.5, 24.5), (11.5, 22)]
    d.body("gold", hel, bevel=2.2, lo=2)
    d.flat(RAMPS["red"][0], [(10.8, 15.5), (12.5, 14.2), (15.8, 14.4), (15.2, 16.2), (12.5, 16.4)])
    d.flat(RAMPS["red"][0], [(10.8, 16.8), (12.6, 16.8), (12.8, 21.8), (11.8, 22)])
    d.sparkle(24, 8, "gold")
    return d.finish()


def bow(kind="archer", pull=0):
    """pull 0 = 쉬는 모양, 1..3 = 당김 단계. 끝이 오른쪽 위 · 왼쪽 아래, 손잡이가 왼쪽 위로 휜다"""
    d = Dot()
    top, bot = (29.5, 2.5), (2.5, 29.5)
    g = 6.5 + pull * 0.4
    grip_p = (g, g)
    limb_mat = "wood" if kind == "archer" else "bone"
    smat = "string" if kind == "archer" else "fire"
    k = [0, 3.0, 5.0, 7.0][pull]
    pp = (16 + k, 16 + k)
    if pull == 0:
        d.line([top, bot], RAMPS[smat][-2])
    else:
        d.line([top, pp], RAMPS[smat][-2])
        d.line([pp, bot], RAMPS[smat][-2])
    up = bez(grip_p, (12, 0.5), (22, 0), top, n=26)
    dn = bez(grip_p, (0.5, 12), (0, 22), bot, n=26)
    for limb in (up, dn):
        d.body(limb_mat, curve_strip(limb, lambda t: 1.5 - t * 1.3), bevel=1.2, tips=[end_tip(limb)])
        if kind == "chimera":
            d.stroke("fire", limb[5:18], 0.35, lo=3, core=False)
        band = limb[20]
        d.body("bronze" if kind == "archer" else "gold", ellipse(band, 1.0, 1.0), bevel=0.8)
    d.body("leather" if kind == "archer" else "red", ellipse(grip_p, 2.3, 2.3), bevel=1.2)
    d.px(grip_p[0], grip_p[1], RAMPS["gold"][5])
    if pull > 0:
        tip = (grip_p[0] - 3 + pull * 0.3, grip_p[1] - 3 + pull * 0.3)
        d.body("wood", strip(pp, tip, lambda t: 0.5), bevel=0.5)
        hm = "steel" if kind == "archer" else "fire"
        hd = [(tip[0] - 2.8, tip[1] - 2.8), (tip[0] + 1.6, tip[1] - 0.2), (tip[0] - 0.2, tip[1] + 1.6)]
        if kind == "archer":
            d.body(hm, hd, bevel=0.8, tips=[(hd[0], (-1, -1))])
        else:
            d.glow_body(hm, hd)
        fm = "marble" if kind == "archer" else "red"
        for s in (1, -1):
            d.body(fm, [pp, (pp[0] - 3 + s * 1.6, pp[1] - 3 - s * 1.6), (pp[0] - 1.2 + s * 1.6, pp[1] - 1.2 - s * 1.6)], bevel=0.6)
    return d.finish()


def crossbow(state="standby"):
    """아르테미스의 석궁: 개머리 오른쪽 아래 → 앞 왼쪽 위, 초승달 은빛 활대"""
    d = Dot()
    a, b = (29.5, 29.5), (5, 5)
    back = {"standby": 0.0, "pull0": 0.08, "pull1": 0.15, "pull2": 0.22, "arrow": 0.22}[state]
    cp = along(a, b, 0.8)
    t_up = along(a, b, 0.7, 12.5)
    t_dn = along(a, b, 0.7, -12.5)
    latch = along(a, b, 0.72 - back)
    d.line([t_up, latch], RAMPS["string"][-2])
    d.line([t_dn, latch], RAMPS["string"][-2])
    d.body("black", strip(a, b, lambda t: 1.9 - 0.6 * t + (0.8 if t < 0.25 else 0)), bevel=1.6)
    d.line([along(a, b, 0.3), along(a, b, 0.92)], RAMPS["silver"][4])
    for s in (0.1, 0.2):
        d.body("silver", strip(along(a, b, s), along(a, b, s + 0.03), lambda t: 2.4), bevel=0.8)
    d.body("silver", curve_strip(bez(along(a, b, 0.44, -1.6), along(a, b, 0.47, -3.4), along(a, b, 0.52, -3.2), n=8), lambda t: 0.5), bevel=0.5)
    for sgn, tip in ((1, t_up), (-1, t_dn)):
        limb = bez(cp, along(a, b, 0.86, sgn * 7), tip, n=24)
        d.body("silver", curve_strip(limb, lambda t: 1.5 * (1 - t) + 0.1), bevel=1.2, tips=[end_tip(limb)])
    d.body("silver", ellipse(cp, 2.2, 2.2), bevel=1.2)
    d.glow_body("gem_blue", ellipse(cp, 1.2, 1.2))
    if state == "arrow":
        tip = along(a, b, 1.04)
        d.body("gold", strip(latch, tip, lambda t: 0.5), bevel=0.5)
        d.body("silver", [along(a, b, 1.12), along(a, b, 1.0, 1.6), along(a, b, 1.0, -1.6)], bevel=0.8,
               tips=[(along(a, b, 1.12), (b[0] - a[0], b[1] - a[1]))])
    else:
        d.body("silver", ellipse(latch, 1.0, 1.0), bevel=0.8)
    return d.finish()


def hoplon_face():
    d = Dot()
    c = (16, 16)
    d.body("bronze", ellipse(c, 15.9, 15.9, 96), bevel=2.4, outline=False)
    d.body("red", ellipse(c, 12.6, 12.6, 96), bevel=3.0, lo=1, hi=4, outline=False)
    d.body("gold", star(c, 9.8, 3.0, k=16), bevel=1.6, outline=False)
    d.body("gold", ellipse(c, 2.6, 2.6), bevel=1.4, outline=False)
    for k in range(20):
        a = 2 * math.pi * k / 20
        d.px(c[0] + math.cos(a) * 14.2, c[1] + math.sin(a) * 14.2, RAMPS["gold"][5])
    return d.finish()


def hoplon_back():
    d = Dot()
    c = (16, 16)
    d.body("bronze", ellipse(c, 15.9, 15.9, 96), bevel=2.4, outline=False)
    d.body("wood", ellipse(c, 14, 14, 96), bevel=2.0, lo=1, hi=4, outline=False)
    for x in range(4, 29, 3):
        d.line([(x, 3), (x, 29)], RAMPS["wood"][2])
    d.body("leather", strip((5.5, 16), (26.5, 16), lambda t: 1.4), bevel=0.8, outline=False)
    d.body("leather", strip((16, 9.5), (16, 22.5), lambda t: 1.2), bevel=0.8, outline=False)
    for x in (6.5, 25.5):
        d.body("bronze", ellipse((x, 16), 1.1, 1.1), bevel=0.8, outline=False)
    return d.finish()


SPRITES = {
    "infantry_sword": infantry_sword, "xiphos": xiphos, "kopis": kopis, "dagger": dagger, "hephaestus_sword": hephaestus_sword,
    "hydra_fang": hydra_fang, "labrys": labrys, "siege_hammer": siege_hammer, "scylla_trident": scylla_trident,
    "dory": dory, "dory_in_hand": dory_in_hand, "corinthian": corinthian, "hades_helm": hades_helm, "lion_pelt": lion_pelt,
    "cerberus_collar": cerberus_collar, "medusa_head": medusa_head, "golden_apple": golden_apple, "menu": menu, "hero": hero,
}
for _k in ("archer", "chimera"):
    SPRITES[f"{_k}_bow"] = (lambda k=_k: bow(k, 0))
    for _p in range(3):
        SPRITES[f"{_k}_bow_pulling_{_p}"] = (lambda k=_k, q=_p: bow(k, q + 1))
for _s, _n in (("standby", "artemis_crossbow"), ("pull0", "artemis_crossbow_pulling_0"), ("pull1", "artemis_crossbow_pulling_1"),
               ("pull2", "artemis_crossbow_pulling_2"), ("arrow", "artemis_crossbow_arrow")):
    SPRITES[_n] = (lambda s=_s: crossbow(s))

if __name__ == "__main__":
    from PIL import Image
    S = "/tmp/claude-0/-home-user-minecraft/2d68590e-6d8d-5099-8a63-c0ef9e8e5738/scratchpad/"
    names = list(SPRITES) + ["hoplon_face", "hoplon_back"]
    fns = dict(SPRITES, hoplon_face=hoplon_face, hoplon_back=hoplon_back)
    cols, Z = 8, 4
    rows = (len(names) + cols - 1) // cols
    W = Image.new("RGBA", (cols * (32 * Z + 12) + 8, rows * (32 * Z + 12) + 8), (198, 196, 190, 255))
    slot = Image.new("RGBA", (32 * Z + 8, 32 * Z + 8), (139, 139, 139, 255))
    for i, n in enumerate(names):
        x, y = 8 + (i % cols) * (32 * Z + 12), 8 + (i // cols) * (32 * Z + 12)
        W.alpha_composite(slot, (x - 4, y - 4))
        W.alpha_composite(fns[n]().resize((32 * Z, 32 * Z), Image.NEAREST), (x, y))
    W.save(S + "dot_items.png")
    print(len(names))
