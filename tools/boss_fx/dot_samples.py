"""도트 시안: 스킬 아이콘 4 + 아이템 4"""
import math

from dot import Dot, RAMPS, along, arc, bez, curve_strip, ellipse, strip


def ic_minotaur_frenzy():
    d = Dot("minotaur")
    c = (16, 16)
    # 회전 궤적 두 줄 (꼬리 → 머리)
    d.stroke("fire", arc(c, 11.5, 200, 470, 50), lambda t: 0.6 + 1.9 * t)
    d.stroke("fire", arc(c, 7.5, 20, 290, 40), lambda t: 0.5 + 1.4 * t)
    # 라브리스
    d.body("wood", strip((10, 23), (21, 10), lambda t: 0.9))
    for sgn in (1, -1):
        blade = [along((10, 23), (21, 10), 0.72, sgn * 1.0)] + \
            bez(along((10, 23), (21, 10), 0.55, sgn * 1.2), along((10, 23), (21, 10), 0.66, sgn * 6.8),
                along((10, 23), (21, 10), 1.02, sgn * 5.2), n=16) + [along((10, 23), (21, 10), 0.92, sgn * 1.0)]
        d.body("steel", blade, bevel=2.0)
    d.body("gold", ellipse(along((10, 23), (21, 10), 0.8), 1.8, 1.8))
    d.embers("fire", 14, (3, 3, 29, 29), seed=4)
    d.sparkle(24, 7, "fire", big=True)
    return d.finish()


def ic_cerberus_howl():
    d = Dot("cerberus")
    c = (16, 17)
    for r, w in ((13, 1.3), (9.5, 1.1), (6, 0.9)):
        d.stroke("soul", arc(c, r, 200, 520, 60), lambda t, w=w: w * (0.6 + t * 0.6), core=True, lo=1)
    # 개 머리 실루엣
    head = ellipse((16, 17), 4.2, 3.6)
    d.body("black", head, bevel=1.6)
    for sgn in (1, -1):
        d.body("black", [(16 + sgn * 1.5, 14.5), (16 + sgn * 4.4, 10.5), (16 + sgn * 4, 15.5)], bevel=1.0)
        d.px(16 + sgn * 1.8 - (1 if sgn < 0 else 0), 16, RAMPS["hell"][-1])
    d.body("black", [(13.5, 18), (18.5, 18), (17.5, 21.5), (14.5, 21.5)], bevel=1.0)
    d.embers("soul", 16, (2, 2, 30, 30), seed=7)
    return d.finish()


def ic_medusa_gaze():
    d = Dot("medusa")
    # 눈에서 뻗는 빛줄기
    for ang in (-35, -12, 12, 35):
        a = math.radians(ang + 90)
        d.stroke("venom", [(16, 17), (16 + math.cos(a) * 15, 17 + math.sin(a) * 15)][::-1], lambda t: 0.4 + 0.9 * t, lo=1)
    for ang in (-35, -12, 12, 35):
        a = math.radians(-ang - 90)
        d.stroke("venom", [(16, 17), (16 + math.cos(a) * 15, 17 + math.sin(a) * 15)][::-1], lambda t: 0.4 + 0.9 * t, lo=1)
    eye = bez((4, 17), (10, 9), (22, 9), (28, 17), n=20) + bez((28, 17), (22, 25), (10, 25), (4, 17), n=20)
    d.body("marble", eye, bevel=2.5)
    d.glow_body("gem_amber", ellipse((16, 17), 5.2, 5.6))
    d.body("black", [(15.2, 12.2), (16.8, 12.2), (17.3, 17), (16.8, 21.8), (15.2, 21.8), (14.7, 17)], bevel=1.0, outline=False)
    d.sparkle(18, 14, "gem_amber")
    # 뱀 머리카락 몇 가닥
    for k, (x0, y0, x1, y1) in enumerate(((8, 9, 5, 3), (13, 8, 12, 2), (19, 8, 21, 2), (24, 9, 27, 3))):
        d.body("green", curve_strip(bez((x0, y0), ((x0 + x1) / 2 + (2 if k % 2 else -2), (y0 + y1) / 2), (x1, y1), n=12),
                                    lambda t: 1.1 - t * 0.4), bevel=0.8)
    return d.finish()


def ic_scylla_maelstrom():
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


def it_xiphos():
    d = Dot()
    a, b = (4.5, 27.5), (29, 3)
    d.body("wood", strip(along(a, b, 0.05), along(a, b, 0.24), lambda t: 1.3))
    for s in (0.09, 0.14, 0.19):
        d.body("leather", strip(along(a, b, s - 0.012), along(a, b, s + 0.012), lambda t: 1.45))
    d.body("gold", ellipse(along(a, b, 0.03), 2.1, 2.1))

    def prof(t):
        w = 1.4 + 1.5 * math.sin(min(1, t * 1.2) * math.pi) ** 1.2
        if t > 0.8:
            w *= max(0.05, 1 - (t - 0.8) / 0.2)
        return w
    d.body("gold", strip(along(a, b, 0.25), b, prof, n=60), lo=2, bevel=1.6)
    d.body("bronze", strip(along(a, b, 0.28), along(a, b, 0.78), lambda t: 0.35), outline=False, flat=True, lo=4, hi=5)
    guard = strip(along(a, b, 0.25, 4.6), along(a, b, 0.25, -4.6), lambda t: 0.9 + 0.5 * math.sin(t * math.pi))
    d.body("gold", guard, bevel=1.2)
    d.body("gem_red", ellipse(along(a, b, 0.25), 1.2, 1.2), bevel=1.0)
    d.sparkle(*along(a, b, 0.6, 0.8), "gold")
    return d.finish()


def it_labrys():
    d = Dot()
    a, b = (3, 29), (24, 8)
    d.body("wood", strip(a, b, lambda t: 1.1))
    for s0, s1 in ((0.04, 0.3),):
        for k in range(5):
            s = s0 + (s1 - s0) * k / 5
            d.body("leather", strip(along(a, b, s), along(a, b, s + 0.035), lambda t: 1.3))
    for sgn in (1, -1):
        blade = [along(a, b, 0.72, sgn * 1.1)] + bez(along(a, b, 0.62, sgn * 1.3), along(a, b, 0.66, sgn * 8.4),
                                                    along(a, b, 1.05, sgn * 6.5), n=18) + [along(a, b, 0.93, sgn * 1.1)]
        d.body("steel", blade, bevel=2.2)
        edge = bez(along(a, b, 0.63, sgn * 5.0), along(a, b, 0.8, sgn * 7.9), along(a, b, 1.0, sgn * 5.6), n=16)
        d.stroke("ice", edge, 0.5, glow=False, core=False, lo=3)
    d.body("gold", ellipse(along(a, b, 0.82), 2.0, 2.0))
    d.body("gem_red", ellipse(along(a, b, 0.82), 1.0, 1.0), bevel=0.8, outline=False)
    tas = bez(along(a, b, 0.38, 1.4), along(a, b, 0.33, 4.5), along(a, b, 0.25, 4.0), n=10)
    d.body("red", curve_strip(tas, lambda t: 0.6 + t * 1.0), bevel=1.0)
    return d.finish()


def it_archer_bow_pull():
    d = Dot()
    grip = (7, 7)
    up = bez(grip, (13, 0.5), (22, 0.5), (29.5, 2.5), n=24)
    dn = bez(grip, (0.5, 13), (0.5, 22), (2.5, 29.5), n=24)
    pp = (19.5, 19.5)
    for a in ((29.5, 2.5), (2.5, 29.5)):
        d.stroke("string", [a, pp], 0.45, glow=False, core=False, lo=1)
    for limb in (up, dn):
        d.body("wood", curve_strip(limb, lambda t: 1.4 - t * 0.7), bevel=1.2)
        d.body("bronze", ellipse(limb[-1], 1.0, 1.0), bevel=0.8)
    d.body("leather", ellipse(grip, 2.2, 2.2), bevel=1.2)
    # 화살
    d.body("wood", strip(pp, (3.5, 3.5), lambda t: 0.5), bevel=0.6)
    d.body("steel", [(1.5, 1.5), (5.5, 2.6), (2.6, 5.5)], bevel=0.8)
    for sgn in (1, -1):
        d.body("red", [pp, (pp[0] - 3 + sgn * 1.6, pp[1] - 3 - sgn * 1.6), (pp[0] - 1 + sgn * 1.6, pp[1] - 1 - sgn * 1.6)], bevel=0.6)
    return d.finish()


def it_cerberus_collar():
    d = Dot()
    c = (16, 16)
    for k in range(10):
        a = k / 10 * 2 * math.pi + 0.3
        base = (c[0] + math.cos(a) * 9.5, c[1] + math.sin(a) * 9.5)
        tip = (c[0] + math.cos(a) * 14.8, c[1] + math.sin(a) * 14.8)
        nx, ny = -math.sin(a), math.cos(a)
        d.body("steel", [(base[0] + nx * 1.6, base[1] + ny * 1.6), tip, (base[0] - nx * 1.6, base[1] - ny * 1.6)], bevel=1.0)
    ring = ellipse(c, 11.5, 11.5, 64) + [ellipse(c, 11.5, 11.5, 64)[0]] + ellipse(c, 7.2, 7.2, 64)[::-1] + [ellipse(c, 7.2, 7.2, 64)[-1]]
    d.body("black", ring, bevel=1.8)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        d.px(c[0] + math.cos(a) * 9.4, c[1] + math.sin(a) * 9.4, RAMPS["gold"][4])
    for a in (math.pi * 0.5, math.pi * 0.25, math.pi * 0.75):
        q = (c[0] + math.cos(a) * 9.6, c[1] + math.sin(a) * 9.6)
        d.glow_body("soul", ellipse(q, 2.3, 2.3))
        d.px(q[0] - 0.8, q[1] - 0.8, RAMPS["soul"][-1])
    return d.finish()


if __name__ == "__main__":
    from PIL import Image
    S = "/tmp/claude-0/-home-user-minecraft/2d68590e-6d8d-5099-8a63-c0ef9e8e5738/scratchpad/"
    icons = [ic_minotaur_frenzy(), ic_cerberus_howl(), ic_medusa_gaze(), ic_scylla_maelstrom()]
    items = [it_xiphos(), it_labrys(), it_archer_bow_pull(), it_cerberus_collar()]
    W = Image.new("RGBA", (4 * 208 + 8, 2 * 208 + 8), (198, 196, 190, 255))
    slot = Image.new("RGBA", (200, 200), (139, 139, 139, 255))
    for i, im in enumerate(icons):
        W.alpha_composite(im.resize((192, 192), Image.NEAREST), (8 + i * 208, 8))
    for i, im in enumerate(items):
        W.alpha_composite(slot, (4 + i * 208, 212))
        W.alpha_composite(im.resize((192, 192), Image.NEAREST), (8 + i * 208, 216))
    W.save(S + "dot_samples.png")
