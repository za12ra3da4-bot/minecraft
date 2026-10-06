"""직업 전용 전설 무기 14종 스킬 효과 그림 (바닥에 깔리는 빛 효과) → tele/fx3_<무기> (평면 모델)
   위쪽 = 앞 (시전자가 바라보는 방향)
"""
import math

import numpy as np
from PIL import Image

from skillfx import Canvas, _crack, _noise, _radial, _dark_under, _rng
from skillfx2 import _arc, _sparks, _streaks

PAL3 = {
    "moon": ((90, 140, 255), (190, 215, 255), (255, 255, 255)),
    "magma": ((255, 70, 10), (255, 160, 40), (255, 230, 120)),
    "crystal": ((150, 70, 255), (220, 170, 255), (255, 235, 255)),
    "tempest": ((60, 130, 255), (170, 220, 255), (240, 250, 255)),
    "holy": ((255, 200, 70), (255, 240, 170), (255, 255, 240)),
    "vampire": ((190, 10, 30), (255, 70, 80), (255, 190, 190)),
    "sunbow": ((255, 130, 20), (255, 210, 80), (255, 250, 200)),
    "viper": ((60, 190, 40), (160, 255, 100), (230, 255, 120)),
    "starbow": ((110, 90, 255), (200, 190, 255), (255, 245, 200)),
    "shuriken": ((110, 40, 180), (190, 130, 255), (240, 220, 255)),
    "frostaxe": ((80, 170, 255), (190, 235, 255), (245, 252, 255)),
    "twinaxe": ((230, 60, 40), (255, 150, 110), (255, 230, 210)),
    "mjolnir": ((70, 120, 255), (160, 210, 255), (255, 245, 150)),
    "bastion": ((230, 160, 40), (255, 220, 120), (255, 250, 220)),
}
S = 256


def _star(c, k, cx, cy, R, r0=0.42, n=5, val=255, rot=-90):
    pts = []
    for i in range(n * 2):
        a = math.radians(i * 180 / n + rot)
        rr = R if i % 2 == 0 else R * r0
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    c.poly(k, pts, val)


def moon():
    """월광 발도: 앞으로 길게 뻗은 초승달 참격 두 겹 + 달빛 꽃잎"""
    c = Canvas(S, S); R = _rng(301); cx = S / 2
    _arc(c, "mid", cx, S * 1.05, 150, 196, -150, -30, 200, 120)
    _arc(c, "core", cx, S * 1.05, 172, 188, -140, -40, 255, 120)
    _arc(c, "mid", cx, S * 1.15, 120, 150, -135, -45, 140, 100)
    _streaks(c, R, cx, S * 0.98, S * 0.1, 16, 26, "mid", (0.6, 1.8))
    for i in range(22):
        x, y = R.uniform(30, 226), R.uniform(20, 200)
        c.poly("gold", [(x, y - 4), (x + 3, y), (x, y + 4), (x - 3, y)], 230)
    return c.render(PAL3["moon"], bloom=1.1, core_white=0.8)


def magma():
    """용암 균열: 앞으로 퍼지는 세 갈래 갈라진 땅 + 끝의 불기둥 자국 (아래 = 시전자)"""
    c = Canvas(S, S); R = _rng(302); ox, oy = S / 2, S * 0.96
    for a in (-24, 0, 24):
        rad = math.radians(a - 90)
        x, y, pts = ox, oy, []
        for i in range(30):
            pts.append((x, y))
            x += math.cos(rad) * 7.5 + R.normal(0, 2.5); y += math.sin(rad) * 7.5
        for i in range(len(pts) - 1):
            t = i / len(pts)
            c.line("mid", [pts[i], pts[i + 1]], 12 * (1 - t * 0.4), 210)
            c.line("core", [pts[i], pts[i + 1]], 4 * (1 - t * 0.3), 255)
        for j in range(6):
            px, py = pts[R.integers(3, len(pts) - 1)]
            _crack(c, px, py, rad + R.choice([-1.4, 1.4]) + R.normal(0, 0.3), R.uniform(14, 34), 2.4, R, "mid", val=200)
        ex, ey = pts[-1]
        c.disc("mid", ex, ey, 20, 200)
        c.disc("core", ex, ey, 9)
        _sparks(c, R, ex, ey, 6, 30, 16, "gold", (0.8, 2.2))
    g = c.render(PAL3["magma"], bloom=1.2, core_white=0.55)
    yy, xx = np.mgrid[0:S, 0:S]
    return _dark_under(g, np.clip(1 - np.hypot(xx - ox, yy - oy) / 240, 0, 1) * 0.35 * (0.6 + 0.4 * _noise(S, 20, 6)))


def crystal():
    """결정 감옥: 육각 결정 문양 + 사방으로 자란 자수정 결정 + 빛나는 고리"""
    c = Canvas(S, S); R = _rng(303); cx = cy = S / 2
    hexa = [(cx + math.cos(math.radians(30 + i * 60)) * 62, cy + math.sin(math.radians(30 + i * 60)) * 62) for i in range(6)]
    c.line("core", hexa + [hexa[0]], 3.0)
    for i in range(12):
        a = math.radians(i * 30 + R.normal(0, 4))
        L = 118 if i % 2 == 0 else 90
        side = (math.cos(a + 1.57), math.sin(a + 1.57))
        b = (cx + math.cos(a) * 40, cy + math.sin(a) * 40)
        c.poly("mid", [(b[0] + side[0] * 12, b[1] + side[1] * 12), (cx + math.cos(a) * L, cy + math.sin(a) * L), (b[0] - side[0] * 12, b[1] - side[1] * 12)], 220)
        c.line("core", [b, (cx + math.cos(a) * (L - 6), cy + math.sin(a) * (L - 6))], 1.8)
    c.circle("mid", cx, cy, 110, 2.2, 180)
    c.circle("gold", cx, cy, 36, 3, 255)
    c.disc("core", cx, cy, 12)
    _sparks(c, R, cx, cy, 20, 122, 80, "gold", (0.5, 1.8))
    g = c.render(PAL3["crystal"], bloom=1.1, core_white=0.65)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - rr / 115, 0, 1) * 0.3)


def tempest():
    """회오리 베기: 세 겹으로 감기는 바람 참격 + 바깥 바람 고리"""
    c = Canvas(S, S); R = _rng(304); cx = cy = S / 2
    for j in range(3):
        a0 = j * 120
        _arc(c, "mid", cx, cy, 60 + j * 8, 100 + j * 8, a0, a0 + 200, 190, 100)
        _arc(c, "core", cx, cy, 86 + j * 8, 94 + j * 8, a0 + 20, a0 + 180, 255, 100)
    for i in range(16):
        a0 = R.uniform(0, 360)
        pts = [(cx + math.cos(math.radians(a0 + t * 50)) * (40 + t * 76), cy + math.sin(math.radians(a0 + t * 50)) * (40 + t * 76)) for t in np.linspace(0, 1, 14)]
        c.line("mid", pts, R.uniform(1, 2.6), 170)
    c.circle("mid", cx, cy, 118, 1.6, 130)
    _sparks(c, R, cx, cy, 30, 125, 60, "core", (0.5, 1.4))
    return c.render(PAL3["tempest"], bloom=1.05, core_white=0.7)


def holy():
    """성흔 십자: 빛나는 십자가 + 원형 성배 고리 + 빛살 (위 = 앞)"""
    c = Canvas(S, S); R = _rng(305); cx = cy = S / 2
    c.poly("mid", [(cx - 18, 6), (cx + 18, 6), (cx + 18, S - 6), (cx - 18, S - 6)], 210)
    c.poly("mid", [(16, cy - 18), (S - 16, cy - 18), (S - 16, cy + 18), (16, cy + 18)], 210)
    c.line("core", [(cx, 10), (cx, S - 10)], 6)
    c.line("core", [(20, cy), (S - 20, cy)], 6)
    c.circle("gold", cx, cy, 70, 3.5, 255)
    c.circle("gold", cx, cy, 84, 1.6, 200)
    for i in range(24):
        a = math.radians(i * 15)
        c.line("mid", [(cx + math.cos(a) * 90, cy + math.sin(a) * 90), (cx + math.cos(a) * 120, cy + math.sin(a) * 120)], 2, 160)
    c.disc("core", cx, cy, 20)
    _sparks(c, R, cx, cy, 20, 125, 70)
    return c.render(PAL3["holy"], bloom=1.15, core_white=0.8)


def vampire():
    """핏빛 찌르기: 앞으로 찌른 붉은 궤적 + 핏방울 + 박쥐 날개 무늬"""
    c = Canvas(S, S); R = _rng(306); cx = S / 2
    c.poly("mid", [(cx - 12, S * 0.98), (cx, S * 0.02), (cx + 12, S * 0.98)], 200)
    c.line("core", [(cx, S * 0.95), (cx, S * 0.05)], 2.6)
    for s_ in (-1, 1):
        for k in range(3):
            y0 = S * (0.62 + k * 0.08)
            pts = [(cx + s_ * 10, y0), (cx + s_ * (40 + k * 6), y0 - 22), (cx + s_ * (70 - k * 8), y0 - 6), (cx + s_ * (90 - k * 10), y0 + 16)]
            c.line("mid", pts, 5 - k, 220)
    for i in range(30):
        x, y = cx + R.normal(0, 30), R.uniform(10, S - 10)
        r = R.uniform(1.5, 4)
        c.disc("mid", x, y, r, 220)
        c.disc("core", x - r * 0.3, y - r * 0.3, r * 0.35, 200)
    _streaks(c, R, cx, S, S * 0.1, 14, 12, "mid", (0.6, 1.6))
    return c.render(PAL3["vampire"], bloom=1.0, core_white=0.5)


def sunbow():
    """태양 화살: 태양 원반 문양 (햇살 24개 + 두 겹 고리 + 가운데 해)"""
    c = Canvas(S, S); R = _rng(307); cx = cy = S / 2
    for i in range(24):
        a = math.radians(i * 15)
        L = 120 if i % 2 == 0 else 96
        side = (math.cos(a + 1.57), math.sin(a + 1.57))
        b = (cx + math.cos(a) * 44, cy + math.sin(a) * 44)
        c.poly("mid", [(b[0] + side[0] * 7, b[1] + side[1] * 7), (cx + math.cos(a) * L, cy + math.sin(a) * L), (b[0] - side[0] * 7, b[1] - side[1] * 7)], 210)
    c.circle("core", cx, cy, 46, 4, 255)
    c.circle("gold", cx, cy, 60, 1.8, 220)
    c.disc("mid", cx, cy, 34, 200)
    c.disc("core", cx, cy, 18)
    _sparks(c, R, cx, cy, 50, 125, 60)
    return c.render(PAL3["sunbow"], bloom=1.2, core_white=0.7)


def viper():
    """독사의 이빨: 부채꼴 다섯 줄기 독 화살 궤적 + 뱀 비늘 무늬 (아래 = 시전자)"""
    c = Canvas(S, S); R = _rng(308); ox, oy = S / 2, S * 0.96
    for a in (-44, -22, 0, 22, 44):
        rad = math.radians(a - 90)
        pts = []
        for t in np.linspace(0, 1, 30):
            L = t * 230
            wob = math.sin(t * 14 + a) * 5 * t
            pts.append((ox + math.cos(rad) * L - math.sin(rad) * wob, oy + math.sin(rad) * L + math.cos(rad) * wob))
        for i in range(len(pts) - 1):
            t = i / len(pts)
            c.line("mid", [pts[i], pts[i + 1]], 7 * (1 - t * 0.5), 190)
            c.line("core", [pts[i], pts[i + 1]], 2, 255)
        hx, hy = pts[-1]
        c.poly("gold", [(hx + math.cos(rad) * 10, hy + math.sin(rad) * 10), (hx + math.cos(rad + 2.4) * 8, hy + math.sin(rad + 2.4) * 8),
                        (hx + math.cos(rad - 2.4) * 8, hy + math.sin(rad - 2.4) * 8)], 255)
    for i in range(40):
        a = math.radians(R.uniform(-140, -40)); r = R.uniform(30, 220)
        c.disc("mid", ox + math.cos(a) * r, oy + math.sin(a) * r, R.uniform(1, 3), 200)
    g = c.render(PAL3["viper"], bloom=1.0, core_white=0.5)
    rr, ang = _radial(S, ox, oy)
    ad = np.degrees(ang)
    return _dark_under(g, ((ad > -140) & (ad < -40)).astype(np.float32) * np.clip(1 - rr / 230, 0, 1) * 0.3)


def starbow():
    """유성우: 큰 별 문양 마법진 + 작은 별 · 별자리 선"""
    c = Canvas(S, S); R = _rng(309); cx = cy = S / 2
    c.circle("mid", cx, cy, 112, 2.4, 200)
    c.circle("gold", cx, cy, 100, 1.4, 220)
    _star(c, "mid", cx, cy, 96, 0.4, 5, 150)
    pts = [(cx + math.cos(math.radians(-90 + i * 144)) * 96, cy + math.sin(math.radians(-90 + i * 144)) * 96) for i in range(6)]
    c.line("core", pts, 2.4)
    for i in range(14):
        x, y = cx + R.uniform(-110, 110), cy + R.uniform(-110, 110)
        if math.hypot(x - cx, y - cy) < 115:
            _star(c, "gold", x, y, R.uniform(4, 9), 0.4, 4, 255, rot=R.uniform(0, 90))
    c.disc("core", cx, cy, 14)
    _sparks(c, R, cx, cy, 10, 122, 90, "core", (0.4, 1.3))
    g = c.render(PAL3["starbow"], bloom=1.1, core_white=0.6)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - rr / 118, 0, 1) * 0.35)


def shuriken():
    """그림자 표창: 네 갈래 표창 그림자 + 도는 베기 자국"""
    c = Canvas(S, S); R = _rng(310); cx = cy = S / 2
    for i in range(4):
        a = math.radians(i * 90 + 20)
        tip = (cx + math.cos(a) * 112, cy + math.sin(a) * 112)
        l_ = (cx + math.cos(a + 0.6) * 40, cy + math.sin(a + 0.6) * 40)
        r_ = (cx + math.cos(a - 0.4) * 28, cy + math.sin(a - 0.4) * 28)
        c.poly("mid", [r_, tip, l_], 220)
        c.line("core", [(cx, cy), tip], 1.8)
    for j in range(3):
        _arc(c, "mid", cx, cy, 70 + j * 14, 80 + j * 14, j * 120, j * 120 + 90, 170, 60)
    c.circle("core", cx, cy, 18, 3)
    _sparks(c, R, cx, cy, 20, 120, 40, "gold", (0.5, 1.6))
    return c.render(PAL3["shuriken"], bloom=1.0, core_white=0.5)


def frostaxe():
    """빙하 내려찍기: 사방으로 갈라진 얼음 균열 + 눈꽃 고리 + 가운데 충격"""
    c = Canvas(S, S); R = _rng(311); cx = cy = S / 2
    for i in range(12):
        a = 2 * math.pi * i / 12 + R.normal(0, 0.1)
        _crack(c, cx + math.cos(a) * 24, cy + math.sin(a) * 24, a, R.uniform(70, 110), 4.6, R, "mid", val=230)
    for i in range(8):
        a = math.radians(i * 45)
        x, y = cx + math.cos(a) * 92, cy + math.sin(a) * 92
        for k in range(3):
            b = a + math.radians(k * 60)
            c.line("core", [(x - math.cos(b) * 9, y - math.sin(b) * 9), (x + math.cos(b) * 9, y + math.sin(b) * 9)], 1.8)
    c.circle("mid", cx, cy, 60, 4, 210)
    c.circle("core", cx, cy, 62, 1.4)
    c.circle("mid", cx, cy, 116, 1.6, 140)
    c.disc("core", cx, cy, 22)
    _sparks(c, R, cx, cy, 20, 124, 90, "gold", (0.5, 1.6))
    g = c.render(PAL3["frostaxe"], bloom=1.05, core_white=0.7)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - rr / 110, 0, 1) * 0.3)


def twinaxe():
    """쌍도끼 투척: X 자로 교차하는 두 도끼 궤적 (위 = 앞)"""
    c = Canvas(S, S); R = _rng(312); ox, oy = S / 2, S * 0.97
    for s_ in (-1, 1):
        pts = [(ox + s_ * 70 * math.sin(math.pi * t), oy - t * 236) for t in np.linspace(0, 1, 40)]
        for i in range(len(pts) - 1):
            t = i / len(pts)
            c.line("mid", [pts[i], pts[i + 1]], 10 * (0.5 + 0.5 * math.sin(math.pi * t)), 200)
            c.line("core", [pts[i], pts[i + 1]], 3, 255)
        for k in range(6):
            x, y = pts[R.integers(6, 34)]
            _arc(c, "gold", x, y, 8, 12, 0, 180 * s_, 230, 20)
    _sparks(c, R, ox, oy - 118, 10, 110, 50, "gold", (0.6, 1.8))
    return c.render(PAL3["twinaxe"], bloom=1.0, core_white=0.55)


def mjolnir():
    """묠니르: 망치 자국 사각 + 사방 번개 + 룬 고리"""
    c = Canvas(S, S); R = _rng(313); cx = cy = S / 2
    c.poly("mid", [(cx - 30, cy - 22), (cx + 30, cy - 22), (cx + 30, cy + 22), (cx - 30, cy + 22)], 220)
    c.poly("core", [(cx - 20, cy - 12), (cx + 20, cy - 12), (cx + 20, cy + 12), (cx - 20, cy + 12)], 255)
    for i in range(10):
        a = 2 * math.pi * i / 10 + R.normal(0, 0.15)
        _crack(c, cx + math.cos(a) * 34, cy + math.sin(a) * 34, a, R.uniform(70, 100), 3.0, R, "gold", val=255)
    c.circle("mid", cx, cy, 96, 3, 200)
    for i in range(16):
        a = math.radians(i * 22.5)
        x, y = cx + math.cos(a) * 108, cy + math.sin(a) * 108
        c.line("core", [(x - 4, y - 5), (x, y + 5), (x + 4, y - 5)], 1.6)
    _sparks(c, R, cx, cy, 40, 120, 60)
    g = c.render(PAL3["mjolnir"], bloom=1.15, core_white=0.7)
    rr, _ = _radial(S, cx, cy)
    return _dark_under(g, np.clip(1 - rr / 100, 0, 1) * 0.3)


def bastion():
    """성채 방벽: 앞쪽 성벽 문양 (총안) + 뒤쪽 금빛 방패 결계 반원 (위 = 앞)"""
    c = Canvas(S, S); R = _rng(314); cx = S / 2
    y0 = S * 0.42
    # 성벽 띠 (총안)
    c.poly("mid", [(20, y0), (S - 20, y0), (S - 20, y0 + 30), (20, y0 + 30)], 210)
    for i in range(7):
        x = 26 + i * 34
        c.poly("mid", [(x, y0 - 18), (x + 20, y0 - 18), (x + 20, y0), (x, y0)], 210)
    c.line("core", [(24, y0 + 15), (S - 24, y0 + 15)], 3)
    # 방패 결계
    _arc(c, "gold", cx, S * 0.98, 120, 128, -180, 0, 230, 80, taper=False)
    _arc(c, "mid", cx, S * 0.98, 70, 76, -180, 0, 180, 80, taper=False)
    c.poly("gold", [(cx - 26, S * 0.72), (cx + 26, S * 0.72), (cx + 22, S * 0.84), (cx, S * 0.92), (cx - 22, S * 0.84)], 240)
    c.disc("core", cx, S * 0.8, 6)
    _sparks(c, R, cx, S * 0.6, 20, 120, 50)
    return c.render(PAL3["bastion"], bloom=1.05, core_white=0.6)


FX = {f"fx3_{k}": f for k, f in (("moon", moon), ("magma", magma), ("crystal", crystal), ("tempest", tempest), ("holy", holy),
                                   ("vampire", vampire), ("sunbow", sunbow), ("viper", viper), ("starbow", starbow), ("shuriken", shuriken),
                                   ("frostaxe", frostaxe), ("twinaxe", twinaxe), ("mjolnir", mjolnir), ("bastion", bastion))}


def export(pack):
    from telegraphs import flat_model
    for name, fn in FX.items():
        ref = pack.texture(f"tele/{name}", fn())
        pack.item_model(f"tele/{name}", flat_model(ref))


def preview(path):
    cell = 200
    cols = 7
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
