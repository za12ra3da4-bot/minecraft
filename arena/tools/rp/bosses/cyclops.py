"""외눈 거인 키클롭스 — 채석장을 지배하는 거인. 끊어진 족쇄를 찬 채 쇠가시 곤봉을 휘두른다.

 근접 광역·추적형: 대지 진동(발 구르기 → 자기 주변 동심원 3겹이 안→밖 순서로 터짐),
 거암 추격(한 명을 3초간 따라다니는 원 → 고정 → 바위 낙하), 회전 강타(곤봉을 뻗고 두 바퀴 회전)

 파츠: 몸 4 + 머리 3 + 가죽 2 + 팔 16 + 사슬 6 + 곤봉 1 + 다리 6 + 허리천 4 + 머리칼 1 = 43
"""
import numpy as np

from modelkit import *

SKIN = Mat((136, 150, 118), var=0.06, edge_dark=0.30, top_light=0.26, spots=((104, 118, 90), 0.26, 3))
SKIN_D = Mat((106, 120, 90), var=0.06, edge_dark=0.30, top_light=0.24, spots=((84, 96, 70), 0.22, 3))
SKIN_L = Mat((168, 176, 140), var=0.04, edge_dark=0.26, top_light=0.2)
LEATHER = Mat((124, 78, 44), var=0.05, edge_dark=0.30, top_light=0.2, pattern=lambda a, f, w, h, r: _stitch(a, w, h))
FURD = Mat((74, 56, 44), var=0.05, edge_dark=0.25, top_light=0.24, pattern=fur((48, 34, 26), (112, 86, 64)))
IRON = Mat((78, 78, 86), var=0.05, edge_dark=0.30, top_light=0.3, pattern=metal((120, 70, 40), 0.3, 0.06))
WOOD = Mat((122, 84, 48), var=0.05, edge_dark=0.30, top_light=0.2, pattern=stripes((122, 84, 48), (92, 60, 32), 1, vertical=False))
BONE = Mat((232, 224, 204), var=0.03, edge_dark=0.28, top_light=0.24)
HORN = Mat((70, 58, 52), var=0.04, edge_dark=0.3, top_light=0.3)
ROPE = Mat((176, 146, 96), var=0.05, edge_dark=0.25, pattern=stripes((176, 146, 96), (130, 102, 62), 1))
EYE = Mat((255, 184, 60), var=0.02, edge_dark=0.0, top_light=0.0)
MOUTH = Mat((70, 30, 30), var=0.04, edge_dark=0.2)
HAIR = Mat((52, 44, 40), var=0.05, edge_dark=0.25, pattern=fur((30, 26, 24), (84, 72, 64)))


def _stitch(a, w, h):
    if h < 4:
        return
    for x in range(1, w - 1, 2):
        a[1, x, :3] = (200, 170, 120)
        a[h - 2, x, :3] = (200, 170, 120)


def eye_face(a, w, h):
    """세로 동공 + 홍채 고리"""
    cx, cy = w / 2, h / 2
    for y in range(h):
        for x in range(w):
            d = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5 / (w / 2)
            if d > 1:
                a[y, x, :3] = (236, 226, 200)
            else:
                a[y, x, :3] = np.array((255, 236, 140)) * (1 - d) + np.array((230, 110, 20)) * d
    for y in range(h):
        for x in range(w):
            if ((x + 0.5 - cx) ** 2 + ((y + 0.5 - cy) * 1.3) ** 2) ** 0.5 < w * 0.16:
                a[y, x, :3] = (30, 10, 4)


def face_front(a, w, h):
    cx = w // 2
    a[int(h * 0.25), 2:w - 2, :3] *= 0.55          # 콧잔등 주름
    a[int(h * 0.62), cx - 2:cx - 1, :3] = (40, 36, 40)
    a[int(h * 0.62), cx + 1:cx + 2, :3] = (40, 36, 40)


def belly_face(a, w, h):
    cx = w // 2
    a[int(h * 0.55):int(h * 0.55) + 1, cx:cx + 1, :3] *= 0.5   # 배꼽
    for y in range(h):
        a[y, 0:2, :3] *= 0.85; a[y, w - 2:w, :3] *= 0.85


def build():
    P = {}
    P["pelvis"] = Part("pelvis", rbox((-7, -3, -4.6), (7, 3.6, 4.6), SKIN_D, r=1.4)
                       + [Box((-7.5, 1.6, -5.0), (7.5, 3.4, 5.0), ROPE)]
                       + rbox((-1.8, 1.0, 4.8), (1.8, 4.0, 6.6), BONE, r=0.6))
    P["belly"] = Part("belly", rbox((-9.2, -0.5, -5.6), (9.2, 10, 9.0), SKIN, {"south": belly_face}, r=3.4))
    P["chest"] = Part("chest", rbox((-10.6, 0, -6.2), (10.6, 10.5, 6.2), SKIN, r=2.8)
                      + rbox((-8.6, 3, 5.0), (-0.4, 9.6, 7.0), SKIN_L, r=1.0) + rbox((0.4, 3, 5.0), (8.6, 9.6, 7.0), SKIN_L, r=1.0)
                      + [Box((-9, 7.4, -7.0), (9, 9.6, -5.8), LEATHER)])
    P["head"] = Part("head", [
        *rbox((-5.0, -1.0, -4.4), (5.0, 8.4, 4.4), SKIN, {"south": face_front}, r=1.8),
        *rbox((-5.4, 6.4, 2.6), (5.4, 8.2, 5.6), SKIN_D, r=0.8),              # 한 줄 눈썹 뼈
        Box((-3.8, 2.2, 4.3), (3.8, 6.8, 4.7), MOUTH),                         # 눈구멍 그늘
        *rbox((-1.2, 0.2, 4.3), (1.2, 2.2, 6.2), SKIN_L, r=0.5),               # 코 (눈 아래)
        Box((-0.9, 8.2, -1.6), (0.9, 12.4, 0.8), HORN, rot=("x", -22.5, (0, 8.2, -0.4))),
        Box((-6.0, 2.6, -1.2), (-4.8, 5.4, 1.2), SKIN_D), Box((4.8, 2.6, -1.2), (6.0, 5.4, 1.2), SKIN_D),   # 귀
    ])
    P["eye"] = Part("eye", [Box((-3.0, -2.0, 0), (3.0, 2.0, 0.6), EYE, {"south": eye_face}, glow=True)])
    P["jaw"] = Part("jaw", rbox((-4.6, -3.2, -1.0), (4.6, 0, 5.4), SKIN_D, r=1.2) + [
        Box((-3.6, -0.3, 0.4), (3.6, 0.2, 5.0), MOUTH),
        Box((-3.8, -0.2, 3.6), (-2.8, 3.4, 4.6), BONE, rot=("x", 22.5, (-3.3, 0, 4.1))),
        Box((2.8, -0.2, 3.6), (3.8, 3.4, 4.6), BONE, rot=("x", 22.5, (3.3, 0, 4.1))),
        *rbox((-2.4, -6.0, 1.0), (2.4, -2.6, 5.0), HAIR, r=0.8),              # 턱수염
    ])
    P["hair"] = Part("hair", rbox((-2.2, 0, -3.4), (2.2, 4.4, 1.8), HAIR, r=0.8) + [Box((-1.0, -0.6, -4.4), (1.0, 3.0, -2.6), HAIR)])
    for s, sg in (("l", 1), ("r", -1)):
        mb = rbox((-6.0, -5.5, -6.4), (6.0, 2.4, 6.4), FURD, r=2.2) + rbox((-4.8, -7.5, -5.0), (4.8, -4.5, 5.0), FURD, r=1.6)
        if s == "l":
            mb += rbox((-2.6, 2.6, -2.6), (2.6, 6.2, 2.8), BONE, r=1.0) + [Box((-1.7, 3.8, 2.7), (-0.5, 5.0, 2.95), MOUTH), Box((0.5, 3.8, 2.7), (1.7, 5.0, 2.95), MOUTH)]
        P["mantle_" + s] = Part("mantle_" + s, mb)
    P["upper"] = Part("upper", rbox((-4.2, -12.5, -4.2), (4.2, 1.5, 4.2), SKIN, r=1.8))
    P["fore"] = Part("fore", rbox((-3.6, -11, -3.6), (3.6, 0.6, 3.6), SKIN, r=1.4)
                     + rbox((-4.2, -9.6, -4.2), (4.2, -6.4, 4.2), IRON, r=0.8)
                     + [Box((-3.8, -3, -3.8), (3.8, -1.4, 3.8), ROPE)])
    P["palm"] = Part("palm", rbox((-3.4, -4.6, -2.4), (3.4, 0, 3.0), SKIN_D, r=1.0))
    P["finger"] = Part("finger", rbox((-0.85, -4.6, -1.0), (0.85, 0, 1.0), SKIN_D, r=0.35) + [Box((-0.7, -4.8, 0.2), (0.7, -4.0, 1.1), BONE)])
    P["thumb"] = Part("thumb", rbox((-1.0, -3.8, -1.0), (1.0, 0, 1.0), SKIN_D, r=0.35))
    P["link"] = Part("link", [Box((-0.5, -3.4, -1.1), (0.5, 0, 1.1), IRON), Box((-1.1, -3.4, -0.5), (1.1, -2.2, 0.5), IRON)])
    club = rbox((-1.4, -12, -1.4), (1.4, 3, 1.4), WOOD, r=0.5)
    club += rbox((-4.2, -30, -4.2), (4.2, -11, 4.2), WOOD, r=1.8)
    club += [Box((-4.5, -15.4, -4.5), (4.5, -13.4, 4.5), IRON), Box((-4.5, -24.4, -4.5), (4.5, -22.4, 4.5), IRON)]
    for yy in (-19, -27):
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            lo = (dx * 4.0 - 0.7 + min(0, dx) * 1.8, yy - 0.7, dz * 4.0 - 0.7 + min(0, dz) * 1.8)
            hi = (dx * 4.0 + 0.7 + max(0, dx) * 1.8, yy + 0.7, dz * 4.0 + 0.7 + max(0, dz) * 1.8)
            club.append(Box(lo, hi, IRON))
    P["club"] = Part("club", club)
    P["thigh"] = Part("thigh", rbox((-4.2, -10, -4.2), (4.2, 1, 4.2), SKIN, r=1.6))
    P["shin"] = Part("shin", rbox((-3.6, -9, -3.6), (3.6, 0.5, 3.6), SKIN_D, r=1.2)
                     + [Box((-3.9, -7.6, -3.9), (3.9, -6.4, 3.9), ROPE), Box((-3.9, -4.6, -3.9), (3.9, -3.4, 3.9), ROPE)])
    P["foot"] = Part("foot", rbox((-3.8, -2.6, -3.8), (3.8, 0.4, 6.8), SKIN_D, r=1.0)
                     + [Box((-3.4 + k * 2.2, -2.7, 6.2), (-2.2 + k * 2.2, -1.4, 7.4), BONE) for k in range(4)])
    for k, (L, w_) in enumerate(((7, 9.6), (6, 8.6))):
        P[f"cloth_f{k}"] = Part(f"cloth_f{k}", [Box((-w_ / 2, -L, -0.35), (w_ / 2, 0, 0.35), LEATHER)])
        P[f"cloth_b{k}"] = Part(f"cloth_b{k}", [Box((-w_ / 2, -L, -0.35), (w_ / 2, 0, 0.35), FURD)])
    parts = list(P.values())

    R = Rig("cyclops", 2.2)
    R.bone("pelvis", None, (0, 19, 0), P["pelvis"])
    R.bone("belly", "pelvis", (0, 3, 0), P["belly"], rest=(12, 0, 0))
    R.bone("chest", "belly", (0, 8.8, -0.8), P["chest"], rest=(26, 0, 0))
    R.bone("head", "chest", (0, 10.4, 5.0), P["head"], rest=(-40, 0, 0), scale=1.2)
    R.bone("eye", "head", (0, 4.5, 4.95), P["eye"])
    R.bone("jaw", "head", (0, 0.4, 0.2), P["jaw"], rest=(4, 0, 0))
    R.bone("hair", "head", (0, 8.2, -1.2), P["hair"], rest=(-10, 0, 0))
    R.bone("cloth_f0", "pelvis", (0, 1.4, 5.2), P["cloth_f0"])
    R.bone("cloth_f1", "cloth_f0", (0, -6.8, 0), P["cloth_f1"])
    R.bone("cloth_b0", "pelvis", (0, 1.4, -5.2), P["cloth_b0"])
    R.bone("cloth_b1", "cloth_b0", (0, -5.8, 0), P["cloth_b1"])
    for s, sg in (("l", 1), ("r", -1)):
        R.bone("mantle_" + s, "chest", (sg * 9.4, 9.0, 0), P["mantle_" + s], rest=(0, 0, sg * 10))
        R.bone("upper_" + s, "chest", (sg * 12.6, 7.0, 0), P["upper"], rest=(-26, 0, sg * 10))
        R.bone("fore_" + s, "upper_" + s, (0, -12.4, 0), P["fore"], rest=(-24, 0, -sg * 4))
        R.bone("palm_" + s, "fore_" + s, (0, -10.8, 0), P["palm"])
        for f in range(4):
            R.bone(f"finger{f}_" + s, "palm_" + s, (-2.4 + f * 1.6, -4.4, 1.8), P["finger"], rest=(-60, 0, 0))
        R.bone("thumb_" + s, "palm_" + s, (-sg * 3.2, -1.6, 2.2), P["thumb"], rest=(-40, 0, -sg * 30))
        R.bone("chain0_" + s, "fore_" + s, (sg * 3.6, -8.2, 1.0), P["link"])
        R.bone("chain1_" + s, "chain0_" + s, (0, -3.2, 0), P["link"], rest=(0, 90, 0))
        R.bone("chain2_" + s, "chain1_" + s, (0, -3.2, 0), P["link"], rest=(0, 90, 0))
        R.bone("thigh_" + s, "pelvis", (sg * 4.4, -1.6, 0), P["thigh"], rest=(-6, 0, sg * 4))
        R.bone("shin_" + s, "thigh_" + s, (0, -10, 0), P["shin"], rest=(10, 0, -sg * 4))
        R.bone("foot_" + s, "shin_" + s, (0, -8.8, 0), P["foot"], rest=(-4, 0, 0))
    R.bone("club", "palm_r", (0, -3.0, 0.6), P["club"], rest=(-60, 0, 0))
    return R, parts, anims()


# ─────────────────────────────────────────────────────────────────────────────
def P_(*ds, **kw):
    out = {}
    for d in ds:
        out.update(d)
    out.update(kw)
    return out


def arms(ul=0, ur=0, zl=0, zr=0, fl=0, fr=0, yl=0, yr=0):
    return {"upper_l": (ul, yl, zl), "upper_r": (ur, yr, zr), "fore_l": (fl, 0, 0), "fore_r": (fr, 0, 0)}


def legs(tl=0, tr_=0, sl=0, sr=0, fl=0, fr=0):
    return {"thigh_l": (tl, 0, 0), "thigh_r": (tr_, 0, 0), "shin_l": (sl, 0, 0), "shin_r": (sr, 0, 0), "foot_l": (fl, 0, 0), "foot_r": (fr, 0, 0)}


def hands(cl=0.0, cr=1.0):
    d = {}
    for s, c in (("l", cl), ("r", cr)):
        for f in range(4):
            d[f"finger{f}_{s}"] = (-c * 60, 0, 0)
        d["thumb_" + s] = (-c * 30, 0, 0)
    return d


def swing(t, a=1.0):
    d = {}
    for s in ("l", "r"):
        for k in range(3):
            d[f"chain{k}_{s}"] = (a * 8 * np.sin(t + k * 0.7), 0, a * 6 * np.sin(t * 0.8 + k))
    d["cloth_f0"] = (a * 4 * np.sin(t), 0, 0); d["cloth_f1"] = (a * 6 * np.sin(t - 0.6), 0, 0)
    d["cloth_b0"] = (-a * 4 * np.sin(t), 0, 0); d["cloth_b1"] = (-a * 6 * np.sin(t - 0.6), 0, 0)
    return d


def anims():
    A = {}
    A["idle"] = dict(loop=True, keys=[(P_(arms(2 * np.sin(t), 2 * np.sin(t)), hands(0.4, 1), swing(t, 0.6),
                                          chest=(1.5 * np.sin(t), 0, 0), head=(-1.5 * np.sin(t), 0, 0), jaw=(2 + 2 * np.sin(t), 0, 0),
                                          club=(2 * np.sin(t), 0, 0), _root=(0, 0.4 * np.sin(t), 0)), 12)
                                      for t in np.linspace(0, 2 * np.pi, 5)[:-1]])
    walk = []
    for i in range(6):
        ph = i / 6 * 2 * np.pi
        s = np.sin(ph)
        walk.append((P_(legs(-24 * s, 24 * s, 20 * max(0, s) + 4, 20 * max(0, -s) + 4, 4 * s, -4 * s), arms(18 * s, -14 * s), hands(0.5, 1),
                        swing(ph * 2, 1.4), chest=(3, 6 * s, 3 * s), head=(0, -5 * s, 0), _root=(0, -1.0 * abs(np.cos(ph)), 0)), 5))
    A["walk"] = dict(loop=True, keys=walk)
    # 기본: 곤봉 내려찍기
    A["slam"] = dict(loop=False, keys=[
        (P_(arms(0, -170, 0, -10, 0, -20), hands(0.4, 1), swing(0, 1), chest=(-12, 12, 0), head=(-8, -8, 0), club=(50, 0, 0)), 10),
        (P_(arms(-20, -50, 0, -6, 0, -10), hands(0.4, 1), swing(1, 1.5), chest=(30, -8, 0), head=(-14, 6, 0), club=(-20, 0, 0), _root=(0, -2.4, 1.5)), 3),
        (P_(arms(-20, -46, 0, -6, 0, -10), hands(0.4, 1), swing(2, 1.2), chest=(30, -8, 0), head=(-14, 6, 0), club=(-24, 0, 0), _root=(0, -2.4, 1.5)), 8),
        (P_(arms(), hands(0.4, 1), swing(3, 0.6)), 10),
    ])
    # 대지 진동: 한쪽 다리를 높이 들었다가 쿵
    A["quake"] = dict(loop=False, keys=[
        (P_(legs(-70, 4, 60, 0), arms(-40, -40, 50, -50, -30, -30), hands(-0.5, 1), swing(0, 1), chest=(-10, 0, -8), head=(-20, 0, 0), jaw=(30, 0, 0), _root=(0, 1, 0)), 14),
        (P_(legs(-24, 4, 20, 0), arms(-20, -20, 30, -30, -20, -20), hands(-0.5, 1), swing(1, 2), chest=(24, 0, 4), head=(-10, 0, 0), jaw=(20, 0, 0), _root=(0, -3, 0.8)), 3),
        (P_(legs(-24, 4, 20, 0), arms(-20, -20, 30, -30, -20, -20), hands(-0.5, 1), swing(2, 1.5), chest=(24, 0, 4), head=(-10, 0, 0), jaw=(20, 0, 0), _root=(0, -3, 0.8)), 12),
        (P_(arms(), hands(0.4, 1)), 10),
    ])
    # 거암 추격: 왼손으로 바위를 집어 머리 위로 → 던짐
    A["boulder"] = dict(loop=False, keys=[
        (P_(arms(-40, 0, 20, 0, -30, 0), hands(-0.6, 1), legs(-20, -20, 30, 30), chest=(40, 0, 0), head=(-30, 0, 0), _root=(0, -3, 0)), 10),
        (P_(arms(-176, 10, 10, 0, -40, 0), hands(-0.6, 1), chest=(-18, 0, 0), head=(-26, 0, 0), jaw=(16, 0, 0)), 14),
        (P_(arms(-176, 10, 10, 0, -40, 0), hands(-0.6, 1), chest=(-20, 0, 0), head=(-28, 0, 0), jaw=(16, 0, 0)), 30),
        (P_(arms(-50, 10, 10, 0, -10, 0), hands(-0.2, 1), chest=(26, 0, 0), head=(-10, 0, 0), _root=(0, -1, 1)), 4),
        (P_(arms(), hands(0.4, 1)), 10),
    ])
    # 회전 강타: 곤봉을 옆으로 뻗고 두 바퀴
    spin = []
    for k in range(9):
        spin.append((P_(arms(-20, -80, 30, -80, -10, 0), hands(0.4, 1), swing(k, 2), chest=(6, 0, 0), head=(-10, 0, 0), club=(-100, 0, 0),
                        _rootrot=(0, -90 * k, 0), _root=(0, -1, 0)), 4 if k else 10))
    spin.append((P_(arms(), hands(0.4, 1)), 10))
    A["whirl"] = dict(loop=False, keys=spin)
    A["roar"] = dict(loop=False, keys=[
        (P_(arms(-60, -60, 50, -50, -30, -30), hands(-0.8, 1), swing(0, 2), chest=(-18, 0, 0), head=(-30, 0, 0), jaw=(40, 0, 0)), 10),
        (P_(arms(-70, -70, 60, -60, -30, -30), hands(-0.8, 1), swing(2, 2), chest=(-20, 0, 0), head=(-34, 0, 0), jaw=(44, 0, 0)), 30),
        (P_(arms(), hands(0.4, 1)), 10),
    ])
    A["stun"] = dict(loop=False, keys=[
        (P_(legs(-80, -60, 90, 70), arms(30, 20, 20, -20, -10, -10), hands(-0.3, 0.6), chest=(30, 0, 14), head=(30, 20, 10), jaw=(20, 0, 0), _root=(0, -8, 0)), 8),
        (P_(legs(-80, -60, 90, 70), arms(34, 24, 20, -20, -10, -10), hands(-0.3, 0.6), chest=(34, 0, 16), head=(36, 20, 10), jaw=(24, 0, 0), _root=(0, -8.2, 0)), 30),
    ])
    A["death"] = dict(loop=False, keys=[
        (P_(legs(-60, -60, 80, 80), arms(-40, -40, 60, -60), hands(-0.8, 0), chest=(-20, 0, 0), head=(-30, 0, 0), jaw=(40, 0, 0), _root=(0, -6, 0)), 14),
        (P_(legs(-90, -90, 10, 10), arms(-120, -120, 60, -60), hands(-0.8, 0), chest=(-60, 0, 0), head=(-20, 0, 0), jaw=(40, 0, 0), _root=(0, -14, -6)), 16),
    ])
    return A


INFO = dict(hitbox="husk", hit_scale=3.4, portrait=dict(bone="head", dist=1.7, height=0.35))
