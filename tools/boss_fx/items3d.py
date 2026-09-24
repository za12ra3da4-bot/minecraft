"""플레이어 아이템 입체 모델 22종 (큐보이드 조립) — models/gear/*.json + textures/item/gear3d/*.png

좌표: 마인크래프트 모델 단위 (0..16 = 한 블록). 무기는 바닐라 스프라이트와 같은 대각선에 놓는다
(손잡이 왼쪽 아래 → 끝 오른쪽 위, 창(손)만 반대) → 바닐라 손 자세가 그대로 맞는다.
"""
import math

from model3d import BOW, CROSSBOW, GENERATED, HANDHELD, M3, SPEAR_HAND

R2 = math.sqrt(0.5)


class Axis:
    """A 에서 heading(도) 방향으로 뻗는 무기 축. P(s) = 축 위 s 칸, N(s, o) = 수직으로 o 칸"""

    def __init__(self, a, heading=45.0):
        self.a = a
        h = math.radians(heading)
        self.d = (math.cos(h), math.sin(h))
        self.n = (-self.d[1], self.d[0])

    def P(self, s, o=0.0):
        return (self.a[0] + self.d[0] * s + self.n[0] * o, self.a[1] + self.d[1] * s + self.n[1] * o)


def blade(m, ax, s0, s1, w, mat, z=8.0, d=0.8, o=0.0, **opt):
    m.seg(ax.P(s0, o), ax.P(s1, o), w, z, d, mat, **opt)


def cross(m, ax, s, half, w, mat, z=8.0, d=2.0, **opt):
    m.seg(ax.P(s, half), ax.P(s, -half), w, z, d, mat, **opt)


def knob(m, p, size, mat, z=8.0, d=None, **opt):
    d = d or size
    m.box((p[0] - size / 2, p[1] - size / 2, z - d / 2), (p[0] + size / 2, p[1] + size / 2, z + d / 2), mat, **opt)


# ═════════════════════════════════════════ 검 · 도끼 · 망치 (handheld)
def infantry_sword():
    m = M3("infantry_sword")
    ax = Axis((2.2, 2.2))
    blade(m, ax, -0.2, 1.1, 2.0, "bronze", d=2.0, engrave=True)          # 폼멜
    blade(m, ax, 1.1, 4.6, 1.3, "leather", d=1.3)                        # 손잡이 감개
    cross(m, ax, 5.2, 3.3, 1.1, "bronze", d=2.0, engrave=True)          # 코등이
    blade(m, ax, 5.7, 7.0, 1.7, "steel", d=1.0)                          # 리카소
    blade(m, ax, 6.6, 15.6, 2.0, "steel", d=0.8, fuller=True, edge=True)
    blade(m, ax, 15.5, 17.0, 1.3, "steel", d=0.7, edge=True, tiplight=True)
    blade(m, ax, 16.9, 18.0, 0.6, "steel", d=0.5, tiplight=True)
    return m.save(HANDHELD)


def xiphos():
    m = M3("xiphos")
    ax = Axis((2.0, 2.0))
    blade(m, ax, -0.2, 0.9, 2.4, "gold", d=2.2, engrave=True)
    blade(m, ax, 0.9, 4.2, 1.3, "wood", d=1.3)
    cross(m, ax, 4.7, 2.8, 1.0, "gold", d=2.0, engrave=True)
    for o in (3.1, -3.1):
        knob(m, ax.P(4.7, o), 1.1, "gold")
    for s0, s1, w in ((5.1, 7.5, 1.8), (7.5, 10.5, 2.5), (10.5, 13.5, 3.1), (13.5, 15.5, 2.5), (15.5, 17.0, 1.5), (16.9, 18.0, 0.6)):
        blade(m, ax, s0, s1, w, "bronze", d=0.8, edge=True)
    blade(m, ax, 5.3, 16.4, 0.45, "gold", d=0.95, noao=True)                # 가운데 능선
    return m.save(HANDHELD)


def kopis():
    m = M3("kopis")
    ax = Axis((2.4, 2.0))
    knob(m, ax.P(-0.2), 1.9, "bronze", d=1.6, engrave=True)               # 새 머리 폼멜
    m.seg(ax.P(-0.4, 0.4), ax.P(-1.6, 1.4), 0.7, 8, 1.0, "bronze")        # 부리
    blade(m, ax, 0.8, 4.2, 1.3, "leather", d=1.3)
    cross(m, ax, 4.7, 1.9, 0.9, "bronze", d=1.8)
    blade(m, ax, 5.0, 9.0, 1.7, "steel", d=0.8, edge=True)
    blade(m, ax, 9.0, 12.4, 2.6, "steel", d=0.8, o=-0.4, edge=True)       # 앞이 무거운 배
    q = ax.P(12.3, -0.55)
    h = math.radians(22.5)
    q2 = (q[0] + math.cos(h) * 3.6, q[1] + math.sin(h) * 3.6)
    m.seg(q, q2, 2.3, 8, 0.8, "steel", edge=True)
    q3 = (q2[0] + math.cos(h) * 1.5, q2[1] + math.sin(h) * 1.5)
    m.seg(q2, q3, 1.1, 8, 0.6, "steel", tiplight=True)
    return m.save(HANDHELD)


def dagger():
    m = M3("dagger")
    ax = Axis((4.2, 4.2))
    knob(m, ax.P(0), 2.0, "bone", d=2.0)
    blade(m, ax, 0.9, 3.3, 1.3, "leather", d=1.3)
    cross(m, ax, 3.8, 2.4, 0.9, "bronze", d=1.8, engrave=True)
    blade(m, ax, 4.2, 8.4, 2.6, "steel", d=0.8, fuller=True, edge=True)
    blade(m, ax, 8.3, 10.0, 1.5, "steel", d=0.7, edge=True)
    blade(m, ax, 9.9, 10.9, 0.6, "steel", d=0.5, tiplight=True)
    return m.save(HANDHELD)


def hephaestus_sword():
    m = M3("hephaestus_sword")
    ax = Axis((2.4, 2.4))
    cross(m, ax, 0.0, 1.7, 1.5, "steel", d=2.2)                           # 망치 폼멜
    blade(m, ax, 0.7, 4.4, 1.3, "leather", d=1.3)
    cross(m, ax, 5.0, 3.5, 1.4, "dsteel", d=2.4)
    knob(m, ax.P(5.0), 1.3, "ember", d=2.6, gem=True)
    blade(m, ax, 5.6, 16.0, 2.5, "dsteel", d=0.9, fuller=True)
    for o in (1.3, -1.3):
        blade(m, ax, 6.0, 15.6, 0.4, "ember", d=0.95, o=o, noao=True)     # 달궈진 날
    blade(m, ax, 15.9, 17.3, 1.5, "dsteel", d=0.8)
    blade(m, ax, 17.2, 18.2, 0.6, "ember", d=0.6)
    return m.save(HANDHELD)


def hydra_fang():
    m = M3("hydra_fang")
    ax = Axis((2.2, 2.2))
    knob(m, ax.P(0), 1.8, "eye", d=1.8, gem=True)
    blade(m, ax, 0.8, 4.3, 1.4, "green", d=1.4)
    for o in (2.6, -2.6):                                                   # 뱀 머리 코등이
        m.seg(ax.P(4.7), ax.P(4.9, o), 1.0, 8, 1.3, "green")
        knob(m, ax.P(5.1, o * 1.1), 1.3, "green", d=1.5)
    blade(m, ax, 5.0, 9.0, 2.7, "bone", d=0.9, edge=True)
    blade(m, ax, 9.0, 12.5, 2.2, "bone", d=0.85, o=0.3, edge=True)
    blade(m, ax, 12.5, 15.4, 1.5, "bone", d=0.8, o=0.7)
    q = ax.P(15.3, 0.7)
    h = math.radians(67.5)
    m.seg(q, (q[0] + math.cos(h) * 2.2, q[1] + math.sin(h) * 2.2), 0.8, 8, 0.7, "bone", tiplight=True)
    blade(m, ax, 5.3, 14.8, 0.5, "venom", d=0.95, o=0.2, noao=True)       # 독 홈
    for s, o in ((9.5, -1.9), (11.0, -2.3), (8.2, -1.7)):
        knob(m, ax.P(s, o), 0.7, "venom", d=0.7)
    return m.save(HANDHELD)


def labrys():
    m = M3("labrys")
    ax = Axis((0.8, 0.8))
    blade(m, ax, 0, 21.0, 1.3, "wood", d=1.3)
    for s in (1.0, 9.0, 15.0):
        blade(m, ax, s, s + 0.7, 1.7, "bronze", d=1.7)
    knob(m, ax.P(17.5), 2.4, "gold", d=2.4, engrave=True)
    for sgn in (1, -1):                                                    # 부채꼴로 넓어지는 초승달 날
        for o, half in ((1.4, 1.3), (2.2, 1.9), (3.0, 2.5), (3.8, 3.0), (4.5, 3.3)):
            m.seg(ax.P(17.5 - half, o * sgn), ax.P(17.5 + half, o * sgn), 0.95, 8, 0.7 if o < 4 else 0.55,
                  "steel", edge=(o >= 4.5))
        m.seg(ax.P(13.9, 4.9 * sgn), ax.P(21.1, 4.9 * sgn), 0.5, 8, 0.45, "silver", noao=True)   # 벼린 날
    p = ax.P(6.0, 0.9)
    m.box((p[0] - 0.8, p[1] - 3.2, 8.3), (p[0] + 0.8, p[1], 8.7), "red")    # 매단 붉은 천
    return m.save(HANDHELD)


def siege_hammer():
    m = M3("siege_hammer")
    ax = Axis((1.0, 1.0))
    blade(m, ax, 0, 18.2, 1.5, "wood", d=1.5)
    blade(m, ax, 0, 1.0, 1.9, "steel", d=1.9)
    blade(m, ax, 14.0, 14.8, 2.0, "steel", d=2.0)
    cross(m, ax, 18.0, 4.2, 4.2, "bronze", d=4.2, engrave=True)
    for sgn in (1, -1):                                                    # 치는 면 (쇠)
        m.seg(ax.P(18.0, 4.2 * sgn), ax.P(18.0, 5.0 * sgn), 4.6, 8, 4.6, "dsteel")
    for zc in (10.35, 5.65):                                                # 숫양 뿔 말림
        p = ax.P(18.0, 1.6)
        m.box((p[0] - 1.1, p[1] - 1.1, zc - 0.25), (p[0] + 1.1, p[1] + 1.1, zc + 0.25), "gold")
        p = ax.P(18.0, -1.6)
        m.box((p[0] - 0.8, p[1] - 0.8, zc - 0.25), (p[0] + 0.8, p[1] + 0.8, zc + 0.25), "gold")
    return m.save(HANDHELD)


def scylla_trident():
    m = M3("scylla_trident")
    ax = Axis((0.6, 0.6))
    blade(m, ax, 0, 1.2, 1.4, "bronze", d=1.4)
    blade(m, ax, 1.0, 16.2, 1.0, "teal", d=1.0)
    for i, s in enumerate((3.0, 4.6, 6.2, 7.8, 9.4, 11.0)):
        knob(m, ax.P(s, 0.55 if i % 2 else -0.55), 0.9, "purple", z=8 + (0.3 if i % 2 else -0.3))
    cross(m, ax, 16.2, 2.8, 0.9, "bronze", d=1.3, engrave=True)
    blade(m, ax, 16.2, 22.0, 0.8, "steel", d=0.8, tiplight=True)
    for o in (2.5, -2.5):
        blade(m, ax, 16.2, 20.6, 0.7, "steel", d=0.7, o=o, tiplight=True)
        m.seg(ax.P(20.0, o), ax.P(19.2, o * 0.72), 0.5, 8, 0.5, "steel")  # 미늘
    m.seg(ax.P(21.2), ax.P(20.4, 0.7), 0.5, 8, 0.5, "steel")
    return m.save(HANDHELD)


# ═════════════════════════════════════════ 창 (도루)
def spear_parts(m, ax):
    blade(m, ax, 0, 2.0, 0.9, "bronze", d=0.9)                            # 사우로테르
    blade(m, ax, 1.8, 17.6, 0.8, "wood", d=0.8)
    blade(m, ax, 17.5, 18.6, 1.1, "bronze", d=1.1)
    for s0, s1, w in ((18.5, 19.8, 1.7), (19.8, 21.2, 2.4), (21.2, 22.2, 1.4), (22.1, 23.0, 0.6)):
        blade(m, ax, s0, s1, w, "steel", d=0.7, edge=True)
    blade(m, ax, 18.7, 22.4, 0.4, "silver", d=0.85, noao=True)


def dory():
    m = M3("dory")
    spear_parts(m, Axis((-0.2, -0.2)))
    return m.save(dict(HANDHELD, gui={"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.72, 0.72, 0.72]}))


def dory_in_hand():
    m = M3("dory_in_hand")
    spear_parts(m, Axis((16.4, -0.4), heading=135))
    disp = dict(SPEAR_HAND)
    disp["ground"] = {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]}
    return m.save(disp)


# ═════════════════════════════════════════ 활 (바닐라 활과 같은 자리 · 방향)
BOW_PATH = [(90, 3.5), (67.5, 3.0), (45, 3.0), (22.5, 3.0), (0, 3.5)]


def bow_model(name, kind, pull):
    m = M3(name)
    k = 1.42
    p = (1.0, 1.2)
    pts = [p]
    for hd, L in BOW_PATH:
        h = math.radians(hd)
        p = (p[0] + math.cos(h) * L * k, p[1] + math.sin(h) * L * k)
        pts.append(p)
    limb = "wood" if kind == "archer" else "bone"
    widths = [0.9, 1.15, 1.45, 1.15, 0.9]
    for i in range(5):
        m.seg(pts[i], pts[i + 1], widths[i], 8, 1.0 if i != 2 else 1.3, limb)
    # 손잡이 감개 (가운데 조각 위)
    g0, g1 = pts[2], pts[3]
    mid = ((g0[0] + g1[0]) / 2, (g0[1] + g1[1]) / 2)
    m.seg((mid[0] - 0.9, mid[1] - 0.9), (mid[0] + 0.9, mid[1] + 0.9), 1.75, 8, 1.55, "leather" if kind == "archer" else "red")
    if kind == "chimera":
        for i in (1, 3):
            a, b = pts[i], pts[i + 1]
            m.seg((a[0] * 0.6 + b[0] * 0.4, a[1] * 0.6 + b[1] * 0.4), (a[0] * 0.3 + b[0] * 0.7, a[1] * 0.3 + b[1] * 0.7),
                  0.4, 8.55, 0.2, "ember", noao=True)
    # 반곡 끝 (시위 반대쪽으로 튕긴 끝)
    b0, t0 = pts[0], pts[-1]
    tipmat = "bronze" if kind == "archer" else "ember"
    m.seg(b0, (b0[0] + 1.3, b0[1] - 1.3), 0.7, 8, 0.8, tipmat)
    m.seg(t0, (t0[0] + 1.3, t0[1] - 1.3), 0.7, 8, 0.8, tipmat)
    # 시위: 쉴 때 = 곧은 대각선 / 당길 때 = 22.5° 씩 꺾인 V
    smat = "string" if kind == "archer" else "red"
    if pull == 0:
        m.seg(b0, t0, 0.28, 8, 0.28, smat, noao=True)
    else:
        half = math.hypot(t0[0] - b0[0], t0[1] - b0[1]) / 2
        c = ((b0[0] + t0[0]) / 2, (b0[1] + t0[1]) / 2)
        off = half * math.tan(math.radians(22.5))
        pp = (c[0] + off * R2, c[1] - off * R2)                      # 시위를 오른쪽 아래로
        m.seg(b0, pp, 0.28, 8, 0.28, smat, noao=True)
        m.seg(pp, t0, 0.28, 8, 0.28, smat, noao=True)
        # 화살 (오른쪽 아래 → 왼쪽 위)
        L = [11.5, 12.2, 12.8][pull - 1]
        tip = (pp[0] - L * R2, pp[1] + L * R2)
        m.seg(pp, tip, 0.4, 8.35, 0.4, "wood")
        head = "steel" if kind == "archer" else "ember"
        m.seg(tip, (tip[0] - 1.4 * R2, tip[1] + 1.4 * R2), 1.1, 8.35, 0.5, head, tiplight=True)
        fl = "white" if kind == "archer" else "red"
        for o in (0.55, -0.55):
            q0 = (pp[0] - 0.4 * R2 + o * R2, pp[1] + 0.4 * R2 + o * R2)
            m.seg(q0, (q0[0] - 2.2 * R2, q0[1] + 2.2 * R2), 0.5, 8.35, 0.2, fl, noao=True)
    return m.save(BOW)


# ═════════════════════════════════════════ 아르테미스의 석궁
def crossbow_model(name, state):
    m = M3(name)
    ax = Axis((15.2, 0.8), heading=135)                                    # 개머리(오른쪽 아래) → 앞(왼쪽 위)
    blade(m, ax, 0, 15.8, 1.9, "black", d=1.6)
    blade(m, ax, 3.0, 15.4, 0.5, "silver", d=1.75, noao=True)             # 레일
    blade(m, ax, 0, 1.2, 2.1, "silver", d=1.8)
    knob(m, ax.P(14.2), 1.8, "moon", d=2.0, gem=True)                      # 초승달 보석
    c = ax.P(13.2)
    # 활대: 축에 수직(45°)으로, 끝이 뒤(315°)로 휜다
    up = [(45, 3.0), (22.5, 3.4)]
    dn = [(225, 3.0), (247.5, 3.4)]
    tips = []
    for path in (up, dn):
        p = c
        for i, (hd, L) in enumerate(path):
            h = math.radians(hd)
            q = (p[0] + math.cos(h) * L, p[1] + math.sin(h) * L)
            m.seg(p, q, 1.2 if i == 0 else 0.9, 8, 1.0, "silver")
            p = q
        tips.append(p)
    # 시위: 끝에서 걸쇠까지 (쉴 때 45°, 당길 때 22.5° → 걸쇠가 뒤로)
    back = (math.cos(math.radians(315)), math.sin(math.radians(315)))
    ang = 45 if state == "standby" else 22.5
    t_up, t_dn = tips
    mid = ((t_up[0] + t_dn[0]) / 2, (t_up[1] + t_dn[1]) / 2)
    half = math.hypot(t_up[0] - t_dn[0], t_up[1] - t_dn[1]) / 2
    dist = half / math.tan(math.radians(ang))
    latch = (mid[0] + back[0] * dist, mid[1] + back[1] * dist)
    m.seg(t_up, latch, 0.28, 8.9, 0.28, "string", noao=True)
    m.seg(t_dn, latch, 0.28, 8.9, 0.28, "string", noao=True)
    knob(m, latch, 0.9, "silver", z=8.9)
    if state == "arrow":
        front = ax.P(16.4)
        m.seg(latch, front, 0.45, 9.0, 0.45, "gold")
        m.seg(front, (front[0] - 1.3 * R2, front[1] + 1.3 * R2), 1.0, 9.0, 0.5, "silver", tiplight=True)
    return m.save(CROSSBOW)


# ═════════════════════════════════════════ 투구 · 유물 (입체 아이콘)
def helmet(name, metal, crest, eye=None):
    m = M3(name)
    # 투구 몸통 (앞 = -z 쪽, 인벤토리에선 3/4 로 보인다)
    m.box((4, 3, 4), (12, 11, 12), metal, engrave=(metal == "bronze"))
    m.box((4.5, 11, 4.5), (11.5, 12.5, 11.5), metal)
    m.box((5.5, 12.5, 5.5), (10.5, 13.2, 10.5), metal)
    m.box((3.6, 1, 3.6), (6.2, 7, 5.2), metal)                            # 뺨가리개
    m.box((9.8, 1, 3.6), (12.4, 7, 5.2), metal)
    m.box((7.3, 2.5, 3.4), (8.7, 8.2, 4.2), metal)                        # 코가리개
    m.box((4.8, 7.2, 3.7), (7.1, 8.4, 4.1), eye or "black", noao=True)    # 눈구멍
    m.box((8.9, 7.2, 3.7), (11.2, 8.4, 4.1), eye or "black", noao=True)
    m.box((4, 3, 11.8), (12, 6, 12.6), metal)                             # 목가리개
    # 말총 볏: 앞에서 뒤로 휘는 줄
    m.box((7.2, 13, 3.4), (8.8, 15.4, 12.6), crest)
    m.box((7.2, 12, 12.4), (8.8, 14.6, 14.2), crest)
    m.box((7.2, 10.2, 13.8), (8.8, 12.6, 15.2), crest)
    m.box((7.0, 15.2, 4.2), (9.0, 15.9, 11.8), crest)
    m.mirror_z()
    return m.save(dict(GENERATED, gui={"rotation": [18, 35, 0], "translation": [0, 0.5, 0], "scale": [1.0, 1.0, 1.0]}))


def lion_pelt():
    m = M3("lion_pelt")
    m.box((2.5, 1.0, 7.0), (13.5, 11.0, 8.4), "fur")                      # 망토
    for x0, y0 in ((2.5, -0.8), (5.7, -1.4), (9.0, -1.0), (11.6, -0.6)):
        m.box((x0, y0, 7.1), (x0 + 1.8, 1.2, 8.3), "fur")                 # 너덜한 끝
    m.box((3.0, 8.0, 5.0), (13.0, 15.5, 9.5), "mane")                      # 갈기
    m.box((5.0, 9.0, 3.4), (11.0, 14.5, 7.0), "fur")                       # 얼굴
    m.box((6.3, 9.2, 2.4), (9.7, 11.6, 3.6), "fur")                        # 주둥이
    m.box((7.4, 11.0, 2.2), (8.6, 11.8, 2.6), "black")                     # 코
    m.box((5.8, 12.4, 3.2), (6.9, 13.3, 3.5), "eye", noao=True)
    m.box((9.1, 12.4, 3.2), (10.2, 13.3, 3.5), "eye", noao=True)
    m.box((4.6, 14.2, 5.2), (6.2, 16.0, 6.8), "mane")                      # 귀
    m.box((9.8, 14.2, 5.2), (11.4, 16.0, 6.8), "mane")
    m.box((6.6, 8.6, 2.6), (7.1, 9.4, 3.3), "white", noao=True)            # 송곳니
    m.box((8.9, 8.6, 2.6), (9.4, 9.4, 3.3), "white", noao=True)
    m.mirror_z()
    return m.save(dict(GENERATED, gui={"rotation": [10, 20, 0], "translation": [0, 0, 0], "scale": [1.0, 1.0, 1.0]}))


def cerberus_collar():
    m = M3("cerberus_collar")
    c = (8.0, 8.0)
    R = 5.2
    for k in range(8):
        a0 = math.radians(k * 45 + 22.5)
        a1 = math.radians(k * 45 + 67.5)
        p0 = (c[0] + math.cos(a0) * R, c[1] + math.sin(a0) * R)
        p1 = (c[0] + math.cos(a1) * R, c[1] + math.sin(a1) * R)
        m.seg(p0, p1, 1.8, 8, 2.2, "black")
        am = math.radians(k * 45 + 45)
        pm = (c[0] + math.cos(am) * (R - 0.2), c[1] + math.sin(am) * (R - 0.2))
        tip = (c[0] + math.cos(am) * (R + 2.6), c[1] + math.sin(am) * (R + 2.6))
        m.seg(pm, tip, 0.9, 8, 0.9, "steel", tiplight=True)                # 가시
        knob(m, (c[0] + math.cos(a0) * R, c[1] + math.sin(a0) * R), 0.7, "bronze", z=9.2, d=0.4)
    for k, a in enumerate((-90, -135, -45)):
        h = math.radians(a)
        knob(m, (c[0] + math.cos(h) * R, c[1] + math.sin(h) * R), 1.5, "soul", z=9.3, d=0.8, gem=True)
    return m.save(dict(GENERATED, gui={"rotation": [25, 0, 0], "translation": [0, 0, 0], "scale": [0.95, 0.95, 0.95]}))


def medusa_head():
    m = M3("medusa_head")
    m.box((4.5, 3.5, 4.5), (11.5, 11.0, 11.5), "skin")
    m.box((5.4, 6.4, 4.1), (7.4, 7.6, 4.5), "eye", noao=True)
    m.box((8.6, 6.4, 4.1), (10.6, 7.6, 4.5), "eye", noao=True)
    m.box((7.4, 5.2, 3.9), (8.6, 7.4, 4.5), "skin")                        # 코
    m.box((6.2, 4.2, 4.2), (9.8, 4.9, 4.5), "red", noao=True)              # 입
    m.box((5.0, 1.8, 5.0), (11.0, 3.6, 11.0), "red")                       # 잘린 목
    for k in range(9):
        a = math.radians(0 + k * 22.5)
        base = (8 + math.cos(a) * 3.2, 10.6 + math.sin(a) * 1.0)
        tip = (8 + math.cos(a) * 7.0, 11.0 + math.sin(a) * 5.0)
        z = 6.0 + (k % 3) * 2.0
        m.seg(base, tip, 1.0, z, 1.0, "green")
        knob(m, tip, 1.4, "green", z=z, d=1.6)
        knob(m, (tip[0], tip[1] + 0.2), 0.4, "eye", z=z - 0.8, d=0.2, noao=True)
    m.mirror_z()
    return m.save(dict(GENERATED, gui={"rotation": [8, 25, 0], "translation": [0, -0.5, 0], "scale": [0.95, 0.95, 0.95]}))


def golden_apple():
    m = M3("golden_apple")
    for (x0, y0, z0), (x1, y1, z1) in (((4.2, 1.8, 4.2), (11.8, 12.0, 11.8)), ((3.2, 3.0, 5.0), (12.8, 10.8, 11.0)),
                                         ((5.0, 3.0, 3.2), (11.0, 10.8, 12.8)), ((2.7, 4.6, 6.0), (13.3, 9.4, 10.0)),
                                         ((6.0, 4.6, 2.7), (10.0, 9.4, 13.3)), ((3.7, 2.4, 3.7), (12.3, 11.4, 12.3)),
                                         ((5.4, 1.0, 5.4), (10.6, 12.5, 10.6))):
        m.box((x0, y0, z0), (x1, y1, z1), "gold")
    m.box((6.8, 11.8, 7.0), (8.4, 12.6, 8.6), "gold")                      # 꼭지 오목
    m.seg((7.6, 12.0), (8.6, 15.0), 0.8, 7.8, 0.8, "wood")
    m.box((8.6, 13.6, 7.5), (12.4, 14.6, 8.1), "leaf")
    m.box((4.3, 9.5, 3.4), (5.3, 10.5, 3.6), "white", noao=True)           # 반짝임
    return m.save(dict(GENERATED, gui={"rotation": [15, 25, 0], "translation": [0, 0, 0], "scale": [1.0, 1.0, 1.0]}))


def olympus_menu():
    m = M3("menu")
    m.box((1.5, 1.0, 4.0), (14.5, 2.2, 12.0), "marble")                    # 기단
    m.box((2.5, 2.2, 5.0), (13.5, 3.2, 11.0), "marble")
    for x in (3.6, 6.2, 8.8, 11.4):
        m.box((x - 0.8, 3.2, 6.2), (x + 0.8, 10.2, 7.8), "marble")          # 기둥
        m.box((x - 1.1, 9.8, 5.9), (x + 1.1, 10.6, 8.1), "gold")
    m.box((2.2, 10.6, 5.2), (13.8, 11.8, 10.8), "marble")                   # 엔타블러처
    m.box((2.2, 11.8, 5.2), (13.8, 12.3, 10.8), "gold")
    for i, (x0, x1) in enumerate(((2.6, 13.4), (4.2, 11.8), (5.8, 10.2), (7.2, 8.8))):
        m.box((x0, 12.3 + i * 0.9, 5.4), (x1, 13.2 + i * 0.9, 10.6), "marble" if i % 2 == 0 else "red")
    return m.save(dict(GENERATED, gui={"rotation": [15, 30, 0], "translation": [0, 0, 0], "scale": [1.0, 1.0, 1.0]}))


def hero_emblem():
    m = M3("hero")
    for a in (0, 22.5, 45, -22.5):                                         # 원판 (돌린 사각 넷 = 16각)
        m.box((2.5, 2.5, 7.3), (13.5, 13.5, 8.7), "bronze", rot={"angle": a, "axis": "z", "origin": [8, 8, 8]} if a else None,
              engrave=True)
    for a in (0, 45):
        m.box((4.0, 4.0, 8.7), (12.0, 12.0, 9.1), "red", rot={"angle": a, "axis": "z", "origin": [8, 8, 8]} if a else None)
    for p0, p1, w in (((10.0, 13.0), (6.5, 8.0), 1.4), ((6.5, 8.0), (9.5, 8.0), 1.2), ((9.5, 8.0), (6.0, 3.0), 1.4)):
        m.seg(p0, p1, w, 9.6, 1.0, "gold", tiplight=True)                  # 번개
    return m.save(dict(GENERATED, gui={"rotation": [0, 15, 0], "translation": [0, 0, 0], "scale": [1.0, 1.0, 1.0]}))


# 키 → 만드는 함수 (build_items 가 부른다)
BUILDERS = {
    "infantry_sword": infantry_sword, "xiphos": xiphos, "kopis": kopis, "dagger": dagger,
    "hephaestus_sword": hephaestus_sword, "hydra_fang": hydra_fang, "labrys": labrys, "siege_hammer": siege_hammer,
    "scylla_trident": scylla_trident, "dory": dory, "dory_in_hand": dory_in_hand,
    "corinthian": lambda: helmet("corinthian", "bronze", "red"),
    "hades_helm": lambda: helmet("hades_helm", "dsteel", "purple", eye="soul"),
    "lion_pelt": lion_pelt, "cerberus_collar": cerberus_collar, "medusa_head": medusa_head,
    "golden_apple": golden_apple, "menu": olympus_menu, "hero": hero_emblem,
}
for _k in ("archer", "chimera"):
    for _p in range(4):
        _n = f"{_k}_bow" + ("" if _p == 0 else f"_pulling_{_p - 1}")
        BUILDERS[_n] = (lambda n=_n, k=_k, p=_p: bow_model(n, k, p))
for _s, _n in (("standby", "artemis_crossbow"), ("pull0", "artemis_crossbow_pulling_0"), ("pull1", "artemis_crossbow_pulling_1"),
               ("pull2", "artemis_crossbow_pulling_2"), ("arrow", "artemis_crossbow_arrow")):
    BUILDERS[_n] = (lambda n=_n, s=_s: crossbow_model(n, s))
