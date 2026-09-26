"""스핑크스 — 사자의 몸, 파라오의 얼굴, 황금 날개. 수수께끼를 풀지 못한 자를 돌로 만든다.

 광역 마법진·석화형: 석화의 수수께끼(자기 중심 거대 마법진 → 안쪽 전원 석화), 모래 표식(플레이어마다 발밑 원 동시),
 봉인의 고리(도넛: 가까이 붙어야 안전) — 석화(멀어져라) ↔ 봉인(붙어라)이 번갈아 온다
"""
import numpy as np

from modelkit import *

FUR = Mat((214, 170, 98), var=0.12, edge_dark=0.28, top_light=0.22, pattern=fur((176, 126, 64), (236, 200, 132)))
FUR_D = Mat((178, 132, 72), var=0.12, edge_dark=0.3, top_light=0.2, pattern=fur((140, 96, 48), (206, 160, 96)))
SKIN = Mat((204, 150, 98), var=0.06, edge_dark=0.2, top_light=0.12)
GOLD = Mat((236, 188, 64), var=0.08, edge_dark=0.35, top_light=0.3, pattern=metal((180, 120, 30), 0.35, 0.0))
LAPIS = (34, 66, 156)
NEMES = Mat((232, 184, 62), var=0.06, edge_dark=0.25, top_light=0.18, pattern=stripes((232, 184, 62), LAPIS, 2, vertical=False))
NEMES_V = Mat((232, 184, 62), var=0.06, edge_dark=0.25, top_light=0.18, pattern=stripes((232, 184, 62), LAPIS, 2, vertical=True))
COLLAR = Mat((236, 188, 64), var=0.05, edge_dark=0.3, top_light=0.1, pattern=stripes((236, 188, 64), (190, 40, 36), 2, vertical=False))
WING = Mat((226, 196, 124), var=0.08, edge_dark=0.25, top_light=0.12, pattern=feathers((54, 128, 150), (120, 90, 50)))
WING_T = Mat((70, 140, 160), var=0.1, edge_dark=0.25, top_light=0.12, pattern=feathers((240, 214, 140), (30, 70, 90)))
CLAW = Mat((236, 226, 200), var=0.05, edge_dark=0.2)
EYE = Mat((110, 240, 255), var=0.1, edge_dark=0.0, top_light=0.0)
DARKFUR = Mat((96, 62, 30), var=0.12, edge_dark=0.2, pattern=fur((60, 36, 16), (140, 92, 46)))


def face(a, w, h):
    """황금 장례 가면: 청금석 눈썹·눈화장, 코 음영, 굳게 다문 입"""
    cx = w // 2
    ey = int(h * 0.40)
    L = np.array(LAPIS)
    for sx in (-1, 1):
        x0 = cx + 1 if sx > 0 else cx - 6
        a[ey - 3, x0:x0 + 5, :3] = L                              # 눈썹
        a[ey - 2, x0 + (0 if sx > 0 else 1):x0 + (4 if sx > 0 else 5), :3] = L * 0.8
        a[ey, x0:x0 + 5, :3] = L                                  # 눈 윤곽
        a[ey + 1, x0:x0 + 5, :3] = (20, 20, 30)
        a[ey + 2, x0:x0 + 5, :3] = L
        ex = x0 + 5 if sx > 0 else x0 - 1
        a[ey + 1:ey + 3, ex, :3] = L                              # 꼬리선
    a[ey:ey + 6, cx - 1:cx + 1, :3] = np.minimum(255, a[ey:ey + 6, cx - 1:cx + 1, :3] * 1.18)
    a[ey + 5, cx - 2:cx + 2, :3] *= 0.6
    a[int(h * 0.78), cx - 3:cx + 3, :3] *= 0.45
    a[int(h * 0.78) + 1, cx - 2:cx + 2, :3] *= 0.7
    for y in range(h):
        a[y, 0, :3] *= 0.7; a[y, w - 1, :3] *= 0.7


def claws(a, w, h):
    for x in range(1, w - 1, 3):
        a[h - 2:h, x, :3] = (240, 232, 210)


def build():
    P = {}
    P["body"] = Part("body", [
        Box((-7, -6, -15), (7, 6.5, 12), FUR),
        Box((-7.6, -5, 4), (7.6, 7.2, 13.2), FUR),                       # 가슴 (앞이 두툼)
        Box((-7.9, 1.5, 11.2), (7.9, 6.6, 14.2), COLLAR),                 # 우세크 목걸이
        Box((-6.5, -6.6, -13), (6.5, -5.4, 10), FUR_D),                   # 배
        Box((-7.3, 4, -15.4), (7.3, 7, -9), FUR),                         # 엉덩이 둔덕
    ])
    P["head"] = Part("head", [
        Box((-3.9, -3.4, -1), (3.9, 5.8, 5.6), GOLD, {"south": face}),
        Box((-0.7, -0.4, 5.6), (0.7, 2.2, 6.4), GOLD),
        Box((-5.2, 3.4, -3.6), (5.2, 8.4, 4.4), NEMES),
        Box((-6.2, -9, -0.6), (-3.9, 5, 3.8), NEMES),
        Box((3.9, -9, -0.6), (6.2, 5, 3.8), NEMES),
        Box((-3.4, -5, -6.0), (3.4, 6, -3.4), NEMES_V),
        Box((-5.2, 5.6, 4.2), (5.2, 6.6, 4.8), GOLD),                    # 이마 띠
        Box((-0.7, 6.0, 4.6), (0.7, 9.4, 5.6), GOLD),                     # 우라에우스 코브라
        Box((-1.1, -7.2, 3.2), (1.1, -3.0, 5.0), Mat((40, 70, 150), pattern=stripes((40, 70, 150), (236, 188, 64), 1, False))),
        Box((-3.4, 1.8, 5.62), (-1.0, 2.6, 5.9), EYE, glow=True), Box((1.0, 1.8, 5.62), (3.4, 2.6, 5.9), EYE, glow=True),
    ])
    for s, sg in (("l", 1), ("r", -1)):
        P["fleg_" + s] = Part("fleg_" + s, [Box((-3.1, -7, -3.1), (3.1, 1.6, 3.2), FUR), Box((-3.3, -1, -3.3), (3.3, 2.2, 3.4), FUR)])
        P["fpaw_" + s] = Part("fpaw_" + s, [
            Box((-2.7, -5, -2.7), (2.7, 0, 2.9), FUR_D),
            Box((-3.3, -6, -2.4), (3.3, -4.4, 5.2), FUR_D, {"south": claws}),
            Box((-3.0, -2.0, -3.0), (3.0, -0.6, 3.2), GOLD),                   # 팔찌
        ])
        P["hleg_" + s] = Part("hleg_" + s, [Box((-3.3, -7, -4.6), (3.3, 2.8, 3.6), FUR)])
        P["hpaw_" + s] = Part("hpaw_" + s, [
            Box((-2.5, -6, -2.3), (2.5, 0, 2.3), FUR_D),
            Box((-3.0, -7, -2.4), (3.0, -5.6, 4.2), FUR_D, {"south": claws}),
        ])
        P["wing_" + s] = Part("wing_" + s, [
            Box((-0.8, -3, -15), (0.8, 6, 1.5), WING),
            Box((-0.7, -7, -14), (0.7, -3, -1), WING_T),
            Box((-1.0, 4.2, -3), (1.0, 7.0, 2), GOLD),
        ])
        P["wingtip_" + s] = Part("wingtip_" + s, [
            Box((-0.6, -2, -13), (0.6, 6, 0), WING),
            Box((-0.5, -6, -12), (0.5, -2, -1), WING_T),
        ])
    P["tail1"] = Part("tail1", [Box((-0.9, -0.9, -7.5), (0.9, 0.9, 0), FUR)])
    P["tail2"] = Part("tail2", [Box((-0.8, -0.8, -6), (0.8, 0.8, 0), FUR), Box((-1.6, -1.6, -8.2), (1.6, 1.6, -5.6), DARKFUR)])
    parts = list(P.values())

    R = Rig("sphinx", 2.1)
    R.bone("body", None, (0, 17, 0), P["body"])
    R.bone("head", "body", (0, 8.8, 12.6), P["head"], scale=1.0)
    for s, sg in (("l", 1), ("r", -1)):
        R.bone("fleg_" + s, "body", (sg * 4.6, -4.5, 9.5), P["fleg_" + s])
        R.bone("fpaw_" + s, "fleg_" + s, (0, -6.5, 0), P["fpaw_" + s])
        R.bone("hleg_" + s, "body", (sg * 4.8, -3.5, -11), P["hleg_" + s])
        R.bone("hpaw_" + s, "hleg_" + s, (0, -6.5, -1.2), P["hpaw_" + s])
        R.bone("wing_" + s, "body", (sg * 6.2, 6.2, 6), P["wing_" + s], rest=(34, sg * 8, sg * 16))
        R.bone("wingtip_" + s, "wing_" + s, (0, 0.5, -14.6), P["wingtip_" + s], rest=(22, sg * -4, 0))
    R.bone("tail1", "body", (0, 3, -15), P["tail1"], rest=(-38, 0, 0))
    R.bone("tail2", "tail1", (0, 0, -7.3), P["tail2"], rest=(40, 0, 0))
    return R, parts, anims()


def P_(*ds, **kw):
    out = {}
    for d in ds:
        out.update(d)
    out.update(kw)
    return out


def legs(fl=0, fr=0, pl=0, pr=0, hl=0, hr=0, ql=0, qr=0):
    return {"fleg_l": (fl, 0, 0), "fleg_r": (fr, 0, 0), "fpaw_l": (pl, 0, 0), "fpaw_r": (pr, 0, 0),
            "hleg_l": (hl, 0, 0), "hleg_r": (hr, 0, 0), "hpaw_l": (ql, 0, 0), "hpaw_r": (qr, 0, 0)}


def wings(rx_=0, ry_=0, rz_=0, tip=0):
    return {"wing_l": (rx_, ry_, rz_), "wing_r": (rx_, -ry_, -rz_), "wingtip_l": (0, tip, 0), "wingtip_r": (0, -tip, 0)}


def anims():
    A = {}
    A["idle"] = dict(loop=True, keys=[
        (P_(wings(0, 0, 0), tail1=(0, 12, 0), tail2=(0, 14, 0), head=(2, 0, 0), _root=(0, 0, 0)), 22),
        (P_(wings(-2, 0, 4), tail1=(4, -12, 0), tail2=(0, -14, 0), head=(-1, 0, 0), body=(-1, 0, 0), _root=(0, 0.35, 0)), 22),
    ])
    walk = []
    for i in range(6):
        ph = i / 6 * 2 * np.pi
        s = np.sin(ph)
        walk.append((P_(legs(-24 * s, 24 * s, 16 * max(0, s), 16 * max(0, -s), 22 * s, -22 * s, -10 * max(0, -s), -10 * max(0, s)),
                        wings(0, 0, 2 * s), tail1=(0, 16 * s, 0), tail2=(0, 18 * s, 0), head=(0, 4 * s, 0),
                        _root=(0, -0.5 * abs(np.cos(ph)), 0)), 4))
    A["walk"] = dict(loop=True, keys=walk)
    A["claw"] = dict(loop=False, keys=[
        (P_(legs(-10, -96, 0, 30, 10, 10), body=(-12, 0, 0), head=(8, 0, 0), _root=(0, 1.2, 0)), 6),
        (P_(legs(-10, -18, 0, 0, 12, 12), body=(10, 0, 0), head=(-6, 0, 0), _root=(0, -0.8, 1)), 3),
        (P_(legs(-10, -14, 0, 0, 12, 12), body=(8, 0, 0), head=(-4, 0, 0), _root=(0, -0.8, 1)), 5),
        (P_(legs(), body=(0, 0, 0)), 8),
    ])
    # 석화의 수수께끼: 뒷발로 앉아 상체를 세우고 날개를 활짝
    A["riddle"] = dict(loop=False, keys=[
        (P_(legs(-30, -30, 20, 20, 60, 60, -40, -40), wings(-30, 50, 50, -30), body=(-30, 0, 0), head=(20, 0, 0),
            tail1=(20, 0, 0), _root=(0, -3, -2)), 14),
        (P_(legs(-40, -40, 30, 30, 64, 64, -44, -44), wings(-44, 60, 60, -40), body=(-34, 0, 0), head=(24, 0, 0),
            tail1=(24, 0, 0), _root=(0, -3, -2)), 40),
        (P_(legs()), 12),
    ])
    A["mark"] = dict(loop=False, keys=[
        (P_(legs(), wings(-6, 12, 20), head=(-14, 0, 0), body=(-4, 0, 0)), 8),
        (P_(legs(), wings(-10, 18, 26), head=(12, 0, 0), body=(4, 0, 0), _root=(0, -0.6, 0)), 6),
        (P_(legs()), 10),
    ])
    A["seal"] = dict(loop=False, keys=[
        (P_(legs(-20, -20, 30, 30, -10, -10, 20, 20), wings(10, 70, 20, -20), body=(12, 0, 0), head=(-18, 0, 0), _root=(0, -3, 0)), 12),
        (P_(legs(-24, -24, 34, 34, -12, -12, 22, 22), wings(14, 76, 10, -30), body=(14, 0, 0), head=(-22, 0, 0), _root=(0, -3.4, 0)), 36),
        (P_(legs()), 12),
    ])
    A["stun"] = dict(loop=False, keys=[
        (P_(legs(-50, -50, 70, 70, 60, 60, -60, -60), wings(10, 0, -10), body=(6, 0, 12), head=(30, 20, 0), _root=(0, -6, 0)), 8),
        (P_(legs(-50, -50, 70, 70, 60, 60, -60, -60), wings(10, 0, -12), body=(6, 0, 14), head=(34, 24, 0), _root=(0, -6.2, 0)), 30),
    ])
    A["death"] = dict(loop=False, keys=[
        (P_(legs(-60, -60, 80, 80, 70, 70, -70, -70), wings(20, 20, -20), body=(10, 0, 30), head=(40, 30, 0), _root=(0, -8, 0)), 16),
        (P_(legs(-60, -60, 80, 80, 70, 70, -70, -70), wings(20, 30, -30), body=(10, 0, 70), head=(40, 30, 0), _root=(0, -10, 0)), 14),
    ])
    return A


INFO = dict(hitbox="ravager", hit_scale=1.5, portrait=dict(bone="head", dist=1.5, height=0.25))
