"""거인 보스 공용 뼈대 (이미르 · 수르트) — 재질 · 장식 · 무기는 보스 파일이 정한다

 키 7.5블록 남짓 (k≈2.3). 앞 = +Z. 오른손에 대검 (자루 · 날 · 날끝 세 조각 — 모델 범위 ±24 때문)
 애니메이션 (모든 거인 공통 이름):
   idle · walk · smash(한 손 내려베기, 근접) · plunge(두 손으로 검을 땅에 꽂음) · raise(검을 하늘로 · 포효)
   spin(검을 옆으로 뻗고 두 바퀴) · stomp(한 발 들어 쿵) · stun · death
"""
import numpy as np

from modelkit import *


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


def sway(t, a=1.0):
    """망토 · 허리천 · 수염 흔들림"""
    return {"cape0": (a * 3 * np.sin(t) + 4, 0, 0), "cape1": (a * 5 * np.sin(t - 0.7) + 4, 0, 0), "cape2": (a * 7 * np.sin(t - 1.4), 0, 0),
            "cloth_f0": (a * 4 * np.sin(t), 0, 0), "cloth_f1": (a * 6 * np.sin(t - 0.6), 0, 0),
            "beard": (a * 3 * np.sin(t + 0.5), 0, a * 2 * np.sin(t * 0.7))}


def hand_face(a, w, h):
    for x in (w // 4, w // 2, 3 * w // 4):
        a[:, x, :3] *= 0.6


def build_giant(name, k, M, deco):
    """M: 재질 dict (skin, skin_d, armor, armor_d, trim, cloth, fur, eye, glow, blade, blade_core, hilt, grip, sole)
       deco: 보스마다 덧붙이는 함수 deco(P) → P 에 파츠를 더하고 (bone, parent, offset, part, rest) 목록을 돌려줌"""
    P = {}
    # ── 몸통
    P["pelvis"] = Part("pelvis", rbox((-7.4, -3, -4.8), (7.4, 3.8, 4.8), M["armor_d"], r=1.4)
                       + [Box((-7.9, 1.4, -5.3), (7.9, 3.6, 5.3), M["trim"])]
                       + rbox((-2.2, 0.6, 5.0), (2.2, 4.4, 6.4), M["trim"], r=0.6))
    P["belly"] = Part("belly", rbox((-8.8, -0.5, -5.4), (8.8, 9.6, 6.6), M["skin"], r=3.0)
                      + [Box((-9.2, 2.0, -5.8), (9.2, 3.4, 7.0), M["armor"]), Box((-9.2, 5.6, -5.8), (9.2, 7.0, 7.0), M["armor"])])
    P["chest"] = Part("chest", rbox((-10.8, 0, -6.4), (10.8, 10.8, 6.4), M["armor"], r=2.6)
                      + rbox((-8.8, 2.4, 5.4), (-0.6, 9.6, 7.4), M["armor_d"], r=1.0) + rbox((0.6, 2.4, 5.4), (8.8, 9.6, 7.4), M["armor_d"], r=1.0)
                      + [Box((-11.2, 8.6, -6.8), (11.2, 10.4, 6.8), M["trim"])])
    P["core"] = Part("core", rbox((-2.6, -2.6, 0), (2.6, 2.6, 1.6), M["glow"], r=0.8, glow=True), glow=True)
    # ── 머리
    P["head"] = Part("head", [
        *rbox((-4.8, -1.0, -4.4), (4.8, 8.4, 4.6), M["skin"], r=1.8),
        *rbox((-5.2, 5.4, 3.0), (5.2, 7.2, 5.4), M["skin_d"], r=0.7),            # 눈썹 뼈
        *rbox((-1.1, 1.6, 4.4), (1.1, 4.6, 6.2), M["skin_d"], r=0.5),            # 코
        Box((-3.8, 3.6, 4.5), (3.8, 5.4, 4.8), M["sole"]),                       # 눈 그늘
        Box((-5.6, 2.6, -1.2), (-4.6, 5.6, 1.4), M["skin_d"]), Box((4.6, 2.6, -1.2), (5.6, 5.6, 1.4), M["skin_d"]),
    ])
    P["eyes"] = Part("eyes", [Box((-3.4, -0.7, 0), (-1.2, 0.7, 0.4), M["eye"], glow=True), Box((1.2, -0.7, 0), (3.4, 0.7, 0.4), M["eye"], glow=True)], glow=True)
    P["jaw"] = Part("jaw", rbox((-4.4, -3.0, -1.0), (4.4, 0, 5.0), M["skin_d"], r=1.2) + [Box((-3.4, -0.3, 0.6), (3.4, 0.2, 4.6), M["sole"])])
    # ── 팔 (어깨 갑옷 · 위팔 · 아래팔 + 팔찌 · 손)
    for s, sg in (("l", 1), ("r", -1)):
        P["pauldron_" + s] = Part("pauldron_" + s, rbox((-6.4, -4.6, -6.6), (6.4, 3.2, 6.6), M["armor"], r=2.2)
                                  + rbox((-5.4, -7.0, -5.4), (5.4, -4.0, 5.4), M["armor_d"], r=1.4)
                                  + [Box((-6.8, -1.6, -7.0), (6.8, -0.4, 7.0), M["trim"])])
        P["palm_" + s] = Part("palm_" + s, [
            *rbox((-3.7, -5.2, -2.8), (3.7, 0.8, 3.0), M["skin_d"], r=1.0),
            *[b for kk in range(4) for b in rbox((-3.6 + kk * 1.82, -7.4 + (0.5 if kk in (0, 3) else 0), -1.6), (-1.86 + kk * 1.82, -3.4, 3.6), M["skin_d"], r=0.45)],
            *rbox((-3.8, -4.6, 2.6), (3.8, -3.0, 4.0), M["skin"], {"south": hand_face}, r=0.4),
            *rbox((-sg * 3.9 - 1.2, -6.6, 0.4), (-sg * 3.9 + 1.2, -2.6, 4.2), M["skin_d"], r=0.45),
        ])
    P["upper"] = Part("upper", rbox((-4.2, -12.5, -4.2), (4.2, 1.5, 4.2), M["skin"], r=1.8))
    P["fore"] = Part("fore", rbox((-3.6, -11, -3.6), (3.6, 0.6, 3.6), M["skin"], r=1.4)
                     + rbox((-4.3, -10.4, -4.3), (4.3, -5.0, 4.3), M["armor"], r=0.9)
                     + [Box((-4.5, -9.0, -4.5), (4.5, -8.0, 4.5), M["trim"])])
    # ── 다리
    P["thigh"] = Part("thigh", rbox((-4.4, -10, -4.4), (4.4, 1, 4.4), M["cloth"], r=1.6)
                      + rbox((-4.8, -4.0, -1.8), (4.8, 0.6, 5.0), M["armor"], r=0.8))
    P["shin"] = Part("shin", rbox((-3.8, -9, -3.8), (3.8, 0.5, 3.8), M["armor"], r=1.2)
                     + rbox((-4.2, -1.6, 2.2), (4.2, 1.8, 5.2), M["armor_d"], r=0.8)          # 무릎 보호대
                     + [Box((-4.0, -7.6, -4.0), (4.0, -6.6, 4.0), M["trim"])])
    P["foot"] = Part("foot", rbox((-4.0, -2.8, -4.0), (4.0, 0.4, 7.0), M["armor_d"], r=1.0) + [Box((-4.2, -3.0, -4.2), (4.2, -2.0, 7.2), M["sole"])])
    # ── 허리천 · 망토
    for kk, (L, w_) in enumerate(((7, 10), (6, 9))):
        P[f"cloth_f{kk}"] = Part(f"cloth_f{kk}", [Box((-w_ / 2, -L, -0.4), (w_ / 2, 0, 0.4), M["cloth"])] + ([Box((-w_ / 2, -L, -0.5), (w_ / 2, -L + 1.2, 0.5), M["trim"])] if kk == 1 else []))
    for kk in range(3):
        w_ = 20 - kk * 1.5
        P[f"cape{kk}"] = Part(f"cape{kk}", [Box((-w_ / 2, -10, -0.5), (w_ / 2, 0, 0.5), M["fur"] if kk == 0 else M["cloth"])]
                              + ([Box((-w_ / 2, -10, -0.7), (w_ / 2, -8.6, 0.7), M["trim"])] if kk == 2 else []))
    # ── 대검 (자루 · 날 · 날끝) — 손바닥 아래로 뻗음
    P["hilt"] = Part("hilt", rbox((-0.9, -2.0, -0.9), (0.9, 6.0, 0.9), M["grip"], r=0.3)
                     + rbox((-1.6, 6.0, -1.6), (1.6, 8.6, 1.6), M["hilt"], r=0.6)                     # 폼멜
                     + rbox((-7.0, -3.6, -1.4), (7.0, -1.6, 1.4), M["hilt"], r=0.6)                   # 가드
                     + rbox((-8.6, -3.0, -0.9), (-6.6, 0.2, 0.9), M["hilt"], r=0.4) + rbox((6.6, -3.0, -0.9), (8.6, 0.2, 0.9), M["hilt"], r=0.4))
    P["blade"] = Part("blade", [Box((-2.4, -22, -0.6), (2.4, 0, 0.6), M["blade"], glow=True), Box((-0.6, -22, -0.8), (0.6, 0, 0.8), M["blade_core"], glow=True)], glow=True)
    P["blade_tip"] = Part("blade_tip", [Box((-2.4, -14, -0.6), (2.4, 0, 0.6), M["blade"], glow=True), Box((-1.6, -18, -0.5), (1.6, -14, 0.5), M["blade"], glow=True),
                                        Box((-0.7, -21, -0.4), (0.7, -18, 0.4), M["blade"], glow=True), Box((-0.6, -16, -0.8), (0.6, 0, 0.8), M["blade_core"], glow=True)], glow=True)

    R = Rig(name, k)
    R.bone("pelvis", None, (0, 19, 0), P["pelvis"])
    R.bone("belly", "pelvis", (0, 3, 0), P["belly"], rest=(8, 0, 0))
    R.bone("chest", "belly", (0, 9.0, -0.6), P["chest"], rest=(10, 0, 0))
    R.bone("core", "chest", (0, 6.0, 7.2), P["core"])
    R.bone("head", "chest", (0, 10.8, 1.6), P["head"], rest=(-16, 0, 0))
    R.bone("eyes", "head", (0, 4.6, 4.55), P["eyes"])
    R.bone("jaw", "head", (0, 0.4, 0.2), P["jaw"], rest=(4, 0, 0))
    R.bone("cloth_f0", "pelvis", (0, 1.4, 5.4), P["cloth_f0"])
    R.bone("cloth_f1", "cloth_f0", (0, -6.8, 0), P["cloth_f1"])
    R.bone("cape0", "chest", (0, 10.2, -6.8), P["cape0"], rest=(6, 0, 0))
    R.bone("cape1", "cape0", (0, -9.6, 0), P["cape1"], rest=(4, 0, 0))
    R.bone("cape2", "cape1", (0, -9.6, 0), P["cape2"], rest=(4, 0, 0))
    for s, sg in (("l", 1), ("r", -1)):
        R.bone("pauldron_" + s, "chest", (sg * 11.0, 9.6, 0), P["pauldron_" + s], rest=(0, 0, sg * 12))
        R.bone("upper_" + s, "chest", (sg * 12.8, 7.4, 0), P["upper"], rest=(-14, 0, sg * 12))
        R.bone("fore_" + s, "upper_" + s, (0, -12.4, 0), P["fore"], rest=(-26, 0, -sg * 6))
        R.bone("palm_" + s, "fore_" + s, (0, -10.4, 0.2), P["palm_" + s])
        R.bone("thigh_" + s, "pelvis", (sg * 4.6, -1.6, 0), P["thigh"], rest=(-6, 0, sg * 4))
        R.bone("shin_" + s, "thigh_" + s, (0, -10, 0), P["shin"], rest=(10, 0, -sg * 4))
        R.bone("foot_" + s, "shin_" + s, (0, -8.8, 0), P["foot"], rest=(-4, 0, 0))
    R.bone("hilt", "palm_r", (0, -4.6, 1.2), P["hilt"], rest=(-70, 0, 0))
    R.bone("blade", "hilt", (0, -3.6, 0), P["blade"])
    R.bone("blade_tip", "blade", (0, -22, 0), P["blade_tip"])
    extra = deco(P)
    for (bn, par, off, part, rest) in extra:
        R.bone(bn, par, off, P[part] if isinstance(part, str) else part, rest=rest)
    return R, list(P.values())


def giant_anims(extra_idle=None):
    """extra_idle(t) → 보스마다 덧붙이는 뼈 움직임 (불꽃 · 얼음 조각)"""
    ex = extra_idle or (lambda t: {})
    A = {}
    A["idle"] = dict(loop=True, keys=[(P_(arms(2 * np.sin(t), 3 * np.sin(t)), sway(t, 0.6), ex(t),
                                          chest=(1.5 * np.sin(t), 0, 0), head=(-1.5 * np.sin(t), 0, 0), jaw=(2 + 2 * np.sin(t), 0, 0),
                                          hilt=(3 * np.sin(t), 0, 0), _root=(0, 0.4 * np.sin(t), 0)), 12)
                                      for t in np.linspace(0, 2 * np.pi, 5)[:-1]])
    walk = []
    for i in range(6):
        ph = i / 6 * 2 * np.pi
        s = np.sin(ph)
        walk.append((P_(legs(-24 * s, 24 * s, 20 * max(0, s) + 4, 20 * max(0, -s) + 4, 4 * s, -4 * s), arms(18 * s, -10 * s), sway(ph * 2, 1.3), ex(ph),
                        chest=(3, 6 * s, 3 * s), head=(0, -5 * s, 0), _root=(0, -1.0 * abs(np.cos(ph)), 0)), 5))
    A["walk"] = dict(loop=True, keys=walk)
    # 한 손 내려베기 (근접)
    A["smash"] = dict(loop=False, keys=[
        (P_(arms(0, -165, 0, -14, 0, -24), sway(0, 1), ex(0), chest=(-12, 14, 0), head=(-8, -10, 0), hilt=(40, 0, 0)), 10),
        (P_(arms(-20, -40, 0, -6, 0, -10), sway(1, 1.6), ex(1), chest=(28, -10, 0), head=(-14, 6, 0), hilt=(-30, 0, 0), _root=(0, -2.4, 1.6)), 3),
        (P_(arms(-20, -38, 0, -6, 0, -10), sway(2, 1.2), ex(2), chest=(28, -10, 0), head=(-14, 6, 0), hilt=(-34, 0, 0), _root=(0, -2.4, 1.6)), 8),
        (P_(arms(), sway(3, 0.6), ex(3)), 10),
    ])
    # 두 손으로 검을 높이 들었다가 땅에 꽂음
    A["plunge"] = dict(loop=False, keys=[
        (P_(arms(-170, -170, -10, 10, -20, -20), sway(0, 1), ex(0), chest=(-16, 0, 0), head=(-20, 0, 0), jaw=(16, 0, 0), hilt=(70, 0, 0), _root=(0, 1, 0)), 14),
        (P_(arms(-180, -180, -12, 12, -24, -24), sway(1, 1), ex(1), chest=(-18, 0, 0), head=(-24, 0, 0), jaw=(20, 0, 0), hilt=(72, 0, 0), _root=(0, 1.4, 0)), 8),
        (P_(arms(-60, -60, -8, 8, -10, -10), legs(-30, -30, 40, 40), sway(2, 2), ex(2), chest=(40, 0, 0), head=(-20, 0, 0), jaw=(24, 0, 0), hilt=(-10, 0, 0), _root=(0, -4, 2)), 3),
        (P_(arms(-60, -60, -8, 8, -10, -10), legs(-30, -30, 40, 40), sway(3, 1.4), ex(3), chest=(40, 0, 0), head=(-20, 0, 0), jaw=(20, 0, 0), hilt=(-12, 0, 0), _root=(0, -4, 2)), 22),
        (P_(arms(), sway(4, 0.6), ex(4)), 12),
    ])
    # 검을 하늘로 치켜들고 포효
    A["raise"] = dict(loop=False, keys=[
        (P_(arms(-30, -175, 40, -6, -30, -10), sway(0, 1), ex(0), chest=(-14, 0, 0), head=(-30, 0, 0), jaw=(30, 0, 0), hilt=(90, 0, 0)), 12),
        (P_(arms(-40, -180, 50, -4, -36, -6), sway(1, 1.4), ex(1), chest=(-18, 0, 0), head=(-36, 0, 0), jaw=(40, 0, 0), hilt=(92, 0, 0), _root=(0, 0.8, 0)), 30),
        (P_(arms(), sway(2, 0.6), ex(2)), 12),
    ])
    # 검을 옆으로 뻗고 두 바퀴
    spin = []
    for kk in range(9):
        spin.append((P_(arms(-20, -86, 30, -86, -10, 0), sway(kk, 2), ex(kk), chest=(6, 0, 0), head=(-10, 0, 0), hilt=(-20, 0, 0),
                        _rootrot=(0, -90 * kk, 0), _root=(0, -1, 0)), 4 if kk else 10))
    spin.append((P_(arms(), sway(9, 0.6), ex(9)), 10))
    A["spin"] = dict(loop=False, keys=spin)
    # 한 발 들어 쿵
    A["stomp"] = dict(loop=False, keys=[
        (P_(legs(-70, 4, 60, 0), arms(-40, -30, 50, -40, -30, -30), sway(0, 1), ex(0), chest=(-10, 0, -8), head=(-20, 0, 0), jaw=(30, 0, 0), _root=(0, 1, 0)), 14),
        (P_(legs(-24, 4, 20, 0), arms(-20, -20, 30, -30, -20, -20), sway(1, 2), ex(1), chest=(24, 0, 4), head=(-10, 0, 0), jaw=(20, 0, 0), _root=(0, -3, 0.8)), 3),
        (P_(legs(-24, 4, 20, 0), arms(-20, -20, 30, -30, -20, -20), sway(2, 1.5), ex(2), chest=(24, 0, 4), head=(-10, 0, 0), jaw=(20, 0, 0), _root=(0, -3, 0.8)), 12),
        (P_(arms(), sway(3, 0.6), ex(3)), 10),
    ])
    A["stun"] = dict(loop=False, keys=[
        (P_(legs(-80, -60, 90, 70), arms(30, 20, 20, -20, -10, -10), ex(0), chest=(30, 0, 14), head=(30, 20, 10), jaw=(20, 0, 0), hilt=(20, 0, 0), _root=(0, -8, 0)), 8),
        (P_(legs(-80, -60, 90, 70), arms(34, 24, 20, -20, -10, -10), ex(1), chest=(34, 0, 16), head=(36, 20, 10), jaw=(24, 0, 0), hilt=(20, 0, 0), _root=(0, -8.2, 0)), 30),
    ])
    A["death"] = dict(loop=False, keys=[
        (P_(legs(-60, -60, 80, 80), arms(-40, -40, 60, -60), ex(0), chest=(-20, 0, 0), head=(-30, 0, 0), jaw=(40, 0, 0), _root=(0, -6, 0)), 14),
        (P_(legs(-90, -90, 10, 10), arms(-120, -120, 60, -60), ex(1), chest=(-60, 0, 0), head=(-20, 0, 0), jaw=(40, 0, 0), _root=(0, -14, -6)), 16),
    ])
    return A
