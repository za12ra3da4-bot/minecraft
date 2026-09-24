"""스킬 아이콘 34개 (32x32) — 리소스팩 assets/oly/textures/item/icon/<name>.png

같은 PNG 를 (1) 폰트 글리프 oly:icons (보스바·자막·액션바) 와
(2) 아이템 모델 oly:icon/<name> (보스 머리 위 시전 표시, 사냥 표식) 에 함께 쓴다.
"""
import math
from pixel import Sheet, plate, compose, SS

S = Sheet.s

FIELD = {
    "minotaur": ["#2a0808", "#5a1010", "#8a2418"],
    "nemean_lion": ["#3a2008", "#6a4010", "#9a6a1c"],
    "chimera": ["#301008", "#602010", "#903818"],
    "cerberus": ["#100818", "#281438", "#402058"],
    "hydra": ["#081a10", "#103820", "#1c5a30"],
    "medusa": ["#08201e", "#104040", "#1c6a60"],
    "scylla": ["#06122a", "#0c2a50", "#184a80"],
    "common": ["#1a1612", "#3a3026", "#5a4a38"],
}


def poly(d, pts):
    d.polygon([(S(x), S(y)) for x, y in pts], fill=255)


def ell(d, x0, y0, x1, y1):
    d.ellipse([S(x0), S(y0), S(x1), S(y1)], fill=255)


def ring(d, cx, cy, r, w):
    d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], outline=255, width=int(S(w)))


def line(d, pts, w):
    d.line([(S(x), S(y)) for x, y in pts], fill=255, width=int(S(w)), joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse([S(x - w / 2), S(y - w / 2), S(x + w / 2), S(y + w / 2)], fill=255)


def arc(d, cx, cy, r, a0, a1, w):
    d.arc([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], a0, a1, fill=255, width=int(S(w)))


def curve(d, pts, w, steps=24):
    """2차 베지어 연결선."""
    out = []
    for i in range(0, len(pts) - 2, 2):
        (x0, y0), (x1, y1), (x2, y2) = pts[i], pts[i + 1], pts[i + 2]
        for k in range(steps + 1):
            t = k / steps
            x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t * t * x2
            y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t * t * y2
            out.append((x, y))
    line(d, out, w)


def taper(d, pts, w0, w1, steps=28):
    """굵기가 줄어드는 곡선 (뿔·촉수·꼬리)."""
    (x0, y0), (x1, y1), (x2, y2) = pts
    for k in range(steps + 1):
        t = k / steps
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t * t * x2
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t * t * y2
        r = (w0 + (w1 - w0) * t) / 2
        d.ellipse([S(x - r), S(y - r), S(x + r), S(y + r)], fill=255)


def flame(d, cx, by, h, w):
    """불꽃 한 줄기 (아래 넓고 위로 휘어 올라간다)."""
    pts = []
    for k in range(0, 181, 12):
        a = math.radians(k)
        pts.append((cx + math.cos(a) * w / 2, by - math.sin(a) * w * 0.35))
    poly(d, [(cx - w / 2, by)] + [(cx - w * 0.45, by - h * 0.45), (cx - w * 0.1, by - h * 0.7),
                                 (cx + w * 0.05, by - h), (cx + w * 0.2, by - h * 0.62),
                                 (cx + w * 0.5, by - h * 0.4), (cx + w / 2, by)])
    ell(d, cx - w / 2, by - w * 0.55, cx + w / 2, by + w * 0.3)


def sparkle(d, cx, cy, r):
    poly(d, [(cx, cy - r), (cx + r * 0.25, cy - r * 0.25), (cx + r, cy), (cx + r * 0.25, cy + r * 0.25),
             (cx, cy + r), (cx - r * 0.25, cy + r * 0.25), (cx - r, cy), (cx - r * 0.25, cy - r * 0.25)])


# ─────────────────────────────── 미노타우로스
def minotaur_charge(sh):
    d = sh.layer("bone")
    taper(d, [(15, 16), (8, 15), (6, 7)], 4.2, 1.2)      # 왼뿔
    taper(d, [(17, 16), (24, 15), (26, 7)], 4.2, 1.2)    # 오른뿔
    d = sh.layer("fur")
    poly(d, [(11, 13), (21, 13), (22, 20), (19, 26), (13, 26), (10, 20)])
    d = sh.layer("dark")
    ell(d, 13, 22, 15, 24)
    ell(d, 17, 22, 19, 24)
    d = sh.layer("red")
    ell(d, 12, 16, 14.5, 18.5)
    ell(d, 17.5, 16, 20, 18.5)
    d = sh.layer("wave")
    for y in (9, 12):
        line(d, [(4 + (y - 9), y + 17), (9 + (y - 9), y + 17)], 1.4)


def minotaur_frenzy(sh):
    d = sh.layer("wave")
    arc(d, 16, 16, 12, 200, 330, 1.6)
    arc(d, 16, 16, 12, 20, 150, 1.6)
    d = sh.layer("bronze")
    poly(d, [(15, 5), (17, 5), (17, 28), (15, 28)])        # 자루
    d = sh.layer("steel")
    # 양날 도끼 (라브리스)
    poly(d, [(17, 8), (25, 4), (27, 9), (27, 15), (25, 19), (17, 14)])
    poly(d, [(15, 8), (7, 4), (5, 9), (5, 15), (7, 19), (15, 14)])


def minotaur_quake(sh):
    d = sh.layer("stone")
    poly(d, [(2, 24), (30, 24), (30, 29), (2, 29)])
    d = sh.layer("hellfire")
    for pts in ([(16, 24), (13, 26.5), (11, 29)], [(16, 24), (19, 26.5), (22, 29)],
                [(16, 24), (8, 25.5), (3, 26)], [(16, 24), (24, 25.5), (29, 27)]):
        line(d, pts, 1.2)
    d = sh.layer("fur")
    poly(d, [(12, 2), (20, 2), (21, 12), (11, 12)])        # 다리
    d = sh.layer("dark")
    # 갈라진 발굽 두 개
    poly(d, [(9, 12), (15.4, 12), (15.4, 22), (8, 22), (7.5, 17)])
    poly(d, [(16.6, 12), (23, 12), (24.5, 17), (24, 22), (16.6, 22)])
    d = sh.layer("wave")
    arc(d, 16, 24, 11, 195, 245, 1.3)
    arc(d, 16, 24, 11, 295, 345, 1.3)
    line(d, [(4, 12), (6, 16)], 1.1)
    line(d, [(28, 12), (26, 16)], 1.1)


def minotaur_horn(sh):
    d = sh.layer("bone")
    taper(d, [(9, 27), (10, 12), (22, 5)], 6.5, 1.3)
    d = sh.layer("eye")
    sparkle(d, 23, 22, 6)
    d = sh.layer("wave")
    line(d, [(18, 13), (22, 10)], 1.2)
    line(d, [(19, 17), (25, 15)], 1.2)


def minotaur_rage(sh):
    d = sh.layer("hellfire")
    flame(d, 8, 29, 18, 8)
    flame(d, 24, 29, 18, 8)
    flame(d, 16, 29, 24, 10)
    d = sh.layer("bone")
    taper(d, [(14, 14), (8, 13), (7, 6)], 3.4, 1)
    taper(d, [(18, 14), (24, 13), (25, 6)], 3.4, 1)
    d = sh.layer("dark")
    poly(d, [(11, 11), (21, 11), (22, 18), (19, 25), (13, 25), (10, 18)])
    d = sh.layer("red")
    poly(d, [(11.5, 14), (15, 15.5), (14.5, 17.5), (12, 16.5)])
    poly(d, [(20.5, 14), (17, 15.5), (17.5, 17.5), (20, 16.5)])


# ─────────────────────────────── 네메아의 사자
def lion_paw(d, cx, cy, s):
    ell(d, cx - 4.5 * s, cy - 2 * s, cx + 4.5 * s, cy + 5 * s)
    for dx, dy in ((-5, -5.5), (-1.8, -8), (1.8, -8), (5, -5.5)):
        ell(d, cx + (dx - 1.7) * s, cy + (dy - 1.9) * s, cx + (dx + 1.7) * s, cy + (dy + 1.9) * s)


def nemean_lion_pounce(sh):
    d = sh.layer("wave")
    arc(d, 16, 30, 15, 205, 335, 1.4)
    d = sh.layer("fur")
    # 발바닥 (세 갈래 패드)
    poly(d, [(9, 22), (11, 17), (16, 15.5), (21, 17), (23, 22), (20, 25.5), (16, 24), (12, 25.5)])
    for cx, cy in ((8, 14), (13, 10), (19, 10), (24, 14)):
        ell(d, cx - 2.4, cy - 2.9, cx + 2.4, cy + 2.9)
    d = sh.layer("white")
    for cx, cy in ((8, 14), (13, 10), (19, 10), (24, 14)):
        poly(d, [(cx - 0.8, cy - 2.6), (cx + 0.8, cy - 2.6), (cx, cy - 5)])


def nemean_lion_roar(sh):
    d = sh.layer("wave")
    for r in (10, 13.5):
        arc(d, 11, 17, r, 305, 55, 1.4)
    d = sh.layer("gold")
    pts = []
    for k in range(24):
        a = math.radians(k * 15)
        r = 10.5 if k % 2 == 0 else 7.8
        pts.append((12 + math.cos(a) * r, 17 + math.sin(a) * r))
    poly(d, pts)                                          # 갈기 (톱니)
    d = sh.layer("fur")
    ell(d, 6.5, 11, 17.5, 23)
    d = sh.layer("dark")
    poly(d, [(9.5, 18.5), (15, 18), (14.5, 23), (10, 23)])  # 벌린 입
    d = sh.layer("white")
    poly(d, [(10.3, 18.6), (11.4, 18.6), (10.8, 20.4)])
    poly(d, [(13.2, 18.3), (14.3, 18.2), (13.8, 20.2)])
    d = sh.layer("red")
    ell(d, 8.8, 14, 10.6, 15.8)
    ell(d, 13.4, 14, 15.2, 15.8)


def nemean_lion_hunt(sh):
    d = sh.layer("red")
    ring(d, 16, 16, 11, 1.6)
    for a in (0, 90, 180, 270):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        line(d, [(16 + ca * 8, 16 + sa * 8), (16 + ca * 13.5, 16 + sa * 13.5)], 1.6)
    d = sh.layer("eye")
    poly(d, [(7, 16), (12, 11.5), (20, 11.5), (25, 16), (20, 20.5), (12, 20.5)])
    d = sh.layer("dark")
    poly(d, [(15, 11.8), (17, 11.8), (17.6, 16), (17, 20.2), (15, 20.2), (14.4, 16)])


def nemean_lion_claw(sh):
    d = sh.layer("white")
    for k, off in enumerate((-6, 0, 6)):
        taper(d, [(8 + off, 5 + abs(off) * 0.3), (15 + off, 15), (21 + off, 27 - abs(off) * 0.3)], 1.0, 3.2)
    d = sh.layer("blood")
    for off in (-6, 0, 6):
        ell(d, 20 + off, 25 - abs(off) * 0.3, 22.5 + off, 28 - abs(off) * 0.3)


# ─────────────────────────────── 키메라
def chimera_breath(sh):
    d = sh.layer("fire")
    poly(d, [(6, 14), (27, 5), (29, 16), (27, 27), (6, 18)])
    d = sh.layer("eye")
    poly(d, [(8, 15), (24, 10), (25, 16), (24, 22), (8, 17)])
    d = sh.layer("fur")
    ell(d, 2, 10, 11, 22)
    d = sh.layer("dark")
    ell(d, 4.5, 13, 6.5, 15)


def chimera_venom(sh):
    d = sh.layer("poison")
    poly(d, [(16, 4), (22, 15), (23, 20), (16, 27), (9, 20), (10, 15)])
    ell(d, 9, 14, 23, 27)
    d = sh.layer("scale")
    ell(d, 23, 21, 28, 26)
    ell(d, 5, 22, 9, 26)
    d = sh.layer("white")
    ell(d, 12, 14, 15, 18)
    d = sh.layer("dark")
    # 해골 느낌 두 눈
    ell(d, 12, 19, 15, 22)
    ell(d, 17, 19, 20, 22)


def chimera_spikes(sh):
    d = sh.layer("stone")
    poly(d, [(2, 25), (30, 25), (30, 29), (2, 29)])
    d = sh.layer("bone")
    for x, h in ((7, 11), (13, 17), (20, 21), (26, 13)):
        taper(d, [(x, 25), (x - 1, 25 - h * 0.6), (x + 1.5, 25 - h)], 4.5, 0.6)


def chimera_triple(sh):
    d = sh.layer("fur")
    ell(d, 3, 4, 14, 15)
    d = sh.layer("bone")
    ell(d, 18, 4, 29, 15)
    taper(d, [(20, 6), (18, 2), (15, 3)], 1.8, 0.6)
    taper(d, [(27, 6), (29, 2), (31, 3)], 1.8, 0.6)
    d = sh.layer("scale")
    taper(d, [(16, 29), (9, 23), (16, 17)], 3.4, 4.2)
    ell(d, 13, 16, 20, 22)
    d = sh.layer("red")
    for cx, cy in ((7, 9), (10, 9), (22, 9), (25, 9), (15, 18.5), (18, 18.5)):
        ell(d, cx - 0.9, cy - 0.9, cx + 0.9, cy + 0.9)


# ─────────────────────────────── 케르베로스
def cerberus_flame(sh):
    d = sh.layer("hellfire")
    flame(d, 16, 28, 23, 14)
    d = sh.layer("eye")
    flame(d, 16, 28, 12, 7)
    d = sh.layer("dark")
    for x in (6, 26):
        poly(d, [(x - 2, 28), (x + 2, 28), (x, 21)])


def cerberus_howl(sh):
    d = sh.layer("soul")
    for r in (5, 9, 13):
        ring(d, 16, 17, r, 1.6)
    d = sh.layer("dark")
    ell(d, 12.5, 13.5, 19.5, 20.5)
    d = sh.layer("eye")
    ell(d, 14, 15.5, 16, 17.5)
    ell(d, 16.5, 15.5, 18.5, 17.5)


def cerberus_hunt(sh):
    d = sh.layer("dark")
    poly(d, [(4, 8), (28, 8), (26, 14), (6, 14)])
    poly(d, [(6, 18), (26, 18), (28, 24), (4, 24)])
    d = sh.layer("white")
    for x in range(7, 26, 4):
        poly(d, [(x, 13.5), (x + 2.6, 13.5), (x + 1.3, 17.5)])
        poly(d, [(x + 1, 18.5), (x + 3.6, 18.5), (x + 2.3, 14.8)])
    d = sh.layer("red")
    ell(d, 24, 9, 26.5, 11.5)


def cerberus_gate(sh):
    d = sh.layer("stone")
    poly(d, [(5, 28), (9, 28), (9, 10), (5, 10)])
    poly(d, [(23, 28), (27, 28), (27, 10), (23, 10)])
    poly(d, [(3, 6), (29, 6), (29, 10), (3, 10)])
    d = sh.layer("soul")
    poly(d, [(10, 28), (22, 28), (22, 11), (10, 11)])
    d = sh.layer("dark")
    ell(d, 12, 13, 20, 26)
    d = sh.layer("eye")
    ell(d, 13.5, 17, 15.2, 18.7)
    ell(d, 16.8, 17, 18.5, 18.7)


def cerberus_fury(sh):
    d = sh.layer("hellfire")
    flame(d, 6, 30, 20, 8)
    flame(d, 26, 30, 20, 8)
    flame(d, 16, 30, 27, 14)
    d = sh.layer("dark")
    for cx, cy in ((8, 19), (16, 13), (24, 19)):
        ell(d, cx - 4.2, cy - 3.4, cx + 4.2, cy + 4.4)
        poly(d, [(cx - 4, cy - 0.5), (cx - 3.4, cy - 6.5), (cx - 1, cy - 2.5)])
        poly(d, [(cx + 4, cy - 0.5), (cx + 3.4, cy - 6.5), (cx + 1, cy - 2.5)])
        poly(d, [(cx - 2.2, cy + 2), (cx + 2.2, cy + 2), (cx + 1.4, cy + 6), (cx - 1.4, cy + 6)])
    d = sh.layer("eye")
    for cx, cy in ((8, 19), (16, 13), (24, 19)):
        ell(d, cx - 2.6, cy - 0.4, cx - 0.8, cy + 1.4)
        ell(d, cx + 0.8, cy - 0.4, cx + 2.6, cy + 1.4)


# ─────────────────────────────── 히드라
def hydra_bite(sh):
    d = sh.layer("scale")
    taper(d, [(16, 29), (15, 18), (16, 8)], 4.4, 3.4)
    taper(d, [(13, 29), (6, 22), (6, 11)], 4.0, 3)
    taper(d, [(19, 29), (26, 22), (26, 11)], 4.0, 3)
    for cx, cy in ((16, 7), (6, 10), (26, 10)):
        ell(d, cx - 3.4, cy - 3, cx + 3.4, cy + 2.6)
    d = sh.layer("eye")
    for cx, cy in ((16, 7), (6, 10), (26, 10)):
        ell(d, cx - 1.9, cy - 1.8, cx - 0.6, cy - 0.5)
        ell(d, cx + 0.6, cy - 1.8, cx + 1.9, cy - 0.5)


def hydra_venom(sh):
    d = sh.layer("poison")
    for cx, cy, s in ((9, 9, 0.8), (22, 7, 1.0), (15, 18, 1.2), (25, 21, 0.7), (7, 22, 0.75)):
        poly(d, [(cx, cy - 5 * s), (cx + 3 * s, cy), (cx, cy + 3 * s), (cx - 3 * s, cy)])
        ell(d, cx - 3 * s, cy - 1.5 * s, cx + 3 * s, cy + 3.2 * s)
    d = sh.layer("scale")
    poly(d, [(3, 28), (29, 28), (27, 30), (5, 30)])


def hydra_tempest(sh):
    d = sh.layer("poison")
    for k in range(7):
        a = math.radians(-90 + k * 360 / 7)
        line(d, [(16 + math.cos(a) * 5, 16 + math.sin(a) * 5), (16 + math.cos(a) * 13, 16 + math.sin(a) * 13)], 1.8)
        tx, ty = 16 + math.cos(a) * 14, 16 + math.sin(a) * 14
        poly(d, [(tx + math.cos(a) * 1.5, ty + math.sin(a) * 1.5),
                 (tx + math.cos(a + 2.2) * 2.4, ty + math.sin(a + 2.2) * 2.4),
                 (tx + math.cos(a - 2.2) * 2.4, ty + math.sin(a - 2.2) * 2.4)])
    d = sh.layer("scale")
    ell(d, 11, 11, 21, 21)
    d = sh.layer("eye")
    ell(d, 13.5, 13.5, 18.5, 18.5)


def hydra_regrow(sh):
    d = sh.layer("scale")
    taper(d, [(14, 30), (10, 18), (16, 9)], 5, 3.6)
    ell(d, 12, 4, 22, 12)
    d = sh.layer("eye")
    ell(d, 17, 6, 19, 8)
    d = sh.layer("poison")
    poly(d, [(22, 16), (25, 16), (25, 19), (28, 19), (28, 22), (25, 22), (25, 25), (22, 25), (22, 22), (19, 22), (19, 19), (22, 19)])


def hydra_sever(sh):
    d = sh.layer("scale")
    taper(d, [(8, 30), (7, 22), (10, 17)], 5.5, 5)
    taper(d, [(15, 12), (19, 8), (21, 4)], 5, 3.6)
    d = sh.layer("blood")
    ell(d, 8, 15, 13, 19)
    ell(d, 13, 10, 17, 14)
    ell(d, 17, 19, 19, 22)
    d = sh.layer("steel")
    poly(d, [(4, 26), (26, 6), (28, 8), (6, 28)])
    d = sh.layer("bronze")
    poly(d, [(24, 4), (30, 10), (28.5, 11.5), (22.5, 5.5)])


# ─────────────────────────────── 메두사
def medusa_gaze(sh):
    d = sh.layer("scale")
    for k in range(5):
        a = math.radians(200 + k * 35)
        taper(d, [(16 + math.cos(a) * 8, 16 + math.sin(a) * 7),
                  (16 + math.cos(a) * 12, 16 + math.sin(a) * 12 - 2),
                  (16 + math.cos(a) * 14, 16 + math.sin(a) * 13 + 2)], 2.4, 1.4)
    d = sh.layer("white")
    poly(d, [(4, 18), (10, 12.5), (22, 12.5), (28, 18), (22, 23.5), (10, 23.5)])
    d = sh.layer("eye")
    ell(d, 11.5, 13, 20.5, 23)
    d = sh.layer("dark")
    poly(d, [(15.2, 13.5), (16.8, 13.5), (17.3, 18), (16.8, 22.5), (15.2, 22.5), (14.7, 18)])


def medusa_zone(sh):
    d = sh.layer("stone")
    ell(d, 2, 13, 30, 29)
    d = sh.layer("dark")
    ell(d, 6, 16, 26, 26)
    d = sh.layer("jade")
    arc(d, 16, 21, 8, 20, 320, 1.8)
    poly(d, [(22.5, 15), (26, 16.5), (24, 19)])
    d = sh.layer("stone")
    for x, h in ((9, 9), (16, 13), (23, 8)):
        poly(d, [(x - 2.5, 21), (x + 2.5, 21), (x + 1, 21 - h), (x - 1, 21 - h - 1)])
    d = sh.layer("eye")
    ell(d, 15, 3, 17, 5)


def medusa_serpent(sh):
    d = sh.layer("bronze")
    line(d, [(4, 28), (21, 11)], 1.6)
    poly(d, [(3, 25), (6, 29), (3, 30), (2, 27)])
    d = sh.layer("scale")
    poly(d, [(18, 10), (24, 4), (29, 3), (28, 8), (22, 14)])
    d = sh.layer("red")
    poly(d, [(27, 5), (31, 2), (30, 6)])
    d = sh.layer("eye")
    ell(d, 23, 6, 24.8, 7.8)


def medusa_tail(sh):
    d = sh.layer("scale")
    for r, w in ((12, 3.8), (8, 3.2), (4.2, 2.6)):
        arc(d, 16, 16, r, 0, 300, w)
    taper(d, [(27.5, 13), (29, 20), (25, 26)], 3.6, 1)
    d = sh.layer("white")
    for a in range(0, 300, 40):
        x, y = 16 + math.cos(math.radians(a)) * 12, 16 + math.sin(math.radians(a)) * 12
        ell(d, x - 0.6, y - 0.6, x + 0.6, y + 0.6)


def medusa_mirror(sh):
    d = sh.layer("bronze")
    ell(d, 5, 5, 27, 27)
    d = sh.layer("steel")
    ell(d, 8, 8, 24, 24)
    d = sh.layer("white")
    poly(d, [(11, 10), (14, 9), (10, 17), (9, 14)])
    d = sh.layer("eye")
    line(d, [(28, 4), (19, 13)], 1.6)
    line(d, [(19, 13), (27, 21)], 1.6)
    sparkle(d, 19, 13, 3.4)


# ─────────────────────────────── 스킬라
def scylla_slam(sh):
    d = sh.layer("water")
    poly(d, [(2, 26), (30, 26), (30, 30), (2, 30)])
    d = sh.layer("flesh")
    taper(d, [(26, 4), (22, 18), (12, 24)], 5.5, 2.4)
    taper(d, [(12, 24), (7, 25), (8, 21)], 2.4, 1)
    d = sh.layer("jade")
    for t in (0.25, 0.45, 0.65):
        x = (1 - t) ** 2 * 26 + 2 * (1 - t) * t * 22 + t * t * 12
        y = (1 - t) ** 2 * 4 + 2 * (1 - t) * t * 18 + t * t * 24
        ell(d, x - 0.9, y - 0.9, x + 0.9, y + 0.9)
    d = sh.layer("wave")
    for x in (8, 16, 23):
        poly(d, [(x - 2, 26), (x, 21), (x + 2, 26)])


def scylla_hounds(sh):
    d = sh.layer("dark")
    for cx, cy in ((9, 11), (23, 11), (16, 20)):
        ell(d, cx - 5, cy - 4, cx + 5, cy + 4.5)
        poly(d, [(cx - 5, cy - 1), (cx - 4, cy - 7), (cx - 1.5, cy - 3)])
        poly(d, [(cx + 5, cy - 1), (cx + 4, cy - 7), (cx + 1.5, cy - 3)])
    d = sh.layer("white")
    for cx, cy in ((9, 11), (23, 11), (16, 20)):
        poly(d, [(cx - 2.5, cy + 2), (cx - 1.5, cy + 2), (cx - 2, cy + 4)])
        poly(d, [(cx + 1.5, cy + 2), (cx + 2.5, cy + 2), (cx + 2, cy + 4)])
    d = sh.layer("red")
    for cx, cy in ((9, 11), (23, 11), (16, 20)):
        ell(d, cx - 3, cy - 1.5, cx - 1.4, cy + 0.1)
        ell(d, cx + 1.4, cy - 1.5, cx + 3, cy + 0.1)


def scylla_cage(sh):
    d = sh.layer("water")
    ell(d, 3, 19, 29, 29)
    d = sh.layer("dark")
    ell(d, 7, 21.5, 25, 27)
    d = sh.layer("flesh")
    for k in range(7):
        a = math.radians(180 + k * 30)
        x = 16 + math.cos(a) * 12
        y = 24 + math.sin(a) * 4
        h = 17 - abs(k - 3) * 2.5
        taper(d, [(x, y + 1), (x - 2, y - h * 0.5), (x + 1.2, y - h)], 3.6, 0.9)


def scylla_maelstrom(sh):
    d = sh.layer("water")
    ell(d, 3, 3, 29, 29)
    d = sh.layer("wave")
    for k in range(3):
        a0 = k * 120
        pts = []
        for i in range(30):
            t = i / 29
            a = math.radians(a0 + t * 300)
            r = 12 * (1 - t) + 1.5
            pts.append((16 + math.cos(a) * r, 16 + math.sin(a) * r))
        line(d, pts, 1.6)


# ─────────────────────────────── 공통
def common_warn(sh):
    d = sh.layer("gold")
    poly(d, [(16, 4), (29, 27), (3, 27)])
    d = sh.layer("dark")
    poly(d, [(14.4, 11), (17.6, 11), (17, 20), (15, 20)])
    ell(d, 14.5, 21.5, 17.5, 24.5)


def common_stun(sh):
    d = sh.layer("eye")
    for k in range(3):
        a = math.radians(-90 + k * 120)
        sparkle(d, 16 + math.cos(a) * 8, 17 + math.sin(a) * 6, 4.2)
    d = sh.layer("wave")
    ring(d, 16, 17, 10, 1.1)


ICONS = [
    ("minotaur", "charge", minotaur_charge, "황소의 돌진"),
    ("minotaur", "frenzy", minotaur_frenzy, "도끼 난무"),
    ("minotaur", "quake", minotaur_quake, "지면 강타"),
    ("minotaur", "horn", minotaur_horn, "뿔 치받기"),
    ("minotaur", "rage", minotaur_rage, "광폭화"),
    ("nemean_lion", "pounce", nemean_lion_pounce, "포식자의 도약"),
    ("nemean_lion", "roar", nemean_lion_roar, "사자의 포효"),
    ("nemean_lion", "hunt", nemean_lion_hunt, "사냥 본능"),
    ("nemean_lion", "claw", nemean_lion_claw, "발톱 연격"),
    ("chimera", "breath", chimera_breath, "화염 브레스"),
    ("chimera", "venom", chimera_venom, "독성 투사체"),
    ("chimera", "spikes", chimera_spikes, "뿔가시"),
    ("chimera", "triple", chimera_triple, "삼중 공격"),
    ("cerberus", "flame", cerberus_flame, "지옥불 숨결"),
    ("cerberus", "howl", cerberus_howl, "저승의 충격파"),
    ("cerberus", "hunt", cerberus_hunt, "사냥개의 물기"),
    ("cerberus", "gate", cerberus_gate, "지옥문"),
    ("cerberus", "fury", cerberus_fury, "삼두의 분노"),
    ("hydra", "bite", hydra_bite, "다두 연쇄 물기"),
    ("hydra", "venom", hydra_venom, "독액 비"),
    ("hydra", "tempest", hydra_tempest, "칠두 폭풍"),
    ("hydra", "regrow", hydra_regrow, "머리 재생"),
    ("hydra", "sever", hydra_sever, "머리 절단"),
    ("medusa", "gaze", medusa_gaze, "석화의 시선"),
    ("medusa", "zone", medusa_zone, "석화 지대"),
    ("medusa", "serpent", medusa_serpent, "뱀머리 화살"),
    ("medusa", "tail", medusa_tail, "꼬리 휘감기"),
    ("medusa", "mirror", medusa_mirror, "반사"),
    ("scylla", "slam", scylla_slam, "촉수 강타"),
    ("scylla", "hounds", scylla_hounds, "여섯 개의 머리"),
    ("scylla", "cage", scylla_cage, "촉수 울타리"),
    ("scylla", "maelstrom", scylla_maelstrom, "소용돌이"),
    ("common", "warn", common_warn, "경고"),
    ("common", "stun", common_stun, "기절"),
]


def render(boss, fn, seed=0):
    sh = Sheet(32)
    fn(sh)
    fg = sh.bake()
    return compose(plate(FIELD[boss], 32, seed), fg)
