"""경도 거리 시설 — 블록 디스플레이 모델 (bdkit · 픽셀 좌표 16 = 1블록 · 원점 = 기둥 밑 가운데 · +z = 신호등이 보는 쪽)

 traffic_light(lit)  신호등: 받침 · 가는 기둥 · 도로 위로 뻗은 팔 (모델 -x 쪽) · 매달린 3색 신호 상자 (차양) · 기둥의 보행 신호 · 도로 표지판
                     lit = "green" / "red" — 켜진 등만 빛남 (나머지는 어두운 색)
"""
import bdkit as K

POLE = "gray_concrete"
DARK = "black_concrete"
BODY = "gray_concrete"


def traffic_light(lit="green"):
    m = K.Model()
    b = m.box
    b("polished_andesite", -4, 0, -4, 4, 2, 4)
    b(POLE, -2.2, 2, -2.2, 2.2, 3.5, 2.2)
    m.rod(POLE, (0, 2, 0), (0, 84, 0), 3.2)
    m.box("gray_concrete", -2.5, 84, -2.5, 2.5, 86, 2.5)
    # 팔 (도로 위로 4.5블록) + 받침대 사선
    m.rod(POLE, (0, 80, 0), (-74, 80, 0), 2.6)
    m.rod(POLE, (0, 66, 0), (-20, 79.5, 0), 1.8)
    # 매달린 신호 상자 (세로 3등) — 팔 끝
    hx = -66
    b(DARK, hx - 4.5, 52, -4, hx + 4.5, 79, 3)
    b("yellow_concrete", hx - 5, 51.5, -4.4, hx + 5, 79.5, -3.6)            # 뒷판 테두리 (노란 띠)
    b(DARK, hx - 4.2, 52.2, -4.6, hx + 4.2, 79.2, -4.3)
    colors = [("red", 72.5), ("yellow", 65.5), ("green", 58.5)]
    for col, cy in colors:
        on = col == lit
        blk = {"red": "redstone_block" if on else "red_terracotta",
               "yellow": "yellow_terracotta" if not on else "gold_block",
               "green": "lime_concrete" if on else "green_terracotta"}[col]
        if col == "yellow":
            blk = "yellow_terracotta"
        m.box(blk, hx - 2.6, cy - 2.6, 3, hx + 2.6, cy + 2.6, 3.8, glow=on)
        b(DARK, hx - 3.4, cy + 2.6, 3, hx + 3.4, cy + 3.4, 6.5)               # 차양
        b(DARK, hx - 3.4, cy - 2.6, 3, hx - 2.6, cy + 2.6, 5.5)
        b(DARK, hx + 2.6, cy - 2.6, 3, hx + 3.4, cy + 2.6, 5.5)
    m.rod(DARK, (hx, 79, 0), (hx, 80.5, 0), 1.5)
    # 도로 표지판 (팔 위 초록 판)
    b("green_concrete", -48, 82, -0.6, -24, 89, 0.6)
    b("white_concrete", -46.5, 85, -0.75, -25.5, 86, 0.75)
    # 기둥의 보행 신호 (사람 쪽 · 작은 상자)
    b(DARK, -3.5, 36, 2, 3.5, 46, 8)
    m.box("lime_concrete" if lit == "red" else "red_terracotta", -2.4, 40.5, 8, 2.4, 44.5, 8.6, glow=(lit == "red"))
    m.box("red_concrete" if lit == "green" else "red_terracotta", -2.4, 37.2, 8, 2.4, 40.2, 8.6, glow=(lit == "green"))
    # 기둥 옆 버튼 상자
    b("yellow_concrete", 1.8, 22, -2, 4.6, 27, 2)
    return m


def preview(path):
    import math
    import numpy as np
    import render as R
    from PIL import Image
    SUN = np.array([-0.45, 0.78, 0.5]); SUN = SUN / np.linalg.norm(SUN)
    N = 24
    vox = np.zeros((N, N, N), np.int32)
    vox[:, 4, :] = 1
    pal = R.Palette(["air", "gray_concrete"])
    origin = np.array([N / 2 + 3, 5, N / 2])
    mesh = R.Mesh()
    K.add_to_mesh(mesh, traffic_light("green"), origin, 0.0, 1.0, SUN)
    K.add_to_mesh(mesh, traffic_light("red"), origin + np.array([-8, 0, 6]), 180.0, 1.0, SUN)
    ims = []
    for cam in ((N / 2 - 4, 7, N / 2 + 9), (N / 2 + 7, 9, N / 2 - 6)):
        ims.append(R.render(vox, pal, 600, 520, cam, origin + np.array([-2.5, 3.5, 0]), fov=60, mesh=mesh, ss=2, sun=tuple(SUN), fog_dist=1e9))
    out = Image.new("RGB", (1200, 520))
    out.paste(ims[0], (0, 0)); out.paste(ims[1], (600, 0))
    out.save(path)


if __name__ == "__main__":
    import sys
    preview(sys.argv[1] if len(sys.argv) > 1 else "streetbd.png")
