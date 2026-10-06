"""지옥견 케르베로스 — 타르타로스의 문지기. 머리 셋 · 가시 목걸이 · 용암이 흐르는 검은 털 · 불꽃 갈기 · 뱀 꼬리

 화산 군도 맵 보스 (모래 신전 투기장). 스킬: 지옥 돌진(일직선 돌진) · 삼두 화염(세 방향 불 숨) · 용암 웅덩이(사냥감 발밑 용암)
"""
import numpy as np

from modelkit import *
from _hound import build_hound, hound_anims


def lava_cracks(c1=(255, 110, 20), c2=(255, 190, 70)):
    def fn(a, face, w, h, r):
        if w < 3 or h < 3:
            return
        for _ in range(max(1, (w * h) // 50)):
            x, y = int(r.integers(0, w)), int(r.integers(0, h))
            for _ in range(int(r.integers(2, 5))):
                if 0 <= x < w and 0 <= y < h:
                    a[y, x, :3] = col(c1) if r.random() < 0.7 else col(c2)
                x += int(r.integers(-1, 2)); y += int(r.integers(0, 2))
    return fn


FLAME = Mat((255, 130, 30), var=0.10, edge_dark=0.06, top_light=0.25)
FLAME_Y = Mat((255, 214, 90), var=0.05, edge_dark=0.0, top_light=0.1)
GOLD = Mat((214, 160, 60), var=0.05, edge_dark=0.32, top_light=0.30, pattern=metal((140, 80, 30), 0.3, 0.02))
SCALE = Mat((54, 30, 30), var=0.06, edge_dark=0.28, top_light=0.24, pattern=scales((24, 10, 10), 4, 1.4))
M = dict(
    body=Mat((40, 30, 30), var=0.07, edge_dark=0.28, top_light=0.24, pattern=combine(fur((22, 16, 16), (70, 50, 46)), lava_cracks())),
    body_d=Mat((30, 22, 22), var=0.07, edge_dark=0.30, top_light=0.22, pattern=lava_cracks()),
    belly=Mat((70, 40, 34), var=0.06, edge_dark=0.22, top_light=0.2, pattern=lava_cracks()),
    mane=Mat((110, 36, 20), var=0.08, edge_dark=0.24, top_light=0.24, pattern=fur((70, 20, 10), (220, 90, 30))),
    claw=Mat((240, 196, 120), var=0.04, edge_dark=0.26, top_light=0.3),
    eye=Mat((255, 70, 30), var=0.02, edge_dark=0.0, top_light=0.0),
    mouth=Mat((255, 110, 30), var=0.06, edge_dark=0.1),
    fang=Mat((240, 228, 200), var=0.03, edge_dark=0.2, top_light=0.2),
    collar=GOLD,
)


def deco(P):
    # 불꽃 갈기 (가슴 위로 활활)
    fl = []
    for i, (x, z, h) in enumerate(((0, 2, 9), (-4, 1, 7), (4, 1, 7), (-2, -2, 8), (2, -2, 8), (-6, -1, 5), (6, -1, 5))):
        fl.append(Box((x - 1.5, 0, z - 1.5), (x + 1.5, h, z + 1.5), FLAME, rot=("x", -22.5, (x, 0, z)), glow=True))
        fl.append(Box((x - 0.7, h * 0.4, z - 0.7), (x + 0.7, h + 1.8, z + 0.7), FLAME_Y, rot=("x", -22.5, (x, 0, z)), glow=True))
    P["flame"] = Part("flame", fl, glow=True)
    # 등 가시 (흑요암)
    P["spikes"] = Part("spikes", [Box((x - 0.9, 0, z - 0.9), (x + 0.9, h, z + 0.9), Mat((26, 18, 24), var=0.05, edge_dark=0.3, top_light=0.4), rot=("x", -22.5, (x, 0, z)))
                                  for (x, z, h) in ((0, 0, 5), (0, -4, 6), (0, -8, 5), (-2.4, -2, 3), (2.4, -2, 3), (-2.4, -6, 3), (2.4, -6, 3))])
    # 뱀 꼬리 끝 (머리 + 불 혀)
    P["snake"] = Part("snake", rbox((-1.6, -1.4, -5.6), (1.6, 1.6, 0.4), SCALE, r=0.6) + [Box((-0.4, -0.6, -8.0), (0.4, 0.0, -5.4), FLAME, glow=True),
                      Box((-1.2, 0.6, -4.4), (-0.6, 1.2, -3.8), FLAME_Y, glow=True), Box((0.6, 0.6, -4.4), (1.2, 1.2, -3.8), FLAME_Y, glow=True)])
    return [("flame", "chest", (0, 8.2, -0.6), "flame", (0, 0, 0)),
            ("spikes", "body", (0, 5.4, -1), "spikes", (0, 0, 0)),
            ("snake", "tail2", (0, 0, -7.6), "snake", (0, 0, 0))]


def build():
    R, parts, H = build_hound("cerberus", 2.6, M, [(-6.4, 38, 0.95), (0, 0, 1.1), (6.4, -38, 0.95)], deco)
    for p in parts:
        if p.name in ("tail0", "tail1", "tail2"):
            for b in p.boxes:
                b.mat = SCALE
    return R, parts, hound_anims(H, lambda t: {"flame": (4 * np.sin(t * 2), 6 * np.sin(t), 0), "snake": (10 * np.sin(t), 20 * np.sin(t * 0.7), 0)})


INFO = dict(hitbox="iron_golem", hit_scale=2.9, portrait=dict(bone="head1", dist=1.9, cy=2.0, cz=6.0))
