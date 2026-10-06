"""직업 전용 전설 무기 14종 — 128px 픽셀 판타지 (weapons_legend2 와 같은 붓 · 마무리)

 전사(검)    moon 월광의 카타나 · magma 용암의 플람베르주 · crystal 수정 결정검 · tempest 폭풍의 바스타드소드
             holy 성흔의 클레이모어 · vampire 흡혈귀의 레이피어
 궁수(원거리) sunbow 태양신의 장궁 · viper 독사의 석궁 · starbow 별빛 연발궁 · shuriken 그림자 표창
 수호자(도끼) frostaxe 서리 거인의 도끼 · twinaxe 투척 쌍도끼 · mjolnir 천둥 망치 · bastion 성채 방패도끼
 무기 축: 왼쪽 아래(손잡이) → 오른쪽 위(끝)
"""
import math

import numpy as np
from PIL import Image

from icon2d import *
from icon2d import S, XX, YY, U, V
from weapons_legend2 import (M, ICE_B, ICE_D, SILVER, GOLD2, DGOLD, NAVY, STORM, DARKM, GHOST, BONE2, PEARL, TWIST, TOXIC, SUN, CRIM,
                             STONE2, LAVA, BRONZE2, LAPIS, SCALE_G, SCALE_D, OAK, IRON, EYEW, curve, stroke, cdisc, ring_mask,
                             filigree, Aura, swirls, finish)

MOONSTEEL = M((190, 205, 235), spec=1.0, shin=70, env=0.55, grain="brushed", sky=(250, 252, 255), ground=(40, 50, 90))
INDIGO = M((44, 40, 96), spec=0.4, shin=20, env=0.2, grain="cloth", rough=0.15)
BASALT = M((50, 40, 40), spec=0.5, shin=25, env=0.25, grain="stone", rough=0.2, sky=(140, 110, 100), ground=(10, 6, 6))
MAGMA = M((255, 110, 20), spec=0.6, shin=30, env=0.3, rough=0.04, glow=(255, 100, 20), sky=(255, 220, 120), ground=(120, 20, 0))
AMETH = M((185, 110, 255), spec=1.0, shin=90, env=0.45, rough=0.02, glow=(190, 120, 255), sky=(250, 230, 255), ground=(60, 10, 100))
AMETH_D = M((110, 50, 180), spec=1.0, shin=80, env=0.4, rough=0.02, glow=(140, 70, 220), sky=(220, 180, 255), ground=(30, 6, 60))
STEELB = M((150, 170, 200), spec=1.0, shin=60, env=0.5, grain="brushed", sky=(230, 240, 255), ground=(20, 30, 60))
WHITEG = M((248, 246, 236), spec=1.0, shin=60, env=0.55, rough=0.02, sky=(255, 255, 255), ground=(160, 140, 90))
BLOODS = M((150, 14, 26), spec=1.0, shin=70, env=0.45, rough=0.02, glow=(200, 20, 40), sky=(255, 140, 150), ground=(30, 0, 4))
BLACKS = M((34, 30, 38), spec=0.9, shin=55, env=0.45, grain="brushed", sky=(140, 130, 150), ground=(6, 4, 8))
VIPER = M((70, 150, 50), spec=0.9, shin=50, env=0.35, rough=0.04, sky=(200, 255, 170), ground=(10, 40, 10))
STARM = M((120, 110, 220), spec=1.0, shin=70, env=0.5, rough=0.03, glow=(150, 140, 255), sky=(230, 225, 255), ground=(20, 14, 70))
SHADOW = M((60, 46, 80), spec=1.0, shin=60, env=0.5, grain="brushed", sky=(170, 150, 210), ground=(8, 4, 14))
FROSTI = M((170, 225, 255), spec=1.0, shin=80, env=0.55, rough=0.02, glow=(140, 210, 255), sky=(245, 252, 255), ground=(40, 90, 170))
RUNEST = M((110, 116, 130), spec=0.6, shin=30, env=0.35, grain="stone", rough=0.15, sky=(210, 220, 240), ground=(20, 22, 30))
BLUEL = M((40, 60, 120), spec=0.2, shin=10, grain="leather", rough=0.2)
REDL = M((120, 30, 30), spec=0.2, shin=10, grain="leather", rough=0.2)


def _tip_glow(c, pts, col, w=2.2, k=1.2):
    c.emissive(line_dens(pts, w), col, k)


# ═════════════════════════════════════════════ 전사 — 검
def moon():
    """월광의 카타나 — 남색 끈 손잡이 + 초승달 츠바 + 가늘게 휜 달빛 날 + 은빛 물결 무늬"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(31)
    c.part(profile([(8, 9), (150, 10)]), INDIGO, 1, bevel=6, ang=AX_ANG)
    for u in range(16, 150, 14):
        c.part(stroke([(u, -10), (u + 7, 0), (u, 10)], 3.5), MOONSTEEL, 2 + u, bevel=2)
    c.part(disc(8, 0, 11), SILVER, 3, bevel=6)
    # 초승달 츠바
    tb = smooth_poly([(150, -34), (168, -30), (174, 0), (168, 30), (150, 34), (160, 0)], 8)
    c.part(tb, GOLD2, 4, bevel=6)
    c.part(disc(162, 0, 8), SAPPHIRE, 5, bevel=4)
    # 휜 날 (위로 살짝 휨)
    bend = lambda u: -0.00018 * (u - 170) ** 2
    up = [(u, bend(u) - 13 + (u - 170) / 380 * 9) for u in range(170, 541, 10)]
    lo = [(u, bend(u) + 9 - (u - 170) / 380 * 9) for u in range(540, 169, -10)]
    pts = up + [(552, bend(552) - 2)] + lo
    c.part(poly(pts), MOONSTEEL, 10, shape="blade", height=1.0)
    # 하몬 (물결 무늬) · 등날 빛
    hamon = [(u, bend(u) + 3 + 3 * math.sin(u * 0.12)) for u in range(180, 530, 6)]
    c.emissive(line_dens(hamon, 1.6), (200, 225, 255), 0.7)
    _tip_glow(c, [(u, bend(u) - 11 + (u - 170) / 380 * 9) for u in range(190, 541, 10)], (220, 235, 255), 1.6, 1.0)
    # 오라: 달빛 + 꽃잎
    for k in range(6):
        u = r.uniform(220, 520)
        au.wisp([(u, -20), (u - 30, -60), (u - 80, -70), (u - 110, -50)], r.uniform(8, 13), (120, 170, 255), (230, 240, 255), 0.85)
    for k in range(10):
        u, v = r.uniform(160, 540), r.uniform(-90, 60)
        au.wisp([(u, v), (u + 6, v + 4)], 6, (210, 220, 255), (255, 255, 255), 0.9)
    au.glow(c.sil, (130, 170, 255), 10, 0.5)
    return c, au, dict(outline_col=(10, 14, 40), sparkle=(235, 245, 255), n_sparkle=8)


def magma():
    """용암의 플람베르주 — 현무암 물결 날 + 갈라진 틈의 용암 + 뿔 가드 + 불꽃"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(32)
    c.part(profile([(8, 10), (130, 11)]), REDL, 1, bevel=6, ang=AX_ANG)
    for u in range(16, 130, 14):
        c.part(profile([(u, 12), (u + 5, 12)]), DGOLD, 2 + u, bevel=3)
    c.part(disc(8, 0, 13), BASALT, 3, bevel=7)
    c.part(disc(8, 0, 7), MAGMA, 4, bevel=4)
    # 뿔 가드
    for s_ in (1, -1):
        c.part(smooth_poly([(130, s_ * 8), (150, s_ * 40), (126, s_ * 64), (146, s_ * 52), (164, s_ * 16)], 6), BASALT, 5 + s_, bevel=6)
    c.part(disc(150, 0, 14), BASALT, 7, bevel=6)
    c.part(disc(150, 0, 8), MAGMA, 8, bevel=4)
    # 물결 날 (플람베르주)
    up, lo = [], []
    for u in range(164, 531, 6):
        w = 22 - (u - 164) / 366 * 14 + 4 * math.sin(u * 0.09)
        up.append((u, -w)); lo.append((u, w))
    c.part(poly(up + [(556, 0)] + lo[::-1]), BASALT, 10, shape="blade", height=0.9)
    # 용암 틈
    crack = [(170, 0)]
    for k in range(18):
        crack.append((crack[-1][0] + 20, r.uniform(-5, 5)))
    c.emissive(line_dens(crack, 4.0), (255, 120, 20), 1.6)
    for k in range(8):
        u0 = r.uniform(190, 500); s_ = 1 if k % 2 else -1
        c.emissive(line_dens([(u0, 0), (u0 + r.uniform(6, 14), s_ * r.uniform(8, 14))], 2.2), (255, 160, 40), 1.2)
    # 오라: 불꽃
    swirls(au, r, (255, 90, 20), 9, 180, 520, 70, (10, 18))
    au.glow(c.sil, (255, 110, 30), 12, 0.6)
    return c, au, dict(outline_col=(30, 8, 2), sparkle=(255, 220, 140))


def crystal():
    """수정 결정검 — 자수정 결정이 뭉쳐 자란 날 + 은 손잡이 + 결정 가드"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(33)
    c.part(profile([(8, 9), (140, 10)]), SILVER, 1, bevel=6, ang=AX_ANG)
    for u in range(20, 140, 18):
        c.part(stroke([(u, -10), (u + 9, 10)], 4), AMETH_D, 2 + u, bevel=2)
    c.part(disc(8, 0, 12), AMETH, 3, bevel=6)
    # 결정 가드 (양쪽 결정 세 개씩)
    for s_ in (1, -1):
        for k, (a, L) in enumerate(((60, 52), (90, 44), (120, 38))):
            ang = math.radians(a) * s_
            du, dv = math.sin(ang) * 0.4, math.cos(ang)
            base_u = 150
            tip = (base_u + du * L * 0.9 - 10 * k, s_ * (14 + L * abs(dv)))
            c.part(poly([(base_u - 8, s_ * 8), tip, (base_u + 8, s_ * 8)]), AMETH if k % 2 == 0 else AMETH_D, 4 + k + (s_ + 1) * 5, shape="blade", height=1.0)
    c.part(disc(150, 0, 14), SILVER, 20, bevel=6)
    # 날: 큰 중심 결정 + 옆으로 자란 작은 결정들
    c.part(poly([(160, -18), (470, -14), (556, 0), (470, 14), (160, 18)]), AMETH, 30, shape="blade", height=1.1)
    for k in range(9):
        u = 200 + k * 36
        s_ = 1 if k % 2 else -1
        L = r.uniform(26, 44)
        c.part(poly([(u - 10, s_ * 10), (u + 18, s_ * (10 + L)), (u + 12, s_ * 10)]), AMETH_D if k % 3 else AMETH, 40 + k, shape="blade", height=1.0)
    c.emissive(line_dens([(170, 0), (540, 0)], 2.0), (240, 210, 255), 1.0)
    # 오라: 결정 빛 + 반짝임
    for k in range(7):
        u = r.uniform(180, 520); s_ = 1 if k % 2 else -1
        au.wisp([(u, s_ * 20), (u + 20, s_ * 60), (u + 10, s_ * 90)], r.uniform(8, 12), (170, 100, 255), (240, 220, 255), 0.8)
    au.glow(c.sil, (170, 110, 255), 12, 0.6)
    return c, au, dict(outline_col=(24, 6, 40), sparkle=(250, 235, 255), n_sparkle=10)


def tempest():
    """폭풍의 바스타드소드 — 넓은 강철 날에 푸른 번개 홈 + 날개 가드 + 바람 소용돌이"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(34)
    c.part(profile([(8, 9), (150, 10)]), BLUEL, 1, bevel=6, ang=AX_ANG)
    for u in range(20, 150, 16):
        c.part(stroke([(u, -10), (u + 8, 10)], 4), SILVER, 2 + u, bevel=2)
    c.part(disc(8, 0, 14), SILVER, 3, bevel=7)
    c.part(disc(8, 0, 8), SAPPHIRE, 4, bevel=4)
    # 날개 가드
    for s_ in (1, -1):
        for k in range(3):
            c.part(smooth_poly([(150 - k * 6, s_ * 10), (136 - k * 14, s_ * (44 + k * 12)), (152 - k * 10, s_ * (50 + k * 12)), (166, s_ * 14)], 6),
                   SILVER if k % 2 == 0 else STEELB, 5 + k + (s_ + 1) * 4, bevel=5)
    c.part(disc(160, 0, 15), GOLD2, 20, bevel=6)
    c.part(disc(160, 0, 9), SAPPHIRE, 21, bevel=4)
    # 날
    c.part(profile([(172, 24), (240, 26), (460, 22), (520, 14), (556, 0.5)]), STEELB, 30, shape="blade", height=0.9, ang=AX_ANG)
    c.part(profile([(180, 7), (470, 5), (500, 1)]), NAVY, 31, bevel=3)
    bolt = [(185, 0), (230, 4), (270, -4), (320, 5), (370, -4), (420, 4), (470, -2)]
    c.emissive(line_dens(bolt, 3.0), (130, 200, 255), 1.4)
    # 오라: 바람 회오리
    for k in range(8):
        u = r.uniform(180, 540)
        au.wisp([(u, 26), (u + 30, 60), (u - 10, 90), (u - 50, 70), (u - 30, 40)], r.uniform(8, 13), (120, 180, 255), (220, 240, 255), 0.75)
    au.glow(c.sil, (100, 160, 255), 10, 0.5)
    return c, au, dict(outline_col=(8, 14, 40), sparkle=(225, 240, 255))


def holy():
    """성흔의 클레이모어 — 흰 금 대검 + 십자 가드 + 날 위 빛나는 성흔 + 후광"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(35)
    c.part(profile([(6, 10), (140, 11)]), M((200, 180, 140), spec=0.2, shin=10, grain="leather", rough=0.2), 1, bevel=6, ang=AX_ANG)
    for u in range(14, 140, 14):
        c.part(profile([(u, 12), (u + 5, 12)]), GOLD2, 2 + u, bevel=3)
    c.part(disc(6, 0, 15), GOLD2, 3, bevel=7)
    c.part(disc(6, 0, 8), TOPAZ, 4, bevel=4)
    # 십자 가드 (끝이 넓게 퍼짐)
    for s_ in (1, -1):
        c.part(poly([(138, s_ * 8), (130, s_ * 58), (154, s_ * 70), (166, s_ * 58), (160, s_ * 8)]), GOLD2, 5 + s_, bevel=7)
        c.part(disc(150, s_ * 60, 6), RUBY, 8 + s_, bevel=3)
    c.part(disc(152, 0, 18), GOLD2, 10, bevel=7)
    c.part(disc(152, 0, 10), RUBY, 11, bevel=5)
    # 넓은 날
    c.part(profile([(166, 30), (420, 28), (500, 20), (556, 0.5)]), WHITEG, 20, shape="blade", height=0.8, ang=AX_ANG)
    c.part(profile([(176, 8), (460, 6), (500, 1)]), GOLD2, 21, bevel=3)
    # 성흔 (날 위 십자 세 개)
    for u in (240, 330, 420):
        c.emissive(line_dens([(u - 16, 0), (u + 16, 0)], 4), (255, 230, 120), 1.4)
        c.emissive(line_dens([(u, -12), (u, 12)], 4), (255, 230, 120), 1.4)
    # 오라: 후광 빛살
    for k in range(11):
        a = -90 + k * 18
        au.wisp([(360, 0), (360 + 150 * math.cos(math.radians(a)), 150 * math.sin(math.radians(a)))], 12, (255, 220, 110), alpha=0.32)
    au.glow(c.sil, (255, 225, 130), 14, 0.6)
    return c, au, dict(outline_col=(40, 28, 6), sparkle=(255, 255, 225), n_sparkle=10)


def vampire():
    """흡혈귀의 레이피어 — 검은 장미 바구니 가드 + 가늘고 긴 핏빛 날 + 박쥐 날개"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(36)
    c.part(profile([(10, 8), (130, 9)]), BLACKS, 1, bevel=6, ang=AX_ANG)
    for u in range(20, 130, 12):
        c.part(stroke([(u, -9), (u + 6, 9)], 3), BLOODS, 2 + u, bevel=2)
    c.part(disc(10, 0, 12), BLACKS, 3, bevel=6)
    c.part(disc(10, 0, 6), RUBY, 4, bevel=3)
    # 바구니 가드 (휘감긴 고리)
    for k, (a, b) in enumerate(((-50, 20), (-30, 40), (30, -40), (50, -20))):
        c.part(stroke(curve([(130, 0), (150, a), (190, b * 0.6), (200, 0)], 10), 6, 4), BLACKS, 10 + k, bevel=3)
    c.part(ring_mask(*P(170, 0), 22, 30), BLACKS, 15, bevel=5)
    # 장미
    c.part(disc(170, 0, 16), BLOODS, 16, bevel=7)
    for k in range(5):
        a = math.radians(k * 72)
        c.ink(line_dens([(170, 0), (170 + math.cos(a) * 12, math.sin(a) * 12)], 1.6), (60, 0, 10), 0.6)
    # 박쥐 날개 (가드 양옆)
    for s_ in (1, -1):
        wing = smooth_poly([(180, s_ * 20), (200, s_ * 70), (226, s_ * 58), (242, s_ * 86), (262, s_ * 60), (240, s_ * 26)], 8)
        c.part(wing, BLACKS, 20 + s_, shape="flat", bevel=8, alpha=0.95)
    # 가는 날
    c.part(profile([(200, 8), (500, 5), (560, 0.5)]), BLOODS, 30, shape="blade", height=1.0, ang=AX_ANG)
    c.emissive(line_dens([(205, 0), (550, 0)], 1.6), (255, 80, 90), 1.2)
    # 오라: 핏방울 · 박쥐 그림자
    swirls(au, r, (190, 20, 40), 7, 200, 540, 60, (7, 12))
    for k in range(6):
        u, v = r.uniform(240, 540), r.uniform(-80, 80)
        au.wisp([(u, v), (u + 8, v + 10)], 8, (200, 20, 30), (255, 90, 100), 0.9)
    au.glow(c.sil, (200, 30, 50), 10, 0.5)
    return c, au, dict(outline_col=(20, 2, 6), sparkle=(255, 200, 200))


# ═════════════════════════════════════════════ 궁수 — 활 · 원거리
def sunbow():
    """태양신의 장궁 — 금 활대 끝에 햇살 장식 + 가운데 태양 원반 + 불꽃 시위"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(41)
    bend = lambda u: -64 * math.sin(math.pi * (u - 40) / 460)
    limb = [(u, bend(u)) for u in range(40, 501, 20)]
    c.emissive(line_dens([(40, bend(40) + 2), (500, bend(500) + 2)], 2.4), (255, 200, 90), 1.0)
    up, lo = limb[:12], limb[11:]
    c.part(stroke(up[::-1], 24, 9), DGOLD, 2, bevel=6)
    c.part(stroke(lo, 24, 9), DGOLD, 3, bevel=6)
    c.part(stroke([(u, v - 3) for u, v in up[::-1]], 13, 5), GOLD2, 4, bevel=5)
    c.part(stroke([(u, v - 3) for u, v in lo], 13, 5), GOLD2, 5, bevel=5)
    # 끝: 햇살 장식
    for u in (40, 500):
        v = bend(u)
        for k in range(7):
            a = math.radians(k * 51)
            c.part(poly([(u + math.cos(a - 0.25) * 8, v + math.sin(a - 0.25) * 8), (u + math.cos(a) * 24, v + math.sin(a) * 24),
                         (u + math.cos(a + 0.25) * 8, v + math.sin(a + 0.25) * 8)]), SUN, 10 + k + u, shape="blade")
        c.part(disc(u, v, 9), GOLD2, 30 + u, bevel=4)
        c.part(disc(u, v, 5), TOPAZ, 31 + u, bevel=3)
    # 손잡이 태양 원반
    mid = 270
    vm = bend(mid)
    c.part(stroke([(mid - 34, vm), (mid + 34, vm)], 26, 26), CRIM, 50, bevel=8)
    c.part(disc(mid, vm - 6, 30), SUN, 51, bevel=10)
    c.part(disc(mid, vm - 6, 20), GOLD2, 52, bevel=8)
    c.part(disc(mid, vm - 6, 11), TOPAZ, 53, bevel=6)
    for k in range(12):
        a = math.radians(k * 30)
        x0, y0 = mid + math.cos(a) * 30, vm - 6 + math.sin(a) * 30
        c.part(poly([(x0 - math.sin(a) * 5, y0 + math.cos(a) * 5), (mid + math.cos(a) * 44, vm - 6 + math.sin(a) * 44), (x0 + math.sin(a) * 5, y0 - math.cos(a) * 5)]),
               SUN, 60 + k, shape="blade", height=0.8)
    # 오라: 햇빛 불꽃
    swirls(au, r, (255, 150, 30), 8, 60, 480, 70, (9, 16))
    au.glow(c.sil, (255, 170, 50), 12, 0.6)
    return c, au, dict(outline_col=(40, 20, 2), sparkle=(255, 250, 200), n_sparkle=8)


def viper():
    """독사의 석궁 — 뱀 비늘 개머리 + 뱀 머리 활대 + 독이 맺힌 볼트"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(42)
    # 개머리 (축 따라)
    c.part(profile([(20, 18), (120, 16), (360, 12), (420, 10)]), SCALE_D, 1, bevel=8, ang=AX_ANG)
    for u in range(40, 400, 18):
        c.part(stroke([(u, -12), (u + 8, 0), (u, 12)], 3), SCALE_G, 2 + u, bevel=2)
    c.part(profile([(20, 20), (40, 20)]), GOLD2, 3, bevel=5)
    # 방아쇠
    c.part(poly([(170, 12), (184, 40), (196, 14)]), DARKM, 4, bevel=3)
    # 활대 (가로, 끝이 뱀 머리)
    limb_u = 360
    for s_ in (1, -1):
        pts = curve([(limb_u, 0), (limb_u - 10, s_ * 50), (limb_u - 40, s_ * 100), (limb_u - 76, s_ * 126)], 10)
        c.part(stroke(pts, 20, 12), VIPER, 10 + s_, bevel=6)
        hu, hv = pts[-1]
        c.part(smooth_poly([(hu + 10, hv - s_ * 4), (hu - 14, hv + s_ * 10), (hu - 30, hv + s_ * 2), (hu - 20, hv - s_ * 14)], 6), SCALE_G, 14 + s_, bevel=6)
        c.emissive(disc(hu - 14, hv - s_ * 4, 3).astype(np.float32), (255, 230, 40), 1.0)
        c.part(poly([(hu - 26, hv + s_ * 4), (hu - 40, hv + s_ * 16), (hu - 30, hv - s_ * 2)]), BONE2, 18 + s_, shape="blade")
        # 시위
        c.emissive(line_dens([(hu - 6, hv), (250, 0)], 1.6), (220, 230, 210), 0.5)
    # 독 볼트
    c.part(profile([(250, 4), (470, 4)]), DARKM, 30, bevel=3, ang=AX_ANG)
    c.part(poly([(466, -12), (510, 0), (466, 12), (476, 0)]), M((90, 230, 60), spec=1.0, shin=60, env=0.4, glow=(110, 255, 70)), 31, shape="blade")
    for s_ in (1, -1):
        c.part(poly([(250, 0), (232, s_ * 14), (270, s_ * 4)]), SCALE_G, 32 + s_, shape="flat")
    c.emissive(disc(512, 6, 5).astype(np.float32), (120, 255, 80), 1.2)
    # 오라: 독 안개
    swirls(au, r, (80, 210, 50), 8, 120, 480, 64, (9, 15))
    au.glow(c.sil, (90, 220, 60), 10, 0.45)
    return c, au, dict(outline_col=(6, 22, 6), sparkle=(220, 255, 170))


def starbow():
    """별빛 연발궁 — 밤하늘 남보라 활대 + 별 장식 + 활대를 따라 뜬 작은 별들"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(43)
    bend = lambda u: -54 * math.sin(math.pi * (u - 50) / 440)
    limb = [(u, bend(u)) for u in range(50, 491, 20)]
    c.emissive(line_dens([(50, bend(50) + 2), (490, bend(490) + 2)], 2.0), (200, 190, 255), 0.9)
    up, lo = limb[:12], limb[11:]
    c.part(stroke(up[::-1], 22, 8), STARM, 2, bevel=6)
    c.part(stroke(lo, 22, 8), STARM, 3, bevel=6)
    c.part(stroke([(u, v - 3) for u, v in up[::-1]], 9, 3), SILVER, 4, bevel=4)
    c.part(stroke([(u, v - 3) for u, v in lo], 9, 3), SILVER, 5, bevel=4)

    def star(u, v, R, mat, seed):
        pts = []
        for k in range(10):
            a = math.radians(k * 36 - 90)
            rr = R if k % 2 == 0 else R * 0.45
            pts.append((u + math.cos(a) * rr, v + math.sin(a) * rr))
        c.part(poly(pts), mat, seed, shape="blade", height=0.9)
    for u in (50, 490):
        star(u, bend(u), 22, GOLD2, 10 + u)
    mid = 270
    vm = bend(mid)
    c.part(stroke([(mid - 32, vm), (mid + 32, vm)], 24, 24), INDIGO, 30, bevel=8)
    star(mid, vm, 30, GOLD2, 31)
    c.part(disc(mid, vm, 9), SAPPHIRE, 32, bevel=4)
    # 활대 위 작은 별
    for k, u in enumerate((120, 180, 360, 420)):
        star(u, bend(u) - 22, 9, M((255, 245, 200), spec=1.0, shin=60, glow=(255, 240, 180)), 40 + k)
    # 오라: 은하수 · 별가루
    for k in range(5):
        u = r.uniform(80, 460)
        au.wisp([(u, -30), (u + 40, -80), (u + 90, -100)], r.uniform(10, 16), (130, 110, 255), (230, 220, 255), 0.6)
    for k in range(14):
        u, v = r.uniform(40, 520), r.uniform(-120, 30)
        au.wisp([(u, v), (u + 4, v + 4)], 5, (255, 250, 220), (255, 255, 255), 0.95)
    au.glow(c.sil, (150, 130, 255), 12, 0.55)
    return c, au, dict(outline_col=(14, 8, 40), sparkle=(255, 250, 230), n_sparkle=12)


def shuriken():
    """그림자 표창 — 검은 강철 네 갈래 큰 표창 + 보라 그림자 결 + 가운데 고리"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(44)
    cx, cy = 256, 256
    for k in range(4):
        a = math.radians(k * 90 + 20)
        tip = (cx + math.cos(a) * 200, cy + math.sin(a) * 200)
        l_ = (cx + math.cos(a + 0.62) * 70, cy + math.sin(a + 0.62) * 70)
        r_ = (cx + math.cos(a - 0.38) * 46, cy + math.sin(a - 0.38) * 46)
        hook = (cx + math.cos(a + 0.3) * 120, cy + math.sin(a + 0.3) * 120)
        c.part(poly([r_, tip, hook, l_], local=False), SHADOW, 10 + k, shape="blade", height=0.9)
        c.emissive(line_dens([(cx + math.cos(a) * 60, cy + math.sin(a) * 60), (tip[0] * 0.9 + cx * 0.1, tip[1] * 0.9 + cy * 0.1)], 2.0, local=False), (190, 120, 255), 1.0)
    c.part(cdisc(cx, cy, 52), BLACKS, 1, bevel=12)
    c.part(ring_mask(cx, cy, 30, 44), SILVER, 2, bevel=5)
    c.part(cdisc(cx, cy, 18), AMETHYST, 3, bevel=6)
    # 오라: 돌며 번지는 그림자
    for k in range(9):
        a0 = math.radians(k * 40 + r.uniform(-8, 8))
        pts = [(cx + math.cos(a0 + t * 0.16) * (150 + t * 14), cy + math.sin(a0 + t * 0.16) * (150 + t * 14)) for t in range(6)]
        au.wisp(pts, r.uniform(12, 18), (110, 50, 170), (210, 170, 255), 0.85, local=False)
    au.glow(c.sil, (130, 60, 200), 12, 0.55)
    return c, au, dict(outline_col=(10, 4, 20), sparkle=(235, 215, 255))


# ═════════════════════════════════════════════ 수호자 — 도끼 · 둔기
def frostaxe():
    """서리 거인의 도끼 — 룬 새긴 돌 자루 + 얼음 결정 거대 도끼날 + 고드름"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(51)
    c.part(profile([(6, 11), (440, 12)]), RUNEST, 1, bevel=7, ang=AX_ANG)
    for u in (60, 150, 240, 330):
        c.part(profile([(u - 7, 15), (u + 7, 15)]), SILVER, 2 + u, bevel=4)
        c.emissive(line_dens([(u + 20, -6), (u + 30, 6), (u + 40, -6)], 2.0), (140, 210, 255), 1.0)
    c.part(disc(6, 0, 14), SILVER, 3, bevel=6)
    c.part(disc(6, 0, 7), SAPPHIRE, 4, bevel=4)
    # 도끼날 (한쪽으로 크게 — 결정 각)
    blade = poly([(372, -14), (360, -50), (316, -110), (300, -160), (340, -186), (392, -196), (440, -180), (468, -134), (448, -60), (440, -14)])
    c.part(blade, FROSTI, 10, shape="blade", height=0.85)
    c.part(poly([(384, -30), (350, -110), (380, -160), (430, -160), (440, -70)]), ICE_D, 11, shape="flat", bevel=10, alpha=0.55)
    for k, (u, v) in enumerate(((330, -150), (366, -176), (410, -182), (448, -150))):
        c.part(poly([(u - 10, v + 14), (u - 4, v - 26), (u + 12, v + 10)]), ICE_B, 14 + k, shape="blade")
    _tip_glow(c, [(316, -110), (300, -160), (340, -186), (392, -196), (440, -180), (468, -134)], (210, 240, 255), 2.4, 1.2)
    # 반대쪽 가시
    c.part(poly([(400, 12), (440, 60), (460, 12)]), FROSTI, 12, shape="blade")
    # 끝 창날 + 고드름
    c.part(poly([(440, -10), (500, 0), (440, 10)]), FROSTI, 13, shape="blade")
    for k, u in enumerate((380, 410, 440)):
        c.part(poly([(u - 6, 12), (u + 6, 12), (u, 40 + k * 6)]), ICE_B, 20 + k, shape="blade")
    c.part(profile([(370, 16), (476, 16)]), SILVER, 30, bevel=5)
    # 오라: 눈보라
    swirls(au, r, (110, 190, 255), 8, 200, 520, 70, (9, 15))
    for k in range(10):
        u, v = r.uniform(300, 540), r.uniform(-200, 40)
        au.wisp([(u, v), (u + 5, v + 5)], 5, (230, 245, 255), (255, 255, 255), 0.95)
    au.glow(c.sil, (120, 200, 255), 12, 0.55)
    return c, au, dict(outline_col=(8, 20, 46), sparkle=(235, 250, 255), n_sparkle=8)


def twinaxe():
    """투척 쌍도끼 — 교차한 손도끼 두 자루 (붉은 끈 · 강철 반달날 · 금 박음)"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(52)

    def hatchet(x0, y0, x1, y1, flip, seed):
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
        nx, ny = -uy * flip, ux * flip
        Q = lambda u, v: (x0 + ux * u + nx * v, y0 + uy * u + ny * v)
        c.part(stroke([Q(0, 0), Q(L, 0)], 16, 18, local=False), OAK, seed, bevel=6)
        for k in range(5):
            u = 30 + k * 22
            c.part(stroke([Q(u, -9), Q(u + 10, 9)], 4, 4, local=False), REDL, seed + 1 + k, bevel=2)
        c.part(cdisc(*Q(0, 0), 11), IRON, seed + 10, bevel=5)
        bl = [Q(L - 52, -10), Q(L - 56, -36), Q(L - 92, -74), Q(L - 74, -104), Q(L - 30, -112), Q(L + 14, -96), Q(L + 18, -70), Q(L - 4, -36), Q(L - 10, -10)]
        c.part(smooth_poly(bl, 8, local=False), SILVER, seed + 20, shape="blade", height=0.85)
        c.emissive(line_dens([Q(L - 88, -76), Q(L - 72, -100), Q(L - 30, -108), Q(L + 12, -94), Q(L + 16, -72)], 2.2, local=False), (255, 200, 190), 0.9)
        c.part(stroke([Q(L - 80, 0), Q(L + 8, 0)], 22, 22, local=False), DARKM, seed + 30, bevel=6)
        c.part(cdisc(*Q(L - 36, 0), 6), GOLD2, seed + 31, bevel=3)
        c.part(poly([Q(L - 40, 10), Q(L - 20, 40), Q(L - 10, 10)], local=False), SILVER, seed + 32, shape="blade")
    hatchet(110, 440, 380, 120, 1, 100)
    hatchet(400, 440, 130, 120, -1, 200)
    # 오라: 휘도는 궤적
    for k in range(6):
        a0 = math.radians(r.uniform(0, 360))
        pts = [(256 + math.cos(a0 + t * 0.25) * (170 + t * 8), 256 + math.sin(a0 + t * 0.25) * (170 + t * 8)) for t in range(6)]
        au.wisp(pts, r.uniform(10, 16), (230, 70, 50), (255, 200, 170), 0.7, local=False)
    au.glow(c.sil, (230, 80, 60), 10, 0.45)
    return c, au, dict(outline_col=(26, 10, 6), sparkle=(255, 230, 210))


def mjolnir():
    """천둥 망치 — 짧은 가죽 자루 + 룬 새긴 큰 쇠 망치 머리 + 번개"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(53)
    c.part(profile([(40, 11), (300, 12)]), M((100, 60, 36), spec=0.2, shin=10, grain="leather", rough=0.25), 1, bevel=6, ang=AX_ANG)
    for u in range(54, 300, 16):
        c.part(stroke([(u, -12), (u + 8, 12)], 4), M((70, 40, 24), spec=0.1, shin=8, grain="leather"), 2 + u, bevel=2)
    c.part(disc(36, 0, 13), SILVER, 3, bevel=6)
    c.part(stroke([(20, 0), (-10, 30), (10, 50)], 5), M((80, 50, 30), spec=0.1, shin=8, grain="leather"), 4, bevel=2)
    c.part(profile([(296, 18), (320, 18)]), SILVER, 5, bevel=6)
    # 망치 머리 (축에 가로로 놓인 큰 직육면체)
    head = poly([(320, -90), (470, -90), (480, -80), (480, 80), (470, 90), (320, 90), (310, 80), (310, -80)])
    c.part(head, RUNEST, 10, bevel=18)
    c.part(poly([(320, -90), (470, -90), (480, -80), (310, -80)]), SILVER, 11, bevel=6)
    c.part(poly([(310, 80), (480, 80), (470, 90), (320, 90)]), SILVER, 12, bevel=6)
    for v0 in (-60, 60):
        c.part(profile([(318, 0), (472, 0)]) & (np.abs(V - v0) < 8), SILVER, 13 + v0, bevel=4)
    # 룬
    rune = [(360, -30), (380, 0), (360, 30)], [(400, -30), (400, 30)], [(420, -30), (440, -10), (420, 10), (440, 30)]
    for pts in rune:
        c.emissive(line_dens(pts, 3.0), (130, 200, 255), 1.4)
    # 오라: 번개
    for k in range(7):
        u0, v0 = r.uniform(300, 500), r.choice([-1, 1]) * r.uniform(90, 110)
        pts = [(u0, v0)]
        for j in range(5):
            pts.append((pts[-1][0] + r.uniform(-20, 20), pts[-1][1] + np.sign(v0) * r.uniform(8, 16)))
        au.wisp(pts, 4, (140, 200, 255), (240, 250, 255), 1.0)
    swirls(au, r, (70, 120, 255), 5, 320, 480, 70, (8, 14))
    au.glow(c.sil, (100, 160, 255), 10, 0.45)
    return c, au, dict(outline_col=(10, 14, 30), sparkle=(230, 245, 255))


def bastion():
    """성채 방패도끼 — 성벽 모양 방패 (총안 · 사자 문장) 를 단 무거운 도끼"""
    c, au, r = Canvas(), Aura(), np.random.default_rng(54)
    c.part(profile([(6, 11), (430, 12)]), OAK, 1, bevel=7, ang=AX_ANG)
    for u in (50, 120, 190):
        c.part(profile([(u - 6, 14), (u + 6, 14)]), IRON, 2 + u, bevel=4)
    c.part(disc(6, 0, 14), GOLD2, 3, bevel=6)
    # 도끼날 (앞쪽)
    blade = poly([(404, 14), (400, 44), (366, 92), (380, 130), (432, 146), (476, 128), (490, 90), (464, 48), (452, 14)])
    c.part(blade, SILVER, 10, shape="blade", height=0.85)
    _tip_glow(c, [(366, 92), (380, 130), (432, 146), (476, 128), (490, 90)], (255, 230, 160), 2.0, 0.9)
    # 방패 (뒤쪽, 성벽 모양)
    sh = [(250, -20), (250, -150), (270, -150), (270, -170), (300, -170), (300, -150), (330, -150), (330, -170), (360, -170), (360, -150),
          (390, -150), (390, -170), (420, -170), (420, -150), (440, -150), (440, -20)]
    c.part(poly(sh), STONE2, 20, bevel=10)
    c.part(poly([(262, -30), (262, -140), (428, -140), (428, -30)]), CRIM, 21, bevel=6)
    c.part(poly([(262, -30), (262, -140), (428, -140), (428, -30)]) & (np.abs(U - 345) > 12) & (np.abs(V + 85) > 12), CRIM, 22, bevel=6)
    c.part(profile([(333, 1), (357, 1)]) & (V < -32) & (V > -138) | (poly([(262, -79), (428, -79), (428, -91), (262, -91)])), GOLD2, 23, bevel=3)
    c.part(disc(345, -85, 22), GOLD2, 24, bevel=7)
    c.part(disc(345, -85, 13), TOPAZ, 25, bevel=5)
    # 방패 테두리 징
    for u in (262, 300, 345, 390, 428):
        for v in (-30, -140):
            c.part(disc(u, v, 5), IRON, 30 + u + v, bevel=2)
    c.part(profile([(380, 16), (470, 16)]), IRON, 40, bevel=5)
    c.part(poly([(470, -10), (520, 0), (470, 10)]), SILVER, 41, shape="blade")
    # 오라: 금빛 수호 기운
    for k in range(9):
        a = -170 + k * 20
        au.wisp([(345, -85), (345 + 140 * math.cos(math.radians(a)), -85 + 140 * math.sin(math.radians(a)))], 12, (255, 210, 90), alpha=0.3)
    au.glow(c.sil, (255, 210, 100), 12, 0.5)
    return c, au, dict(outline_col=(30, 20, 8), sparkle=(255, 245, 200))


WEAPONS3 = {"moon": moon, "magma": magma, "crystal": crystal, "tempest": tempest, "holy": holy, "vampire": vampire,
            "sunbow": sunbow, "viper": viper, "starbow": starbow, "shuriken": shuriken,
            "frostaxe": frostaxe, "twinaxe": twinaxe, "mjolnir": mjolnir, "bastion": bastion}


def paint(wid, out=128):
    c, au, opt = WEAPONS3[wid]()
    return finish(c, au, out, seed=sum(map(ord, wid)), **opt)


def preview(path, scale=2):
    ims = [paint(w) for w in WEAPONS3]
    cols = 7
    rows = (len(ims) + cols - 1) // cols
    cell = 128 * scale + 16
    W = Image.new("RGBA", (cols * cell + 16, rows * cell + 16), (58, 58, 62, 255))
    for i, im in enumerate(ims):
        x, y = 16 + (i % cols) * cell, 16 + (i // cols) * cell
        W.alpha_composite(im.resize((128 * scale, 128 * scale), Image.NEAREST), (x, y))
    W.convert("RGB").save(path)


if __name__ == "__main__":
    import sys
    preview(sys.argv[1] if len(sys.argv) > 1 else "weapons3.png")
