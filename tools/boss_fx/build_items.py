"""플레이어 아이템 → 리소스팩

- 텍스처  assets/oly/textures/item/gear/<name>.png (32x32)
- 모델    assets/oly/models/gear/<name>.json
- 연결    assets/minecraft/items/<바닐라>.json  —  minecraft:custom_model_data(floats[0]) 로 분기.
          번호가 N 이면 우리 모델, N+0.5 부터는 다시 바닐라 (다른 번호가 우연히 걸리지 않게).
          번호가 없는 아이템(= 기존 모든 아이템)은 fallback = 바닐라 1.21.11 정의 그대로 (tools/boss_fx/vanilla/*.json)
- Skript  06-army / 10-monsters / 14-events / 08-heroes 가 olyCmdl(아이템, 번호) 로 번호를 붙인다
"""
import copy
import json
import os

from items_art import ITEMS, SPRITES, bake, hoplon_back, hoplon_face

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "resourcepack", "olympus_pack", "assets")
VAN = os.path.join(HERE, "vanilla")


def wjson(path, obj, compact=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def tex(name, im):
    p = os.path.join(ROOT, "oly", "textures", "item", "gear", name + ".png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p, optimize=True)


def mdl(name, obj):
    wjson(os.path.join(ROOT, "oly", "models", "gear", name + ".json"), obj)


def ref(name):
    return {"type": "minecraft:model", "model": f"oly:gear/{name}"}


def simple(name, parent):
    mdl(name, {"parent": parent, "textures": {"layer0": f"oly:item/gear/{name}"}})


def shield_models():
    tex("hoplon_face", hoplon_face(64))
    tex("hoplon_back", hoplon_back(64))
    rim = {"uv": [0, 7, 1, 9], "texture": "#back"}
    els = [
        # 앞 · 뒤 판 (원형은 텍스처 투명도로)
        {"from": [-4, -1, 6], "to": [12, 15, 7],
         "faces": {"north": {"uv": [0, 0, 16, 16], "texture": "#front"},
                   "south": {"uv": [16, 0, 0, 16], "texture": "#back"}}},
    ]
    # 팔각형 테두리 두께
    for frm, to in (([-4, 3, 6], [12, 11, 7]), ([0, -1, 6], [8, 15, 7]), ([-2.8, 0.2, 6], [10.8, 13.8, 7])):
        els.append({"from": frm, "to": to, "faces": {k: dict(rim) for k in ("east", "west", "up", "down")}})
    # 가운데 돌기 · 손잡이
    els.append({"from": [2.5, 5.5, 5.3], "to": [5.5, 8.5, 6],
                "faces": {k: {"uv": [7, 7, 9, 9], "texture": "#front"} for k in ("north", "east", "west", "up", "down")}})
    els.append({"from": [3, 3, 7], "to": [5, 11, 10],
                "faces": {k: {"uv": [4, 7, 6, 9], "texture": "#back"} for k in ("south", "east", "west", "up", "down")}})
    base = json.load(open(os.path.join(VAN, "_model_shield.json")))
    block = json.load(open(os.path.join(VAN, "_model_shield_blocking.json")))
    textures = {"front": "oly:item/gear/hoplon_face", "back": "oly:item/gear/hoplon_back", "particle": "oly:item/gear/hoplon_face"}
    mdl("hoplon", {"gui_light": "front", "textures": textures, "elements": els, "display": base["display"]})
    mdl("hoplon_blocking", {"parent": "oly:gear/hoplon", "display": block["display"]})


def entry_for(key, kind):
    if kind in ("handheld", "trident"):
        simple(key, "minecraft:item/handheld")
        return ref(key)
    if kind == "generated":
        simple(key, "minecraft:item/generated")
        return ref(key)
    if kind == "bow":
        simple(key, "minecraft:item/bow")
        for i in range(3):
            simple(f"{key}_pulling_{i}", "minecraft:item/bow")
        return {"type": "minecraft:condition", "property": "minecraft:using_item",
                "on_false": ref(key),
                "on_true": {"type": "minecraft:range_dispatch", "property": "minecraft:use_duration", "scale": 0.05,
                            "entries": [{"threshold": 0.65, "model": ref(f"{key}_pulling_1")},
                                        {"threshold": 0.9, "model": ref(f"{key}_pulling_2")}],
                            "fallback": ref(f"{key}_pulling_0")}}
    if kind == "crossbow":
        simple(key, "minecraft:item/crossbow")
        for i in range(3):
            simple(f"{key}_pulling_{i}", "minecraft:item/crossbow")
        simple(f"{key}_arrow", "minecraft:item/crossbow")
        return {"type": "minecraft:select", "property": "minecraft:charge_type",
                "cases": [{"when": "arrow", "model": ref(f"{key}_arrow")},
                          {"when": "rocket", "model": ref(f"{key}_arrow")}],
                "fallback": {"type": "minecraft:condition", "property": "minecraft:using_item",
                             "on_false": ref(key),
                             "on_true": {"type": "minecraft:range_dispatch", "property": "minecraft:crossbow/pull",
                                         "entries": [{"threshold": 0.58, "model": ref(f"{key}_pulling_1")},
                                                     {"threshold": 1.0, "model": ref(f"{key}_pulling_2")}],
                                         "fallback": ref(f"{key}_pulling_0")}}}
    if kind == "spear":
        simple(key, "minecraft:item/generated")
        simple(f"{key}_in_hand", "minecraft:item/spear_in_hand")
        return {"type": "minecraft:select", "property": "minecraft:display_context",
                "cases": [{"when": ["gui", "ground", "fixed", "on_shelf"], "model": ref(key)}],
                "fallback": ref(f"{key}_in_hand")}
    if kind == "shield":
        shield_models()
        return {"type": "minecraft:condition", "property": "minecraft:using_item",
                "on_false": ref("hoplon"), "on_true": ref("hoplon_blocking")}
    raise ValueError(kind)


def build():
    for name, fn in SPRITES.items():
        tex(name, bake(fn))
    by_base = {}
    for key, (base, cmd, kind) in ITEMS.items():
        by_base.setdefault(base, []).append((cmd, key, entry_for(key, kind)))
    table = []
    for base, lst in sorted(by_base.items()):
        van = json.load(open(os.path.join(VAN, base + ".json")))
        fallback = van["model"]
        entries = []
        for cmd, key, model in sorted(lst):
            entries.append({"threshold": cmd, "model": model})
            entries.append({"threshold": cmd + 0.5, "model": copy.deepcopy(fallback)})
            table.append((cmd, base, key))
        out = dict(van)
        out["model"] = {"type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data",
                        "index": 0, "entries": entries, "fallback": fallback}
        wjson(os.path.join(ROOT, "minecraft", "items", base + ".json"), out, compact=True)
    return sorted(table)


if __name__ == "__main__":
    for cmd, base, key in build():
        print(cmd, base, key)
