"""수묵 붓터치 렌더러 — 붉은 먹(주묵) 경고 장판용

 stroke(): 경로를 따라 붓 자국을 그린다.
   - 붓털(bristle) 수십 가닥이 각자 굵기·먹 양을 가지고 경로를 따라감 → 드라이브러시 갈라짐
   - 시작부 먹 고임, 끝으로 갈수록 먹이 말라 갈라짐 (획마다 우연성)
   - 결과는 먹 농도 맵 (0..1)
 colorize(): 농도 → 색 (진한 곳 짙은 주홍, 옅은 곳 밝은 주홍) + 알파
"""
import math

import numpy as np
from scipy import ndimage

VERMILION = np.array((226, 44, 28), np.float32)
DEEP = np.array((150, 12, 12), np.float32)
LIGHT = np.array((255, 110, 70), np.float32)


def rng(seed):
    return np.random.default_rng(seed)


def stroke(size, path, width, seed=1, dry=0.55, pool=0.35, taper=(0.35, 0.6), bristles=16, rough=0.6):
    """붓 한 획: 먹이 꽉 찬 몸통 + 굵은 붓털 가닥(드라이브러시) + 시작부 먹 고임 → 농도 맵"""
    R = rng(seed)
    H = W = size
    P = np.array(path, np.float32)
    n = len(P)
    acc = np.zeros((H, W), np.float32)
    if n < 2:
        return acc
    seg = np.diff(P, axis=0)
    L = np.linalg.norm(seg, axis=1)
    cum = np.concatenate([[0], np.cumsum(L)])
    total = cum[-1] + 1e-6
    tang = np.zeros_like(P)
    tang[:-1] = seg / (L[:, None] + 1e-6)
    tang[-1] = tang[-2]
    nrm = np.stack([-tang[:, 1], tang[:, 0]], 1)
    t = cum / total
    prof = np.clip(np.minimum(t / taper[0] * 0.45 + 0.55, 1.0), 0, 1) * np.clip((1 - t) / (1 - taper[1]) * 0.75 + 0.25, 0, 1)
    wob = ndimage.gaussian_filter1d(R.normal(0, 1, n), max(1, n / 30)) * width * 0.06 * rough
    step = max(1, int(n / (total / 1.2)))
    yy, xx = np.mgrid[0:H, 0:W]

    def dab(x, y, r, v):
        x0, x1 = int(max(0, x - r - 1)), int(min(W - 1, x + r + 1))
        y0, y1 = int(max(0, y - r - 1)), int(min(H - 1, y + r + 1))
        if x0 > x1 or y0 > y1:
            return
        d = np.sqrt((xx[y0:y1 + 1, x0:x1 + 1] - x) ** 2 + (yy[y0:y1 + 1, x0:x1 + 1] - y) ** 2)
        val = np.clip(r + 0.6 - d, 0, 1) * v
        np.maximum(acc[y0:y1 + 1, x0:x1 + 1], val, out=acc[y0:y1 + 1, x0:x1 + 1])

    # 1) 몸통: 획의 가운데 60% 폭, 먹이 꽉 참 (끝으로 갈수록 마름)
    body_dry = 1 - dry * 0.55
    for i in range(0, n, step):
        if t[i] > body_dry + R.random() * 0.08:
            break
        c = P[i] + nrm[i] * wob[i]
        dab(c[0], c[1], width * 0.32 * prof[i], 0.92)
    # 2) 붓털: 굵은 가닥이 가장자리까지 — 마를수록 끊김
    for b in range(bristles):
        off = (b / (bristles - 1) - 0.5) * 0.98
        ink0 = 0.7 + 0.3 * R.random()
        thick = width / bristles * (1.1 + 0.9 * R.random())
        dry_start = np.clip(R.normal(1 - dry * 0.7, 0.14) - abs(off) * dry * 0.6, 0.15, 1.1)
        gaps = ndimage.gaussian_filter1d(R.random(n), 2.0) > (0.55 - 0.1 * dry)
        for i in range(0, n, step):
            ti = t[i]
            ink = ink0
            if ti > dry_start:
                ink *= max(0.0, 1 - (ti - dry_start) * 3.5)
                if gaps[i]:
                    continue
            if ink <= 0.03:
                continue
            c = P[i] + nrm[i] * (off * width * prof[i] + wob[i])
            dab(c[0], c[1], thick * 0.5 * (0.7 + 0.5 * prof[i]), ink)
    # 3) 시작부 먹 고임 + 튄 먹
    if pool > 0:
        c = P[min(2, n - 1)]
        d = np.sqrt((xx - c[0]) ** 2 + (yy - c[1]) ** 2)
        acc = np.maximum(acc, np.clip(1 - d / (width * 0.6), 0, 1) ** 0.7 * pool * 1.6)
        for k in range(int(3 + pool * 6)):
            a_ = R.uniform(0, 2 * np.pi); rr = width * R.uniform(0.7, 1.4)
            dab(c[0] + np.cos(a_) * rr, c[1] + np.sin(a_) * rr, R.uniform(0.6, 1.8), 0.9)
    # 화선지 번짐
    acc = np.maximum(acc, ndimage.gaussian_filter(acc, 1.0) * 0.85)
    return np.clip(acc, 0, 1)


def paper(size, seed, amt=0.12):
    """화선지 결 (알파에 곱할 미세 결)"""
    R = rng(seed)
    n = R.random((size, size)).astype(np.float32)
    n = ndimage.gaussian_filter(n, 0.7)
    fib = ndimage.gaussian_filter(R.random((size, size)).astype(np.float32), (0.5, 3))
    return 1 - amt + amt * 2 * (0.6 * n + 0.4 * fib)


def wash(mask, seed, strength=0.45, edge_bleed=3.0):
    """먹물 담채 (면 채움): 가장자리 쪽이 진하게 고이고 불규칙 번짐"""
    R = rng(seed)
    size = mask.shape[0]
    m = mask.astype(np.float32)
    # 불규칙 경계
    noise = ndimage.gaussian_filter(R.random(m.shape).astype(np.float32), 4)
    noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-6)
    soft = ndimage.gaussian_filter(m, edge_bleed)
    shape = np.clip((soft - 0.35 - (noise - 0.5) * 0.25) * 4, 0, 1)
    # 가장자리 고임
    inner = ndimage.gaussian_filter(m, edge_bleed * 3)
    pool = np.clip(shape - inner * 0.85, 0, 1)
    tex = ndimage.gaussian_filter(R.random(m.shape).astype(np.float32), 1.5)
    dens = shape * (strength * (0.75 + 0.5 * tex)) + pool * 0.5
    return np.clip(dens, 0, 1)


def colorize(dens, alpha=1.0, color=None, deep=None, light=None, paper_seed=0):
    c = VERMILION if color is None else np.array(color, np.float32)
    d = DEEP if deep is None else np.array(deep, np.float32)
    l = LIGHT if light is None else np.array(light, np.float32)
    h, w = dens.shape
    out = np.zeros((h, w, 4), np.float32)
    k = dens[..., None]
    col = l * (1 - k) + c * k
    kk = np.clip(k - 0.7, 0, 0.3) / 0.3 * 0.5
    col = col * (1 - kk) + d * kk
    out[..., :3] = col
    a = np.clip(dens * 1.25, 0, 1) * alpha
    if paper_seed:
        a *= paper(max(h, w), paper_seed)[:h, :w]
    out[..., 3] = a * 255
    return out


def circle_path(size, radius, start_deg=-100, sweep=360, cx=None, cy=None, wobble=0.012, seed=0, n=720):
    R = rng(seed)
    cx = size / 2 if cx is None else cx
    cy = size / 2 if cy is None else cy
    pts = []
    wob = ndimage.gaussian_filter1d(R.normal(0, 1, n), n / 20) * size * wobble
    for i in range(n):
        a = math.radians(start_deg + sweep * i / (n - 1))
        r = radius + wob[i]
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def line_path(p0, p1, n=300, wobble=0.0, seed=0):
    R = rng(seed)
    wob = ndimage.gaussian_filter1d(R.normal(0, 1, n), n / 12) * wobble
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / L, dx / L
    return [(x0 + dx * i / (n - 1) + nx * wob[i], y0 + dy * i / (n - 1) + ny * wob[i]) for i in range(n)]


def to_img(arr):
    from PIL import Image
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
