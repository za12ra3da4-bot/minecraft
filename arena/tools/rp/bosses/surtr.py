"""화염 거인 수르트 — 무스펠헤임의 군주. 용암이 흐르는 흑요암 몸 · 휘어진 뿔 · 불꽃 머리칼과 수염 · 가슴의 용암 심장 · 불의 대검

 화산 군도 맵 보스 (대장간 투기장). 스킬: 멸망의 검(일직선 화염 내려찍기) · 화염 비(운석 낙하) · 라그나로크(불의 고리 세 겹)
"""
import numpy as np

from modelkit import *
from _giant import build_giant, giant_anims


def lava_cracks(c1=(255, 120, 20), c2=(255, 200, 80)):
    """흑요암 위 갈라진 용암 줄"""
    def fn(a, face, w, h, r):
        if w < 3 or h < 3:
            return
        for _ in range(max(1, (w * h) // 40)):
            x, y = int(r.integers(0, w)), int(r.integers(0, h))
            for _ in range(int(r.integers(2, 6))):
                if 0 <= x < w and 0 <= y < h:
                    a[y, x, :3] = col(c1) if r.random() < 0.7 else col(c2)
                x += int(r.integers(-1, 2)); y += int(r.integers(0, 2))
    return fn


FLAME = Mat((255, 136, 30), var=0.10, edge_dark=0.08, top_light=0.25)
FLAME_Y = Mat((255, 214, 90), var=0.06, edge_dark=0.0, top_light=0.1)
HORN = Mat((40, 30, 28), var=0.05, edge_dark=0.32, top_light=0.32, pattern=stripes((40, 30, 28), (66, 46, 36), 1, vertical=False))
M = dict(
    skin=Mat((56, 40, 36), var=0.07, edge_dark=0.30, top_light=0.24, pattern=lava_cracks()),
    skin_d=Mat((42, 30, 28), var=0.07, edge_dark=0.30, top_light=0.22, pattern=lava_cracks()),
    armor=Mat((50, 44, 46), var=0.05, edge_dark=0.30, top_light=0.30, pattern=metal((230, 110, 40), 0.3, 0.04)),
    armor_d=Mat((32, 28, 30), var=0.05, edge_dark=0.30, top_light=0.26, pattern=metal((200, 90, 30), 0.3, 0.03)),
    trim=Mat((214, 150, 60), var=0.05, edge_dark=0.32, top_light=0.30, pattern=combine(metal((150, 90, 30), 0.3, 0.0), greek_band(0.5, (255, 214, 120), (90, 40, 10)))),
    cloth=Mat((96, 26, 18), var=0.07, edge_dark=0.26, top_light=0.18, pattern=stripes((96, 26, 18), (70, 18, 12), 2)),
    fur=Mat((44, 32, 30), var=0.06, edge_dark=0.24, top_light=0.2, pattern=fur((24, 16, 14), (90, 50, 30))),
    eye=Mat((255, 230, 110), var=0.02, edge_dark=0.0, top_light=0.0),
    glow=Mat((255, 150, 40), var=0.06, edge_dark=0.0, top_light=0.0),
    blade=Mat((255, 146, 40), var=0.10, edge_dark=0.08, top_light=0.2),
    blade_core=Mat((255, 240, 170), var=0.03, edge_dark=0.0, top_light=0.0),
    hilt=Mat((70, 56, 54), var=0.05, edge_dark=0.30, top_light=0.30, pattern=metal((255, 140, 50), 0.3, 0.02)),
    grip=Mat((44, 26, 22), var=0.06, edge_dark=0.25, pattern=stripes((44, 26, 22), (70, 40, 30), 1, vertical=False)),
    sole=Mat((16, 10, 10), var=0.04, edge_dark=0.1),
)


def deco(P):
    # 휘어진 큰 뿔 (세 마디가 바깥 → 위 → 앞으로 휨)
    for s, sg in (("l", 1), ("r", -1)):
        P["horn_" + s] = Part("horn_" + s, rbox((-1.8, -1.8, -1.8), (1.8, 1.8, 7.0), HORN, r=0.6) + rbox((-1.4, -1.4, 6.0), (1.4, 1.4, 12.0), HORN, r=0.5)
                              + [Box((-0.8, -0.8, 11.4), (0.8, 0.8, 15.4), HORN), Box((-0.4, -0.4, 15.0), (0.4, 0.4, 17.4), FLAME, glow=True)])
    # 불꽃 머리칼 (뒤로 솟는 불길 여러 겹)
    fl = []
    for i, (x, z, h) in enumerate(((0, 1.6, 11), (-2.6, 0.6, 9), (2.6, 0.6, 9), (-1.4, -2.4, 12), (1.4, -2.4, 12), (0, -4.6, 10), (-3.8, -2, 7), (3.8, -2, 7))):
        fl.append(Box((x - 1.4, 0, z - 1.4), (x + 1.4, h, z + 1.4), FLAME, rot=("x", -22.5, (x, 0, z)), glow=True))
        fl.append(Box((x - 0.7, h * 0.4, z - 0.7), (x + 0.7, h + 1.8, z + 0.7), FLAME_Y, rot=("x", -22.5, (x, 0, z)), glow=True))
    P["flame"] = Part("flame", fl, glow=True)
    # 불꽃 수염
    beard = []
    for i, x in enumerate((-3.2, -1.6, 0, 1.6, 3.2)):
        L = (6, 8, 10, 8, 6)[i]
        beard.append(Box((x - 0.9, -L, -0.2), (x + 0.9, 0, 1.8), FLAME, glow=True))
        beard.append(Box((x - 0.4, -L - 1.6, 0.4), (x + 0.4, -L * 0.4, 1.4), FLAME_Y, glow=True))
    P["beard"] = Part("beard", beard, glow=True)
    # 어깨 쇠가시
    for s, sg in (("l", 1), ("r", -1)):
        sp = []
        for (x, z, h, a) in ((0, 0, 7, 0), (sg * 3.0, 2.6, 5, 22.5), (sg * 3.0, -2.6, 5, 22.5)):
            sp.append(Box((x - 1.1, 0, z - 1.1), (x + 1.1, h, z + 1.1), M["armor_d"], rot=("z", -sg * a if a else 0, (x, 0, z))))
            sp.append(Box((x - 0.5, h, z - 0.5), (x + 0.5, h + 1.4, z + 0.5), FLAME, rot=("z", -sg * a if a else 0, (x, 0, z)), glow=True))
        P["shard_" + s] = Part("shard_" + s, sp)
    # 등의 불길 (날개처럼 솟음)
    spine = []
    for i, (x, y, h) in enumerate(((0, 0, 11), (-4, -2, 8), (4, -2, 8), (-7, -5, 6), (7, -5, 6))):
        spine.append(Box((x - 1.5, y, -1.5), (x + 1.5, y + h, 1.5), FLAME, rot=("x", -22.5, (x, y, 0)), glow=True))
        spine.append(Box((x - 0.7, y + h * 0.5, -0.7), (x + 0.7, y + h + 1.6, 0.7), FLAME_Y, rot=("x", -22.5, (x, y, 0)), glow=True))
    P["spine"] = Part("spine", spine, glow=True)
    return [("horn_l", "head", (4.6, 6.4, 0), "horn_l", (-34, 75, 0)),
            ("horn_r", "head", (-4.6, 6.4, 0), "horn_r", (-34, -75, 0)),
            ("flame", "head", (0, 7.6, -1.0), "flame", (0, 0, 0)),
            ("beard", "jaw", (0, -2.2, 3.2), "beard", (10, 0, 0)),
            ("shard_l", "pauldron_l", (0, 3.0, 0), "shard_l", (0, 0, 0)),
            ("shard_r", "pauldron_r", (0, 3.0, 0), "shard_r", (0, 0, 0)),
            ("spine", "chest", (0, 9.0, -6.6), "spine", (-14, 0, 0))]


def build():
    R, parts = build_giant("surtr", 2.5, M, deco)
    return R, parts, giant_anims(lambda t: {"flame": (4 * np.sin(t * 2), 6 * np.sin(t), 0), "spine": (3 * np.sin(t * 2), 0, 0)})


INFO = dict(hitbox="iron_golem", hit_scale=3.1, portrait=dict(bone="head", dist=1.9, cy=4.2, cz=3.0))
