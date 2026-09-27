"""새 특수무기 8종 + 보스 무기 4종 스킬 효과 그림 (바닥에 깔리는 빛 효과, 512px)
   → tele/fx2_* (평면 모델). 위쪽 = 앞 (시전자가 바라보는 방향)
"""
import math

import numpy as np
from PIL import Image

from skillfx import Canvas, _crack, _noise, _radial, _dark_under, _rng

PAL2 = {
    "frost": ((80, 170, 255), (190, 235, 255), (240, 250, 255)),
    "storm": ((60, 110, 255), (160, 200, 255), (255, 235, 120)),
    "scythe": ((30, 200, 160), (140, 255, 215), (200, 255, 240)),
    "lance": ((255, 200, 80), (255, 240, 180), (255, 255, 235)),
    "skull": ((70, 200, 40), (170, 255, 110), (180, 90, 230)),
    "chakram": ((255, 120, 20), (255, 200, 80), (255, 245, 180)),
    "chain": ((220, 30, 40), (255, 120, 110), (230, 230, 240)),
    "gauntlet": ((255, 90, 10), (255, 170, 60), (255, 230, 150)),
    "talos": ((230, 110, 30), (255, 190, 110), (255, 230, 170)),
    "sphinx": ((230, 160, 50), (255, 225, 140), (90, 140, 255)),
    "ladon": ((50, 190, 40), (160, 255, 110), (255, 220, 60)),
    "cyclops": ((230, 120, 40), (255, 200, 120), (255, 240, 200)),
}
S = 256


def _arc(c, k, cx, cy, r0, r1, a0, a1, val=255, n=80, taper=True):
    """두께가 있는 호 (a0→a1 도, 가운데 굵고 끝 가늘게)"""
    outer, inner = [], []
    for t in np.linspace(0, 1, n):
        a = math.radians(a0 + (a1 - a0) * t)
        w = (r1 - r0) * (math.sin(math.pi * t) ** 0.8 if taper else 1)
        outer.append((cx + math.cos(a) * (r0 + w), cy + math.sin(a) * (r0 + w)))
        inner.append((cx + math.cos(a) * r0, cy + math.sin(a) * r0))
    c.poly(k, outer + inner[::-1], val)


def _sparks(c, R, cx, cy, rmin, rmax, n, k="gold", size=(0.6, 1.8), amin=0, amax=360):
    for i in range(n):
        a = math.radians(R.uniform(amin, amax)); r = R.uniform(rmin, rmax)
        c.disc(k if i % 3 else "core", cx + math.cos(a) * r, cy + math.sin(a) * r, R.uniform(*size))


def _streaks(c, R, cx, y0, y1, n, spread, k="mid", w=(0.8, 2.6)):
    for i in range(n):
        x = cx + R.normal(0, spread)
        a, b = R.uniform(y1, (y0 + y1) / 2), R.uniform((y0 + y1) / 2, y0)
        c.line(k if i % 4 else "core", [(x, b), (x, a)], R.uniform(*w), int(R.uniform(150, 255)))


def frost_burst():
    """얼음 가시 폭발: 육각 눈꽃 + 뻗는 얼음 결정 + 서리 가루"""
    c = Canvas(S, S); R = _rng(101); cx = cy = S / 2
    for i in range(6):
        a = math.radians(i * 60 + 30)
        L = 105
        tip = (cx + math.cos(a) * L, cy + math.sin(a) * L)
        side = (math.cos(a + math.pi / 2), math.sin(a + math.pi / 2))
        c.poly("mid", [(cx + side[0] * 9, cy + side[1] * 9), tip, (cx - side[0] * 9, cy - side[1] * 9)], 210)
        c.line("core", [(cx, cy), tip], 2.4)
        for f in (0.45, 0.7):
            bx, by = cx + math.cos(a) * L * f, cy + math.sin(a) * L * f
            for s_ in (-1, 1):
                b = a + s_ * math.radians(50)
                c.line("core", [(bx, by), (bx + math.cos(b) * 26 * (1.2 - f), by + math.sin(b) * 26 * (1.2 - f))], 1.8)
    for i in range(14):
        a = R.uniform(0, 6.28); L = R.uniform(40, 90)
        side = (math.cos(a + 1.57), math.sin(a + 1.57))
        bx, by = cx + math.cos(a) * 20, cy + math.sin(a) * 20
        c.poly("mid", [(bx + side[0] * 5, by + side[1] * 5), (bx + math.cos(a) * L, by + math.sin(a) * L), (bx - side[0] * 5, by - side[1] * 5)], 150)
    c.circle("mid", cx, cy, 100, 2.0, 170)
    c.disc("core", cx, cy, 14)
    _sparks(c, R, cx, cy, 20, 120, 90, "gold", (0.5, 1.6))
    g = c.render(PAL2["frost"], bloom=1.0, core_white=0.7)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - rr / 110, 0, 1) * 0.25)


def frost_arrow():
    """얼음 화살 궤적 (위쪽 = 날아가는 방향)"""
    c = Canvas(S, S); R = _rng(102); cx = S / 2
    c.poly("mid", [(cx - 10, S * 0.95), (cx, S * 0.05), (cx + 10, S * 0.95)], 200)
    c.line("core", [(cx, S * 0.95), (cx, S * 0.06)], 3.0)
    c.poly("core", [(cx - 16, S * 0.2), (cx, S * 0.02), (cx + 16, S * 0.2), (cx, S * 0.14)], 255)
    _streaks(c, R, cx, S * 0.98, S * 0.25, 18, 14)
    for i in range(30):
        c.disc("gold", cx + R.normal(0, 20), R.uniform(S * 0.2, S), R.uniform(0.5, 1.5))
    return c.render(PAL2["frost"], bloom=1.0)


def storm_strike():
    """낙뢰 충격: 푸른 번개 균열 + 노란 번개 가지 + 충격 고리"""
    c = Canvas(S, S); R = _rng(111); cx = cy = S / 2
    for i in range(11):
        a = 2 * math.pi * i / 11 + R.normal(0, 0.15)
        _crack(c, cx + math.cos(a) * 12, cy + math.sin(a) * 12, a, R.uniform(80, 120), 5.0, R, "mid", val=230)
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        _crack(c, cx + math.cos(a) * 20, cy + math.sin(a) * 20, a, R.uniform(50, 80), 2.6, R, "gold", val=255)
    c.circle("mid", cx, cy, 70, 3.0, 200)
    c.circle("core", cx, cy, 72, 1.2, 255)
    c.circle("mid", cx, cy, 108, 1.6, 120)
    c.disc("core", cx, cy, 18)
    c.disc("mid", cx, cy, 34, 170)
    _sparks(c, R, cx, cy, 30, 120, 80)
    g = c.render(PAL2["storm"], bloom=1.15, core_white=0.8)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - rr / 100, 0, 1) ** 0.8 * (0.3 + 0.3 * _noise(S, 30, 7)))


def scythe_ring():
    """영혼 수확: 한 바퀴 휘감는 초승달 베기 두 겹 + 영혼 꼬리"""
    c = Canvas(S, S); R = _rng(121); cx = cy = S / 2
    _arc(c, "mid", cx, cy, 78, 112, -90, 250, 150, 140)
    _arc(c, "mid", cx, cy, 86, 106, -60, 240, 220, 140)
    _arc(c, "core", cx, cy, 96, 104, -40, 220, 255, 140)
    for i in range(10):
        a0 = R.uniform(0, 360)
        pts = [(cx + math.cos(math.radians(a0 + t * 30)) * (100 + t * 16), cy + math.sin(math.radians(a0 + t * 30)) * (100 + t * 16)) for t in np.linspace(0, 1, 16)]
        c.line("mid", pts, R.uniform(1.5, 3.5), 200)
    for i in range(12):
        a = math.radians(i * 30)
        c.disc("core", cx + math.cos(a) * 60, cy + math.sin(a) * 60, 2.2)
    c.circle("mid", cx, cy, 58, 1.5, 150)
    _sparks(c, R, cx, cy, 70, 125, 70, "gold", (0.6, 2.0))
    g = c.render(PAL2["scythe"], bloom=1.1, core_white=0.6)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - np.abs(rr - 95) / 35, 0, 1) * 0.35)


def lance_streak():
    """성광 돌격: 앞으로 뻗는 빛창 + 양옆 빛 날개 깃 + 빛가루"""
    c = Canvas(S, S); R = _rng(131); cx = S / 2
    c.poly("mid", [(cx - 22, S * 0.98), (cx, S * 0.02), (cx + 22, S * 0.98)], 190)
    c.poly("core", [(cx - 8, S * 0.95), (cx, S * 0.04), (cx + 8, S * 0.95)], 255)
    for s_ in (-1, 1):
        for k in range(5):
            y0 = S * (0.55 + k * 0.08)
            pts = [(cx + s_ * 14, y0), (cx + s_ * (50 + k * 8), y0 + 18), (cx + s_ * (90 - k * 6), y0 + 50)]
            c.line("mid", pts, 7 - k, 220)
            c.line("core", pts, 2, 255)
    _streaks(c, R, cx, S, S * 0.1, 24, 30, "mid", (0.6, 2.0))
    for i in range(50):
        c.disc("gold", cx + R.normal(0, 34), R.uniform(0, S), R.uniform(0.5, 1.6))
    return c.render(PAL2["lance"], bloom=1.1, core_white=0.8)


def skull_miasma():
    """저주의 독 구름: 초록 늪 + 거품 + 가운데 해골 룬 + 보라 저주 고리"""
    c = Canvas(S, S); R = _rng(141); cx = cy = S / 2
    n = _noise(S, 40, 5)
    for i in range(40):
        a = R.uniform(0, 6.28); r = R.uniform(0, 90)
        c.disc("mid", cx + math.cos(a) * r, cy + math.sin(a) * r, R.uniform(10, 26), int(R.uniform(60, 130)))
    for i in range(26):
        a = R.uniform(0, 6.28); r = R.uniform(10, 100)
        x, y, rr = cx + math.cos(a) * r, cy + math.sin(a) * r, R.uniform(3, 8)
        c.circle("core", x, y, rr, 1.2, 230)
    # 해골 룬
    c.circle("gold", cx, cy, 44, 2.5, 230)
    c.circle("gold", cx, cy, 112, 2.0, 200)
    for i in range(16):
        a = math.radians(i * 22.5)
        x, y = cx + math.cos(a) * 112, cy + math.sin(a) * 112
        c.line("gold", [(x - 4, y - 4), (x + 4, y + 4)], 1.6)
        c.line("gold", [(x - 4, y + 4), (x + 4, y - 4)], 1.6)
    c.disc("core", cx, cy - 6, 22, 200)
    c.disc("mid", cx - 9, cy - 8, 6, 30)
    c.disc("mid", cx + 9, cy - 8, 6, 30)
    c.poly("core", [(cx - 12, cy + 10), (cx + 12, cy + 10), (cx + 8, cy + 22), (cx - 8, cy + 22)], 200)
    g = c.render(PAL2["skull"], bloom=1.0, core_white=0.4)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - rr / 115, 0, 1) * (0.35 + 0.3 * n))


def chakram_sun():
    """태양 원반: 도는 해 (가시 햇살 16개) + 불꽃 소용돌이"""
    c = Canvas(S, S); R = _rng(151); cx = cy = S / 2
    for i in range(16):
        a = math.radians(i * 22.5)
        L = 118 if i % 2 == 0 else 96
        side = (math.cos(a + 1.57), math.sin(a + 1.57))
        bx, by = cx + math.cos(a) * 54, cy + math.sin(a) * 54
        c.poly("mid", [(bx + side[0] * 10, by + side[1] * 10), (cx + math.cos(a + 0.1) * L, cy + math.sin(a + 0.1) * L), (bx - side[0] * 10, by - side[1] * 10)], 220)
    for i in range(8):
        a0 = i * 45
        pts = [(cx + math.cos(math.radians(a0 + t * 70)) * (60 + t * 50), cy + math.sin(math.radians(a0 + t * 70)) * (60 + t * 50)) for t in np.linspace(0, 1, 20)]
        c.line("core", pts, 2.5, 230)
    c.circle("core", cx, cy, 56, 5, 255)
    c.circle("gold", cx, cy, 44, 2.5, 255)
    c.disc("mid", cx, cy, 30, 180)
    c.disc("core", cx, cy, 14)
    _sparks(c, R, cx, cy, 60, 125, 70)
    return c.render(PAL2["chakram"], bloom=1.15, core_white=0.6)


def chain_hook():
    """사슬 걸기: 붉은 표적 문양 + 도는 사슬 고리 + 갈고리 네 개"""
    c = Canvas(S, S); R = _rng(161); cx = cy = S / 2
    for i in range(22):
        a = math.radians(i * 360 / 22)
        x, y = cx + math.cos(a) * 88, cy + math.sin(a) * 88
        if i % 2:
            c.circle("gold", x, y, 8, 2.4, 240)
        else:
            c.line("gold", [(x - math.sin(a) * 9, y + math.cos(a) * 9), (x + math.sin(a) * 9, y - math.cos(a) * 9)], 3.2, 240)
    for i in range(4):
        a = math.radians(i * 90 + 45)
        pts = [(cx + math.cos(a) * 30, cy + math.sin(a) * 30), (cx + math.cos(a) * 70, cy + math.sin(a) * 70),
               (cx + math.cos(a + 0.35) * 76, cy + math.sin(a + 0.35) * 76), (cx + math.cos(a + 0.5) * 64, cy + math.sin(a + 0.5) * 64)]
        c.line("mid", pts, 5, 230)
        c.line("core", pts, 1.8)
    c.circle("mid", cx, cy, 44, 4, 220)
    c.circle("core", cx, cy, 24, 2, 255)
    c.disc("core", cx, cy, 6)
    c.circle("mid", cx, cy, 116, 1.5, 150)
    _sparks(c, R, cx, cy, 40, 120, 50, "mid")
    g = c.render(PAL2["chain"], bloom=1.0, core_white=0.5)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - rr / 120, 0, 1) * 0.3)


def gauntlet_fissure():
    """대지 분쇄: 앞으로 길게 갈라지는 땅 + 용암 빛 + 튄 돌 조각 (아래 = 시전자)"""
    c = Canvas(S, S); R = _rng(171); cx = S / 2
    x, y, pts = cx, S * 0.97, []
    while y > S * 0.03:
        pts.append((x, y)); x += R.normal(0, 5); x = min(max(x, cx - 14), cx + 14); y -= 8
    for i in range(len(pts) - 1):
        t = i / len(pts)
        c.line("mid", [pts[i], pts[i + 1]], 14 * (1 - t * 0.5), 200)
        c.line("core", [pts[i], pts[i + 1]], 4.5 * (1 - t * 0.4), 255)
    for i in range(18):
        px, py = pts[R.integers(2, len(pts) - 2)]
        a = math.radians(R.choice([0, 180]) + R.normal(0, 35))
        _crack(c, px, py, a, R.uniform(24, 60), 2.8, R, "mid", val=220)
    for i in range(40):
        px, py = pts[R.integers(0, len(pts))]
        c.poly("gold", [(px + R.normal(0, 30), py + R.normal(0, 8)) for _ in range(3)], 200)
    g = c.render(PAL2["gauntlet"], bloom=1.1, core_white=0.55)
    yy, xx = np.mgrid[0:S, 0:S]
    dark = np.clip(1 - np.abs(xx - cx) / 60, 0, 1) * (0.4 + 0.3 * _noise(S, 20, 9))
    return _dark_under(g, dark)


def talos_gear():
    """청동 폭주 발자국: 톱니바퀴 문양 + 증기 고리 + 용광로 심지"""
    c = Canvas(S, S); R = _rng(181); cx = cy = S / 2
    teeth = 14
    outer = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        r = 96 if (i % 4) in (1, 2) else 80
        outer.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    c.poly("mid", outer, 170)
    c.disc("mid", cx, cy, 64, 0)
    lay = c.layers["mid"]
    c.circle("core", cx, cy, 80, 3.0)
    c.circle("gold", cx, cy, 58, 3.5)
    for i in range(6):
        a = math.radians(i * 60)
        c.line("gold", [(cx + math.cos(a) * 20, cy + math.sin(a) * 20), (cx + math.cos(a) * 56, cy + math.sin(a) * 56)], 4)
    c.disc("core", cx, cy, 16)
    for i in range(10):
        a0 = R.uniform(0, 360)
        pts = [(cx + math.cos(math.radians(a0 + t * 40)) * (100 + t * 20), cy + math.sin(math.radians(a0 + t * 40)) * (100 + t * 20)) for t in np.linspace(0, 1, 12)]
        c.line("mid", pts, R.uniform(3, 7), 110)
    _sparks(c, R, cx, cy, 90, 125, 50)
    g = c.render(PAL2["talos"], bloom=1.1, core_white=0.55)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - rr / 100, 0, 1) * 0.35)


def sphinx_vortex():
    """시간의 모래폭풍: 모래 소용돌이 팔 + 상형문자 고리 + 가운데 지혜의 눈"""
    c = Canvas(S, S); R = _rng(191); cx = cy = S / 2
    for arm in range(5):
        a0 = arm * 72
        for layer, (w, k, v) in enumerate(((9, "mid", 150), (4, "mid", 230), (1.6, "core", 255))):
            pts = [(cx + math.cos(math.radians(a0 + t * 300)) * (14 + t * 104), cy + math.sin(math.radians(a0 + t * 300)) * (14 + t * 104)) for t in np.linspace(0, 1, 60)]
            c.line(k, pts, w, v)
    c.circle("gold", cx, cy, 70, 2.2, 230)
    c.circle("gold", cx, cy, 84, 1.4, 200)
    for i in range(20):
        a = math.radians(i * 18)
        x, y = cx + math.cos(a) * 77, cy + math.sin(a) * 77
        kind = i % 4
        if kind == 0:
            c.circle("gold", x, y, 3, 1.2)
        elif kind == 1:
            c.line("gold", [(x - 3, y), (x + 3, y)], 1.4); c.line("gold", [(x, y - 3), (x, y + 3)], 1.4)
        elif kind == 2:
            c.poly("gold", [(x - 3, y + 3), (x, y - 3), (x + 3, y + 3)], 230)
        else:
            c.line("gold", [(x - 3, y - 3), (x + 3, y + 3)], 1.4)
    # 눈
    pts_u = [(cx - 30 + t * 60, cy - math.sin(math.pi * t) * 16) for t in np.linspace(0, 1, 20)]
    pts_d = [(cx - 30 + t * 60, cy + math.sin(math.pi * t) * 16) for t in np.linspace(0, 1, 20)]
    c.line("core", pts_u, 2.4); c.line("core", pts_d, 2.4)
    c.disc("gold", cx, cy, 8, 255)
    c.line("core", [(cx - 2, cy + 16), (cx - 8, cy + 30), (cx + 4, cy + 36)], 1.8)
    for i in range(120):
        a = R.uniform(0, 6.28); r = R.uniform(20, 125)
        c.disc("mid", cx + math.cos(a) * r, cy + math.sin(a) * r, R.uniform(0.5, 1.5), 230)
    g = c.render(PAL2["sphinx"], bloom=1.0, core_white=0.5)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - rr / 125, 0, 1) * (0.2 + 0.3 * _noise(S, 24, 3)))


def ladon_fan():
    """삼두 채찍질: 부채꼴로 뻗는 세 줄기 독 채찍 (아래 가운데 = 시전자)"""
    c = Canvas(S, S); R = _rng(201); ox, oy = S / 2, S * 0.95
    for j, a in enumerate((-32, 0, 32)):
        rad = math.radians(a - 90)
        pts = []
        for t in np.linspace(0, 1, 40):
            L = t * 225
            wob = math.sin(t * 9 + j) * 12 * t
            x = ox + math.cos(rad) * L - math.sin(rad) * wob
            y = oy + math.sin(rad) * L + math.cos(rad) * wob
            pts.append((x, y))
        for i in range(len(pts) - 1):
            t = i / len(pts)
            c.line("mid", [pts[i], pts[i + 1]], 14 * (1 - t * 0.6), 190)
            c.line("core", [pts[i], pts[i + 1]], 4 * (1 - t * 0.5), 255)
        hx, hy = pts[-1]
        c.disc("mid", hx, hy, 12, 230)
        c.disc("gold", hx - 4, hy - 2, 2.5); c.disc("gold", hx + 4, hy - 2, 2.5)
        for i in range(14):
            px, py = pts[R.integers(5, len(pts))]
            c.disc("gold" if i % 3 == 0 else "mid", px + R.normal(0, 12), py + R.normal(0, 12), R.uniform(1, 3.5), 220)
    g = c.render(PAL2["ladon"], bloom=1.05, core_white=0.5)
    rr, ang = _radial(S, ox, oy)
    ad = np.degrees(ang)
    dark = ((ad > -135) & (ad < -45)).astype(np.float32) * np.clip(1 - rr / 230, 0, 1) * 0.35
    return _dark_under(g, dark)


def cyclops_crater():
    """거암 충돌: 움푹 팬 구덩이 + 사방 균열 + 흙먼지 고리 + 튄 돌"""
    c = Canvas(S, S); R = _rng(211); cx = cy = S / 2
    for i in range(14):
        a = 2 * math.pi * i / 14 + R.normal(0, 0.12)
        _crack(c, cx + math.cos(a) * 34, cy + math.sin(a) * 34, a, R.uniform(60, 95), 5.5, R, "mid", val=210)
    c.circle("core", cx, cy, 36, 4, 255)
    c.circle("mid", cx, cy, 100, 6, 150)
    c.circle("mid", cx, cy, 112, 2.5, 110)
    for i in range(30):
        a = R.uniform(0, 6.28); r = R.uniform(40, 120)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        c.poly("gold", [(x + R.normal(0, 5), y + R.normal(0, 5)) for _ in range(4)], 200)
    _sparks(c, R, cx, cy, 30, 125, 60)
    g = c.render(PAL2["cyclops"], bloom=1.1, core_white=0.5)
    rr, _ = _radial(S, cx, cy)
    dark = np.clip(1 - rr / 40, 0, 1) * 0.75 + np.clip(1 - np.abs(rr - 70) / 50, 0, 1) * 0.3 * _noise(S, 20, 4)
    return _dark_under(g, np.clip(dark, 0, 0.85))


FX = {"fx2_frost_burst": frost_burst, "fx2_frost_arrow": frost_arrow, "fx2_storm_strike": storm_strike,
      "fx2_scythe_ring": scythe_ring, "fx2_lance_streak": lance_streak, "fx2_skull_miasma": skull_miasma,
      "fx2_chakram_sun": chakram_sun, "fx2_chain_hook": chain_hook, "fx2_gauntlet_fissure": gauntlet_fissure,
      "fx2_talos_gear": talos_gear, "fx2_sphinx_vortex": sphinx_vortex, "fx2_ladon_fan": ladon_fan,
      "fx2_cyclops_crater": cyclops_crater}


def export(pack):
    from telegraphs import flat_model
    for name, fn in FX.items():
        ref = pack.texture(f"tele/{name}", fn())
        pack.item_model(f"tele/{name}", flat_model(ref))


def preview(path):
    cell = 256
    cols = 5
    rows = (len(FX) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cell + 10) + 10, rows * (cell + 10) + 10), (14, 12, 18))
    for i, (name, fn) in enumerate(FX.items()):
        bg = Image.new("RGBA", (cell, cell), (70, 76, 60, 255))
        bg.alpha_composite(fn().resize((cell, cell), Image.LANCZOS))
        sheet.paste(bg.convert("RGB"), (10 + (i % cols) * (cell + 10), 10 + (i // cols) * (cell + 10)))
    sheet.save(path)


if __name__ == "__main__":
    import sys
    preview(sys.argv[1])
