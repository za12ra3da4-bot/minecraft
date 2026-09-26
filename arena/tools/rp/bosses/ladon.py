"""백두룡 라돈 — 헤스페리데스의 황금 사과나무를 지키는 머리 여럿 달린 용.

 다중 지점·순차형: 백두 폭풍(번호 매겨진 원 여러 개가 순서대로 차오르고 머리가 차례로 내리꽂힘),
 독 숨결(부채꼴 → 독 웅덩이 잔존), 황금 사과의 재생(사과 수정 3개를 부수지 않으면 회복)

 파츠: 몸 3 + 다리 12 + 꼬리 10 + 목 5x8 + 머리 5x2 = 75
"""
import numpy as np

from modelkit import *

SCALE = Mat((34, 112, 112), var=0.06, edge_dark=0.30, top_light=0.24, pattern=scales((10, 50, 54), 4, 1.35))
SCALE_L = Mat((74, 150, 136), var=0.06, edge_dark=0.28, top_light=0.22, pattern=scales((24, 80, 76), 4, 1.3))
SCALE_D = Mat((22, 78, 82), var=0.06, edge_dark=0.30, top_light=0.2, pattern=scales((8, 36, 40), 3, 1.3))
BELLY = Mat((232, 204, 118), var=0.04, edge_dark=0.30, top_light=0.12, pattern=stripes((232, 204, 118), (178, 142, 70), 2, vertical=False))
GOLD = Mat((244, 196, 70), var=0.05, edge_dark=0.38, top_light=0.35, pattern=metal((170, 110, 30), 0.35, 0.0))
HORN = Mat((240, 226, 180), var=0.04, edge_dark=0.30, top_light=0.3)
HORN_D = Mat((170, 136, 92), var=0.05, edge_dark=0.30, top_light=0.25)
EYE = Mat((255, 120, 40), var=0.03, edge_dark=0, top_light=0)
MOUTH = Mat((140, 30, 40), var=0.05, edge_dark=0.25)
TOOTH = Mat((248, 246, 232), var=0.02, edge_dark=0.1, top_light=0.1)
FIN = Mat((236, 180, 52), var=0.04, edge_dark=0.35, top_light=0.25, pattern=stripes((236, 180, 52), (180, 112, 30), 2))

HEADS = 5
NSEG = 8
SEGL = 3.6
# (좌우 위치, 요, 기본 들어올림, 길이 배율)
NECKS = [(-8.0, -58, -26, 0.92), (-4.0, -26, -36, 1.06), (0.0, 0, -44, 1.2), (4.0, 26, -36, 1.06), (8.0, 58, -26, 0.92)]
REST = [0, -10, -6, 0, 6, 12, 16, 14]              # 마디별 굽힘 → 부드러운 S자


def pupil(a, w, h):
    a[:, w // 2:w // 2 + 1, :3] = (40, 20, 0)


def head_part(i):
    b = []
    b += rbox((-3.6, -2.0, -2.8), (3.6, 3.8, 4.6), SCALE, r=1.0)                 # 두개골
    b += rbox((-2.8, -1.2, 4.2), (2.8, 2.6, 11.6), SCALE, r=0.9)                 # 위턱
    b += rbox((-3.8, 2.6, -2.0), (3.8, 4.4, 3.8), SCALE_D, r=0.6)                # 눈두덩
    b += [Box((-3.85, 1.2, 1.6), (-3.55, 2.6, 3.6), EYE, {"*": pupil}, glow=True),
          Box((3.55, 1.2, 1.6), (3.85, 2.6, 3.6), EYE, {"*": pupil}, glow=True)]
    b += [Box((-1.6, 2.2, 10.4), (-0.8, 2.7, 11.2), SCALE_D), Box((0.8, 2.2, 10.4), (1.6, 2.7, 11.2), SCALE_D)]  # 콧구멍
    # 뿔: 뒤로 휜 큰 뿔 2 + 작은 뿔 2
    b += [Box((-3.0, 3.4, -6.5), (-1.6, 4.8, 0.5), HORN, rot=("x", 22.5, (-2.3, 4.1, 0.5))),
          Box((1.6, 3.4, -6.5), (3.0, 4.8, 0.5), HORN, rot=("x", 22.5, (2.3, 4.1, 0.5))),
          Box((-2.6, 5.4, -10.2), (-1.8, 6.2, -6.0), HORN_D, rot=("x", 22.5, (-2.2, 5.8, -6.0))),
          Box((1.8, 5.4, -10.2), (2.6, 6.2, -6.0), HORN_D, rot=("x", 22.5, (2.2, 5.8, -6.0)))]
    # 볼 지느러미 (옆으로 벌어짐)
    b += [Box((-4.0, -1.4, -4.0), (-3.4, 3.2, 1.0), FIN, rot=("y", -22.5, (-3.7, 0, 1.0))),
          Box((3.4, -1.4, -4.0), (4.0, 3.2, 1.0), FIN, rot=("y", 22.5, (3.7, 0, 1.0)))]
    # 윗니
    for k in range(5):
        z = 5.2 + k * 1.3
        b += [Box((-2.5, -2.0, z), (-1.9, -1.1, z + 0.6), TOOTH), Box((1.9, -2.0, z), (2.5, -1.1, z + 0.6), TOOTH)]
    b += [Box((-0.6, 4.0, -3.6), (0.6, 5.8, 3.0), GOLD)]
    return Part(f"head{i}", b)


def jaw_part(i):
    b = rbox((-2.4, -1.8, 0), (2.4, 0, 7.4), SCALE_D, r=0.6)
    b += [Box((-2.0, -0.05, 0.3), (2.0, 0.25, 7.0), MOUTH)]
    for k in range(4):
        z = 1.6 + k * 1.4
        b += [Box((-2.1, 0, z), (-1.6, 1.0, z + 0.6), TOOTH), Box((1.6, 0, z), (2.1, 1.0, z + 0.6), TOOTH)]
    b += [Box((-1.6, -2.4, 0.6), (1.6, -1.7, 6.0), BELLY)]
    return Part(f"jaw{i}", b)


def neck_part(name, r, L, spike):
    b = rbox((-r, -r, -0.6), (r, r, L + 0.6), SCALE, r=r * 0.38)
    b += [Box((-r * 0.5, -r - 0.25, 0), (r * 0.5, -r + 0.4, L), SCALE_L)]
    if spike:
        b += [Box((-0.4, r - 0.3, 0.2), (0.4, r + 1.8, L * 0.6), GOLD, rot=("x", -22.5, (0, r, 0.2)))]
    return Part(name, b)


def build():
    P = {}
    P["chest"] = Part("chest", rbox((-11, -7, -2), (11, 8.5, 13), SCALE, r=2.6)
                      + [Box((-9, -7.6, 0), (9, -6.2, 12), BELLY)]
                      + [Box((-0.6, 8, z), (0.6, 11, z + 3), GOLD, rot=("x", -22.5, (0, 8, z))) for z in (0, 4.5, 9)])
    P["belly"] = Part("belly", rbox((-10.4, -6.6, -13), (10.4, 8, 0.6), SCALE, r=2.6)
                      + [Box((-8.6, -7.2, -12), (8.6, -5.8, 0), BELLY)]
                      + [Box((-0.6, 7.6, z), (0.6, 10.6, z + 3), GOLD, rot=("x", -22.5, (0, 7.6, z))) for z in (-12, -7.5, -3)])
    P["hips"] = Part("hips", rbox((-9.4, -6, -11), (9.4, 7.4, 0.6), SCALE, r=2.4)
                     + [Box((-7.4, -6.6, -10), (7.4, -5.2, 0), BELLY)]
                     + [Box((-0.6, 7, z), (0.6, 9.6, z + 3), GOLD, rot=("x", -22.5, (0, 7, z))) for z in (-9, -4.5)])
    for i, (x, yaw, lift, lm) in enumerate(NECKS):
        for s in range(NSEG):
            r = 3.4 - s * 0.16
            P[f"neck{i}_{s}"] = neck_part(f"neck{i}_{s}", r, SEGL * lm, s % 2 == 0)
        P[f"head{i}"] = head_part(i)
        P[f"jaw{i}"] = jaw_part(i)
    P["fu"] = Part("fu", rbox((-3.8, -8, -3.8), (3.8, 2, 3.8), SCALE, r=1.2))
    P["fl"] = Part("fl", rbox((-3.0, -7, -3.0), (3.0, 0.6, 3.0), SCALE_D, r=0.9))
    P["hu"] = Part("hu", rbox((-4.2, -8, -5), (4.2, 2.4, 3.8), SCALE, r=1.4))
    P["hl"] = Part("hl", rbox((-3.1, -7, -2.8), (3.1, 0.6, 3.2), SCALE_D, r=0.9))
    P["foot"] = Part("foot", rbox((-3.8, -2.4, -3.0), (3.8, 0, 4.0), SCALE_D, r=0.7)
                     + [Box((-3.4, -2.5, 3.6), (-2.2, -1.0, 6.2), HORN), Box((-0.6, -2.5, 3.6), (0.6, -1.0, 6.6), HORN),
                        Box((2.2, -2.5, 3.6), (3.4, -1.0, 6.2), HORN)])
    for k in range(10):
        r = 5.0 - k * 0.42
        b = rbox((-r, -r * 0.85, -5.2), (r, r * 0.95, 0.4), SCALE if k % 3 else SCALE_L, r=r * 0.35)
        b += [Box((-r * 0.7, -r * 0.85 - 0.35, -5), (r * 0.7, -r * 0.85 + 0.2, 0), BELLY)]
        if k < 9 and k % 2 == 0:
            b += [Box((-0.4, r * 0.95 - 0.3, -3.8), (0.4, r * 0.95 + 1.6, -1.0), GOLD, rot=("x", -22.5, (0, r * 0.95, -1.0)))]
        if k == 9:
            b += [Box((-3.8, -0.35, -10.5), (3.8, 0.35, -4.5), GOLD), Box((-2.4, -0.4, -12.5), (2.4, 0.4, -10.4), GOLD)]
        P[f"tail{k}"] = Part(f"tail{k}", b)
    parts = list(P.values())

    R = Rig("ladon", 2.0)
    R.bone("belly", None, (0, 15.5, 0), P["belly"])
    R.bone("chest", "belly", (0, 0.4, 0), P["chest"], rest=(-4, 0, 0))
    R.bone("hips", "belly", (0, 0, -12.4), P["hips"], rest=(4, 0, 0))
    for i, (x, yaw, lift, lm) in enumerate(NECKS):
        L = SEGL * lm
        R.bone(f"neck{i}_0", "chest", (x, 4.0 - abs(x) * 0.25, 11.0), P[f"neck{i}_0"], rest=(lift, yaw, 0))
        for s in range(1, NSEG):
            R.bone(f"neck{i}_{s}", f"neck{i}_{s - 1}", (0, 0, L), P[f"neck{i}_{s}"], rest=(REST[s], -yaw * 0.07, 0))
        R.bone(f"head{i}", f"neck{i}_{NSEG - 1}", (0, 0, L + 0.6), P[f"head{i}"], rest=(10, 0, 0), scale=1.3)
        R.bone(f"jaw{i}", f"head{i}", (0, -1.6, 3.6), P[f"jaw{i}"], rest=(10, 0, 0))
    for s, sg in (("l", 1), ("r", -1)):
        R.bone("fu_" + s, "chest", (sg * 9, -3.5, 7), P["fu"], rest=(-12, 0, sg * 10))
        R.bone("fl_" + s, "fu_" + s, (0, -7.6, 0), P["fl"], rest=(22, 0, -sg * 10))
        R.bone("ff_" + s, "fl_" + s, (0, -6.6, 0.4), P["foot"], rest=(-10, 0, 0))
        R.bone("hu_" + s, "hips", (sg * 8.2, -3, -5), P["hu"], rest=(16, 0, sg * 10))
        R.bone("hl_" + s, "hu_" + s, (0, -7.6, -1.2), P["hl"], rest=(-26, 0, -sg * 10))
        R.bone("hf_" + s, "hl_" + s, (0, -6.6, 0.4), P["foot"], rest=(10, 0, 0))
    R.bone("tail0", "hips", (0, 0.8, -10.6), P["tail0"], rest=(8, 0, 0))
    for k in range(1, 10):
        R.bone(f"tail{k}", f"tail{k - 1}", (0, 0, -5.0), P[f"tail{k}"], rest=(3 if k < 4 else -2, 0, 0))
    return R, parts, anims()


# ─────────────────────────────────────────────────────────────────────────────
def P_(*ds, **kw):
    out = {}
    for d in ds:
        out.update(d)
    out.update(kw)
    return out


def curve(total_pitch, bend=0.0):
    """목 전체 굽힘: total_pitch 를 마디에 나눠 준다 (+ = 앞/아래로)"""
    return [total_pitch / NSEG + bend * np.sin(s / (NSEG - 1) * np.pi) for s in range(NSEG)]


def neck_pose(i, add, yaw=0.0, head=0.0, jaw=0.0, t=0.0, amp=1.0):
    d = {}
    for s in range(NSEG):
        wob = amp * 3.2 * np.sin(t + i * 1.3 - s * 0.55)
        d[f"neck{i}_{s}"] = (add[s] + wob, (yaw if s == 0 else 0) + amp * 3 * np.sin(t * 0.8 + i * 0.9 - s * 0.5), 0)
    d[f"head{i}"] = (head - amp * 4 * np.sin(t + i * 1.3 - NSEG * 0.55), 0, 0)
    d[f"jaw{i}"] = (jaw + amp * (3 + 4 * np.sin(t * 1.3 + i)), 0, 0)
    return d


def all_necks(add, t=0.0, head=0.0, jaw=0.0, amp=1.0, yaws=None):
    d = {}
    for i in range(HEADS):
        d.update(neck_pose(i, add, yaws[i] if yaws else 0, head, jaw, t, amp))
    return d


ZERO = [0.0] * NSEG
RAISE = curve(-22, -4)             # 치켜듦
STRIKE = curve(62, 10)              # 내리꽂음


def tail(t, a=8):
    return {f"tail{k}": (0, a * np.sin(t - k * 0.5), 0) for k in range(10)}


def legs_walk(s):
    return {"fu_l": (-22 * s, 0, 0), "fu_r": (22 * s, 0, 0), "fl_l": (14 * max(0, s), 0, 0), "fl_r": (14 * max(0, -s), 0, 0),
            "hu_l": (22 * s, 0, 0), "hu_r": (-22 * s, 0, 0), "hl_l": (-14 * max(0, -s), 0, 0), "hl_r": (-14 * max(0, s), 0, 0)}


def anims():
    A = {}
    A["idle"] = dict(loop=True, keys=[(P_(all_necks(ZERO, t), tail(t), chest=(-4 + 1.2 * np.sin(t), 0, 0), _root=(0, 0.3 * np.sin(t), 0)), 8)
                                      for t in np.linspace(0, 2 * np.pi, 7)[:-1]])
    walk = []
    for k in range(6):
        ph = k / 6 * 2 * np.pi
        s = np.sin(ph)
        walk.append((P_(all_necks(ZERO, ph, amp=0.8), tail(ph, 14), legs_walk(s),
                        chest=(-4, 5 * s, 0), hips=(4, -5 * s, 0), _root=(0, -0.4 * abs(np.cos(ph)), 0)), 4))
    A["walk"] = dict(loop=True, keys=walk)

    def one(i, add, head=0.0, jaw=0.0):
        d = all_necks(ZERO, 0, amp=0.4)
        d.update(neck_pose(i, add, 0, head, jaw, 0, 0.1))
        return d
    A["bite"] = dict(loop=False, keys=[(P_(one(2, RAISE, -20, 46)), 6), (P_(one(2, STRIKE, 24, 4)), 3),
                                       (P_(one(2, STRIKE, 24, 4)), 5), (P_(all_necks(ZERO)), 8)])
    order = [2, 0, 4, 1, 3]
    storm = [(P_(all_necks(RAISE, head=18, jaw=46, amp=0.4), chest=(-10, 0, 0), _root=(0, 0.8, 0)), 14)]
    struck = []
    for i in order:
        struck.append(i)
        d = all_necks(RAISE, head=18, jaw=46, amp=0.4)
        for j in struck:
            d.update(neck_pose(j, STRIKE, 0, 24, 6, 0, 0.1))
        storm.append((P_(d, chest=(2, 0, 0)), 5))
    storm.append((P_(all_necks(ZERO)), 12))
    A["storm"] = dict(loop=False, keys=storm)
    FWD = curve(8, 2)
    NARROW = [-v * 0.5 for v in (-58, -26, 0, 26, 58)]
    A["venom"] = dict(loop=False, keys=[
        (P_(all_necks(curve(-24), head=-16, jaw=14, amp=0.3, yaws=NARROW), chest=(-12, 0, 0)), 12),
        (P_(all_necks(FWD, head=-12, jaw=56, amp=0.2, yaws=NARROW), chest=(2, 0, 0), _root=(0, -0.5, 1)), 4),
        (P_(all_necks(FWD, head=-12, jaw=60, amp=0.5, yaws=NARROW), chest=(2, 0, 0), _root=(0, -0.5, 1)), 30),
        (P_(all_necks(ZERO)), 10),
    ])
    UP = curve(-40, -14)
    A["apple"] = dict(loop=False, keys=[
        (P_(all_necks(UP, head=-30, jaw=54, amp=0.6), chest=(-18, 0, 0), _root=(0, 1.5, 0)), 12),
        (P_(all_necks(UP, 1.5, head=-34, jaw=60, amp=1.0), chest=(-20, 0, 0), _root=(0, 1.6, 0)), 30),
        (P_(all_necks(ZERO)), 12),
    ])
    DOWN = curve(70, 10)
    A["stun"] = dict(loop=False, keys=[
        (P_(all_necks(DOWN, head=10, jaw=24, amp=0.2), chest=(8, 0, 8), _root=(0, -3, 0)), 8),
        (P_(all_necks(DOWN, 1, head=12, jaw=28, amp=0.4), chest=(10, 0, 10), _root=(0, -3.2, 0)), 30),
    ])
    A["death"] = dict(loop=False, keys=[
        (P_(all_necks(curve(80, 10), head=10, jaw=30, amp=0.1), chest=(10, 0, 20), _root=(0, -5, 0)), 16),
        (P_(all_necks(curve(100, 10), head=10, jaw=30, amp=0.0), chest=(10, 0, 50), _root=(0, -8, 0)), 14),
    ])
    return A


INFO = dict(hitbox="iron_golem", hit_scale=2.4, portrait=dict(bone="head2", dist=2.1, cy=0.5, cz=6.0))
