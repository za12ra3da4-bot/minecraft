"""상점 전설 무기 4종 (동양 무협) — 3D 아이템 모델. 손잡이 = 모델 원점, 날은 위(+Y)

 뇌정검(雷霆劍)   곧은 양날검 · 보랏빛 번개 홈 · 여의 구름 가드 · 붉은 수술
 청룡언월도       초승달 칼날 · 청룡 머리 · 붉은 옻칠 장대 · 비취 날선
 풍혼선(風魂扇)   펼친 철선 · 비취 한지에 물결 · 금테 · 바람 빛
 방천화극         창날 + 양쪽 초승달 날 · 봉황 깃 수술 · 금 장식
"""
import math

import numpy as np

from modelkit import *

STEEL = Mat((150, 160, 178), var=0.04, edge_dark=0.30, top_light=0.42, pattern=metal((120, 132, 152), 0.45, 0.02))
STEEL_D = Mat((150, 158, 176), var=0.04, edge_dark=0.32, top_light=0.35, pattern=metal((90, 98, 116), 0.4, 0.02))
GOLD = Mat((238, 190, 72), var=0.05, edge_dark=0.36, top_light=0.38, pattern=metal((160, 100, 26), 0.4, 0.0))
GOLD_D = Mat((190, 138, 44), var=0.05, edge_dark=0.36, top_light=0.3, pattern=metal((120, 74, 18), 0.35, 0.0))
JADE = Mat((70, 170, 130), var=0.06, edge_dark=0.3, top_light=0.35, spots=((40, 120, 92), 0.25, 2))
LACQUER = Mat((132, 20, 24), var=0.05, edge_dark=0.34, top_light=0.32, pattern=metal((80, 8, 12), 0.25, 0.0))
BLACK = Mat((34, 30, 36), var=0.05, edge_dark=0.3, top_light=0.25, pattern=stripes((34, 30, 36), (58, 52, 60), 1, vertical=False))
CORD = Mat((44, 34, 58), var=0.05, edge_dark=0.3, top_light=0.2, pattern=stripes((44, 34, 58), (92, 70, 120), 1, vertical=False))
TASSEL = Mat((196, 28, 32), var=0.06, edge_dark=0.25, top_light=0.2, pattern=stripes((196, 28, 32), (140, 14, 20), 1))
PAPER = Mat((196, 230, 212), var=0.05, edge_dark=0.06, top_light=0.08, spots=((150, 204, 182), 0.2, 3))
BLADE = Mat((142, 152, 172), var=0.03, edge_dark=0.16, top_light=0.22, pattern=metal((110, 120, 142), 0.45, 0.03))
FEATHER = Mat((232, 90, 40), var=0.05, edge_dark=0.28, top_light=0.2, pattern=stripes((232, 90, 40), (250, 180, 60), 1))
G_VIOLET = Mat((190, 160, 255), var=0.04, edge_dark=0.0, top_light=0.0)
G_JADE = Mat((140, 255, 200), var=0.04, edge_dark=0.0, top_light=0.0)
G_GOLD = Mat((255, 230, 140), var=0.04, edge_dark=0.0, top_light=0.0)
G_RED = Mat((255, 110, 70), var=0.04, edge_dark=0.0, top_light=0.0)


def B(lo, hi, m, **k):
    return Box(lo, hi, m, **k)


def mirror_x(boxes):
    out = list(boxes)
    for b in boxes:
        rot = None
        if b.rot:
            ax, ang, org = b.rot
            rot = (ax, -ang if ax in ("y", "z") else ang, (-org[0], org[1], org[2]))
        out.append(Box((-b.to[0], b.frm[1], b.frm[2]), (-b.frm[0], b.to[1], b.to[2]), b.mat, rot=rot, glow=not b.shade))
    return out


def tassel(x, y, z, L, mat=TASSEL):
    """아래로 늘어진 수술: 매듭 + 가닥 5개 (살짝 벌어짐)"""
    b = [B((x - 0.5, y - 1.2, z - 0.5), (x + 0.5, y, z + 0.5), GOLD), B((x - 0.8, y - 2.2, z - 0.8), (x + 0.8, y - 1.2, z + 0.8), mat)]
    for i, (dx, dz, ang) in enumerate(((0, 0, 0), (-0.5, 0, -22.5), (0.5, 0, 22.5), (0, -0.5, 0), (0, 0.5, 0))):
        l = L - (i % 2) * 1.2
        rot = ("z", ang, (x + dx, y - 2.2, z + dz)) if ang else None
        b.append(B((x + dx - 0.3, y - 2.2 - l, z + dz - 0.3), (x + dx + 0.3, y - 2.2, z + dz + 0.3), mat, rot=rot))
    return b


# ─────────────────────────────────────────────────────────── 뇌정검
def thunder():
    b = []
    # 날: 가장자리(밝은 강철) + 몸(어두운 강철) + 가운데 번개 홈(발광)
    for y0, y1, w in ((3.5, 17, 1.35), (17, 19.5, 1.1), (19.5, 21.5, 0.8), (21.5, 23, 0.45)):
        b += [B((-w, y0, -0.35), (w, y1, 0.35), BLADE), B((-w * 0.62, y0, -0.45), (w * 0.62, y1, 0.45), STEEL_D)]
    b += [B((-0.3, 5, -0.52), (0.3, 20, 0.52), G_VIOLET, glow=True)]
    for k in range(4):                                     # 번개 가지 새김
        y = 6.5 + k * 3.3
        s = 1 if k % 2 else -1
        b.append(B((min(0, s * 0.95), y, -0.5), (max(0, s * 0.95), y + 0.6, 0.5), G_VIOLET, glow=True))
    # 여의 구름 가드
    b += rbox((-2.6, 1.9, -1.05), (2.6, 3.6, 1.05), GOLD, r=0.45)
    b += mirror_x([B((2.2, 2.6, -0.8), (3.8, 4.6, 0.8), GOLD), B((3.2, 4.0, -0.6), (4.4, 5.2, 0.6), GOLD_D),
                   B((2.4, 1.2, -0.7), (3.4, 2.2, 0.7), GOLD_D)])
    b += [B((-0.9, 2.2, -1.15), (0.9, 3.3, 1.15), JADE), B((-0.4, 2.45, -1.25), (0.4, 3.05, 1.25), G_JADE, glow=True)]
    # 손잡이: 감은 끈 (마름모 감기) + 금 고리
    b += [B((-0.62, -4.4, -0.62), (0.62, 1.9, 0.62), CORD)]
    for y in (-3.8, -2.2, -0.6, 1.0):
        b.append(B((-0.72, y, -0.72), (0.72, y + 0.5, 0.72), BLACK))
    b += [B((-0.85, 1.3, -0.85), (0.85, 1.9, 0.85), GOLD), B((-0.85, -4.9, -0.85), (0.85, -4.3, 0.85), GOLD)]
    # 폼멜 + 수술
    b += rbox((-1.2, -6.4, -1.0), (1.2, -4.8, 1.0), GOLD, r=0.4) + [B((-0.45, -6.0, -1.1), (0.45, -5.2, 1.1), G_VIOLET, glow=True)]
    b += tassel(0, -6.4, 0, 7.5)
    return b


# ─────────────────────────────────────────────────────────── 청룡언월도
def dragon():
    b = [B((-0.6, -21, -0.6), (0.6, 9, 0.6), LACQUER)]
    for y in (-20, -12, -4, 4):
        b += [B((-0.75, y, -0.75), (0.75, y + 0.7, 0.75), GOLD)]
    b += [B((-0.8, -23.5, -0.8), (0.8, -21, 0.8), GOLD_D), B((-0.35, -24, -0.35), (0.35, -23.5, 0.35), GOLD)]
    # 청룡 머리 (칼날 뿌리, 입에서 날이 나옴)
    b += rbox((-1.4, 8.6, -1.5), (1.4, 12.2, 1.5), JADE, r=0.6)
    b += [B((-1.1, 11.4, -1.9), (1.1, 12.6, -1.4), JADE), B((-0.6, 12.2, -2.5), (0.6, 13.0, -1.8), JADE),
          B((-1.55, 11.0, -1.0), (-1.3, 11.8, -0.4), G_GOLD, glow=True), B((1.3, 11.0, -1.0), (1.55, 11.8, -0.4), G_GOLD, glow=True),
          B((-1.2, 12.2, 0.4), (-0.7, 14.4, 0.9), GOLD, rot=("x", 22.5, (-1, 12.2, 0.6))), B((0.7, 12.2, 0.4), (1.2, 14.4, 0.9), GOLD, rot=("x", 22.5, (1, 12.2, 0.6)))]
    b += [B((-0.9, 7.4, -0.9), (0.9, 8.6, 0.9), GOLD)]
    b += [B((-0.25, 7.8 - k * 1.1, 1.0 + k * 0.1), (0.25, 8.6 - k * 1.1, 1.6 + k * 0.1), TASSEL) for k in range(4)]   # 갈기
    # 언월 칼날: 등은 곧고, 날은 바깥(+x)으로 불룩, 끝은 등쪽으로 휘어 뾰족
    b += [B((-1.2, 11.8, -0.4), (3.0, 20.0, 0.4), BLADE), B((3.0, 13.8, -0.36), (4.2, 19.2, 0.36), BLADE),
          B((-1.2, 20.0, -0.36), (2.2, 23.4, 0.36), BLADE, rot=("z", 22.5, (-1.2, 20.0, 0))),
          B((4.2, 14.2, -0.28), (4.8, 18.8, 0.28), G_JADE, glow=True), B((3.0, 12.2, -0.28), (3.6, 13.8, 0.28), G_JADE, glow=True),
          B((2.2, 20.0, -0.28), (2.8, 23.0, 0.28), G_JADE, glow=True, rot=("z", 22.5, (-1.2, 20.0, 0))),
          B((-1.6, 11.8, -0.5), (-0.7, 20.8, 0.5), STEEL_D), B((0.2, 14.5, -0.46), (1.2, 18.5, 0.46), G_JADE, glow=True)]
    for k in range(3):                                       # 날등 톱니
        y = 14 + k * 3
        b.append(B((-2.3, y, -0.35), (-1.3, y + 1.2, 0.35), STEEL_D))
    return b


# ─────────────────────────────────────────────────────────── 풍혼선
def wind():
    b = []
    piv = (0, 0, 0)
    angs = (-45, -22.5, 0, 22.5, 45)
    for i, a in enumerate(angs):
        rot = ("z", a, piv) if a else None
        # 한지 판 (살 사이를 채움, 겹쳐서 빈틈 없게)
        b.append(B((-2.9, 6.0, -0.15), (2.9, 16.5, 0.15), PAPER, rot=rot))
        # 금테 끝 + 바람빛 선
        b.append(B((-2.9, 16.5, -0.25), (2.9, 17.4, 0.25), GOLD, rot=rot))
        b.append(B((-2.4, 14.2, -0.28), (2.4, 14.7, 0.28), G_JADE, glow=True, rot=rot))
        # 살 (검은 쇠)
        b.append(B((-0.35, 0.8, -0.35), (0.35, 17.6, 0.35), BLACK, rot=rot))
    # 물결 먹 문양 (가운데 판)
    for k in range(3):
        y = 8 + k * 2.2
        b.append(B((-2.2 + k * 0.6, y, -0.22), (1.2 + k * 0.6, y + 0.6, 0.22), Mat((40, 90, 80), var=0.03, edge_dark=0.1, top_light=0.05)))
    b += [B((-3.0, -0.2, -0.45), (3.0, 1.0, 0.45), BLACK, rot=("z", 45, piv)), B((-3.0, -0.2, -0.45), (3.0, 1.0, 0.45), BLACK, rot=("z", -45, piv))]
    b += rbox((-1.0, -1.0, -0.8), (1.0, 1.0, 0.8), GOLD, r=0.4) + [B((-0.4, -0.4, -0.9), (0.4, 0.4, 0.9), G_JADE, glow=True)]
    b += [B((-0.55, -5.5, -0.5), (0.55, -1.0, 0.5), BLACK), B((-0.7, -3.4, -0.65), (0.7, -2.8, 0.65), GOLD)]
    b += tassel(0, -5.5, 0, 6, Mat((40, 150, 120), var=0.05, edge_dark=0.25, top_light=0.2, pattern=stripes((40, 150, 120), (20, 100, 80), 1)))
    return b


# ─────────────────────────────────────────────────────────── 방천화극
def phoenix():
    b = [B((-0.55, -22, -0.55), (0.55, 11, 0.55), BLACK)]
    for y in (-21, -9, 0, 8):
        b.append(B((-0.72, y, -0.72), (0.72, y + 0.7, 0.72), GOLD))
    b += [B((-0.75, -24, -0.75), (0.75, -22, 0.75), GOLD_D)]
    # 금 목 장식 + 봉황 깃 수술
    b += rbox((-1.2, 10.4, -1.2), (1.2, 12.6, 1.2), GOLD, r=0.5) + [B((-0.5, 11.1, -1.3), (0.5, 11.9, 1.3), G_RED, glow=True)]
    for k, (dx, ang) in enumerate(((-0.6, -22.5), (0, 0), (0.6, 22.5))):
        rot = ("z", ang, (dx, 10.4, 0)) if ang else None
        b.append(B((dx - 0.45, 4.6, -0.45), (dx + 0.45, 10.4, 0.45), FEATHER, rot=rot))
    # 창날 (가운데, 잎 모양)
    for y0, y1, w in ((12.6, 15, 0.9), (15, 18.5, 1.25), (18.5, 21, 1.0), (21, 22.8, 0.6), (22.8, 24, 0.25)):
        b += [B((-w, y0, -0.35), (w, y1, 0.35), BLADE), B((-w * 0.5, y0, -0.45), (w * 0.5, y1, 0.45), STEEL_D)]
    b += [B((-0.22, 13.5, -0.5), (0.22, 21.5, 0.5), G_GOLD, glow=True)]
    # 양쪽 초승달 날 (월아)
    moon = []
    moon += [B((0.9, 12.8, -0.36), (3.6, 14.2, 0.36), BLADE),
             B((3.0, 12.4, -0.34), (4.4, 18.0, 0.34), BLADE, rot=("z", -22.5, (3.0, 12.4, 0))),
             B((3.0, 10.4, -0.32), (4.2, 12.6, 0.32), BLADE, rot=("z", 22.5, (3.0, 12.6, 0))),
             B((4.4, 12.4, -0.26), (5.0, 18.0, 0.26), G_GOLD, glow=True, rot=("z", -22.5, (3.0, 12.4, 0))),
             B((4.2, 10.4, -0.26), (4.8, 12.6, 0.26), G_GOLD, glow=True, rot=("z", 22.5, (3.0, 12.6, 0)))]
    moon += [B((1.0, 12.4, -0.5), (2.2, 13.4, 0.5), GOLD)]
    b += mirror_x(moon)
    return b


WEAPONS = {"thunder": thunder, "dragon": dragon, "wind": wind, "phoenix": phoenix}
DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, -90, 0], "translation": [0, 1.5, 0.8], "scale": [0.85, 0.85, 0.85]},
    "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [0, 1.5, 0.8], "scale": [0.85, 0.85, 0.85]},
    "firstperson_righthand": {"rotation": [0, -90, 20], "translation": [1.1, 2.2, 1.1], "scale": [0.6, 0.6, 0.6]},
    "firstperson_lefthand": {"rotation": [0, 90, -20], "translation": [1.1, 2.2, 1.1], "scale": [0.6, 0.6, 0.6]},
    "gui": {"rotation": [0, 0, -45], "translation": [0, 0, 0], "scale": [0.4, 0.4, 0.4]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.4, 0.4, 0.4]},
    "fixed": {"rotation": [0, 0, -45], "translation": [0, 0, 0], "scale": [0.45, 0.45, 0.45]},
}


def build(wid):
    part = Part("weapon_" + wid, WEAPONS[wid]())
    at = bake_parts([part], tpu=4, atlas_size=256, seed=len(wid) * 17)
    return part, at.image()


def export(pack):
    for wid in WEAPONS:
        part, img = build(wid)
        ref = pack.texture(f"weapon/{wid}", img)
        js = model_json(part, ref, img.size[0], img.size[1])
        js["display"] = DISPLAY
        pack.item_model(f"weapon/{wid}", js)


def preview(path):
    """무기 4종 미리보기 (먹색 배경)"""
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import render as R
    from world import World
    from bossgen import corners, rot_elem
    from PIL import Image
    tiles = []
    for wid in WEAPONS:
        part, img = build(wid)
        mesh = R.Mesh()
        tid = mesh.texture(wid, img)
        AW, AH = img.size
        sun = np.array((-0.4, 0.7, 0.6)); sun /= np.linalg.norm(sun)
        base = np.array((100.0, 2.0, 100.0))
        a = math.radians(-18)
        M = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        for b in part.boxes:
            for f, uvr in b.uv.items():
                cs = corners(b, f)
                if b.rot:
                    cs = [rot_elem(c, (b.rot[0], b.rot[1], np.array(b.rot[2], float))) for c in cs]
                pts = [base + M @ (np.array(c) / 16 * 2.0) for c in cs]
                n = np.cross(pts[1] - pts[0], pts[3] - pts[0])
                x0, y0, x1, y1 = uvr
                glow = not b.shade
                mesh.quad(pts[0], pts[1], pts[2], pts[3], (x0 / AW, y0 / AH, x1 / AW, y1 / AH), tid, flags=1 if glow else 0,
                          light=(1.3, 1.25, 1.2) if glow else R.face_light(n, sun))
        w = World(8, 8, 8); w.set(0, 0, 0, "stone")
        tgt = base + np.array((0, 0.1, 0))
        im = R.render(w.vox, R.Palette(w.pal), 400, 720, tgt + np.array((0, 0.3, 5.4)), tuple(tgt), fov=40, mesh=mesh, ss=2,
                      sky_top=(0.1, 0.1, 0.12), sky_hor=(0.2, 0.19, 0.2), fog_dist=1e9, post=False, amb_col=(0.8, 0.8, 0.85))
        tiles.append(im)
    W = Image.new("RGB", (1600, 720))
    for i, t in enumerate(tiles):
        W.paste(t, (i * 400, 0))
    W.save(path)
