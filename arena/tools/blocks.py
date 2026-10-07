"""블록 레지스트리 — 블록 상태 문자열 → 렌더링 정보(형태 박스, 면 텍스처, 틴트, 발광)

맵 생성기는 블록을 "stone_brick_stairs[facing=north,half=bottom]" 같은 문자열로 다룬다.
이 모듈은 (1) 그 블록이 1.21.11 에 실제로 존재하는지 검증하고,
(2) 미리보기 렌더러가 쓸 형태/텍스처를 계산한다.
"""
import json
import os
import re
import subprocess

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache", "vanilla")
TEXDIR = os.path.join(CACHE, "textures", "block")
RAW = "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.21.11/assets/minecraft/"

_valid = None


def valid_ids():
    global _valid
    if _valid is None:
        p = os.path.join(CACHE, "blockstates_list.json")
        if not os.path.exists(p):
            os.makedirs(CACHE, exist_ok=True)
            subprocess.check_call(["curl", "-sS", "-o", p, RAW + "blockstates/_list.json"])
        _valid = {f[:-5] for f in json.load(open(p))["files"] if f.endswith(".json")}
        _valid.add("air")
    return _valid


def parse(state):
    """'x[a=b,c=d]' → ('x', {'a':'b','c':'d'})"""
    m = re.match(r"^(?:minecraft:)?([a-z0-9_]+)(?:\[(.*)\])?$", state)
    if not m:
        raise ValueError(state)
    props = {}
    if m.group(2):
        for kv in m.group(2).split(","):
            k, v = kv.split("=")
            props[k.strip()] = v.strip()
    return m.group(1), props


def fmt(bid, props):
    if not props:
        return bid
    return bid + "[" + ",".join(f"{k}={v}" for k, v in props.items()) + "]"


# ─────────────────────────────────────────────────────────────────────────────
#  텍스처
# ─────────────────────────────────────────────────────────────────────────────
_tex_cache = {}


_missing = None


def tex_path(name):
    global _missing
    p = os.path.join(TEXDIR, name + ".png")
    if not os.path.exists(p):
        mf = os.path.join(CACHE, "missing.txt")
        if _missing is None:
            _missing = set(open(mf).read().split()) if os.path.exists(mf) else set()
        if name in _missing:
            return p
        os.makedirs(TEXDIR, exist_ok=True)
        subprocess.call(["curl", "-sS", "-f", "-o", p, RAW + "textures/block/" + name + ".png"], stderr=subprocess.DEVNULL)
        if not os.path.exists(p):
            _missing.add(name)
            with open(mf, "a") as f:
                f.write(name + "\n")
    return p


def load_tex(name):
    """16x16 RGBA float32 (0..1). 애니메이션 텍스처는 첫 프레임만"""
    if name in _tex_cache:
        return _tex_cache[name]
    p = tex_path(name)
    if not os.path.exists(p):
        raise FileNotFoundError(name)
    im = Image.open(p).convert("RGBA")
    w, h = im.size
    if h > w:
        im = im.crop((0, 0, w, w))
    if w != 16:
        im = im.resize((16, 16), Image.NEAREST)
    a = np.asarray(im, dtype=np.float32) / 255.0
    _tex_cache[name] = a
    return a


def tex_exists(name):
    return os.path.exists(tex_path(name))


GRASS = np.array([0.57, 0.74, 0.35], np.float32)
FOLIAGE = np.array([0.47, 0.67, 0.18], np.float32)
SPRUCE = np.array([0.38, 0.60, 0.38], np.float32)
BIRCH = np.array([0.50, 0.65, 0.33], np.float32)
WATER = np.array([0.25, 0.46, 0.89], np.float32)
DRY = np.array([0.75, 0.72, 0.42], np.float32)

WOODS = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "pale_oak", "bamboo", "crimson", "warped"]

# 재료 접두사 → (위, 옆, 아래) 텍스처.  stairs/slab/wall 계열이 여기서 기본 재료를 찾는다
MATERIAL = {
    "stone_brick": "stone_bricks", "mossy_stone_brick": "mossy_stone_bricks",
    "cobblestone": "cobblestone", "mossy_cobblestone": "mossy_cobblestone",
    "stone": "stone", "smooth_stone": "smooth_stone", "granite": "granite", "polished_granite": "polished_granite",
    "diorite": "diorite", "polished_diorite": "polished_diorite", "andesite": "andesite",
    "polished_andesite": "polished_andesite", "brick": "bricks", "mud_brick": "mud_bricks",
    "sandstone": ("sandstone_top", "sandstone", "sandstone_bottom"),
    "smooth_sandstone": "sandstone_top", "cut_sandstone": ("sandstone_top", "cut_sandstone", "sandstone_top"),
    "red_sandstone": ("red_sandstone_top", "red_sandstone", "red_sandstone_bottom"),
    "smooth_red_sandstone": "red_sandstone_top", "cut_red_sandstone": ("red_sandstone_top", "cut_red_sandstone", "red_sandstone_top"),
    "quartz": ("quartz_block_top", "quartz_block_side", "quartz_block_bottom"), "smooth_quartz": "quartz_block_bottom",
    "cobbled_deepslate": "cobbled_deepslate", "polished_deepslate": "polished_deepslate",
    "deepslate_brick": "deepslate_bricks", "deepslate_tile": "deepslate_tiles",
    "blackstone": ("blackstone_top", "blackstone", "blackstone_top"), "polished_blackstone": "polished_blackstone",
    "polished_blackstone_brick": "polished_blackstone_bricks",
    "tuff": "tuff", "polished_tuff": "polished_tuff", "tuff_brick": "tuff_bricks",
    "end_stone_brick": "end_stone_bricks", "prismarine": "prismarine", "prismarine_brick": "prismarine_bricks",
    "dark_prismarine": "dark_prismarine", "nether_brick": "nether_bricks", "red_nether_brick": "red_nether_bricks",
    "purpur": "purpur_block", "resin_brick": "resin_bricks",
    "cut_copper": "cut_copper", "exposed_cut_copper": "exposed_cut_copper", "weathered_cut_copper": "weathered_cut_copper",
    "oxidized_cut_copper": "oxidized_cut_copper", "waxed_cut_copper": "cut_copper",
    "waxed_oxidized_cut_copper": "oxidized_cut_copper", "waxed_weathered_cut_copper": "weathered_cut_copper",
    "waxed_exposed_cut_copper": "exposed_cut_copper",
}
for _w in WOODS:
    MATERIAL[_w] = _w + "_planks"

# 블록 → 텍스처 특수 규칙 (top, side, bottom)
SPECIAL = {
    "grass_block": ("grass_block_top", "grass_block_side", "dirt"),
    "podzol": ("podzol_top", "podzol_side", "dirt"),
    "mycelium": ("mycelium_top", "mycelium_side", "dirt"),
    "dirt_path": ("dirt_path_top", "dirt_path_side", "dirt"),
    "farmland": ("farmland", "dirt", "dirt"),
    "sandstone": ("sandstone_top", "sandstone", "sandstone_bottom"),
    "chiseled_sandstone": ("sandstone_top", "chiseled_sandstone", "sandstone_top"),
    "cut_sandstone": ("sandstone_top", "cut_sandstone", "sandstone_top"),
    "smooth_sandstone": ("sandstone_top",) * 3,
    "red_sandstone": ("red_sandstone_top", "red_sandstone", "red_sandstone_bottom"),
    "smooth_red_sandstone": ("red_sandstone_top",) * 3,
    "quartz_block": ("quartz_block_top", "quartz_block_side", "quartz_block_bottom"),
    "smooth_quartz": ("quartz_block_bottom",) * 3,
    "chiseled_quartz_block": ("chiseled_quartz_block_top", "chiseled_quartz_block", "chiseled_quartz_block_top"),
    "quartz_pillar": ("quartz_pillar_top", "quartz_pillar", "quartz_pillar_top"),
    "quartz_bricks": ("quartz_bricks",) * 3,
    "smooth_stone": ("smooth_stone",) * 3,
    "basalt": ("basalt_top", "basalt_side", "basalt_top"),
    "polished_basalt": ("polished_basalt_top", "polished_basalt_side", "polished_basalt_top"),
    "smooth_basalt": ("smooth_basalt",) * 3,
    "blackstone": ("blackstone_top", "blackstone", "blackstone_top"),
    "chiseled_polished_blackstone": ("chiseled_polished_blackstone",) * 3,
    "gilded_blackstone": ("gilded_blackstone",) * 3,
    "deepslate": ("deepslate_top", "deepslate", "deepslate_top"),
    "chiseled_deepslate": ("chiseled_deepslate",) * 3,
    "reinforced_deepslate": ("reinforced_deepslate_top", "reinforced_deepslate_side", "reinforced_deepslate_bottom"),
    "bone_block": ("bone_block_top", "bone_block_side", "bone_block_top"),
    "hay_block": ("hay_block_top", "hay_block_side", "hay_block_top"),
    "magma_block": ("magma",) * 3,
    "crying_obsidian": ("crying_obsidian",) * 3,
    "ochre_froglight": ("ochre_froglight_top", "ochre_froglight_side", "ochre_froglight_top"),
    "verdant_froglight": ("verdant_froglight_top", "verdant_froglight_side", "verdant_froglight_top"),
    "pearlescent_froglight": ("pearlescent_froglight_top", "pearlescent_froglight_side", "pearlescent_froglight_top"),
    "snow_block": ("snow",) * 3, "snow": ("snow",) * 3,
    "water": ("water_still",) * 3, "lava": ("lava_still",) * 3,
    "chiseled_stone_bricks": ("chiseled_stone_bricks",) * 3,
    "chiseled_tuff": ("chiseled_tuff_top", "chiseled_tuff", "chiseled_tuff_top"),
    "chiseled_tuff_bricks": ("chiseled_tuff_bricks_top", "chiseled_tuff_bricks", "chiseled_tuff_bricks_top"),
    "chiseled_resin_bricks": ("chiseled_resin_bricks",) * 3,
    "beacon": ("beacon",) * 3,
    "dried_kelp_block": ("dried_kelp_top", "dried_kelp_side", "dried_kelp_bottom"),
    "moss_carpet": ("moss_block",) * 3, "pale_moss_carpet": ("pale_moss_block",) * 3,
    "lodestone": ("lodestone_top", "lodestone_side", "lodestone_top"),
    "target": ("target_top", "target_side", "target_top"),
    "melon": ("melon_top", "melon_side", "melon_top"),
    "pumpkin": ("pumpkin_top", "pumpkin_side", "pumpkin_top"),
    "barrel": ("barrel_top", "barrel_side", "barrel_bottom"),
    "crafting_table": ("crafting_table_top", "crafting_table_front", "oak_planks"),
    "smithing_table": ("smithing_table_top", "smithing_table_front", "smithing_table_bottom"),
    "anvil": ("anvil_top", "anvil", "anvil"),
    "cauldron": ("cauldron_top", "cauldron_side", "cauldron_bottom"),
    "lectern": ("lectern_top", "lectern_sides", "oak_planks"),
    "bookshelf": ("oak_planks", "bookshelf", "oak_planks"),
    "tnt": ("tnt_top", "tnt_side", "tnt_bottom"),
    "copper_bulb": ("copper_bulb_lit",) * 3,
    "oxidized_copper_bulb": ("oxidized_copper_bulb_lit",) * 3,
    "decorated_pot": ("terracotta",) * 3,
    "iron_bars": ("iron_bars",) * 3,
    "rooted_dirt": ("rooted_dirt",) * 3,
    "mud": ("mud",) * 3,
    "packed_mud": ("packed_mud",) * 3,
    "sculk": ("sculk",) * 3,
    "cactus": ("cactus_top", "cactus_side", "cactus_bottom"),
    "scaffolding": ("scaffolding_top", "scaffolding_side", "scaffolding_bottom"),
    "suspicious_sand": ("suspicious_sand_0",) * 3,
    "suspicious_gravel": ("suspicious_gravel_0",) * 3,
    "respawn_anchor": ("respawn_anchor_top", "respawn_anchor_side4", "respawn_anchor_bottom"),
    "chiseled_copper": ("chiseled_copper",) * 3,
    "copper_grate": ("copper_grate",) * 3,
    "oxidized_copper_grate": ("oxidized_copper_grate",) * 3,
    "glowstone": ("glowstone",) * 3,
    "shroomlight": ("shroomlight",) * 3,
    "sea_lantern": ("sea_lantern",) * 3,
    "amethyst_block": ("amethyst_block",) * 3,
    "budding_amethyst": ("budding_amethyst",) * 3,
    "raw_gold_block": ("raw_gold_block",) * 3,
    "gold_block": ("gold_block",) * 3,
    "iron_block": ("iron_block",) * 3,
    "calcite": ("calcite",) * 3,
    "dripstone_block": ("dripstone_block",) * 3,
    "soul_soil": ("soul_soil",) * 3,
    "soul_sand": ("soul_sand",) * 3,
    "grindstone": ("grindstone_side",) * 3,
}

EMISSIVE = {
    "glowstone": 1.0, "shroomlight": 1.0, "sea_lantern": 1.0, "lantern": 1.0, "soul_lantern": 0.9,
    "copper_lantern": 1.0, "oxidized_copper_lantern": 1.0,
    "ochre_froglight": 1.0, "verdant_froglight": 1.0, "pearlescent_froglight": 1.0, "magma_block": 0.7,
    "lava": 1.0, "fire": 1.0, "soul_fire": 1.0, "campfire": 0.8, "soul_campfire": 0.8, "torch": 1.0,
    "wall_torch": 1.0, "soul_torch": 1.0, "soul_wall_torch": 1.0, "end_rod": 1.0, "beacon": 1.0,
    "crying_obsidian": 0.5, "jack_o_lantern": 1.0, "copper_bulb": 1.0, "oxidized_copper_bulb": 0.8,
    "redstone_lamp": 0.0, "candle": 0.6, "firefly_bush": 0.2, "respawn_anchor": 0.6,
}

CROSS = {"short_grass", "fern", "dead_bush", "poppy", "dandelion", "cornflower", "oxeye_daisy", "allium",
         "azure_bluet", "blue_orchid", "lily_of_the_valley", "red_tulip", "orange_tulip", "white_tulip",
         "pink_tulip", "sweet_berry_bush", "bush", "firefly_bush", "short_dry_grass", "tall_dry_grass",
         "fire", "soul_fire", "oak_sapling", "spruce_sapling", "birch_sapling", "cherry_sapling",
         "pointed_dripstone", "brown_mushroom", "red_mushroom", "crimson_roots", "warped_roots",
         "nether_sprouts", "torchflower", "cactus_flower", "cobweb", "hanging_roots", "pale_hanging_moss",
         "tall_grass", "large_fern", "rose_bush", "lilac", "peony", "sunflower", "wither_rose",
         "open_eyeblossom", "closed_eyeblossom", "iron_bars_cross", "wheat"}

CROSS_TEX = {"sweet_berry_bush": "sweet_berry_bush_stage3", "fire": "fire_0", "soul_fire": "soul_fire_0",
             "pointed_dripstone": "pointed_dripstone_up_tip", "tall_grass": "tall_grass_bottom",
             "large_fern": "large_fern_bottom", "rose_bush": "rose_bush_bottom", "lilac": "lilac_bottom",
             "peony": "peony_bottom", "sunflower": "sunflower_bottom", "tall_dry_grass": "tall_dry_grass",
             "open_eyeblossom": "open_eyeblossom", "closed_eyeblossom": "closed_eyeblossom", "wheat": "wheat_stage7"}

TINT_CROSS = {"short_grass": GRASS, "fern": GRASS, "tall_grass": GRASS, "large_fern": GRASS, "bush": GRASS}

LEAVES_TINT = {"oak_leaves": FOLIAGE, "jungle_leaves": FOLIAGE, "acacia_leaves": FOLIAGE,
               "dark_oak_leaves": FOLIAGE, "mangrove_leaves": FOLIAGE, "spruce_leaves": SPRUCE,
               "birch_leaves": BIRCH}

TRANSLUCENT_SUFFIX = ("_stained_glass",)


def base_material(bid):
    """stone_brick_stairs → stone_brick"""
    for suf in ("_stairs", "_slab", "_wall", "_fence_gate", "_fence", "_pressure_plate", "_button", "_trapdoor", "_door", "_sign", "_hanging_sign"):
        if bid.endswith(suf):
            return bid[: -len(suf)], suf
    return bid, ""


def material_tex(mat):
    """재료 이름 → (top, side, bottom)"""
    if mat in MATERIAL:
        t = MATERIAL[mat]
        if isinstance(t, str):
            return (t, t, t)
        return t
    if mat in SPECIAL:
        return SPECIAL[mat]
    for cand in (mat + "s", mat + "_block", mat):
        if tex_exists(cand):
            return (cand, cand, cand)
    raise KeyError("no texture for material " + mat)


def block_tex(bid, props):
    """꽉 찬 블록의 (top, side, bottom). 원목은 축 처리"""
    if bid in SPECIAL:
        return SPECIAL[bid]
    if bid.endswith("_log") or bid.endswith("_stem") or bid.endswith("_wood") or bid.endswith("_hyphae"):
        stripped = bid.startswith("stripped_")
        core = bid.replace("_wood", "_log").replace("_hyphae", "_stem")
        top = core + "_top"
        side = core
        if bid.endswith("_wood") or bid.endswith("_hyphae"):
            top = side
        return (top, side, top)
    if bid.endswith("_pillar") and tex_exists(bid + "_top"):
        return (bid + "_top", bid, bid + "_top")
    if tex_exists(bid):
        return (bid, bid, bid)
    if tex_exists(bid + "_top") and tex_exists(bid + "_side"):
        bot = bid + "_bottom" if tex_exists(bid + "_bottom") else bid + "_top"
        return (bid + "_top", bid + "_side", bot)
    mat, suf = base_material(bid)
    return material_tex(mat)


# ─────────────────────────────────────────────────────────────────────────────
#  렌더 기술자
# ─────────────────────────────────────────────────────────────────────────────
#  kind: 0 air, 1 opaque, 2 cutout(leaves), 3 cross(plant), 4 translucent(glass), 5 water, 6 lava
#  face order: 0 -x(west) 1 +x(east) 2 -y(down) 3 +y(up) 4 -z(north) 5 +z(south)

FACE_DIR = {"west": 0, "east": 1, "down": 2, "up": 3, "north": 4, "south": 5}


class Desc:
    __slots__ = ("kind", "boxes", "tex", "tint", "emit", "alpha")

    def __init__(self, kind, boxes, tex, tint=None, emit=0.0, alpha=1.0):
        self.kind = kind
        self.boxes = boxes          # [(x0,y0,z0,x1,y1,z1)] 0..1
        self.tex = tex              # 6 texture names
        self.tint = tint or [None] * 6
        self.emit = emit
        self.alpha = alpha


FULL = [(0, 0, 0, 1, 1, 1)]


def _tsb(t, s, b):
    return [s, s, b, t, s, s]


def _stairs_boxes(facing, half, shape="straight"):
    y0, y1 = (0, 0.5) if half == "bottom" else (0.5, 1)
    u0, u1 = (0.5, 1) if half == "bottom" else (0, 0.5)
    boxes = [(0, y0, 0, 1, y1, 1)]
    q = {"north": (0, u0, 0, 1, u1, 0.5), "south": (0, u0, 0.5, 1, u1, 1),
         "west": (0, u0, 0, 0.5, u1, 1), "east": (0.5, u0, 0, 1, u1, 1)}
    boxes.append(q[facing])
    return boxes


def _conn_boxes(post, arm, props, arm_h):
    """벽/울타리/판유리: 중심 기둥 + 연결 팔"""
    px0, px1 = post
    ax0, ax1 = arm
    boxes = []
    if post:
        up = props.get("up", "true") == "true" if "up" in props else True
        boxes.append((px0, 0, px0, px1, 1 if up else arm_h, px1))
    for d in ("north", "south", "west", "east"):
        v = props.get(d, "none")
        if v in ("none", "false"):
            continue
        h = 1.0 if v == "tall" else arm_h
        if d == "north":
            boxes.append((ax0, 0, 0, ax1, h, 0.5))
        elif d == "south":
            boxes.append((ax0, 0, 0.5, ax1, h, 1))
        elif d == "west":
            boxes.append((0, 0, ax0, 0.5, h, ax1))
        else:
            boxes.append((0.5, 0, ax0, 1, h, ax1))
    return boxes


_desc_cache = {}


def describe(state):
    if state in _desc_cache:
        return _desc_cache[state]
    d = _describe(state)
    _desc_cache[state] = d
    return d


def _describe(state):
    bid, p = parse(state)
    if bid in ("air", "cave_air", "void_air", "barrier", "light", "structure_void"):
        return Desc(0, [], [None] * 6)
    if bid == "water":
        return Desc(5, [(0, 0, 0, 1, 0.875, 1)], ["water_still"] * 6, [WATER] * 6, alpha=0.62)
    if bid == "lava":
        return Desc(6, [(0, 0, 0, 1, 0.875, 1)], ["lava_still"] * 6, emit=1.0)
    if bid == "grass_block":
        tint = [None, None, None, GRASS, None, None]
        return Desc(1, FULL, ["grass_block_side_c"] * 2 + ["dirt", "grass_block_top"] + ["grass_block_side_c"] * 2, tint)
    if bid.endswith("_leaves"):
        t = bid
        tint = LEAVES_TINT.get(bid)
        return Desc(2, FULL, [t] * 6, [tint] * 6)
    if bid in CROSS:
        t = CROSS_TEX.get(bid, bid)
        return Desc(3, FULL, [t] * 6, [TINT_CROSS.get(bid)] * 6, emit=EMISSIVE.get(bid, 0.0))
    if bid.endswith("_stained_glass") or bid in ("glass", "tinted_glass"):
        return Desc(4, FULL, [bid] * 6, alpha=0.45)
    if bid.endswith("_stained_glass_pane") or bid == "glass_pane":
        g = bid[:-5]
        return Desc(4, _conn_boxes((7 / 16, 9 / 16), (7 / 16, 9 / 16), p, 1.0), [g] * 6, alpha=0.5)
    if bid in ("iron_bars",):
        return Desc(2, _conn_boxes((7 / 16, 9 / 16), (7 / 16, 9 / 16), p, 1.0), ["iron_bars"] * 6)
    if bid.endswith("_slab"):
        mat, _ = base_material(bid)
        t, s, b = material_tex(mat)
        typ = p.get("type", "bottom")
        box = {"bottom": (0, 0, 0, 1, 0.5, 1), "top": (0, 0.5, 0, 1, 1, 1), "double": (0, 0, 0, 1, 1, 1)}[typ]
        return Desc(1, [box], _tsb(t, s, b))
    if bid.endswith("_stairs"):
        mat, _ = base_material(bid)
        t, s, b = material_tex(mat)
        return Desc(1, _stairs_boxes(p.get("facing", "north"), p.get("half", "bottom")), _tsb(t, s, b))
    if bid.endswith("_wall") and not bid.endswith("_sign"):
        mat, _ = base_material(bid)
        t, s, b = material_tex(mat)
        return Desc(1, _conn_boxes((0.25, 0.75), (5 / 16, 11 / 16), p, 14 / 16), _tsb(t, s, b))
    if bid.endswith("_fence"):
        mat, _ = base_material(bid)
        t, s, b = material_tex(mat)
        return Desc(1, _conn_boxes((6 / 16, 10 / 16), (7 / 16, 9 / 16), p, 15 / 16), _tsb(t, s, b))
    if bid.endswith("_carpet"):
        col = bid[:-7]
        tex = col + "_wool" if tex_exists(col + "_wool") else ("moss_block" if col == "moss" else "pale_moss_block")
        return Desc(1, [(0, 0, 0, 1, 1 / 16, 1)], [tex] * 6)
    if bid in ("leaf_litter", "pink_petals", "wildflowers"):
        return Desc(2, [(0, 0, 0, 1, 1 / 32, 1)], [bid] * 6, [DRY if bid == "leaf_litter" else None] * 6)
    if bid == "snow":
        n = int(p.get("layers", "1"))
        return Desc(1, [(0, 0, 0, 1, n / 8, 1)], ["snow"] * 6)
    if bid in ("lantern", "soul_lantern", "copper_lantern", "oxidized_copper_lantern"):
        hang = p.get("hanging") == "true"
        y0 = 1 / 16 if hang else 0
        return Desc(1, [(5 / 16, y0, 5 / 16, 11 / 16, y0 + 7 / 16, 11 / 16)], [bid] * 6, emit=EMISSIVE.get(bid, 1.0))
    if bid in ("iron_chain", "copper_chain", "oxidized_copper_chain"):
        ax = p.get("axis", "y")
        if ax == "y":
            b = (7 / 16, 0, 7 / 16, 9 / 16, 1, 9 / 16)
        elif ax == "x":
            b = (0, 7 / 16, 7 / 16, 1, 9 / 16, 9 / 16)
        else:
            b = (7 / 16, 7 / 16, 0, 9 / 16, 9 / 16, 1)
        return Desc(1, [b], ["iron_chain" if bid == "iron_chain" else "copper_chain"] * 6)
    if bid in ("torch", "soul_torch"):
        return Desc(1, [(7 / 16, 0, 7 / 16, 9 / 16, 10 / 16, 9 / 16)], [bid] * 6, emit=1.0)
    if bid in ("wall_torch", "soul_wall_torch"):
        return Desc(1, [(7 / 16, 3 / 16, 7 / 16, 9 / 16, 13 / 16, 9 / 16)], [bid.replace("wall_", "")] * 6, emit=1.0)
    if bid in ("campfire", "soul_campfire"):
        lit = "campfire_log_lit" if bid == "campfire" else "soul_campfire_log_lit"
        return Desc(1, [(0, 0, 0, 1, 7 / 16, 1)], [lit] * 6, emit=0.8)
    if bid == "end_rod":
        return Desc(1, [(7 / 16, 0, 7 / 16, 9 / 16, 1, 9 / 16)], ["end_rod"] * 6, emit=1.0)
    if bid == "lightning_rod":
        return Desc(1, [(7 / 16, 0, 7 / 16, 9 / 16, 1, 9 / 16)], ["copper_block"] * 6)
    if bid.endswith("candle") or bid.endswith("_candle"):
        return Desc(1, [(7 / 16, 0, 7 / 16, 9 / 16, 6 / 16, 9 / 16)], ["candle"] * 6, emit=0.6)
    if bid == "flower_pot" or bid.startswith("potted_"):
        return Desc(1, [(5 / 16, 0, 5 / 16, 11 / 16, 6 / 16, 11 / 16)], ["flower_pot"] * 6)
    if bid.endswith("_trapdoor"):
        mat, _ = base_material(bid)
        t = bid if tex_exists(bid) else material_tex(mat)[1]
        half = p.get("half", "bottom")
        op = p.get("open", "false") == "true"
        if not op:
            b = (0, 0, 0, 1, 3 / 16, 1) if half == "bottom" else (0, 13 / 16, 0, 1, 1, 1)
        else:
            f = p.get("facing", "north")
            b = {"north": (0, 0, 13 / 16, 1, 1, 1), "south": (0, 0, 0, 1, 1, 3 / 16),
                 "west": (13 / 16, 0, 0, 1, 1, 1), "east": (0, 0, 0, 3 / 16, 1, 1)}[f]
        return Desc(2, [b], [t] * 6)
    if bid in ("anvil", "chipped_anvil", "damaged_anvil"):
        return Desc(1, [(0.125, 0, 0.125, 0.875, 0.25, 0.875), (0.25, 0.25, 0.3, 0.75, 0.6, 0.7), (0, 0.6, 0.2, 1, 1, 0.8)], _tsb("anvil_top", "anvil", "anvil"))
    if bid == "cauldron":
        return Desc(1, [(0, 0.2, 0, 1, 1, 1)], _tsb("cauldron_top", "cauldron_side", "cauldron_bottom"))
    if bid == "decorated_pot":
        return Desc(1, [(1 / 16, 0, 1 / 16, 15 / 16, 1, 15 / 16)], ["terracotta"] * 6)
    if bid.endswith("_head") or bid.endswith("_skull"):
        return Desc(1, [(0.25, 0, 0.25, 0.75, 0.5, 0.75)], ["bone_block_side"] * 6)
    if bid == "lily_pad":
        return Desc(2, [(0, 0, 0, 1, 1 / 64, 1)], ["lily_pad"] * 6, [np.array([0.13, 0.5, 0.19], np.float32)] * 6)
    if bid == "moss_carpet":
        return Desc(1, [(0, 0, 0, 1, 1 / 16, 1)], ["moss_block"] * 6)
    if bid == "pale_moss_carpet":
        return Desc(1, [(0, 0, 0, 1, 1 / 16, 1)], ["pale_moss_block"] * 6)
    if bid.endswith("_banner") or bid.endswith("_wall_banner"):
        col = bid.replace("_wall_banner", "").replace("_banner", "")
        return Desc(1, [(0.45, 0, 0.1, 0.55, 1, 0.9)], [col + "_wool"] * 6)
    if bid.endswith("_button") or bid.endswith("_pressure_plate"):
        mat, _ = base_material(bid)
        t = material_tex(mat)
        return Desc(1, [(0.06, 0, 0.06, 0.94, 1 / 16, 0.94)], [t[0]] * 6)
    if bid in ("ladder", "vine", "glow_lichen"):
        f = p.get("facing", "north")
        b = {"north": (0, 0, 15 / 16, 1, 1, 1), "south": (0, 0, 0, 1, 1, 1 / 16),
             "west": (15 / 16, 0, 0, 1, 1, 1), "east": (0, 0, 0, 1 / 16, 1, 1)}.get(f, (0, 0, 15 / 16, 1, 1, 1))
        return Desc(2, [b], [bid] * 6, [FOLIAGE if bid == "vine" else None] * 6)
    if bid.endswith("_log") or bid.endswith("_wood") or bid.endswith("_stem") or bid.endswith("_hyphae") or bid in (
            "basalt", "polished_basalt", "bone_block", "hay_block", "quartz_pillar", "purpur_pillar", "deepslate",
            "ochre_froglight", "verdant_froglight", "pearlescent_froglight") or "axis" in p:
        t, s, b = block_tex(bid, p)
        ax = p.get("axis", "y")
        if ax == "y":
            tex = [s, s, b, t, s, s]
        elif ax == "x":
            tex = [t, t, s, s, s, s]
        else:
            tex = [s, s, s, s, t, t]
        return Desc(1, FULL, tex, emit=EMISSIVE.get(bid, 0.0))
    # 기본: 꽉 찬 블록
    t, s, b = block_tex(bid, p)
    kind = 1
    return Desc(kind, FULL, _tsb(t, s, b), emit=EMISSIVE.get(bid, 0.0))


def composite_textures():
    """합성 텍스처 (풀 옆면 = 흙 옆면 + 색입힌 오버레이)"""
    side = load_tex("grass_block_side").copy()
    ov = load_tex("grass_block_side_overlay")
    a = ov[..., 3:4]
    col = ov[..., :3] * GRASS
    side[..., :3] = side[..., :3] * (1 - a) + col * a
    _tex_cache["grass_block_side_c"] = side


def check_all(states):
    """존재하지 않는 블록 ID 가 있으면 예외"""
    ids = valid_ids()
    bad = sorted({parse(s)[0] for s in states if parse(s)[0] not in ids})
    if bad:
        raise ValueError("존재하지 않는 블록: " + ", ".join(bad))
