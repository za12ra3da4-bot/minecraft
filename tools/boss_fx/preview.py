"""리소스팩 추가분 미리보기 한 장 → docs/preview/resourcepack_preview.png"""
import glob
import os

from PIL import Image, ImageDraw, ImageFont

from icons import ICONS, render
from illus_items import SPRITES

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..", "..", "resourcepack", "olympus_pack", "assets", "oly")
OUT = os.path.join(HERE, "..", "..", "docs", "preview", "resourcepack_preview.png")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BG = (28, 24, 22, 255)
PANEL = (44, 38, 34, 255)
GOLD = (232, 190, 96, 255)
TXT = (214, 204, 186, 255)


def section(draw, y, title, W):
    draw.rectangle([16, y, W - 16, y + 34], fill=(60, 46, 30, 255))
    draw.text((28, y + 6), title, font=ImageFont.truetype(FONTB, 20), fill=GOLD)
    return y + 46


def grid(canvas, draw, y, items, cell, scale, W, label_font):
    cols = (W - 32) // cell
    for i, (name, im) in enumerate(items):
        cx = 16 + (i % cols) * cell
        cy = y + (i // cols) * (cell + 18)
        draw.rectangle([cx + 4, cy, cx + cell - 4, cy + cell - 8], fill=PANEL)
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        canvas.alpha_composite(big, (cx + (cell - big.width) // 2, cy + (cell - 8 - big.height) // 2))
        tw = draw.textlength(name, font=label_font)
        draw.text((cx + (cell - tw) / 2, cy + cell - 6), name, font=label_font, fill=TXT)
    rows = (len(items) + cols - 1) // cols
    return y + rows * (cell + 18) + 12


def main():
    W = 1400
    canvas = Image.new("RGBA", (W, 3400), BG)
    draw = ImageDraw.Draw(canvas)
    lf = ImageFont.truetype(FONT, 11)
    draw.text((20, 14), "Olympus resource pack — boss skill expansion (added files only)", font=ImageFont.truetype(FONTB, 26), fill=GOLD)
    y = 60
    y = section(draw, y, "Skill icons (illustrated) 64x64 item + 32x32 font  →  font oly:icons (bossbar / title / actionbar) + item model oly:icon/<name> (floating over the boss)", W)
    icons = [(f"{b[:5]}_{k}", Image.open(os.path.join(PACK, "textures", "item", "icon", f"{b}_{k}.png")).convert("RGBA"))
             for i, (b, k, fn, _) in enumerate(ICONS)]
    y = grid(canvas, draw, y, icons, 136, 2, W, lf)
    y = section(draw, y, "Skill effect textures  →  models oly:fx/<name> (item_display decals, projectiles, tentacles, stone shell)", W)
    fx = []
    for p in sorted(glob.glob(os.path.join(PACK, "textures", "item", "fx", "*.png"))):
        im = Image.open(p).convert("RGBA")
        s = 96 // im.width if im.width <= 96 else 1
        fx.append((os.path.basename(p)[:-4], im.resize((im.width * max(1, s) // 1, im.height * max(1, s) // 1), Image.NEAREST)))
    y = grid(canvas, draw, y, fx, 116, 1, W, lf)
    y = section(draw, y, "Player items — 128px illustrations  →  custom_model_data 7101-7404 on the vanilla item", W)
    items = [(n, Image.open(os.path.join(PACK, "textures", "item", "gear", n + ".png")).convert("RGBA")) for n in SPRITES]
    items += [(n, Image.open(os.path.join(PACK, "textures", "item", "gear", n + ".png")).convert("RGBA")) for n in ("hoplon_face", "hoplon_back")]
    y = grid(canvas, draw, y, items, 136, 1, W, lf)
    y = section(draw, y, "Menu windows (font oly:gui over the chest)  —  Olympus menu 6 rows = temple facade  |  other menus 3/4/6 rows", W)
    x = 24
    for f in ("menu_main", "menu_grid3", "menu_grid4"):
        im = Image.open(os.path.join(PACK, "textures", "gui", f + ".png")).convert("RGBA")
        big = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        canvas.alpha_composite(big, (x, y))
        draw.text((x, y + big.height + 4), f, font=lf, fill=TXT)
        x += big.width + 40
    y += 222 * 2 + 30
    canvas = canvas.crop((0, 0, W, y + 10))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    canvas.save(OUT, optimize=True)
    print(OUT, canvas.size)


if __name__ == "__main__":
    main()
