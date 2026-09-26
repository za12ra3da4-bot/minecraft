"""대기실 — 맵 가운데 하늘에 떠 있는 섬 (게임 전 · 후 모이는 곳)

 바닥 반지름 17: 대리석 · 금 문양 원판, 가운데 유리창(아래 맵이 보임)
 네 방향 팀 발판 (밟으면 팀 선택) · 둘레 기둥 + 랜턴 · 난간 · 아래쪽 바위 섬
"""
import math

from layout import *
from prims import slab, stairs

LOBBY_Y = 84
LOBBY_R = 17
TEAM_BLOCK = {"red": "red", "blue": "blue", "green": "lime", "yellow": "yellow"}


def build_lobby(b):
    cx, cz = C
    y = LOBBY_Y
    # 아래쪽 바위 섬 (거꾸로 된 원뿔, 울퉁불퉁)
    for x in range(cx - LOBBY_R - 2, cx + LOBBY_R + 3):
        for z in range(cz - LOBBY_R - 2, cz + LOBBY_R + 3):
            d = math.hypot(x - cx, z - cz)
            if d > LOBBY_R + 1.5:
                continue
            depth = int((1 - d / (LOBBY_R + 1.5)) ** 0.8 * 14) + (1 if (x * 7 + z * 13) % 5 == 0 else 0)
            for k in range(1, depth + 1):
                s = "deepslate_tiles" if k > depth - 2 else ("stone" if (x + z + k) % 4 else "andesite")
                if k > 3 and (x * 5 + z * 3 + k) % 9 == 0:
                    s = "amethyst_block"
                b.set(x, y - k, z, s)
    # 바닥
    for x in range(cx - LOBBY_R - 1, cx + LOBBY_R + 2):
        for z in range(cz - LOBBY_R - 1, cz + LOBBY_R + 2):
            d = math.hypot(x - cx, z - cz)
            if d > LOBBY_R + 0.5:
                continue
            a = math.degrees(math.atan2(z - cz, x - cx))
            if d < 2.5:
                s = "glass"
            elif d < 3.5:
                s = "gold_block"
            elif d < 7.5:
                s = "white_glazed_terracotta" if int((a + 180) / 22.5) % 2 else "polished_diorite"
            elif d < 8.5:
                s = "gold_block"
            elif d < 15.5:
                s = "smooth_quartz" if (x + z) % 2 else "quartz_bricks"
            elif d < 16.5:
                s = "chiseled_quartz_block"
            else:
                s = "polished_blackstone_bricks"
            b.set(x, y, z, s)
            b.air(x, y + 1, z, x, y + 10, z)
    # 난간 (가장자리)
    for x in range(cx - LOBBY_R - 1, cx + LOBBY_R + 2):
        for z in range(cz - LOBBY_R - 1, cz + LOBBY_R + 2):
            d = math.hypot(x - cx, z - cz)
            if LOBBY_R - 0.5 <= d <= LOBBY_R + 0.5:
                b.set(x, y + 1, z, "polished_blackstone_brick_wall")
    # 기둥 8개 + 랜턴 + 금 장식
    for k in range(8):
        a = k / 8 * 2 * math.pi + math.pi / 8
        px, pz = round(cx + math.cos(a) * 14), round(cz + math.sin(a) * 14)
        b.set(px, y + 1, pz, "chiseled_quartz_block")
        b.fill(px, y + 2, pz, px, y + 6, pz, "quartz_pillar[axis=y]")
        b.set(px, y + 7, pz, "chiseled_quartz_block")
        b.set(px, y + 8, pz, "gold_block")
        b.set(px, y + 9, pz, "lantern[hanging=false,waterlogged=false]")
    # 팀 발판 (네 방향, 3x3 색 콘크리트 + 유리 테두리 + 빛)
    for t, ((dx, dz), name, code, dye) in TEAMS.items():
        px, pz = cx + dx * 10, cz + dz * 10
        col = TEAM_BLOCK[t]
        for ox in range(-2, 3):
            for oz in range(-2, 3):
                edge = max(abs(ox), abs(oz)) == 2
                b.set(px + ox, y, pz + oz, f"{col}_stained_glass" if edge else f"{col}_concrete")
        b.set(px, y - 1, pz, "sea_lantern")
        # 발판 뒤 깃대 + 색 양털 깃발
        bx, bz = px + dx * 3, pz + dz * 3
        b.fill(bx, y + 1, bz, bx, y + 5, bz, "dark_oak_fence")
        b.set(bx, y + 6, bz, "gold_block")
        for k in range(3):
            b.set(bx + (dz if dz else 0) * 0, y + 5 - k, bz, "dark_oak_fence")
        b.set(bx - dz, y + 5, bz + dx, f"{col}_wool")
        b.set(bx - dz, y + 4, bz + dx, f"{col}_wool")
        b.set(bx - 2 * dz, y + 5, bz + 2 * dx, f"{col}_wool")
        b.w.mark(f"lobby_pad_{t}", px + 0.5, y + 1, pz + 0.5, radius=2.2)
    # 가운데 샘 (금 테두리 + 빛)
    b.set(cx, y + 1, cz, "sea_lantern")
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        b.set(cx + dx, y + 1, cz + dz, "gold_block" if False else "polished_blackstone_brick_wall")
    b.w.mark("lobby_spawn", cx + 0.5, y + 1, cz + 3.5, yaw=180, radius=LOBBY_R)
