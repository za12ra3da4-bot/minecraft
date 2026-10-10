"""신화 아케이드 — 서버 첫 화면 허브 (밤바다 위에 떠 있는 오락실 광장)

 사용자가 보낸 참고 그림(우주 아케이드 로비) 구성 그대로:
 · 뒤 가운데: 고리(포털)를 배 앞에 든 거대 우주인 로봇 — 흰 헬멧 · 검은 얼굴판 · 빛나는 눈 · 웃는 입
 · 로봇 양옆 · 광장 양옆에 거대한 오락기 4대 — 모두 블록 면과 나란히 세워서 면이 계단처럼 깨지지 않게
   · 둥근 윗모서리 · 색유리 너머로 빛나는 간판 (글자 없음) · 가운데 노랑 / 가장자리 주황으로 빛나는 둥근 화면
   · 앞으로 튀어나온 조작판 (조이스틱 + 버튼) · 옆판 흰 테 + 무늬 띠 + 별 · 앞 빛나는 입장 발판
     안쪽 왼쪽 = 신화쟁탈전 (하늘색) · 안쪽 오른쪽 = PvP 연습장 (남색)
     바깥 왼쪽 = 준비 중 (보라) · 바깥 오른쪽 = 준비 중 (주황)
 · 흰 타일 광장 · 가운데 검은 원 + 빛나는 주황 점선 고리 · 색깔 가로등 · 꼬마 로봇 · 유리 돔 · 산호 섬 · 하늘의 행성
 원점 = 광장 가운데 바닥 칸 (Skript {bg::hub::x/y/z}, 데이터팩 storage bg:hub origin)
 좌표: x = 동(+), z = 남(+). 처음 서는 자리는 광장 남쪽, 북쪽(로봇)을 본다
"""
import math
import os

import numpy as np

N = 176
H = 84
FL = 16
C = N // 2
R_ISLAND = 82
R_PLAZA = 38
CH = 29             # 오락기 높이
CW = 8              # 오락기 반폭 (fx -8..8)
BACK = -6           # 오락기 뒷면 (fz)
RZ = -50            # 로봇 자리 (z)

PAL = ["air", "white_concrete", "light_gray_concrete", "smooth_quartz", "quartz_block", "gray_concrete",
       "black_concrete", "blue_concrete", "light_blue_concrete", "cyan_concrete", "purple_concrete",
       "magenta_concrete", "orange_concrete", "red_concrete", "yellow_concrete", "lime_concrete", "pink_concrete",
       "ochre_froglight", "pearlescent_froglight", "verdant_froglight", "sea_lantern", "glowstone", "shroomlight",
       "light_blue_stained_glass", "orange_stained_glass", "yellow_stained_glass", "purple_stained_glass",
       "blue_stained_glass", "magenta_stained_glass", "white_stained_glass", "black_stained_glass",
       "end_rod[facing=up]", "end_rod[facing=down]", "smooth_quartz_slab[type=bottom,waterlogged=false]", "barrier",
       "blue_terracotta", "cyan_terracotta", "light_blue_terracotta", "prismarine", "dark_prismarine",
       "tube_coral_block", "brain_coral_block", "bubble_coral_block", "fire_coral_block", "horn_coral_block",
       "diorite_wall[up=true,east=none,west=none,north=none,south=none,waterlogged=false]",
       "orange_carpet", "red_carpet", "yellow_carpet", "lime_carpet", "light_blue_carpet",
       "light_gray_stained_glass", "cyan_stained_glass"]
P = {}
for _i, _s in enumerate(PAL):
    P.setdefault(_s.split("[")[0] + ("_down" if "facing=down" in _s else ""), _i)

# 오락기: 자리 (x, z) · 보는 방향 (S = 남, E = 동, W = 서) · 몸통 / 무늬 / 별 / 간판 유리 / 등 색
BOOTHS = {
    "myth": dict(pos=(-23, -44), face="S", body="light_blue_concrete", art="blue_concrete", star="white_concrete",
                 glass="light_blue_stained_glass", lamp="sea_lantern", name="신화쟁탈전"),
    "pvp": dict(pos=(23, -44), face="S", body="blue_concrete", art="light_blue_concrete", star="yellow_concrete",
                glass="blue_stained_glass", lamp="ochre_froglight", name="PvP 연습장"),
    "soon1": dict(pos=(-42, -18), face="E", body="purple_concrete", art="magenta_concrete", star="pink_concrete",
                  glass="magenta_stained_glass", lamp="pearlescent_froglight", name="준비 중"),
    "soon2": dict(pos=(42, -18), face="W", body="orange_concrete", art="yellow_concrete", star="white_concrete",
                  glass="orange_stained_glass", lamp="shroomlight", name="준비 중"),
}
FACE_YAW = {"S": 0.0, "E": -90.0, "W": 90.0}       # 오락기가 보는 방향 (마인크래프트 yaw)


def frame_xz(cx, cz, face, fx, fz):
    """오락기 좌표 (fx = 앞에 선 사람 기준 오른쪽, fz = 앞쪽) → 허브 칸 좌표. 축과 나란한 방향만 → 면이 반듯함"""
    if face == "S":
        return cx + fx, cz + fz
    if face == "E":
        return cx + fz, cz - fx
    return cx - fz, cz + fx


def rrect(x, y, hw, hh, rad):
    """둥근 사각형 안쪽까지의 거리 (안쪽이면 양수 = 가장자리까지 칸 수)"""
    dx = abs(x) - (hw - rad)
    dy = abs(y) - (hh - rad)
    if dx > 0 and dy > 0:
        return rad - math.hypot(dx, dy)
    return min(hw - abs(x), hh - abs(y))


def rrect_np(x, y, hw, hh, rad):
    dx = np.abs(x) - (hw - rad)
    dy = np.abs(y) - (hh - rad)
    corner = rad - np.hypot(np.maximum(dx, 0), np.maximum(dy, 0))
    return np.where((dx > 0) & (dy > 0), corner, np.minimum(hw - np.abs(x), hh - np.abs(y)))


def erode(m):
    e = m.copy()
    e[1:, :] &= m[:-1, :]
    e[:-1, :] &= m[1:, :]
    e[:, 1:] &= m[:, :-1]
    e[:, :-1] &= m[:, 1:]
    return e


def build():
    v = np.zeros((N, H, N), np.uint16)
    xx, zz = np.meshgrid(np.arange(N) - C + 0.5, np.arange(N) - C + 0.5, indexing="ij")
    r = np.hypot(xx, zz)
    ang = (np.degrees(np.arctan2(zz, xx)) + 360) % 360
    rng = np.random.default_rng(8)

    def put(hx, y, hz, blk):
        gx, gz, y = C + int(math.floor(hx)), C + int(math.floor(hz)), int(y)
        if 0 <= gx < N and 0 <= y < H and 0 <= gz < N:
            v[gx, y, gz] = P[blk]

    def cell(hx, y, hz):
        gx, gz, y = C + int(math.floor(hx)), C + int(math.floor(hz)), int(y)
        if 0 <= gx < N and 0 <= y < H and 0 <= gz < N:
            return v[gx, y, gz]
        return 0

    def ring(y, r0, r1, blk, m=None):
        mm = (r >= r0) & (r < r1)
        if m is not None:
            mm &= m
        v[:, y, :][mm] = P[blk]

    def glow_floor(m, glass, light="sea_lantern"):
        """바닥에 빛나는 줄: 색유리 + 바로 밑 빛 블록"""
        v[:, FL, :][m] = P[glass]
        v[:, FL - 1, :][m] = P[light]

    def frame(cx, cz, face):
        def at(fx, fz, y, blk):
            hx, hz = frame_xz(cx, cz, face, int(math.floor(fx + 0.5)), int(math.floor(fz + 0.5)))
            put(hx, y, hz, blk)

        def get(fx, fz, y):
            hx, hz = frame_xz(cx, cz, face, int(math.floor(fx + 0.5)), int(math.floor(fz + 0.5)))
            return cell(hx, y, hz)
        return at, get

    def lamp(hx, hz, head, h=4):
        put(hx, FL + 1, hz, "smooth_quartz")
        for y in range(FL + 2, FL + 2 + h):
            put(hx, y, hz, "diorite_wall")
        put(hx, FL + 2 + h, hz, head)
        put(hx, FL + 3 + h, hz, head)
        put(hx, FL + 4 + h, hz, "smooth_quartz_slab")

    # ── 섬: 밤바다 바위
    for k in range(FL):
        y = FL - 1 - k
        rad = R_ISLAND - k * 4.4 - (k ** 1.6) * 0.35
        if rad < 3:
            break
        wob = np.sin(np.radians(ang) * 6 + k) * 1.8 + np.sin(np.radians(ang) * 15 + k * 3) * 0.7
        m = r < rad + wob
        layer = np.where(np.sin(xx * 0.23 + k) + np.cos(zz * 0.27 - k * 0.5) > 0.3, P["dark_prismarine"], P["blue_terracotta"])
        v[:, y, :][m] = layer[m]
    isl = r < R_ISLAND - 0.5
    v[:, FL, :][isl] = P["blue_terracotta"]
    v[:, FL, :][isl & (np.sin(xx * 0.4) * np.cos(zz * 0.37) > 0.45)] = P["cyan_terracotta"]
    v[:, FL, :][isl & (np.sin(xx * 0.21 + 1) * np.cos(zz * 0.19 - 2) > 0.7)] = P["light_blue_terracotta"]

    # ── 흰 타일 광장: 남쪽 둥근 광장 + 북쪽 무대 (로봇 · 오락기)
    plaza = (r < R_PLAZA) | (rrect_np(xx, zz + 18, 50, 44, 22) > 0)
    e1 = erode(plaza); e2 = erode(e1); e3 = erode(e2); e4 = erode(e3)
    v[:, FL, :][plaza] = P["white_concrete"]
    v[:, FL - 1, :][plaza] = P["light_gray_concrete"]
    ix = np.floor(xx).astype(int); iz = np.floor(zz).astype(int)
    tile = ((np.mod(ix, 5) == 0) | (np.mod(iz, 5) == 0)) & e4
    v[:, FL, :][tile] = P["light_gray_concrete"]
    v[:, FL, :][plaza & ~e2] = P["smooth_quartz"]
    v[:, FL + 1, :][plaza & ~e1] = P["smooth_quartz_slab"]
    glow_floor(e3 & ~e4, "light_blue_stained_glass")
    # 가운데 원: 검은 원 · 빛나는 주황 점선 · 흰 테 · 빛나는 하늘색 테
    ring(FL, 0, 7.5, "black_concrete")
    glow_floor((r < 2.2), "light_blue_stained_glass")
    ring(FL, 3.5, 4.3, "gray_concrete")
    dash = (np.mod(np.floor(ang / 12), 2) == 0)
    ring(FL, 7.5, 9.0, "black_concrete")
    glow_floor((r >= 7.5) & (r < 9.0) & dash, "orange_stained_glass", "shroomlight")
    ring(FL, 9.0, 10.5, "white_concrete")
    glow_floor((r >= 10.5) & (r < 11.3), "light_blue_stained_glass")
    # 둥근 흰 단 (한 칸, 동서남북 계단 길)
    gap = (np.abs(xx) < 3) | (np.abs(zz) < 3)
    ring(FL + 1, 13, 17, "smooth_quartz", ~gap)
    ring(FL + 1, 17, 18, "smooth_quartz_slab", ~gap)
    m = (r >= 14.2) & (r < 15.0) & ~gap
    v[:, FL + 1, :][m] = P["light_blue_stained_glass"]
    v[:, FL, :][m] = P["sea_lantern"]

    # ── 색깔 가로등 (광장 남쪽 둘레)
    heads = ["pearlescent_froglight", "ochre_froglight", "sea_lantern", "verdant_froglight", "shroomlight"]
    for i, t in enumerate(range(18, 163, 24)):
        lamp(math.cos(math.radians(t)) * (R_PLAZA - 5), math.sin(math.radians(t)) * (R_PLAZA - 5), heads[i % 5])
    for s in (-1, 1):
        lamp(s * 34, -34, heads[(s + 1) % 5])
        lamp(s * 12, -30, "sea_lantern", h=3)

    # ── 오락기 4대
    def inside(fx, top):
        if top < 1 or top > CH or abs(fx) > CW:
            return False
        if top <= CH - 10:
            return True
        return rrect(fx, top - CH / 2, CW + 0.5, CH / 2, 4.2) > 0

    def prof(fx, top):
        """옆에서 본 앞면 위치 (fz): 받침 · 아래 몸통 · 튀어나온 조작판 · 들어간 화면 · 튀어나온 간판"""
        if top == 1:
            return 2
        if top <= 10:
            return 3
        if top <= 12:
            return 7
        if top <= 23:
            return 3 if abs(fx) == CW else 2
        return 4

    def solid(fx, fz, top):
        return inside(fx, top) and BACK <= fz <= prof(fx, top)

    SIDE_STARS = [(-3, 6), (0, 9), (-4, 18), (-1, 25), (1, 21), (-4, 13)]
    FRONT_STARS = [(-6, 9), (-3, 4), (-5, 3), (1, 9), (-7, 6), (7, 10)]

    for key, b in BOOTHS.items():
        at, get = frame(b["pos"][0], b["pos"][1], b["face"])
        body, art, star = b["body"], b["art"], b["star"]
        # 속 (몸통 색) + 검은 받침
        for fx in range(-CW, CW + 1):
            for top in range(1, CH + 1):
                if not inside(fx, top):
                    continue
                for fz in range(BACK, prof(fx, top) + 1):
                    at(fx, fz, FL + top, "black_concrete" if top == 1 else body)
        # 옆판: 흰 테 (옆 모양을 따라) + 비스듬한 무늬 띠 + 별
        for s in (-CW, CW):
            for top in range(2, CH + 1):
                if not inside(s, top):
                    continue
                for fz in range(BACK, prof(s, top) + 1):
                    edge = (not solid(s, fz + 1, top) or not solid(s, fz - 1, top) or not solid(s, fz, top + 1)
                            or top == 2)
                    if edge:
                        blk = "white_concrete"
                    else:
                        w = top - (0.55 * fz + 15.5)
                        blk = art if abs(w) < 1.1 else (star if abs(w - 3.2) < 0.45 else body)
                    at(s, fz, FL + top, blk)
            for fz, top in SIDE_STARS:
                for dz, dt in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    z2, t2 = fz + dz, top + dt
                    if solid(s, z2 + 1, t2) and solid(s, z2 - 1, t2) and solid(s, z2, t2 + 1) and solid(s, z2, t2 - 1):
                        at(s, z2, FL + t2, star)
        # 아래 몸통 앞 (fz 3): 흰 밑 테 · 비스듬한 무늬 띠 · 오른쪽 작은 동전 상자 + 별
        for fx in range(-CW + 1, CW):
            for top in range(2, 11):
                w = top - (0.42 * fx + 6.0)
                blk = "white_concrete" if top == 2 else (art if abs(w) < 1.0 else body)
                rr = rrect(fx - 4, top - 6, 2.5, 2.5, 1.0)
                if rr > 0:
                    blk = "light_gray_concrete" if rr < 1 else "gray_concrete"
                    if fx == 4 and top in (6, 7):
                        blk = "shroomlight"
                at(fx, 3, FL + top, blk)
        for fx, top in FRONT_STARS:
            at(fx, 3, FL + top, star)
        # 조작판 (top 11..12, fz 3..7): 검은 판 · 흰 앞 테 · 조이스틱 · 버튼
        for fx in range(-CW + 1, CW):
            for fz in range(3, 7):
                at(fx, fz, FL + 12, "black_concrete")
            at(fx, 7, FL + 12, "white_concrete")
            at(fx, 7, FL + 11, art)
        at(-4, 5, FL + 13, "end_rod")
        for fx, fz, c in ((1, 4, "orange_carpet"), (3, 4, "orange_carpet"), (5, 4, "orange_carpet"),
                          (2, 6, "red_carpet"), (4, 6, "yellow_carpet"), (6, 6, "orange_carpet"),
                          (-1, 3, "lime_carpet"), (0, 3, "light_blue_carpet")):
            at(fx, fz, FL + 13, c)
        # 화면 (top 13..23): 검은 테 · 한 칸 들어간 둥근 화면 (가운데 노랑, 가장자리 주황)
        for fx in range(-CW + 1, CW):
            for top in range(13, 24):
                es = rrect(fx, top - 18, 6.5, 4.5, 2.2)
                if es > 0:
                    at(fx, 2, FL + top, "air")
                    at(fx, 1, FL + top, "shroomlight" if es < 1.0 else "ochre_froglight")
                elif rrect(fx, top - 18, 7.5, 5.5, 3.0) > 0:
                    at(fx, 2, FL + top, "black_concrete")
        # 간판 아래 조명 (화면을 비춤)
        for fx in (-5, 0, 5):
            at(fx, 3, FL + 23, "end_rod_down")
        # 간판 (top 24..CH, fz 4): 흰 둥근 테 + 무늬 색 안쪽 테 + 색유리 너머 빛
        for fx in range(-CW, CW + 1):
            for top in range(24, CH + 1):
                if not inside(fx, top):
                    continue
                e1_ = not inside(fx + 1, top) or not inside(fx - 1, top) or not inside(fx, top + 1) or top == 24
                if e1_:
                    at(fx, 4, FL + top, "white_concrete")
                else:
                    at(fx, 4, FL + top, b["glass"])
                    at(fx, 3, FL + top, "sea_lantern")
        # 입장 발판 (앞 7×5): 흰 테 + 빛나는 색유리
        for fx in range(-3, 4):
            for fz in range(9, 14):
                if abs(fx) == 3 or fz in (9, 13):
                    at(fx, fz, FL, "white_concrete")
                else:
                    at(fx, fz, FL, b["glass"])
                    at(fx, fz, FL - 1, "sea_lantern")
        # 발판 옆 작은 가로등
        for fx in (-5, 5):
            hx, hz = frame_xz(b["pos"][0], b["pos"][1], b["face"], fx, 11)
            lamp(hx, hz, b["lamp"], h=2)

    # ── 거대 우주인 로봇 (북쪽 가운데, 남쪽을 봄)
    at, get = frame(0, RZ, "S")
    for fx in range(-14, 15):
        for fz in range(-14, 15):
            d = math.hypot(fx, fz)
            if d <= 13.4:
                at(fx, fz, FL + 1, "light_gray_concrete")
                at(fx, fz, FL + 2, "light_blue_concrete" if 12.4 < d else "white_concrete")
                at(fx, fz, FL + 3, "white_concrete" if d <= 11.4 else "smooth_quartz_slab")
                if 11.4 < d <= 12.4:
                    lit = int((math.degrees(math.atan2(fz, fx)) + 360) % 360) % 20 < 9
                    at(fx, fz, FL + 3, "light_blue_stained_glass" if lit else "white_concrete")
                    if lit:
                        at(fx, fz, FL + 2, "sea_lantern")
    base = FL + 4

    def ell(cx, cy, cz, rx, ry, rz, blk, p=2.0, cond=None):
        for fx in range(int(cx - rx) - 1, int(cx + rx) + 2):
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                for fz in range(int(cz - rz) - 1, int(cz + rz) + 2):
                    q = abs((fx - cx) / rx) ** p + abs((y - cy) / ry) ** p + abs((fz - cz) / rz) ** p
                    if q <= 1 and (cond is None or cond(fx, y, fz)):
                        at(fx, fz, y, blk)

    def limb(p0, p1, rad, blk):
        n = int(max(abs(p1[i] - p0[i]) for i in range(3)) * 2) + 2
        for k in range(n + 1):
            t = k / n
            ell(*(p0[i] + (p1[i] - p0[i]) * t for i in range(3)), rad, rad, rad, blk)

    def front_px(fx, y, blk, want=None, depth=1):
        """앞쪽에서 처음 만나는 블록을 바꿈 (want 가 있으면 그 블록일 때만)"""
        fx, y = int(round(fx)), int(round(y))
        for fz in range(16, -4, -1):
            c = get(fx, fz, y)
            if c:
                if want is None or c == P[want]:
                    for d in range(depth):
                        at(fx, fz - d, y, blk)
                return

    # 장화 · 다리 · 무릎 띠
    for s in (-1, 1):
        ell(s * 4.6, base + 2.0, 1.2, 3.5, 2.2, 4.6, "light_gray_concrete", p=3)
        ell(s * 4.6, base + 1.2, 1.2, 3.6, 0.7, 4.7, "gray_concrete", p=3)
        ell(s * 4.6, base + 7.5, 0, 3.0, 4.2, 3.0, "white_concrete", p=3)
        ell(s * 4.6, base + 6.5, 0, 3.15, 0.6, 3.15, "yellow_concrete", p=3)
    # 엉덩이 · 몸통 · 허리띠 · 배낭
    ell(0, base + 11.5, 0, 8.4, 2.6, 6.2, "light_gray_concrete", p=3)
    ell(0, base + 19.5, 0, 10.0, 8.0, 7.0, "white_concrete", p=3.5)
    ell(0, base + 12.4, 0, 9.3, 1.1, 6.8, "light_gray_concrete", p=3)
    ell(0, base + 20, -5.5, 8.5, 8.0, 4.0, "light_gray_concrete", p=4)
    for s in (-1, 1):
        ell(s * 4.5, base + 21, -9.2, 2.2, 6.0, 1.6, "white_concrete", p=3)       # 산소통
        ell(s * 4.5, base + 27.2, -9.2, 1.4, 0.8, 1.0, "light_blue_concrete", p=2)
    # 가슴판 (노랑 · 흰 테) + 단추 3개
    for fx in range(-5, 6):
        for y in range(base + 18, base + 26):
            edge = abs(fx) == 5 or y in (base + 18, base + 25)
            front_px(fx, y, "light_gray_concrete" if edge else "yellow_concrete", "white_concrete")
    for fx, c in ((-2, "red_concrete"), (0, "sea_lantern"), (2, "lime_concrete")):
        front_px(fx, base + 21, c, "yellow_concrete")
    for fx in range(-3, 4):
        front_px(fx, base + 23, "gray_concrete", "yellow_concrete")
    # 어깨 · 팔 (배 앞의 고리를 양손으로 듦)
    gcy, gz, GR = base + 10, 10, 8.6
    for s in (-1, 1):
        ell(s * 11, base + 24.5, 0, 3.8, 3.4, 3.8, "light_gray_concrete")
        ell(s * 11, base + 26.6, 0, 3.0, 0.9, 3.0, "yellow_concrete")
        limb((s * 12, base + 22.5, 0), (s * 12.8, base + 15, 3), 2.5, "white_concrete")
        ell(s * 12.8, base + 15, 3, 2.7, 2.7, 2.7, "light_gray_concrete")             # 팔꿈치
        limb((s * 12.8, base + 15, 3), (s * (GR + 1.2), gcy + 2.5, gz - 0.5), 2.3, "white_concrete")
        ell(s * (GR + 1.0), gcy + 1.5, gz + 0.5, 2.6, 3.0, 2.6, "light_gray_concrete")  # 장갑
    # 고리 (세로 원, 배 앞): 남색 몸 · 빛 테 · 검은 가운데 (안쪽에 희미한 하늘색 소용돌이)
    for fx in range(-11, 12):
        for y in range(gcy - 11, gcy + 12):
            d = math.hypot(fx, y - gcy)
            a = math.degrees(math.atan2(y - gcy, fx))
            for fz in (gz, gz + 1, gz + 2):
                if d <= 5.0:
                    glow = 2.9 < d <= 3.7
                    if fz == gz + 1:
                        at(fx, fz, y, "cyan_stained_glass" if glow else "black_stained_glass")
                    elif fz == gz:
                        at(fx, fz, y, "sea_lantern" if glow else "black_concrete")
                elif d <= 6.2:
                    at(fx, fz, y, "sea_lantern" if fz >= gz + 1 else "light_blue_concrete")
                elif d <= GR:
                    at(fx, fz, y, "blue_concrete" if (fz < gz + 2 or d < GR - 0.6) else "light_blue_concrete")
                    if fz == gz + 2 and abs(d - 7.4) < 0.5 and int(a + 360) % 30 < 8:
                        at(fx, fz, y, "sea_lantern")
                elif d <= GR + 0.9 and fz == gz + 1:
                    at(fx, fz, y, "light_blue_concrete")
    # 머리: 큰 흰 헬멧 · 검은 얼굴판 · 빛나는 눈 · 웃는 입 · 귀 · 안테나
    hy = base + 37
    ell(0, hy - 10.8, 0, 6.8, 1.3, 6.2, "light_gray_concrete")                     # 목 칼라
    ell(0, hy, 0, 11.5, 10.0, 10.0, "white_concrete")

    def face(fx, y):
        return rrect(fx, y - (hy - 0.5), 7.8, 5.8, 3.8) > 0
    for fx in range(-10, 11):
        for y in range(hy - 9, hy + 9):
            if face(fx, y):
                front_px(fx, y, "black_concrete", "white_concrete", depth=2)
    for fx in range(-10, 11):
        for y in range(hy - 9, hy + 9):
            if not face(fx, y) and any(face(fx + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                front_px(fx, y, "light_blue_concrete", "white_concrete")
    for s in (-1, 1):
        for fx in range(-3, 4):
            for dy in range(-4, 5):
                if (fx / 2.2) ** 2 + (dy / 3.1) ** 2 <= 1:
                    front_px(s * 3.6 + fx, hy + 1 + dy, "sea_lantern", "black_concrete")
        front_px(s * 3.6 - s * 1, hy + 2.6, "white_concrete", "sea_lantern")           # 눈 반짝임
    for fx in range(-4, 5):
        front_px(fx, hy - 3.6 + round(0.1 * fx * fx), "sea_lantern", "black_concrete")
    for s in (-1, 1):
        front_px(s * 6.2, hy - 1.8, "pink_concrete", "black_concrete")                 # 볼
        ell(s * 11.4, hy, 0, 1.9, 3.6, 3.6, "light_gray_concrete")
        ell(s * 12.6, hy, 0, 0.9, 2.2, 2.2, "light_blue_concrete")
        at(s * 13, 0, hy, "sea_lantern")
    for y in range(hy + 10, hy + 14):
        at(0, 0, y, "light_gray_concrete")
    at(0, 0, hy + 14, "sea_lantern")
    at(0, 0, hy + 15, "end_rod")

    # ── 꼬마 로봇 4 (광장 가장자리)
    def mini(hx, hz, col, face):
        at, get = frame(hx, hz, face)
        for fx in range(-2, 3):
            for fz in range(-2, 3):
                at(fx, fz, FL + 1, "light_gray_concrete")
                at(fx, fz, FL + 2, "gray_concrete" if abs(fx) + abs(fz) > 3 else "light_gray_concrete")
                for y in range(FL + 3, FL + 8):
                    if abs(fx) + abs(fz) < 4:
                        at(fx, fz, y, "white_concrete")
        for fx in range(-2, 3):
            for y in (FL + 5, FL + 6):
                at(fx, 3, y, "black_concrete")
        at(-1, 3, FL + 6, "sea_lantern"); at(1, 3, FL + 6, "sea_lantern")
        at(0, 3, FL + 4, col)
        at(0, 0, FL + 8, col); at(0, 0, FL + 9, "end_rod")
        for s in (-3, 3):
            at(s, 0, FL + 5, col); at(s, 0, FL + 4, "light_gray_concrete")
    mini(-44, 10, "yellow_concrete", "E")
    mini(44, 10, "lime_concrete", "W")
    mini(-27, 33, "orange_concrete", "E")
    mini(27, 33, "pink_concrete", "W")

    # ── 배경: 유리 돔 4 · 하늘의 행성
    for hx0, hz0, dr in ((-63, -32, 7.5), (63, -32, 7.5), (-58, 34, 5.5), (58, 34, 5.5)):
        R0 = int(dr) + 1
        for fx in range(-R0 - 1, R0 + 2):
            for fz in range(-R0 - 1, R0 + 2):
                d = math.hypot(fx, fz)
                if d <= dr + 1:
                    put(hx0 + fx, FL + 1, hz0 + fz, "smooth_quartz")
                    if dr < d:
                        put(hx0 + fx, FL + 2, hz0 + fz, "light_blue_concrete")
        for fx in range(-R0, R0 + 1):
            for fz in range(-R0, R0 + 1):
                for yy in range(0, R0 + 1):
                    d = math.sqrt(fx * fx + fz * fz + yy * yy)
                    if dr - 1.0 < d <= dr:
                        ang2 = math.degrees(math.atan2(fz, fx)) % 45
                        rib = ang2 < 7 or yy == 0
                        put(hx0 + fx, FL + 2 + yy, hz0 + fz, "white_concrete" if rib else "light_blue_stained_glass")
        for fx in range(-2, 3):
            for fz in range(-2, 3):
                if abs(fx) + abs(fz) < 3:
                    put(hx0 + fx, FL + 2, hz0 + fz, "sea_lantern")
        put(hx0, FL + 3 + int(dr), hz0, "sea_lantern")
    def sphere(cx, cy, cz, rad, pick):
        for x in range(int(cx - rad) - 1, int(cx + rad) + 2):
            for y in range(int(cy - rad) - 1, int(cy + rad) + 2):
                for z in range(int(cz - rad) - 1, int(cz + rad) + 2):
                    d = math.sqrt((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 + (z + 0.5 - cz) ** 2)
                    if d <= rad:
                        put(x, y, z, pick(x - cx, y - cy, z - cz))
    # 고리 행성 (북서쪽 하늘) + 작은 달 (북동쪽 하늘)
    pcx, pcy, pcz = -52, FL + 52, -70
    sphere(pcx, pcy, pcz, 7.5, lambda x, y, z: "purple_concrete" if math.sin(y * 0.9 + x * 0.15) > 0.2 else "magenta_concrete")
    for t in range(0, 360, 2):
        for rr in (10.5, 11.5, 12.5):
            x = math.cos(math.radians(t)) * rr
            z = math.sin(math.radians(t)) * rr
            y = x * 0.3 + z * 0.25
            if math.sqrt(x * x + y * y + z * z) > 8:
                put(pcx + x, pcy + y, pcz + z, "light_blue_concrete" if rr != 11.5 else "white_concrete")
    sphere(58, FL + 48, -64, 4.5, lambda x, y, z: "light_gray_concrete" if (x * 3 + z * 2 + y * 5) % 7 > 2 else "white_concrete")

    # ── 산호 (광장 밖, 돔 둘레 비움)
    near = plaza.copy()
    for _ in range(4):
        near = ~erode(~near)
    corals = ["bubble_coral_block", "brain_coral_block", "tube_coral_block", "bubble_coral_block", "horn_coral_block", "fire_coral_block"]
    domes = ((-63, -32, 11), (63, -32, 11), (-58, 34, 9), (58, 34, 9), (0, RZ, 16), (-44, 10, 5), (44, 10, 5),
             (-27, 33, 5), (27, 33, 5))
    n_ok = 0
    while n_ok < 110:
        a = rng.uniform(0, 360); rr = rng.uniform(R_PLAZA, R_ISLAND - 4)
        cx, cz = math.cos(math.radians(a)) * rr, math.sin(math.radians(a)) * rr
        if near[C + int(math.floor(cx)), C + int(math.floor(cz))]:
            continue
        if any(math.hypot(cx - dx, cz - dz) < dd for dx, dz, dd in domes):
            continue
        n_ok += 1
        blk = corals[int(rng.integers(0, len(corals)))]
        for j in range(int(rng.integers(2, 6))):
            tx, tz = cx + rng.uniform(-2.5, 2.5), cz + rng.uniform(-2.5, 2.5)
            if near[C + int(math.floor(tx)), C + int(math.floor(tz))]:
                continue
            hgt = int(rng.integers(3, 12))
            for y in range(FL + 1, FL + 1 + hgt):
                put(tx, y, tz, blk)
            if rng.random() < 0.5:
                put(tx, FL + 1 + hgt, tz, "sea_lantern")
            if rng.random() < 0.5:
                put(tx + 1, FL + 1, tz, blk); put(tx, FL + 1, tz + 1, blk)

    # ── 둘레 보이지 않는 벽
    edge = (r >= R_ISLAND - 1.5) & (r < R_ISLAND - 0.2)
    for y in range(FL + 1, H):
        v[:, y, :][edge] = P["barrier"]
    return v


def markers():
    """허브 원점 기준 (칸 가운데 좌표): 시작 자리 · 오락기 발판 가운데 / 이름표 자리 (+ 오락기가 보는 방향)"""
    out = {"spawn": (0.5, 1, 26.5, 180.0)}
    for key, b in BOOTHS.items():
        cx, cz = b["pos"]
        yaw = FACE_YAW[b["face"]]
        for name, fz, y in (("pad", 11, 1), ("label", 11, 4.2)):
            hx, hz = frame_xz(cx, cz, b["face"], 0, fz)
            out[f"{key}_{name}"] = (hx + 0.5, y, hz + 0.5, yaw)
    return out


def commands(greedy_boxes):
    v = build()
    cmds = []
    for pid, x0, y0, z0, x1, y1, z1 in greedy_boxes(v):
        st = "minecraft:" + PAL[pid]
        a = f"~{x0 - C} ~{y0 - FL} ~{z0 - C}"
        if (x0, y0, z0) == (x1, y1, z1):
            cmds.append(f"$execute positioned $(x) $(y) $(z) run setblock {a} {st}")
        else:
            cmds.append(f"$execute positioned $(x) $(y) $(z) run fill {a} ~{x1 - C} ~{y1 - FL} ~{z1 - C} {st}")
    return cmds


def forceload_range():
    return (-C, -C, N - 1 - C, N - 1 - C)


NIGHT = dict(sun=(0.15, 0.7, 0.7), sun_col=(1.0, 0.98, 1.0), amb_col=(0.55, 0.62, 0.78),
             sky_top=(0.01, 0.06, 0.16), sky_hor=(0.04, 0.22, 0.40), fog_col=(0.04, 0.18, 0.34))


def preview(path):
    import render as R
    from PIL import Image, ImageDraw, ImageFont
    v = build()
    v2 = np.where(v == P["barrier"], 0, v)
    pal = R.Palette(PAL)
    W, Hh = 1000, 560
    shots = [
        ((C + 0.5, FL + 3.6, C + 30), (C + 0.5, FL + 20, C - 50), 100),
        ((C - 23 + 0.5, FL + 9, C - 44 + 40), (C - 23 + 0.5, FL + 15, C - 44), 55),
        ((C + 0.5, FL + 10, C + 4), (C + 0.5, FL + 28, C + RZ), 62),
        ((C + 66, FL + 62, C + 72), (C, FL + 6, C - 16), 55),
    ]
    ims = [R.render(v2, pal, W, Hh, cam, tgt, fov=fov, ss=2, fog_dist=900, **NIGHT) for cam, tgt, fov in shots]
    labels = ["처음 들어오면 서는 자리에서 (광장 남쪽 → 로봇 쪽)",
              "오락기 앞 (신화쟁탈전) — 빛나는 간판 · 둥근 화면 · 조작판 · 입장 발판",
              "거대 우주인 로봇 — 포털 고리를 든 모습",
              "하늘에서 — 흰 광장 · 오락기 4대 · 산호 섬 · 유리 돔"]
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
    out = Image.new("RGB", (W, Hh * len(ims)))
    for i, im in enumerate(ims):
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W, 40), fill=(4, 12, 28))
        d.text((14, 6), labels[i], font=font, fill=(140, 220, 255))
        out.paste(im, (0, Hh * i))
    out.save(path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview(sys.argv[1] if len(sys.argv) > 1 else "hub.png")
