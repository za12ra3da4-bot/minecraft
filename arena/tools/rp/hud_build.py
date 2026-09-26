"""HUD/보스바 글리프 생성 + 합성 규칙 (파이썬판)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from PIL import Image

import hud as H
from bossdata import BOSSES

PORTRAITS = os.path.join(os.path.dirname(HERE), ".cache", "portraits")


def gui_panel(f):
    """상점 화면 배경 글리프 4조각 (2x2) — 인벤토리 제목에 넣으면 상자 화면 전체를 덮는다
       제목 기준선: 위쪽 조각 ascent 13 (= 화면 맨 위), 아래 조각 -71"""
    import decor2d
    im = decor2d.shop_panel()                     # 352 x 336 (GUI 176 x 168 의 2배)
    keys = []
    for r in range(2):
        for c in range(2):
            tile = im.crop((c * 176, r * 168, (c + 1) * 176, (r + 1) * 168)).copy()
            px = tile.load()
            if px[175, 0][3] == 0:
                px[175, 0] = (0, 0, 0, 1)
            ch = chr(f.next); f.next += 1
            fname = f"font/gui_shop_{r}{c}.png"
            f.files[fname] = tile
            f.providers.append({"type": "bitmap", "file": f"{H.NS}:{fname}", "height": 84, "ascent": 13 - 84 * r, "chars": [ch]})
            keys.append(ch)
    # 제목 위치(x=8) → 화면 왼쪽(0) 으로, 조각마다 폭 88 + 1 (알파 1 픽셀)
    s = H.sp(-8) + keys[0] + H.sp(-1) + keys[1] + H.sp(-177) + keys[2] + H.sp(-1) + keys[3] + H.sp(-169)
    f.glyphs["gui/shop"] = dict(char=s, adv=0, x=0, y=0, widget="hud")
    return s


def build(pack):
    f = H.Font()
    H.boss_static(f)
    H.fill_tiles(f)
    H.banners(f)
    H.status_icons(f)
    H.digits(f, "boss/d", "boss", 18)
    H.digits(f, "hud/d", "hud", 6)
    H.digits(f, "hud/t", "hud", 3)
    H.team_hud(f)
    for bid, b in BOSSES.items():
        H.label(f, f"boss/name_{bid}", b["name"], "name")
        p = os.path.join(PORTRAITS, f"{bid}.png")
        if os.path.exists(p):
            img = Image.open(p)
        else:
            img = Image.new("RGBA", (64, 64), (60, 40, 30, 255))
        H.portrait(f, bid, img)
    gui_panel(f)
    # 파일
    for name, img in f.files.items():
        pack.png(f"assets/{H.NS}/textures/{name}", img)
    pack.put(f"assets/{H.NS}/font/hud.json", H.build_font_json(f))
    # 바닐라 white 보스바 숨김
    blank = Image.new("RGBA", (182, 5), (0, 0, 0, 0))
    pack.png("assets/minecraft/textures/gui/sprites/boss_bar/white_background.png", blank)
    pack.png("assets/minecraft/textures/gui/sprites/boss_bar/white_progress.png", blank)
    return f


# ── 합성 (Skript 쪽 13-bg-hud.sk 가 똑같이 한다)
def fill_str(f, kind, px, tile, x0, prefix="boss/"):
    s = ""
    full, part = divmod(int(px), tile)
    for i in range(full):
        s += H.place(f, f"{prefix}{kind}_{tile}", x0 + i * tile)
    if part > 0:
        s += H.place(f, f"{prefix}{kind}_{part}", x0 + full * tile)
    return s


def digits_str(f, text, cx, prefix, widget_x=0, adv=8):
    w = len(text) * adv
    x = int(round(widget_x + cx - w / 2))
    chars = ""
    for ch in text:
        k = {"/": "slash", ":": "colon"}.get(ch, ch)
        chars += f.glyphs[f"{prefix}_{k}"]["char"]
    return H.sp(x) + chars + H.sp(-(x + w))


def boss_str(f, boss, hp, maxhp, trail, state="normal", skill=None, cast=0.0):
    s = H.place(f, "boss/back0") + H.place(f, "boss/back1")
    tp = round(H.FILL_W * max(0, min(1, trail / maxhp)))
    hpx = round(H.FILL_W * max(0, min(1, hp / maxhp)))
    if hp > 0 and hpx == 0:
        hpx = 1
    s += fill_str(f, "trail", tp, H.TILE, H.FILL[0])
    s += fill_str(f, "hp", hpx, H.TILE, H.FILL[0])
    s += H.place(f, "boss/front0") + H.place(f, "boss/front1")
    ban = "rage" if state == "rage" else "normal"
    s += H.place(f, f"boss/banner_{ban}")
    s += H.place(f, f"boss/name_{boss}")
    s += H.place(f, f"boss/portrait_{boss}")
    s += H.place(f, f"boss/status_{'rage' if state == 'rage' else ('stun' if state == 'stun' else 'normal')}")
    cpx = round((H.CAST_FILL[2] - H.CAST_FILL[0]) * cast)
    s += fill_str(f, "cast", cpx, H.CAST_TILE, H.CAST_FILL[0])
    s += H.place(f, "boss/diamond_lit" if skill else "boss/diamond_idle")
    s += digits_str(f, f"{int(hp)}/{int(maxhp)}", 120, "boss/d", H.BOSS_X)
    return s


def hud_str(f, scores, me, time_sec, owners):
    """scores: {team: n}, owners: {temple/nw/ne/sw/se: team|none|contest}"""
    s = ""
    colors = {}
    for t in ("red", "blue", "green", "yellow"):
        s += H.place(f, f"hud/plate_{t}{'_me' if t == me else ''}")
    for t in ("red", "blue", "green", "yellow"):
        txt = str(int(scores.get(t, 0)))
        cx = H.PLATE_X[t] + 17 + (H.PLATE_W - 17) / 2
        s += digits_str(f, txt, cx, "hud/d")
    s += H.place(f, "hud/timer")
    m, sec = divmod(int(time_sec), 60)
    s += digits_str(f, f"{m:02d}:{sec:02d}", 150, "hud/t")
    return s


def preview(f, path, boss="talos", **kw):
    L = H.Layout(f)
    s = hud_str(f, {"red": 245, "blue": 198, "green": 160, "yellow": 131}, "red", 734,
                {"temple": "red", "nw": "yellow", "ne": "blue", "sw": "none", "se": "contest"})
    s += boss_str(f, boss, **kw) if kw else ""
    s += H.sp(H.TOTAL_W)
    img, cx = L.render(s)
    return img, s
