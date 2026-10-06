"""네 발 짐승 보스 공용 뼈대 (펜리르 · 케르베로스) — 머리 수 · 재질 · 장식은 보스 파일이 정한다

 앞 = +Z. 몸통(뒤) · 가슴(앞) · 목/머리/턱 (1개 또는 3개) · 다리 4 (윗다리 · 아랫다리 · 발) · 꼬리 3마디
 애니메이션: idle · walk · bite(근접: 덮쳐 물기) · pounce(웅크렸다 도약) · howl(하늘 보고 울부짖음)
            breath(머리를 낮추고 입을 벌려 내뿜기) · stun · death
"""
import numpy as np

from modelkit import *


def P_(*ds, **kw):
    out = {}
    for d in ds:
        out.update(d)
    out.update(kw)
    return out


def build_hound(name, k, M, heads, deco):
    """heads: [(목 x 위치, 목 좌우 각도, 머리 배율)], M: body, body_d, belly, mane, claw, eye, mouth, fang, collar, glow"""
    P = {}
    P["body"] = Part("body", rbox((-7.0, -6.2, -15), (7.0, 6.6, 4), M["body"], r=2.8)
                     + rbox((-5.6, -7.2, -12), (5.6, -3.4, 2), M["belly"], r=1.6)
                     + rbox((-7.6, -1.0, -15.6), (7.6, 4.0, -9.0), M["body_d"], r=1.6))
    P["chest"] = Part("chest", rbox((-8.4, -7.6, -3), (8.4, 8.2, 9), M["body"], r=3.0)
                      + rbox((-9.6, -2.6, -3.0), (9.6, 10.4, 7.0), M["mane"], r=3.0)
                      + rbox((-6.0, -9.0, 1), (6.0, -4.0, 9.6), M["mane"], r=1.8))
    P["neck"] = Part("neck", rbox((-4.0, -4.2, -1), (4.0, 4.2, 9), M["body"], r=1.6) + rbox((-4.6, -1.0, -1), (4.6, 5.4, 7), M["mane"], r=1.6))
    P["head"] = Part("head", [
        *rbox((-4.4, -3.2, -2.0), (4.4, 4.2, 6.0), M["body"], r=1.6),             # 머리통
        *rbox((-3.0, -2.8, 5.0), (3.0, 1.8, 9.0), M["body_d"], r=1.0),             # 주둥이 뿌리
        *rbox((-2.4, -2.6, 8.4), (2.4, 1.2, 12.4), M["body_d"], r=0.9),            # 주둥이 끝
        *rbox((-5.8, -3.0, -1.0), (-3.6, 1.4, 4.0), M["mane"], r=0.7), *rbox((3.6, -3.0, -1.0), (5.8, 1.4, 4.0), M["mane"], r=0.7),   # 볼 털
        Box((-1.2, 0.6, 12.0), (1.2, 1.8, 12.8), M["mouth"]),                      # 코
        *rbox((-4.8, 1.6, 2.0), (-1.2, 3.6, 4.2), M["body_d"], r=0.6), *rbox((1.2, 1.6, 2.0), (4.8, 3.6, 4.2), M["body_d"], r=0.6),   # 눈두덩
        Box((-2.2, -2.8, 6.0), (-1.6, -1.2, 11.8), M["fang"]), Box((1.6, -2.8, 6.0), (2.2, -1.2, 11.8), M["fang"]),                 # 윗니 줄
        Box((-2.4, -4.4, 10.4), (-1.6, -2.4, 11.2), M["fang"]), Box((1.6, -4.4, 10.4), (2.4, -2.4, 11.2), M["fang"]),             # 송곳니
    ])
    P["ear"] = Part("ear", [Box((-1.4, 0, -0.8), (1.4, 4.2, 0.8), M["body_d"]), Box((-0.8, 3.6, -0.6), (0.8, 5.8, 0.6), M["body_d"]), Box((-0.8, 0.6, 0.7), (0.8, 3.4, 0.9), M["mouth"])])
    P["eyes"] = Part("eyes", [Box((-3.8, -0.6, 0), (-1.6, 0.6, 0.4), M["eye"], glow=True), Box((1.6, -0.6, 0), (3.8, 0.6, 0.4), M["eye"], glow=True)], glow=True)
    P["jaw"] = Part("jaw", rbox((-2.4, -2.2, -0.5), (2.4, 0, 7.6), M["body_d"], r=0.7) + [Box((-1.9, -0.2, 0.5), (1.9, 0.3, 7.2), M["mouth"]),
                    Box((-2.2, 0, 6.2), (-1.4, 2.0, 7.0), M["fang"]), Box((1.4, 0, 6.2), (2.2, 2.0, 7.0), M["fang"])])
    P["collar"] = Part("collar", rbox((-4.4, -4.4, -1.2), (4.4, 4.6, 1.2), M["collar"], r=0.8)
                       + [Box((x - 0.6, 4.4, -0.6), (x + 0.6, 6.6, 0.6), M["claw"]) for x in (-3, 0, 3)]
                       + [Box((4.2, y - 0.6, -0.6), (6.4, y + 0.6, 0.6), M["claw"]) for y in (-2, 2)] + [Box((-6.4, y - 0.6, -0.6), (-4.2, y + 0.6, 0.6), M["claw"]) for y in (-2, 2)])
    P["leg_fu"] = Part("leg_fu", rbox((-3.4, -8.6, -3.6), (3.4, 2.0, 3.6), M["body"], r=1.4))
    P["leg_bu"] = Part("leg_bu", rbox((-3.8, -8.0, -4.4), (3.8, 2.6, 4.4), M["body"], r=1.6))
    P["leg_l"] = Part("leg_l", rbox((-2.4, -7.4, -2.4), (2.4, 0.6, 2.4), M["body_d"], r=0.9))
    P["paw"] = Part("paw", rbox((-3.0, -2.2, -2.4), (3.0, 0.4, 4.4), M["body_d"], r=0.9)
                    + [Box((-2.6 + i * 1.7, -2.4, 4.0), (-1.6 + i * 1.7, -0.6, 6.0), M["claw"]) for i in range(4)])
    for i in range(3):
        w_ = 2.6 - i * 0.6
        P[f"tail{i}"] = Part(f"tail{i}", rbox((-w_, -w_, -8), (w_, w_, 0.5), M["mane"] if i else M["body"], r=0.8))

    R = Rig(name, k)
    R.bone("body", None, (0, 17.6, -2), P["body"])
    R.bone("chest", "body", (0, 0.8, 4), P["chest"], rest=(-6, 0, 0))
    heads_ix = []
    for i, (x, ry_, s_) in enumerate(heads):
        sfx = "" if len(heads) == 1 else str(i)
        R.bone("neck" + sfx, "chest", (x, 4.6, 7.4), P["neck"], rest=(-34, ry_, 0))
        R.bone("collar" + sfx, "neck" + sfx, (0, 0, 2.4), P["collar"])
        R.bone("head" + sfx, "neck" + sfx, (0, 0.8, 8.4), P["head"], rest=(30, 0, 0), scale=s_)
        R.bone("eyes" + sfx, "head" + sfx, (0, 2.6, 4.25), P["eyes"])
        R.bone("jaw" + sfx, "head" + sfx, (0, -2.6, 4.2), P["jaw"], rest=(6, 0, 0))
        R.bone("ear_l" + sfx, "head" + sfx, (3.0, 3.8, 0.4), P["ear"], rest=(-10, 0, -16))
        R.bone("ear_r" + sfx, "head" + sfx, (-3.0, 3.8, 0.4), P["ear"], rest=(-10, 0, 16))
        heads_ix.append(sfx)
    for s, sg in (("l", 1), ("r", -1)):
        R.bone("fu_" + s, "chest", (sg * 5.8, -4.6, 3.6), P["leg_fu"], rest=(6, 0, 0))
        R.bone("fl_" + s, "fu_" + s, (0, -8.2, 0), P["leg_l"], rest=(-6, 0, 0))
        R.bone("fp_" + s, "fl_" + s, (0, -7.2, 0), P["paw"])
        R.bone("bu_" + s, "body", (sg * 5.2, -2.2, -11.6), P["leg_bu"], rest=(-14, 0, 0))
        R.bone("bl_" + s, "bu_" + s, (0, -7.8, 0.6), P["leg_l"], rest=(22, 0, 0))
        R.bone("bp_" + s, "bl_" + s, (0, -7.2, 0), P["paw"], rest=(-8, 0, 0))
    R.bone("tail0", "body", (0, 3.0, -14.6), P["tail0"], rest=(-30, 0, 0))
    R.bone("tail1", "tail0", (0, 0, -7.6), P["tail1"], rest=(12, 0, 0))
    R.bone("tail2", "tail1", (0, 0, -7.6), P["tail2"], rest=(12, 0, 0))
    for (bn, par, off, part, rest) in deco(P):
        R.bone(bn, par, off, P[part] if isinstance(part, str) else part, rest=rest)
    return R, list(P.values()), heads_ix


def _heads(H, fn):
    d = {}
    for i, sfx in enumerate(H):
        d.update(fn(sfx, i))
    return d


def legs4(fl=0, fr=0, bl=0, br=0, kfl=0, kfr=0, kbl=0, kbr=0):
    return {"fu_l": (fl, 0, 0), "fu_r": (fr, 0, 0), "bu_l": (bl, 0, 0), "bu_r": (br, 0, 0),
            "fl_l": (kfl, 0, 0), "fl_r": (kfr, 0, 0), "bl_l": (kbl, 0, 0), "bl_r": (kbr, 0, 0)}


def tail(t, a=1.0, up=0):
    return {"tail0": (up + 4 * a * np.sin(t * 0.5), 10 * a * np.sin(t), 0), "tail1": (up * 0.5, 14 * a * np.sin(t - 0.7), 0), "tail2": (0, 18 * a * np.sin(t - 1.4), 0)}


def hound_anims(H, extra=None):
    ex = extra or (lambda t: {})
    A = {}
    look = lambda t: _heads(H, lambda s, i: {"head" + s: (3 * np.sin(t + i), 8 * np.sin(t * 0.5 + i * 1.7), 0), "jaw" + s: (4 + 3 * np.sin(t * 2 + i), 0, 0)})
    A["idle"] = dict(loop=True, keys=[(P_(tail(t, 0.6), look(t), ex(t), chest=(1.5 * np.sin(t), 0, 0), _root=(0, 0.3 * np.sin(t), 0)), 12)
                                      for t in np.linspace(0, 2 * np.pi, 5)[:-1]])
    walk = []
    for i in range(6):
        ph = i / 6 * 2 * np.pi
        s = np.sin(ph)
        walk.append((P_(legs4(26 * s, -26 * s, -24 * s, 24 * s, -20 * max(0, -s), -20 * max(0, s), 18 * max(0, s), 18 * max(0, -s)),
                        tail(ph * 2, 1.0), look(ph), ex(ph), chest=(2 * s, 3 * s, 0), _root=(0, -0.8 * abs(np.cos(ph)), 0)), 4))
    A["walk"] = dict(loop=True, keys=walk)
    # 덮쳐 물기 (근접)
    bite_open = _heads(H, lambda s, i: {"head" + s: (-24, 0, 0), "jaw" + s: (44, 0, 0)})
    bite_shut = _heads(H, lambda s, i: {"head" + s: (24, 0, 0), "jaw" + s: (0, 0, 0)})
    A["bite"] = dict(loop=False, keys=[
        (P_(legs4(-20, -20, 30, 30, 20, 20, -20, -20), bite_open, tail(0, 1, 20), ex(0), chest=(10, 0, 0), _root=(0, -2.5, -2)), 10),
        (P_(legs4(-60, -60, 10, 10, 10, 10, -10, -10), bite_shut, tail(1, 1, 20), ex(1), chest=(-10, 0, 0), _root=(0, 1, 9)), 3),
        (P_(legs4(-30, -30, 10, 10, 0, 0, 0, 0), bite_shut, tail(2, 1, 10), ex(2), chest=(6, 0, 0), _root=(0, -1, 7)), 8),
        (P_(tail(3, 0.6), ex(3)), 10),
    ])
    # 웅크렸다가 앞으로 크게 도약
    A["pounce"] = dict(loop=False, keys=[
        (P_(legs4(-30, -30, 40, 40, 40, 40, -40, -40), bite_open, tail(0, 1, 30), ex(0), chest=(14, 0, 0), _root=(0, -5, -3)), 16),
        (P_(legs4(-80, -80, -50, -50, -10, -10, 30, 30), bite_open, tail(1, 0.5, -10), ex(1), chest=(-16, 0, 0), _root=(0, 9, 4)), 5),
        (P_(legs4(-40, -40, 30, 30, 30, 30, -20, -20), bite_shut, tail(2, 1, 20), ex(2), chest=(12, 0, 0), _root=(0, -3, 6)), 4),
        (P_(legs4(-40, -40, 30, 30, 30, 30, -20, -20), bite_shut, tail(3, 1, 20), ex(3), chest=(12, 0, 0), _root=(0, -3, 6)), 8),
        (P_(tail(4, 0.6), ex(4)), 10),
    ])
    # 하늘을 보고 울부짖음
    howl = _heads(H, lambda s, i: {"neck" + s: (-40, 0, 0), "head" + s: (-40, (i - (len(H) - 1) / 2) * 10, 0), "jaw" + s: (40, 0, 0)})
    A["howl"] = dict(loop=False, keys=[
        (P_(legs4(18, 18, 30, 30, 0, 0, -30, -30), howl, tail(0, 1, 20), ex(0), chest=(-18, 0, 0), _root=(0, -1.2, 0)), 12),
        (P_(legs4(20, 20, 34, 34, 0, 0, -34, -34), howl, tail(2, 1.5, 24), ex(1), chest=(-20, 0, 0), _root=(0, -1.6, 0)), 30),
        (P_(tail(3, 0.6), ex(2)), 12),
    ])
    # 머리를 낮추고 입을 크게 벌려 내뿜기
    br = _heads(H, lambda s, i: {"neck" + s: (20, 0, 0), "head" + s: (-30, 0, 0), "jaw" + s: (50, 0, 0)})
    A["breath"] = dict(loop=False, keys=[
        (P_(legs4(-10, -10, 30, 30, 10, 10, -20, -20), _heads(H, lambda s, i: {"neck" + s: (-20, 0, 0), "head" + s: (-20, 0, 0), "jaw" + s: (30, 0, 0)}), tail(0, 1, 10), ex(0), chest=(-10, 0, 0), _root=(0, 0, -2)), 12),
        (P_(legs4(-20, -20, 30, 30, 20, 20, -30, -30), br, tail(1, 1.2, 10), ex(1), chest=(12, 0, 0), _root=(0, -2.5, 2)), 6),
        (P_(legs4(-20, -20, 30, 30, 20, 20, -30, -30), br, tail(3, 1.2, 10), ex(2), chest=(12, 0, 0), _root=(0, -2.5, 2)), 34),
        (P_(tail(4, 0.6), ex(3)), 12),
    ])
    lie = _heads(H, lambda s, i: {"head" + s: (40, (i - 1) * 20, 0), "jaw" + s: (10, 0, 0)})
    A["stun"] = dict(loop=False, keys=[
        (P_(legs4(-80, -80, 70, 70, 90, 90, -80, -80), lie, tail(0, 0.3), ex(0), chest=(10, 0, 8), _root=(0, -9, 0)), 8),
        (P_(legs4(-80, -80, 70, 70, 90, 90, -80, -80), lie, tail(1, 0.3), ex(1), chest=(12, 0, 10), _root=(0, -9.2, 0)), 30),
    ])
    A["death"] = dict(loop=False, keys=[
        (P_(legs4(-40, -40, 40, 40), _heads(H, lambda s, i: {"head" + s: (-30, 0, 0), "jaw" + s: (40, 0, 0)}), ex(0), chest=(-10, 0, 0), _root=(0, -3, 0)), 14),
        (P_(legs4(-90, -70, 60, 80, 30, 20, -20, -10), _heads(H, lambda s, i: {"head" + s: (20, 0, 30), "jaw" + s: (20, 0, 0)}), ex(1),
            chest=(0, 0, 0), _rootrot=(0, 0, 80), _root=(14, 2, 0)), 18),
    ])
    return A
