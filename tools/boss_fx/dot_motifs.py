"""도트 모티프 — 아이콘 · 아이템이 함께 쓰는 짐승 머리 · 촉수 · 불꽃 · 돌 조각 등 (지역 좌표 → xf 로 배치)"""
import math

import numpy as np

from dot import RAMPS, along, bez, curve_strip, ellipse, hx, strip, xf


def local_ellipse(cx, cy, rx, ry, n=32, rot=0.0):
    return ellipse((cx, cy), rx, ry, n, rot)


def star(c, r, r2, k=5, rot=-90.0):
    out = []
    for i in range(2 * k):
        a = math.radians(rot + i * 180.0 / k)
        rr = r if i % 2 == 0 else r2
        out.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
    return out


def flame(d, base, h, w, lean=0.0, mat="fire"):
    bx, by = base
    tip = (bx + lean, by - h)
    pts = bez((bx - w, by), (bx - w * 1.1, by - h * 0.45), (bx + lean * 0.3 - w * 0.2, by - h * 0.7), tip, n=16) + \
        bez(tip, (bx + lean * 0.3 + w * 0.5, by - h * 0.6), (bx + w * 1.1, by - h * 0.4), (bx + w, by), n=16) + \
        bez((bx + w, by), (bx + w * 0.5, by + w * 0.7), (bx - w * 0.5, by + w * 0.7), (bx - w, by), n=8)
    return d.glow_body(mat, pts)


def rock(d, c, r, seed=0, mat="stone"):
    rs = np.random.default_rng(seed)
    n = int(rs.integers(5, 8))
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rs.uniform(-0.3, 0.3)
        rr = r * rs.uniform(0.7, 1.15)
        pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
    return d.body(mat, pts, bevel=max(0.8, r * 0.6))


def bull_head(d, c, s=1.0, eye="hell", horns=True, fur="bull"):
    if horns:
        for f in (1, -1):
            h = bez((f * 3.8, -3.6), (f * 9.5, -4.6), (f * 12.2, -8.2), (f * 10.4, -12.6), n=24)
            hp = xf(h, c, s)
            d.body("bone", curve_strip(hp, lambda t: s * (1.8 - 1.6 * t)), bevel=1.3, tips=[end_tip(hp)])
            for q in (0.18, 0.34):                          # 뿔 마디
                i = int(q * 24)
                p = xf([h[i]], c, s)[0]
                d.px(p[0], p[1], RAMPS["bone"][1])
    for f in (1, -1):
        d.body(fur, xf([(f * 4, -3.2), (f * 8.8, -2.4), (f * 8, -0.2), (f * 4.2, 0.4)], c, s), bevel=1.0)
        d.px(*xf([(f * 6.5, -1.6)], c, s)[0], RAMPS["red"][2])
    head = [(-4.6, -5.4), (-1.5, -6.4), (1.5, -6.4), (4.6, -5.4), (5.2, -1), (4, 3.5), (3.4, 8), (-3.4, 8), (-4, 3.5), (-5.2, -1)]
    d.body(fur, xf(head, c, s), bevel=2.4)
    d.body("leather", xf(local_ellipse(0, 6.2, 3.7, 2.5), c, s), lo=2, bevel=1.4)
    for f in (1, -1):
        d.px(*xf([(f * 1.4, 6.2)], c, s)[0], RAMPS["bull"][0])
        d.px(*xf([(f * 2.2, 0.2)], c, s)[0], RAMPS[eye][-1])
        d.px(*xf([(f * 2.2 + f * 1, 0.2)], c, s)[0], RAMPS[eye][-2])
        d.px(*xf([(f * 2.6, -1.0)], c, s)[0], RAMPS["bull"][0])
        d.px(*xf([(f * 1.6, -0.9)], c, s)[0], RAMPS["bull"][0])
    ring = [(xf([(math.cos(a) * 1.5, 8.1 + math.sin(a) * 1.2)], c, s)[0]) for a in np.linspace(0.2, math.pi - 0.2, 9)]
    d.line(ring, RAMPS["gold"][5])


def lion_head(d, c, s=1.0, roar=False, eye="gem_amber"):
    mane = []
    for k in range(28):
        a = 2 * math.pi * k / 28
        r = 10.2 if k % 2 == 0 else 8.0
        mane.append((math.cos(a) * r, math.sin(a) * r * 1.02 + 0.8))
    d.body("mane", xf(mane, c, s), bevel=3.4)
    for f in (1, -1):
        d.body("fur", xf(local_ellipse(f * 4.6, -5.0, 1.7, 1.6), c, s), bevel=1)
    face = [(-4.4, -4.4), (0, -5.2), (4.4, -4.4), (5.3, 0), (3.8, 4.6), (1.9, 6.8), (-1.9, 6.8), (-3.8, 4.6), (-5.3, 0)]
    d.body("fur", xf(face, c, s), bevel=2.6)
    for f in (1, -1):
        d.body("bone", xf(local_ellipse(f * 1.4, 3.4, 1.9, 1.5), c, s), lo=2, bevel=1.0, outline=False)
        e = xf([(f * 2.3, -0.8)], c, s)[0]
        d.px(e[0], e[1], RAMPS[eye][-2])
        d.px(e[0] - f, e[1], RAMPS["mane"][0])
        d.line(xf([(f * 1.2, -2.2), (f * 3.4, -1.8)], c, s), RAMPS["mane"][1])
    d.flat(RAMPS["mane"][0], xf([(-1.5, 1.0), (1.5, 1.0), (0, 2.7)], c, s))
    if roar:
        d.flat(hx("3e0a14"), xf([(-2.6, 4.4), (2.6, 4.4), (1.8, 8.6), (-1.8, 8.6)], c, s))
        d.flat(RAMPS["red"][2], xf([(-1.2, 7.0), (1.2, 7.0), (0.8, 8.2), (-0.8, 8.2)], c, s))
        for f in (1, -1):
            d.px(*xf([(f * 1.7, 4.8)], c, s)[0], RAMPS["bone"][-1])
            d.px(*xf([(f * 1.3, 8.0)], c, s)[0], RAMPS["bone"][-1])


def dog_side(d, c, s=1.0, ang=0.0, flip=False, mat="dfur", eye="hell", open_=False):
    """개 머리 옆모습 (코가 +x)"""
    top = [(-6, 4), (-6.6, -0.5), (-5, -3.2), (-4.6, -8.6), (-2.0, -4.2), (1.2, -3.4), (2.8, -2.4), (8.2, -1.6), (9.4, -0.6)]
    if open_:
        body = top + [(9.2, 0.4), (4.6, 0.8), (2.4, 1.6), (7.6, 3.4), (8.0, 4.4), (6.8, 5.0), (1.6, 4.6), (-1.2, 6.0), (-3.6, 8.0), (-6.2, 7.0)]
    else:
        body = top + [(9.2, 0.9), (7.2, 2.0), (3.2, 2.8), (-0.6, 5.0), (-3.6, 8.0), (-6.2, 7.0)]
    ear = xf([(-4.6, -8.6), (-4.2, -6.6)], c, s, ang, flip)
    d.body(mat, xf(body, c, s, ang, flip), bevel=2.0, tips=[(ear[0], (ear[0][0] - ear[1][0], ear[0][1] - ear[1][1]))])
    d.body(mat, xf([(-4.0, -3.6), (-4.2, -7.0), (-2.6, -4.2)], c, s, ang, flip), lo=2, outline=False, bevel=0.6)
    e = xf([(1.0, -1.8)], c, s, ang, flip)[0]
    d.px(e[0], e[1], RAMPS[eye][-1])
    e2 = xf([(0.0, -1.8)], c, s, ang, flip)[0]
    d.px(e2[0], e2[1], RAMPS[eye][-3])
    n = xf([(8.8, -0.9)], c, s, ang, flip)[0]
    d.px(n[0], n[1], RAMPS["black"][0])
    if open_:
        d.flat(hx("3e0a14"), xf([(9.0, 0.35), (4.6, 0.85), (2.6, 1.6), (7.4, 3.3)], c, s, ang, flip))
        for p in ((7.6, 0.9), (5.2, 1.1), (6.8, 2.9)):
            q = xf([p], c, s, ang, flip)[0]
            d.px(q[0], q[1], RAMPS["bone"][-1])


def dog_front(d, c, s=1.0, mat="dfur", eye="hell"):
    head = [(-4.2, -3.2), (-6.0, -9.4), (-2.2, -4.8), (2.2, -4.8), (6.0, -9.4), (4.2, -3.2), (4.8, 1), (2.8, 5), (1.4, 7.4),
            (-1.4, 7.4), (-2.8, 5), (-4.8, 1)]
    ears = [(xf([(f * 6.0, -9.4)], c, s)[0], (f * 0.4, -1.0)) for f in (1, -1)]
    d.body(mat, xf(head, c, s), bevel=2.2, tips=ears)
    for f in (1, -1):
        d.body(mat, xf([(f * 4.4, -4.2), (f * 5.4, -7.8), (f * 3.0, -4.6)], c, s), lo=2, outline=False, bevel=0.5)
        a = xf([(f * 1.6, -0.6)], c, s)[0]
        b = xf([(f * 3.0, -1.4)], c, s)[0]
        d.px(a[0], a[1], RAMPS[eye][-1])
        d.px(b[0], b[1], RAMPS[eye][-2])
    d.body(mat, xf(local_ellipse(0, 4.4, 2.4, 2.4), c, s), lo=2, outline=False, bevel=1.2)
    n = xf([(0, 5.4)], c, s)[0]
    d.px(n[0], n[1], RAMPS["black"][0])
    d.px(n[0] - 1, n[1], RAMPS["black"][0])
    for f in (1, -1):
        q = xf([(f * 1.5, 7.6)], c, s)[0]
        d.px(q[0], q[1], RAMPS["bone"][-1])


def snake_head(d, c, s=1.0, ang=0.0, flip=False, mat="green", eye="gem_amber", open_=False):
    if open_:
        up = [(-3, -1.6), (0, -2.8), (3.2, -2.8), (5.8, -2.2), (6.4, -1.4), (3.2, -0.6), (0.4, 0.2)]
        lo = [(0.4, 0.6), (3.0, 1.8), (5.4, 3.4), (5.2, 4.0), (2.6, 3.4), (0, 2.6), (-3, 1.8)]
        d.flat(hx("3e0a14"), xf([(0, 0.2), (6.2, -1.4), (5.4, 3.6), (0, 0.8)], c, s, ang, flip))
        d.body(mat, xf(up + [(-3, 0.4)], c, s, ang, flip), bevel=1.4)
        d.body(mat, xf(lo + [(-3, 0.4)], c, s, ang, flip), bevel=1.0)
        for p in ((5.4, -1.0), (4.8, 2.9)):
            q = xf([p], c, s, ang, flip)[0]
            d.px(q[0], q[1], RAMPS["bone"][-1])
    else:
        head = [(-3, -1.8), (0, -2.6), (2.8, -2.4), (4.8, -1.2), (5.4, 0), (4.8, 1.2), (2.8, 1.9), (0, 2.2), (-3, 1.6)]
        d.body(mat, xf(head, c, s, ang, flip), bevel=1.6)
    e = xf([(1.8, -1.2)], c, s, ang, flip)[0]
    d.px(e[0], e[1], RAMPS[eye][-2])


def tentacle(d, pts, w0, w1, mat="flesh", suckers=True, side=1):
    d.body(mat, curve_strip(pts, lambda t: w0 + (w1 - w0) * t), bevel=max(1.0, w0 * 0.8))
    if suckers:
        n = len(pts)
        step = max(2, n // 9)
        for i in range(step, n - 2, step):
            p, q = pts[i], pts[min(n - 1, i + 1)]
            dx, dy = q[0] - p[0], q[1] - p[1]
            Ln = math.hypot(dx, dy) or 1
            w = w0 + (w1 - w0) * i / (n - 1)
            x, y = p[0] - dy / Ln * w * 0.55 * side, p[1] + dx / Ln * w * 0.55 * side
            d.px(x, y, RAMPS[mat][-1])


def labrys(d, a, b, s=1.0, blade="steel", edge=True):
    """양날 도끼: 날마다 위 · 아래 뿔 끝이 뾰족한 초승달"""
    d.body("wood", strip(a, b, lambda t: 1.1 * s), bevel=1.0)
    for k in range(4):
        q = 0.06 + k * 0.06
        d.body("leather", strip(along(a, b, q), along(a, b, q + 0.035), lambda t: 1.35 * s), bevel=0.8)
    d.body("steel", [along(a, b, 1.0, 0.7 * s), along(a, b, 1.0, -0.7 * s), along(a, b, 1.12)], bevel=0.8,
           tips=[(along(a, b, 1.12), (b[0] - a[0], b[1] - a[1]))])
    for sgn in (1, -1):
        h_top, h_bot = along(a, b, 1.1, sgn * 8.2 * s), along(a, b, 0.52, sgn * 8.2 * s)
        bl = bez(along(a, b, 0.93, sgn * 1.1 * s), along(a, b, 0.97, sgn * 4.0 * s), h_top, n=10) + \
            bez(h_top, along(a, b, 0.81, sgn * 11.4 * s), h_bot, n=20) + \
            bez(h_bot, along(a, b, 0.64, sgn * 4.0 * s), along(a, b, 0.7, sgn * 1.1 * s), n=10)
        ctr = along(a, b, 0.81, sgn * 5.0 * s)
        d.body(blade, bl, bevel=2.4 * s, tips=[(h_top, (h_top[0] - ctr[0], h_top[1] - ctr[1])), (h_bot, (h_bot[0] - ctr[0], h_bot[1] - ctr[1]))])
        if edge:
            e = bez(along(a, b, 1.02, sgn * 8.0 * s), along(a, b, 0.81, sgn * 10.4 * s), along(a, b, 0.6, sgn * 8.0 * s), n=18)
            d.line(e, RAMPS[blade][-1])
    d.body("gold", ellipse(along(a, b, 0.81), 2.0 * s, 2.0 * s), bevel=1.2)
    g = along(a, b, 0.81)
    d.px(g[0], g[1], RAMPS["gem_red"][2])
    d.px(g[0] - 1, g[1] - 1, RAMPS["gem_red"][-1])


def end_tip(pts, k=3):
    """곡선 끝점과 그 방향 (뾰족한 끝 등록용)"""
    p, q = pts[-1], pts[-1 - k]
    return p, (p[0] - q[0], p[1] - q[1])
