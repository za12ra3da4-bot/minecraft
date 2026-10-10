"""허브 오락기 화면 로고 — 오락실 간판 글씨 (픽셀 글꼴 · 두꺼운 검은 테 · 입체 그림자 · 위→아래 색 번짐)

 글꼴 bg:hubscr (text_display 의 text 에 font:"bg:hubscr") — 글자 하나가 로고 그림 하나
   \\ue000 신화쟁탈전 · \\ue001 PvP 온리소드 · \\ue002 준비 중
 픽셀 글꼴: 갈무리11 Bold (SIL OFL 1.1, fonts/galmuri/OFL.txt)
 그림 1픽셀 = 글꼴 0.5픽셀 (bitmap height = 그림 높이 / 2) → Skript 에서 크기를 맞춰 화면을 채움
"""
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


def export(pack):
    provs = []
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
