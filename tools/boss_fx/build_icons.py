"""아이콘 → 리소스팩 (텍스처 · 아이템 모델 · 폰트) + Skript 글리프 표.

python3 build_icons.py  (tools/boss_fx 에서)
"""
import json
import os
from icons import ICONS, render, render_small

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "resourcepack", "olympus_pack", "assets", "oly")
BASE_CP = 0xE100


def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main():
    providers = []
    table = []
    for i, (boss, key, fn, label) in enumerate(ICONS):
        name = f"{boss}_{key}"
        # 64px = 아이템 모델 (보스 머리 위 · 표식 · 인벤토리), 32px = 폰트 글리프 (보스바 · 자막 · 액션바)
        png = os.path.join(ROOT, "textures", "item", "icon", name + ".png")
        os.makedirs(os.path.dirname(png), exist_ok=True)
        render(boss, fn, i).save(png, optimize=True)
        small = os.path.join(ROOT, "textures", "font", "icons", name + ".png")
        os.makedirs(os.path.dirname(small), exist_ok=True)
        render_small(boss, fn, i).save(small, optimize=True)
        # 아이템 모델 (보스 머리 위 시전 표시 · 표식 · 인벤토리)
        w(os.path.join(ROOT, "models", "icon", name + ".json"),
          {"parent": "minecraft:item/generated", "textures": {"layer0": f"oly:item/icon/{name}"}})
        w(os.path.join(ROOT, "items", "icon", name + ".json"),
          {"model": {"type": "minecraft:model", "model": f"oly:icon/{name}"}})
        ch = chr(BASE_CP + i)
        providers.append({"type": "minecraft:bitmap", "file": f"oly:font/icons/{name}.png",
                          "ascent": 8, "height": 9, "chars": [ch]})
        table.append((boss, key, ch, label, BASE_CP + i))
    w(os.path.join(ROOT, "font", "icons.json"), {"providers": providers})
    return table


if __name__ == "__main__":
    t = main()
    for boss, key, ch, label, cp in t:
        print(f"{boss:12s} {key:10s} U+{cp:04X} {label}")
