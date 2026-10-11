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


def disc(m, block, cy, R, h, glow=False, cx=0.0, cz=0.0):
    """정십이각형 원판 (지름 방향 띠 6개를 30° 씩 돌려 겹침 = 정확히 십이각형) · 가운데 (cx, cz) · 아랫면 높이 cy"""
    import math
    a = R * math.cos(math.radians(15))
    w = 2 * R * math.sin(math.radians(15))
    for k in range(6):
        m.cbox(block, (cx, cy + h / 2, cz), (w, h, 2 * a), yaw=k * 30.0, glow=glow)


def ring(m, block, cy, R, t, h, n=24):
    """수평 고리: 조각마다 양끝을 굵기만큼 늘려 겹침 (이음새 틈 없음)"""
    import math
    import numpy as np
    for k in range(n):
        a0, a1 = math.radians(k * 360 / n), math.radians((k + 1) * 360 / n)
        p0 = np.array([math.cos(a0) * R, cy, math.sin(a0) * R])
        p1 = np.array([math.cos(a1) * R, cy, math.sin(a1) * R])
        d = (p1 - p0) / np.linalg.norm(p1 - p0) * (t * 0.5)
        m.rod(block, p0 - d, p1 + d, t, h)


def oct_rod(m, block, a, b, w, glow=False):
    """정팔각 기둥 (폭 w = 마주 보는 면 사이): 가운데를 지나는 띠 4개 (폭 w × 한 변) 를 45° 씩 돌려 겹침 = 정확히 팔각"""
    import math
    side = w * math.tan(math.radians(22.5))
    for k in range(4):
        m.rod(block, a, b, w, side, glow=glow, twist=k * 45.0)


def oct_plate(m, block, c, w, t, axis="z"):
    """세운 팔각 판 (압력계 눈금판 등) — 가운데 c · 폭 w · 두께 t · 바라보는 축 z"""
    import math
    side = w * math.tan(math.radians(22.5))
    for k in range(4):
        m.cbox(block, c, (w, side, t), roll=k * 45.0)


def flange(m, block, y, r, h, bolts=8, bolt_r=None):
    """팔각 플랜지 + 볼트 (육각 머리 느낌: 작은 상자 두 겹)"""
    import math
    oct_rod(m, block, (0, y, 0), (0, y + h, 0), r * 2)
    br = bolt_r or r * 0.78
    for k in range(bolts):
        a = math.radians(k * 360 / bolts + 180 / bolts)
        x, z = math.cos(a) * br, math.sin(a) * br
        m.cbox("iron_block", (x, y + h + 0.3, z), (1.1, 0.6, 1.1))
        m.cbox("light_gray_concrete", (x, y + h + 0.3, z), (0.8, 0.62, 0.8), yaw=45)


def valve_base():
    """하수구 밸브 몸체 (+z = 도둑이 서는 쪽)
    경고 줄무늬 받침 · 팔각 관 (볼트 플랜지 2) · 뒤로 나가 땅으로 꺾이는 옆관 (이음 고리) · 둥근 압력계 (눈금 · 바늘) · 이름판 · 경고등 받침"""
    import math
    m = K.Model()
    b = m.box
    b("gray_concrete", -9, 0, -9, 9, 1.4, 9)
    b("light_gray_concrete", -8, 1.4, -8, 8, 1.8, 8)
    for k in range(-9, 9, 3):
        col = "yellow_concrete" if (k // 3) % 2 == 0 else "black_concrete"
        b(col, k, 1.4, -9, k + 3, 2.0, -7.6); b(col, k, 1.4, 7.6, k + 3, 2.0, 9)
        b(col, -9, 1.4, k, -7.6, 2.0, k + 3); b(col, 7.6, 1.4, k, 9, 2.0, k + 3)
    flange(m, "gray_concrete", 1.8, 4.6, 2.2)
    oct_rod(m, "light_gray_concrete", (0, 4, 0), (0, 17.5, 0), 6.0)
    for y in (8.5, 13):
        oct_rod(m, "gray_concrete", (0, y, 0), (0, y + 0.8, 0), 6.7)
    flange(m, "gray_concrete", 17.5, 4.3, 2.0)
    oct_rod(m, "iron_block", (0, 19.5, 0), (0, 25.2, 0), 2.4)            # 축 (바퀴는 따로)
    oct_rod(m, "gray_concrete", (0, 22.8, 0), (0, 23.6, 0), 3.4)         # 축 고정 너트
    # 옆관: 뒤로 → 아래로 (꺾이는 곳 이음 고리)
    oct_rod(m, "light_gray_concrete", (0, 10, -2.5), (0, 10, -12.4), 4.0)
    oct_rod(m, "gray_concrete", (0, 10, -8.6), (0, 10, -9.6), 4.8)
    oct_rod(m, "gray_concrete", (0, 10, -11), (0, 10, -12.6), 4.8)
    oct_rod(m, "light_gray_concrete", (0, 12, -12.4), (0, -1, -12.4), 4.0)
    oct_rod(m, "gray_concrete", (0, 2.4, -12.4), (0, 3.4, -12.4), 4.8)
    # 둥근 압력계 (앞)
    oct_rod(m, "iron_block", (0, 14, 2.8), (0, 14, 5.4), 1.2)
    oct_plate(m, "black_concrete", (0, 14, 5.9), 4.6, 0.8)
    oct_plate(m, "white_concrete", (0, 14, 6.35), 3.8, 0.3)
    for k in range(7):
        a = math.radians(210 - k * 40)
        m.cbox("black_concrete" if k < 5 else "red_concrete", (math.cos(a) * 1.45, 14 + math.sin(a) * 1.45, 6.52), (0.35, 0.35, 0.1))
    m.cbox("red_concrete", (0.45, 14.4, 6.6), (0.3, 1.8, 0.1), roll=-35)
    m.cbox("black_concrete", (0, 14, 6.62), (0.6, 0.6, 0.12), roll=45)
    # 이름판
    m.cbox("blue_concrete", (0, 6.6, 3.35), (5, 2.6, 0.4))
    m.cbox("white_concrete", (0, 6.9, 3.57), (3.6, 0.45, 0.1))
    m.cbox("white_concrete", (0, 6.1, 3.57), (2.4, 0.35, 0.1))
    # 경고등 받침 (불빛은 valve_lamp 따로)
    oct_rod(m, "gray_concrete", (6.5, 1.8, 6.5), (6.5, 2.8, 6.5), 4.0)
    oct_rod(m, "gray_concrete", (6.5, 5.4, 6.5), (6.5, 6.0, 6.5), 3.0)
    return m


LAMP_AT = (6.5, 2.8, 6.5)     # 밸브 몸체 기준 경고등 자리 (px)
WHEEL_AT = (0, 25.5, 0)       # 바퀴 축 자리 (px)


def valve_lamp():
    """경고등 불빛 하나 (빨강 = 아직 · Skript 가 돌리면 초록으로 바꿈)"""
    m = K.Model()
    m.box("redstone_block", -1.5, 0, -1.5, 1.5, 2.6, 1.5, glow=True)
    return m


def valve_wheel():
    """빨간 바퀴 (원점 = 축 가운데 · 수평) — 엔티티 방향(yaw)을 돌리면 바퀴가 돎
    두꺼운 테 (32조각 · 겹침) + 안쪽 진한 테 · 살 5개 (안쪽은 굵게) · 팔각 허브 + 뚜껑 · 손잡이"""
    import math
    m = K.Model()
    R = 8.0
    ring(m, "red_concrete", 0, R, 2.2, 2.2, n=32)
    ring(m, "red_terracotta", -0.3, R - 1.3, 0.9, 1.3, n=32)
    for k in range(5):
        a = math.radians(k * 72 + 18)
        mid = (math.cos(a) * R * 0.45, 0, math.sin(a) * R * 0.45)
        m.rod("red_concrete", (0, 0, 0), mid, 1.8, 1.6)
        m.rod("red_concrete", mid, (math.cos(a) * (R - 0.8), 0, math.sin(a) * (R - 0.8)), 1.3, 1.3)
    oct_rod(m, "black_concrete", (0, -1.2, 0), (0, 1.2, 0), 3.6)
    oct_rod(m, "gray_concrete", (0, 1.2, 0), (0, 1.8, 0), 2.6)
    m.cbox("iron_block", (0, 2.0, 0), (1.2, 0.5, 1.2), yaw=45)
    hx = R
    oct_rod(m, "black_concrete", (hx, 0.6, 0), (hx, 4.6, 0), 1.6)          # 손잡이
    oct_rod(m, "red_concrete", (hx, 4.4, 0), (hx, 5.4, 0), 2.1)
    return m


def manhole_frame():
    """맨홀 테두리 · 어두운 구멍 (도로 위에 거의 붙여서) · 주변 금 · 둘레 고깔 4"""
    import math
    m = K.Model()
    disc(m, "polished_deepslate", 0.0, 27, 0.5)
    disc(m, "black_concrete", 0.5, 22, 0.25)
    disc(m, "gray_concrete", 0.62, 22.6, 0.06)
    disc(m, "black_concrete", 0.7, 21.5, 0.06)
    ring(m, "iron_block", 0.9, 24.5, 2.2, 0.8, n=24)
    # 공사 고깔 4 (주황 · 흰 줄)
    for k in range(4):
        a = math.radians(k * 90 + 45)
        cx, cz = math.cos(a) * 40, math.sin(a) * 40
        m.box("black_concrete", cx - 4, 0, cz - 4, cx + 4, 1, cz + 4)
        for lvl, (r, col) in enumerate(((3.0, "orange_concrete"), (2.4, "white_concrete"), (1.9, "orange_concrete"), (1.3, "white_concrete"), (0.8, "orange_concrete"))):
            m.box(col, cx - r, 1 + lvl * 2.2, cz - r, cx + r, 3.2 + lvl * 2.2, cz + r)
    return m


def manhole_cover():
    """주철 맨홀 뚜껑 (원점 = 가운데 · 열리면 Skript 가 옆으로 밀어냄): 두꺼운 원판 · 돋을 테 · 격자 무늬 · 지렛대 구멍 2"""
    import math
    m = K.Model()
    disc(m, "gray_concrete", 0.6, 23.2, 1.4)
    disc(m, "light_gray_concrete", 2.0, 21, 0.3)
    ring(m, "gray_concrete", 2.3, 18.5, 1.2, 0.6, n=24)
    ring(m, "gray_concrete", 2.3, 10, 1.2, 0.6, n=16)
    for k in range(-3, 4):
        L = math.sqrt(max(0, 16.5 ** 2 - (k * 4.6) ** 2))
        m.box("gray_concrete", k * 4.6 - 0.5, 2.3, -L, k * 4.6 + 0.5, 2.8, L)
        m.box("gray_concrete", -L, 2.3, k * 4.6 - 0.5, L, 2.8, k * 4.6 + 0.5)
    disc(m, "light_gray_concrete", 2.3, 5, 0.6)
    for sx in (-14, 14):
        m.box("black_concrete", sx - 1.2, 2.31, -0.7, sx + 1.2, 2.4, 0.7)
    return m


def valve():
    m = valve_base()
    w = valve_wheel()
    m.add(w, t=WHEEL_AT)
    m.add(valve_lamp(), t=LAMP_AT)
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
