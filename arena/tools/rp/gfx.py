"""그리기 유틸 (PIL + numpy)"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), ".cache", "fonts")
FONT_URLS = {
    "Galmuri11-Bold.ttf": "https://raw.githubusercontent.com/quiple/galmuri/main/dist/Galmuri11-Bold.ttf",
    "Galmuri9.ttf": "https://raw.githubusercontent.com/quiple/galmuri/main/dist/Galmuri9.ttf",
    "BlackHanSans.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/blackhansans/BlackHanSans-Regular.ttf",
    "NanumBrush.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumbrushscript/NanumBrushScript-Regular.ttf",
    "NanumMyeongjoBold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/nanummyeongjo/NanumMyeongjo-ExtraBold.ttf",
}


def font(name, size):
    p = os.path.join(FONTS, name)
    if not os.path.exists(p):
        os.makedirs(FONTS, exist_ok=True)
        os.system(f"curl -sS -o '{p}' '{FONT_URLS[name]}'")
    return ImageFont.truetype(p, size)


def rgba(c, a=255):
    if len(c) == 4:
        return tuple(c)
    return (c[0], c[1], c[2], a)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def grad_v(w, h, stops):
    """세로 그라데이션 RGBA 배열. stops = [(t, color)]"""
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]; t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                c = lerp(rgba(c0), rgba(c1), (t - t0) / max(1e-6, t1 - t0))
                out[y, :] = c
                break
    return out


def ss_draw(w, h, fn, ss=4):
    """고해상도로 그린 뒤 축소 (부드러운 가장자리)"""
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fn(d, ss)
    return im.resize((w, h), Image.LANCZOS)


def paste(dst, src, x, y):
    dst.alpha_composite(src, (int(x), int(y)))


def mask_img(img, mask):
    a = np.asarray(img).copy()
    m = np.asarray(mask.convert("L"), np.float32) / 255.0
    a[..., 3] = (a[..., 3] * m).astype(np.uint8)
    return Image.fromarray(a)


def fill_mask(mask, color_arr):
    """mask(L) 모양대로 색 배열(RGBA np) 채움"""
    h, w = color_arr.shape[:2]
    im = Image.fromarray(color_arr, "RGBA")
    return mask_img(im, mask)


def outline(img, color, r=1):
    """알파 외곽선"""
    a = img.split()[3]
    grown = a.filter(ImageFilter.MaxFilter(r * 2 + 1))
    base = Image.new("RGBA", img.size, rgba(color))
    base.putalpha(grown)
    base.alpha_composite(img)
    return base


def text_img(text, fnt, fill_stops, outline_col=(30, 14, 4), outline_r=2, shadow=True, pad=6):
    """그라데이션 글자 + 외곽선"""
    bbox = fnt.getbbox(text)
    w = bbox[2] - bbox[0] + pad * 2
    h = bbox[3] - bbox[1] + pad * 2
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((pad - bbox[0], pad - bbox[1]), text, font=fnt, fill=255)
    g = grad_v(w, h, fill_stops)
    # 그라데이션을 글자 높이에 맞춤
    top = pad; bot = h - pad
    g2 = grad_v(w, bot - top, fill_stops)
    g = np.zeros((h, w, 4), np.uint8)
    g[:top] = g2[0]; g[top:bot] = g2; g[bot:] = g2[-1]
    im = fill_mask(m, g)
    im = outline(im, outline_col, outline_r)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        s = im.split()[3].point(lambda v: int(v * 0.5))
        blk = Image.new("RGBA", im.size, (10, 4, 2, 255))
        blk.putalpha(s)
        sh.alpha_composite(blk, (0, 2))
        sh.alpha_composite(im)
        im = sh
    return im


def noise(w, h, seed, scale=1.0):
    r = np.random.default_rng(seed)
    return r.random((h, w)) * scale


def brush_noise(w, h, seed, cell=6):
    from scipy import ndimage
    r = np.random.default_rng(seed)
    g = r.random((h // cell + 3, w // cell + 3))
    up = ndimage.zoom(g, cell, order=3)[:h, :w]
    return up
