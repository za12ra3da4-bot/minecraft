"""보스 텍스처 재도색 (512 → 1024) — 원본의 색·그림을 바탕으로 붓질한 털 · 겹친 비늘 · 근육 · 뿔 마디 · 금속 · 젖은 촉수

UV 는 0..16 비율이라 아틀라스를 키워도 같은 자리. 원본은 tools/boss_fx/boss_src/ 에서 읽는다.
"""
import colorsys
import glob
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from boss_hd import BOSSES, SRC, classify

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..", "..", "resourcepack", "olympus_pack", "assets", "oly")
N = 1024


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def shift(c, f):
    """밝기 f 배 (색조 유지)"""
    return np.clip(np.array(c, float) * f, 0, 255)


def fur_strokes(h, w, base, rs, along_v=True, density=1.4, length=(6, 14)):
    """붓질한 털: 짧은 곡선 획을 겹겹이 (아래쪽이 끝, 끝이 밝다)"""
    S = 3
    im = Image.new("RGB", (w * S, h * S), tuple(int(v) for v in shift(base, 0.72)))
    d = ImageDraw.Draw(im)
    n = int(w * h * density)
    for _ in range(n):
        x = rs.uniform(-2, w + 2)
        y = rs.uniform(-4, h + 2)
        L = rs.uniform(*length)
        ang = rs.normal(0, 0.28) + (math.pi / 2 if along_v else 0)
        bend = rs.normal(0, 0.25)
        f = rs.uniform(0.55, 1.4)
        col = shift(base, f)
        pts = []
        for k in range(5):
            t = k / 4
            a = ang + bend * t
            pts.append(((x + math.cos(a) * L * t) * S, (y + math.sin(a) * L * t) * S))
        wd = max(1, int(S * rs.uniform(0.6, 1.2)))
        d.line(pts, fill=tuple(int(v) for v in col), width=wd)
        tip = pts[-1]
        d.ellipse([tip[0] - wd / 2, tip[1] - wd / 2, tip[0] + wd / 2, tip[1] + wd / 2], fill=tuple(int(v) for v in shift(col, 1.18)))
    return np.asarray(im.resize((w, h), Image.LANCZOS), dtype=float)


def scales(h, w, base, rs, cell=7.0):
    S = 3
    im = Image.new("RGB", (w * S, h * S), tuple(int(v) for v in shift(base, 0.45)))
    d = ImageDraw.Draw(im)
    rows = int(h / (cell * 0.62)) + 2
    for r in range(rows):
        y = (r * cell * 0.62 - cell * 0.4) * S
        off = (r % 2) * cell / 2
        cols = int(w / cell) + 2
        for c in range(cols):
            x = (c * cell - off) * S
            f = rs.uniform(0.85, 1.12)
            R = cell * 0.62 * S
            # 비늘 한 장: 어두운 테두리 → 몸 → 윗부분 하이라이트
            d.ellipse([x - R, y - R * 0.2, x + R, y + R * 1.5], fill=tuple(int(v) for v in shift(base, 0.55 * f)))
            d.ellipse([x - R * 0.86, y, x + R * 0.86, y + R * 1.3], fill=tuple(int(v) for v in shift(base, 1.0 * f)))
            d.ellipse([x - R * 0.5, y + R * 0.1, x + R * 0.4, y + R * 0.55], fill=tuple(int(v) for v in shift(base, 1.35 * f)))
    return np.asarray(im.resize((w, h), Image.LANCZOS), dtype=float)


def smooth(h, w, s, rs):
    return ndimage.gaussian_filter(rs.random((h, w)), s) - 0.5


def skin(h, w, base, rs, face):
    m = smooth(h, w, max(2, min(h, w) / 5), rs) * 1.2 + smooth(h, w, 1.0, rs) * 0.35
    img = np.array(base, float)[None, None, :] * (1 + m[..., None] * 0.35)
    # 근육 결: 세로로 부드러운 밝고 어두운 띠 (옆면)
    if face in ("north", "south", "east", "west") and w > 8:
        xs = np.arange(w)[None, :] / w
        img *= (1 + np.sin(xs * math.pi * 2.2) * 0.07)[..., None]
    return img


def horn(h, w, base, rs):
    ys = np.arange(h)[:, None] / max(1, h - 1)
    xs = np.arange(w)[None, :] / max(1, w - 1)
    ring = (np.sin((ys * h + np.sin(xs * 6) * 0.8) * 1.15) > 0.55) * -0.16
    grad = 0.8 + ys * 0.0 + xs * 0.35
    crack = (smooth(h, w, 0.8, rs) < -0.36) * -0.2
    img = np.array(base, float)[None, None, :] * (grad + ring + crack + smooth(h, w, 3, rs) * 0.3)[..., None]
    return img


def metal(h, w, base, rs):
    ys = np.arange(h)[:, None] / max(1, h - 1)
    band = np.exp(-((ys - 0.28) ** 2) / 0.015) * 0.5 + np.exp(-((ys - 0.7) ** 2) / 0.03) * -0.25
    brushed = ndimage.gaussian_filter1d(rs.random((h, w)), 6, axis=1) - 0.5
    scratch = np.zeros((h, w))
    for _ in range(max(1, (h * w) // 180)):
        x0, y0 = rs.integers(0, w), rs.integers(0, h)
        L = rs.integers(3, 9)
        for k in range(L):
            xx, yy = x0 + k, y0 + int(k * rs.uniform(-0.4, 0.4))
            if 0 <= xx < w and 0 <= yy < h:
                scratch[yy, xx] = 0.35
    img = np.array(base, float)[None, None, :] * (1 + band + brushed * 0.5 + scratch)[..., None]
    return img


def cloth(h, w, base, rs):
    xs = np.arange(w)[None, :]
    ys = np.arange(h)[:, None]
    fold = np.sin(xs / max(3, w) * math.pi * 4 + smooth(h, w, 4, rs) * 3) * 0.18
    weave = (((xs + ys) % 2) - 0.5) * 0.08
    img = np.array(base, float)[None, None, :] * (1 + fold + weave)[..., None]
    img[-2:, :] *= 0.7
    return img


def flesh(h, w, base, rs, face):
    m = smooth(h, w, 2.5, rs) * 0.8 + smooth(h, w, 0.8, rs) * 0.3
    img = np.array(base, float)[None, None, :] * (1 + m[..., None] * 0.45)
    # 젖은 광택
    ys = np.arange(h)[:, None] / max(1, h - 1)
    img += (np.exp(-((ys - 0.25) ** 2) / 0.01) * 60)[..., None] * np.array([1, 0.9, 1.0])[None, None, :]
    # 빨판 (아랫면 · 옆면 한쪽)
    if face in ("down", "west") and min(h, w) >= 6:
        pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(pil)
        step = max(5, min(h, w) // 2)
        for y in range(step // 2, h, step):
            for x in range(step // 2, w, step):
                r = step * 0.32
                d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v) for v in shift(base, 1.5)))
                d.ellipse([x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45], fill=tuple(int(v) for v in shift(base, 0.6)))
        img = np.asarray(pil, dtype=float)
    return img


def face_light(img, face):
    h, w, _ = img.shape
    ys = np.arange(h)[:, None] / max(1, h - 1)
    if face in ("north", "south", "east", "west"):
        g = 1.12 - ys * 0.34                       # 위 밝고 아래 그늘 (AO)
    elif face == "up":
        g = np.full((h, 1), 1.18)
    else:
        g = np.full((h, 1), 0.62)
    img = img * g[..., None]
    # 가장자리 AO + 윗모서리 빛
    e = np.ones((h, w))
    if h > 3 and w > 3:
        e[:, 0] *= 0.82
        e[:, -1] *= 0.82
        e[-1, :] *= 0.72
        e[0, :] *= 1.15
    return img * e[..., None]


def paint_region(orig, cls, face, rs):
    h, w, _ = orig.shape
    rgb = orig[..., :3]
    base = rgb.reshape(-1, 3).mean(0)
    if cls == "eye":
        return orig
    if cls == "fur":
        det = fur_strokes(h, w, base, rs, along_v=face not in ("up", "down"))
    elif cls == "scale":
        det = scales(h, w, base, rs)
    elif cls == "skin":
        det = skin(h, w, base, rs, face)
    elif cls == "horn":
        det = horn(h, w, base, rs)
    elif cls == "metal":
        det = metal(h, w, base, rs)
    elif cls == "wood":
        det = cloth(h, w, base, rs) * 0 + np.array(base)[None, None, :] * (1 + (np.sin(np.arange(w)[None, :] * 1.3 + smooth(h, w, 3, rs) * 5) * 0.14))[..., None]
    elif cls == "cloth":
        det = cloth(h, w, base, rs)
    else:
        det = flesh(h, w, base, rs, face)
    # 원본의 그림(얼굴 · 무늬 · 장식)은 살린다: 원본이 평균에서 많이 벗어난 곳은 원본을 더 섞는다
    # 원본에서 '그림'(눈 · 코 · 벨트 · 무늬선)만 골라 살린다: 면의 중앙값과 색이 크게 다른 곳
    med = np.median(rgb.reshape(-1, 3), axis=0)
    dev = np.abs(rgb - med).sum(2, keepdims=True) / (np.abs(med).sum() + 30)
    thr = {"fur": 0.45, "scale": 0.45, "flesh": 0.4}.get(cls, 0.16)   # 피부 · 뿔 · 금속은 원본 선(복근 · 무늬)을 더 살린다
    keep = np.clip((dev - thr) * 3.0, 0.0, 0.92)
    keep = ndimage.gaussian_filter(keep[..., 0], 0.6)[..., None]
    mix = det * (1 - keep) + rgb * keep
    out = face_light(mix, face)
    res = orig.copy().astype(float)
    res[..., :3] = np.clip(out, 0, 255)
    return res


def repaint(boss):
    src = os.path.join(SRC, boss + ".png")
    old = Image.open(src).convert("RGBA")
    big = np.asarray(old.resize((N, N), Image.NEAREST), dtype=float)
    out = big.copy()
    seen = set()
    mdir = os.path.join(SRC, "models", boss)
    files = sorted(glob.glob(os.path.join(mdir if os.path.isdir(mdir) else os.path.join(PACK, "models", "boss", boss), "*.json")))
    for f in files:
        part = os.path.basename(f)[:-5]
        for ei, el in enumerate(json.load(open(f))["elements"]):
            for face, fd in el["faces"].items():
                u0, v0, u1, v1 = fd["uv"]
                x0, x1 = sorted((u0 * N / 16, u1 * N / 16))
                y0, y1 = sorted((v0 * N / 16, v1 * N / 16))
                x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
                key = (x0, y0, x1, y1)
                if key in seen or x1 - x0 < 2 or y1 - y0 < 2:
                    continue
                seen.add(key)
                reg = big[y0:y1, x0:x1]
                if reg[..., 3].max() == 0:
                    continue
                cls = classify(boss, part, reg[..., :3].reshape(-1, 3).mean(0))
                rs = np.random.default_rng(abs(hash((boss, part, ei, face))) % (2 ** 31))
                # 면을 뒤집어 쓴 UV (u0>u1 등)는 무늬 방향도 같이 뒤집힌다 — 털 방향만 맞추면 충분
                flip_v = v0 > v1
                r = reg[::-1] if flip_v else reg
                pr = paint_region(r, cls, face, rs)
                out[y0:y1, x0:x1] = pr[::-1] if flip_v else pr
    return out


def save(boss, arr):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA").save(
        os.path.join(PACK, "textures", "item", "boss", boss + ".png"), optimize=True)


if __name__ == "__main__":
    import sys
    for b in (sys.argv[1:] or BOSSES):
        save(b, repaint(b))
        print(b, "ok")
