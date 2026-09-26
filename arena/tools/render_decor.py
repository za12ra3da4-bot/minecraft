"""블록 디스플레이 장식 미리보기 → arena/preview/decor_bd.png"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import render as R
import bdkit
import bdmodels as M

OUT = os.path.join(HERE, "..", "preview")

SHOTS = [
    ("화염 기사", "god_ares", dict(kind="statue"), 2.6),
    ("수호 기사", "god_athena", dict(kind="statue"), 2.6),
    ("바람 기사", "god_hermes", dict(kind="statue"), 2.6),
    ("생명 기사", "god_demeter", dict(kind="statue"), 2.6),
    ("성소 근위병", "hoplite", dict(kind="statue"), 2.4),
    ("부서진 석상", "hoplite_broken", dict(kind="statue"), 2.2),
    ("팀 표식 (빨강)", "deco/flag_red", dict(kind="item"), 2.6),
    ("팀 표식 (파랑)", "deco/flag_blue", dict(kind="item"), 2.6),
    ("팀 문장 (초록)", "deco/crest_green", dict(kind="item"), 3.0),
    ("팀 문장 (노랑)", "deco/crest_yellow", dict(kind="item"), 3.0),
    ("왕좌의 왕관", "deco/zeus_bolt", dict(kind="item"), 4.0),
    ("불꽃 제단 수정", "deco/sigil_ares", dict(kind="item"), 3.2),
    ("생명 제단 수정", "deco/sigil_demeter", dict(kind="item"), 3.2),
    ("벽 화로", "deco/banner_olympus", dict(kind="item"), 3.2),
    ("전리품", "deco/war_banner", dict(kind="item"), 2.4),
    ("바람개비", "deco/wind_ribbon", dict(kind="item"), 2.2),
    ("날개 왕관 부조", "deco/eagle_relief", dict(kind="item"), 5.0),
    ("스핑크스 머리", "deco/sphinx_head", dict(kind="item"), 5.0),
    ("대검", "deco/great_sword", dict(kind="item", tilt=12), 2.2),
    ("거인의 곤봉", "deco/giant_club", dict(kind="item", tilt=62), 4.0),
    ("부엉이 석상", "deco/owl", dict(kind="item"), 1.8),
    ("청동 잔해", "deco/bronze_debris", dict(kind="item"), 3.0),
    ("황금 사과", "deco/peach", dict(kind="item"), 1.4),
    ("전장 방패", "deco/shield", dict(kind="item", tilt=-20), 2.2),
    ("보스 보상 상자", "chest_red", dict(kind="item"), 1.0),
    ("보스 보상 상자 (초록)", "chest_green", dict(kind="item"), 1.0),
]

SUN = np.array([-0.45, 0.78, 0.5]); SUN = SUN / np.linalg.norm(SUN)


def bounds(model, k):
    pts = []
    for p in model.parts:
        for c in ((0, 0, 0), (1, 1, 1), (1, 0, 1), (0, 1, 0)):
            pts.append((p.T + p.R @ (p.S * np.array(c))) * k)
    a = np.array(pts)
    return a.min(0), a.max(0)


def shot(name, d, sc, W=420, H=460):
    if name.startswith("chest_"):
        m = M.treasure_chest(name[6:])
        m.parts = [p for p in m.parts if p.S[1] < 100]
    else:
        m = M.build(name, sc, d)
    if d.get("tilt"):
        bdkit.rotate(m.parts, bdkit.rot(0, d["tilt"], 0), (0, 0, 0))
    k = 1 / 16
    lo, hi = bounds(m, k)
    size = float(max(hi - lo)) + 0.5
    ctr = (lo + hi) / 2
    N = 48
    floor_y = int(np.floor(lo[1])) - 1 + N // 2
    vox = np.zeros((N, N, N), np.int32)
    pal_states = ["air", "polished_andesite", "smooth_stone"]
    for x in range(N):
        for z in range(N):
            vox[x, max(0, floor_y), z] = 1 if (x + z) % 2 else 2
    pal = R.Palette(pal_states)
    origin = np.array([N / 2, N / 2, N / 2])
    mesh = R.Mesh()
    bdkit.add_to_mesh(mesh, m, origin, -18.0, 1.0, SUN)
    target = origin + ctr
    cam = target + np.array([0.9, 0.55, -1.25]) * size * 1.55 * np.array([1, 1, 1])
    cam = target + np.array([size * 0.55, size * 0.35, size * 1.5])
    im = R.render(vox, pal, W, H, cam, target, fov=42, mesh=mesh, ss=2, sun=tuple(SUN), fog_dist=1e9)
    return im


def main():
    from PIL import ImageFont
    font = None
    for f in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"):
        if os.path.exists(f):
            font = ImageFont.truetype(f, 22)
    cols = 6
    W, H = 420, 460
    rows = (len(SHOTS) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * W, rows * H), (20, 20, 24))
    for i, (label, name, d, sc) in enumerate(SHOTS):
        im = shot(name, d, sc, W, H)
        dr = ImageDraw.Draw(im)
        if font:
            dr.rectangle((0, H - 38, W, H), fill=(18, 16, 22))
            dr.text((12, H - 34), label, fill=(240, 214, 140), font=font)
        sheet.paste(im, ((i % cols) * W, (i // cols) * H))
        print(label)
    sheet.save(os.path.join(OUT, "decor_bd.png"))


if __name__ == "__main__":
    main()
