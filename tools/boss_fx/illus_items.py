"""플레이어 아이템 일러스트 (128px, 곡선 + 조명) — paint.py 로 그린다"""
import math

from paint import Painting, along, bez, curve_strip, ellipse, strip

A0, B0 = (0.13, 0.87), (0.93, 0.07)          # 검: 손잡이 끝 → 칼끝


def key_path(a, b, t0, t1, w, n=6):
    """a→b 축 위 t0..t1 구간의 그리스 뇌문(메안더) 꺾은선 → 식각 홈 목록"""
    pts = []
    L = t1 - t0
    step = L / n
    for i in range(n):
        s = t0 + i * step
        seq = [(0, -w), (0, w), (0.5, w), (0.5, -0.2 * w), (0.25, -0.2 * w), (0.25, 0.45 * w), (0.75, 0.45 * w), (0.75, -w), (1, -w)]
        for fx, fy in seq:
            pts.append(along(a, b, s + fx * step, fy))
    gro = []
    for p0, p1 in zip(pts, pts[1:]):
        if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < 1e-6:
            continue
        gro.append((strip(p0, p1, lambda t: 0.0028, n=2), 0.004))
    return gro


def wrap_grip(p, a, b, t0, t1, half, mat="leather", bands=7, wire="gold"):
    """가죽 띠를 한 겹씩 비스듬히 감는다 (띠 사이 그림자) + 양끝 금실 고리"""
    L = t1 - t0
    for i in range(bands):
        s0 = t0 + L * i / bands
        s1 = s0 + L / bands * 1.25
        q = [along(a, b, s0, half * 1.02), along(a, b, s0 + L / bands * 0.35, -half * 1.02),
             along(a, b, s1 + L / bands * 0.35 - L / bands * 0.25, -half * 1.02), along(a, b, s1 - L / bands * 0.25, half * 1.02)]
        p.shape(mat, q, bevel=0.012, direction=(0.707, 0.707))
    for s in (t0, t1):
        p.shape(wire, strip(along(a, b, s - 0.012), along(a, b, s + 0.012), lambda t: half * 1.18, n=4), bevel=0.01)


def guard_volute(p, a, b, t, half, mat, gem=None):
    """코등이: 가운데 두툼 + 양끝 소용돌이 + 리벳"""
    pts_l = [along(a, b, t + 0.018 + 0.012 * (abs(s) ** 3), s * half) for s in [i / 30 - 1 for i in range(61)]]
    pts_r = [along(a, b, t - 0.02 - 0.004 * (abs(s) ** 2), s * half) for s in [1 - i / 30 for i in range(61)]]
    p.shape(mat, pts_l + pts_r, bevel=0.022)
    for sgn in (1, -1):
        c = along(a, b, t - 0.004, sgn * half * 1.02)
        p.shape(mat, ellipse(c, 0.028, 0.028), bevel=0.022)
        p.shape(mat, ellipse(along(a, b, t - 0.004, sgn * half * 1.02), 0.013, 0.013), bevel=0.01, height=1.4)
    for sgn in (0.45, -0.45):
        p.shape("silver" if mat != "silver" else "gold", ellipse(along(a, b, t, sgn * half), 0.009, 0.009), bevel=0.009, height=1.5)
    if gem:
        c = along(a, b, t)
        p.shape(mat, ellipse(c, 0.03, 0.03), bevel=0.02, height=1.3)
        p.shape(gem, ellipse(c, 0.019, 0.019), bevel=0.02, height=1.6)


def pommel(p, c, r, mat, gem=None):
    p.shape(mat, ellipse(c, r, r), bevel=0.03)
    p.shape(mat, ellipse(c, r * 0.72, r * 0.72), bevel=0.015, height=1.25)
    if gem:
        p.shape(gem, ellipse(c, r * 0.45, r * 0.45), bevel=0.02, height=1.5)


def xiphos():
    p = Painting()
    a, b = A0, B0
    tg = 0.26

    def prof(t):  # 잎 모양
        w = 0.029 + 0.033 * math.sin(min(1.0, t * 1.2) * math.pi) ** 1.3
        if t > 0.78:
            w *= max(0.0, 1 - (t - 0.78) / 0.22) ** 0.8
        return max(w, 0.0015)
    wrap_grip(p, a, b, 0.07, tg - 0.01, 0.034, "leather", bands=6, wire="gold")
    pommel(p, along(a, b, 0.035), 0.052, "gold", gem="gem_red")
    gro = [(strip(along(a, b, tg + 0.03), along(a, b, 0.8), lambda t: 0.0045), 0.008)] + key_path(a, b, tg + 0.03, tg + 0.2, 0.02, n=4)
    p.shape("bronze", strip(along(a, b, tg), b, prof, n=120), profile="blade", grooves=gro)
    guard_volute(p, a, b, tg, 0.13, "gold", gem="gem_red")
    return p.finish()


def labrys():
    p = Painting()
    a, b = (0.1, 0.9), (0.74, 0.26)                     # 자루
    p.shape("wood", strip(a, b, lambda t: 0.026 - 0.004 * t, n=40), bevel=0.025, direction=(0.707, -0.707))
    wrap_grip(p, a, b, 0.06, 0.3, 0.03, "leather", bands=6, wire="bronze")
    # 매단 붉은 술
    c = along(a, b, 0.42, 0.03)
    tassel = bez(c, (c[0] - 0.02, c[1] + 0.08), (c[0] + 0.03, c[1] + 0.16), n=30)
    p.shape("red", curve_strip(tassel, lambda t: 0.012 + t * 0.02), bevel=0.012, direction=(0, 1))
    p.shape("gold", ellipse(c, 0.018, 0.018), bevel=0.012)
    # 양날 초승달 도끼머리 (자루에 수직, 가운데 목에서 양쪽으로)
    hc = along(a, b, 0.82)
    for sgn in (1, -1):
        root0 = along(a, b, 0.78, sgn * 0.03)
        root1 = along(a, b, 0.87, sgn * 0.03)
        tip0 = along(a, b, 0.64, sgn * 0.26)
        tip1 = along(a, b, 1.02, sgn * 0.26)
        edge = bez(tip0, along(a, b, 0.83, sgn * 0.36), tip1, n=50)
        outline = [root0] + bez(root0, along(a, b, 0.74, sgn * 0.12), tip0, n=24) + edge + bez(tip1, along(a, b, 0.92, sgn * 0.12), root1, n=24)
        p.shape("steel", outline, profile="blade", bevel=0.02,
                grooves=[(curve_strip(bez(along(a, b, 0.72, sgn * 0.2), along(a, b, 0.83, sgn * 0.27), along(a, b, 0.94, sgn * 0.2), n=30),
                                      lambda t: 0.004), 0.006)])
    p.shape("bronze", ellipse(hc, 0.06, 0.05, rot=-0.785), bevel=0.03)
    p.shape("gold", ellipse(hc, 0.034, 0.028, rot=-0.785), bevel=0.02, height=1.3)
    p.shape("gem_red", ellipse(hc, 0.016, 0.016), bevel=0.015, height=1.6)
    return p.finish()



def infantry_sword():
    p = Painting()
    a, b = A0, B0
    tg = 0.25

    def prof(t):
        w = 0.042 - 0.006 * t
        if t > 0.84:
            w *= max(0.0, 1 - (t - 0.84) / 0.16) ** 0.9
        return max(w, 0.0015)
    wrap_grip(p, a, b, 0.07, tg - 0.012, 0.033, "leather", bands=6, wire="bronze")
    pommel(p, along(a, b, 0.035), 0.05, "bronze")
    gro = [(strip(along(a, b, tg + 0.02), along(a, b, 0.78), lambda t: 0.006 * (1 - t * 0.4)), 0.01)]
    p.shape("steel", strip(along(a, b, tg), b, prof, n=120), profile="blade", grooves=gro)
    guard_volute(p, a, b, tg, 0.15, "bronze")
    return p.finish()


def kopis():
    p = Painting()
    a = (0.14, 0.9)
    b = (0.62, 0.42)
    tg = 0.36
    wrap_grip(p, a, b, 0.1, tg - 0.02, 0.032, "leather", bands=5, wire="bronze")
    # 새 머리 폼멜
    c = along(a, b, 0.04)
    p.shape("bronze", ellipse(c, 0.05, 0.04, rot=-0.78), bevel=0.03)
    beak = [along(a, b, 0.02, 0.03), along(a, b, -0.12, 0.09), along(a, b, 0.04, 0.05)]
    p.shape("bronze", beak, bevel=0.015)
    p.shape("gem_amber", ellipse(along(a, b, 0.05, 0.012), 0.01, 0.01), bevel=0.01, height=1.5)
    # 앞으로 휘며 끝이 넓어지는 외날 칼
    base = along(a, b, tg)
    spine = bez(base, (0.72, 0.28), (0.8, 0.1), (0.94, 0.06), n=80)
    def prof(t):
        w = 0.03 + 0.05 * math.sin(min(1.0, t * 1.15) * math.pi * 0.62)
        if t > 0.86:
            w *= max(0.0, 1 - (t - 0.86) / 0.14)
        return max(w, 0.0015)
    left = []
    right = []
    n = len(spine)
    for i, pt in enumerate(spine):
        q = spine[min(n - 1, i + 1)]
        o = spine[max(0, i - 1)]
        dx, dy = q[0] - o[0], q[1] - o[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = prof(i / (n - 1))
        left.append((pt[0] + nx * w * 0.35, pt[1] + ny * w * 0.35))      # 등 (얇게)
        right.append((pt[0] - nx * w * 1.0, pt[1] - ny * w * 1.0))      # 배 (넓게)
    p.shape("steel", left + right[::-1], profile="blade",
            grooves=[(curve_strip(spine[5:60], lambda t: 0.004), 0.007)])
    guard_volute(p, a, b, tg, 0.09, "bronze")
    return p.finish()


def dagger():
    p = Painting()
    a, b = (0.2, 0.8), (0.84, 0.16)
    tg = 0.3
    def prof(t):
        w = 0.07 - 0.03 * t
        if t > 0.7:
            w *= max(0.0, 1 - (t - 0.7) / 0.3) ** 0.9
        return max(w, 0.0015)
    p.shape("bone", strip(along(a, b, 0.07), along(a, b, tg), lambda t: 0.036 + 0.008 * math.sin(t * math.pi)), bevel=0.03,
            direction=(0.707, -0.707))
    for s in (0.12, 0.19):
        p.shape("gold", strip(along(a, b, s - 0.01), along(a, b, s + 0.01), lambda t: 0.043, n=4), bevel=0.01)
    pommel(p, along(a, b, 0.04), 0.055, "bone")
    p.shape("steel", strip(along(a, b, tg), b, prof, n=100), profile="blade",
            grooves=[(strip(along(a, b, tg + 0.03), along(a, b, 0.66), lambda t: 0.007), 0.01)])
    guard_volute(p, a, b, tg, 0.12, "bronze", gem="gem_green")
    return p.finish()


def hephaestus_sword():
    p = Painting()
    a, b = A0, B0
    tg = 0.26
    def prof(t):
        w = 0.05 - 0.01 * t
        if t > 0.84:
            w *= max(0.0, 1 - (t - 0.84) / 0.16)
        return max(w, 0.0015)
    wrap_grip(p, a, b, 0.09, tg - 0.012, 0.033, "leather", bands=6, wire="dsteel")
    # 망치 폼멜
    c = along(a, b, 0.045)
    p.shape("dsteel", strip(along(a, b, 0.045, 0.07), along(a, b, 0.045, -0.07), lambda t: 0.034, n=6), bevel=0.02)
    p.shape("steel", strip(along(a, b, 0.045, 0.075), along(a, b, 0.045, 0.055), lambda t: 0.036, n=4), bevel=0.01)
    p.shape("steel", strip(along(a, b, 0.045, -0.055), along(a, b, 0.045, -0.075), lambda t: 0.036, n=4), bevel=0.01)
    # 검은 쇠 칼날 + 달궈진 날
    blade = strip(along(a, b, tg), b, prof, n=120)
    p.shape("ember", strip(along(a, b, tg + 0.01), along(a, b, 0.99), lambda t: prof(t) * 1.04, n=120))
    p.shape("dsteel", strip(along(a, b, tg), along(a, b, 0.97), lambda t: prof(t) * 0.78, n=120), profile="blade",
            grooves=[(strip(along(a, b, tg + 0.03), along(a, b, 0.8), lambda t: 0.006), 0.009)])
    for k in range(5):                                             # 날에 흐르는 불씨 균열
        t0 = 0.34 + k * 0.11
        p.shape("ember", strip(along(a, b, t0, 0.008), along(a, b, t0 + 0.05, -0.012), lambda t: 0.0035, n=4))
    guard_volute(p, a, b, tg, 0.15, "dsteel", gem="gem_amber")
    return p.finish()


def hydra_fang():
    p = Painting()
    a = (0.12, 0.9)
    b = (0.46, 0.56)
    tg = 0.44
    # 비늘 손잡이 + 뱀 눈 폼멜
    p.shape("green", strip(along(a, b, 0.08), along(a, b, tg), lambda t: 0.036, n=20), bevel=0.03, direction=(0.707, -0.707))
    pommel(p, along(a, b, 0.05), 0.05, "bronze", gem="gem_amber")
    # 휘어진 상아 이빨 날
    base = along(a, b, tg)
    spine = bez(base, (0.6, 0.38), (0.78, 0.26), (0.93, 0.05), n=80)
    blade = curve_strip(spine, lambda t: max(0.058 * (1 - t) ** 0.8, 0.0015))
    p.shape("bone", blade, profile="blade")
    p.shape("venom", curve_strip(spine[4:62], lambda t: 0.007 * (1 - t * 0.6)), bevel=0.006, height=0.6)
    for d in ((0.62, 0.47), (0.67, 0.43), (0.57, 0.52)):
        p.shape("venom", ellipse(d, 0.009, 0.013), bevel=0.01)
    # 뱀 머리 코등이 두 개
    for sgn in (1, -1):
        neck = bez(along(a, b, tg), along(a, b, tg + 0.05, sgn * 0.08), along(a, b, tg + 0.18, sgn * 0.12), n=30)
        p.shape("green", curve_strip(neck, lambda t: 0.024 - t * 0.008), bevel=0.02)
        h = neck[-1]
        p.shape("green", ellipse(h, 0.032, 0.022, rot=-0.3 * sgn), bevel=0.02)
        p.shape("gem_amber", ellipse((h[0] + 0.006, h[1] - 0.008), 0.007, 0.007), bevel=0.006, height=1.4)
    return p.finish()


def siege_hammer():
    p = Painting()
    a, b = (0.1, 0.92), (0.66, 0.36)
    p.shape("wood", strip(a, b, lambda t: 0.03, n=30), bevel=0.028, direction=(0.707, -0.707))
    wrap_grip(p, a, b, 0.04, 0.3, 0.032, "leather", bands=6, wire="steel")
    for s in (0.62, 0.72):
        p.shape("steel", strip(along(a, b, s - 0.015), along(a, b, s + 0.015), lambda t: 0.04, n=4), bevel=0.012)
    # 숫양 머리 망치
    hc = along(a, b, 0.93)
    blk = [along(a, b, 0.84, 0.2), along(a, b, 0.84, -0.2), along(a, b, 1.04, -0.2), along(a, b, 1.04, 0.2)]
    p.shape("bronze", blk, bevel=0.035)
    p.shape("dsteel", [along(a, b, 0.85, 0.215), along(a, b, 0.85, 0.17), along(a, b, 1.03, 0.17), along(a, b, 1.03, 0.215)], bevel=0.015)
    p.shape("dsteel", [along(a, b, 0.85, -0.17), along(a, b, 0.85, -0.215), along(a, b, 1.03, -0.215), along(a, b, 1.03, -0.17)], bevel=0.015)
    for sgn in (1, -1):                                            # 말린 뿔
        c = along(a, b, 0.94, sgn * 0.085)
        spiral = [(c[0] + math.cos(t) * (0.055 - t * 0.006), c[1] + math.sin(t) * (0.055 - t * 0.006)) for t in [i * 0.2 for i in range(40)]]
        p.shape("gold", curve_strip(spiral, lambda t: 0.014 - t * 0.008), bevel=0.012, height=1.3)
    p.shape("gem_red", ellipse(along(a, b, 0.94), 0.02, 0.02), bevel=0.015, height=1.5)
    return p.finish()


def scylla_trident():
    p = Painting()
    a, b = (0.05, 0.95), (0.66, 0.34)
    p.shape("teal", strip(a, b, lambda t: 0.022, n=30), bevel=0.02, direction=(0.707, -0.707))
    p.shape("bronze", strip(a, along(a, b, 0.04), lambda t: 0.028, n=4), bevel=0.015)
    # 감긴 촉수
    pts = []
    for i in range(120):
        t = 0.1 + i / 120 * 0.62
        pts.append(along(a, b, t, math.sin(t * 60) * 0.03))
    p.shape("purple", curve_strip(pts, lambda t: 0.012 - t * 0.004), bevel=0.012, height=1.2)
    for i in range(0, 120, 12):
        p.shape("marble", ellipse(pts[i], 0.005, 0.005), bevel=0.005, height=1.4)
    # 갈래
    cb = along(a, b, 0.98)
    p.shape("bronze", strip(along(a, b, 0.98, 0.13), along(a, b, 0.98, -0.13), lambda t: 0.022, n=10), bevel=0.018)
    for o, L in ((0.0, 0.36), (0.11, 0.26), (-0.11, 0.26)):
        s0 = along(a, b, 0.99, o)
        tip = along(a, b, 0.99 + L, o)
        p.shape("steel", strip(s0, tip, lambda t: 0.014 if t < 0.8 else max(0.0015, 0.014 * (1 - (t - 0.8) / 0.2)), n=30), profile="blade")
        barb = [along(a, b, 0.99 + L * 0.82, o), along(a, b, 0.99 + L * 0.62, o - 0.035 * (1 if o >= 0 else -1) - (0.035 if o == 0 else 0)),
                along(a, b, 0.99 + L * 0.7, o)]
        p.shape("steel", barb, bevel=0.008)
    p.shape("gem_blue", ellipse(cb, 0.02, 0.02), bevel=0.015, height=1.5)
    return p.finish()


def spear(tip_left=False):
    p = Painting()
    if tip_left:
        a, b = (0.97, 0.97), (0.3, 0.3)
    else:
        a, b = (0.03, 0.97), (0.7, 0.3)
    p.shape("bronze", strip(a, along(a, b, 0.08), lambda t: 0.012 + 0.008 * t, n=10), profile="blade")
    p.shape("wood", strip(along(a, b, 0.07), b, lambda t: 0.016, n=30), bevel=0.016, direction=(0.707, -0.707))
    for s in (0.42, 0.5):
        p.shape("leather", strip(along(a, b, s), along(a, b, s + 0.06), lambda t: 0.019, n=4), bevel=0.01)
    p.shape("bronze", strip(along(a, b, 0.97), along(a, b, 1.06), lambda t: 0.02, n=6), bevel=0.012)
    def prof(t):
        w = 0.012 + 0.05 * math.sin(min(1.0, t * 1.4) * math.pi) ** 1.2
        if t > 0.7:
            w *= max(0.0, 1 - (t - 0.7) / 0.3)
        return max(w, 0.0015)
    c = along(a, b, 1.06)
    d = along(a, b, 1.42)
    p.shape("steel", strip(c, d, prof, n=80), profile="blade", grooves=[(strip(along(c, d, 0.05), along(c, d, 0.7), lambda t: 0.004), 0.006)])
    return p.finish()


def dory():
    return spear(False)


def dory_in_hand():
    return spear(True)


def helmet(metal="bronze", crest="red", eye=None):
    """코린트식 투구 (3/4 옆모습): 둥근 정수리 · 긴 뺨가리개 · 코가리개 · 눈구멍 · 말총 볏"""
    p = Painting()
    # 말총 볏 (뒤에서 앞으로 휘는 부채꼴 + 털 결)
    arc = bez((0.2, 0.42), (0.26, 0.04), (0.62, 0.02), (0.9, 0.34), n=60)
    p.shape(crest, curve_strip(arc, lambda t: 0.06 + 0.03 * math.sin(t * math.pi)), bevel=0.03, direction=(0.2, 1))
    for k in range(9):
        t = 0.08 + k * 0.1
        i = int(t * 60)
        q = arc[i]
        p.shape(crest, ellipse((q[0], q[1] - 0.02), 0.012, 0.05, rot=0.4 - t), bevel=0.012, height=0.7)
    p.shape("gold" if metal == "bronze" else "silver", curve_strip(arc[5:56], lambda t: 0.012), bevel=0.01, height=1.2)
    # 투구 몸통
    body = (bez((0.2, 0.46), (0.2, 0.2), (0.72, 0.18), (0.8, 0.44), n=40)
            + bez((0.8, 0.44), (0.84, 0.62), (0.8, 0.8), (0.72, 0.94), n=30)
            + [(0.6, 0.94), (0.6, 0.72), (0.52, 0.68), (0.46, 0.94), (0.3, 0.9)]
            + bez((0.3, 0.9), (0.22, 0.78), (0.18, 0.62), (0.2, 0.46), n=30))
    p.shape(metal, body, bevel=0.07)
    # 눈썹 테 · 눈구멍 · 코가리개
    p.shape(metal, curve_strip(bez((0.25, 0.5), (0.45, 0.42), (0.78, 0.5), n=40), lambda t: 0.018), bevel=0.015, height=1.3)
    eyec = eye or "black"
    p.shape(eyec, bez((0.3, 0.55), (0.4, 0.5), (0.49, 0.57), (0.44, 0.64), n=20) + [(0.34, 0.63)], bevel=0.01, height=0.3)
    p.shape(eyec, bez((0.58, 0.57), (0.66, 0.51), (0.76, 0.55), (0.74, 0.63), n=20) + [(0.62, 0.64)], bevel=0.01, height=0.3)
    p.shape(metal, [(0.5, 0.52), (0.56, 0.52), (0.555, 0.8), (0.505, 0.8)], bevel=0.012, height=1.2)
    # 가장자리 테두리 새김 (정수리 선)
    p.shape("gold" if metal == "bronze" else "silver", curve_strip(bez((0.24, 0.4), (0.32, 0.22), (0.7, 0.2), (0.78, 0.4), n=40),
                                                                    lambda t: 0.008), bevel=0.008, height=1.4)
    for x, y in ((0.26, 0.72), (0.76, 0.72), (0.3, 0.84), (0.72, 0.84)):
        p.shape("gold" if metal == "bronze" else "silver", ellipse((x, y), 0.012, 0.012), bevel=0.01, height=1.5)
    return p.finish()


def corinthian():
    return helmet("bronze", "red")


def hades_helm():
    return helmet("dsteel", "purple", eye="soulfire")


def lion_pelt():
    p = Painting()
    cloak = [(0.12, 0.34), (0.88, 0.34)] + bez((0.88, 0.34), (0.96, 0.7), (0.92, 0.9), n=20) + \
        [(0.84, 0.97), (0.76, 0.88), (0.66, 0.98), (0.56, 0.89), (0.46, 0.99), (0.36, 0.89), (0.26, 0.98), (0.16, 0.9)] + \
        bez((0.08, 0.9), (0.04, 0.7), (0.12, 0.34), n=20)
    p.shape("fur", cloak, bevel=0.08, direction=(0, 1))
    # 앞발 두 개 (매듭)
    for sgn in (1, -1):
        paw = bez((0.5 + sgn * 0.3, 0.38), (0.5 + sgn * 0.38, 0.55), (0.5 + sgn * 0.3, 0.72), n=20)
        p.shape("fur", curve_strip(paw, lambda t: 0.05), bevel=0.04, direction=(0, 1))
        for k in range(3):
            c = (0.5 + sgn * (0.28 + k * 0.025), 0.74 + k * 0.012)
            p.shape("bone", [(c[0] - 0.01, c[1]), (c[0] + 0.01, c[1]), (c[0], c[1] + 0.04)], bevel=0.006)
    # 갈기 (털 뭉치를 겹겹이)
    for k in range(22):
        a = k / 22 * 2 * math.pi
        c = (0.5 + math.cos(a) * 0.22, 0.3 + math.sin(a) * 0.21)
        p.shape("mane", ellipse(c, 0.07, 0.1, rot=a + math.pi / 2), bevel=0.05, direction=(math.cos(a), math.sin(a)))
    for k in range(16):
        a = k / 16 * 2 * math.pi + 0.2
        c = (0.5 + math.cos(a) * 0.15, 0.3 + math.sin(a) * 0.14)
        p.shape("fur", ellipse(c, 0.05, 0.075, rot=a + math.pi / 2), bevel=0.04, direction=(math.cos(a), math.sin(a)))
    # 얼굴
    p.shape("fur", ellipse((0.5, 0.31), 0.14, 0.15), bevel=0.08)
    p.shape("fur", ellipse((0.5, 0.39), 0.08, 0.065), bevel=0.05, height=1.3)
    p.shape("black", [(0.46, 0.35), (0.54, 0.35), (0.5, 0.39)], bevel=0.01, height=1.5)
    p.shape("red", ellipse((0.5, 0.44), 0.04, 0.018), bevel=0.01, height=0.8)
    for sgn in (1, -1):
        p.shape("gem_amber", ellipse((0.5 + sgn * 0.06, 0.27), 0.022, 0.016), bevel=0.012, height=1.2)
        p.shape("black", ellipse((0.5 + sgn * 0.06, 0.27), 0.006, 0.013), bevel=0.004, height=1.4)
        p.shape("bone", [(0.5 + sgn * 0.03, 0.425), (0.5 + sgn * 0.045, 0.425), (0.5 + sgn * 0.037, 0.47)], bevel=0.005, height=1.4)
        p.shape("mane", ellipse((0.5 + sgn * 0.12, 0.17), 0.035, 0.035), bevel=0.02)
    return p.finish()


def cerberus_collar():
    p = Painting()
    c = (0.5, 0.48)
    ring = [(c[0] + math.cos(a) * 0.34, c[1] + math.sin(a) * 0.32) for a in [i / 80 * 2 * math.pi for i in range(80)]]
    inner = [(c[0] + math.cos(a) * 0.22, c[1] + math.sin(a) * 0.2) for a in [i / 80 * 2 * math.pi for i in range(80)]][::-1]
    # 가시 (뒤쪽)
    for k in range(12):
        a = k / 12 * 2 * math.pi + 0.13
        base = (c[0] + math.cos(a) * 0.31, c[1] + math.sin(a) * 0.29)
        tip = (c[0] + math.cos(a) * 0.47, c[1] + math.sin(a) * 0.45)
        nx, ny = -math.sin(a), math.cos(a)
        p.shape("steel", [(base[0] + nx * 0.03, base[1] + ny * 0.03), tip, (base[0] - nx * 0.03, base[1] - ny * 0.03)], profile="blade")
    p.shape("black", ring + [ring[0]] + [inner[-1]] + inner, bevel=0.05, direction=(1, 0))
    for k in range(24):
        a = k / 24 * 2 * math.pi
        p.shape("bronze", ellipse((c[0] + math.cos(a) * 0.28, c[1] + math.sin(a) * 0.26), 0.012, 0.012), bevel=0.01, height=1.4)
    for a in (math.pi * 0.5, math.pi * 0.28, math.pi * 0.72):
        q = (c[0] + math.cos(a) * 0.28, c[1] + math.sin(a) * 0.26 + 0.05)
        p.shape("dsteel", ellipse(q, 0.06, 0.06), bevel=0.03)
        p.shape("soulfire", ellipse(q, 0.045, 0.045))
        p.shape("gem_purple", ellipse(q, 0.03, 0.03), bevel=0.02, height=1.5)
    return p.finish()


def medusa_head():
    p = Painting()
    # 뱀 머리카락 (뒤)
    for k in range(11):
        a = math.pi + k / 10 * math.pi
        s0 = (0.5 + math.cos(a) * 0.14, 0.36 + math.sin(a) * 0.12)
        s3 = (0.5 + math.cos(a) * 0.42, 0.34 + math.sin(a) * 0.3)
        wig = 0.08 * (1 if k % 2 else -1)
        body = bez(s0, (s0[0] + math.cos(a + 1.2) * wig + (s3[0] - s0[0]) * 0.4, s0[1] + (s3[1] - s0[1]) * 0.3),
                   (s3[0] - math.cos(a + 1.2) * wig, s3[1] - (s3[1] - s0[1]) * 0.2), s3, n=30)
        p.shape("green", curve_strip(body, lambda t: 0.028 - t * 0.01), bevel=0.02, direction=(math.cos(a), math.sin(a)))
        p.shape("green", ellipse(s3, 0.035, 0.025, rot=a), bevel=0.02, height=1.1)
        p.shape("gem_amber", ellipse((s3[0] + math.cos(a) * 0.012, s3[1] + math.sin(a) * 0.012 - 0.008), 0.007, 0.007), bevel=0.005, height=1.4)
        p.shape("red", [(s3[0] + math.cos(a) * 0.03, s3[1] + math.sin(a) * 0.03), (s3[0] + math.cos(a) * 0.06 + 0.01, s3[1] + math.sin(a) * 0.06),
                        (s3[0] + math.cos(a) * 0.06 - 0.01, s3[1] + math.sin(a) * 0.06 + 0.01)], bevel=0.004)
    # 얼굴
    face = bez((0.32, 0.36), (0.3, 0.7), (0.44, 0.84), (0.5, 0.86), n=30) + bez((0.5, 0.86), (0.56, 0.84), (0.7, 0.7), (0.68, 0.36), n=30) + \
        bez((0.68, 0.36), (0.62, 0.2), (0.38, 0.2), (0.32, 0.36), n=30)
    p.shape("skin", face, bevel=0.1)
    p.shape("skin", [(0.49, 0.5), (0.51, 0.5), (0.53, 0.64), (0.47, 0.64)], bevel=0.02, height=1.2)
    for sgn in (1, -1):
        p.shape("black", ellipse((0.5 + sgn * 0.085, 0.5), 0.05, 0.026, rot=-0.15 * sgn), bevel=0.01, height=0.4)
        p.shape("soulfire" if False else "gem_green", ellipse((0.5 + sgn * 0.085, 0.5), 0.035, 0.018), bevel=0.012, height=1.2)
        p.shape("skin", curve_strip(bez((0.5 + sgn * 0.03, 0.44), (0.5 + sgn * 0.08, 0.41), (0.5 + sgn * 0.14, 0.45), n=12), lambda t: 0.008),
                bevel=0.006, height=1.3)
    p.shape("red", bez((0.43, 0.72), (0.5, 0.69), (0.57, 0.72), n=12) + bez((0.57, 0.72), (0.5, 0.77), (0.43, 0.72), n=12), bevel=0.01)
    # 잘린 목과 핏방울
    p.shape("red", [(0.42, 0.84), (0.58, 0.84), (0.56, 0.9), (0.44, 0.9)], bevel=0.02)
    for x, y in ((0.47, 0.95), (0.54, 0.97)):
        p.shape("red", ellipse((x, y), 0.012, 0.018), bevel=0.01)
    return p.finish()


def golden_apple():
    p = Painting()
    body = bez((0.5, 0.26), (0.18, 0.1), (0.02, 0.5), (0.26, 0.86), n=40) + bez((0.26, 0.86), (0.38, 0.98), (0.44, 0.9), (0.5, 0.9), n=20) + \
        bez((0.5, 0.9), (0.56, 0.9), (0.62, 0.98), (0.74, 0.86), n=20) + bez((0.74, 0.86), (0.98, 0.5), (0.82, 0.1), (0.5, 0.26), n=40)
    p.shape("gold", body, bevel=0.35)
    p.shape("wood", curve_strip(bez((0.5, 0.3), (0.5, 0.18), (0.56, 0.08), n=20), lambda t: 0.018 - t * 0.006), bevel=0.012)
    leaf = bez((0.55, 0.14), (0.66, 0.02), (0.84, 0.06), n=20) + bez((0.84, 0.06), (0.74, 0.18), (0.55, 0.14), n=20)
    p.shape("leaf", leaf, bevel=0.03, direction=(1, -0.3))
    p.shape("leaf", curve_strip(bez((0.57, 0.13), (0.7, 0.1), (0.82, 0.07), n=12), lambda t: 0.004), bevel=0.004, height=1.3)
    for c, r in (((0.28, 0.36), 0.03), ((0.25, 0.46), 0.012)):
        p.shape("marble", ellipse(c, r, r * 1.4, rot=0.6), bevel=r)
    return p.finish()


def menu():
    p = Painting()
    # 월계관
    for side in (1, -1):
        stem = [(0.5 + side * math.cos(a) * 0.4, 0.52 + math.sin(a) * 0.4) for a in [math.pi * (0.55 + i / 40 * 0.8) for i in range(41)]]
        p.shape("gold", curve_strip(stem, lambda t: 0.01), bevel=0.008)
        for k in range(9):
            q = stem[k * 4 + 2]
            a = math.atan2(q[1] - 0.52, q[0] - 0.5)
            for off in (-0.5, 0.5):
                c = (q[0] + math.cos(a + off) * 0.05, q[1] + math.sin(a + off) * 0.05)
                p.shape("gold", ellipse(c, 0.05, 0.02, rot=a + off + math.pi / 2), bevel=0.02, height=1.1)
    # 신전
    p.shape("marble", [(0.22, 0.78), (0.78, 0.78), (0.8, 0.84), (0.2, 0.84)], bevel=0.02)
    p.shape("marble", [(0.26, 0.73), (0.74, 0.73), (0.76, 0.78), (0.24, 0.78)], bevel=0.02)
    for x in (0.31, 0.43, 0.57, 0.69):
        p.shape("marble", [(x - 0.035, 0.44), (x + 0.035, 0.44), (x + 0.03, 0.73), (x - 0.03, 0.73)], bevel=0.03,
                grooves=[(strip((x - 0.012, 0.46), (x - 0.012, 0.71), lambda t: 0.003), 0.004),
                         (strip((x + 0.012, 0.46), (x + 0.012, 0.71), lambda t: 0.003), 0.004)])
    p.shape("marble", [(0.24, 0.38), (0.76, 0.38), (0.78, 0.44), (0.22, 0.44)], bevel=0.02)
    p.shape("marble", [(0.22, 0.38), (0.5, 0.2), (0.78, 0.38)], bevel=0.04)
    p.shape("gold", curve_strip([(0.24, 0.37), (0.5, 0.22), (0.76, 0.37)], lambda t: 0.008), bevel=0.008, height=1.3)
    p.shape("gem_amber", ellipse((0.5, 0.31), 0.025, 0.025), bevel=0.02, height=1.4)
    return p.finish()


def hero():
    p = Painting()
    c = (0.5, 0.5)
    rim = [(c[0] + math.cos(a) * (0.44 + 0.02 * math.cos(a * 16)), c[1] + math.sin(a) * (0.44 + 0.02 * math.cos(a * 16)))
           for a in [i / 96 * 2 * math.pi for i in range(96)]]
    p.shape("bronze", rim, bevel=0.06)
    p.shape("red", ellipse(c, 0.34, 0.34, n=80), bevel=0.03, height=0.6)
    p.shape("gold", ellipse(c, 0.36, 0.36, n=80)[:1] + ellipse(c, 0.36, 0.36, n=80), bevel=0.01, height=0.3)
    p.shape("red", ellipse(c, 0.33, 0.33, n=80), bevel=0.04, height=0.7)
    bolt = [(0.58, 0.14), (0.34, 0.52), (0.48, 0.52), (0.38, 0.86), (0.68, 0.44), (0.53, 0.44), (0.66, 0.14)]
    p.shape("gold", bolt, bevel=0.03, height=1.4)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        p.shape("gold", ellipse((c[0] + math.cos(a) * 0.395, c[1] + math.sin(a) * 0.395), 0.016, 0.016), bevel=0.012, height=1.5)
    return p.finish()


def bow(kind="archer", pull=0):
    """바닐라 활과 같은 자리: 끝이 오른쪽 위 · 왼쪽 아래, 손잡이가 왼쪽 위로 휜다. pull 0..3"""
    p = Painting()
    top, bot = (0.93, 0.05), (0.05, 0.93)
    grip = (0.2 + pull * 0.012, 0.2 + pull * 0.012)
    limb_mat = "wood" if kind == "archer" else "bone"
    up = bez(grip, (0.36, 0.02), (0.72, -0.02), top, n=50)
    dn = bez(grip, (0.02, 0.36), (-0.02, 0.72), bot, n=50)
    # 시위 (뒤에 그린다)
    smat = "string" if kind == "archer" else "red"
    k = [0, 0.1, 0.16, 0.22][pull]
    pp = (0.49 + k, 0.49 + k)
    if pull == 0:
        p.shape(smat, strip(top, bot, lambda t: 0.005, n=4), bevel=0.004)
    else:
        p.shape(smat, strip(top, pp, lambda t: 0.005, n=4), bevel=0.004)
        p.shape(smat, strip(pp, bot, lambda t: 0.005, n=4), bevel=0.004)
    for limb in (up, dn):
        p.shape(limb_mat, curve_strip(limb, lambda t: 0.034 * (1 - t) + 0.012), bevel=0.02, direction=(0.707, -0.707))
        if kind == "chimera":
            p.shape("ember", curve_strip(limb[8:40], lambda t: 0.006))
        # 반곡 끝 + 끝 장식
        e = limb[-1]
        d = (limb[-1][0] - limb[-4][0], limb[-1][1] - limb[-4][1])
        L = math.hypot(*d) or 1
        d = (d[0] / L, d[1] / L)
        flick = [e, (e[0] + d[0] * 0.03 + d[1] * 0.04, e[1] + d[1] * 0.03 - d[0] * 0.04)]
        p.shape("bronze" if kind == "archer" else "gold", curve_strip(flick, lambda t: 0.012), bevel=0.01)
    # 손잡이 감개
    gl = bez((grip[0] + 0.04, grip[1] - 0.06), grip, (grip[0] - 0.06, grip[1] + 0.04), n=20)
    p.shape("leather" if kind == "archer" else "red", curve_strip(gl, lambda t: 0.042), bevel=0.02, direction=(0.707, 0.707))
    p.shape("gold", ellipse(grip, 0.018, 0.018), bevel=0.012, height=1.4)
    if pull > 0:
        # 화살: 시위 → 손잡이 너머 (촉이 왼쪽 위)
        tipd = [0, 0.02, 0.05, 0.08][pull]
        tip = (grip[0] - 0.1 + tipd, grip[1] - 0.1 + tipd)
        p.shape("wood", strip(pp, tip, lambda t: 0.007, n=4), bevel=0.006)
        head_mat = "steel" if kind == "archer" else "ember"
        hd = [(tip[0] - 0.05, tip[1] - 0.05), (tip[0] + 0.03, tip[1] - 0.006), (tip[0] - 0.006, tip[1] + 0.03)]
        p.shape(head_mat, hd, profile="blade")
        fl = "marble" if kind == "archer" else "red"
        for sgn in (1, -1):
            f = [pp, (pp[0] - 0.08 + sgn * 0.02, pp[1] - 0.08 - sgn * 0.02), (pp[0] - 0.02 + sgn * 0.03, pp[1] - 0.02 - sgn * 0.03)]
            p.shape(fl, f, bevel=0.01, height=0.6)
    return p.finish()


def crossbow(state="standby"):
    """아르테미스의 석궁: 개머리 오른쪽 아래 → 앞 왼쪽 위, 초승달 은빛 활대"""
    p = Painting()
    a, b = (0.95, 0.95), (0.16, 0.16)
    back = {"standby": 0.0, "pull0": 0.08, "pull1": 0.14, "pull2": 0.2, "arrow": 0.2}[state]
    cp = along(a, b, 0.8)
    t_up = along(a, b, 0.72, 0.42)
    t_dn = along(a, b, 0.72, -0.42)
    latch = along(a, b, 0.7 - back)
    p.shape("string", strip(t_up, latch, lambda t: 0.005, n=4), bevel=0.004)
    p.shape("string", strip(t_dn, latch, lambda t: 0.005, n=4), bevel=0.004)
    # 개머리
    stock = strip(a, b, lambda t: 0.055 - 0.02 * t + (0.018 if t < 0.25 else 0), n=40)
    p.shape("black", stock, bevel=0.04, direction=(0.707, 0.707))
    p.shape("silver", strip(along(a, b, 0.3), along(a, b, 0.92), lambda t: 0.012, n=20), bevel=0.01, height=1.3)
    for s in (0.12, 0.22):
        p.shape("silver", strip(along(a, b, s), along(a, b, s + 0.025), lambda t: 0.06, n=4), bevel=0.012)
    # 방아쇠
    p.shape("silver", curve_strip(bez(along(a, b, 0.42, -0.05), along(a, b, 0.45, -0.1), along(a, b, 0.5, -0.1), n=10), lambda t: 0.01), bevel=0.008)
    # 초승달 활대
    for sgn, tip in ((1, t_up), (-1, t_dn)):
        limb = bez(cp, along(a, b, 0.86, sgn * 0.22), tip, n=40)
        p.shape("silver", curve_strip(limb, lambda t: 0.03 * (1 - t) + 0.01), profile="blade")
        p.shape("gem_blue", ellipse(tip, 0.016, 0.016), bevel=0.012, height=1.3)
    p.shape("moon" if False else "silver", ellipse(cp, 0.05, 0.05), bevel=0.03)
    p.shape("gem_blue", ellipse(cp, 0.03, 0.03), bevel=0.02, height=1.5)
    p.shape("silver", ellipse(latch, 0.018, 0.018), bevel=0.012, height=1.4)
    if state == "arrow":
        tip = along(a, b, 1.02)
        p.shape("gold", strip(latch, tip, lambda t: 0.008, n=4), bevel=0.006, height=1.6)
        p.shape("silver", [along(a, b, 1.08), along(a, b, 1.0, 0.03), along(a, b, 1.0, -0.03)], profile="blade", height=1.6)
    return p.finish()


def hoplon_face(size=128):
    p = Painting()
    c = (0.5, 0.5)
    p.shape("bronze", ellipse(c, 0.495, 0.495, n=120), bevel=0.05)
    p.shape("red", ellipse(c, 0.4, 0.4, n=120), bevel=0.06, height=0.8)
    # 베르기나의 별 (16 광선)
    pts = []
    for k in range(32):
        a = k / 32 * 2 * math.pi - math.pi / 2
        r = 0.3 if k % 2 == 0 else 0.09
        pts.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
    p.shape("gold", pts, bevel=0.03, height=1.3)
    p.shape("gold", ellipse(c, 0.07, 0.07), bevel=0.05, height=1.6)
    for k in range(20):
        a = k / 20 * 2 * math.pi
        p.shape("gold", ellipse((c[0] + math.cos(a) * 0.45, c[1] + math.sin(a) * 0.45), 0.014, 0.014), bevel=0.01, height=1.5)
    im = p.finish(outline=False)
    return im.resize((size, size)) if size != 128 else im


def hoplon_back(size=128):
    p = Painting()
    c = (0.5, 0.5)
    p.shape("bronze", ellipse(c, 0.495, 0.495, n=120), bevel=0.05)
    p.shape("wood", ellipse(c, 0.44, 0.44, n=120), bevel=0.05, direction=(1, 0))
    p.shape("leather", strip((0.18, 0.5), (0.82, 0.5), lambda t: 0.04, n=10), bevel=0.02)
    p.shape("leather", strip((0.5, 0.3), (0.5, 0.7), lambda t: 0.035, n=10), bevel=0.02)
    for x in (0.2, 0.8):
        p.shape("bronze", ellipse((x, 0.5), 0.03, 0.03), bevel=0.02, height=1.4)
    im = p.finish(outline=False)
    return im.resize((size, size)) if size != 128 else im


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
    W = Image.new("RGBA", (1100, 560), (48, 44, 42, 255))
    x = xiphos()
    l = labrys()
    W.alpha_composite(x.resize((512, 512), Image.NEAREST), (10, 24))
    W.alpha_composite(l.resize((512, 512), Image.NEAREST), (560, 24))
    W.alpha_composite(x, (10, 0)) if False else None
    W.save(S + "ill_proto.png")
