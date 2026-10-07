"""특수무기 20종 스킬 안무 (상점 설명창 영상용 — shoptip.py 가 장면을 그림)

 무기마다 실제 스킬 동작을 따라 움직인다 (a50 · a55 · a56 의 판정 · 연출과 같은 흐름):
   시전자 자세(팔 · 몸 돌림 · 점프 · 이동) + 무기/소품(거대한 검 · 날아가는 창 · 사슬 · 돌기둥 ...)
   + 타격 지점(impacts) + 적 반응(hits: 밀려남 · 띄움 · 끌려옴 · 빙결 · 중독 · 둔화)
 좌표: 시전자 발 = o, 앞 = +z, 오른쪽 = -x.  t = 0..1 (영상 한 바퀴)
"""
import math

import numpy as np
from PIL import Image, ImageDraw


# ─────────────────────────────────────────── 시간 도우미
def seg(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    return max(0.0, min(1.0, (t - a) / (b - a)))


def ease(u):
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 2


def ease_in(u):
    u = max(0.0, min(1.0, u))
    return u * u * u


def back_out(u, k=1.7):
    u = max(0.0, min(1.0, u)) - 1
    return 1 + u * u * ((k + 1) * u + k)


def arc(u):
    """0→1→0 포물선"""
    u = max(0.0, min(1.0, u))
    return 4 * u * (1 - u)


def V(x, y, z):
    return np.array([x, y, z], float)


def rot_y(v, a):
    c, s = math.cos(a), math.sin(a)
    return V(v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)


def dir_yaw(a):
    """yaw 방향 단위 벡터 (0 = +z, + = 왼쪽(+x) 으로 돎)"""
    return V(math.sin(a), 0, math.cos(a))


# ─────────────────────────────────────────── 작은 그림 (빛 구슬 · 하트 · 별)
_IMG = {}


def glow_img(col):
    key = ("glow", col)
    if key not in _IMG:
        yy, xx = np.mgrid[0:64, 0:64]
        rr = np.sqrt((xx - 32) ** 2 + (yy - 32) ** 2) / 32
        arr = np.zeros((64, 64, 4), np.float32)
        arr[..., :3] = np.array(col) / 255 * 0.55 + 0.45
        arr[..., 3] = np.clip(1 - rr, 0, 1) ** 1.5
        _IMG[key] = Image.fromarray((arr * 255).astype(np.uint8), "RGBA")
    return _IMG[key]


def heart_img():
    if "heart" not in _IMG:
        P = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]
        im = Image.new("RGBA", (7 * 6, 6 * 6), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for y, row in enumerate(P):
            for x, c in enumerate(row):
                if c == "1":
                    d.rectangle([x * 6, y * 6, x * 6 + 5, y * 6 + 5], fill=(230, 30, 40, 255) if (x + y) % 5 else (255, 120, 120, 255))
        _IMG["heart"] = im
    return _IMG["heart"]


def star_img():
    if "star" not in _IMG:
        im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts = []
        for i in range(10):
            r = 15 if i % 2 == 0 else 6
            a = math.pi / 2 + i * math.pi / 5
            pts.append((16 + math.cos(a) * r, 16 - math.sin(a) * r))
        d.polygon(pts, fill=(255, 230, 80, 255))
        _IMG["star"] = im
    return _IMG["star"]


def streak_img(col):
    key = ("streak", col)
    if key not in _IMG:
        arr = np.zeros((16, 128, 4), np.float32)
        xx = np.linspace(0, 1, 128)
        for y in range(16):
            k = 1 - abs(y - 7.5) / 8
            arr[y, :, :3] = np.array(col) / 255 * 0.5 + 0.5
            arr[y, :, 3] = np.clip(k, 0, 1) ** 1.5 * xx ** 0.7
        _IMG[key] = Image.fromarray((arr * 255).astype(np.uint8), "RGBA")
    return _IMG[key]


# ─────────────────────────────────────────── 장면 상태
class Ctx:
    def __init__(self, t, f, o, Y, kind, acc):
        self.t, self.f, self.o, self.Y = t, f, o, Y
        self.kind, self.acc = kind, acc
        self.me = o.copy()
        self.yaw = 0.0
        self.arm, self.arm_side, self.arm_l, self.legs, self.jump = 0.3, 0.12, 0.0, 0.0, 0.0
        self.hold = True                 # 무기를 손에 듦
        self.foes = [o + V(1.0, 0, 5.6), o + V(-1.3, 0, 6.4)]
        self.hits = []                   # (적 번호, 시작 t, 반응, 기준점)
        self.impacts = []                # (시작 t, 위치, 반지름, 파편)
        self.ground = []                 # (시작 t, 끝 t, 위치, 지름, 회전)  — 실제 게임 바닥 효과 그림
        self.props = []                  # (종류, 인자...) — shoptip 이 그림
        self.heal = 0.0

    # 소품
    def big_weapon(self, H, T, q=None, scale_key="", alpha=1.0, light=1.15):
        self.props.append(("weapon", H, T, q, alpha, light))

    def orb(self, p, size, col=None, alpha=1.0):
        self.props.append(("orb", p, size, col or self.acc, alpha))

    def block(self, name, p, size, rot=0.0):
        self.props.append(("block", name, p, size, rot))

    def streak(self, a, b, width, col=None, alpha=1.0):
        self.props.append(("streak", a, b, width, col or self.acc, alpha))

    def sprite(self, img_key, p, size, alpha=1.0):
        self.props.append(("sprite", img_key, p, size, alpha))

    def chain(self, a, b, n=10):
        for i in range(n + 1):
            p = a + (b - a) * (i / n)
            self.block("iron_block", p, 0.11, i * 0.9)

    def hit(self, i, t0, kind, src=None):
        self.hits.append((i, t0, kind, self.me.copy() if src is None else src))

    def impact(self, t0, p, r, deb=True):
        q = p.copy(); q[1] = self.Y
        self.impacts.append((t0, q, r, deb))


def hand_pos(c):
    """오른손 대략 위치 (팔 각도 반영)"""
    sh = c.me + V(0, c.jump, 0) + rot_y(V(-0.36, 1.32, 0), c.yaw)
    d = rot_y(V(0, -math.cos(c.arm), math.sin(c.arm)), c.yaw)
    return sh + d * 0.7


# ═══════════════════════════════════════════ 무기별 안무
def thunder(c, t):
    # 성검을 하늘로 치켜들면 → 하늘에서 거대한 성검이 내리꽂히며 낙뢰 · 번개 충격파
    tg = c.o + V(0, 0, 6.0)
    c.arm = 0.4 + 2.6 * back_out(seg(t, 0.05, 0.25))
    c.arm_l = 0.6 * seg(t, 0.1, 0.25)
    c.ground.append((0.1, 0.9, tg, 5.5, t * 2))
    fall = seg(t, 0.26, 0.4)
    if 0.24 < t < 0.9:
        tip = tg + V(0, 6.5 * (1 - ease_in(fall)) - 0.4, 0)          # 날끝이 땅에 박힘
        c.big_weapon(tip + V(0, 4.2, 0), tip, q=V(1, 0, 0))
    if 0.4 <= t < 0.5:
        c.props.append(("bolt", tg, 7.0, 1 - seg(t, 0.4, 0.5)))
    c.impact(0.4, tg, 3.0)
    c.hit(0, 0.4, "knock", tg); c.hit(1, 0.4, "knock", tg)


def dragon(c, t):
    # 도끼를 옆으로 뻗고 몸을 두 바퀴 돌리며 불꽃을 흩뿌림 → 앞쪽 적이 튕겨 나감
    c.foes = [c.o + V(1.4, 0, 2.6), c.o + V(-1.8, 0, 2.2)]
    u = seg(t, 0.12, 0.62)
    c.yaw = 2 * 2 * math.pi * ease(u)
    c.arm, c.arm_side = 1.35 * seg(t, 0.05, 0.14), 1.3 * seg(t, 0.05, 0.14)
    c.legs = 0.3 * math.sin(t * 40) if 0.12 < t < 0.62 else 0
    if 0.12 < t < 0.66:
        c.ground.append((0.12, 0.7, c.o, 6.5, c.yaw))
        for j in range(6):
            a = c.yaw - j * 0.35 - 1.2
            c.orb(c.o + dir_yaw(a) * 2.0 + V(0, 1.1, 0), 0.6 - j * 0.07, (255, 120, 30), 1 - j * 0.14)
    c.impact(0.62, c.o, 2.6)
    for i, tt in ((0, 0.28), (1, 0.4), (0, 0.5), (1, 0.6)):
        c.hit(i, tt, "knock", c.o)


def wind(c, t):
    # 질주하며 레이피어로 세 번 찌르기 (찌를 때마다 앞으로 휙)
    c.foes = [c.o + V(0.5, 0, 2.6), c.o + V(-0.6, 0, 4.4)]
    steps = [(0.1, 0.22, 1.6), (0.3, 0.42, 3.2), (0.5, 0.62, 4.8)]
    z = 0.0
    for a_, b_, zz in steps:
        if t >= a_:
            prev = steps[steps.index((a_, b_, zz)) - 1][2] if steps.index((a_, b_, zz)) else 0.0
            z = prev + (zz - prev) * ease(seg(t, a_, b_))
    c.me = c.o + V(0, 0, z)
    jab = max((math.sin(math.pi * seg(t, a_, b_)) for a_, b_, _ in steps), default=0)
    c.arm = 1.45 + 0.1 * jab
    c.legs = 0.6 * jab
    for a_, b_, zz in steps:
        if a_ <= t < b_ + 0.06:
            c.streak(c.me + V(-0.3, 1.25, 0.2), c.me + V(-0.3, 1.25, 2.4), 0.35, (180, 255, 230), 1 - seg(t, b_, b_ + 0.06))
    c.ground.append((0.1, 0.8, c.o + V(0, 0, 2.6), 5.0, 0))
    for (a_, b_, zz), i in zip(steps, (0, 1, 1)):
        c.impact(b_, c.o + V(0, 0, zz + 0.9), 1.4, False)
        c.hit(i, b_, "knock", c.me.copy())


def phoenix(c, t):
    # 손을 치켜들면 하늘에서 거대한 망치가 떨어져 내리찍음 → 빛기둥 8개 · 결계 (적은 밖으로 밀려남)
    c.foes = [c.o + V(2.2, 0, 2.0), c.o + V(-2.4, 0, 1.0)]
    c.arm = 0.3 + 2.7 * back_out(seg(t, 0.05, 0.2))
    c.hold = t < 0.2 or t > 0.6
    fall = seg(t, 0.22, 0.36)
    tg = c.o + V(0, 0, 1.2)
    if 0.2 < t < 0.75:
        tip = tg + V(0, 6.5 * (1 - ease_in(fall)) - 0.2, 0)
        c.big_weapon(tip + V(0, 4.5, 0), tip, q=V(1, 0, 0))
    c.ground.append((0.36, 0.95, c.o, 7.0, 0))
    c.impact(0.36, tg, 3.4)
    for k in range(8):
        tk = 0.4 + k * 0.025
        p = c.o + dir_yaw(k * math.pi / 4) * 3.2
        if tk <= t < tk + 0.25:
            c.props.append(("pillar", p, seg(t, tk, tk + 0.25)))
    c.hit(0, 0.36, "knock", c.o); c.hit(1, 0.36, "knock", c.o)


def blackiron(c, t):
    # 앞으로 돌진 → 거대한 유령 대검이 앞을 가로로 크게 휩쓺
    c.foes = [c.o + V(1.3, 0, 4.6), c.o + V(-1.4, 0, 5.0)]
    c.me = c.o + V(0, 0, 3.2 * ease(seg(t, 0.08, 0.26)))
    c.legs = 0.7 * math.sin(t * 50) if 0.08 < t < 0.26 else 0.3
    c.arm, c.arm_side = 1.4, 1.2 * (1 - seg(t, 0.32, 0.5))
    c.ground.append((0.08, 0.85, c.o + V(0, 0, 3.6), 7.0, 0))
    u = seg(t, 0.3, 0.52)
    if 0.28 < t < 0.62:
        ang = -1.9 + 3.8 * ease_in(u)
        H = c.me + V(0, 1.1, 0)
        T = H + dir_yaw(ang) * 4.6
        c.big_weapon(H, T, q=V(0, 1, 0), alpha=1 - seg(t, 0.52, 0.62), light=1.3)
        for j in range(5):
            a2 = ang - j * 0.22
            c.orb(H + dir_yaw(a2) * 3.4, 0.7, (220, 20, 50), 0.7 - j * 0.12)
    c.impact(0.42, c.me + V(0, 0, 2.0), 2.4)
    c.hit(0, 0.38, "knock", c.me.copy()); c.hit(1, 0.46, "knock", c.me.copy())


def tiger(c, t):
    # 단검 두 자루가 앞으로 날아가 X 자로 교차 — 세 번 (팔을 좌우로 번갈아 벰)
    c.foes = [c.o + V(0.6, 0, 3.6), c.o + V(-0.9, 0, 4.2)]
    waves = [0.12, 0.34, 0.56]
    for w0 in waves:
        u = seg(t, w0, w0 + 0.16)
        if 0 < u < 1:
            for s in (-1, 1):
                p0 = c.o + V(s * 1.3, 1.2, 0.8)
                p1 = c.o + V(-s * 1.3, 1.2, 5.6)
                p = p0 + (p1 - p0) * ease(u)
                d = (p1 - p0) / np.linalg.norm(p1 - p0)
                c.big_weapon(p - d * 0.7, p + d * 0.7, q=V(0, 1, 0), light=1.3)
                c.orb(p - d * 0.9, 0.5, (200, 120, 255), 0.6)
    k = max((math.sin(math.pi * seg(t, w0, w0 + 0.16)) for w0 in waves))
    c.arm = 1.2 + 0.5 * k
    c.arm_side = 0.8 * math.sin(t * 25)
    c.ground.append((0.12, 0.85, c.o + V(0, 0, 3.4), 4.5, 0.6))
    for w0 in waves:
        c.impact(w0 + 0.1, c.o + V(0, 0, 3.8), 1.4, False)
        c.hit(0, w0 + 0.1, "knock", c.o); c.hit(1, w0 + 0.1, "knock", c.o)


def staff(c, t):
    # 지팡이가 손에서 떠올라 돌며 비전 구체를 모음 → 폭발해 적을 공중으로
    c.foes = [c.o + V(2.0, 0, 2.2), c.o + V(-2.1, 0, 1.6)]
    c.hold = False
    c.arm = c.arm_l = 2.6 * back_out(seg(t, 0.05, 0.2))
    u = seg(t, 0.05, 0.45)
    if t < 0.62:
        spin = t * 18
        cen = c.o + V(0, 1.6 + 1.4 * ease(u), 0)
        d = V(math.sin(spin) * 0.4, 1.0, math.cos(spin) * 0.4)
        d /= np.linalg.norm(d)
        c.big_weapon(cen - d * 1.3, cen + d * 1.3, q=rot_y(V(1, 0, 0), spin))
    orb_c = c.o + V(0, 3.4, 0)
    if 0.1 < t < 0.46:
        s = 0.3 + 1.6 * seg(t, 0.1, 0.45)
        c.orb(orb_c, s, (190, 120, 255))
        for j in range(8):
            a = j * math.pi / 4 + t * 6
            rr = 3.2 * (1 - seg(t, 0.1 + j * 0.02, 0.45))
            c.orb(orb_c + V(math.cos(a) * rr, math.sin(a * 1.3) * 0.6, math.sin(a) * rr), 0.3, (230, 190, 255))
    elif 0.46 <= t < 0.58:
        c.orb(orb_c, 3.5 * (1 + seg(t, 0.46, 0.58)), (220, 170, 255), 1 - seg(t, 0.46, 0.58))
    c.ground.append((0.05, 0.9, c.o, 6.5, t * 3))
    c.impact(0.46, c.o, 3.0)
    c.hit(0, 0.46, "launch", c.o); c.hit(1, 0.46, "launch", c.o)


def peachwood(c, t):
    # 불붙은 창 여섯 자루가 하늘에서 둥글게 차례로 쏟아짐 (적은 불타며 밀려남)
    c.foes = [c.o + V(3.0, 0, 1.4), c.o + V(-2.6, 0, 2.2)]
    c.arm = 0.3 + 2.6 * back_out(seg(t, 0.04, 0.18))
    c.ground.append((0.08, 0.9, c.o, 7.5, t * 2))
    for k in range(6):
        tk = 0.18 + k * 0.06
        p = c.o + dir_yaw(k * math.pi / 3 + 0.3) * 3.4
        u = seg(t, tk, tk + 0.1)
        if tk <= t < 0.9:
            tip = p + V(0, 6.0 * (1 - ease_in(u)) - 0.3, 0)
            c.big_weapon(tip + V(0, 2.6, 0), tip, q=V(1, 0, 0), alpha=1 - seg(t, 0.75, 0.9))
            if u < 1:
                c.orb(tip + V(0, 2.0, 0), 0.9, (255, 120, 20), 0.8)
        c.impact(tk + 0.1, p, 1.6, k % 2 == 0)
    c.hit(0, 0.34, "burn", c.o); c.hit(1, 0.46, "burn", c.o)


def frost(c, t):
    # 활시위를 당기는 자세 → 얼음 화살 세 발 → 맞은 적 자리에 얼음 가시 (얼어붙음)
    tg = c.o + V(0.6, 0, 6.0)
    c.foes = [tg.copy(), c.o + V(-1.6, 0, 6.6)]
    c.arm = 1.5 * seg(t, 0.02, 0.1)
    c.arm_l = 1.5 * seg(t, 0.02, 0.1)
    c.yaw = 0.15
    for k in range(3):
        t0 = 0.18 + k * 0.08
        u = seg(t, t0, t0 + 0.12)
        if 0 < u < 1:
            a = c.o + V(-0.3, 1.3, 0.8)
            b = tg + V((k - 1) * 0.5, 1.0, 0)
            p = a + (b - a) * u
            c.streak(p - (b - a) / np.linalg.norm(b - a) * 1.6, p, 0.28, (190, 235, 255))
    if t >= 0.3:
        u = seg(t, 0.3, 0.38)
        for j in range(7):
            a = j * 0.9
            r = 0.6 + (j % 3) * 0.25
            h = (1.3 + (j % 2) * 0.6) * ease(u) * (1 - seg(t, 0.8, 0.92))
            if h > 0.05:
                c.props.append(("icespike", tg + V(math.cos(a) * r, 0, math.sin(a) * r), h))
    c.ground.append((0.3, 0.9, tg, 4.5, 0))
    c.impact(0.3, tg, 2.0)
    c.hit(0, 0.3, "freeze", tg)


def storm(c, t):
    # 삼지창을 뒤로 젖혔다 던짐 → 꽂힌 자리에 낙뢰 → 번개가 다음 적에게 튀어감
    tg = c.o + V(0.8, 0, 6.2)
    c.foes = [tg + V(0.3, 0, 0.4), c.o + V(-1.8, 0, 6.8)]
    if t < 0.2:
        c.arm = -0.9 * ease(seg(t, 0.02, 0.18)) + 0.3
        c.yaw = -0.4 * seg(t, 0.02, 0.18)
    else:
        c.arm = -0.6 + 2.3 * back_out(seg(t, 0.2, 0.28))
        c.yaw = -0.4 + 0.6 * seg(t, 0.2, 0.28)
    c.hold = t < 0.24
    u = seg(t, 0.24, 0.4)
    if 0.24 <= t < 0.85:
        a = c.o + V(-0.4, 1.6, 0.4)
        b = tg + V(0, 0.6, 0)
        p = a + (b - a) * u + V(0, arc(u) * 1.2, 0)
        d = (b - a) / np.linalg.norm(b - a)
        c.big_weapon(p - d * 1.1, p + d * 1.1, q=V(0, 1, 0))
    if 0.4 <= t < 0.5:
        c.props.append(("bolt", tg, 7.0, 1 - seg(t, 0.4, 0.5)))
    if 0.5 <= t < 0.62:
        c.props.append(("zap", tg + V(0, 1.2, 0), c.foes[1] + V(0, 1.2, 0), 1 - seg(t, 0.5, 0.62)))
    c.ground.append((0.38, 0.9, tg, 5.0, 0))
    c.impact(0.4, tg, 2.6)
    c.hit(0, 0.4, "knock", tg); c.hit(1, 0.52, "knock", tg)


def scythe(c, t):
    # 누운 낫이 몸 둘레를 한 바퀴 돌며 벰 → 맞은 적의 영혼(하트)이 시전자에게 흘러와 회복
    c.foes = [c.o + V(2.2, 0, 1.6), c.o + V(-2.3, 0, 1.0)]
    u = seg(t, 0.12, 0.42)
    c.yaw = 2 * math.pi * ease(u)
    c.arm, c.arm_side = 1.4 * seg(t, 0.04, 0.12), 1.35 * seg(t, 0.04, 0.12)
    c.ground.append((0.1, 0.9, c.o, 7.0, c.yaw))
    for j in range(5):
        a = c.yaw - j * 0.3 - 1.3
        if 0.12 < t < 0.45:
            c.orb(c.o + dir_yaw(a) * 2.2 + V(0, 1.1, 0), 0.55, (90, 255, 230), 0.8 - j * 0.15)
    c.hit(0, 0.26, "knock", c.o); c.hit(1, 0.36, "knock", c.o)
    c.impact(0.42, c.o, 2.4, False)
    if 0.45 < t < 0.85:
        for i, fp in enumerate(c.foes):
            for k in range(3):
                u2 = seg(t, 0.45 + k * 0.06 + i * 0.03, 0.7 + k * 0.06 + i * 0.03)
                if 0 < u2 < 1:
                    p = fp + V(0, 1.4, 0) + (c.me + V(0, 1.4, 0) - fp - V(0, 1.4, 0)) * ease(u2) + V(0, arc(u2) * 0.8, 0)
                    c.sprite("heart", p, 0.35)
    c.heal = seg(t, 0.6, 0.8) * (1 - seg(t, 0.85, 0.95))


def lance(c, t):
    # 창을 수평으로 겨누고 일직선 돌격 — 지나가는 길의 적이 공중으로 튕겨 오름
    c.foes = [c.o + V(0.4, 0, 2.6), c.o + V(-0.3, 0, 4.6)]
    z = 6.0 * ease(seg(t, 0.1, 0.5))
    c.me = c.o + V(0, 0, z)
    c.arm = 1.5
    c.legs = 0.8 * math.sin(t * 60) if 0.1 < t < 0.5 else 0
    if 0.1 < t < 0.6:
        c.streak(c.me + V(0, 1.1, -3.0), c.me + V(0, 1.1, 0.4), 1.2, (255, 235, 150), 1 - seg(t, 0.5, 0.6))
    c.ground.append((0.08, 0.85, c.o + V(0, 0, 3.0), 6.5, 0))
    for i, fz in enumerate((2.6, 4.6)):
        tt = 0.1 + (0.4) * (1 - math.sqrt(max(0, 1 - fz / 6.0)))
        c.hit(i, tt, "launch", c.o + V(0, 0, fz - 1))
        c.impact(tt, c.o + V(0, 0, fz), 1.5, False)
    c.impact(0.5, c.o + V(0, 0, 6.6), 2.2)


def skull(c, t):
    # 해골이 날아가 터지며 독 구름 (구름 속 적은 초록빛으로 중독)
    tg = c.o + V(0.6, 0, 6.0)
    c.foes = [tg + V(0.6, 0, 0.3), tg + V(-1.2, 0, 0.6)]
    c.arm = 1.6 * back_out(seg(t, 0.05, 0.15))
    u = seg(t, 0.15, 0.36)
    if 0.15 <= t < 0.36:
        p = c.o + V(-0.3, 1.5, 0.6) + (tg + V(0, 1.0, 0) - c.o - V(-0.3, 1.5, 0.6)) * u
        c.block("skull", p, 0.5, t * 20)
        c.orb(p, 0.9, (120, 255, 90), 0.6)
        c.streak(p - V(0, 0, 1.4), p, 0.3, (120, 255, 90), 0.6)
    if 0.36 <= t < 0.95:
        for j in range(6):
            a = j * 1.05 + t * 2
            r = 1.4 * ease(seg(t, 0.36, 0.5))
            c.orb(tg + V(math.cos(a) * r, 0.6 + (j % 2) * 0.5, math.sin(a) * r), 1.6, (90, 220, 60), 0.5 * (1 - seg(t, 0.8, 0.95)))
    c.ground.append((0.36, 0.95, tg, 5.5, t))
    c.impact(0.36, tg, 2.4)
    c.hit(0, 0.36, "poison", tg); c.hit(1, 0.38, "poison", tg)


def chakram(c, t):
    # 원반을 던지면 회전하며 날아갔다가 돌아옴 — 가는 길 · 오는 길 두 번 벰
    c.foes = [c.o + V(0.4, 0, 3.4), c.o + V(-0.4, 0, 5.6)]
    c.arm = 1.5 * seg(t, 0.04, 0.12) if t < 0.7 else 1.5 * (1 - seg(t, 0.7, 0.8))
    c.hold = not (0.14 < t < 0.68)
    if 0.14 <= t < 0.68:
        u = seg(t, 0.14, 0.41) if t < 0.41 else 1 - seg(t, 0.41, 0.68)
        p = c.o + V(-0.3, 1.2, 0.6 + 6.0 * ease(u)) + V(math.sin(u * math.pi) * 1.2, 0, 0)
        sp = t * 40
        d = V(math.cos(sp), 0, math.sin(sp))
        c.big_weapon(p - d * 0.6, p + d * 0.6, q=V(-math.sin(sp), 0, math.cos(sp)), light=1.3)
        c.orb(p, 1.0, (255, 210, 90), 0.5)
    c.ground.append((0.14, 0.85, c.o + V(0, 0, 3.6), 5.0, t * 4))
    c.hit(0, 0.22, "knock", c.o); c.hit(1, 0.34, "knock", c.o)
    c.hit(1, 0.48, "knock", c.o + V(0, 0, 7)); c.hit(0, 0.6, "knock", c.o + V(0, 0, 7))
    c.impact(0.41, c.o + V(0, 0, 6.6), 1.6, False)


def chain(c, t):
    # 사슬을 던져 앞의 적을 낚아 → 끌어와 기절 (머리 위에 별)
    c.foes = [c.o + V(0.3, 0, 6.0), c.o + V(-1.8, 0, 6.6)]
    c.arm = 1.55 * seg(t, 0.03, 0.1)
    c.hold = True
    hand = c.o + V(-0.36, 1.25, 0.7)
    tip_u = seg(t, 0.1, 0.24)
    pull_u = seg(t, 0.28, 0.44)
    foe0 = c.foes[0] + (c.o + V(0, 0, 1.4) - c.foes[0]) * ease(pull_u)
    if 0.1 <= t < 0.5:
        tip = hand + (foe0 + V(0, 1.1, 0) - hand) * (tip_u if t < 0.26 else 1)
        c.chain(hand, tip, 12)
    c.ground.append((0.24, 0.9, c.o + V(0, 0, 1.4), 3.5, 0))
    c.hit(0, 0.26, "pull", c.o + V(0, 0, 1.4))
    c.impact(0.44, c.o + V(0, 0, 1.4), 1.4, False)
    if 0.46 < t < 0.95:
        for k in range(3):
            a = t * 9 + k * 2.1
            c.sprite("star", c.o + V(0, 0, 1.4) + V(math.cos(a) * 0.45, 2.2, math.sin(a) * 0.45), 0.28)


def gauntlet(c, t):
    # 땅을 주먹으로 내리치면 → 앞으로 돌기둥이 줄지어 솟아 적을 띄움
    c.foes = [c.o + V(0.3, 0, 3.4), c.o + V(-0.4, 0, 5.8)]
    if t < 0.2:
        c.arm = 0.3 + 2.6 * back_out(seg(t, 0.03, 0.16))
    else:
        c.arm = 2.9 - 2.9 * ease_in(seg(t, 0.2, 0.25)) + 0.15
    c.jump = -0.12 * seg(t, 0.2, 0.25) * (1 - seg(t, 0.4, 0.5))
    c.ground.append((0.24, 0.9, c.o + V(0, 0, 4.0), 7.0, 0))
    c.impact(0.25, c.o + V(0, 0, 0.8), 1.6)
    for k in range(7):
        tk = 0.26 + k * 0.035
        z = 1.4 + k * 0.85
        if t >= tk:
            h = (1.2 + k * 0.1) * back_out(seg(t, tk, tk + 0.06)) * (1 - seg(t, 0.75, 0.9))
            if h > 0.05:
                c.props.append(("pillar_stone", c.o + V(0, 0, z), h, k))
    c.hit(0, 0.26 + 2 * 0.035, "launch", c.o); c.hit(1, 0.26 + 5 * 0.035, "launch", c.o)


def b_talos(c, t):
    # 청동 대검을 들고 지그재그로 세 번 연속 돌진 (톱니 잔상)
    pts = [V(0, 0, 0), V(1.4, 0, 2.2), V(-1.2, 0, 4.0), V(0.4, 0, 6.0)]
    segs = [(0.06, 0.2), (0.28, 0.42), (0.5, 0.64)]
    c.foes = [c.o + V(0.9, 0, 2.6), c.o + V(-0.6, 0, 4.6)]
    p = pts[0]
    for k, (a_, b_) in enumerate(segs):
        if t >= a_:
            p = pts[k] + (pts[k + 1] - pts[k]) * ease(seg(t, a_, b_))
    c.me = c.o + p
    k_now = max([k for k, (a_, b_) in enumerate(segs) if t >= a_] or [0])
    dv = pts[k_now + 1] - pts[k_now]
    c.yaw = math.atan2(dv[0], dv[2])
    c.arm = 1.4
    c.legs = 0.8 * math.sin(t * 60) if any(a_ < t < b_ for a_, b_ in segs) else 0
    for k, (a_, b_) in enumerate(segs):
        if a_ <= t < b_ + 0.1:
            q0 = c.o + pts[k]; q1 = c.me if t < b_ else c.o + pts[k + 1]
            c.streak(q0 + V(0, 0.8, 0), q1 + V(0, 0.8, 0), 0.9, (255, 170, 60), 1 - seg(t, b_, b_ + 0.1))
        c.impact(b_, c.o + pts[k + 1], 1.8)
    c.ground.append((0.06, 0.8, c.o + V(0, 0, 3.0), 6.0, t * 3))
    c.hit(0, 0.17, "knock", c.o + pts[0]); c.hit(1, 0.44, "knock", c.o + pts[2])


def b_sphinx(c, t):
    # 머리 위에 모래시계가 떠서 돌고, 모래 · 황금 블록 폭풍이 몸 둘레를 휘감음 (적은 느려지고 눈이 멂)
    c.foes = [c.o + V(2.8, 0, 2.4), c.o + V(-2.6, 0, 1.6)]
    c.arm = c.arm_l = 2.2 * back_out(seg(t, 0.04, 0.16))
    c.hold = False
    if t < 0.92:
        cen = c.o + V(0, 3.0 + 0.15 * math.sin(t * 12), 0)
        sp = t * 6
        d = V(0, 1, 0)
        c.big_weapon(cen - d * 0.9, cen + d * 0.9, q=V(math.cos(sp), 0, math.sin(sp)))
    n = 16
    for k in range(n):
        a = k * 2 * math.pi / n + t * 7
        r = 2.0 + (k % 4) * 0.55
        y = 0.4 + (k % 3) * 0.6 + t * 1.2
        if 0.08 < t < 0.9:
            c.block(["sand", "sandstone", "gold_block"][k % 3], c.o + V(math.cos(a) * r, y, math.sin(a) * r), 0.32, a)
    c.ground.append((0.06, 0.92, c.o, 9.0, t * 4))
    c.impact(0.2, c.o, 3.2, False)
    c.hit(0, 0.24, "slow", c.o); c.hit(1, 0.26, "slow", c.o)


def b_ladon(c, t):
    # 세 갈래 독 채찍이 부채꼴로 뻗었다가 돌아옴
    c.foes = [c.o + V(1.8, 0, 3.6), c.o + V(-1.6, 0, 4.0)]
    c.arm = 1.45 * back_out(seg(t, 0.05, 0.16))
    u = seg(t, 0.16, 0.32) if t < 0.36 else 1 - seg(t, 0.4, 0.55)
    for k in (-1, 0, 1):
        a = k * 0.56
        H = c.o + V(-0.3, 1.2, 0.6)
        for j in range(8):
            L = 4.4 * ease(u) * (j + 1) / 8
            wav = math.sin(t * 30 + j * 0.8) * 0.15 * j / 8
            p = H + dir_yaw(a) * L + V(0, wav, 0)
            c.orb(p, 0.45 - j * 0.02, (100, 230, 70), 0.85)
        if u > 0.2:
            T = H + dir_yaw(a) * 4.4 * ease(u)
            c.big_weapon(T - dir_yaw(a) * 0.7, T + dir_yaw(a) * 0.4, q=V(0, 1, 0))
    c.ground.append((0.16, 0.8, c.o + V(0, 0, 3.2), 6.5, 0))
    c.impact(0.32, c.o + V(0, 0, 3.8), 2.0, False)
    c.hit(0, 0.31, "poison", c.o); c.hit(1, 0.31, "poison", c.o)


def b_cyclops(c, t):
    # 거대한 바위를 머리 위로 들어 올려 → 포물선으로 던져 땅을 뒤흔듦
    tg = c.o + V(0.4, 0, 6.6)
    c.foes = [tg + V(1.0, 0, 0.3), tg + V(-1.2, 0, 0.6)]
    c.arm = c.arm_l = 3.0 * back_out(seg(t, 0.04, 0.2)) if t < 0.3 else 3.0 - 1.6 * ease(seg(t, 0.3, 0.36))
    c.yaw = -0.3 * seg(t, 0.2, 0.3) * (1 - seg(t, 0.3, 0.36))
    c.hold = False
    if t < 0.32:
        rock = c.o + V(0, 2.6 + 0.4 * ease(seg(t, 0.04, 0.2)), 0)
    else:
        u = seg(t, 0.32, 0.5)
        a = c.o + V(0, 3.0, 0)
        rock = a + (tg + V(0, 0.8, 0) - a) * u + V(0, arc(u) * 3.0, 0)
    if t < 0.5:
        for k, (dx, dy, dz) in enumerate(((0, 0, 0), (0.5, 0.2, 0.1), (-0.4, 0.3, -0.2), (0.1, -0.35, 0.3), (-0.2, 0.15, 0.45))):
            c.block(["cobblestone", "mossy_cobblestone", "andesite", "stone", "cobblestone"][k], rock + V(dx, dy, dz), 0.75, t * 8 + k)
    c.ground.append((0.36, 0.95, tg, 6.5, 0))
    c.impact(0.5, tg, 3.4)
    c.hit(0, 0.5, "launch", tg); c.hit(1, 0.5, "launch", tg)


CHOREO = {"thunder": thunder, "dragon": dragon, "wind": wind, "phoenix": phoenix, "blackiron": blackiron, "tiger": tiger,
          "staff": staff, "peachwood": peachwood, "frost": frost, "storm": storm, "scythe": scythe, "lance": lance,
          "skull": skull, "chakram": chakram, "chain": chain, "gauntlet": gauntlet, "b_talos": b_talos, "b_sphinx": b_sphinx,
          "b_ladon": b_ladon, "b_cyclops": b_cyclops}
# 카메라가 볼 곳 (시전자 기준 앞쪽 거리) — 멀리 던지는 스킬은 가운데를 봄
FOCUS = {"thunder": 3.2, "storm": 3.2, "skull": 3.2, "frost": 3.2, "b_cyclops": 3.3, "chain": 3.0, "chakram": 3.0, "lance": 3.0,
         "wind": 2.6, "gauntlet": 3.0, "b_talos": 3.0, "blackiron": 2.6, "tiger": 2.2, "b_ladon": 2.0, "dragon": 1.2,
         "phoenix": 0.8, "staff": 0.6, "peachwood": 0.6, "scythe": 0.6, "b_sphinx": 0.6}
