"""화면 상단 HUD (팀 점수 스트립) + 보스 체력바 — 폰트 글리프

 보스바(바닐라) 한 개의 '이름' 자리에 글리프를 겹쳐 그린다.
  - 바닐라 막대는 white 색상 스프라이트를 투명하게 바꿔 숨긴다.
  - 모든 글리프는 2배 해상도(텍스처 2px = GUI 1px), 오른쪽 끝 열에 알파 1 점을 찍어
    글자 폭(advance) = 너비 + 1 로 고정 → 위치 계산이 정확해진다.
  - 이름 줄 y = 3 (첫 보스바).  글리프 top = 3 + 7 - ascent  →  ascent = 10 - top

 출력: 리소스팩 파일 + hud_glyphs.json (Skript 데이터 생성용)
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from gfx import *
import gfx

NS = "bg"
FONT_ID = f"{NS}:hud"
LINE_Y = 3
HUD_TOP = 1
BOSS_TOP = 22
TOTAL_W = 300            # 합성 폭 (가운데 정렬 기준)
BOSS_W = 240
BOSS_X = (TOTAL_W - BOSS_W) // 2

GOLD = [(0, (255, 238, 170)), (0.35, (236, 186, 84)), (0.7, (176, 112, 36)), (1, (110, 64, 18))]
GOLD_DARK = (40, 22, 6)


class Font:
    def __init__(self):
        self.next = 0xE000
        self.glyphs = {}        # key → dict(char, adv, img, x, y, widget)
        self.providers = []
        self.files = {}

    def add(self, key, img, x, y, widget):
        """img: RGBA (2배 해상도), x,y: 위젯 기준 GUI 좌표"""
        w, h = img.size
        if w % 2:
            img = img.crop((0, 0, w + 1, h)); w += 1
        if h % 2:
            im2 = Image.new("RGBA", (w, h + 1), (0, 0, 0, 0)); im2.paste(img, (0, 0)); img = im2; h += 1
        assert h <= 256, (key, img.size)
        if w > 256:
            # 넓은 그림은 256 이하 조각으로 나눈다
            n = (w + 255) // 256
            cw = ((w // n) + 1) // 2 * 2
            parts = []
            for i in range(n):
                sub = img.crop((i * cw, 0, min(w, (i + 1) * cw), h))
                k = f"{key}_p{i}"
                self.add(k, sub, x + i * cw / 2, y, widget)
                parts.append(k)
            self.glyphs[key] = dict(parts=parts, widget=widget)
            return None
        img = img.copy()
        px = img.load()
        r, g, b_, a = px[w - 1, 0]
        if a == 0:
            px[w - 1, 0] = (0, 0, 0, 1)
        y = int(round(y))
        top = (HUD_TOP if widget == "hud" else BOSS_TOP) + y
        hg = h // 2
        ascent = 10 - top
        if ascent > hg:
            raise ValueError(f"{key}: ascent {ascent} > height {hg}")
        ch = chr(self.next); self.next += 1
        adv = w // 2 + 1
        fname = f"font/{key}.png"
        self.files[fname] = img
        self.providers.append({"type": "bitmap", "file": f"{NS}:{fname}", "height": hg, "ascent": ascent, "chars": [ch]})
        self.glyphs[key] = dict(char=ch, adv=adv, x=x, y=y, widget=widget, img=img)
        return ch


# ─────────────────────────────────────────────────────────────────────────────
#  보스 위젯 아트  (GUI 좌표 240 x 44)
# ─────────────────────────────────────────────────────────────────────────────
S = 2                       # 텍스처 배율
LC = (18, 22); RC = (222, 22); CR = 17        # 원 중심/반지름
BAR = (30, 16, 210, 29)     # 막대 바깥
FILL = (33, 19, 207, 26)    # 채움 영역 (174 x 7)
FILL_W = FILL[2] - FILL[0]
TILE = 29                   # 채움 타일 폭 (6 타일 = 174)
BAN = (56, 0, 184, 17)      # 배너 (128 x 17)
CAST = (46, 33, 194, 37)    # 시전 게이지 줄
CAST_FILL = (50, 34, 190, 36)
CAST_TILE = 35              # 4 타일 = 140


def canvas(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def gold_ring(img, cx, cy, r_out, r_in, ox=0, oy=0, rivets=8, seed=0):
    """금 테두리 원 (금속 그라데이션 + 리벳)"""
    W, H = img.size
    ss = 4
    big = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = ((cx - ox) * S * ss, (cy - oy) * S * ss)
    ro = r_out * S * ss; ri = r_in * S * ss
    # 어두운 외곽
    d.ellipse([c[0] - ro - 2 * ss, c[1] - ro - 2 * ss, c[0] + ro + 2 * ss, c[1] + ro + 2 * ss], fill=GOLD_DARK + (255,))
    # 금속 링 (세로 그라데이션 마스크)
    m = Image.new("L", big.size, 0)
    md = ImageDraw.Draw(m)
    md.ellipse([c[0] - ro, c[1] - ro, c[0] + ro, c[1] + ro], fill=255)
    md.ellipse([c[0] - ri, c[1] - ri, c[0] + ri, c[1] + ri], fill=0)
    g = grad_v(big.size[0], big.size[1], [(0, (255, 240, 180)), (max(0, (c[1] - ro) / big.size[1]), (255, 236, 160)),
                                           (min(1, c[1] / big.size[1]), (214, 158, 60)), (min(1, (c[1] + ro) / big.size[1]), (120, 70, 20)), (1, (90, 50, 14))])
    ring = fill_mask(m, g)
    big.alpha_composite(ring)
    # 안쪽 어두운 선 + 바깥 하이라이트
    d.ellipse([c[0] - ri - ss, c[1] - ri - ss, c[0] + ri + ss, c[1] + ri + ss], outline=(60, 34, 8, 255), width=int(1.5 * ss))
    d.arc([c[0] - ro + ss, c[1] - ro + ss, c[0] + ro - ss, c[1] + ro - ss], 200, 340, fill=(255, 250, 220, 200), width=ss)
    # 리벳
    for k in range(rivets):
        a = k / rivets * 2 * math.pi + math.pi / rivets
        rr = (ro + ri) / 2
        px, py = c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr
        s = 1.3 * S * ss
        d.ellipse([px - s, py - s, px + s, py + s], fill=(90, 52, 14, 255))
        d.ellipse([px - s * 0.6 - ss * 0.5, py - s * 0.6 - ss * 0.5, px + s * 0.3, py + s * 0.3], fill=(255, 244, 196, 255))
    img.alpha_composite(big.resize((W, H), Image.LANCZOS))


def circle_bg(img, cx, cy, r, col_top, col_bot, ox=0, oy=0):
    W, H = img.size
    ss = 4
    big = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    m = Image.new("L", big.size, 0)
    c = ((cx - ox) * S * ss, (cy - oy) * S * ss); rr = r * S * ss
    ImageDraw.Draw(m).ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=255)
    g = grad_v(big.size[0], big.size[1], [(0, col_top), (max(0.01, (c[1] - rr) / big.size[1]), col_top), (min(0.99, (c[1] + rr) / big.size[1]), col_bot), (1, col_bot)])
    big.alpha_composite(fill_mask(m, g))
    # 안쪽 그늘
    sh = Image.new("L", big.size, 0)
    ImageDraw.Draw(sh).ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], outline=150, width=int(2.5 * ss))
    sh = sh.filter(ImageFilter.GaussianBlur(2 * ss))
    dark = Image.new("RGBA", big.size, (0, 0, 0, 255)); dark.putalpha(Image.fromarray((np.asarray(sh) * (np.asarray(m) > 0)).astype(np.uint8)))
    big.alpha_composite(dark)
    img.alpha_composite(big.resize((W, H), Image.LANCZOS))


def bevel_rect(img, x0, y0, x1, y1, ox=0, oy=0, dark=GOLD_DARK):
    """금 테두리 사각 (1px 어두운 외곽 + 2px 금)"""
    d = ImageDraw.Draw(img)
    X0, Y0, X1, Y1 = (x0 - ox) * S, (y0 - oy) * S, (x1 - ox) * S, (y1 - oy) * S
    d.rectangle([X0 - 2, Y0 - 2, X1 + 1, Y1 + 1], fill=dark + (255,))
    g = grad_v(X1 - X0, Y1 - Y0, [(0, (255, 236, 160)), (0.45, (218, 162, 62)), (1, (116, 68, 20))])
    gi = Image.fromarray(g, "RGBA")
    img.alpha_composite(gi, (X0, Y0))
    d.line([X0, Y0, X1 - 1, Y0], fill=(255, 250, 220, 255), width=1)


def boss_static(font):
    """뒤판 (막대 홈 + 시전 줄 바탕) / 앞판 (칸막이 + 광택 + 원 테두리)"""
    back = canvas(BOSS_W, 44)
    d = ImageDraw.Draw(back)
    # 막대: 금 테두리 + 어두운 홈
    bevel_rect(back, BAR[0], BAR[1], BAR[2], BAR[3])
    X0, Y0, X1, Y1 = FILL[0] * S, FILL[1] * S, FILL[2] * S, FILL[3] * S
    g = grad_v(X1 - X0 + 2, Y1 - Y0 + 2, [(0, (8, 4, 6)), (0.3, (30, 14, 16)), (1, (46, 22, 22))])
    back.alpha_composite(Image.fromarray(g, "RGBA"), (X0 - 1, Y0 - 1))
    # 홈 속 희미한 칸 무늬
    for k in range(1, 8):
        x = X0 + round(FILL_W * S * k / 8)
        d.line([x, Y0, x, Y1 - 1], fill=(70, 34, 30, 255), width=2)
    # 시전 줄 바탕: 가는 금선 + 끝 구슬
    cy = (CAST[1] + CAST[3]) / 2
    d.rectangle([CAST[0] * S, (cy - 1.5) * S, CAST[2] * S, (cy + 1.5) * S], fill=GOLD_DARK + (255,))
    d.rectangle([CAST[0] * S + 2, (cy - 0.5) * S, CAST[2] * S - 2, (cy + 0.5) * S], fill=(60, 34, 12, 255))
    for ex in (CAST[0], CAST[2]):
        gold_ring(back, ex, cy, 2.6, 0.01, rivets=0)
    front = canvas(BOSS_W, 44)
    fd = ImageDraw.Draw(front)
    # 칸막이 (채움 위에 그려짐)
    for k in range(1, 8):
        x = X0 + round(FILL_W * S * k / 8)
        fd.line([x - 1, Y0, x - 1, Y1 - 1], fill=(40, 10, 10, 170), width=1)
        fd.line([x, Y0, x, Y1 - 1], fill=(20, 6, 6, 230), width=2)
        fd.line([x + 2, Y0, x + 2, Y1 - 1], fill=(255, 190, 170, 40), width=1)
    # 유리 광택
    gl = Image.new("RGBA", back.size, (0, 0, 0, 0))
    ImageDraw.Draw(gl).rectangle([X0, Y0, X1 - 1, Y0 + 3], fill=(255, 255, 255, 46))
    ImageDraw.Draw(gl).rectangle([X0, Y1 - 3, X1 - 1, Y1 - 1], fill=(0, 0, 0, 60))
    front.alpha_composite(gl)
    # 원: 바탕 (초상화/아이콘 아래 → 여기선 테두리만, 바탕은 back)
    for c in (LC, RC):
        circle_bg(back, c[0], c[1], CR - 3, (26, 30, 52), (12, 14, 26))
        gold_ring(front, c[0], c[1], CR, CR - 3.2, rivets=8)
    # 원과 막대 잇는 장식 발톱
    for sx, c in ((1, LC), (-1, RC)):
        bx = c[0] + sx * (CR - 1)
        pts = [(bx, 18), (bx + sx * 8, 16), (bx + sx * 10, 14.5), (bx + sx * 7, 19)]
        ss = 4
        big = Image.new("RGBA", (front.size[0] * ss, front.size[1] * ss), (0, 0, 0, 0))
        bd = ImageDraw.Draw(big)
        bd.polygon([(p[0] * S * ss, p[1] * S * ss) for p in pts], fill=(236, 186, 84, 255), outline=GOLD_DARK + (255,))
        front.alpha_composite(big.resize(front.size, Image.LANCZOS))
    # 두 장으로 자르기 (각 120 GUI = 240px)
    for name, im in (("back", back), ("front", front)):
        for i in range(2):
            font.add(f"boss/{name}{i}", im.crop((i * 240, 0, (i + 1) * 240, 88)), i * 120, 0, "boss")


def fill_tiles(font):
    """HP 채움 (빨강) / 잔상 (밝은 주황) / 시전 게이지 (금) — 타일 + 부분 타일"""
    h = (FILL[3] - FILL[1]) * S
    red = grad_v(TILE * S, h, [(0, (255, 120, 96)), (0.25, (232, 58, 44)), (0.7, (178, 24, 24)), (1, (110, 10, 14))])
    trail = grad_v(TILE * S, h, [(0, (255, 236, 196)), (0.5, (255, 196, 120)), (1, (220, 140, 70))])
    # 붉은 채움에 미세한 결
    rn = np.random.default_rng(3).random((h, TILE * S))
    red = red.astype(np.float32)
    red[..., :3] *= (0.9 + 0.12 * rn[..., None])
    red = np.clip(red, 0, 255).astype(np.uint8)
    for kind, arr in (("hp", red), ("trail", trail)):
        for n in range(1, TILE + 1):
            im = Image.new("RGBA", (TILE * S, 88), (0, 0, 0, 0))
            seg = Image.fromarray(arr[:, :n * S].copy(), "RGBA")
            if kind == "hp":
                a = np.asarray(seg).copy()
                if n < TILE:     # 끝 부분 밝은 가장자리
                    a[:, -2:, :3] = np.clip(a[:, -2:, :3].astype(int) + 70, 0, 255)
                seg = Image.fromarray(a)
            else:
                a = np.asarray(seg).copy(); a[..., 3] = 200; seg = Image.fromarray(a)
            im.paste(seg, (0, FILL[1] * S))
            im = im.crop((0, FILL[1] * S, TILE * S, FILL[3] * S))
            # 오른쪽 끝 열 알파1 → advance 고정 (부분 타일도 전체 폭)
            font.add(f"boss/{kind}_{n}", im, 0, FILL[1], "boss")
    # 시전 게이지
    ch = (CAST_FILL[3] - CAST_FILL[1]) * S
    gold = grad_v(CAST_TILE * S, ch, [(0, (255, 248, 200)), (0.5, (255, 204, 80)), (1, (200, 120, 30))])
    for n in range(1, CAST_TILE + 1):
        im = Image.new("RGBA", (CAST_TILE * S, ch), (0, 0, 0, 0))
        im.paste(Image.fromarray(gold[:, :n * S].copy(), "RGBA"), (0, 0))
        font.add(f"boss/cast_{n}", im, 0, CAST_FILL[1], "boss")
    # 가운데 마름모 (시전 중 빛남 / 평상시)
    for state in ("idle", "lit"):
        sz = 10
        im = Image.new("RGBA", (sz * S * 4, sz * S * 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = sz * S * 2
        r = sz * S * 2 - 2
        d.polygon([(c, c - r), (c + r, c), (c, c + r), (c - r, c)], fill=GOLD_DARK + (255,))
        r2 = r - 10
        col = (255, 226, 120, 255) if state == "lit" else (200, 150, 60, 255)
        d.polygon([(c, c - r2), (c + r2, c), (c, c + r2), (c - r2, c)], fill=col)
        r3 = r2 - 14
        d.polygon([(c, c - r3), (c + r3, c), (c, c + r3), (c - r3, c)], fill=(255, 250, 220, 255) if state == "lit" else (120, 70, 20, 255))
        im = im.resize((sz * S, sz * S), Image.LANCZOS)
        if state == "lit":
            glow = im.filter(ImageFilter.GaussianBlur(3))
            big = Image.new("RGBA", (sz * S + 12, sz * S + 12), (0, 0, 0, 0))
            big.alpha_composite(glow, (6, 6)); big.alpha_composite(glow, (6, 6)); big.alpha_composite(im, (6, 6))
            font.add(f"boss/diamond_{state}", big, 120 - sz / 2 - 3, (CAST[1] + CAST[3]) / 2 - sz / 2 - 3, "boss")
        else:
            font.add(f"boss/diamond_{state}", im, 120 - sz / 2, (CAST[1] + CAST[3]) / 2 - sz / 2, "boss")


def banner_shape(w, h, notch=7):
    """리본 배너 다각형 (끝이 뾰족)"""
    return [(notch, 0), (w - notch, 0), (w, h / 2), (w - notch, h), (notch, h), (0, h / 2)]


def banners(font):
    W = BAN[2] - BAN[0]; H = BAN[3] - BAN[1]
    styles = {
        "normal": [(0, (150, 26, 30)), (0.5, (104, 12, 18)), (1, (62, 6, 10))],
        "rage": [(0, (196, 30, 26)), (0.5, (132, 10, 12)), (1, (70, 4, 6))],
        "cast": [(0, (132, 88, 30)), (0.5, (86, 54, 16)), (1, (50, 30, 8))],
    }
    for st, stops in styles.items():
        pad = 10 if st == "rage" else 0
        cw = W + pad * 2
        ss = 4
        big = Image.new("RGBA", (cw * S * ss, (H + 2) * S * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        def P(pts, dx=0, dy=0):
            return [((x + pad + dx) * S * ss, (y + 1 + dy) * S * ss) for x, y in pts]
        outer = banner_shape(W, H)
        if st == "rage":
            # 붉은 발톱 장식 (양옆)
            for sx in (-1, 1):
                base_x = W / 2 + sx * (W / 2 - 2)
                claws = [[(base_x, 5), (base_x + sx * 12, -1), (base_x + sx * 7, 6)],
                         [(base_x, 9), (base_x + sx * 14, 8), (base_x + sx * 7, 11)],
                         [(base_x, 12), (base_x + sx * 11, 17), (base_x + sx * 5, 12)]]
                for cl in claws:
                    d.polygon(P(cl), fill=(40, 6, 6, 255))
                    d.polygon(P([(cl[0][0], cl[0][1] + 0.6), (cl[1][0] - sx * 1.5, cl[1][1] + (0.8 if cl[1][1] < 8 else -0.8)), (cl[2][0], cl[2][1] - 0.4)]), fill=(200, 36, 30, 255))
        d.polygon(P(outer), fill=GOLD_DARK + (255,))
        inner_gold = banner_shape(W - 2, H - 2, 6)
        m = Image.new("L", big.size, 0)
        ImageDraw.Draw(m).polygon(P(inner_gold, 1, 1), fill=255)
        big.alpha_composite(fill_mask(m, grad_v(big.size[0], big.size[1], [(0, (255, 236, 160)), (0.5, (214, 158, 60)), (1, (120, 72, 20))])))
        m2 = Image.new("L", big.size, 0)
        ImageDraw.Draw(m2).polygon(P(banner_shape(W - 6, H - 6, 5), 3, 3), fill=255)
        big.alpha_composite(fill_mask(m2, grad_v(big.size[0], big.size[1], stops)))
        # 안쪽 가는 금선 장식
        d2 = ImageDraw.Draw(big)
        d2.line(P([(14, 4.2), (W - 14, 4.2)]), fill=(255, 210, 120, 90), width=ss)
        d2.line(P([(14, H - 4.2), (W - 14, H - 4.2)]), fill=(0, 0, 0, 90), width=ss)
        im = big.resize((cw * S, (H + 2) * S), Image.LANCZOS)
        font.add(f"boss/banner_{st}", im, BAN[0] - pad, BAN[1] - 1, "boss")


def label(font, key, text, style="name"):
    """배너 위 글자 (보스 이름 / 스킬 이름)"""
    f = font_kr(22)
    if style == "name":
        stops = [(0, (255, 250, 214)), (0.45, (255, 214, 96)), (1, (214, 132, 36))]
    else:
        stops = [(0, (255, 255, 240)), (0.5, (255, 232, 150)), (1, (240, 170, 60))]
    txt = ("◆ " + text) if style == "skill" else text
    im = text_img(txt if style != "skill" else text, f, stops, outline_col=(34, 10, 4), outline_r=2, pad=4)
    if style == "skill":
        # 앞에 작은 마름모
        dm = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dm)
        dd.polygon([(9, 1), (17, 9), (9, 17), (1, 9)], fill=(34, 10, 4, 255))
        dd.polygon([(9, 4), (14, 9), (9, 14), (4, 9)], fill=(255, 214, 90, 255))
        im2 = Image.new("RGBA", (im.size[0] + 22, max(im.size[1], 18)), (0, 0, 0, 0))
        im2.alpha_composite(dm, (0, (im2.size[1] - 18) // 2 - 1))
        im2.alpha_composite(im, (22, 0))
        im = im2
    maxw = (BAN[2] - BAN[0] - 18) * S
    if im.size[0] > maxw:
        im = im.resize((maxw, int(im.size[1] * maxw / im.size[0])), Image.LANCZOS)
    w, h = im.size
    x = 120 - w / S / 2
    y = (BAN[1] + BAN[3]) / 2 - h / S / 2
    return font.add(key, im, round(x * 2) / 2, round(y), "boss")


def font_kr(size):
    return gfx.font("Galmuri11-Bold.ttf", size)


PIX = {
    "0": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    "/": ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
    ":": [".....", "..#..", "..#..", ".....", "..#..", "..#..", "....."],
}


def digits(font, prefix, widget, y, adv_gui=8, **_):
    """5x7 픽셀 숫자 (흰색 + 1px 어두운 외곽선) — 텍스처 2배, 최근접 확대로 또렷하게"""
    out = {}
    for ch, rows in PIX.items():
        core = np.zeros((9, 7), bool)
        for yy, row in enumerate(rows):
            for xx, c in enumerate(row):
                if c == "#":
                    core[yy + 1, xx + 1] = True
        ol = np.zeros_like(core)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ol |= np.roll(np.roll(core, dy, 0), dx, 1)
        a = np.zeros((9, 7, 4), np.uint8)
        a[ol] = (22, 10, 8, 255)
        for yy in range(9):
            t = (yy - 1) / 6
            c = (255, 255, 255) if t < 0.5 else (228, 226, 222)
            a[yy][core[yy]] = c + (255,)
        im = Image.fromarray(a, "RGBA").resize((14, 18), Image.NEAREST)
        w = (adv_gui - 1) * S          # advance = w/2 + 1 = adv_gui
        can = Image.new("RGBA", (w, 18), (0, 0, 0, 0))
        can.alpha_composite(im, ((w - 14) // 2, 0))
        k = f"{prefix}_{'slash' if ch == '/' else ('colon' if ch == ':' else ch)}"
        font.add(k, can, 0, y, widget)
        out[ch] = k
    return out


def minimap_plate(font):
    """거점 미니맵 받침 (다이아몬드 배치 뒤)"""
    w, h = 34, 24
    im = canvas(w, h)
    ss = 4
    big = Image.new("RGBA", (im.size[0] * ss, im.size[1] * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big); k = S * ss
    d.rounded_rectangle([1 * k, 1 * k, (w - 1) * k, (h - 1) * k], radius=4 * k, fill=(14, 12, 20, 190), outline=(150, 120, 70, 255), width=k)
    # 십자 길 표시
    d.line([(w / 2 * k, 3 * k), (w / 2 * k, (h - 3) * k)], fill=(90, 80, 70, 200), width=k)
    d.line([(4 * k, h / 2 * k), ((w - 4) * k, h / 2 * k)], fill=(90, 80, 70, 200), width=k)
    d.line([(8 * k, 5 * k), ((w - 8) * k, (h - 5) * k)], fill=(70, 60, 55, 160), width=k)
    d.line([((w - 8) * k, 5 * k), (8 * k, (h - 5) * k)], fill=(70, 60, 55, 160), width=k)
    im.alpha_composite(big.resize(im.size, Image.LANCZOS))
    font.add("hud/minimap", im, 150 - w / 2, 12, "hud")


# ─────────────────────────────────────────────────────────────────────────────
#  상태 아이콘 (오른쪽 원)
# ─────────────────────────────────────────────────────────────────────────────
def status_icons(font):
    for st in ("normal", "rage", "stun"):
        r = CR - 3
        size = r * 2
        im = canvas(size, size)
        if st == "rage":
            circle_bg(im, r, r, r, (170, 30, 30), (70, 8, 8))
        elif st == "stun":
            circle_bg(im, r, r, r, (70, 70, 90), (30, 30, 40))
        ss = 4
        big = Image.new("RGBA", (im.size[0] * ss, im.size[1] * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        k = S * ss
        if st in ("normal", "rage"):
            bolt = [(r + 3, r - 11), (r - 5, r + 1), (r - 0.5, r + 1), (r - 3, r + 11), (r + 5.5, r - 2), (r + 1, r - 2), (r + 4, r - 11)]
            d.polygon([(x * k, y * k) for x, y in bolt], fill=(40, 20, 4, 255))
            inner = [(r + 2.4, r - 9.5), (r - 3.6, r + 0.2), (r + 0.6, r + 0.2), (r - 1.5, r + 8.5), (r + 4.2, r - 1.2), (r + 0.1, r - 1.2), (r + 2.8, r - 9.5)]
            m = Image.new("L", big.size, 0)
            ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in inner], fill=255)
            big.alpha_composite(fill_mask(m, grad_v(big.size[0], big.size[1], [(0, (255, 248, 200)), (0.5, (255, 200, 70)), (1, (210, 120, 20))])))
        else:
            for i in range(3):
                a = i * 2.1
                d.arc([(r - 8 + i) * k, (r - 8 + i) * k, (r + 8 - i) * k, (r + 8 - i) * k], math.degrees(a), math.degrees(a) + 160, fill=(255, 240, 150, 255), width=int(1.6 * k))
        small = big.resize(im.size, Image.LANCZOS)
        if st in ("normal", "rage"):
            glow = small.filter(ImageFilter.GaussianBlur(3))
            im.alpha_composite(glow)
        im.alpha_composite(small)
        font.add(f"boss/status_{st}", im, RC[0] - r, RC[1] - r, "boss")


def portrait(font, boss, img):
    """왼쪽 원 초상화: img 는 정사각 렌더 → 원형 마스크"""
    r = CR - 3
    size = r * 2 * S
    im = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse([2, 2, size * 4 - 2, size * 4 - 2], fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    im = mask_img(im, m)
    font.add(f"boss/portrait_{boss}", im, LC[0] - r, LC[1] - r, "boss")


# ─────────────────────────────────────────────────────────────────────────────
#  팀 HUD (GUI 300 x 36)
# ─────────────────────────────────────────────────────────────────────────────
TEAM_COL = {"red": (224, 52, 48), "blue": (60, 120, 240), "green": (70, 200, 70), "yellow": (240, 200, 40)}
PLATE_X = {"red": 6, "blue": 68, "green": 176, "yellow": 238}
PLATE_W = 56
PLATE = (0, 2, 0, 18)


def team_hud(font):
    for t, col in TEAM_COL.items():
        for mine in (False, True):
            w, h = PLATE_W, 16
            im = canvas(w + 2, h + 2)
            ss = 4
            big = Image.new("RGBA", (im.size[0] * ss, im.size[1] * ss), (0, 0, 0, 0))
            d = ImageDraw.Draw(big)
            k = S * ss
            # 판: 어두운 반투명 + 금/은 테두리
            d.rounded_rectangle([1 * k, 1 * k, (w + 1) * k, (h + 1) * k], radius=3 * k, fill=(14, 12, 20, 205),
                                outline=(255, 214, 110, 255) if mine else (120, 110, 100, 255), width=int((1.4 if mine else 1.0) * k))
            # 팀 색 방패
            sx, sy = 3, 2
            shield = [(sx, sy), (sx + 12, sy), (sx + 12, sy + 7), (sx + 6, sy + 13), (sx, sy + 7)]
            d.polygon([((x + 1) * k, (y + 1) * k) for x, y in shield], fill=(20, 10, 6, 255))
            inner = [(sx + 1.3, sy + 1.3), (sx + 10.7, sy + 1.3), (sx + 10.7, sy + 6.6), (sx + 6, sy + 11.4), (sx + 1.3, sy + 6.6)]
            m = Image.new("L", big.size, 0)
            ImageDraw.Draw(m).polygon([((x + 1) * k, (y + 1) * k) for x, y in inner], fill=255)
            c2 = tuple(min(255, int(v * 1.35 + 30)) for v in col)
            c3 = tuple(int(v * 0.55) for v in col)
            big.alpha_composite(fill_mask(m, grad_v(big.size[0], big.size[1], [(0, c2), (0.5, col), (1, c3)])))
            # 방패 위 작은 별 문양
            cxs, cys = (sx + 6 + 1) * k, (sy + 5.8 + 1) * k
            star = []
            for i in range(10):
                a = -math.pi / 2 + i * math.pi / 5
                rr = (2.6 if i % 2 == 0 else 1.1) * k
                star.append((cxs + math.cos(a) * rr, cys + math.sin(a) * rr))
            d.polygon(star, fill=(255, 246, 210, 255))
            im.alpha_composite(big.resize(im.size, Image.LANCZOS))
            if mine:
                glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
                gd = ImageDraw.Draw(glow)
                gd.rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], radius=8, outline=(255, 220, 120, 120), width=2)
                im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(1.5)))
            font.add(f"hud/plate_{t}{'_me' if mine else ''}", im, PLATE_X[t] - 1, PLATE[1] - 1, "hud")
    # 가운데 타이머 판
    w, h = 40, 14
    im = canvas(w + 2, h + 2)
    ss = 4
    big = Image.new("RGBA", (im.size[0] * ss, im.size[1] * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big); k = S * ss
    d.polygon([(1 * k, 1 * k), ((w + 1) * k, 1 * k), ((w - 3 + 1) * k, (h + 1) * k), (4 * k, (h + 1) * k)], fill=GOLD_DARK + (255,))
    m = Image.new("L", big.size, 0)
    ImageDraw.Draw(m).polygon([(2.2 * k, 2 * k), ((w - 0.2) * k, 2 * k), ((w - 3.2) * k, h * k), (5 * k, h * k)], fill=255)
    big.alpha_composite(fill_mask(m, grad_v(big.size[0], big.size[1], [(0, (40, 30, 26)), (1, (14, 10, 10))])))
    d.line([(2.2 * k, 2 * k), ((w - 0.2) * k, 2 * k)], fill=(255, 214, 110, 255), width=k)
    im.alpha_composite(big.resize(im.size, Image.LANCZOS))
    font.add("hud/timer", im, 150 - (w + 2) / 2, 0, "hud")


# ─────────────────────────────────────────────────────────────────────────────
#  문자열 합성 (Skript 도 같은 규칙) + 미리보기 엔진
# ─────────────────────────────────────────────────────────────────────────────
SPACE_BASE = 0xF000


def space_chars():
    """±1..±256 공백 글자"""
    adv = {}
    m = {}
    c = SPACE_BASE
    for p in range(9):
        v = 1 << p
        for sgn in (1, -1):
            ch = chr(c); c += 1
            adv[ch] = sgn * v
            m[sgn * v] = ch
    return adv, m


SP_ADV, SP_CH = space_chars()


def sp(n):
    """n 만큼 커서 이동 문자열"""
    n = int(n)
    if n == 0:
        return ""
    sgn = 1 if n > 0 else -1
    n = abs(n)
    out = ""
    for p in range(8, -1, -1):
        v = 1 << p
        while n >= v:
            out += SP_CH[sgn * v]
            n -= v
    return out


def place(font, key, dx=0.0, extra_x=0):
    """글리프를 (위젯 x + dx) 에 그리고 커서를 0 으로 되돌림.  반 픽셀 위치는 불가 → 반올림"""
    g = font.glyphs[key]
    if "parts" in g:
        return "".join(place(font, k, dx, extra_x) for k in g["parts"])
    base = (BOSS_X if g["widget"] == "boss" else 0) + extra_x
    x = int(round(g["x"] + dx + base))
    return sp(x) + g["char"] + sp(-(x + g["adv"]))


def build_font_json(font):
    prov = [{"type": "space", "advances": {ch: a for ch, a in SP_ADV.items()}}] + font.providers
    return {"providers": prov}


class Layout:
    """마인크래프트 폰트 렌더링 흉내 (미리보기용): 문자열 → 2배 해상도 이미지"""

    def __init__(self, font):
        self.by_char = {g["char"]: g for g in font.glyphs.values() if "char" in g}

    def render(self, s, width=TOTAL_W, height=70, colors=None):
        img = Image.new("RGBA", (width * S, height * S), (0, 0, 0, 0))
        cx = 0
        for i, ch in enumerate(s):
            if ch in SP_ADV:
                cx += SP_ADV[ch]
                continue
            g = self.by_char.get(ch)
            if g is None:
                continue
            top = (HUD_TOP if g["widget"] == "hud" else BOSS_TOP) + g["y"]
            gi = g["img"]
            if colors and i in colors:
                a = np.asarray(gi).astype(np.float32).copy()
                a[..., :3] *= np.array(colors[i]) / 255.0
                gi = Image.fromarray(a.astype(np.uint8))
            img.alpha_composite(gi, (cx * S, int(round(top * S))))
            cx += g["adv"]
        return img, cx
