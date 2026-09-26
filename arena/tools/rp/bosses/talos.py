"""청동 거인 탈로스 — 크레타를 지키던 청동 자동인형. 가슴의 용광로 심장과
   목에서 발목까지 흐르는 이코르(신의 피) 혈관이 빛난다. 등에는 찢어진 진홍 망토.

 돌진·직선형: 청동 돌진(직선 장판 → 돌진, 기둥에 부딪히면 기절), 대지 가르기(부채꼴 3갈래 균열 순차 폭발),
 용광로 폭주(광폭화: 몸 주변 과열 고리 + 연속 돌진)

 파츠: 몸통 19 + 손가락 10 + 망토 15 + 볏 3 = 47
"""
import numpy as np

from modelkit import *

PAT = (70, 150, 126)
BRONZE = Mat((198, 128, 56), var=0.06, edge_dark=0.36, top_light=0.30, pattern=combine(metal(PAT, 0.3, 0.03), rivets(14, (255, 236, 180), (70, 36, 8), 1)))
BRONZE_P = Mat((236, 180, 88), var=0.05, edge_dark=0.34, top_light=0.28, pattern=combine(metal(PAT, 0.28, 0.02), greek_band(0.55, (255, 238, 170), (92, 50, 14))))
BRONZE_T = Mat((236, 180, 88), var=0.05, edge_dark=0.34, top_light=0.28, pattern=metal(PAT, 0.3, 0.02))
BRONZE_R = Mat((216, 150, 66), var=0.05, edge_dark=0.38, top_light=0.30, pattern=combine(metal(PAT, 0.3, 0.03), rivets(7, (255, 238, 190), (70, 36, 10))))
BRONZE_D = Mat((126, 76, 32), var=0.06, edge_dark=0.30, top_light=0.22, pattern=metal(PAT, 0.2, 0.04))
IRON = Mat((62, 58, 58), var=0.08, edge_dark=0.25, top_light=0.2)
EMBER = Mat((255, 170, 60), var=0.1, edge_dark=0.0, top_light=0.0)
ICHOR = Mat((255, 200, 80), var=0.05, edge_dark=0.0, top_light=0.0)
CREST = Mat((170, 26, 30), var=0.06, edge_dark=0.25, top_light=0.25, pattern=fur((110, 12, 16), (222, 64, 54)))
CLOTH = Mat((150, 24, 30), var=0.06, edge_dark=0.25, top_light=0.25)
CLOTH_TRIM = Mat((236, 180, 88), var=0.04, edge_dark=0.3, top_light=0.2)


def core_face(a, w, h):
    cx, cy = w / 2, h / 2
    for y in range(h):
        for x in range(w):
            d = min(1, ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5 / (w / 2))
            a[y, x, :3] = np.array((255, 252, 214)) * (1 - d) ** 1.5 + np.array((255, 110, 16)) * (1 - (1 - d) ** 1.5)
    for x in range(0, w, 3):
        a[:, x, :3] *= 0.55


def helm_face(a, w, h):
    cx = w // 2
    a[int(h * 0.45):int(h * 0.45) + 2, 1:w - 1, :3] = (22, 8, 2)
    a[int(h * 0.45) + 2:h - 1, cx - 1:cx + 1, :3] = (30, 12, 4)


def pec(a, w, h):
    a[h - 1, :, :3] *= 0.5
    a[h - 2, :, :3] *= 0.8


def abs_face(a, w, h):
    cx = w // 2
    a[:, cx - 1:cx + 1, :3] *= 0.55
    for y in range(3, h, 4):
        a[y, 1:w - 1, :3] *= 0.6


def vents(a, w, h):
    for y in range(1, h - 1, 2):
        a[y, 1:w - 1, :3] = (26, 14, 8)


def knuckle_lines(a, w, h):
    for x in (w // 4, w // 2, 3 * w // 4):
        a[:, x, :3] *= 0.45


def ridge(a, w, h):
    cx = w // 2
    a[:, cx - 1:cx + 1, :3] = np.minimum(255, a[:, cx - 1:cx + 1, :3] * 1.35)


def tatter(a, w, h):
    r = np.random.default_rng(w * 31 + h)
    for x in range(w):
        cut = int(r.integers(0, max(1, h // 4)))
        if cut:
            a[h - cut:, x, 3] = 0


def build():
    P = {}
    P["pelvis"] = Part("pelvis", rbox((-6.4, -3, -4), (6.4, 3.2, 4), BRONZE, r=1.0) + [
        Box((-6.8, 1.4, -4.3), (6.8, 3.6, 4.3), BRONZE_P),
        *rbox((-2.0, 0.4, 4.1), (2.0, 4.4, 5.2), BRONZE_R, r=0.5),
        Box((-6, -8, 3.4), (-3.2, -1, 4.6), BRONZE_D), Box((-2.8, -9, 3.6), (0, -1, 4.8), BRONZE_R), Box((0, -9, 3.6), (2.8, -1, 4.8), BRONZE_R), Box((3.2, -8, 3.4), (6, -1, 4.6), BRONZE_D),
        Box((-6, -7.5, -4.6), (-3.2, -1, -3.4), BRONZE_D), Box((-2.8, -8.5, -4.8), (2.8, -1, -3.6), BRONZE_D), Box((3.2, -7.5, -4.6), (6, -1, -3.4), BRONZE_D),
        Box((6.0, -7, -3), (7.0, -1, 3), BRONZE_D), Box((-7.0, -7, -3), (-6.0, -1, 3), BRONZE_D),
    ])
    P["torso"] = Part("torso", [
        *rbox((-6.4, 0, -4.4), (6.4, 6.8, 4.4), BRONZE, {"south": abs_face}, r=1.2),
        *rbox((-8.8, 6, -5.4), (8.8, 10.8, 5.4), BRONZE, r=1.4),
        *rbox((-11, 10, -6.4), (11, 17.4, 6.4), BRONZE, r=1.8),
        *rbox((-9.8, 11, 5.6), (-3.8, 16.8, 7.4), BRONZE_R, {"south": pec}, r=0.7),
        *rbox((3.8, 11, 5.6), (9.8, 16.8, 7.4), BRONZE_R, {"south": pec}, r=0.7),
        Box((-3.8, 14.8, 6.0), (3.8, 16.8, 7.0), BRONZE_R),
        Box((-3.0, 8.0, 6.3), (3.0, 14.0, 7.5), EMBER, {"south": core_face}, glow=True),
        Box((-3.8, 7.2, 6.0), (3.8, 8.0, 7.7), BRONZE_D), Box((-3.8, 14.0, 6.0), (3.8, 14.8, 7.7), BRONZE_D),
        Box((-3.8, 8.0, 6.0), (-3.0, 14.0, 7.7), BRONZE_D), Box((3.0, 8.0, 6.0), (3.8, 14.0, 7.7), BRONZE_D),
        Box((-0.4, 0.6, 4.3), (0.4, 7.2, 4.7), ICHOR, glow=True), Box((-0.4, 6.4, 4.7), (0.4, 7.2, 6.1), ICHOR, glow=True),
        *rbox((-4.8, 17, -4.2), (4.8, 18.8, 4.2), BRONZE_D, r=0.5),
        Box((-2.6, 18.4, -2.4), (2.6, 20.2, 2.6), IRON),
        *rbox((-7.6, 11, -8.4), (-4.4, 18.5, -5.8), IRON, r=0.5), *rbox((4.4, 11, -8.4), (7.6, 18.5, -5.8), IRON, r=0.5),
        Box((-8, 18, -8.8), (-4, 19.4, -5.4), BRONZE_D), Box((4, 18, -8.8), (8, 19.4, -5.4), BRONZE_D),
        Box((-4, 8, -6.8), (4, 15, -5.9), IRON, {"north": vents}),
        Box((-11.3, 16, -6.6), (11.3, 17.6, 6.6), BRONZE_P),
    ])
    P["head"] = Part("head", [
        *rbox((-3.8, 0, -4), (3.8, 7.2, 4.2), BRONZE_R, {"south": helm_face}, r=1.0),
        Box((-3.9, 0, 2.2), (-1.2, 4.6, 4.9), BRONZE_T), Box((1.2, 0, 2.2), (3.9, 4.6, 4.9), BRONZE_T),
        Box((-0.9, 1.2, 4.2), (0.9, 5.4, 5.2), BRONZE_T),
        Box((-3.3, 4.7, 4.22), (-0.9, 5.6, 4.5), EMBER, glow=True), Box((0.9, 4.7, 4.22), (3.3, 5.6, 4.5), EMBER, glow=True),
        Box((-4.1, 6, -4.3), (4.1, 7.2, 4.5), BRONZE_D),
        Box((-1.6, 6.8, -2.6), (1.6, 8.2, 3.2), BRONZE_T),
    ])
    for k, (z0, z1, h) in enumerate(((-1.5, 4.0, 4.6), (-4.6, -1.5, 4.4), (-7.0, -4.6, 3.8))):
        P[f"crest{k}"] = Part(f"crest{k}", [*rbox((-1.0, 0, z0), (1.0, h, z1), CREST, r=0.35)])
    for s, sg in (("l", 1), ("r", -1)):
        P["shoulder_" + s] = Part("shoulder_" + s, [
            *rbox((-4.4, -0.4, -4.8), (4.4, 3.4, 4.8), BRONZE_R, r=1.2),
            *rbox((-4.9, -2.8, -5.1), (4.9, 0.2, 5.1), BRONZE_D, r=0.8),
            *rbox((-5.3, -4.8, -5.3), (5.3, -2.4, 5.3), BRONZE_T, r=0.6),
            Box((sg * 1.5 - 1.2, 3.2, -3.5), (sg * 1.5 + 1.2, 5.8, 3.5), BRONZE_T),
            Box((sg * 1.5 - 0.3, 4.2, -2.5), (sg * 1.5 + 0.3, 5.9, 2.5), ICHOR, glow=True),
        ])
        P["arm_" + s] = Part("arm_" + s, [
            *rbox((-2.6, -9.5, -2.6), (2.6, 0, 2.6), IRON, r=0.8),
            *rbox((-3.1, -7.5, -3.1), (3.1, -2.8, 3.1), BRONZE, r=0.8),
            *rbox((-2.3, -11.6, -2.3), (2.3, -9.2, 2.3), BRONZE_D, r=0.6),
        ])
        fore = [*rbox((-3.4, -10, -3.4), (3.4, 0, 3.4), BRONZE, r=1.0),
                *rbox((-4.0, -10.4, -4.0), (4.0, -7.0, 4.0), BRONZE_P, r=0.7),
                *rbox((-3.7, -1.4, -3.7), (3.7, 0.5, 3.7), BRONZE_D, r=0.5)]
        if s == "r":
            fore.append(Box((-3.6, -9.5, -0.3), (-3.3, -0.5, 0.3), ICHOR, glow=True))
        P["fore_" + s] = Part("fore_" + s, fore)
        P["palm_" + s] = Part("palm_" + s, [
            *rbox((-3.7, -5.2, -2.8), (3.7, 0.8, 3.0), BRONZE_R, r=1.0),                                   # 손등·손바닥
            *[b for k in range(4) for b in rbox((-3.6 + k * 1.82, -7.4 + (0.5 if k in (0, 3) else 0), -1.6), (-1.86 + k * 1.82, -3.4, 3.6), BRONZE_T, r=0.45)],  # 말아 쥔 손가락 4개
            *rbox((-3.8, -4.6, 2.6), (3.8, -3.0, 4.0), BRONZE_D, r=0.4),                                   # 너클 줄
            *rbox((-sg * 3.9 - 1.2, -6.6, 0.4), (-sg * 3.9 + 1.2, -2.6, 4.2), BRONZE_R, r=0.45),          # 엄지 (안쪽에서 감쌈)
        ])
        P["thigh_" + s] = Part("thigh_" + s, [*rbox((-3.6, -9.6, -3.6), (3.6, 0, 3.6), BRONZE, r=1.2),
                                              Box((-3.3, -6.5, 3.3), (3.3, 0, 4.4), BRONZE_T)])
        shin = [*rbox((-3.2, -8.5, -3.2), (3.2, 0, 3.4), BRONZE, r=1.0),
                *rbox((-2.8, -8, 3.0), (2.8, -0.6, 4.3), BRONZE_R, {"south": ridge}, r=0.5),
                *rbox((-3.6, -1.8, -2.4), (3.6, 1.8, 4.5), BRONZE_T, r=0.8)]
        if s == "r":
            shin.append(Box((-3.55, -8.4, -0.3), (-3.15, 0, 0.3), ICHOR, glow=True))
            shin.append(Box((-4.0, -8.4, -1), (-3.2, -6.8, 1), BRONZE_T))
        P["shin_" + s] = Part("shin_" + s, shin)
        P["foot_" + s] = Part("foot_" + s, [*rbox((-3.5, -2, -3.8), (3.5, 0.2, 6.6), BRONZE_D, r=0.7),
                                            *rbox((-3.2, -0.6, -3.4), (3.2, 1.6, 3.4), BRONZE, r=0.6),
                                            *rbox((-3.0, -1.8, 5.8), (3.0, 0.6, 7.6), BRONZE_R, r=0.5)])
    for c in range(5):
        for seg in range(3):
            w_ = 3.9
            L = 6.2
            b = [Box((-w_ / 2, -L, -0.3), (w_ / 2, 0.2, 0.3), CLOTH, {"north": tatter, "south": tatter} if seg == 2 else None)]
            if seg == 0:
                b.append(Box((-w_ / 2 - 0.05, -1.0, -0.4), (w_ / 2 + 0.05, 0.2, 0.4), CLOTH_TRIM))
            P[f"cape{c}_{seg}"] = Part(f"cape{c}_{seg}", b)
    parts = list(P.values())

    R = Rig("talos", 2.0)
    R.bone("pelvis", None, (0, 22, 0), P["pelvis"])
    R.bone("torso", "pelvis", (0, 3, 0), P["torso"], rest=(4, 0, 0))
    R.bone("head", "torso", (0, 19.2, 1.4), P["head"], rest=(-4, 0, 0), scale=1.3)
    R.bone("crest0", "head", (0, 7.6, 0), P["crest0"])
    R.bone("crest1", "crest0", (0, 0, 0), P["crest1"], rest=(8, 0, 0))
    R.bone("crest2", "crest1", (0, -0.5, 0), P["crest2"], rest=(14, 0, 0))
    for s, sg in (("l", 1), ("r", -1)):
        R.bone("shoulder_" + s, "torso", (sg * 12.8, 14.2, 0), P["shoulder_" + s], rest=(0, 0, sg * 10))
        R.bone("arm_" + s, "shoulder_" + s, (sg * 0.4, -2.2, 0), P["arm_" + s], rest=(0, 0, sg * 2))
        R.bone("fore_" + s, "arm_" + s, (0, -10.8, 0), P["fore_" + s], rest=(-14, 0, 0))
        R.bone("palm_" + s, "fore_" + s, (0, -9.6, 0.2), P["palm_" + s])
        R.bone("thigh_" + s, "pelvis", (sg * 3.8, -2, 0), P["thigh_" + s], rest=(0, 0, sg * 3))
        R.bone("shin_" + s, "thigh_" + s, (0, -9.6, 0), P["shin_" + s], rest=(4, 0, -sg * 3))
        R.bone("foot_" + s, "shin_" + s, (0, -8.5, 0), P["foot_" + s], rest=(-4, 0, 0))
    for c in range(5):
        x = -7.6 + c * 3.8
        R.bone(f"cape{c}_0", "torso", (x, 17.2, -7.2 - abs(x) * 0.08), P[f"cape{c}_0"], rest=(8, 0, 0))
        R.bone(f"cape{c}_1", f"cape{c}_0", (0, -6.0, 0), P[f"cape{c}_1"], rest=(3, 0, 0))
        R.bone(f"cape{c}_2", f"cape{c}_1", (0, -6.0, 0), P[f"cape{c}_2"], rest=(3, 0, 0))
    return R, parts, anims()


def arms(rx_l=0, rx_r=0, rz_l=0, rz_r=0, fl=0, fr=0):
    return {"arm_l": (rx_l, 0, rz_l), "arm_r": (rx_r, 0, rz_r), "fore_l": (fl, 0, 0), "fore_r": (fr, 0, 0)}


def legs(tl=0, tr_=0, sl=0, sr=0, fl=0, fr=0):
    return {"thigh_l": (tl, 0, 0), "thigh_r": (tr_, 0, 0), "shin_l": (sl, 0, 0), "shin_r": (sr, 0, 0), "foot_l": (fl, 0, 0), "foot_r": (fr, 0, 0)}


def hands(curl_l=0.0, curl_r=0.0):
    return {}




def cape(t, amp=1.0, lift=0.0):
    d = {}
    for c in range(5):
        for seg in range(3):
            d[f"cape{c}_{seg}"] = (lift * (1 if seg == 0 else 0.4) + amp * 4 * np.sin(t + c * 0.9 + seg * 0.7), 0, amp * 2 * np.sin(t * 0.7 + c))
    return d


def P_(*ds, **kw):
    out = {}
    for d in ds:
        out.update(d)
    out.update(kw)
    return out


def anims():
    A = {}
    A["idle"] = dict(loop=True, keys=[
        (P_(arms(4, 4, 2, -2), hands(0.3, 0.3), cape(0), torso=(1, 0, 0), head=(2, 0, 0), crest2=(4, 0, 0), _root=(0, 0, 0)), 20),
        (P_(arms(-2, -2, 4, -4), hands(0.2, 0.2), cape(np.pi), torso=(-1.5, 0, 0), head=(-1, 0, 0), crest2=(-4, 0, 0), _root=(0, 0.3, 0)), 20),
    ])
    walk = []
    for i in range(6):
        ph = i / 6 * 2 * np.pi
        s = np.sin(ph); c = np.cos(ph)
        walk.append((P_(legs(-26 * s, 26 * s, 22 * max(0, s) + 6, 22 * max(0, -s) + 6, 4 * s, -4 * s),
                        arms(22 * s, -22 * s, 3, -3, -14, -14), hands(0.5, 0.5), cape(ph * 2, 1.4, 14),
                        torso=(4, 5 * s, 0), head=(-3, -4 * s, 0), _root=(0, -0.8 * abs(c), 0)), 4))
    A["walk"] = dict(loop=True, keys=walk)
    A["punch"] = dict(loop=False, keys=[
        (P_(arms(10, 60, 4, -10, -20, -40), hands(0.3, 1), cape(0, 1, 10), torso=(0, 22, 0), head=(0, -12, 0)), 6),
        (P_(arms(10, -96, 4, -4, -20, -4), hands(0.3, 1), cape(1, 1, 30), torso=(8, -26, 0), head=(4, 14, 0), _root=(0, -0.6, 1)), 3),
        (P_(arms(10, -80, 4, -4, -20, -8), hands(0.3, 1), cape(2, 1, 20), torso=(8, -20, 0), head=(4, 10, 0), _root=(0, -0.6, 1)), 5),
        (P_(arms(4, 4, 2, -2), hands(0.3, 0.3), cape(3), torso=(1, 0, 0)), 8),
    ])
    crouch = P_(legs(-32, -12, 44, 30, -12, -18), arms(38, 38, 12, -12, -28, -28), hands(1, 1), cape(0, 0.6, 20),
                torso=(26, 0, 0), head=(-18, 0, 0), _root=(0, -3.2, -1))
    A["rush_windup"] = dict(loop=False, keys=[(crouch, 10)])
    run = []
    for i in range(4):
        s = 1 if i % 2 == 0 else -1
        run.append((P_(legs(-48 * s, 48 * s, 60 if s < 0 else 12, 60 if s > 0 else 12, 0, 0), arms(50, 50, 16, -16, -30, -30),
                       hands(1, 1), cape(i * 1.6, 2.0, 62), torso=(34, 0, 0), head=(-26, 0, 0), _root=(0, -2.0 + (0.8 if i % 2 else 0), 0)), 3))
    A["rush"] = dict(loop=True, keys=run)
    A["stun"] = dict(loop=False, keys=[
        (P_(legs(-70, 10, 80, 96, -10, -40), arms(22, 16, 6, -8, -6, -10), hands(-0.3, -0.3), cape(0, 0.3, -6), torso=(34, 0, 12), head=(34, 18, 10), _root=(0, -6.5, 0)), 6),
        (P_(legs(-70, 10, 80, 96, -10, -40), arms(26, 20, 6, -8, -6, -10), hands(-0.3, -0.3), cape(1, 0.3, -6), torso=(38, 0, 14), head=(40, 18, 10), _root=(0, -6.8, 0)), 30),
    ])
    A["fissure"] = dict(loop=False, keys=[
        (P_(arms(-168, -168, 10, -10, -18, -18), hands(1, 1), legs(-6, -6, 6, 6), cape(0, 0.6, -4), torso=(-12, 0, 0), head=(-14, 0, 0), _root=(0, 0.6, 0)), 12),
        (P_(arms(-172, -172, 6, -6, -8, -8), hands(1, 1), cape(1, 0.6, -6), torso=(-16, 0, 0), head=(-18, 0, 0), _root=(0, 0.8, 0)), 8),
        (P_(arms(-38, -38, 8, -8, -10, -10), hands(1, 1), legs(-38, -38, 60, 60, -20, -20), cape(2, 1.5, 40), torso=(42, 0, 0), head=(-10, 0, 0), _root=(0, -4.0, 1)), 3),
        (P_(arms(-30, -30, 8, -8, -10, -10), hands(1, 1), legs(-38, -38, 60, 60, -20, -20), cape(3, 1.0, 20), torso=(40, 0, 0), head=(-12, 0, 0), _root=(0, -4.0, 1)), 12),
        (P_(arms(4, 4, 2, -2), hands(0.3, 0.3), cape(4)), 10),
    ])
    A["overheat"] = dict(loop=False, keys=[
        (P_(arms(-20, -20, 72, -72, -30, -30), hands(-1, -1), legs(-10, -10, 12, 12), cape(0, 2, 30), torso=(-10, 0, 0), head=(-28, 0, 0), _root=(0, -0.5, 0)), 14),
        (P_(arms(-26, -26, 86, -86, -20, -20), hands(-1.2, -1.2), legs(-10, -10, 12, 12), cape(2, 2.5, 40), torso=(-14, 0, 0), head=(-34, 0, 0), _root=(0, -0.3, 0)), 26),
        (P_(arms(4, 4, 2, -2), hands(0.3, 0.3), cape(4)), 12),
    ])
    A["death"] = dict(loop=False, keys=[
        (P_(legs(-80, -80, 96, 96, -20, -20), arms(30, 30, 10, -10, -10, -10), hands(-0.5, -0.5), cape(0, 0.2, -10), torso=(20, 0, 0), head=(30, 0, 0), _root=(0, -8, 0)), 14),
        (P_(legs(-80, -80, 96, 96, -20, -20), arms(-60, -60, 20, -20, -10, -10), hands(-0.5, -0.5), cape(0, 0.2, 60), torso=(80, 0, 0), head=(20, 0, 0), _root=(0, -12, 3)), 16),
    ])
    return A


INFO = dict(hitbox="iron_golem", hit_scale=2.4, portrait=dict(bone="head", dist=1.9, cy=4.2, cz=3.0))
