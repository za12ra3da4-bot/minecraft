"""경도 탈출 헬기 — 블록 디스플레이 모델 (bdkit)

 좌표: 픽셀 (16 = 1블록) · +z 앞(코) · +y 위 · x 좌우 · 원점 = 헬기장 바닥 가운데 (스키드 아래)
 몸체 노랑 + 검정 띠 · 짙은 유리 앞창 · 옆창 · 미닫이문 · 엔진 덮개 · 배기구 · 꼬리 붐(점점 가늘게) · 수직 꼬리날개 · 수평 안정판
 스키드 2 (앞 끝 들림) + 버팀대 4 · 탐조등 · 착륙등 · 항법등 (왼쪽 빨강 · 오른쪽 초록) · 꼬리 흰 섬광등 · 지붕 빨간 충돌방지등
 따로 도는 부품:
   main_rotor()  — 원점 = 마스트 꼭대기 (엔티티 yaw 를 돌려서 회전: tp ~ ~ ~ ~각도)
   tail_rotor()  — 원점 = 꼬리 로터 축 (left_rotation 을 x 축으로 돌림 · 날개 방향은 right_rotation 에)
"""
import math

import numpy as np

import bdkit as K

Y = "yellow_concrete"
YD = "orange_concrete"
BK = "black_concrete"
GR = "gray_concrete"
LG = "light_gray_concrete"
WH = "white_concrete"
IR = "iron_block"
GLASS = "light_blue_stained_glass"
TINT = "black_stained_glass"

MAST = (0.0, 66.0, -4.0)           # 메인 로터 축 꼭대기 (px)
TAIL_HUB = (6.5, 50.0, -110.0)     # 꼬리 로터 축 (px) — 오른쪽 면
DOOR = (30.0, 0.0, 6.0)            # 타는 문 바로 바깥 (px, 왼쪽 면 +x)


def body():
    m = K.Model()
    b = m.box
    # ── 스키드 (관) + 앞 끝 들림 + 버팀대 + 발판
    for sx in (-22, 22):
        m.rod(GR, (sx, 2.5, -40), (sx, 2.5, 40), 3.2)
        m.rod(GR, (sx, 2.5, 40), (sx, 9, 50), 3.2)
        m.rod(LG, (sx, 2.5, -40), (sx, 5, -45), 3.0)
        for z in (-22, 22):
            m.rod(LG, (sx, 3.5, z), (sx * 0.55, 14, z), 2.6)
        b(BK, sx - 2.5, 7, -12, sx + 2.5, 8.2, 14)              # 오르는 발판
    m.rod(GR, (-22, 7.6, -12), (-22, 7.6, 14), 1.5)
    # ── 몸통: 겹친 상자로 둥근 단면 (가운데 넓고 위아래로 좁아짐) · 아래 배 검정 · 옆 검정 띠
    b(BK, -11, 10, -25, 11, 15, 27)
    b(BK, -13.5, 12, -27, 13.5, 16, 29)
    b(Y, -15, 15, -30, 15, 44, 30)
    b(Y, -16.5, 17, -29, 16.5, 42, 29.5)
    b(Y, -17, 20, -28, 17, 39, 29)
    b(Y, -13, 44, -27, 13, 47, 26)
    b(Y, -10, 47, -25, 10, 48.5, 22)
    b(BK, -17.15, 22, -28, 17.15, 25.5, 29)
    b(YD, -17.2, 25.5, -28, 17.2, 26.4, 29)
    # ── 코: 앞으로 갈수록 좁고 낮아지는 조각 8 + 위쪽은 짙은 유리 캐노피
    for k in range(8):
        t0, t1 = k / 8, (k + 1) / 8
        z0, z1 = 29 + 25 * t0, 29 + 25 * t1
        hw = 16.5 - 11 * t1 ** 1.6
        bot = 12 + 7 * t1 ** 1.4
        topy = 44 - 20 * t1 ** 1.3
        glass_y = bot + (topy - bot) * (0.42 + 0.1 * t1)
        b(BK, -hw + 1, bot, z0, hw - 1, bot + 4, z1)
        b(Y, -hw, bot + 3, z0, hw, glass_y, z1)
        b(TINT, -hw + 0.3, glass_y, z0, hw - 0.3, topy, z1)
        b(GLASS, -hw + 1.5, glass_y + 0.6, z0 - 0.2, hw - 1.5, topy - 0.6, z1 + 0.2)
        b(BK, -hw - 0.1, glass_y - 0.6, z0, hw + 0.1, glass_y + 0.2, z1)
        b(BK, -0.6, glass_y, z0, 0.6, topy + 0.3, z1)           # 가운데 창틀
    m.box("sea_lantern", -2.5, 13.5, 36, 2.5, 16, 41, glow=True)    # 탐조등
    b(GR, -3.5, 12.5, 35, 3.5, 13.6, 42)
    # ── 옆 창 · 미닫이문 (테두리 선 · 손잡이)
    for sx in (-1, 1):
        x = sx * 17.1
        b(TINT, x - 0.6, 29, -8, x + 0.6, 40, 8)
        b(GLASS, x - 0.7, 30, -7, x + 0.7, 39, 7)
        b(TINT, x - 0.6, 30, -24, x + 0.6, 39, -12)
        for z in (-10, 10):
            b(BK, x - 0.7, 16, z - 0.6, x + 0.7, 41, z + 0.6)    # 문 틈
        b(BK, x - 0.7, 16, -10, x + 0.7, 16.8, 10)
        b(LG, x - 1.2, 24, 6, x + 1.2, 25.5, 8.5)                # 손잡이
        b(BK, x - 0.7, 41, -10, x + 0.7, 42, 10)                 # 문 레일
    # ── 엔진 덮개 · 공기 흡입구 · 배기구 · 마스트
    b(LG, -11, 48, -24, 11, 57, 12)
    b(Y, -9.5, 48, 12, 9.5, 53, 18)
    b(GR, -11.2, 50, 2, 11.2, 55, 10)
    for z in (3.5, 5.5, 7.5):
        b(BK, -11.4, 50.5, z, 11.4, 54.5, z + 0.8)                # 흡입구 줄
    for sx in (-6, 6):
        m.rod(GR, (sx, 53, -22), (sx * 1.3, 51, -31), 4.2)
        m.rod(BK, (sx * 1.3, 51, -31), (sx * 1.35, 50.8, -32), 3.2)
    b(GR, -4, 57, -8, 4, 61, 0)
    m.rod(IR, (0, 57, -4), MAST, 3.4)
    b(GR, -5, 61.5, -9, 5, 63, 1)                                 # 경사판
    m.box("redstone_lamp[lit=true]", -1.5, 57, -18, 1.5, 59, -15, glow=True)   # 충돌방지등
    # ── 꼬리 붐 (점점 가늘게) + 띠
    n = 10
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        za, zb = -28 - 84 * t0, -28 - 84 * t1
        hw = 10 - 6 * t1
        y0 = 25 + 8 * t1
        y1 = 44 - 5.5 * t1
        b(Y, -hw, y0, zb, hw, y1, za)
        b(Y, -hw + 1.2, y0 - 1, zb, hw - 1.2, y1 + 1, za)
        b(BK, -hw - 0.1, y0 + (y1 - y0) * 0.38, zb, hw + 0.1, y0 + (y1 - y0) * 0.55, za)
    b(Y, -3.5, 33, -118, 3.5, 38, -112)
    # 수직 꼬리날개 (뒤로 기움) + 아래 지느러미
    m.cbox(Y, (0, 50, -110), (3, 26, 13), pitch=-22)
    m.cbox(BK, (0, 50, -110.4), (3.2, 4, 13.2), pitch=-22)
    m.cbox(Y, (0, 29, -114), (2.4, 9, 8), pitch=24)
    m.box("white_concrete", -1.2, 62, -118, 1.2, 64, -115, glow=True)     # 흰 섬광등
    # 수평 안정판 + 끝판 + 항법등
    b(Y, -19, 36, -100, 19, 37.8, -91)
    b(BK, -19.1, 36.4, -100, 19.1, 37.4, -98)
    for sx in (-1, 1):
        b(Y, sx * 19 - 1, 33, -100, sx * 19 + 1, 42, -92)
    m.box("redstone_lamp[lit=true]", -20.4, 36, -97, -19.1, 38, -94, glow=True)
    m.box("emerald_block", 19.1, 36, -97, 20.4, 38, -94, glow=True)
    # 꼬리 로터 기어박스 (오른쪽)
    b(GR, 3.5, 47.5, -112.5, 6.5, 52.5, -107.5)
    # 몸통 옆 항법등 · 착륙등
    m.box("redstone_lamp[lit=true]", -17.3, 42, 22, -16.4, 43.5, 25, glow=True)
    m.box("emerald_block", 16.4, 42, 22, 17.3, 43.5, 25, glow=True)
    m.box("sea_lantern", -2, 9.5, 8, 2, 10.2, 12, glow=True)
    # 번호판 띠 (꼬리 붐 앞쪽 흰 사각)
    for sx in (-1, 1):
        b(WH, sx * 9.6 - 0.2, 36, -48, sx * 9.6 + 0.2, 40, -36)
    return m


def main_rotor():
    """원점 = 마스트 꼭대기. 4날 · 끝 노랑 · 살짝 아래로 처짐"""
    m = K.Model()
    m.box(GR, -5, -1.5, -5, 5, 2.5, 5)
    m.box(IR, -2, 2.5, -2, 2, 4.5, 2)
    for k in range(4):
        yaw = k * 90.0
        R = K.rot(yaw, 0, 0)
        for (a, b_, blk) in ((4, 92, BK), (92, 104, Y)):
            c = R @ np.array([0, 0.3 - (a + b_) / 2 * 0.012, (a + b_) / 2])
            m.cbox(blk, c, (7.5, 1.3, b_ - a), yaw=yaw, pitch=1.5)
        m.cbox(GR, R @ np.array([0, 0.5, 6]), (5, 2.4, 6), yaw=yaw)     # 날개 뿌리
    return m


def tail_rotor_parts():
    """꼬리 로터 날개 2 — (블록, right_rotation 쿼터니언, scale(블록), translation(블록)) 목록.
    left_rotation 은 Skript 가 x 축 둘레로 계속 바꿔 돌림 (처음 0)"""
    L, w, t = 20 / 16, 3.4 / 16, 0.9 / 16
    out = []
    for flip in (False, True):
        q = (1.0, 0.0, 0.0, 0.0) if flip else (0.0, 0.0, 0.0, 1.0)      # x 축 180° (아래쪽 날개)
        out.append((BK, q, (t, L, w), (0.0, 0.0, 0.0)))
    out.append((GR, (0.0, 0.0, 0.0, 1.0), (2.2 / 16, 2.6 / 16, 2.6 / 16), (-0.1 / 16, -1.3 / 16, -1.3 / 16)))
    return out


def door_offset(yaw):
    """yaw 로 돌린 뒤 타는 문 바깥 자리 (블록)"""
    return K._ry(-yaw) @ (np.array(DOOR) / 16)


def summon_all(at, x, y, z, yaw, tags):
    """헬기 전부 소환 명령: 몸체 · 메인 로터 (kd_rotor) · 꼬리 로터 (kd_trot)"""
    out = []
    out += K.summon_lines(body(), at, x, y, z, yaw, 1.0, tags, view=3.0)
    mx, my, mz = K._ry(-yaw) @ (np.array(MAST) / 16)
    out += K.summon_lines(main_rotor(), at, x + mx, y + my, z + mz, yaw, 1.0, tags + ['"kd_rotor"'], view=3.0)
    hx, hy, hz = K._ry(-yaw) @ (np.array(TAIL_HUB) / 16)
    f = K._f
    for blk, q, S, T in tail_rotor_parts():
        out.append(f'{at} block_display ~{x + hx:.3f} ~{y + hy:.3f} ~{z + hz:.3f} {{Tags:[{",".join(tags + [chr(34) + "kd_trot" + chr(34)])}],'
                   f'Rotation:[{yaw:.1f}f,0f],block_state:{{Name:"minecraft:{blk}"}},view_range:3f,teleport_duration:2,'
                   f'transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[{",".join(f(v) for v in q)}],'
                   f'translation:[{",".join(f(v) for v in T)}],scale:[{",".join(f(v) for v in S)}]}}}}')
    return out


def preview(path):
    import os
    import render as R
    from PIL import Image, ImageDraw, ImageFont
    SUN = np.array([-0.45, 0.78, 0.5]); SUN = SUN / np.linalg.norm(SUN)
    N = 40
    vox = np.zeros((N, N, N), np.int32)
    for x in range(N):
        for z in range(N):
            d = math.hypot(x - N / 2, z - N / 2)
            vox[x, 8, z] = 1 if d < 8.3 else 2
            if 7.2 < d < 8.3:
                vox[x, 8, z] = 3
    pal = R.Palette(["air", "black_concrete", "gray_concrete", "yellow_stained_glass"])
    origin = np.array([N / 2, 9, N / 2])
    shots = [((8, 5.5, 9), 40, "옆 앞"), ((-9, 4.5, -8), 40, "뒤"), ((0.01, 14, 0.5), 50, "위")]
    W, Hh = 700, 520
    out = Image.new("RGB", (W * len(shots), Hh))
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 22)
    for i, (off, fov, lab) in enumerate(shots):
        mesh = R.Mesh()
        K.add_to_mesh(mesh, body(), origin, 0.0, 1.0, SUN)
        rm = main_rotor()
        mx, my, mz = np.array(MAST) / 16
        K.add_to_mesh(mesh, rm, origin + np.array([mx, my, mz]), 0.0 + 20, 1.0, SUN)
        tgt = origin + np.array([0, 2.2, -1.0])
        cam = tgt + np.array(off, float)
        im = R.render(vox, pal, W, Hh, cam, tgt, fov=fov, mesh=mesh, ss=2, sun=tuple(SUN), fog_dist=1e9)
        ImageDraw.Draw(im).text((12, 8), lab, font=font, fill=(255, 230, 120))
        out.paste(im, (W * i, 0))
    out.save(path)


if __name__ == "__main__":
    import sys
    preview(sys.argv[1] if len(sys.argv) > 1 else "heli.png")
