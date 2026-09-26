"""스핑크스 — 사자의 몸, 황금 가면의 얼굴, 청금석·황금 깃털 날개. 수수께끼를 풀지 못한 자를 돌로 만든다.

 광역 마법진·석화형: 석화의 수수께끼(자기 중심 거대 마법진 → 안쪽 전원 석화), 모래 표식(플레이어마다 발밑 원 동시),
 봉인의 고리(도넛: 가까이 붙어야 안전) — 석화(멀어져라) ↔ 봉인(붙어라)이 번갈아 온다

 파츠: 몸 3 + 머리 1 + 두건 자락 2 + 다리 12 + 꼬리 7 + 날개 2x15 = 55
"""
import numpy as np

from modelkit import *

LAPIS = (30, 62, 150)
FUR = Mat((218, 172, 98), var=0.05, edge_dark=0.26, top_light=0.24, pattern=fur((178, 128, 64), (240, 204, 136)))
FUR_D = Mat((184, 136, 74), var=0.05, edge_dark=0.28, top_light=0.22, pattern=fur((146, 100, 50), (212, 166, 100)))
FUR_B = Mat((236, 206, 150), var=0.04, edge_dark=0.22, top_light=0.14)
GOLD = Mat((240, 192, 66), var=0.04, edge_dark=0.36, top_light=0.32, pattern=metal((180, 120, 30), 0.35, 0.0))
NEMES = Mat((236, 188, 64), var=0.03, edge_dark=0.26, top_light=0.2, pattern=stripes((236, 188, 64), LAPIS, 2, vertical=False))
NEMES_V = Mat((236, 188, 64), var=0.03, edge_dark=0.26, top_light=0.2, pattern=stripes((236, 188, 64), LAPIS, 2, vertical=True))
COLLAR = Mat((236, 188, 64), var=0.03, edge_dark=0.3, top_light=0.12,
             pattern=lambda a, f, w, h, r: _collar(a, w, h))
CLAW = Mat((240, 232, 210), var=0.03, edge_dark=0.2, top_light=0.2)
EYE = Mat((120, 244, 255), var=0.03, edge_dark=0.0, top_light=0.0)
DARKFUR = Mat((100, 64, 32), var=0.05, edge_dark=0.2, pattern=fur((64, 38, 16), (146, 96, 48)))


def _collar(a, w, h):
    cols = [(236, 188, 64), (190, 40, 36), (236, 188, 64), LAPIS, (236, 188, 64), (40, 150, 130)]
    for y in range(h):
        a[y, :, :3] = a[y, :, :3] * 0.3 + np.array(cols[(y // 2) % len(cols)]) * 0.7
    for x in range(0, w, 3):
        a[h - 1, x, :3] = (255, 230, 140)


def feather_pat(base, tip):
    """깃털: 가운데 깃대(밝은 선) + 뿌리→끝 색 변화 + 가장자리 어둡게"""
    def fn(a, face, w, h, r):
        if face in ("up", "down", "north", "south"):
            return
        for x in range(w):
            t = x / max(1, w - 1)
            if face == "east":
                t = 1 - t
            c = np.array(base) * (1 - t ** 1.6) + np.array(tip) * t ** 1.6
            a[:, x, :3] = c
        mid = h // 2
        a[mid, :, :3] = np.minimum(255, a[mid, :, :3] * 1.25 + 20)
        a[0, :, :3] *= 0.6
        a[h - 1, :, :3] *= 0.55
        for x in range(1, w, 3):
            a[1:mid, x, :3] *= 0.88
            a[mid + 1:h - 1, x, :3] *= 0.88
    return fn


FEATHER_IN = Mat((236, 206, 130), var=0.02, edge_dark=0.0, top_light=0.0, pattern=feather_pat((240, 212, 140), (210, 170, 80)))
FEATHER_MID = Mat((236, 206, 130), var=0.02, edge_dark=0.0, top_light=0.0, pattern=feather_pat((236, 196, 110), (46, 130, 150)))
FEATHER_OUT = Mat((236, 206, 130), var=0.02, edge_dark=0.0, top_light=0.0, pattern=feather_pat((210, 176, 90), (30, 62, 150)))


def face(a, w, h):
    """황금 장례 가면: 청금석 눈썹·눈화장, 코 음영, 굳게 다문 입"""
    cx = w // 2
    ey = int(h * 0.40)
    L = np.array(LAPIS)
    for sx in (-1, 1):
        x0 = cx + 1 if sx > 0 else cx - 6
        a[ey - 3, x0:x0 + 5, :3] = L
        a[ey, x0:x0 + 5, :3] = L
        a[ey + 1, x0:x0 + 5, :3] = (20, 20, 30)
        a[ey + 2, x0:x0 + 5, :3] = L
        ex = x0 + 5 if sx > 0 else x0 - 1
        if 0 <= ex < w:
            a[ey + 1:ey + 3, ex, :3] = L
    a[ey:ey + 6, cx - 1:cx + 1, :3] = np.minimum(255, a[ey:ey + 6, cx - 1:cx + 1, :3] * 1.18)
    a[ey + 5, cx - 2:cx + 2, :3] *= 0.6
    a[int(h * 0.8), cx - 3:cx + 3, :3] *= 0.45


def claws(a, w, h):
    for x in range(1, w - 1, 3):
        a[h - 2:h, x, :3] = (244, 236, 214)


def feather(name, L, mat, wdt=3.2):
    return Part(name, [Box((-0.28, -wdt / 2, -L), (0.28, wdt / 2, 0.3), mat),
                       Box((-0.34, -0.25, -L * 0.85), (0.34, 0.25, 0.3), GOLD)])


# 날개 구조: 뼈 3마디 (위로 뻗음) + 각 마디에 뒤로 뻗는 깃털
WING_FEATHERS = {
    "w0": [(1.6, 6.5, "in"), (3.6, 7.5, "in"), (5.6, 8.5, "in")],
    "w1": [(1.0, 9.5, "mid"), (2.8, 10.5, "mid"), (4.6, 11.5, "mid"), (6.4, 12.0, "mid")],
    "w2": [(0.6, 13.0, "out"), (2.0, 13.5, "out"), (3.4, 13.5, "out"), (4.8, 12.5, "out"), (6.0, 11.0, "out")],
}


def build():
    P = {}
    P["chest"] = Part("chest", rbox((-7.8, -6.6, -1), (7.8, 7.2, 12.5), FUR, r=2.2)
                      + rbox((-7.0, -7.4, 1), (7.0, -5.8, 11), FUR_B, r=0.6)
                      + [Box((-8.1, 1.2, 10.6), (8.1, 6.8, 13.4), COLLAR)])
    P["waist"] = Part("waist", rbox((-6.8, -5.6, -12), (6.8, 6.4, 0.5), FUR, r=2.0)
                      + rbox((-5.8, -6.4, -11), (5.8, -4.8, 0), FUR_B, r=0.5))
    P["hips"] = Part("hips", rbox((-7.4, -5.4, -7.5), (7.4, 7.0, 0.5), FUR, r=2.2))
    P["head"] = Part("head", [
        *rbox((-3.9, -3.4, -1), (3.9, 5.8, 5.6), GOLD, {"south": face}, r=0.7),
        Box((-0.7, -0.4, 5.6), (0.7, 2.2, 6.4), GOLD),
        *rbox((-5.4, 3.2, -4.0), (5.4, 8.6, 4.6), NEMES, r=1.2),
        *rbox((-3.4, -4.6, -6.4), (3.4, 6.4, -3.2), NEMES_V, r=0.8),
        Box((-5.4, 5.6, 4.2), (5.4, 6.6, 4.9), GOLD),
        Box((-0.7, 6.0, 4.7), (0.7, 9.6, 5.7), GOLD),
        Box((-1.1, -7.4, 3.0), (1.1, -3.0, 5.0), Mat(LAPIS, pattern=stripes(LAPIS, (236, 188, 64), 1, False))),
        Box((-3.4, 1.8, 5.62), (-1.0, 2.6, 5.9), EYE, glow=True), Box((1.0, 1.8, 5.62), (3.4, 2.6, 5.9), EYE, glow=True),
    ])
    P["lappet"] = Part("lappet", rbox((-1.2, -12, -2.2), (1.2, 0, 2.2), NEMES, r=0.5))
    P["fu"] = Part("fu", rbox((-3.4, -7.5, -3.4), (3.4, 2.4, 3.6), FUR, r=1.2))
    P["fl"] = Part("fl", rbox((-2.8, -5.6, -2.8), (2.8, 0.4, 3.0), FUR_D, r=0.8) + [Box((-3.0, -2.2, -3.0), (3.0, -0.8, 3.2), GOLD)])
    P["paw"] = Part("paw", rbox((-3.4, -2.0, -2.6), (3.4, 0, 4.8), FUR_D, {"south": claws}, r=0.6)
                    + [Box((-3.0 + k * 2.0, -2.1, 4.4), (-2.2 + k * 2.0, -1.2, 6.0), CLAW) for k in range(4)])
    P["hu"] = Part("hu", rbox((-3.6, -7.5, -5), (3.6, 3.2, 4.0), FUR, r=1.5))
    P["hl"] = Part("hl", rbox((-2.6, -6.4, -2.4), (2.6, 0.4, 2.6), FUR_D, r=0.8))
    for k in range(6):
        r = 1.1 - k * 0.08
        P[f"tail{k}"] = Part(f"tail{k}", [*rbox((-r, -r, -3.8), (r, r, 0.3), FUR, r=0.35)])
    P["tuft"] = Part("tuft", rbox((-1.8, -1.8, -4.2), (1.8, 1.8, 0.3), DARKFUR, r=0.7))
    mats = {"in": FEATHER_IN, "mid": FEATHER_MID, "out": FEATHER_OUT}
    P["wbone"] = Part("wbone", rbox((-0.9, 0, -1.3), (0.9, 7.2, 1.3), GOLD, r=0.4))
    for seg, fl in WING_FEATHERS.items():
        for j, (y, L, kind) in enumerate(fl):
            P[f"f_{seg}_{j}"] = feather(f"f_{seg}_{j}", L, mats[kind])
    parts = list(P.values())

    R = Rig("sphinx", 2.6)
    R.bone("waist", None, (0, 17, 0), P["waist"])
    R.bone("chest", "waist", (0, 0.4, 0), P["chest"], rest=(-3, 0, 0))
    R.bone("hips", "waist", (0, 0, -11.6), P["hips"], rest=(4, 0, 0))
    R.bone("head", "chest", (0, 9.2, 12.4), P["head"], rest=(-4, 0, 0))
    for s, sg in (("l", 1), ("r", -1)):
        R.bone("lappet_" + s, "head", (sg * 4.6, 4.2, 1.4), P["lappet"], rest=(6, 0, sg * 6))
        R.bone("fu_" + s, "chest", (sg * 4.8, -4.5, 8.6), P["fu"], rest=(-4, 0, 0))
        R.bone("fl_" + s, "fu_" + s, (0, -7.2, 0.2), P["fl"], rest=(6, 0, 0))
        R.bone("fp_" + s, "fl_" + s, (0, -5.4, 0.2), P["paw"], rest=(-2, 0, 0))
        R.bone("hu_" + s, "hips", (sg * 4.9, -3, -3.5), P["hu"], rest=(16, 0, 0))
        R.bone("hl_" + s, "hu_" + s, (0, -7.2, -1.4), P["hl"], rest=(-26, 0, 0))
        R.bone("hp_" + s, "hl_" + s, (0, -6.2, 0.2), P["paw"], rest=(10, 0, 0))
        # 날개: 어깨 위에서 위·뒤로 솟는다
        R.bone("w0_" + s, "chest", (sg * 5.6, 6.4, 5.0), P["wbone"], rest=(-14, 0, -sg * 16))
        R.bone("w1_" + s, "w0_" + s, (0, 7.0, 0), P["wbone"], rest=(-4, 0, sg * 4))
        R.bone("w2_" + s, "w1_" + s, (0, 7.0, 0), P["wbone"], rest=(16, 0, sg * 4))
        for seg, fl in WING_FEATHERS.items():
            for j, (y, L, kind) in enumerate(fl):
                spread = (j / max(1, len(fl) - 1) - 0.5)
                base = {"w0": 58, "w1": 50, "w2": 34}[seg]
                R.bone(f"f_{seg}_{j}_{s}", f"{seg}_{s}", (sg * 0.3 * j, y, -0.6), P[f"f_{seg}_{j}"], rest=(base + spread * 22, sg * 3, 0))
    R.bone("tail0", "hips", (0, 3.4, -7.2), P["tail0"], rest=(-30, 0, 0))
    for k in range(1, 6):
        R.bone(f"tail{k}", f"tail{k - 1}", (0, 0, -3.6), P[f"tail{k}"], rest=(12, 0, 0))
    R.bone("tuft", "tail5", (0, 0, -3.4), P["tuft"], rest=(10, 0, 0))
    return R, parts, anims()


# ─────────────────────────────────────────────────────────────────────────────
def P_(*ds, **kw):
    out = {}
    for d in ds:
        out.update(d)
    out.update(kw)
    return out


def wings(lift=0.0, spread=0.0, fan=0.0, flap=0.0):
    """lift: 날개 뼈를 더 세움(-) / 눕힘(+), spread: 옆으로 벌림, fan: 깃털 부채 펼침, flap: 끝마디 접기"""
    d = {}
    for s, sg in (("l", 1), ("r", -1)):
        d["w0_" + s] = (lift, 0, -sg * spread)
        d["w1_" + s] = (flap * 0.5, 0, -sg * spread * 0.2)
        d["w2_" + s] = (flap, 0, 0)
        for seg, fl in WING_FEATHERS.items():
            for j in range(len(fl)):
                sp = (j / max(1, len(fl) - 1) - 0.5)
                d[f"f_{seg}_{j}_{s}"] = (-fan * (0.6 + sp), 0, 0)
    return d


def legs(fl=0, fr=0, pl=0, pr=0, hl=0, hr=0, ql=0, qr=0):
    return {"fu_l": (fl, 0, 0), "fu_r": (fr, 0, 0), "fl_l": (pl, 0, 0), "fl_r": (pr, 0, 0),
            "hu_l": (hl, 0, 0), "hu_r": (hr, 0, 0), "hl_l": (ql, 0, 0), "hl_r": (qr, 0, 0)}


def tail(t, a=10):
    return {f"tail{k}": (4 * np.sin(t - k * 0.6), a * np.sin(t - k * 0.5), 0) for k in range(6)}


def lap(t):
    return {"lappet_l": (3 * np.sin(t), 0, 0), "lappet_r": (3 * np.sin(t + 0.8), 0, 0)}


def anims():
    A = {}
    A["idle"] = dict(loop=True, keys=[(P_(wings(2 * np.sin(t), 0, 4 * np.sin(t)), tail(t), lap(t), chest=(-3 + np.sin(t), 0, 0),
                                          head=(-4 + 1.5 * np.sin(t + 1), 0, 0), _root=(0, 0.3 * np.sin(t), 0)), 10)
                                      for t in np.linspace(0, 2 * np.pi, 5)[:-1]])
    walk = []
    for i in range(6):
        ph = i / 6 * 2 * np.pi
        s = np.sin(ph)
        walk.append((P_(legs(-24 * s, 24 * s, 18 * max(0, s), 18 * max(0, -s), 22 * s, -22 * s, -12 * max(0, -s), -12 * max(0, s)),
                        wings(4 * s, 0, 6), tail(ph, 16), lap(ph), head=(-4, 4 * s, 0), _root=(0, -0.5 * abs(np.cos(ph)), 0)), 4))
    A["walk"] = dict(loop=True, keys=walk)
    A["claw"] = dict(loop=False, keys=[
        (P_(legs(-12, -100, 0, 34, 10, 10), wings(-10, 20, 10), chest=(-14, 0, 0), head=(8, 0, 0), _root=(0, 1.2, 0)), 6),
        (P_(legs(-10, -20, 0, 0, 12, 12), wings(4, 10, 4), chest=(8, 0, 0), head=(-6, 0, 0), _root=(0, -0.8, 1)), 3),
        (P_(legs(-10, -16, 0, 0, 12, 12), wings(4, 10, 4), chest=(6, 0, 0), head=(-4, 0, 0), _root=(0, -0.8, 1)), 5),
        (P_(legs(), wings()), 8),
    ])
    # 석화의 수수께끼: 뒷다리로 앉아 상체를 세우고 날개를 하늘로 활짝 — 눈이 빛난다
    rear = P_(legs(-26, -26, 18, 18, 56, 56, -40, -40), chest=(-32, 0, 0), head=(26, 0, 0), _root=(0, -2.6, -2))
    A["riddle"] = dict(loop=False, keys=[
        (P_(rear, wings(-4, 30, -30, -6), tail(0, 4)), 14),
        (P_(rear, wings(-8, 38, -40, -10), tail(1, 6), lap(1)), 40),
        (P_(legs(), wings()), 12),
    ])
    A["mark"] = dict(loop=False, keys=[
        (P_(legs(), wings(-6, 18, -14), head=(-16, 0, 0), chest=(-6, 0, 0)), 8),
        (P_(legs(), wings(0, 26, -20), head=(10, 0, 0), chest=(4, 0, 0), _root=(0, -0.6, 0)), 6),
        (P_(legs(), wings()), 10),
    ])
    # 봉인의 고리: 날개를 낮게 둥글게 펼쳐 몸을 감싼다
    A["seal"] = dict(loop=False, keys=[
        (P_(legs(-20, -20, 30, 30, -10, -10, 20, 20), wings(30, 64, 14, 30), chest=(10, 0, 0), head=(-16, 0, 0), _root=(0, -2.6, 0)), 12),
        (P_(legs(-24, -24, 34, 34, -12, -12, 22, 22), wings(34, 72, 18, 36), chest=(12, 0, 0), head=(-20, 0, 0), _root=(0, -3.0, 0)), 36),
        (P_(legs(), wings()), 12),
    ])
    A["stun"] = dict(loop=False, keys=[
        (P_(legs(-50, -50, 70, 70, 60, 60, -60, -60), wings(50, 20, 30, 20), chest=(6, 0, 12), head=(30, 20, 0), _root=(0, -6, 0)), 8),
        (P_(legs(-50, -50, 70, 70, 60, 60, -60, -60), wings(54, 20, 30, 24), chest=(6, 0, 14), head=(34, 24, 0), _root=(0, -6.2, 0)), 30),
    ])
    A["death"] = dict(loop=False, keys=[
        (P_(legs(-60, -60, 80, 80, 70, 70, -70, -70), wings(60, 30, 30, 30), chest=(10, 0, 30), head=(40, 30, 0), _root=(0, -8, 0)), 16),
        (P_(legs(-60, -60, 80, 80, 70, 70, -70, -70), wings(70, 40, 30, 40), chest=(10, 0, 70), head=(40, 30, 0), _root=(0, -10, 0)), 14),
    ])
    return A


INFO = dict(hitbox="iron_golem", hit_scale=1.3, portrait=dict(bone="head", dist=1.7, cy=1.8, cz=3.0))
