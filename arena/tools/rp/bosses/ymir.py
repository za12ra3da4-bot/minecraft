"""서리 거인 이미르 — 빙하 왕국의 거인 왕. 얼음 왕관 · 얼어붙은 수염 · 어깨와 등에 솟은 빙정 · 서리 대검

 빙하 왕국 맵 보스 (채석장 투기장). 스킬: 빙하 붕괴(얼음 기둥 세 줄) · 눈사태(얼음 덩어리 낙하) · 절대 영도(바깥 고리 빙결 → 안쪽 폭발)
 파츠: 거인 공용(_giant) + 왕관 · 수염 · 빙정 · 등 가시
"""
import numpy as np

from modelkit import *
from _giant import build_giant, giant_anims

ICE = Mat((168, 224, 255), var=0.10, edge_dark=0.18, top_light=0.30)
ICE_D = Mat((110, 180, 236), var=0.10, edge_dark=0.22, top_light=0.26)
M = dict(
    skin=Mat((150, 186, 214), var=0.06, edge_dark=0.28, top_light=0.26, spots=((122, 160, 196), 0.24, 3)),
    skin_d=Mat((118, 152, 186), var=0.06, edge_dark=0.30, top_light=0.24, spots=((96, 128, 164), 0.2, 3)),
    armor=Mat((92, 108, 138), var=0.05, edge_dark=0.30, top_light=0.30, pattern=metal((170, 210, 240), 0.32, 0.03)),
    armor_d=Mat((60, 72, 98), var=0.05, edge_dark=0.30, top_light=0.26, pattern=metal((130, 170, 210), 0.3, 0.02)),
    trim=Mat((214, 228, 242), var=0.04, edge_dark=0.32, top_light=0.30, pattern=combine(metal((160, 190, 220), 0.3, 0.0), greek_band(0.5, (250, 254, 255), (90, 120, 160)))),
    cloth=Mat((64, 80, 120), var=0.07, edge_dark=0.26, top_light=0.2, pattern=stripes((64, 80, 120), (52, 66, 102), 2)),
    fur=Mat((214, 220, 230), var=0.05, edge_dark=0.22, top_light=0.24, pattern=fur((170, 180, 196), (250, 252, 255))),
    eye=Mat((160, 246, 255), var=0.02, edge_dark=0.0, top_light=0.0),
    glow=Mat((130, 226, 255), var=0.04, edge_dark=0.0, top_light=0.0),
    blade=Mat((176, 230, 255), var=0.08, edge_dark=0.10, top_light=0.2),
    blade_core=Mat((240, 252, 255), var=0.02, edge_dark=0.0, top_light=0.0),
    hilt=Mat((196, 212, 232), var=0.04, edge_dark=0.30, top_light=0.30, pattern=metal((150, 180, 210), 0.3, 0.0)),
    grip=Mat((54, 64, 88), var=0.06, edge_dark=0.25, pattern=stripes((54, 64, 88), (36, 44, 64), 1, vertical=False)),
    sole=Mat((22, 28, 42), var=0.04, edge_dark=0.1),
)


def deco(P):
    # 얼음 왕관: 둘레에 높낮이가 다른 빙정 가시 9개
    crown = rbox((-5.2, 0, -4.8), (5.2, 1.6, 5.0), M["trim"], r=0.5)
    for i, (x, z, h) in enumerate(((-4.2, 3.8, 4.5), (-2.2, 4.4, 6.5), (0, 4.6, 8.5), (2.2, 4.4, 6.5), (4.2, 3.8, 4.5),
                                   (-4.6, 0, 5.0), (4.6, 0, 5.0), (-3.0, -4.0, 4.0), (3.0, -4.0, 4.0))):
        crown.append(Box((x - 0.8, 1.2, z - 0.8), (x + 0.8, 1.2 + h, z + 0.8), ICE, glow=True))
        crown.append(Box((x - 0.4, 1.2 + h, z - 0.4), (x + 0.4, 2.2 + h, z + 0.4), ICE, glow=True))
    P["crown"] = Part("crown", crown, glow=True)
    # 얼어붙은 수염 (고드름처럼 끝이 가늘게)
    beard = rbox((-4.2, -5.0, -0.6), (4.2, 0, 2.6), M["fur"], r=0.8)
    for i, x in enumerate((-3.2, -1.6, 0, 1.6, 3.2)):
        L = (9, 11, 13, 11, 9)[i]
        beard.append(Box((x - 0.8, -L, -0.2), (x + 0.8, -4.6, 1.8), M["fur"]))
        beard.append(Box((x - 0.4, -L - 2.4, 0.2), (x + 0.4, -L, 1.4), ICE, glow=True))
    P["beard"] = Part("beard", beard)
    # 어깨 빙정 (어깨 갑옷 위로 비스듬히)
    for s, sg in (("l", 1), ("r", -1)):
        sh = []
        for (x, z, h, a) in ((0, 0, 9, 0), (sg * 2.6, 2.4, 6, 22.5), (-sg * 1.8, -2.8, 7, -22.5), (sg * 3.2, -1.6, 5, 22.5)):
            sh.append(Box((x - 1.2, 0, z - 1.2), (x + 1.2, h, z + 1.2), ICE, rot=("z", -sg * a if a else 0, (x, 0, z)), glow=True))
            sh.append(Box((x - 0.5, h, z - 0.5), (x + 0.5, h + 1.6, z + 0.5), M["blade_core"], rot=("z", -sg * a if a else 0, (x, 0, z)), glow=True))
        P["shard_" + s] = Part("shard_" + s, sh, glow=True)
    # 등에 솟은 빙정 줄기
    spine = []
    for i, (x, y, h) in enumerate(((0, 0, 10), (-3.6, -2, 7), (3.6, -2, 7), (-6, -5, 5), (6, -5, 5))):
        spine.append(Box((x - 1.3, y, -1.3), (x + 1.3, y + h, 1.3), ICE_D, rot=("x", -22.5, (x, y, 0)), glow=True))
        spine.append(Box((x - 0.6, y + h, -0.6), (x + 0.6, y + h + 2, 0.6), ICE, rot=("x", -22.5, (x, y, 0)), glow=True))
    P["spine"] = Part("spine", spine, glow=True)
    return [("crown", "head", (0, 8.0, 0), "crown", (0, 0, 0)),
            ("beard", "jaw", (0, -2.4, 3.2), "beard", (8, 0, 0)),
            ("shard_l", "pauldron_l", (0, 3.0, 0), "shard_l", (0, 0, 0)),
            ("shard_r", "pauldron_r", (0, 3.0, 0), "shard_r", (0, 0, 0)),
            ("spine", "chest", (0, 9.0, -6.6), "spine", (-10, 0, 0))]


def build():
    R, parts = build_giant("ymir", 2.4, M, deco)
    return R, parts, giant_anims(lambda t: {"shard_l": (0, 0, 2 * np.sin(t)), "shard_r": (0, 0, -2 * np.sin(t)), "crown": (0, 3 * np.sin(t), 0)})


INFO = dict(hitbox="iron_golem", hit_scale=3.0, portrait=dict(bone="head", dist=1.9, cy=4.2, cz=3.0))
