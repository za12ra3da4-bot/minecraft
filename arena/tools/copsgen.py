"""경찰과 도둑 (경도) — 밤하늘에 떠 있는 네온 대도시 (허브 보라 오락기로 입장)

 도시 193×193 · 4차선 도로 바둑판 (가로 · 세로 4줄, 폭 10: 중앙 겹노란선 · 차선 점선) · 인도 3칸 (연석)
 구역 25개 (모두 들어갈 수 있는 건물: 층마다 바닥 · 천장 조명 · 상자/책장/가구 = 숨을 곳 · 사다리로 옥상까지)
   경찰서 + 감옥 (남서) · 탈출 헬기장 + 격납고 (북동) · 은행 (기둥 현관 · 금고) · 카지노 (네온 · 전구 간판)
   보석상 · 박물관 (유리 돔) · 창고 (컨테이너 · 하역장) · 편의점 · 중앙 광장 + 랜드마크 타워 (꼭대기 전망대 = 대기실)
   유리 사무실 빌딩 · 벽돌 아파트 (발코니 · 비상계단 · 물탱크) · 상가 (진열창 · 줄무늬 차양 · 네온 간판)
   공원 2 · 입체 주차장 · 공사장
 거리: 신호등 · 가로등 · 버스 정류장 · 벤치 · 소화전 · 가로수 · 주차된 차 / 둘레: 담 + 바깥 고층 스카이라인 (불 켜진 창)
 털이 장소 6 (heist_0..5) · 도둑 시작 자리 12 · 경찰 출동 · 감옥 안/밖 · 구출 발판 · 탈출 발판 · 대기실
 원점 = 도시 가운데 바닥 칸 (데이터팩 storage bg:kd origin)
"""
import math
import os

import numpy as np

E = 96                         # 도시 반폭 (-96..96)
SKY = 14                       # 바깥 스카이라인 폭
N = 2 * (E + SKY + 4) + 1
H = 96
FL = 16
C = N // 2
ROADS = (-60, -20, 20, 60)     # 도로 가운데
RW = 5                         # 도로 c-5 .. c+4
SW = 3                         # 인도 폭
TOWER_FLOORS = 12
WAIT_Y = 5 * TOWER_FLOORS + 2  # 대기실 바닥 (타워 꼭대기 전망대)

PAL = ["air"]
P = {"air": 0}


def pid(s):
    if s not in P:
        P[s] = len(PAL)
        PAL.append(s)
    return P[s]


def post(mat="andesite"):
    return f"{mat}_wall[up=true,east=none,west=none,north=none,south=none,waterlogged=false]"


def slab(mat, typ="bottom"):
    return f"{mat}_slab[type={typ},waterlogged=false]"


def stairs(mat, facing, half="bottom"):
    return f"{mat}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"


def trapdoor(mat, facing, half="bottom", open_=False):
    return f"{mat}_trapdoor[facing={facing},half={half},open={'true' if open_ else 'false'},powered=false,waterlogged=false]"


def ladder(facing):
    return f"ladder[facing={facing},waterlogged=false]"


BARS_EW = "iron_bars[east=true,west=true,north=false,south=false,waterlogged=false]"
BARS_NS = "iron_bars[east=false,west=false,north=true,south=true,waterlogged=false]"
LEAVES = "oak_leaves[persistent=true,distance=1,waterlogged=false]"
LANTERN = "lantern[hanging=false,waterlogged=false]"
LANTERN_H = "lantern[hanging=true,waterlogged=false]"
CHAIN = "iron_chain[axis=y,waterlogged=false]"
LAMP_ON = "redstone_lamp[lit=true]"
OUT = {"s": (0, 1), "n": (0, -1), "e": (1, 0), "w": (-1, 0)}
FACING = {"s": "south", "n": "north", "e": "east", "w": "west"}
OPP = {"s": "north", "n": "south", "e": "west", "w": "east"}
OPPS = {"s": "n", "n": "s", "e": "w", "w": "e"}

# 3×5 글자 (간판)
FONT = {
    "P": ["XXX", "X.X", "XXX", "X..", "X.."], "O": ["XXX", "X.X", "X.X", "X.X", "XXX"],
    "L": ["X..", "X..", "X..", "X..", "XXX"], "I": ["XXX", ".X.", ".X.", ".X.", "XXX"],
    "C": ["XXX", "X..", "X..", "X..", "XXX"], "E": ["XXX", "X..", "XX.", "X..", "XXX"],
    "B": ["XX.", "X.X", "XX.", "X.X", "XX."], "A": [".X.", "X.X", "XXX", "X.X", "X.X"],
    "N": ["X.X", "XXX", "XXX", "X.X", "X.X"], "K": ["X.X", "XX.", "X..", "XX.", "X.X"],
    "S": ["XXX", "X..", "XXX", "..X", "XXX"], "M": ["X.X", "XXX", "X.X", "X.X", "X.X"],
    "U": ["X.X", "X.X", "X.X", "X.X", "XXX"], "H": ["X.X", "X.X", "XXX", "X.X", "X.X"],
    "T": ["XXX", ".X.", ".X.", ".X.", ".X."], "R": ["XX.", "X.X", "XX.", "X.X", "X.X"],
    "G": ["XXX", "X..", "X.X", "X.X", "XXX"], "2": ["XXX", "..X", "XXX", "X..", "XXX"],
    "4": ["X.X", "X.X", "XXX", "..X", "..X"], "7": ["XXX", "..X", ".X.", ".X.", ".X."],
    "/": ["..X", "..X", ".X.", "X..", "X.."], " ": ["...", "...", "...", "...", "..."],
}

PARAPET = {"stone_bricks": "stone_brick", "smooth_quartz": "smooth_quartz", "quartz_block": "quartz",
           "cut_sandstone": "cut_sandstone", "gray_concrete": "smooth_stone", "white_concrete": "smooth_quartz",
           "blue_concrete": "smooth_stone", "black_concrete": "blackstone", "polished_blackstone": "polished_blackstone",
           "bricks": "brick", "light_gray_concrete": "smooth_stone", "white_terracotta": "smooth_quartz",
           "dark_prismarine": "dark_prismarine", "terracotta": "brick", "purpur_block": "purpur",
           "deepslate_bricks": "deepslate_brick", "mud_bricks": "mud_brick", "brown_terracotta": "brick",
           "smooth_stone": "smooth_stone"}


def lot_ranges():
    edges = [-E]
    for c in ROADS:
        edges += [c - RW - 1, c + RW]
    edges.append(E)
    return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]


LOTS = lot_ranges()


STATS = {}
HELI_AT = {}       # 옥상 헬기 자리 (도시 좌표, y 는 바닥 기준) · 방향
BLDG = []          # 검사용: 지은 건물 (b, 층수, 문 방향들) — build() 때마다 새로

def build():
    BLDG.clear()
    DOORS = []
    OBST = []                   # 건물은 아니지만 문 앞을 막는 큰 것 (주차장 · 공사장)
    v = np.zeros((N, H, N), np.uint16)
    xx, zz = np.meshgrid(np.arange(N) - C + 0.5, np.arange(N) - C + 0.5, indexing="ij")
    rng = np.random.default_rng(21)
    marks = {}

    PROPS = []                  # 거리 시설 하나 = 놓은 칸 목록 (문 앞을 막으면 통째로 치움)
    cur_prop = [None]

    def put(x, y, z, blk):
        gx, gz, y = C + int(math.floor(x)), C + int(math.floor(z)), int(y)
        if 0 <= gx < N and 0 <= y < H and 0 <= gz < N:
            v[gx, y, gz] = pid(blk)
            if cur_prop[0] is not None:
                cur_prop[0].append((gx, y, gz, v[gx, y, gz]))

    def prop(fn):
        def wrapped(*a, **k):
            outer = cur_prop[0]
            cur_prop[0] = []
            r = fn(*a, **k)
            PROPS.append(cur_prop[0])
            cur_prop[0] = outer
            return r
        return wrapped

    def get(x, y, z):
        gx, gz, y = C + int(math.floor(x)), C + int(math.floor(z)), int(y)
        if 0 <= gx < N and 0 <= y < H and 0 <= gz < N:
            return PAL[v[gx, y, gz]]
        return "air"

    def box(x0, y0, z0, x1, y1, z1, blk):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    put(x, y, z, blk)

    def mark(name, x, y, z, yaw=None):
        marks[name] = (x + 0.5, y, z + 0.5) + ((yaw,) if yaw is not None else ())

    def chance(p):
        return rng.random() < p

    def pick(seq):
        return seq[int(rng.integers(0, len(seq)))]

    # ── 면 좌표: 건물 한쪽 벽을 바깥에서 볼 때 왼쪽부터 t (0..폭-1), 바깥으로 out 칸
    def fxz(side, x0, z0, x1, z1, t, out=0):
        if side == "s":
            return x0 + t, z1 + out
        if side == "n":
            return x1 - t, z0 - out
        if side == "e":
            return x1 + out, z1 - t
        return x0 - out, z0 + t

    def fwidth(side, x0, z0, x1, z1):
        return (x1 - x0 + 1) if side in "sn" else (z1 - z0 + 1)

    def fput(side, b, t, y, blk, out=0):
        x, z = fxz(side, *b, t, out)
        put(x, y, z, blk)

    def fget(side, b, t, y, out=0):
        x, z = fxz(side, *b, t, out)
        return get(x, y, z)

    def sign(side, b, text, y_top, blk, back=None, out=1):
        """벽에 3×5 글자 간판 (가운데 정렬)"""
        w = fwidth(side, *b)
        tw = len(text) * 4 - 1
        t0 = (w - tw) // 2
        for i, ch in enumerate(text):
            g = FONT.get(ch, FONT[" "])
            for r in range(5):
                for c in range(3):
                    t = t0 + i * 4 + c
                    if back:
                        fput(side, b, t, y_top - r, back, out - 1)
                    if g[r][c] == "X":
                        fput(side, b, t, y_top - r, blk, out)

    # ── 섬 + 바닥
    def rr(hw, rad):
        dx = np.abs(xx) - (hw - rad)
        dz = np.abs(zz) - (hw - rad)
        return np.where((dx > 0) & (dz > 0), np.hypot(dx, dz) <= rad, (np.abs(xx) <= hw) & (np.abs(zz) <= hw))
    for k in range(FL):
        y = FL - 1 - k
        hw = E + SKY + 3 - k * 5.0 - (k ** 1.7) * 0.4
        if hw < 4:
            break
        m = rr(hw, min(hw, 22))
        layer = np.where(np.sin(xx * 0.18 + k) + np.cos(zz * 0.21 - k * 0.5) > 0.3, pid("dark_prismarine"), pid("blue_terracotta"))
        v[:, y, :][m] = layer[m]
    v[:, FL, :][rr(E + SKY + 3, 22)] = pid("blue_terracotta")
    city = (np.abs(xx) <= E) & (np.abs(zz) <= E)
    v[:, FL, :][city] = pid("light_gray_concrete")

    def on_road(t):
        return any(c - RW <= t <= c + RW - 1 for c in ROADS)

    def near_cross(t, d):
        return any(c - RW - d <= t <= c + RW - 1 + d for c in ROADS)

    # ── 도로: 아스팔트 · 겹노란선 · 차선 점선 · 횡단보도 · 연석 · 인도 무늬
    for x in range(-E, E + 1):
        for z in range(-E, E + 1):
            rx, rz = on_road(x), on_road(z)
            if not (rx or rz):
                if near_cross(x, 1) or near_cross(z, 1):
                    put(x, FL, z, "smooth_stone")
                elif (near_cross(x, SW) or near_cross(z, SW)) and (x + z) % 7 == 0:
                    put(x, FL, z, "stone_bricks")
                continue
            blk = "gray_concrete"
            if rx and rz:
                put(x, FL, z, blk)
                continue
            c = min(ROADS, key=lambda c: abs(c - (x if rx else z)))
            u = (x if rx else z) - c               # 도로 가로 방향 칸
            s = z if rx else x                     # 도로 따라가는 좌표
            if u in (-1, 0):
                blk = "yellow_concrete"
            elif u in (-3, 2) and s % 6 < 3:
                blk = "white_concrete"
            for c2 in ROADS:
                if c2 + RW + 1 <= s <= c2 + RW + 3 or c2 - RW - 4 <= s <= c2 - RW - 2:
                    blk = "white_concrete" if u % 2 == 0 else "gray_concrete"
            put(x, FL, z, blk)

    # ── 거리 시설
    @prop
    def street_lamp(x, z):
        for y in range(FL + 1, FL + 6):
            put(x, y, z, post())
        put(x, FL + 6, z, "shroomlight")
        put(x, FL + 7, z, slab("smooth_stone"))

    @prop
    def traffic_light(x, z, face):
        for y in range(FL + 1, FL + 5):
            put(x, y, z, post("stone_brick"))
        dx, dz = OUT[face]
        for y in (FL + 5, FL + 6, FL + 7):
            put(x, y, z, "black_concrete")
        put(x + dx, FL + 7, z + dz, "red_stained_glass")
        put(x + dx, FL + 6, z + dz, "yellow_stained_glass")
        put(x + dx, FL + 5, z + dz, "lime_stained_glass")
        put(x, FL + 8, z, slab("blackstone"))

    @prop
    def hydrant(x, z):
        put(x, FL + 1, z, "red_concrete")
        put(x, FL + 2, z, post("red_sandstone"))

    @prop
    def bench(x, z, face, axis):
        for t in range(2):
            put(x + (t if axis == "x" else 0), FL + 1, z + (t if axis == "z" else 0), stairs("dark_oak", face))

    @prop
    def planter_tree(x, z, h=None):
        h = h or int(rng.integers(4, 7))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                put(x + dx, FL, z + dz, "podzol[snowy=false]")
                if dx or dz:
                    put(x + dx, FL + 1, z + dz, slab("stone_brick"))
        put(x, FL, z, "grass_block[snowy=false]")
        for y in range(FL + 1, FL + 1 + h):
            put(x, y, z, "oak_log[axis=y]")
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                for dy in range(-1, 2):
                    if abs(dx) + abs(dz) + abs(dy) <= 3 and (dx or dz or dy > 0):
                        put(x + dx, FL + h + dy, z + dz, LEAVES)
        put(x, FL + h + 2, z, LEAVES)

    @prop
    def bus_stop(x, z, axis):
        L = 5
        for t in range(L):
            px, pz = (x + t, z) if axis == "x" else (x, z + t)
            ox, oz = (0, -1) if axis == "x" else (-1, 0)
            put(px, FL + 4, pz, slab("smooth_quartz"))
            put(px + ox, FL + 4, pz + oz, slab("smooth_quartz"))
            for y in (FL + 1, FL + 2, FL + 3):
                put(px + ox, y, pz + oz, "light_blue_stained_glass")
            if t in (0, L - 1):
                for y in range(FL + 1, FL + 4):
                    put(px, y, pz, post("diorite"))
        for t in (1, 2, 3):
            px, pz = (x + t, z) if axis == "x" else (x, z + t)
            put(px, FL + 1, pz, stairs("smooth_quartz", "south" if axis == "x" else "east"))

    @prop
    def car(x, z, col, axis="x", police=False):
        L, Wd = (5, 3) if axis == "x" else (3, 5)
        for dx in range(L):
            for dz in range(Wd):
                put(x + dx, FL + 1, z + dz, col)
        for dx, dz in ((0, 0), (L - 1, 0), (0, Wd - 1), (L - 1, Wd - 1)):
            put(x + dx, FL + 1, z + dz, "black_concrete")
        glass = "light_gray_stained_glass" if police else "black_stained_glass"
        if axis == "x":
            for dx in range(1, L - 1):
                for dz in range(Wd):
                    put(x + dx, FL + 2, z + dz, glass)
            for dx in (1, 2, 3):
                put(x + dx, FL + 3, z + 1, col)
            put(x, FL + 1, z + 1, "sea_lantern")
            put(x + L - 1, FL + 1, z + 1, LAMP_ON)
        else:
            for dx in range(L):
                for dz in range(1, Wd - 1):
                    put(x + dx, FL + 2, z + dz, glass)
            for dz in (1, 2, 3):
                put(x + 1, FL + 3, z + dz, col)
            put(x + 1, FL + 1, z, "sea_lantern")
            put(x + 1, FL + 1, z + Wd - 1, LAMP_ON)
        if police:
            mx, mz = (x + 2, z + 1) if axis == "x" else (x + 1, z + 2)
            put(mx, FL + 4, mz, "red_stained_glass")
            put(mx + (1 if axis == "x" else 0), FL + 4, mz + (0 if axis == "x" else 1), "blue_stained_glass")

    for c in ROADS:
        for s in range(-E + 5, E - 3, 12):
            if near_cross(s, SW + 3):
                continue
            street_lamp(c - RW - 2, s)
            street_lamp(c + RW + 1, s)
            street_lamp(s, c - RW - 2)
            street_lamp(s, c + RW + 1)
            if (s // 12) % 3 == 1:
                hydrant(c - RW - 2, s + 3)
                hydrant(s + 3, c + RW + 1)
    for c in ROADS:
        for s2 in range(-E + 11, E - 8, 24):
            if near_cross(s2, SW + 5):
                continue
            for off in (c - RW - 2, c + RW + 1):
                if chance(0.7):
                    put(off, FL + 1, s2 + 5, "cauldron") if chance(0.5) else None
    for cx in ROADS:
        for cz in ROADS:
            traffic_light(cx - RW - 1, cz - RW - 1, "n")
            traffic_light(cx + RW, cz + RW, "s")
            traffic_light(cx + RW, cz - RW - 1, "e")
            traffic_light(cx - RW - 1, cz + RW, "w")
    for c in (-20, 20):
        bus_stop(-42, c - RW - 3, "x")
        bus_stop(36, c + RW + 3, "x")
        bus_stop(c - RW - 3, -44, "z")
        bus_stop(c + RW + 3, 38, "z")
    car_cols = ["red_concrete", "blue_concrete", "white_concrete", "yellow_concrete", "black_concrete", "lime_concrete",
                "orange_concrete", "light_gray_concrete", "cyan_concrete"]
    for c in ROADS:
        for s in range(-E + 8, E - 6, 14):
            if near_cross(s, 6):
                continue
            if chance(0.45):
                car(c + RW - 3, s, pick(car_cols), "z")
            if chance(0.45):
                car(s, c - RW, pick(car_cols), "x")

    # ── 건물 뼈대: 층 (5칸) · 벽 · 창 · 층 띠 · 모서리 기둥 · 천장 조명 · 가구 · 사다리 · 옥상 난간 · 문 차양
    def shell(b, floors, wall, trim, win="glass", pattern="grid", doors=("s",), ground=None, interior=True,
              floor_mat="polished_andesite", sill=None, roof="items"):
        x0, z0, x1, z1 = b
        top = FL + 5 * floors
        # 도시 둘레 담을 보는 문은 안쪽 면으로 옮김 (문 앞이 담 · 보이지 않는 벽이면 못 들어감)
        faces_wall = {"e": x1 >= E - 5, "w": x0 <= -E + 5, "s": z1 >= E - 5, "n": z0 <= -E + 5}
        ok = [d for d in doors if not faces_wall[d]]
        for d in doors:
            if faces_wall[d]:
                for alt in (OPPS[d], "s", "n", "e", "w"):
                    if not faces_wall[alt] and alt not in ok:
                        ok.append(alt)
                        break
        doors = tuple(ok)
        BLDG.append([tuple(b), floors, doors])
        for f in range(floors):
            y0 = FL + 5 * f
            if f > 0:
                box(x0 + 1, y0, z0 + 1, x1 - 1, y0, z1 - 1, floor_mat)
            for side in "snew":
                w = fwidth(side, *b)
                for t in range(w):
                    for dy in range(1, 5):
                        blk = wall
                        if f == 0 and ground == "shop" and 1 <= t <= w - 2 and dy <= 3:
                            blk = "glass" if t % 4 else trim
                        elif pattern == "curtain":
                            blk = win if (t % 3 and 1 <= t <= w - 2) else trim
                        elif pattern == "band" and dy in (2, 3) and 1 <= t <= w - 2:
                            blk = win
                        elif pattern == "grid" and dy in (2, 3) and 2 <= t <= w - 3 and (t - 2) % 3 != 2:
                            blk = win
                        elif pattern == "small" and dy in (2, 3) and 2 <= t <= w - 3 and t % 2 == 0:
                            blk = win
                        fput(side, b, t, y0 + dy, blk)
                    if sill and f > 0 and 2 <= t <= w - 3:
                        if (pattern == "grid" and (t - 2) % 3 != 2) or (pattern == "small" and t % 2 == 0):
                            fput(side, b, t, y0 + 1, slab(sill, "top"), 1)
                for t in range(w):
                    fput(side, b, t, y0 + 5, trim)
            if interior:
                for x in range(x0 + 3, x1 - 1, 4):
                    for z in range(z0 + 3, z1 - 1, 4):
                        put(x, y0 + 5, z, "sea_lantern")
                n = max(2, (x1 - x0) * (z1 - z0) // 30)
                for _ in range(n):
                    bx = int(rng.integers(x0 + 2, x1 - 1)); bz = int(rng.integers(z0 + 2, z1 - 1))
                    if bx <= x0 + 2 and bz <= z0 + 2:
                        continue
                    kind = rng.random()
                    if kind < 0.35:
                        put(bx, y0 + 1, bz, "barrel[facing=up,open=false]")
                        if chance(0.5):
                            put(bx, y0 + 2, bz, "barrel[facing=up,open=false]")
                    elif kind < 0.55:
                        put(bx, y0 + 1, bz, "bookshelf"); put(bx, y0 + 2, bz, "bookshelf")
                    elif kind < 0.7:
                        put(bx, y0 + 1, bz, "spruce_planks"); put(bx, y0 + 2, bz, slab("spruce"))
                    elif kind < 0.85:
                        for t in range(3):
                            if bx + t < x1:
                                put(bx + t, y0 + 1, bz, "white_concrete"); put(bx + t, y0 + 2, bz, "white_concrete")
                    else:
                        put(bx, y0 + 1, bz, "potted_fern")
        for x, z in ((x0, z0), (x0, z1), (x1, z0), (x1, z1)):
            for y in range(FL + 1, top + 2):
                put(x, y, z, trim)
        box(x0, top, z0, x1, top, z1, trim)
        for side in "snew":
            for t in range(fwidth(side, *b)):
                fput(side, b, t, top + 1, slab(PARAPET.get(trim, "smooth_stone")) if t % 2 else trim)
        for y in range(FL + 1, top + 1):
            put(x0 + 1, y, z0 + 1, ladder("south"))
        facade_details(b, floors, top, trim, pattern, sill)
        # 문은 모든 건물을 다 지은 뒤에 뚫음 (다른 건물 벽을 보고 있으면 거리 쪽 면으로 옮김 — 맨 끝 '문 정하기')
        if roof == "items":
            roof_items(b, top)
        return top

    CORN = {"stone_bricks": "stone_brick", "smooth_quartz": "smooth_quartz", "quartz_block": "quartz", "bricks": "brick",
            "polished_blackstone": "polished_blackstone", "cut_sandstone": "smooth_sandstone", "purpur_block": "purpur",
            "brown_terracotta": "brick", "white_terracotta": "smooth_quartz", "dark_prismarine": "dark_prismarine",
            "deepslate_bricks": "deepslate_brick", "mud_bricks": "mud_brick", "white_concrete": "smooth_quartz",
            "gray_concrete": "stone_brick", "light_gray_concrete": "stone_brick", "black_concrete": "blackstone",
            "blue_concrete": "stone_brick", "lime_concrete": "smooth_quartz", "light_blue_concrete": "smooth_quartz"}

    def facade_details(b, floors, top, trim, pattern, sill):
        cm = CORN.get(trim, "stone_brick")
        for side in "snew":
            w = fwidth(side, *b)
            # 지붕 아래 처마 (뒤집힌 계단이 한 칸 튀어나옴) · 바닥 받침 띠
            for t in range(-1, w + 1):
                fput(side, b, t, top, stairs(cm, OPP[side], "top"), 1)
                fput(side, b, t, FL + 1, trim if pattern == "curtain" else "polished_andesite", 0) if t in (0, w - 1) else None
            # 튀어나온 기둥 줄 (유리벽 빌딩 · 넓은 벽만)
            if pattern in ("curtain", "band") and w >= 12:
                for t in range(3, w - 3, 6):
                    for y in range(FL + 5, top):
                        fput(side, b, t, y, trim, 1)
            # 창문 덧문 · 벽 에어컨 (창이 있는 집)
            if pattern in ("grid", "small"):
                for f in range(1, floors):
                    y0 = FL + 5 * f
                    for t in range(2, w - 2):
                        win_here = (pattern == "grid" and (t - 2) % 3 != 2) or (pattern == "small" and t % 2 == 0)
                        if not win_here:
                            continue
                        left_edge = (pattern == "grid" and (t - 2) % 3 == 0) or pattern == "small"
                        right_edge = (pattern == "grid" and (t - 2) % 3 == 1) or pattern == "small"
                        if sill and chance(0.5):
                            sh = trapdoor("spruce" if trim != "smooth_quartz" else "birch", FACING[side], "bottom", True)
                            if left_edge and fget(side, b, t - 1, y0 + 2, 1) == "air":
                                fput(side, b, t - 1, y0 + 2, sh, 1); fput(side, b, t - 1, y0 + 3, sh, 1)
                            if right_edge and fget(side, b, t + 1, y0 + 2, 1) == "air":
                                fput(side, b, t + 1, y0 + 2, sh, 1); fput(side, b, t + 1, y0 + 3, sh, 1)
                        elif chance(0.08) and fget(side, b, t, y0 + 1, 1) == "air":
                            fput(side, b, t, y0 + 1, "light_gray_concrete", 1)
                            fput(side, b, t, y0 + 1, "light_gray_concrete", 1)
                            fput(side, b, t, y0, trapdoor("iron", OPP[side], "top"), 1)

    def roof_items(b, top):
        x0, z0, x1, z1 = b
        w, d = x1 - x0, z1 - z0
        for t in range(2, min(w - 2, 10), 3):
            put(x0 + 2 + t, top + 1, z1 - 2, "light_gray_concrete")
            put(x0 + 2 + t, top + 2, z1 - 2, trapdoor("iron", "north"))
        if w >= 10 and d >= 10 and chance(0.7):
            tx, tz = x1 - 4, z0 + 4
            for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                for y in range(top + 1, top + 3):
                    put(tx + dx, y, tz + dz, post("cobblestone"))
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if abs(dx) + abs(dz) <= 3:
                        edge = abs(dx) == 2 or abs(dz) == 2 or abs(dx) + abs(dz) == 3
                        for y in range(top + 3, top + 6):
                            put(tx + dx, y, tz + dz, "spruce_planks" if edge else "air")
                        put(tx + dx, top + 6, tz + dz, slab("spruce"))
            put(tx, top + 7, tz, slab("spruce"))
        for y in range(top + 1, top + 6):
            put(x0 + 3, y, z0 + 3, CHAIN if y > top + 1 else "iron_block")
        put(x0 + 3, top + 6, z0 + 3, LAMP_ON)
        kind = rng.random()
        if w >= 9 and d >= 9:
            if kind < 0.35:                                   # 옥상 정원
                box(x0 + 5, top + 1, z0 + 6, x1 - 5, top + 1, z1 - 5, "grass_block[snowy=false]")
                for _ in range(max(2, (w * d) // 40)):
                    gx = int(rng.integers(x0 + 5, max(x0 + 6, x1 - 4))); gz = int(rng.integers(z0 + 6, max(z0 + 7, z1 - 4)))
                    put(gx, top + 2, gz, pick(["poppy", "dandelion", "cornflower", "azure_bluet", "short_grass", "oak_leaves[persistent=true,distance=1,waterlogged=false]"]))
                for x in range(x0 + 4, x1 - 3):
                    put(x, top + 1, z0 + 5, slab("spruce")); put(x, top + 1, z1 - 4, slab("spruce"))
            elif kind < 0.65:                                 # 태양광 패널 줄
                for z in range(z0 + 6, z1 - 3, 3):
                    for x in range(x0 + 5, x1 - 4):
                        put(x, top + 1, z, "daylight_detector[inverted=false,power=0]")
            else:                                             # 위성 안테나
                dx, dz = x0 + w // 2, z0 + d // 2
                put(dx, top + 1, dz, "iron_block"); put(dx, top + 2, dz, post("andesite"))
                for ox in (-1, 0, 1):
                    for oy in (0, 1):
                        put(dx + ox, top + 3 + oy, dz, "white_concrete" if oy == 0 or ox == 0 else "light_gray_concrete")
                put(dx, top + 4, dz + 1, LAMP_ON)
        if chance(0.5) and d >= 9:
            box(x0 + 1, top + 1, z0 + 5, x0 + 3, top + 3, z0 + 7, "light_gray_concrete")
            put(x0 + 2, top + 4, z0 + 6, slab("smooth_stone"))

    def balconies(side, b, floors, every=6):
        w = fwidth(side, *b)
        rail_par = BARS_EW if side in "sn" else BARS_NS
        rail_perp = BARS_NS if side in "sn" else BARS_EW
        for f in range(1, floors):
            y0 = FL + 5 * f
            for t0 in range(3, w - 5, every):
                for t in range(t0, t0 + 3):
                    fput(side, b, t, y0, slab("smooth_stone", "top"), 1)
                    fput(side, b, t, y0, slab("smooth_stone", "top"), 2)
                    fput(side, b, t, y0 + 1, rail_par, 3) if False else fput(side, b, t, y0 + 1, rail_par, 2)
                for o in (1,):
                    fput(side, b, t0 - 1, y0 + 1, rail_perp, o)
                    fput(side, b, t0 + 3, y0 + 1, rail_perp, o)
                if chance(0.5):
                    fput(side, b, t0 + 1, y0 + 1, "potted_red_tulip", 1)

    def fire_escape(side, b, floors):
        w = fwidth(side, *b)
        t0 = max(2, w - 6)
        rail = BARS_EW if side in "sn" else BARS_NS
        for f in range(1, floors):
            y0 = FL + 5 * f
            for t in range(t0, t0 + 4):
                fput(side, b, t, y0, trapdoor("iron", OPP[side], "top"), 1)
                fput(side, b, t, y0 + 1, rail, 2)
        for y in range(FL + 1, FL + 5 * floors + 1):
            if (y - FL) % 5:
                fput(side, b, t0, y, ladder(FACING[side]), 1)

    def awning(side, b, cols=("red_wool", "white_wool")):
        w = fwidth(side, *b)
        for t in range(1, w - 1):
            col = cols[(t // 2) % len(cols)]
            fput(side, b, t, FL + 4, col, 1)
            fput(side, b, t, FL + 4, col, 2)

    def neon_strip(side, b, y, glass, light, t0=1, t1=None):
        w = fwidth(side, *b)
        t1 = t1 if t1 is not None else w - 2
        for t in range(t0, t1 + 1):
            fput(side, b, t, y, light, 0)
            fput(side, b, t, y, glass, 1)

    def vault(x, z, name, kind="gold", face="s"):
        """털이 장소: 빛나는 받침 + 금 · 보석 더미 · 랜턴 기둥 4 (표지는 받침 앞 2칸)"""
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                put(x + dx, FL, z + dz, "yellow_stained_glass")
                put(x + dx, FL - 1, z + dz, "ochre_froglight")
        top = {"gold": "gold_block", "gem": "diamond_block", "emerald": "emerald_block"}[kind]
        put(x, FL + 1, z, top)
        put(x - 1, FL + 1, z, "gold_block" if kind == "gold" else "barrel[facing=up,open=false]")
        put(x + 1, FL + 1, z, "barrel[facing=up,open=false]")
        put(x, FL + 2, z, {"gold": "yellow_carpet", "gem": "light_blue_carpet", "emerald": "lime_carpet"}[kind])
        for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            put(x + dx, FL + 1, z + dz, post("polished_blackstone"))
            put(x + dx, FL + 2, z + dz, LANTERN)
        dx, dz = OUT[face]
        i = len([k for k in marks if k.startswith("heist_")])
        mark(f"heist_{i}", x + dx * 2, 1, z + dz * 2)
        marks[f"heistname_{i}"] = name

    def lot(i, j):
        (x0, x1), (z0, z1) = LOTS[i], LOTS[j]
        x0 += SW if i > 0 else 2
        x1 -= SW if i < len(LOTS) - 1 else 2
        z0 += SW if j > 0 else 2
        z1 -= SW if j < len(LOTS) - 1 else 2
        return x0, z0, x1, z1

    def split(b, nx, nz, gap=3):
        x0, z0, x1, z1 = b
        out = []
        wx = (x1 - x0 + 1 - gap * (nx - 1)) // nx
        wz = (z1 - z0 + 1 - gap * (nz - 1)) // nz
        for a in range(nx):
            for c in range(nz):
                bx0 = x0 + a * (wx + gap)
                bz0 = z0 + c * (wz + gap)
                bx1 = x1 if a == nx - 1 else bx0 + wx - 1
                bz1 = z1 if c == nz - 1 else bz0 + wz - 1
                out.append((bx0, bz0, bx1, bz1))
        return out

    @prop
    def dumpsters(b):
        x0, z0, x1, z1 = b
        for _ in range(2):
            ax = int(rng.integers(x0, max(x0 + 1, x1 - 1))); az = int(rng.integers(z0, max(z0 + 1, z1 - 1)))
            put(ax, FL + 1, az, "green_concrete"); put(ax + 1, FL + 1, az, "green_concrete")
            put(ax, FL + 2, az, trapdoor("dark_oak", "north")); put(ax + 1, FL + 2, az, trapdoor("dark_oak", "north"))

    # ═════════════ 구역별 건물 (i: 서→동, j: 북→남)
    # 털이 장소 순서: 은행 · 카지노 · 보석상 · 창고 · 박물관 · 편의점 (Skript 이름표 순서와 같음)

    # ── (1,1) 은행: 석영 + 기둥 현관 + 박공 + 금빛 띠 + BANK
    b = lot(1, 1)
    x0, z0, x1, z1 = b
    bb = (x0, z0, x1, z1 - 5)
    top = shell(bb, 3, "quartz_block", "smooth_quartz", win="light_blue_stained_glass", pattern="grid", doors=("s",),
                sill="smooth_quartz", floor_mat="polished_diorite")
    vault((x0 + x1) // 2, z0 + 5, "은행 금고", "gold", "s")
    for x in range(x0 + 3, x1 - 2):
        put(x, FL + 1, z0 + 10, "polished_andesite"); put(x, FL + 2, z0 + 10, "glass")
    bdx = x0 + fwidth("s", *bb) // 2 - 1                 # 문 왼쪽 칸
    for x in range(x0 + 2, x1 - 1, 3):
        if bdx - 1 <= x <= bdx + 2:
            continue
        for y in range(FL + 1, FL + 10):
            put(x, y, z1 - 3, "quartz_pillar[axis=y]")
    box(x0 + 1, FL + 10, z1 - 4, x1 - 1, FL + 10, z1 - 2, "smooth_quartz")
    half = (x1 - x0) // 2
    for k in range(half):
        lx, rx_ = x0 + 1 + k, x1 - 1 - k
        if lx > rx_:
            break
        y = FL + 11 + k // 2
        for x in range(lx, rx_ + 1):
            put(x, y, z1 - 2, "smooth_quartz")
    for x in range(x0, x1 + 1):
        put(x, FL, z1 - 1, "smooth_quartz")
        put(x, FL + 1, z1, slab("smooth_quartz"))
    neon_strip("s", bb, top - 1, "yellow_stained_glass", "ochre_froglight")
    sign("s", (x0, z0, x1, z1 - 2), "BANK", FL + 18, "ochre_froglight", out=1)

    # ── (3,1) 카지노: 검정 · 보라 · 네온 · 전구 테두리 · CASINO
    b = lot(3, 1)
    x0, z0, x1, z1 = b
    top = shell(b, 3, "polished_blackstone", "purpur_block", win="magenta_stained_glass", pattern="band", doors=("s", "w"),
                floor_mat="red_concrete")
    vault((x0 + x1) // 2, z0 + 6, "카지노 금고", "emerald", "s")
    for f in range(1, 3):
        neon_strip("s", b, FL + 5 * f + 1, "magenta_stained_glass", "pearlescent_froglight")
    for t in range(0, fwidth("s", *b), 2):
        fput("s", b, t, top + 1, LAMP_ON, 1)
        fput("w", b, t, top + 1, LAMP_ON, 1)
    for t in range(fwidth("s", *b)):
        for y in range(top + 1, top + 9):
            fput("s", b, t, y, "black_concrete", 0)
    sign("s", b, "CASINO", top + 7, "ochre_froglight", out=1)
    for t in range(fwidth("s", *b)):
        fput("s", b, t, top + 9, LAMP_ON, 0)
    for dx in range(-2, 3):
        for dz in range(1, 4):
            put((x0 + x1) // 2 + dx, FL, z1 + dz, "red_wool")

    # ── (3,3) 보석상 + 상가 3
    b = lot(3, 3)
    parts = split(b, 2, 2)
    x0, z0, x1, z1 = parts[0]
    shell(parts[0], 2, "white_concrete", "light_blue_concrete", win="glass", pattern="grid", doors=("n", "w"), ground="shop")
    vault((x0 + x1) // 2, (z0 + z1) // 2, "보석상", "gem", "n")
    awning("n", parts[0], ("light_blue_wool", "white_wool"))
    sign("w", parts[0], "GEMS", FL + 9, "sea_lantern", out=1)
    for k, pb in enumerate(parts[1:]):
        st = [("bricks", "stone_bricks"), ("orange_terracotta", "brown_terracotta"), ("cyan_terracotta", "white_terracotta")][k]
        fl = [3, 4, 2][k]
        shell(pb, fl, st[0], st[1], win="glass", pattern="grid", doors=("n", "e"), ground="shop", sill="stone_brick")
        awning("n", pb, [("red_wool", "white_wool"), ("lime_wool", "white_wool"), ("orange_wool", "yellow_wool")][k])
        if fl >= 3:
            balconies("e", pb, fl)

    # ── (0,1) 창고: 골함석 벽 · 셔터 · 하역장 · 컨테이너
    b = lot(0, 1)
    x0, z0, x1, z1 = b
    wb = (x0, z0, x1 - 8, z1)
    top = shell(wb, 2, "light_gray_concrete", "gray_concrete", win="black_stained_glass", pattern="small", doors=("n", "s"),
                floor_mat="smooth_stone")
    vault(x0 + 7, z0 + 7, "창고", "gold", "e")
    for side in "snew":
        for t in range(fwidth(side, *wb)):
            if t % 3 == 0:
                for y in range(FL + 1, top):
                    if fget(side, wb, t, y) not in ("air", "black_stained_glass"):
                        fput(side, wb, t, y, "iron_block")
    box(x1 - 7, FL + 1, z0, x1 - 6, FL + 1, z1, slab("smooth_stone"))
    for k, col in enumerate(("red_concrete", "blue_concrete", "lime_concrete", "orange_concrete")):
        cz = z0 + 1 + k * 6
        if cz + 4 > z1:
            break
        box(x1 - 4, FL + 1, cz, x1, FL + 3, cz + 4, col)
        for y in range(FL + 1, FL + 4):
            put(x1 - 4, y, cz + 2, BARS_NS)
    box(x1 - 4, FL + 4, z0 + 1, x1, FL + 6, z0 + 5, "cyan_concrete")
    dumpsters((x1 - 6, z0, x1 - 5, z1))

    # ── (1,3) 박물관: 사암 · 기둥 현관 · 구리 · 유리 돔 · MUSEUM
    b = lot(1, 3)
    x0, z0, x1, z1 = b
    mb = (x0, z0 + 4, x1, z1)
    top = shell(mb, 3, "sandstone", "cut_sandstone", win="glass", pattern="grid", doors=("n",), roof=None, floor_mat="smooth_sandstone")
    vault((x0 + x1) // 2, (z0 + z1) // 2 + 2, "박물관", "gem", "n")
    mdx = x1 - (fwidth("n", *mb) // 2 - 1)               # 문 칸 (북쪽 면은 오른쪽부터 셈)
    for x in range(x0 + 2, x1 - 1, 3):
        if mdx - 2 <= x <= mdx + 1:
            continue
        for y in range(FL + 1, FL + 13):
            put(x, y, z0 + 2, "quartz_pillar[axis=y]")
    box(x0 + 1, FL + 13, z0 + 1, x1 - 1, FL + 13, z0 + 3, "cut_sandstone")
    cx, cz = (x0 + x1) // 2, (z0 + 4 + z1) // 2
    R = min(x1 - x0, z1 - z0 - 4) // 2 - 2
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            for dy in range(0, R + 1):
                d = math.sqrt(dx * dx + dz * dz + dy * dy)
                if R - 1 < d <= R:
                    rib = dx == 0 or dz == 0 or abs(dx) == abs(dz)
                    put(cx + dx, top + 1 + dy, cz + dz, "oxidized_copper" if rib else "light_blue_stained_glass")
    put(cx, top + R + 2, cz, "lightning_rod[facing=up,powered=false,waterlogged=false]")
    sign("n", mb, "MUSEUM", FL + 19, "sea_lantern", out=4)

    # ── (2,4) 편의점 (24/7) + 아파트 + 유리 빌딩
    b = lot(2, 4)
    parts = split(b, 2, 1)
    x0, z0, x1, z1 = parts[0]
    cb = (x0, z0, x1, z0 + 11)
    shell(cb, 1, "white_concrete", "lime_concrete", win="glass", pattern="band", doors=("n",), ground="shop", roof=None)
    vault((x0 + x1) // 2, z0 + 6, "편의점", "emerald", "n")
    neon_strip("n", cb, FL + 4, "lime_stained_glass", "verdant_froglight")
    for t in range(fwidth("n", *cb)):
        for y in range(FL + 6, FL + 11):
            fput("n", cb, t, y, "white_concrete")
    sign("n", cb, "24/7", FL + 10, "verdant_froglight", out=1)
    ab = (x0, z0 + 14, x1, z1)
    shell(ab, 4, "bricks", "stone_bricks", win="glass", pattern="grid", doors=("w",), sill="stone_brick")
    fire_escape("e", ab, 4)
    shell(parts[1], 6, "deepslate_bricks", "polished_blackstone", win="cyan_stained_glass", pattern="curtain", doors=("n", "e"))

    # ── (0,4) 경찰서 + 감옥 (남서) · POLICE · 깃대 · 경찰차
    b = lot(0, 4)
    x0, z0, x1, z1 = b
    pb = (x0, z0, x1, z0 + 20)
    top = shell(pb, 3, "white_concrete", "blue_concrete", win="light_blue_stained_glass", pattern="band", doors=("s", "e"),
                floor_mat="light_gray_concrete")
    neon_strip("s", pb, FL + 5, "blue_stained_glass", "sea_lantern")
    neon_strip("e", pb, FL + 5, "blue_stained_glass", "sea_lantern")
    for t in range(fwidth("e", *pb)):
        for y in range(top + 1, top + 8):
            fput("e", pb, t, y, "blue_concrete")
    sign("e", pb, "POLICE", top + 6, "sea_lantern", out=1)
    jx0, jx1, jz0, jz1 = x0 + 1, x0 + 11, z0 + 5, z0 + 13
    box(jx0, FL, jz0, jx1, FL, jz1, "gray_concrete")
    box(jx0, FL + 1, jz0 - 1, jx1, FL + 4, jz0 - 1, "stone_bricks")
    box(jx0, FL + 5, jz0 - 1, jx1, FL + 5, jz1, "polished_andesite")
    for x in range(jx0, jx1 + 1):
        for y in range(FL + 1, FL + 5):
            put(x, y, jz1, BARS_EW)
    for z in range(jz0, jz1):
        for y in range(FL + 1, FL + 5):
            put(jx1, y, z, BARS_NS)
    put(jx0 + 5, FL + 5, jz0 + 3, "sea_lantern")
    mark("jail", jx0 + 5, 1, jz0 + 3, 180.0)
    mark("jail_out", jx0 + 5, 1, jz1 + 3, 0.0)
    mark("cop_spawn", x1 - 6, 1, z0 + 9, 180.0)
    car(x1 - 11, z0 + 14, "white_concrete", "x", police=True)
    for x in range(jx0 + 2, jx0 + 9):
        for y in range(FL + 1, FL + 4):
            put(x, y, z0 + 20, BARS_EW)
    rx, rz = jx0 + 5, z0 + 23
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            put(rx + dx, FL, rz + dz, "lime_stained_glass")
            put(rx + dx, FL - 1, rz + dz, "verdant_froglight")
    mark("rescue", rx, 1, rz)
    car(x1 - 8, z1 - 4, "white_concrete", "x", police=True)
    car(x1 - 16, z1 - 4, "white_concrete", "x", police=True)
    for y in range(FL + 1, FL + 14):
        put(x1 - 2, y, z1 - 2, CHAIN if y > FL + 1 else "iron_block")
    box(x1 - 2, FL + 11, z1 - 1, x1 - 2, FL + 13, z1 + 1, "blue_wool")

    # ── (4,0) 탈출 헬기장 타워 (북동) — 7층 (35칸) 꼭대기 옥상 헬기장 · 안쪽 계단실 (층마다 꺾이는 계단 2칸 폭) · 구석 사다리
    #   옥상: 검정 원판 + 흰 H + 노란 빛 테두리 · 가장자리 빛 기둥 · 유리 난간 · 계단 집 · 관제실 · 투광등 · 풍향 자루 · 안테나
    #   헬기 = 블록 디스플레이 (heli.py, 데이터팩이 따로 소환) — 타는 문 앞이 탈출 표지
    b = lot(4, 0)
    x0, z0, x1, z1 = b
    hb = (x0 + 1, z0 + 1, x1 - 1, z1 - 1)
    HF = 7
    top = shell(hb, HF, "black_concrete", "gray_concrete", win="cyan_stained_glass", pattern="curtain", doors=("s", "w"),
                roof=None, floor_mat="smooth_stone")
    bx0, bz0, bx1, bz1 = hb
    xa = bx0 + 2
    lanes = ((bz1 - 5, bz1 - 4), (bz1 - 3, bz1 - 2))
    for f in range(HF):
        y0 = FL + 5 * f
        box(xa, y0 + 1, lanes[0][0], xa + 6, y0 + 4, lanes[1][1], "air")
        lane = lanes[f % 2]
        east = f % 2 == 0
        for i in range(5):
            x = xa + 1 + i if east else xa + 5 - i
            for z in lane:
                for yy in range(y0 + 1, y0 + 1 + i):
                    put(x, yy, z, "light_gray_concrete")
                put(x, y0 + 1 + i, z, stairs("polished_andesite", "east" if east else "west"))
                if i <= 3:
                    put(x, y0 + 5, z, "air")
        # 계단실 표시등 (층마다)
        put(xa + 3, y0 + 4, lanes[1][1] + 1 if lanes[1][1] + 1 < bz1 else lanes[0][0] - 1, "sea_lantern")
    # 옥상 계단 집 (계단 구멍 둘레) — 동쪽으로 문
    hx0, hx1, hz0, hz1 = xa - 1, xa + 7, lanes[0][0] - 1, lanes[1][1] + 1
    for x in range(hx0, hx1 + 1):
        for z in range(hz0, hz1 + 1):
            edge = x in (hx0, hx1) or z in (hz0, hz1)
            for y in range(top + 1, top + 5):
                if edge:
                    put(x, y, z, "gray_concrete" if (x in (hx0, hx1) and z in (hz0, hz1)) else "cyan_stained_glass")
            put(x, top + 5, z, "gray_concrete" if edge else "sea_lantern")
    for z in lanes[0]:
        for y in range(top + 1, top + 4):
            put(hx1, y, z, "air")
    for z in (lanes[0][0] - 1, lanes[0][1] + 1):
        put(hx1 + 1, top + 4, z, LANTERN_H)
    for x in range(hx0, hx1 + 1):
        put(x, top + 6, hz0, slab("smooth_stone")); put(x, top + 6, hz1, slab("smooth_stone"))
    # 헬기장 원판
    hx, hz = bx1 - 9, bz0 + 10
    for dx in range(-9, 10):
        for dz in range(-9, 10):
            d = math.hypot(dx, dz)
            if d <= 8.4:
                put(hx + dx, top, hz + dz, "black_concrete")
                if d > 7.3:
                    put(hx + dx, top, hz + dz, "yellow_stained_glass"); put(hx + dx, top - 1, hz + dz, "ochre_froglight")
                    if int(math.degrees(math.atan2(dz, dx)) + 360) % 45 < 12:
                        put(hx + dx, top, hz + dz, "lime_stained_glass"); put(hx + dx, top - 1, hz + dz, "verdant_froglight")
            elif d <= 9.4 and (int(math.degrees(math.atan2(dz, dx)) + 360) % 30) < 8:
                put(hx + dx, top + 1, hz + dz, "end_rod[facing=up]")
    for dz in range(-4, 5):
        put(hx - 3, top, hz + dz, "white_concrete"); put(hx - 2, top, hz + dz, "white_concrete")
        put(hx + 2, top, hz + dz, "white_concrete"); put(hx + 3, top, hz + dz, "white_concrete")
    for dx in range(-1, 2):
        put(hx + dx, top, hz, "white_concrete")
    # 옥상 유리 난간 (난간 위 한 칸 더) · 모서리 빨간 경고등
    for side in "snew":
        for t in range(fwidth(side, *hb)):
            fput(side, hb, t, top + 2, "light_blue_stained_glass")
    for cx_, cz_ in ((bx0, bz0), (bx1, bz0), (bx0, bz1), (bx1, bz1)):
        put(cx_, top + 2, cz_, "gray_concrete"); put(cx_, top + 3, cz_, LAMP_ON)
    # 관제실 (북동 구석 유리 상자)
    for x in range(bx1 - 4, bx1):
        for z in range(bz0 + 1, bz0 + 4):
            edge = x in (bx1 - 4, bx1 - 1) or z in (bz0 + 1, bz0 + 3)
            for y in range(top + 1, top + 4):
                put(x, y, z, ("light_blue_stained_glass" if y > top + 1 else "gray_concrete") if edge else "air")
            put(x, top + 4, z, "gray_concrete")
    put(bx1 - 2, top + 1, bz0 + 2, "smooth_stone_slab[type=top,waterlogged=false]")
    put(bx1 - 4, top + 2, bz0 + 2, "air"); put(bx1 - 4, top + 1, bz0 + 2, "air")
    for y in range(top + 5, top + 13):
        put(bx1 - 2, y, bz0 + 2, "iron_bars[east=false,west=false,north=false,south=false,waterlogged=false]" if y < top + 12 else LAMP_ON)
    # 투광등 (남동 · 남서 구석)
    for fx_, fz_ in ((bx1 - 1, bz1 - 1), (bx0 + 9, bz1 - 1)):
        for y in range(top + 1, top + 6):
            put(fx_, y, fz_, post("andesite"))
        put(fx_, top + 6, fz_, "sea_lantern"); put(fx_, top + 7, fz_, slab("smooth_stone"))
    # 풍향 자루
    wx_, wz_ = bx1 - 1, bz0 + 6
    for y in range(top + 1, top + 6):
        put(wx_, y, wz_, CHAIN if y > top + 1 else "iron_block")
    for k, col in enumerate(("orange_wool", "white_wool", "orange_wool")):
        put(wx_ - 1 - k, top + 5, wz_, col)
    # 간판 HELI (남 · 서)
    sign("s", hb, "HELI", top - 2, "ochre_froglight", out=1)
    sign("w", hb, "HELI", top - 2, "ochre_froglight", out=1)
    # 입구 안내 표지 (남쪽 문 앞) · 헬기 자리
    mark("heli_gate", bx0 + fwidth("s", *hb) // 2 - 1, 1, bz1 + 3)
    HELI_AT.update(x=hx + 0.5, y=top + 1 - FL, z=hz + 0.5, yaw=90.0)
    import heli as _heli
    ox, oy, oz = _heli.door_offset(90.0)
    marks["escape"] = (round(float(hx + 0.5 + ox * 1.15), 2), top + 1 - FL, round(float(hz + 0.5 + oz * 1.15), 2))

    # ── (2,2) 중앙 광장 + 랜드마크 타워 (꼭대기 전망대 = 대기실)
    b = lot(2, 2)
    x0, z0, x1, z1 = b
    for x in range(x0 - SW + 1, x1 + SW):
        for z in range(z0 - SW + 1, z1 + SW):
            put(x, FL, z, "polished_diorite" if (x + z) % 4 == 0 or (x - z) % 4 == 0 else "polished_andesite")
    tb = (-6, -6, 6, 6)
    top = shell(tb, TOWER_FLOORS, "light_blue_stained_glass", "white_concrete", win="light_blue_stained_glass",
                pattern="curtain", doors=("s", "n", "e", "w"), roof=None, floor_mat="smooth_quartz")
    for f in range(0, TOWER_FLOORS, 3):
        for side in "snew":
            for t in range(-1, 14):
                fput(side, tb, t, FL + 5 * f + 5, "sea_lantern" if f % 2 else "white_concrete", 1)
    put(-5, top, -5, "white_concrete")                     # 사다리는 꼭대기 층까지 (전망대로는 못 올라감)
    wy = FL + WAIT_Y
    for y in range(top + 1, wy):
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if max(abs(dx), abs(dz)) == 3:
                    put(dx, y, dz, "white_concrete" if (y - top) % 2 else "light_blue_stained_glass")
    for dx in range(-9, 10):
        for dz in range(-9, 10):
            d = max(abs(dx), abs(dz))
            put(dx, wy, dz, "white_stained_glass" if d <= 6 else ("sea_lantern" if d == 7 else "smooth_quartz"))
            if d == 9:
                for y in range(wy + 1, wy + 4):
                    put(dx, y, dz, "glass")
                put(dx, wy + 4, dz, "sea_lantern")
    for y in range(wy + 5, wy + 13):
        put(0, y, 0, "end_rod[facing=up]" if y == wy + 12 else ("iron_block" if y < wy + 8 else CHAIN))
    mark("wait", 0, WAIT_Y + 1, 3, 180.0)
    for cx, cz in ((x0 + 2, z0 + 2), (x1 - 2, z0 + 2), (x0 + 2, z1 - 2), (x1 - 2, z1 - 2)):
        planter_tree(cx, cz)
    bench(-1, z1 - 1, "north", "x"); bench(-1, z0 + 1, "south", "x")
    bench(x1 - 1, -1, "west", "z"); bench(x0 + 1, -1, "east", "z")

    # ── 공원 2 · 입체 주차장 · 공사장
    def park(b):
        x0, z0, x1, z1 = b
        box(x0, FL, z0, x1, FL, z1, "grass_block[snowy=false]")
        mx, mz = (x0 + x1) // 2, (z0 + z1) // 2
        for x in range(x0, x1 + 1):
            put(x, FL, mz, "dirt_path"); put(x, FL, mz + 1, "dirt_path")
        for z in range(z0, z1 + 1):
            put(mx, FL, z, "dirt_path"); put(mx + 1, FL, z, "dirt_path")
        for _ in range(10):
            tx = int(rng.integers(x0 + 2, x1 - 1)); tz = int(rng.integers(z0 + 2, z1 - 1))
            if abs(tx - mx) < 4 or abs(tz - mz) < 4:
                continue
            th = int(rng.integers(4, 7))
            for y in range(FL + 1, FL + 1 + th):
                put(tx, y, tz, "oak_log[axis=y]" if chance(0.7) else "birch_log[axis=y]")
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    for dy in range(-1, 3):
                        if abs(dx) + abs(dz) + abs(dy) <= 3 and get(tx + dx, FL + th + dy, tz + dz) == "air":
                            put(tx + dx, FL + th + dy, tz + dz, LEAVES)
        for _ in range(16):
            fx = int(rng.integers(x0, x1)); fz = int(rng.integers(z0, z1))
            if get(fx, FL + 1, fz) == "air" and get(fx, FL, fz).startswith("grass"):
                put(fx, FL + 1, fz, pick(["poppy", "dandelion", "cornflower", "azure_bluet", "short_grass", "short_grass"]))
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                d = math.hypot(dx - 0.5, dz - 0.5)
                if d <= 4.2:
                    put(mx + dx, FL, mz + dz, "light_blue_stained_glass" if d < 3 else "smooth_stone")
                    put(mx + dx, FL - 1, mz + dz, "sea_lantern")
                    if d >= 3:
                        put(mx + dx, FL + 1, mz + dz, slab("smooth_stone"))
        for y in range(FL + 1, FL + 4):
            put(mx, y, mz, "quartz_pillar[axis=y]")
        put(mx, FL + 4, mz, "sea_lantern")
        for bx, bz, f in ((mx - 6, mz + 3, "east"), (mx + 7, mz - 2, "west"), (mx + 3, mz - 6, "south"), (mx - 2, mz + 7, "north")):
            put(bx, FL + 1, bz, stairs("oak", f))
        for lx, lz in ((x0 + 1, z0 + 1), (x1 - 1, z0 + 1), (x0 + 1, z1 - 1), (x1 - 1, z1 - 1)):
            for y in range(FL + 1, FL + 4):
                put(lx, y, lz, post("polished_blackstone"))
            put(lx, FL + 4, lz, LANTERN)
    park(lot(2, 1))
    park(lot(4, 3))

    b = lot(4, 2)
    x0, z0, x1, z1 = b
    OBST.append(b)
    for f in range(4):
        y0 = FL + 5 * f
        if f > 0:
            box(x0, y0, z0, x1, y0, z1, "smooth_stone")
            box(x0 + 2, y0, z0 + 2, x0 + 4, y0, z0 + 4, "air")
            for side in "snew":
                for t in range(fwidth(side, *b)):
                    fput(side, b, t, y0 + 1, slab("smooth_stone"))
        for x in range(x0, x1 + 1, 6):
            for z in range(z0, z1 + 1, 6):
                for y in range(y0 + 1, y0 + 5):
                    put(x, y, z, "light_gray_concrete")
        for k in range(3):
            if chance(0.75):
                car(x0 + 8 + k * 6, z1 - 6, pick(car_cols), "z")
        for y in range(y0 + 1, y0 + 6 if f < 3 else y0 + 6):
            put(x0 + 3, y, z0 + 3, ladder("south"))
    box(x0, FL + 20, z0, x1, FL + 20, z1, "smooth_stone")
    put(x0 + 3, FL + 20, z0 + 3, ladder("south"))
    for t in range(fwidth("w", *b)):
        for y in range(FL + 14, FL + 20):
            if 3 <= t <= 17:
                fput("w", b, t, y, "blue_concrete", 0)
    sign("w", b, "PARK", FL + 19, "sea_lantern", out=1)

    b = lot(0, 3)
    x0, z0, x1, z1 = b
    OBST.append(b)
    box(x0, FL, z0, x1, FL, z1, "coarse_dirt")
    for x in range(x0 + 2, x1 - 1, 5):
        for z in range(z0 + 2, z1 - 1, 5):
            for y in range(FL + 1, FL + 16):
                put(x, y, z, "iron_block" if (y - FL) % 5 == 0 else "stripped_oak_log[axis=y]")
    for y in (FL + 5, FL + 10, FL + 15):
        for x in range(x0 + 2, x1 - 1):
            for z in range(z0 + 2, z1 - 1):
                if (x - x0) % 5 == 2 or (z - z0) % 5 == 2 or chance(0.55):
                    put(x, y, z, "oak_planks" if y < FL + 15 else "iron_block")
    for y in range(FL + 1, FL + 15):
        put(x0 + 3, y, z0 + 1, ladder("south"))
    for y in range(FL + 1, FL + 28):
        put(x1 - 3, y, z1 - 3, "yellow_concrete" if y % 2 else "black_concrete")
    for x in range(x0 - 4, x1):
        put(x, FL + 28, z1 - 3, "yellow_concrete")
    for y in range(FL + 20, FL + 28):
        put(x0 + 4, y, z1 - 3, CHAIN)
    box(x0 + 3, FL + 18, z1 - 4, x0 + 5, FL + 19, z1 - 2, "orange_concrete")
    box(x1 - 6, FL + 1, z0 + 1, x1 - 1, FL + 2, z0 + 3, "orange_concrete")
    for t in range(0, x1 - x0, 2):
        put(x0 + t, FL + 1, z1, "orange_concrete" if t % 4 == 0 else "white_concrete")

    def pocket_park(b):
        """작은 쌈지 공원: 잔디 · 돌길 · 나무 2 · 벤치 · 가로등"""
        x0, z0, x1, z1 = b
        box(x0, FL, z0, x1, FL, z1, "grass_block[snowy=false]")
        mx, mz = (x0 + x1) // 2, (z0 + z1) // 2
        for x in range(x0, x1 + 1):
            put(x, FL, mz, "polished_andesite")
        for z in range(z0, z1 + 1):
            put(mx, FL, z, "polished_andesite")
        for tx, tz in ((x0 + 2, z0 + 2), (x1 - 2, z1 - 2)):
            th = 5
            for y in range(FL + 1, FL + 1 + th):
                put(tx, y, tz, "oak_log[axis=y]")
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    for dy in range(-1, 3):
                        if abs(dx) + abs(dz) + abs(dy) <= 3 and get(tx + dx, FL + th + dy, tz + dz) == "air":
                            put(tx + dx, FL + th + dy, tz + dz, LEAVES)
        put(mx + 2, FL + 1, mz + 2, stairs("oak", "north")); put(mx + 3, FL + 1, mz + 2, stairs("oak", "north"))
        put(mx - 2, FL + 1, mz - 2, stairs("oak", "south")); put(mx - 3, FL + 1, mz - 2, stairs("oak", "south"))
        for y in range(FL + 1, FL + 4):
            put(x1 - 1, y, z0 + 1, post("polished_blackstone"))
        put(x1 - 1, FL + 4, z0 + 1, LANTERN)
        for _ in range(8):
            fx = int(rng.integers(x0, x1 + 1)); fz = int(rng.integers(z0, z1 + 1))
            if get(fx, FL + 1, fz) == "air" and get(fx, FL, fz).startswith("grass"):
                put(fx, FL + 1, fz, pick(["poppy", "dandelion", "cornflower", "short_grass"]))

    # ── 나머지 구역: 사무실 · 아파트 · 상가 (모양 섞기)
    styles = [
        dict(wall="light_gray_concrete", trim="gray_concrete", win="light_blue_stained_glass", pattern="curtain"),
        dict(wall="bricks", trim="stone_bricks", win="glass", pattern="grid", sill="stone_brick", balc=True, fire=True),
        dict(wall="white_terracotta", trim="smooth_quartz", win="glass", pattern="grid", sill="smooth_quartz", balc=True),
        dict(wall="dark_prismarine", trim="polished_blackstone", win="cyan_stained_glass", pattern="curtain"),
        dict(wall="terracotta", trim="bricks", win="glass", pattern="small", sill="brick", fire=True),
        dict(wall="black_concrete", trim="gray_concrete", win="light_blue_stained_glass", pattern="band"),
        dict(wall="mud_bricks", trim="bricks", win="glass", pattern="grid", sill="mud_brick", balc=True),
        dict(wall="white_concrete", trim="light_gray_concrete", win="glass", pattern="band", shop=True),
    ]
    rest = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 1), (0, 2), (1, 2), (3, 2), (1, 4), (3, 4), (4, 4)]
    awn = [("red_wool", "white_wool"), ("blue_wool", "white_wool"), ("green_wool", "white_wool"),
           ("orange_wool", "yellow_wool"), ("purple_wool", "white_wool")]
    for k, (i, j) in enumerate(rest):
        b = lot(i, j)
        layout = [(2, 2), (2, 1), (1, 2), (2, 2), (1, 1)][k % 5]
        road_edges = {"w": i > 0, "e": i < len(LOTS) - 1, "n": j > 0, "s": j < len(LOTS) - 1}
        for n, pb in enumerate(split(b, *layout)):
            touch = {"w": pb[0] == b[0], "e": pb[2] == b[2], "n": pb[1] == b[1], "s": pb[3] == b[3]}
            street = [d for d in "snew" if touch[d] and road_edges[d]]
            if not street:
                pocket_park(pb)                  # 길에 안 닿는 안쪽 조각 = 쌈지 공원 (문이 골목 벽만 보는 건물 X)
                continue
            stl = styles[(k * 3 + n) % len(styles)]
            fl = int(rng.integers(2, 7)) if stl["pattern"] != "curtain" else int(rng.integers(4, 9))
            if pb[2] - pb[0] < 8 or pb[3] - pb[1] < 8:
                dumpsters(pb)
                continue
            ds = tuple(street[:2]) if len(street) >= 2 else (street[0],)
            shop = stl.get("shop") or (n % 3 == 0 and stl["pattern"] != "curtain")
            shell(pb, fl, stl["wall"], stl["trim"], win=stl["win"], pattern=stl["pattern"], doors=ds,
                  ground="shop" if shop else None, sill=stl.get("sill"))
            if stl.get("balc") and fl >= 3:
                balconies(ds[0], pb, fl)
            if stl.get("fire") and fl >= 3:
                fire_escape(("e", "w", "n", "s")[n % 4], pb, fl)
            if shop:
                awning(ds[0], pb, pick(awn))
                neon_strip(ds[0], pb, FL + 6, pick(["pink_stained_glass", "light_blue_stained_glass", "yellow_stained_glass",
                                                    "lime_stained_glass"]),
                           pick(["pearlescent_froglight", "sea_lantern", "ochre_froglight"]), 2, fwidth(ds[0], *pb) - 3)

    # ── 둘레 담 · 보이지 않는 벽 · 바깥 스카이라인 (불 켜진 창이 있는 고층 빌딩 — 끝없는 도시처럼)
    edge = city & ~((np.abs(xx) <= E - 1) & (np.abs(zz) <= E - 1))
    for y in (FL + 1, FL + 2, FL + 3):
        v[:, y, :][edge] = pid("stone_bricks")
    v[:, FL + 4, :][edge] = pid(slab("stone_brick"))
    outer = (np.abs(xx) <= E + 1) & (np.abs(zz) <= E + 1) & ~city
    for y in range(FL + 1, FL + 44):
        v[:, y, :][outer] = pid("barrier")
    lit_cols = ["ochre_froglight", "ochre_froglight", "sea_lantern", "pearlescent_froglight"]
    for side in range(4):
        t = -E - SKY
        while t < E + SKY:
            w = int(rng.integers(7, 15))
            hgt = int(rng.integers(18, 64))
            d = int(rng.integers(6, SKY + 1))
            wall = pick(["gray_concrete", "black_concrete", "blue_terracotta", "light_gray_concrete", "cyan_terracotta",
                         "brown_terracotta", "deepslate_tiles"])
            for a in range(t, min(t + w, E + SKY + 1)):
                for bdep in range(E + 3, E + 3 + d):
                    x, z = ((a, -bdep), (a, bdep), (-bdep, a), (bdep, a))[side]
                    front = bdep == E + 3
                    for y in range(FL + 1, FL + hgt):
                        blk = wall
                        if front and (y - FL) % 4 in (1, 2) and (a - t) % 3 != 0 and 0 < a - t < w - 1:
                            blk = pick(lit_cols) if chance(0.33) else "black_stained_glass"
                        put(x, y, z, blk)
                    put(x, FL + hgt, z, "light_gray_concrete" if front else "gray_concrete")
            if chance(0.5):
                mid = t + w // 2
                dd = E + 3 + d // 2
                x, z = ((mid, -dd), (mid, dd), (-dd, mid), (dd, mid))[side]
                for y in range(FL + hgt + 1, FL + hgt + 6):
                    put(x, y, z, CHAIN)
                put(x, FL + hgt + 6, z, LAMP_ON)
            t += w + int(rng.integers(0, 3))

    # ── 문 정하기: 문 앞 (문 폭 + 양옆 1칸 · 바깥 6칸) 에 다른 건물 · 주차장 · 공사장이 있으면 트인 면으로 옮기고 뚫음
    blocks_ = [tuple(e[0]) for e in BLDG] + OBST

    def door_lane(b, d):
        w = fwidth(d, *b)
        m = w // 2 - 1
        return m, [fxz(d, *b, t, out) for t in range(m - 1, m + 3) for out in range(1, 7)]

    def lane_blocked(b, d):
        _, cells = door_lane(b, d)
        for ob in blocks_:
            if ob == tuple(b):
                continue
            if any(ob[0] <= x <= ob[2] and ob[1] <= z <= ob[3] for x, z in cells):
                return True
        return any(abs(x) >= E - 1 or abs(z) >= E - 1 for x, z in cells[:4])

    for e in BLDG:
        b, floors, doors = e
        final = []
        for d in doors:
            if not lane_blocked(b, d):
                final.append(d)
                continue
            for alt in ("s", "n", "e", "w"):
                if alt not in final and alt not in doors and not lane_blocked(b, alt):
                    final.append(alt)
                    break
            else:
                final.append(d)
        e[2] = tuple(dict.fromkeys(final))
        for d in e[2]:
            m, _ = door_lane(b, d)
            DOORS.append((d, tuple(b), m))
            for dy in range(1, 4):
                for t in (m, m + 1):
                    fput(d, b, t, FL + dy, "air")
            for t in range(m - 1, m + 3):
                if fget(d, b, t, FL + 4, 1) == "air":
                    fput(d, b, t, FL + 4, slab("smooth_stone", "top"), 1)
            for t in (m - 1, m + 2):
                if fget(d, b, t, FL + 3, 1) == "air":
                    fput(d, b, t, FL + 3, LANTERN_H, 1)

    # ── 문 앞길 (문 폭 + 양옆 1칸 · 바깥 7칸) 에 걸친 거리 시설은 통째로 치움 (버스 정류장 · 가로등 · 나무 · 차 · 쓰레기통 …)
    lane_cells = set()
    for d, b, m in DOORS:
        for t in range(m - 1, m + 3):
            for out in range(1, 8):
                x, z = fxz(d, *b, t, out)
                lane_cells.add((C + x, C + z))
    removed = 0
    for cells in PROPS:
        if any((gx, gz) in lane_cells and FL < y <= FL + 5 for gx, y, gz, _ in cells):
            removed += 1
            for gx, y, gz, p_ in cells:
                if y > FL and v[gx, y, gz] == p_:
                    v[gx, y, gz] = 0
    STATS["props_removed"] = removed

    # ── 문 앞뒤 비우기 (모든 건물을 다 지은 뒤 — 나중에 놓인 가로등 · 소화전 · 쓰레기통 · 차 · 기둥 · 가구가 문을 막지 않게)
    #   문 두 칸 줄: 바깥 1~3칸 (인도) 발 · 머리 · 그 위 1칸, 안쪽 1~3칸 발 · 머리 · 그 위 1칸
    #   바깥 2~3칸은 머리 위 높은 곳(가로등 갓 · 나무 잎)도 같이 (떠 있는 조각이 남지 않게)
    for d, b, m in DOORS:
        for t in (m, m + 1):
            for out in (1, 2, 3, -1, -2, -3):
                x, z = fxz(d, *b, t, out)
                for y in range(FL + 1, FL + 4):
                    nm = get(x, y, z)
                    if nm != "air" and "ladder" not in nm:
                        put(x, y, z, "air")
                if out >= 2:
                    for y in range(FL + 4, FL + 10):
                        nm = get(x, y, z)
                        if any(k in nm for k in ("wall[", "lantern", "chain", "lamp", "leaves", "_log", "_bars")):
                            put(x, y, z, "air")
                # 발밑: 땅이 비었거나 낮으면 메움 (계단 · 반 블록은 그대로)
                if get(x, FL, z) == "air":
                    put(x, FL, z, "polished_andesite")

    # ── 도둑 시작 자리 12 (도로 위 · 흩어지게)
    starts = [(-80, -57), (-40, -57), (0, -57), (40, -57), (80, -57), (-57, -80), (-57, 40), (57, -40),
              (-17, 80), (17, 40), (-80, 17), (80, 17)]
    for i, (x, z) in enumerate(starts):
        mark(f"thief_{i}", x, 1, z)
    return v, marks


def markers():
    return build()[1]


def heist_names():
    m = markers()
    return [m[f"heistname_{i}"] for i in range(6)]


def commands(greedy_boxes):
    v, _ = build()
    cmds = []
    for p, x0, y0, z0, x1, y1, z1 in greedy_boxes(v):
        st = "minecraft:" + PAL[p]
        a = f"~{x0 - C} ~{y0 - FL} ~{z0 - C}"
        if (x0, y0, z0) == (x1, y1, z1):
            cmds.append(f"$execute positioned $(x) $(y) $(z) run setblock {a} {st}")
        else:
            cmds.append(f"$execute positioned $(x) $(y) $(z) run fill {a} ~{x1 - C} ~{y1 - FL} ~{z1 - C} {st}")
    return cmds


def display_commands():
    """블록 디스플레이 (헬기) 소환 — 데이터팩 마지막 조각에서 (예전 것은 지우고)"""
    import heli
    if not HELI_AT:
        build()
    at = "$execute positioned $(x) $(y) $(z) run summon"
    h = HELI_AT
    out = ["kill @e[type=block_display,tag=kd_heli]"]
    out += heli.summon_all(at, h["x"], h["y"], h["z"], h["yaw"], ['"kd_heli"'])
    return out


def forceload_range():
    return (-C, -C, N - 1 - C, N - 1 - C)


SHOTS = [
    ((92, 125, 92), (0, 0, 0), 60, "경찰과 도둑 — 밤 대도시 전체 (4차선 도로 · 구역 25 · 바깥 스카이라인)"),
    ((57, 4, -50), (80, 26, -80), 78, "헬기장 타워 (북동) — 7층 35칸 · HELI 간판 · 남쪽 · 서쪽 입구"),
    ((93, 50, -62), (83, 36, -84), 66, "타워 옥상 — 헬기장 (흰 H · 빛 테두리) · 탈출 헬기 · 계단 집 · 관제실 · 투광등 · 풍향 자루"),
    ((77, 39.5, -89.5), (85.5, 38, -81.5), 70, "탈출 헬기 가까이 (블록 디스플레이 · 로터는 실제로 돎)"),
    ((0.5, 3, 42), (0.5, 16, -20), 85, "거리에서 — 중앙 광장 · 랜드마크 타워 (꼭대기 전망대 = 대기실)"),
    ((-18, 7, -17), (-40, 12, -40), 75, "은행 (기둥 현관 · BANK) — 문 앞 기둥 비움"),
    ((18, 7, -17), (40, 14, -40), 75, "카지노 (네온 · 전구 · CASINO)"),
    ((-58, 9, 58), (-76, 10, 78), 75, "경찰서 (POLICE) · 경찰차 · 감옥"),
    ((-40, 6, 18), (-40, 12, 40), 75, "박물관 (기둥 현관 · 유리 돔 · MUSEUM)"),
    ((18, 6, 18), (34, 8, 34), 75, "보석상 (GEMS) · 상가 · 줄무늬 차양"),
    ((-62, 6, -38), (-84, 8, -44), 75, "창고 (하역장 · 컨테이너)"),
    ((-7, 6, 58), (-7, 8, 72), 75, "편의점 (24/7) · 아파트 · 유리 빌딩"),
    ((62, 8, 18), (80, 10, 2), 75, "입체 주차장 (PARK) · 공원"),
    ((-60, 8, 2), (-80, 12, 18), 75, "공사장 · 크레인"),
]


def _shot(args):
    i, cam, tgt, fov, lab = args
    import render as R
    import hubgen
    import bdkit
    import heli
    from PIL import ImageDraw, ImageFont
    v, marks = build()
    v2 = np.where(v == P.get("barrier", -1), 0, v)
    pal = R.Palette(PAL)
    sun = np.array(hubgen.NIGHT["sun"], float); sun /= np.linalg.norm(sun)
    mesh = R.Mesh()
    h = HELI_AT
    o = np.array([C + h["x"], FL + h["y"], C + h["z"]])
    bdkit.add_to_mesh(mesh, heli.body(), o, h["yaw"], 1.0, sun)
    mx, my, mz = bdkit._ry(-h["yaw"]) @ (np.array(heli.MAST) / 16)
    bdkit.add_to_mesh(mesh, heli.main_rotor(), o + np.array([mx, my, mz]), h["yaw"] + 20, 1.0, sun)
    W, Hh = 1000, 560
    c = (C + cam[0], FL + cam[1], C + cam[2]); t = (C + tgt[0], FL + tgt[1], C + tgt[2])
    im = R.render(v2, pal, W, Hh, c, t, fov=fov, ss=2, fog_dist=900, mesh=mesh, **hubgen.NIGHT)
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
    d.rectangle((0, 0, W, 40), fill=(4, 12, 28))
    d.text((14, 6), lab, font=font, fill=(140, 220, 255))
    return i, im


def preview(path, only=None):
    from multiprocessing import Pool
    from PIL import Image
    jobs = [(i,) + s for i, s in enumerate(SHOTS) if only is None or i in only]
    with Pool(4) as pool:
        res = dict(pool.map(_shot, jobs))
    W, Hh = 1000, 560
    out = Image.new("RGB", (W, Hh * len(res)))
    for k, i in enumerate(sorted(res)):
        out.paste(res[i], (0, Hh * k))
    out.save(path)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    preview(sys.argv[1] if len(sys.argv) > 1 else "cops.png")
