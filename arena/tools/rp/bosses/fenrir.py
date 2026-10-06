"""서리 늑대 펜리르 — 신들도 두려워한 거대한 늑대. 끊어진 족쇄 · 등을 따라 솟은 빙정 · 서리 갈기 · 푸르게 빛나는 눈

 빙하 왕국 맵 보스 (정원 투기장). 스킬: 서리 도약(웅크렸다 덮침) · 빙결 포효(앞 부채꼴 서리 숨) · 얼음 송곳니(사냥감마다 얼음 가시)
"""
import numpy as np

from modelkit import *
from _hound import build_hound, hound_anims

ICE = Mat((168, 226, 255), var=0.10, edge_dark=0.16, top_light=0.30)
IRON = Mat((84, 88, 104), var=0.05, edge_dark=0.30, top_light=0.30, pattern=metal((150, 190, 230), 0.3, 0.05))
M = dict(
    body=Mat((196, 206, 222), var=0.06, edge_dark=0.26, top_light=0.24, pattern=fur((150, 164, 188), (240, 246, 255))),
    body_d=Mat((150, 162, 186), var=0.06, edge_dark=0.28, top_light=0.22, pattern=fur((110, 122, 150), (200, 210, 230))),
    belly=Mat((236, 240, 248), var=0.04, edge_dark=0.2, top_light=0.2, pattern=fur((200, 210, 226), (255, 255, 255))),
    mane=Mat((120, 150, 196), var=0.07, edge_dark=0.24, top_light=0.24, pattern=fur((80, 106, 150), (190, 216, 246))),
    claw=Mat((210, 236, 255), var=0.04, edge_dark=0.2, top_light=0.3),
    eye=Mat((130, 236, 255), var=0.02, edge_dark=0.0, top_light=0.0),
    mouth=Mat((40, 30, 52), var=0.05, edge_dark=0.1),
    fang=Mat((236, 244, 255), var=0.03, edge_dark=0.2, top_light=0.2),
    collar=IRON,
)


def deco(P):
    # 등을 따라 솟은 빙정 (앞쪽이 높게)
    sp = []
    for i, (z, h) in enumerate(((2, 9), (-2, 8), (-6, 7), (-10, 5))):
        for x, hh in ((0, h), (-2.6, h * 0.6), (2.6, h * 0.6)):
            sp.append(Box((x - 1.0, 0, z - 1.0), (x + 1.0, hh, z + 1.0), ICE, rot=("x", -22.5, (x, 0, z)), glow=True))
    P["spines"] = Part("spines", sp, glow=True)
    # 끊어진 족쇄 (앞다리 두 개) + 늘어진 사슬
    P["shackle"] = Part("shackle", rbox((-3.2, -2.0, -3.2), (3.2, 0.6, 3.2), IRON, r=0.6)
                        + [Box((x - 0.5, -6.0 - i * 2.4, -0.5), (x + 0.5, -3.6 - i * 2.4, 0.5), IRON) for i, x in enumerate((2.6, 3.2, 2.4))]
                        + [Box((x - 1.0, -5.0 - i * 2.4, -0.4), (x + 1.0, -4.6 - i * 2.4, 0.4), IRON) for i, x in enumerate((2.6, 3.2, 2.4))])
    return [("spines", "body", (0, 5.2, 0), "spines", (0, 0, 0)),
            ("spines2", "chest", (0, 8.4, 0), "spines", (0, 0, 0)),
            ("shackle_l", "fl_l", (0, -5.0, 0), "shackle", (0, 0, 0)),
            ("shackle_r", "fl_r", (0, -5.0, 0), "shackle", (0, 30, 0))]


def build():
    R, parts, H = build_hound("fenrir", 2.7, M, [(0, 0, 1.25)], deco)
    return R, parts, hound_anims(H, lambda t: {"shackle_l": (0, 0, 6 * np.sin(t)), "shackle_r": (0, 0, -6 * np.sin(t))})


INFO = dict(hitbox="iron_golem", hit_scale=2.8, portrait=dict(bone="head", dist=1.9, cy=2.0, cz=6.0))
