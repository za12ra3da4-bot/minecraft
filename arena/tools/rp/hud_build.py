"""HUD/보스바 글리프 생성 + 합성 규칙 (파이썬판)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from PIL import Image

import hud as H
from bossdata import BOSSES, EXTRA_BOSSES

PORTRAITS = os.path.join(os.path.dirname(HERE), ".cache", "portraits")


def gui_panel(f):
    """상점 화면 배경 (쪽마다 한 장, 6줄 상자 176x222 · 텍스쳐 2배 352x444)
       글꼴 그림은 한 장이 256 픽셀을 넘으면 안 그려지므로 2x2 조각(각 176x222 텍셀 = 화면 88x111)
       제목 위치 (8, 6) · 기본 글꼴 ascent 7 → 위 조각 ascent 13, 아래 조각 13-111"""
    import shopgui
    for page in shopgui.PAGES:
        im = shopgui.build(page)
        keys = []
        for r in range(2):
            for c in range(2):
                tile = im.crop((c * 176, r * 222, (c + 1) * 176, (r + 1) * 222)).copy()
                px = tile.load()
                if px[175, 0][3] == 0:
                    px[175, 0] = (0, 0, 0, 1)
                ch = chr(f.next); f.next += 1
                fname = f"font/gui_shop{page}_{r}{c}.png"
                f.files[fname] = tile
                f.providers.append({"type": "bitmap", "file": f"{H.NS}:{fname}", "height": 111, "ascent": 13 - 111 * r, "chars": [ch]})
                keys.append(ch)
        s = H.sp(-8) + keys[0] + H.sp(-1) + keys[1] + H.sp(-177) + keys[2] + H.sp(-1) + keys[3] + H.sp(-169)
        f.glyphs[f"gui/shop{page}"] = dict(char=s, adv=0, x=0, y=0, widget="hud")
        if page == 1:
            f.glyphs["gui/shop"] = dict(char=s, adv=0, x=0, y=0, widget="hud")


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
    H.point_badges(f)
    H.point_fills(f)
    for bid, b in BOSSES.items():
        H.label(f, f"boss/name_{bid}", b["name"], "name")
        p = os.path.join(PORTRAITS, f"{bid}.png")
        if os.path.exists(p):
            img = Image.open(p)
        else:
            img = Image.new("RGBA", (64, 64), (60, 40, 30, 255))
        H.portrait(f, bid, img)
    gui_panel(f)
    # 이벤트 보스 (네메시스) — 맨 뒤에 덧붙여서 기존 글리프 번호가 바뀌지 않게
    for bid, b in EXTRA_BOSSES.items():
        H.label(f, f"boss/name_{bid}", b["name"], "name")
        p = os.path.join(PORTRAITS, f"{bid}.png")
        if os.path.exists(p):
            img = Image.open(p)
        else:
            img = Image.new("RGBA", (64, 64), (60, 30, 90, 255))
        H.portrait(f, bid, img)
    # 연습장 고르기 화면 (맨 뒤에 덧붙임 — 기존 글리프 번호 유지)
    import arenagui
    arenagui.export(f, H)
    # 허브 오락기 화면 로고 (따로 글꼴 bg:hubscr — hud 글리프 번호와 무관)
    import hubscreen
    hubscreen.export(pack)
    import kditems
    kditems.export(pack)
    # 화면 칸용 투명 아이템 (이름 · 설명만 보이고 그림은 없음)
    pack.put(f"assets/{H.NS}/items/gui/blank.json", {"model": {"type": "minecraft:empty"}})
    # 파일
    for name, img in f.files.items():
        pack.png(f"assets/{H.NS}/textures/{name}", img)
    pack.put(f"assets/{H.NS}/font/hud.json", H.build_font_json(f))
    # 기본 글꼴에도 HUD 글리프(사용자 영역 문자)를 연결 → 상자 제목 같은 일반 글자에서도 그림이 나온다 (글꼴 지정 불필요)
    pack.put("assets/minecraft/font/default.json", {"providers": [
        {"type": "reference", "id": f"{H.NS}:hud"},
        {"type": "reference", "id": f"{H.NS}:title"},
        {"type": "reference", "id": f"{H.NS}:fx"},
        {"type": "reference", "id": "minecraft:include/space"},
        {"type": "reference", "id": "minecraft:include/default", "filter": {"uniform": False}},
        {"type": "reference", "id": "minecraft:include/unifont"}]})
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
    for p in H.PT_ORDER:
        o = owners.get(p, "none")
        if o in ("none", "contest"):
            s += H.place(f, f"hud/pt_{p}_neutral")
        else:
            s += H.place(f, f"hud/pt_{p}_{o}{'_me' if o == me else ''}")
        if o == "contest":
            s += H.place(f, "hud/pt_contest", H.PT_X[p])
    s += H.place(f, "hud/timer")
    m, sec = divmod(int(time_sec), 60)
    s += digits_str(f, f"{m:02d}:{sec:02d}", 150, "hud/t")
    return s


def preview(f, path, boss="talos", **kw):
    L = H.Layout(f)
    s = hud_str(f, {"red": 245, "blue": 198, "green": 160, "yellow": 131}, "red", 734,
                {"temple": "blue", "ares": "red", "athena": "yellow", "hermes": "contest", "demeter": "none"})
    s += boss_str(f, boss, **kw) if kw else ""
    s += H.sp(H.TOTAL_W)
    img, cx = L.render(s)
    return img, s
