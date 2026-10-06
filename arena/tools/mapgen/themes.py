"""맵 테마 — 같은 전장 구조 (본진 4 · 대신전 · 제단 4 · 투기장 4 · 대기실) 위에 지형 · 블록 · 풍경을 바꾼다

 olympus  올림포스 (기본 맵, 그대로)
 frost    빙하 왕국 니플헤임 — 높은 설산 · 눈 덮인 대지 · 얼어붙은 강 · 거대한 얼음 첨탑 · 침엽수
 volcano  화산 군도 타르타로스 — 현무암 대지 · 용암 강 · 가장자리 화산 네 개 (분화구 용암) · 진홍 균사 나무 · 현무암 기둥

 흐름 (build_map.generate):
   Terrain(seed, theme) — 언덕 · 산 높이 배율 + terrain_post (강 · 화산 · 호수 파기)
   … 구조물 …
   world_post(w, T, theme) — 블록 바꾸기 + 눈 덮기 / 용암 + 풍경 (얼음 첨탑 · 현무암 기둥)
"""
import math

import numpy as np
from scipy import ndimage

import blocks as B
from layout import *
from noise import fbm, value_noise, smoothstep

S = SIZE

THEMES = {
    "olympus": {"name": "올림포스", "seed": 7, "hill": 1.0, "peak": 0},
    "frost": {"name": "빙하 왕국", "seed": 23, "hill": 1.35, "peak": 12},
    "volcano": {"name": "화산 군도", "seed": 41, "hill": 1.25, "peak": 6},
}

RIVER_L = G - 1          # 강 수면 (용암 · 얼음) — 어디서나 같은 높이라 흐르지 않는다


# ═════════════════════════════════════════════ 지형 (Terrain 이 부름)
def terrain_post(T, theme):
    if theme == "olympus":
        return
    T.lava_cells = np.zeros((S, S), bool)
    _rivers(T, theme)
    if theme == "volcano":
        _volcanoes(T)
    if theme == "frost":
        _frozen_lakes(T)


def _free(T, margin=0.12):
    """구조물 · 길 · 물에서 떨어진 빈 땅"""
    return (T.feature < margin) & (T.road <= 0.01) & (T.water < 0) & (T.zone == "")


def _rivers(T, theme):
    """노이즈 등고선을 따라 굽이치는 강 — 수면 RIVER_L 고정 (둑이 수면보다 높은 곳만 판다)"""
    n = fbm(S, T.seed + 77, ((40, 1.0), (20, 0.4)))
    band = np.abs(n) < (0.035 if theme == "volcano" else 0.03)
    free = _free(T, 0.08)
    m = band & free & (T.H >= RIVER_L + 1.0) & (T.H <= RIVER_L + 5.5)
    # 경계 산맥 · 맵 가장자리 제외
    edge = np.maximum(np.abs(T.X - C[0]), np.abs(T.Z - C[1]))
    m &= edge < 108
    m = ndimage.binary_opening(m, iterations=1)
    # 둑: 강 칸 옆 칸은 모두 수면보다 높아야 (넘쳐흐르지 않게)
    for _ in range(3):
        ring = ndimage.binary_dilation(m) & ~m
        bad = ring & ((T.H < RIVER_L + 0.6) | (T.water >= 0) | (T.road > 0.01))
        if not bad.any():
            break
        m &= ~ndimage.binary_dilation(bad)
    T.H = np.where(m, RIVER_L - 2, T.H)
    T.water = np.where(m, RIVER_L, T.water)
    T.no_veg |= ndimage.binary_dilation(m, iterations=2)
    T.river = m
    if theme == "volcano":
        T.lava_cells |= m


def _volcanoes(T):
    """가장자리 산맥 속 화산 네 개 (본진 뒤 대각) — 꼭대기 분화구에 용암"""
    spots = [(48, 8), (247, 48), (208, 247), (8, 208)]
    for i, (cx, cz) in enumerate(spots):
        d = np.hypot(T.X - cx, T.Z - cz)
        R = 30.0
        top = G + 44 + i % 2 * 4
        cone = np.clip(1 - d / R, 0, 1) ** 1.25
        rug = fbm(S, T.seed + 90 + i, ((8, 1.0), (4, 0.4))) * 2.5
        h = G + 4 + (top - G - 4) * cone + rug * cone
        T.H = np.where(d < R, np.maximum(T.H, h), T.H)
        crater = d < 5.5
        lip = top - 2
        T.H = np.where((d >= 5.5) & (d < 8), np.maximum(T.H, lip), T.H)
        T.H = np.where(crater, lip - 3, T.H)
        T.water = np.where(crater, lip - 1, T.water)
        T.lava_cells |= crater
        T.no_veg |= d < R
        T.zone[(d < R) & (T.zone == "")] = "volcano"


def _frozen_lakes(T):
    """빈 땅 군데군데 얼어붙은 호수"""
    r = np.random.default_rng(T.seed + 55)
    free = _free(T, 0.05)
    edge = np.maximum(np.abs(T.X - C[0]), np.abs(T.Z - C[1]))
    made = 0
    for _ in range(400):
        if made >= 5:
            break
        x, z = int(r.integers(20, S - 20)), int(r.integers(20, S - 20))
        if edge[x, z] > 100 or not free[x, z]:
            continue
        rad = r.uniform(5, 8.5)
        d = np.hypot(T.X - x, T.Z - z)
        wob = value_noise(S, 5, int(r.integers(1e6))) * 2.4
        lake = d < rad + wob - 1.2
        ring = (d < rad + wob + 2.5) & ~lake
        if not free[lake].all() or (T.H[ring] < RIVER_L + 0.6).any():
            continue
        T.H = np.where(lake, RIVER_L - 2, T.H)
        T.water = np.where(lake, RIVER_L, T.water)
        T.no_veg |= ring | lake
        made += 1


# ═════════════════════════════════════════════ 블록 바꾸기
#   "새이름"   = 속성 그대로 · "새이름!" = 속성 지움 · [(블록, 무게), …] = 칸마다 군락 노이즈로 고름
FROST = {
    "grass_block": "grass_block[snowy=true]", "moss_block": "snow_block", "rooted_dirt": "snow_block", "podzol": "snow_block",
    "oak_leaves": "spruce_leaves", "birch_leaves": "spruce_leaves", "azalea_leaves": "spruce_leaves", "jungle_leaves": "spruce_leaves",
    "dark_oak_leaves": "spruce_leaves", "flowering_azalea_leaves": "spruce_leaves",
    "oak_log": "spruce_log", "birch_log": "stripped_birch_log", "jungle_log": "spruce_log", "dark_oak_log": "spruce_log", "oak_wood": "spruce_wood",
    "stripped_dark_oak_log": "stripped_spruce_log", "oak_planks": "spruce_planks", "oak_slab": "spruce_slab", "oak_fence": "spruce_fence",
    "dark_oak_fence": "spruce_fence", "birch_fence": "spruce_fence",
    "sand": "snow_block", "sandstone": "calcite!", "smooth_sandstone": "smooth_quartz", "cut_sandstone": "quartz_bricks",
    "chiseled_sandstone": "chiseled_quartz_block", "sandstone_slab": "quartz_slab", "smooth_sandstone_slab": "smooth_quartz_slab",
    "cut_red_sandstone": "quartz_bricks",
    "terracotta": "packed_ice", "brown_terracotta": "blue_ice", "red_terracotta": "snow_block", "packed_mud": "snow_block",
    "yellow_terracotta": "light_blue_terracotta",
    "tuff": "deepslate[axis=y]",
    "short_grass": "air", "fern": "air", "bush": "air", "poppy": "air", "oxeye_daisy": "air", "azure_bluet": "air", "cornflower": "air",
    "allium": "air", "dandelion": "air", "pink_petals": "air", "lily_of_the_valley": "air", "orange_tulip": "air", "pink_tulip": "air",
    "red_tulip": "air", "dead_bush": "air", "lily_pad": "air", "wheat": "air",
    "farmland": "snow_block!",
}
VOLCANO = {
    "grass_block": [("blackstone", 46), ("smooth_basalt", 22), ("tuff", 14), ("netherrack", 10), ("magma_block", 3), ("crimson_nylium", 5)],
    "moss_block": [("crimson_nylium", 70), ("netherrack", 30)],
    "rooted_dirt": "soul_soil!", "podzol": "soul_soil!", "dirt": "blackstone!", "coarse_dirt": "coarse_dirt", "dirt_path": "soul_soil!",
    "farmland": "soul_soil!",
    "stone": [("blackstone", 55), ("basalt[axis=y]", 30), ("deepslate[axis=y]", 15)],
    "andesite": "basalt[axis=y]", "tuff": "smooth_basalt", "calcite": "calcite", "diorite": "smooth_basalt",
    "cobblestone": "cobbled_deepslate", "mossy_cobblestone": "blackstone", "cobblestone_slab": "cobbled_deepslate_slab",
    "cobblestone_wall": "cobbled_deepslate_wall",
    "stone_bricks": "polished_blackstone_bricks", "mossy_stone_bricks": "cracked_polished_blackstone_bricks",
    "cracked_stone_bricks": "cracked_polished_blackstone_bricks", "chiseled_stone_bricks": "chiseled_polished_blackstone",
    "stone_brick_stairs": "polished_blackstone_brick_stairs", "mossy_stone_brick_stairs": "polished_blackstone_brick_stairs",
    "stone_brick_slab": "polished_blackstone_brick_slab", "mossy_stone_brick_slab": "polished_blackstone_brick_slab",
    "stone_brick_wall": "polished_blackstone_brick_wall",
    "polished_andesite": "polished_blackstone", "polished_andesite_slab": "polished_blackstone_slab",
    "polished_andesite_stairs": "polished_blackstone_stairs", "andesite_slab": "blackstone_slab",
    "smooth_stone": "polished_deepslate", "smooth_stone_slab": "polished_deepslate_slab", "stone_slab": "polished_deepslate_slab",
    "sand": "red_sand", "sandstone": "red_sandstone", "smooth_sandstone": "smooth_red_sandstone", "cut_sandstone": "cut_red_sandstone",
    "chiseled_sandstone": "chiseled_red_sandstone", "sandstone_slab": "red_sandstone_slab", "smooth_sandstone_slab": "smooth_red_sandstone_slab",
    "oak_leaves": "nether_wart_block!", "birch_leaves": "nether_wart_block!", "azalea_leaves": "nether_wart_block!",
    "jungle_leaves": "nether_wart_block!", "flowering_azalea_leaves": "shroomlight!",
    "dark_oak_leaves": "warped_wart_block!", "spruce_leaves": "warped_wart_block!",
    "oak_log": "crimson_stem", "birch_log": "crimson_stem", "jungle_log": "crimson_stem", "oak_wood": "crimson_hyphae",
    "dark_oak_log": "warped_stem", "spruce_log": "warped_stem", "stripped_spruce_log": "stripped_warped_stem",
    "stripped_dark_oak_log": "stripped_warped_stem",
    "spruce_planks": "crimson_planks", "oak_planks": "crimson_planks", "spruce_stairs": "crimson_stairs", "spruce_slab": "crimson_slab",
    "oak_slab": "crimson_slab", "spruce_fence": "crimson_fence", "oak_fence": "crimson_fence", "dark_oak_fence": "warped_fence",
    "birch_fence": "crimson_fence",
    "short_grass": "air", "fern": "air", "bush": "air", "poppy": "air", "oxeye_daisy": "air", "azure_bluet": "air", "cornflower": "air",
    "allium": "air", "dandelion": "air", "pink_petals": "air", "lily_of_the_valley": "air", "orange_tulip": "air", "pink_tulip": "air",
    "red_tulip": "air", "dead_bush": "air", "lily_pad": "air", "wheat": "air", "hay_block": "shroomlight!",
    "clay": "magma_block!",
}
REMAP = {"frost": FROST, "volcano": VOLCANO}

# 바뀐 블록이 원래 블록에 없는 속성을 원할 때 기본값
NEED_AXIS = {"basalt", "deepslate", "polished_basalt"}


def _fam(bid):
    for f in ("_stairs", "_slab", "_wall", "_fence", "_leaves"):
        if bid.endswith(f):
            return f
    if bid.endswith(("_log", "_stem", "_wood", "_hyphae")) or bid in ("basalt", "polished_basalt", "deepslate"):
        return "axis"
    return None


def _target(state, rule):
    """속성은 같은 모양 무리 (계단 · 반 블록 · 담 · 울타리 · 잎 · 통나무) 끼리만 넘긴다"""
    if rule.endswith("!"):
        return rule[:-1]
    sb, sp = B.parse(state)
    nb, np_ = B.parse(rule)
    out = dict(sp) if (_fam(sb) is not None and _fam(sb) == _fam(nb)) else {}
    out.update(np_)
    if nb in NEED_AXIS and "axis" not in out:
        out["axis"] = "y"
    return B.fmt(nb, out)


def remap(w, T, theme):
    table = REMAP.get(theme)
    if not table:
        return
    na = value_noise(S, 6, T.seed + 301)
    nb = value_noise(S, 17, T.seed + 302)
    lut = np.arange(len(w.pal), dtype=np.int64)
    variants = {}
    for pid, st in enumerate(list(w.pal)):
        bid = B.parse(st)[0]
        rule = table.get(bid)
        if rule is None:
            continue
        if isinstance(rule, list):
            variants[pid] = rule
            continue
        lut[pid] = w.id(_target(st, rule)) if rule != "air" else 0
    w.vox = lut[w.vox].astype(np.uint16)
    # 군락 노이즈 고르기 (같은 블록끼리 뭉치게)
    for pid, rule in variants.items():
        xs, ys, zs = np.nonzero(w.vox == pid)
        if not len(xs):
            continue
        k = (na[xs, zs] * 0.65 + nb[xs, zs] * 0.35 + ((ys * 7 + xs * 3) % 5) * 0.01)
        k = (k - k.min()) / (k.max() - k.min() + 1e-6)
        tot = sum(wt for _, wt in rule)
        acc = 0.0
        ids = np.zeros(len(xs), np.uint16)
        for blk, wt in rule:
            lo, acc = acc, acc + wt / tot
            sel = (k >= lo) & (k <= acc + 1e-9)
            ids[sel] = w.id(_target(w.pal[pid], blk))
        w.vox[xs, ys, zs] = ids


# ═════════════════════════════════════════════ 물 → 얼음 · 용암
def fluids(w, T, theme):
    wid = w.pid.get("water")
    if wid is None:
        return
    if theme == "volcano":
        lava = w.id("lava")
        # 헤르메스 협곡 (떨어지는 곳) · 보스 투기장 안 오아시스는 물 그대로
        keep = (T.zone == "hermes") | np.vectorize(lambda z_: str(z_).startswith("lair_"))(T.zone)
        xs, ys, zs = np.nonzero(w.vox == wid)
        sel = ~keep[xs, zs]
        w.vox[xs[sel], ys[sel], zs[sel]] = lava
        print(f"[theme] 물 → 용암 {int(sel.sum())}칸 (헤르메스 협곡 · 투기장은 물 그대로)")
    if theme == "frost":
        ice = w.id("ice")
        river = getattr(T, "river", np.zeros((S, S), bool))
        froze = 0
        for x in range(S):
            for z in range(S):
                wl = T.water[x, z]
                if wl < 0:
                    continue
                if w.vox[x, wl, z] != wid:
                    continue
                # 강 · 호수 · 데메테르 연못은 꽁꽁 · 해자는 얼음 조각만 둥둥 · 헤르메스 협곡은 그대로
                zn = T.zone[x, z]
                if river[x, z] or zn == "demeter" or (zn == "" and T.water[x, z] == RIVER_L):
                    w.vox[x, wl, z] = ice; froze += 1
                elif zn == "plaza" and ((x * 7 + z * 13) % 11) < 3:
                    w.vox[x, wl, z] = ice; froze += 1
        print(f"[theme] 얼음 {froze}칸")


# ═════════════════════════════════════════════ 눈 덮기
SNOW_ON = ("grass_block", "snow_block", "stone", "andesite", "dirt", "coarse_dirt", "gravel", "spruce_leaves", "calcite", "deepslate",
           "packed_ice", "cobblestone", "mossy_cobblestone", "diorite", "tuff", "podzol", "rooted_dirt", "moss_block")


def snow(w, T):
    lay = w.id("snow[layers=1]")
    lay2 = w.id("snow[layers=2]")
    sb = w.id("snow_block")
    ok = np.zeros(len(w.pal), bool)
    for i, st in enumerate(w.pal):
        if B.parse(st)[0] in SNOW_ON:
            ok[i] = True
    X, Y, Z = w.vox.shape
    n = value_noise(S, 9, T.seed + 400)
    bar = w.pid.get("barrier", -1)
    cnt = 0
    for x in range(X):
        for z in range(Z):
            col = w.vox[x, :, z]
            nz = np.nonzero((col != 0) & (col != bar))[0]      # 높이 69 천장(배리어)은 건너뜀
            if not len(nz):
                continue
            top = int(nz[-1])
            if top + 1 >= Y or not ok[col[top]]:
                continue
            if T.road[x, z] > 0.5:
                continue
            # 높은 산 = 만년설 (윗면 두 칸 눈 블록 + 비탈도 하얗게)
            if top > G + 13 and T.zone[x, z] in ("", "volcano"):
                for yy in range(max(0, top - 3), top + 1):
                    if ok[w.vox[x, yy, z]]:
                        w.vox[x, yy, z] = sb
            w.vox[x, top + 1, z] = lay2 if n[x, z] > 0.62 else lay
            cnt += 1
    print(f"[theme] 눈 {cnt}칸")


# ═════════════════════════════════════════════ 풍경
def _spot_ok(T, x, z, margin=0.06):
    return 0 <= x < S and 0 <= z < S and T.feature[x, z] < margin and T.road[x, z] <= 0.01 and T.water[x, z] < 0 and \
        T.zone[x, z] in ("", "volcano") and not T.no_veg[x, z]


def ice_spires(w, T, n=26):
    """거대한 얼음 첨탑 (꽁꽁 언 기둥 · 옆으로 뻗은 얼음 가시)"""
    r = np.random.default_rng(T.seed + 501)
    made, spots = 0, []
    for _ in range(3000):
        if made >= n:
            break
        x, z = int(r.integers(10, S - 10)), int(r.integers(10, S - 10))
        if not _spot_ok(T, x, z) or any((x - a) ** 2 + (z - b) ** 2 < 15 ** 2 for a, b in spots):
            continue
        gy = int(T.Hi[x, z])
        h = int(r.integers(9, 22))
        rad = r.uniform(1.6, 2.8)
        for dy in range(-2, h):
            t = max(0.0, dy) / h
            rr = rad * (1 - t) ** 0.9 + 0.3
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    if dx * dx + dz * dz <= rr * rr:
                        blk = "blue_ice" if (dx * dx + dz * dz) < (rr * 0.45) ** 2 else "packed_ice"
                        w.set(x + dx, gy + dy, z + dz, blk)
        # 옆 가시 2~3개
        for k in range(int(r.integers(2, 4))):
            a = r.uniform(0, 6.28)
            y0 = gy + int(r.integers(1, max(2, h // 2)))
            L = int(r.integers(3, 6))
            for s_ in range(L):
                w.set(int(round(x + math.cos(a) * (2 + s_))), y0 + s_, int(round(z + math.sin(a) * (2 + s_))), "packed_ice")
        spots.append((x, z))
        made += 1
    print(f"[theme] 얼음 첨탑 {made}개")


def basalt_pillars(w, T, n=40):
    """현무암 기둥 무리 (주상절리) + 마그마 틈"""
    r = np.random.default_rng(T.seed + 601)
    made, spots = 0, []
    for _ in range(4000):
        if made >= n:
            break
        x, z = int(r.integers(10, S - 10)), int(r.integers(10, S - 10))
        if not _spot_ok(T, x, z) or any((x - a) ** 2 + (z - b) ** 2 < 11 ** 2 for a, b in spots):
            continue
        gy = int(T.Hi[x, z])
        for k in range(int(r.integers(4, 9))):
            px, pz = x + int(r.integers(-3, 4)), z + int(r.integers(-3, 4))
            if not (0 <= px < S and 0 <= pz < S):
                continue
            g2 = int(T.Hi[px, pz])
            h = int(r.integers(3, 12))
            for dy in range(-1, h):
                w.set(px, g2 + dy, pz, "basalt[axis=y]" if (dy + k) % 5 else "polished_basalt[axis=y]")
            if r.random() < 0.3:
                w.set(px, g2 + h, pz, "magma_block")
        spots.append((x, z))
        made += 1
    print(f"[theme] 현무암 기둥 무리 {made}개")


def magma_veins(w, T):
    """화산 비탈 · 강가에 빛나는 마그마 줄기 (지붕 윗면만)"""
    n = fbm(S, T.seed + 650, ((10, 1.0), (5, 0.4)))
    vein = (np.abs(n) < 0.04)
    cnt = 0
    for x in range(S):
        for z in range(S):
            if not vein[x, z] or T.zone[x, z] not in ("volcano", "") or T.road[x, z] > 0.01:
                continue
            y = int(T.Hi[x, z])
            st = w.get(x, y, z)
            if B.parse(st)[0] in ("blackstone", "smooth_basalt", "basalt", "tuff", "netherrack", "deepslate") and w.is_air(x, y + 1, z):
                w.set(x, y, z, "magma_block")
                cnt += 1
    print(f"[theme] 마그마 줄기 {cnt}칸")


# 직접 고친 성을 옮겨 심을 때: 성 블록은 그대로, 흙 · 풀 · 꽃 · 나무만 맵 테마로
CASTLE_NATURAL = {"grass_block", "moss_block", "dirt", "coarse_dirt", "rooted_dirt", "podzol", "short_grass", "fern", "bush", "sand",
                  "poppy", "oxeye_daisy", "azure_bluet", "cornflower", "allium", "dandelion", "pink_petals", "lily_of_the_valley",
                  "orange_tulip", "pink_tulip", "red_tulip", "dead_bush", "tall_grass", "large_fern", "dirt_path"}


def castle_conv(name, theme):
    table = REMAP.get(theme, {})
    bid = B.parse(name)[0]
    if bid not in CASTLE_NATURAL and not bid.endswith(("_leaves", "_log")):
        return name
    rule = table.get(bid)
    if rule is None:
        return name
    if isinstance(rule, list):
        rule = rule[0][0]
    if rule == "air":
        return "air"
    return _target(name, rule)


def world_post(w, T, theme):
    import userbase
    if theme == "olympus":
        userbase.whole(w)
        return
    remap(w, T, theme)
    fluids(w, T, theme)
    # 직접 고친 본진 성 4개 + 높이 69 천장 (올림포스와 똑같이)
    userbase.castles(w, theme, lambda n: castle_conv(n, theme))
    if theme == "frost":
        ice_spires(w, T)
        snow(w, T)
    if theme == "volcano":
        basalt_pillars(w, T)
        magma_veins(w, T)
    w.theme = theme
