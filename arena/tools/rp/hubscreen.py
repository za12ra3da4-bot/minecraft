"""허브 오락기 화면 로고 — 오락실 간판 글씨 (픽셀 글꼴 · 두꺼운 검은 테 · 입체 그림자 · 위→아래 색 번짐)

 글꼴 bg:hubscr (text_display 의 text 에 font:"bg:hubscr") — 글자 하나가 로고 그림 하나
   \\ue000 신화쟁탈전 · \\ue001 PvP 온리소드 · \\ue002 준비 중
 픽셀 글꼴: 갈무리11 Bold (SIL OFL 1.1, fonts/galmuri/OFL.txt)
 그림 1픽셀 = 글꼴 0.5픽셀 (bitmap height = 그림 높이 / 2) → Skript 에서 크기를 맞춰 화면을 채움
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "galmuri", "Galmuri11-Bold.ttf")
NS = "bg"

# 이름 → (글자, 큰 줄들, 작은 줄, 위→아래 색, 입체 색, 테 색)
LOGOS = [
    ("myth", "", ["신화", "쟁탈전"], "4팀 점령전 · 보스",
     [(255, 255, 255), (150, 232, 255), (60, 140, 255), (34, 64, 210)], (14, 30, 120), (8, 10, 38)),
    ("pvp", "", ["PvP", "온리소드"], "검 하나로 승부",
     [(255, 255, 236), (255, 196, 120), (255, 70, 60), (196, 16, 40)], (104, 8, 20), (32, 4, 8)),
    ("cops", "", ["경찰과", "도둑"], "시참 · 밤 대도시",
     [(255, 255, 255), (150, 200, 255), (70, 110, 255), (220, 40, 60)], (40, 10, 70), (10, 8, 30)),
    ("soon", "", ["준비 중"], "COMING SOON",
     [(255, 240, 255), (244, 160, 255), (178, 80, 244), (110, 40, 190)], (54, 12, 96), (22, 4, 40)),
]


def _mask(text, size=11):
    f = ImageFont.truetype(FONT, size)
    l, t, r, b = f.getbbox(text)
    im = Image.new("L", (r - l + 2, b - t + 2), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    d.text((1 - l, 1 - t), text, font=f, fill=255)
    return np.array(im) > 127


def _shift(m, dx, dy):
    out = np.zeros_like(m)
    h, w = m.shape
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = m[max(-dy, 0):h - max(dy, 0), max(-dx, 0):w - max(dx, 0)]
    return out


def _dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + 1:
                out |= _shift(m, dx, dy)
    return out


def _grad(stops, t):
    n = len(stops) - 1
    i = min(int(t * n), n - 1)
    k = t * n - i
    a, b = stops[i], stops[i + 1]
    return tuple(int(a[j] + (b[j] - a[j]) * k) for j in range(3))


def logo(lines, sub, cols, ext, ink):
    S = 2                                   # 글꼴 1픽셀 = 그림 2픽셀
    PAD = 6
    big = [np.kron(_mask(t), np.ones((S, S), bool)) for t in lines]
    small = _mask(sub)
    W = max([m.shape[1] for m in big] + [small.shape[1]]) + PAD * 2
    gap = 4
    Hh = sum(m.shape[0] for m in big) + gap * (len(big) - 1) + 3 + small.shape[0] + PAD * 2
    title = np.zeros((Hh, W), bool)
    y = PAD
    line_rows = []
    for m in big:
        x = (W - m.shape[1]) // 2
        title[y:y + m.shape[0], x:x + m.shape[1]] |= m
        line_rows.append((y, y + m.shape[0]))
        y += m.shape[0] + gap
    sub_y = y + 3
    sm = np.zeros((Hh, W), bool)
    x = (W - small.shape[1]) // 2
    sm[sub_y:sub_y + small.shape[0], x:x + small.shape[1]] |= small
    # 입체 (오른쪽 아래로 3픽셀) · 바깥 검은 테 2픽셀
    extr = np.zeros_like(title)
    for k in range(1, 4):
        extr |= _shift(title, k // 2, k)
    body = title | extr
    outline = _dilate(body, 2) & ~body
    px = np.zeros((Hh, W, 4), np.uint8)
    px[outline] = ink + (255,)
    px[extr & ~title] = ext + (255,)
    # 채우기: 줄마다 위→아래 색 번짐 + 윗면 빛 (위쪽이 비어 있는 칸은 흰빛)
    for y0, y1 in line_rows:
        for yy in range(y0, y1):
            t = (yy - y0) / max(1, y1 - y0 - 1)
            row = title[yy]
            px[yy][row] = _grad(cols, t) + (255,)
    top = title & ~_shift(title, 0, 1)
    px[top] = (255, 255, 255, 255)
    # 작은 줄: 진한 글자 + 얇은 밝은 테 (노랑 화면 위에서 또렷하게)
    sub_out = _dilate(sm, 1) & ~sm & ~body & ~outline
    px[sub_out] = (255, 250, 230, 200)
    px[sm] = ink + (255,)
    im = Image.fromarray(px, "RGBA")
    if im.getpixel((W - 1, 0))[3] == 0:
        im.putpixel((W - 1, 0), (0, 0, 0, 1))      # 오른쪽 빈칸이 잘려 가운데가 어긋나지 않게
    return im


def build():
    return {key: (ch, logo(lines, sub, cols, ext, ink)) for key, ch, lines, sub, cols, ext, ink in LOGOS}


# 탭 목록 · 이름표 앞 배지 (팀 prefix 에 font:"bg:hubscr") — 4배 해상도 (글꼴 높이 10)
#  반짝이는 그라데이션 알약 · 진한 테두리 · 윗면 빛 · 왼쪽 아이콘 · 외곽선 + 그림자 있는 흰 픽셀 글씨 (갈무리11 Bold ×3)
BADGES = [
    ("hub", "\ue010", "허브", "star", (90, 210, 255), (20, 110, 200), (8, 40, 90)),
    ("myth", "\ue011", "신화쟁탈전", "crown", (255, 214, 90), (220, 130, 20), (90, 46, 6)),
    ("os", "\ue012", "온리소드", "sword", (255, 110, 110), (200, 20, 40), (80, 6, 14)),
    ("cop", "\ue013", "경찰", "shield", (120, 160, 255), (30, 60, 210), (10, 20, 90)),
    ("thief", "\ue014", "도둑", "mask", (255, 90, 90), (150, 10, 30), (50, 4, 10)),
    ("kdwait", "\ue015", "경도", "siren", (190, 140, 255), (100, 50, 210), (40, 14, 90)),
]
BH = 40                          # 배지 그림 높이 (글꼴 높이 10 × 4)


def _icon(d, kind, x, y, s):
    W = (255, 255, 255, 255)
    if kind == "star":
        pts = []
        for i in range(10):
            a = math.radians(-90 + i * 36)
            rr = s / 2 if i % 2 == 0 else s / 4.6
            pts.append((x + s / 2 + math.cos(a) * rr, y + s / 2 + math.sin(a) * rr))
        d.polygon(pts, fill=(255, 240, 120, 255), outline=(120, 80, 0, 255))
    elif kind == "crown":
        d.polygon([(x, y + s * .85), (x, y + s * .3), (x + s * .25, y + s * .55), (x + s * .5, y + s * .15),
                   (x + s * .75, y + s * .55), (x + s, y + s * .3), (x + s, y + s * .85)], fill=(255, 236, 120, 255), outline=(110, 60, 0, 255))
        for cx in (.0, .5, 1.0):
            d.ellipse((x + s * cx - 3, y + s * (.3 if cx != .5 else .15) - 3, x + s * cx + 3, y + s * (.3 if cx != .5 else .15) + 3), fill=(255, 80, 80, 255))
    elif kind == "sword":
        d.line((x + 4, y + s - 4, x + s - 3, y + 3), fill=(220, 245, 255, 255), width=6)
        d.line((x + 4, y + s - 4, x + s - 3, y + 3), fill=(120, 220, 255, 255), width=2)
        d.line((x + 2, y + s * .55, x + s * .45, y + s - 2), fill=(255, 210, 80, 255), width=5)
        d.ellipse((x, y + s - 8, x + 7, y + s - 1), fill=(255, 210, 80, 255))
    elif kind == "shield":
        d.polygon([(x + s / 2, y), (x + s, y + s * .18), (x + s * .88, y + s * .7), (x + s / 2, y + s), (x + s * .12, y + s * .7), (x, y + s * .18)],
                  fill=(255, 220, 90, 255), outline=(110, 70, 0, 255))
        d.polygon([(x + s / 2, y + s * .28), (x + s * .62, y + s * .5), (x + s / 2, y + s * .72), (x + s * .38, y + s * .5)], fill=(40, 70, 200, 255))
    elif kind == "mask":
        d.rounded_rectangle((x, y + s * .25, x + s, y + s * .7), radius=8, fill=(20, 20, 26, 255))
        d.ellipse((x + s * .15, y + s * .36, x + s * .42, y + s * .6), fill=W)
        d.ellipse((x + s * .58, y + s * .36, x + s * .85, y + s * .6), fill=W)
    elif kind == "siren":
        d.rectangle((x + 2, y + s * .78, x + s - 2, y + s), fill=(40, 40, 50, 255))
        d.pieslice((x + 4, y + s * .2, x + s - 4, y + s * 1.3), 180, 360, fill=(255, 60, 60, 255))
        d.pieslice((x + s / 2, y + s * .2, x + s - 4, y + s * 1.3), 270, 360, fill=(70, 120, 255, 255))
        d.line((x + s * .3, y + s * .45, x + s * .36, y + s * .35), fill=W, width=3)


def badge(text, kind, light, base, dark):
    f = ImageFont.truetype(FONT, 11)
    l, t, r, b = f.getbbox(text)
    tm = Image.new("L", (r - l + 2, b - t + 2), 0)
    td = ImageDraw.Draw(tm)
    td.fontmode = "1"
    td.text((1 - l, 1 - t), text, font=f, fill=255)
    tm = tm.resize((tm.size[0] * 3, tm.size[1] * 3), Image.NEAREST)
    icon = 30
    w = 10 + icon + 6 + tm.size[0] + 12
    im = Image.new("RGBA", (w, BH), (0, 0, 0, 0))
    # 알약 모양: 그림자 → 진한 테두리 → 위→아래 그라데이션 → 윗면 빛
    m = Image.new("L", (w, BH), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, BH - 3), radius=13, fill=255)
    sh = Image.new("RGBA", (w, BH), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((0, 2, w - 1, BH - 1), radius=13, fill=(0, 0, 0, 140))
    im.alpha_composite(sh)
    grad = Image.new("RGBA", (w, BH))
    gp = grad.load()
    for yy in range(BH):
        tt = yy / (BH - 3)
        c = tuple(int(light[i] + (base[i] - light[i]) * min(1, tt * 1.3)) for i in range(3))
        for xx in range(w):
            gp[xx, yy] = c + (255,)
    edge = Image.new("RGBA", (w, BH), dark + (255,))
    im.paste(edge, (0, 0), m)
    inner = Image.new("L", (w, BH), 0)
    ImageDraw.Draw(inner).rounded_rectangle((3, 3, w - 4, BH - 6), radius=10, fill=255)
    im.paste(grad, (0, 0), inner)
    shine = Image.new("RGBA", (w, BH), (0, 0, 0, 0))
    ImageDraw.Draw(shine).rounded_rectangle((7, 5, w - 8, 13), radius=4, fill=(255, 255, 255, 90))
    im.alpha_composite(shine)
    d = ImageDraw.Draw(im)
    _icon(d, kind, 9, (BH - 3 - icon) // 2, icon)
    # 글씨: 진한 외곽선 3 · 그림자 · 흰 글씨
    tx, ty = 10 + icon + 6, (BH - 3 - tm.size[1]) // 2 + 1
    arr = np.array(tm) > 0
    out = np.zeros_like(arr)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dx * dx + dy * dy <= 10:
                out |= np.roll(np.roll(arr, dy, 0), dx, 1)
    pad = Image.new("RGBA", tm.size, (0, 0, 0, 0))
    pad.putalpha(Image.fromarray((out * 255).astype("uint8")))
    ol = Image.new("RGBA", tm.size, dark + (255,))
    im.paste(ol, (tx, ty + 2), pad)
    im.paste(ol, (tx, ty), pad)
    im.paste(Image.new("RGBA", tm.size, (255, 255, 255, 255)), (tx, ty), tm)
    return im


def export(pack):
    provs = []
    for key, ch, text, kind, light, base, dark in BADGES:
        im = badge(text, kind, light, base, dark)
        pack.png(f"assets/{NS}/textures/font/badge_{key}.png", im)
        provs.append({"type": "bitmap", "file": f"{NS}:font/badge_{key}.png", "height": 10, "ascent": 8, "chars": [ch]})
    for key, (ch, im) in build().items():
        pack.png(f"assets/{NS}/textures/font/hubscr_{key}.png", im)
        h = im.size[1] // 2
        provs.append({"type": "bitmap", "file": f"{NS}:font/hubscr_{key}.png", "height": h, "ascent": h, "chars": [ch]})
    pack.put(f"assets/{NS}/font/hubscr.json", {"providers": provs})


def sizes():
    """Skript 용: 로고별 (글꼴 픽셀 폭, 높이)"""
    return {key: (im.size[0] / 2, im.size[1] / 2) for key, (ch, im) in build().items()}


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "hubscreen.png"
    ims = [im for _, im in build().values()]
    W = sum(i.size[0] for i in ims) + 20 * (len(ims) + 1)
    H = max(i.size[1] for i in ims) + 40
    bg = Image.new("RGBA", (W, H), (255, 214, 80, 255))
    x = 20
    for i in ims:
        bg.alpha_composite(i, (x, 20))
        x += i.size[0] + 20
    bg.resize((W * 5, H * 5), Image.NEAREST).save(out)
    print(sizes())
