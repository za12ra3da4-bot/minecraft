"""'신화쟁탈전' 타이틀 로고 (입장 · 게임 시작 타이틀)

 글꼴 그림 한 장은 256 픽셀을 넘으면 안 그려지므로 가로로 잘라 글자 여러 개로 잇는다.
 bg:title 글꼴 (U+E900~) — 기본 글꼴이 참조하므로 타이틀 문자열에 글자만 넣으면 그림이 나온다.
 타이틀은 4배로 그려지니 색 코드 · 굵게(&l) 없이 써야 금색이 그대로 나온다 (색을 곱하고, 굵게는 두 번 겹쳐 그림).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import gfx
import hud as H

TEXT = "신화쟁탈전"
CH0 = 0xE900          # bg:hud 는 U+E000 부터 · 공백은 U+F000 — 겹치지 않는 자리
UNITS_H = 18          # 화면 높이 (글꼴 단위, 기본 글자 8)
ASCENT = 16           # 아래 끝이 기준선 근처 → 부제목과 안 겹침
TEX_H = 180           # 그림 높이 → 1단위 = 10텍셀
TILE_U = 25           # 조각 하나 = 25단위 = 250텍셀
SS = 3                # 3배로 그린 뒤 줄여 테두리를 매끈하게

INK = (34, 18, 8)
BRONZE = (122, 66, 18)


def _gold(h, top=(255, 250, 222), hi=(255, 222, 120), mid=(236, 168, 52), low=(150, 78, 18), split=0.52):
    """세로 금속 그라데이션 (위 밝음 · 가운데 지평선에서 한 번 꺾임 · 아래 짙음)"""
    g = np.zeros((h, 3), np.float32)
    for y in range(h):
        t = y / max(1, h - 1)
        if t < split:
            k = t / split
            c = np.array(top) * (1 - k) + np.array(hi) * k
        else:
            k = (t - split) / (1 - split)
            c = np.array(mid) * (1 - k) + np.array(low) * k
        g[y] = c
    return g


def _paint(mask, grad):
    """mask(L) 모양에 세로 그라데이션을 칠한 RGBA"""
    w, h = mask.size
    a = np.asarray(mask, np.float32) / 255
    rgb = np.repeat(grad[:, None, :], w, axis=1)
    out = np.dstack([rgb, a * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def _solid(mask, col):
    im = Image.new("RGBA", mask.size, col + (255,))
    im.putalpha(mask)
    return im


def _grow(mask, r):
    """마스크를 r 픽셀 굵게 (원형)"""
    if r <= 0:
        return mask
    return mask.filter(ImageFilter.GaussianBlur(r * 0.55)).point(lambda v: 255 if v > 18 else int(v * 255 / 18)).filter(ImageFilter.MaxFilter(2 * (r // 2) + 1))


def _laurel(d, cx, cy, rx, ry, flip, s):
    """월계관 반쪽: 아래에서 바깥으로 둥글게 휘어 위로 올라가는 줄기 + 위를 향한 잎"""
    sg = 1 if flip else -1                                   # -1 = 왼쪽 가지
    pts = []
    n = 80
    for i in range(n + 1):
        a = math.radians(-70 + 150 * i / n)                  # 아래 안쪽 → 바깥 → 위 안쪽
        pts.append((cx + sg * rx * math.cos(a), cy - ry * math.sin(a)))
    d.line(pts, fill=255, width=max(1, int(4 * s)), joint="curve")
    leaves = 8
    for j in range(leaves):
        i = int(n * (0.06 + 0.86 * j / (leaves - 1)))
        (xa, ya), (xb, yb) = pts[max(0, i - 1)], pts[min(n, i + 1)]
        tx, ty = xb - xa, yb - ya
        L = math.hypot(tx, ty) or 1
        tx, ty = tx / L, ty / L
        nx, ny = -ty, tx
        size = (30 - 9 * j / (leaves - 1)) * s
        cx0, cy0 = pts[i]
        for side in (1, -1):
            dx, dy = tx * 0.75 + nx * side * 0.66, ty * 0.75 + ny * side * 0.66
            dl = math.hypot(dx, dy)
            dx, dy = dx / dl, dy / dl
            px, py = -dy, dx
            poly = []
            for k in range(13):
                u = k / 12
                w = math.sin(math.pi * u ** 0.8) * size * 0.27
                poly.append((cx0 + dx * size * u + px * w, cy0 + dy * size * u + py * w))
            for k in range(12, -1, -1):
                u = k / 12
                w = math.sin(math.pi * u ** 0.8) * size * 0.27
                poly.append((cx0 + dx * size * u - px * w, cy0 + dy * size * u - py * w))
            d.polygon(poly, fill=255)
    # 꼭대기 잎
    (xa, ya), (xb, yb) = pts[-3], pts[-1]
    tx, ty = xb - xa, yb - ya
    L = math.hypot(tx, ty) or 1
    tx, ty = tx / L, ty / L
    px, py = -ty, tx
    size = 22 * s
    poly = [(xb + tx * size * k / 12 + px * math.sin(math.pi * k / 12) * size * 0.26,
             yb + ty * size * k / 12 + py * math.sin(math.pi * k / 12) * size * 0.26) for k in range(13)]
    poly += [(xb + tx * size * k / 12 - px * math.sin(math.pi * k / 12) * size * 0.26,
              yb + ty * size * k / 12 - py * math.sin(math.pi * k / 12) * size * 0.26) for k in range(12, -1, -1)]
    d.polygon(poly, fill=255)


def _meander(d, x0, x1, y, h, s):
    """그리스 뇌문(雷文) 띠 + 위아래 테 선"""
    lw = max(1, int(3 * s))
    d.rectangle((x0, y, x1, y + lw), fill=255)
    d.rectangle((x0, y + h - lw, x1, y + h), fill=255)
    cell = h * 1.25
    n = int((x1 - x0) // cell)
    ox = x0 + ((x1 - x0) - n * cell) / 2
    m = lw * 1.9
    for i in range(n):
        a = ox + i * cell
        top, bot = y + m, y + h - m
        ih = bot - top
        # ㄹ 자 갈고리 한 칸
        P = [(a, bot), (a, top), (a + cell * 0.78, top), (a + cell * 0.78, top + ih * 0.72),
             (a + cell * 0.3, top + ih * 0.72), (a + cell * 0.3, top + ih * 0.38), (a + cell * 0.5, top + ih * 0.38)]
        d.line(P, fill=255, width=lw, joint="curve")
        d.line([(a, bot), (a + cell, bot)], fill=255, width=lw)


def render():
    s = SS
    fnt = gfx.font("NanumMyeongjoBold.ttf", 120 * s)
    tb = fnt.getbbox(TEXT)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    pad_side = 90 * s                                   # 월계수 자리
    W = tw + 2 * pad_side + 40 * s
    Hh = TEX_H * s
    text_top = 10 * s
    tx = (W - tw) // 2 - tb[0]
    ty = text_top - tb[1]

    m_text = Image.new("L", (W, Hh), 0)
    ImageDraw.Draw(m_text).text((tx, ty), TEXT, font=fnt, fill=255)
    text_bot = text_top + th

    m_deco = Image.new("L", (W, Hh), 0)
    dd = ImageDraw.Draw(m_deco)
    cy = text_top + th * 0.66
    _laurel(dd, (W - tw) // 2 - 4 * s, cy, 44 * s, 60 * s, False, s)
    _laurel(dd, (W + tw) // 2 + 4 * s, cy, 44 * s, 60 * s, True, s)
    my = text_bot + 8 * s
    _meander(dd, (W - tw) // 2 + 6 * s, (W + tw) // 2 - 6 * s, my, 28 * s, s)
    # 띠 양 끝 마름모
    for sx in ((W - tw) // 2 - 4 * s, (W + tw) // 2 + 4 * s):
        dd.polygon([(sx, my + 14 * s - 11 * s), (sx + 8 * s, my + 14 * s), (sx, my + 14 * s + 11 * s), (sx - 8 * s, my + 14 * s)], fill=255)

    shape = Image.fromarray(np.maximum(np.asarray(m_text), np.asarray(m_deco)))
    grad_t = _gold(Hh)

    im = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
    im.alpha_composite(_solid(_grow(shape, 7 * s), INK))                   # 바깥 먹선
    im.alpha_composite(_solid(_grow(shape, 3 * s), BRONZE))                # 청동 테
    # 글자: 텍스트 높이에 맞춘 금 그라데이션
    g = np.zeros((Hh, 3), np.float32)
    gt = _gold(th)
    g[:] = gt[-1]
    g[text_top:text_top + th] = gt
    g[:text_top] = gt[0]
    im.alpha_composite(_paint(m_text, g))
    # 장식: 조금 더 차분한 금
    gd = _gold(Hh, top=(255, 238, 178), hi=(246, 196, 88), mid=(218, 150, 48), low=(156, 86, 24), split=0.5)
    im.alpha_composite(_paint(m_deco, gd))
    # 윗면 반짝임 (마스크 - 아래로 민 마스크)
    up = np.asarray(m_text, np.float32) - np.roll(np.asarray(m_text, np.float32), 4 * s, axis=0)
    hl = Image.fromarray(np.clip(up * 0.75, 0, 255).astype(np.uint8))
    im.alpha_composite(_solid(hl, (255, 255, 240)))
    # 아랫면 그늘
    dn = np.asarray(m_text, np.float32) - np.roll(np.asarray(m_text, np.float32), -3 * s, axis=0)
    sh = Image.fromarray(np.clip(dn * 0.55, 0, 255).astype(np.uint8))
    im.alpha_composite(_solid(sh, (110, 52, 10)))

    im = im.resize((W // s, TEX_H), Image.LANCZOS)
    # 내용이 있는 가로 범위만 남기고 조각 폭(250)의 배수로 맞춤
    bbox = im.getbbox()
    im = im.crop((bbox[0], 0, bbox[2], TEX_H))
    tile = TILE_U * TEX_H // UNITS_H
    n = math.ceil(im.width / tile)
    out = Image.new("RGBA", (n * tile, TEX_H), (0, 0, 0, 0))
    out.alpha_composite(im, ((n * tile - im.width) // 2, 0))
    # 거의 투명한 가장자리 → 타이틀 셰이더가 0.1 미만은 버리므로 미리 정리
    a = np.asarray(out).copy()
    a[a[:, :, 3] < 26] = 0
    return Image.fromarray(a, "RGBA")


def export(pack):
    """그림을 조각으로 넣고 bg:title 글꼴을 쓴다 → 타이틀에 넣을 문자열 반환"""
    img = render()
    tile = TILE_U * TEX_H // UNITS_H
    n = img.width // tile
    prov, s = [], ""
    for i in range(n):
        t = img.crop((i * tile, 0, (i + 1) * tile, TEX_H)).copy()
        px = t.load()
        if px[tile - 1, 0][3] == 0:
            px[tile - 1, 0] = (0, 0, 0, 1)                # 폭 계산이 조각 전체가 되도록 (보이지 않는 점)
        ch = chr(CH0 + i)
        fname = f"font/title_{i}.png"
        pack.png(f"assets/{H.NS}/textures/{fname}", t)
        prov.append({"type": "bitmap", "file": f"{H.NS}:{fname}", "height": UNITS_H, "ascent": ASCENT, "chars": [ch]})
        s += ch + (H.sp(-1) if i < n - 1 else "")     # 글자마다 붙는 1단위 간격을 지움
    pack.put(f"assets/{H.NS}/font/title.json", {"providers": prov})
    return s, img


if __name__ == "__main__":
    im = render()
    big = Image.new("RGBA", im.size, (40, 60, 90, 255))
    big.alpha_composite(im)
    p = sys.argv[1] if len(sys.argv) > 1 else "title_preview.png"
    big.resize((im.width * 2, im.height * 2), Image.NEAREST).save(p)
    print(p, im.size)
