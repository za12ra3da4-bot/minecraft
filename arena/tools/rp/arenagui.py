"""연습장 고르기 화면 배경 (6줄 상자 176x222 → 2배 352x444) — 상자 제목 글리프로 창 전체를 덮는다

 칸 배치 (Skript a68 과 같아야 함)
   0줄: 머리띠 (제목)
   1~4줄 0~3열: 석영 투기장 카드 (아무 칸이나 누르면 입장)     1~4줄 5~8열: 용암 투기장 카드
   1~4줄 4열: VS 장식                                          5줄 45~48 / 50~53: 입장 단추, 49: 닫기
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

from shopgui import noise, stone, wood  # noqa: E402

K = 2
W, H = 176, 222
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
CACHE = os.path.join(TOOLS, ".cache", "arenagui")

CARDS = {
    "quartz": dict(x=7, title="석영 투기장", sub="지름 58칸 · 원형", tag="기본", feat="엄폐 기둥 · 관중석",
                   hi=(255, 226, 140), lo=(120, 86, 24), glow=(255, 236, 170), ink=(40, 30, 10)),
    "lava": dict(x=97, title="용암 투기장", sub="폭 112칸 · 팔각", tag="NEW", feat="용암 해자 · 대장간 탑",
                 hi=(255, 140, 50), lo=(120, 30, 10), glow=(255, 110, 40), ink=(30, 6, 4)),
}
CARD_Y, CARD_W, CARD_H = 35, 72, 72
SLOTS = {"quartz": [r * 9 + c for r in range(1, 5) for c in range(0, 4)] + [45, 46, 47, 48],
         "lava": [r * 9 + c for r in range(1, 5) for c in range(5, 9)] + [50, 51, 52, 53],
         "close": [49]}


def thumb(kind, size):
    """카드 그림: 투기장을 하늘에서 본 모습 (처음 한 번 그려서 캐시)"""
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, f"{kind}_{size}.png")
    if os.path.exists(f):
        return Image.open(f).convert("RGBA")
    import render as R
    if kind == "quartz":
        import pvparena as A
        v = A.build()
        v = np.where(v == A.P["barrier"], 0, v)
        pal = R.Palette(A.PAL)
        C, FL = A.C, A.FL
        im = R.render(v, pal, size, size, (C + 44, FL + 46, C + 50), (C, FL - 2, C), fov=52, ss=2, fog_dist=500)
    else:
        import pvparena2 as A
        v = A.build()
        v = np.where(v == A.P["barrier"], 0, v)
        pal = R.Palette(A.PAL)
        C, FL = A.C, A.FL
        im = R.render(v, pal, size, size, (C + 80, FL + 84, C + 90), (C, FL - 6, C), fov=52, ss=2, fog_dist=700, **A.DUSK)
    im.save(f)
    return im.convert("RGBA")


def grad_text(im, cx, y, t, size, cols, shadow, S):
    """세로 그라데이션 글씨 + 두꺼운 그림자 테"""
    f = ImageFont.truetype(FONT, int(size * S))
    d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), t, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad = 3 * S
    m = Image.new("L", (tw + pad * 2, th + pad * 2), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), t, font=f, fill=255)
    x0 = int(cx * S - tw / 2 - pad)
    y0 = int(y * S - pad)
    # 그림자 테
    edge = m.filter(ImageFilter.MaxFilter(5 if S >= 2 else 3))
    sh = Image.new("RGBA", m.size, shadow + (0,)); sh.putalpha(edge)
    im.alpha_composite(sh, (x0 + S, y0 + S))
    im.alpha_composite(sh, (x0, y0))
    g = np.zeros((m.height, m.width, 4), np.uint8)
    tt = np.linspace(0, 1, m.height)[:, None]
    for i in range(3):
        g[..., i] = (cols[0][i] * (1 - tt) + cols[1][i] * tt).astype(np.uint8)
    g[..., 3] = np.asarray(m)
    im.alpha_composite(Image.fromarray(g), (x0, y0))


def sparks(im, x0, y0, w, h, col, n, seed, S, rise=False):
    """작은 빛 알갱이 (석영 쪽 반짝임 · 용암 쪽 불똥)"""
    rng = np.random.default_rng(seed)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for _ in range(n):
        x = (x0 + rng.uniform(0, w)) * S
        y = (y0 + rng.uniform(0, h)) * S
        r = rng.uniform(0.3, 0.7) * S
        a = int(rng.uniform(140, 255))
        if rise:
            ld.line([(x, y), (x + rng.uniform(-0.6, 0.6) * S, y + r * 4)], fill=col + (a // 2,), width=max(1, int(r)))
            ld.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))
        else:
            L = r * 2.5
            ld.line([(x - L, y), (x + L, y)], fill=col + (a,), width=1)
            ld.line([(x, y - L), (x, y + L)], fill=col + (a,), width=1)
            ld.ellipse([x - r * 0.6, y - r * 0.6, x + r * 0.6, y + r * 0.6], fill=(255, 255, 255, a))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.2 * S)))
    im.alpha_composite(lay)


def build():
    S = K
    im = Image.fromarray(np.clip(stone(W * S, H * S, 31) * 0.8, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)

    def R(x0, y0, x1, y1, fill=None, outline=None, width=1):
        d.rectangle([x0 * S, y0 * S, x1 * S - 1, y1 * S - 1], fill=fill, outline=outline, width=width * S if width else 0)

    def text(x, y, t, size, fill, shadow=(10, 6, 4), anchor="la", bold=1):
        f = ImageFont.truetype(FONT, int(size * S))
        for dx in range(-bold, bold + 1):
            for dy in range(-bold, bold + 1):
                if dx or dy:
                    d.text((x * S + dx * S // 2 + S // 2, y * S + dy * S // 2 + S // 2), t, font=f, fill=shadow, anchor=anchor)
        d.text((x * S, y * S), t, font=f, fill=fill, anchor=anchor)

    # ── 상자 영역 배경: 왼쪽 금빛 · 오른쪽 용암 빛
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-30 * S, 20 * S, 95 * S, 140 * S], fill=(230, 190, 90, 90))
    gd.ellipse([82 * S, 20 * S, 210 * S, 140 * S], fill=(255, 80, 20, 120))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16 * S)))
    d = ImageDraw.Draw(im)

    # ── 머리띠: 반은 석영(흰 금) 반은 흑요석(붉은) — 가운데 교차한 검
    ban = np.zeros((34 * S, W * S, 3), np.float32)
    n = noise(W * S, 34 * S, 5, 17)
    xx = np.mgrid[0:34 * S, 0:W * S][1].astype(np.float32) / (W * S)
    yy = np.mgrid[0:34 * S, 0:W * S][0].astype(np.float32) / (34 * S)
    left = np.array((150, 128, 96), np.float32)
    right = np.array((92, 22, 14), np.float32)
    t = np.clip((xx - 0.38) / 0.24, 0, 1)[..., None]
    ban[:] = (left * (1 - t) + right * t) * (0.75 + 0.35 * n[..., None]) * (1.15 - 0.4 * yy[..., None])
    im.paste(Image.fromarray(np.clip(ban, 0, 255).astype(np.uint8)).convert("RGBA"), (0, 0))
    d = ImageDraw.Draw(im)
    R(0, 32, W, 34, fill=(214, 168, 70))
    R(0, 34, W, 35, fill=(70, 40, 10))
    # 양쪽 전설 무기 그림 (빛 번짐) + 가운데 금빛 제목
    from shopgui import art
    im.alpha_composite(art("thunder", 46 * S, 1.0, glow=(255, 240, 180)), (-4 * S, -8 * S))
    im.alpha_composite(art("phoenix", 46 * S, 1.0, glow=(255, 120, 40), rot=90), (134 * S, -8 * S))
    d = ImageDraw.Draw(im)
    grad_text(im, W / 2, 3.5, "PvP 연습장", 15, ((255, 248, 210), (232, 170, 60)), (40, 16, 4), S)
    d = ImageDraw.Draw(im)
    # 제목 아래 장식 줄 + 마름모
    for sx in (-1, 1):
        d.line([((W / 2 + sx * 10) * S, 25 * S), ((W / 2 + sx * 44) * S, 25 * S)], fill=(214, 168, 70), width=S)
        d.polygon([((W / 2 + sx * 46) * S, 23 * S), ((W / 2 + sx * 48) * S, 25 * S), ((W / 2 + sx * 46) * S, 27 * S), ((W / 2 + sx * 44) * S, 25 * S)], fill=(255, 220, 120))
    text(W / 2, 22.3, "투기장 선택", 5.5, (255, 236, 200), shadow=(40, 16, 4), anchor="ma", bold=1)

    # ── 카드
    for key, cd in CARDS.items():
        x0 = cd["x"]
        th = thumb(key, CARD_W * S)
        # 아래쪽 어둡게 (이름 자리)
        g = np.zeros((CARD_H * S, CARD_W * S, 4), np.uint8)
        ramp = np.clip((np.arange(CARD_H * S) / (CARD_H * S) - 0.55) / 0.45, 0, 1)
        g[..., 3] = (ramp[:, None] * 220).astype(np.uint8)
        th.alpha_composite(Image.fromarray(g))
        top = np.zeros((CARD_H * S, CARD_W * S, 4), np.uint8)
        ramp2 = np.clip(1 - np.arange(CARD_H * S) / (CARD_H * S * 0.22), 0, 1)
        top[..., 3] = (ramp2[:, None] * 140).astype(np.uint8)
        th.alpha_composite(Image.fromarray(top))
        # 빛나는 테두리
        halo = Image.new("RGBA", ((CARD_W + 12) * S, (CARD_H + 12) * S), (0, 0, 0, 0))
        hd = ImageDraw.Draw(halo)
        hd.rectangle([4 * S, 4 * S, (CARD_W + 8) * S, (CARD_H + 8) * S], outline=cd["glow"] + (200,), width=3 * S)
        im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(3 * S)), ((x0 - 6) * S, (CARD_Y - 6) * S))
        im.alpha_composite(th, (x0 * S, CARD_Y * S))
        d = ImageDraw.Draw(im)
        R(x0, CARD_Y, x0 + CARD_W, CARD_Y + CARD_H, outline=cd["lo"], width=1)
        R(x0 + 1, CARD_Y + 1, x0 + CARD_W - 1, CARD_Y + CARD_H - 1, outline=cd["hi"], width=1)
        for (gx, gy) in ((x0 + 2, CARD_Y + 2), (x0 + CARD_W - 3, CARD_Y + 2), (x0 + 2, CARD_Y + CARD_H - 3), (x0 + CARD_W - 3, CARD_Y + CARD_H - 3)):
            d.rectangle([(gx - 1) * S, (gy - 1) * S, (gx + 2) * S - 1, (gy + 2) * S - 1], fill=cd["hi"])
        # 이름 + 설명
        text(x0 + CARD_W / 2, CARD_Y + CARD_H - 21, cd["title"], 9, cd["hi"], shadow=cd["ink"], anchor="ma")
        text(x0 + CARD_W / 2, CARD_Y + CARD_H - 9, cd["sub"], 5.5, (235, 225, 210), shadow=(0, 0, 0), anchor="ma")
        # 아래 설명 띠 위에 특징 한 줄 (어두운 띠)
        strip = Image.new("RGBA", ((CARD_W - 4) * S, 8 * S), (10, 6, 6, 170))
        im.alpha_composite(strip, ((x0 + 2) * S, (CARD_Y + CARD_H - 31) * S))
        d = ImageDraw.Draw(im)
        text(x0 + CARD_W / 2, CARD_Y + CARD_H - 30.2, cd["feat"], 5, cd["glow"], shadow=(0, 0, 0), anchor="ma", bold=0)
        if key == "quartz":
            sparks(im, x0 + 2, CARD_Y + 12, CARD_W - 4, CARD_H - 30, (255, 250, 220), 16, 3, S)
        else:
            sparks(im, x0 + 2, CARD_Y + 12, CARD_W - 4, CARD_H - 30, (255, 150, 50), 26, 4, S, rise=True)
        d = ImageDraw.Draw(im)
        # 꼬리표 (기본 / NEW)
        tw = 15 if cd["tag"] == "NEW" else 13
        tx = x0 + CARD_W - tw - 3
        d.polygon([(tx * S, (CARD_Y + 4) * S), ((tx + tw) * S, (CARD_Y + 4) * S), ((tx + tw) * S, (CARD_Y + 12) * S),
                   (tx * S, (CARD_Y + 12) * S), ((tx - 3) * S, (CARD_Y + 8) * S)], fill=cd["lo"], outline=cd["hi"])
        text(tx + tw / 2, CARD_Y + 5.3, cd["tag"], 5.5, (255, 250, 230), shadow=cd["ink"], anchor="ma", bold=0)

    # ── 가운데 VS 기둥
    R(79, CARD_Y, 97, CARD_Y + CARD_H, fill=(18, 12, 14))
    col = np.linspace(0, 1, CARD_H * S)[:, None]
    stripe = np.zeros((CARD_H * S, 18 * S, 4), np.uint8)
    stripe[..., 0] = (255 * col + 255 * (1 - col)).astype(np.uint8)[:, :1].repeat(18 * S, 1) * 0 + 255
    stripe[..., 1] = (230 * (1 - col) + 120 * col).astype(np.uint8)[:, :1].repeat(18 * S, 1)
    stripe[..., 2] = (150 * (1 - col) + 40 * col).astype(np.uint8)[:, :1].repeat(18 * S, 1)
    xs = np.abs(np.arange(18 * S) - 9 * S + 0.5)[None, :]
    stripe[..., 3] = np.clip(255 - xs * 70 / S, 0, 255).astype(np.uint8).repeat(CARD_H * S, 0) // 3
    im.alpha_composite(Image.fromarray(stripe), (79 * S, CARD_Y * S))
    d = ImageDraw.Draw(im)
    vy = CARD_Y + CARD_H / 2
    d.polygon([(88 * S, (vy - 12) * S), (96 * S, vy * S), (88 * S, (vy + 12) * S), (80 * S, vy * S)], fill=(40, 22, 18), outline=(214, 168, 70), width=S)
    text(88, vy - 5, "VS", 7.5, (255, 220, 120), shadow=(60, 20, 0), anchor="ma")

    # ── 5줄: 입장 단추 2개 + 닫기
    for key, cd in CARDS.items():
        x0 = cd["x"]
        y0 = 107
        btn = np.zeros((18 * S, CARD_W * S, 3), np.float32)
        yy = np.linspace(0, 1, 18 * S)[:, None, None]
        btn[:] = np.array(cd["hi"], np.float32) * (1 - yy) * 0.9 + np.array(cd["lo"], np.float32) * yy
        im.paste(Image.fromarray(np.clip(btn, 0, 255).astype(np.uint8)).convert("RGBA"), (x0 * S, y0 * S))
        d = ImageDraw.Draw(im)
        R(x0, y0, x0 + CARD_W, y0 + 18, outline=(30, 16, 6), width=1)
        R(x0 + 1, y0 + 1, x0 + CARD_W - 1, y0 + 2, fill=(255, 250, 230))
        cx_ = x0 + 13
        d.polygon([((cx_ - 3) * S, (y0 + 5) * S), ((cx_ + 4) * S, (y0 + 9) * S), ((cx_ - 3) * S, (y0 + 13) * S)], fill=(255, 255, 255), outline=cd["ink"])
        text(x0 + CARD_W / 2 + 5, y0 + 4.5, "입장하기", 8, (255, 255, 250), shadow=cd["ink"], anchor="ma")
    # 닫기 (X)
    R(79, 107, 97, 125, fill=(60, 20, 20), outline=(214, 168, 70))
    d.line([(83 * S, 111 * S), (93 * S, 121 * S)], fill=(255, 220, 200), width=2 * S)
    d.line([(93 * S, 111 * S), (83 * S, 121 * S)], fill=(255, 220, 200), width=2 * S)

    # ── 테두리
    R(0, 0, W, 126, outline=(24, 14, 8), width=1)
    R(1, 1, W - 1, 125, outline=(214, 168, 70), width=1)
    for (gx, gy) in ((4, 4), (W - 5, 4)):
        d.ellipse([(gx - 3) * S, (gy - 3) * S, (gx + 3) * S, (gy + 3) * S], fill=(214, 168, 70))
        d.ellipse([(gx - 2) * S, (gy - 2) * S, (gx + 2) * S, (gy + 2) * S], fill=(190, 30, 50))

    # ── 플레이어 가방 (아래)
    parch = np.zeros((96 * S, W * S, 3), np.float32)
    n2 = noise(W * S, 96 * S, 6, 23)
    parch[:] = np.array((44, 34, 30), np.float32)[None, None] * (0.85 + 0.3 * n2[..., None])
    im.paste(Image.fromarray(np.clip(parch, 0, 255).astype(np.uint8)).convert("RGBA"), (0, 126 * S))
    d = ImageDraw.Draw(im)
    R(0, 126, W, 127, fill=(214, 168, 70))
    R(0, 126, W, H, outline=(24, 14, 8), width=1)

    def slot(x, y):
        R(x, y, x + 18, y + 18, fill=(90, 70, 52))
        R(x, y, x + 17, y + 1, fill=(30, 22, 18))
        R(x, y, x + 1, y + 17, fill=(30, 22, 18))
        R(x + 1, y + 1, x + 17, y + 17, fill=(58, 46, 40))
    for r in range(3):
        for c in range(9):
            slot(7 + 18 * c, 139 + 18 * r)
    for c in range(9):
        slot(7 + 18 * c, 197)
    text(8, 129.5, "가방", 6, (230, 200, 150), bold=0)
    return im


def export(f, H):
    """hud_build 의 글꼴(f)에 2x2 조각 글리프 추가 → f.glyphs['gui/arena']"""
    im = build()
    keys = []
    for r in range(2):
        for c in range(2):
            tile = im.crop((c * 176, r * 222, (c + 1) * 176, (r + 1) * 222)).copy()
            px = tile.load()
            if px[175, 0][3] == 0:
                px[175, 0] = (0, 0, 0, 1)
            ch = chr(f.next); f.next += 1
            fname = f"font/gui_arena_{r}{c}.png"
            f.files[fname] = tile
            f.providers.append({"type": "bitmap", "file": f"{H.NS}:{fname}", "height": 111, "ascent": 13 - 111 * r, "chars": [ch]})
            keys.append(ch)
    s = H.sp(-8) + keys[0] + H.sp(-1) + keys[1] + H.sp(-177) + keys[2] + H.sp(-1) + keys[3] + H.sp(-169)
    f.glyphs["gui/arena"] = dict(char=s, adv=0, x=0, y=0, widget="hud")


def preview(path):
    """게임 화면처럼: 배경 + 칸 위 아이템 자리 표시"""
    im = build()
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    bg.convert("RGB").resize((im.width * 2, im.height * 2), Image.NEAREST).save(path)


if __name__ == "__main__":
    preview(sys.argv[1] if len(sys.argv) > 1 else "gui_arena.png")
