"""경고 장판 (붉은 먹 붓터치) — 텍스처 + 평면 아이템 모델

 원형:   ring(옅은 테두리, 고정) + fill(가운데서 커지는 담채) + arc_0..N(테두리를 따라 붓이 그려지는 게이지) + flash
 직선:   rect_base(양옆 붓선 + 옅은 담채) + rect_fill(시작점에서 뻗어나감) + rect_head(화살촉) + rect_flash
 부채꼴: cone{60,90,120}_base / _fill / _flash  (꼭짓점에서 퍼져 나감)
 도넛:   donut_base + donut_fill_0..N (바깥에서 안으로 차오름) + donut_flash   (안쪽 원 = 안전지대)
 기타:   mark_ground(표적 원), mark_head(머리 위 ! 표식, 세워서 사용), num_1..9(순서 숫자),
         rune_sphinx(석화 마법진), poison(독 웅덩이), scorch(그을음), summon(보스 소환진은 decor 쪽)
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gfx
from ink import *

S = 256
ARC_FRAMES = 20
DONUT_FRAMES = 12
FLASH = ((255, 70, 50), (200, 10, 20), (255, 236, 226))


def img(a):
    return to_img(a)


def over(*layers):
    """RGBA float 배열 알파 합성"""
    out = np.zeros_like(layers[0])
    for L in layers:
        a = L[..., 3:4] / 255.0
        oa = out[..., 3:4] / 255.0
        na = a + oa * (1 - a)
        out[..., :3] = np.where(na > 0, (L[..., :3] * a + out[..., :3] * oa * (1 - a)) / np.maximum(na, 1e-6), 0)
        out[..., 3:4] = na * 255
    return out


def disc_mask(size, r, cx=None, cy=None):
    cx = size / 2 if cx is None else cx
    cy = size / 2 if cy is None else cy
    yy, xx = np.mgrid[0:size, 0:size]
    return (np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) <= r)


# ─────────────────────────────────────────────────────────────── 원
def circle_set(out):
    R0 = S * 0.43
    path = circle_path(S, R0, -110, 352, seed=11, wobble=0.006)
    bold = stroke(S, path, S * 0.075, seed=12, dry=0.55, pool=0.25, bristles=16)
    faint = stroke(S, circle_path(S, R0, -95, 360, seed=13, wobble=0.004), S * 0.05, seed=14, dry=0.8, pool=0.0, bristles=14)
    inner = wash(disc_mask(S, R0 - 4), 15, strength=0.14, edge_bleed=2.0)
    out["circle_ring"] = over(colorize(inner, 0.7, paper_seed=16), colorize(faint, 0.55, paper_seed=17))
    out["circle_fill"] = colorize(wash(disc_mask(S, R0 - 2), 18, strength=0.42, edge_bleed=2.5), 0.85, paper_seed=19)
    # 게이지: 붓이 원을 따라 그려진다 — 같은 획을 잘라서 쓰면 먹 흐름이 자연스럽다
    n = len(path)
    for k in range(ARC_FRAMES):
        frac = (k + 1) / ARC_FRAMES
        sub = path[:max(3, int(n * frac))]
        dens = stroke(S, sub, S * 0.075, seed=12, dry=0.55 * (0.4 + 0.6 * frac), pool=0.25, bristles=16)
        out[f"circle_arc_{k}"] = colorize(dens, 1.0, paper_seed=20)
    fl = np.maximum(bold, wash(disc_mask(S, R0), 21, 0.55, 2.0) * 0.8)
    out["circle_flash"] = colorize(fl, 1.0, *FLASH, paper_seed=22)


# ─────────────────────────────────────────────────────────────── 직선
def rect_set(out):
    W, H = 128, 256          # 가로(폭) x 세로(길이) — 길이 방향이 이미지 세로
    base = np.zeros((H, W), np.float32)
    for sx, sd in ((10, 31), (W - 11, 32)):
        base = np.maximum(base, stroke(max(W, H), line_path((sx, 6), (sx, H - 6), 300, 1.5, sd), 11, seed=sd, dry=0.6, pool=0.2, bristles=12)[:H, :W])
    m = np.zeros((H, W), bool); m[4:H - 4, 12:W - 12] = True
    inner = wash(np.pad(m, ((0, 0), (0, H - W)))[:, :max(W, H)], 33, 0.14, 2.0)[:H, :W]
    out["rect_base"] = over(colorize(inner, 0.7, paper_seed=34), colorize(base, 0.6, paper_seed=35))
    fm = np.zeros((H, H), bool); fm[3:H - 3, 10:W - 10] = True
    fill = wash(fm, 36, 0.42, 2.5)[:H, :W]
    out["rect_fill"] = colorize(fill, 0.85, paper_seed=37)
    fl = np.maximum(fill * 1.4, base)
    out["rect_flash"] = colorize(np.clip(fl, 0, 1), 1.0, *FLASH, paper_seed=38)
    # 화살촉 (정사각)
    head = stroke(S, line_path((S * 0.15, S * 0.62), (S * 0.5, S * 0.25), 200, 2, 40), S * 0.08, seed=41, dry=0.5)
    head = np.maximum(head, stroke(S, line_path((S * 0.5, S * 0.25), (S * 0.85, S * 0.62), 200, 2, 42), S * 0.08, seed=43, dry=0.6, pool=0))
    head = np.maximum(head, stroke(S, line_path((S * 0.22, S * 0.88), (S * 0.5, S * 0.58), 200, 2, 44), S * 0.06, seed=45, dry=0.7))
    head = np.maximum(head, stroke(S, line_path((S * 0.5, S * 0.58), (S * 0.78, S * 0.88), 200, 2, 46), S * 0.06, seed=47, dry=0.7, pool=0))
    out["rect_head"] = colorize(head, 1.0, paper_seed=48)


# ─────────────────────────────────────────────────────────────── 부채꼴
def cone_set(out, deg):
    # 꼭짓점 = 이미지 아래 가운데, 위쪽으로 퍼짐
    ax, ay = S / 2, S / 2
    R0 = S / 2 - 8
    a0 = -90 - deg / 2
    a1 = -90 + deg / 2
    yy, xx = np.mgrid[0:S, 0:S]
    ang = np.degrees(np.arctan2(yy + 0.5 - ay, xx + 0.5 - ax))
    dist = np.hypot(xx + 0.5 - ax, yy + 0.5 - ay)
    m = (dist <= R0 - 3) & (ang >= a0 + 1.5) & (ang <= a1 - 1.5)
    edge = np.zeros((S, S), np.float32)
    for k, a in enumerate((a0, a1)):
        p1 = (ax + math.cos(math.radians(a)) * R0, ay + math.sin(math.radians(a)) * R0)
        edge = np.maximum(edge, stroke(S, line_path((ax, ay), p1, 260, 1.5, 50 + k), 9, seed=51 + k, dry=0.6, pool=0.2 if k == 0 else 0, bristles=12))
    arc = circle_path(S, R0, a0, deg, cx=ax, cy=ay, seed=53, wobble=0.003, n=400)
    edge = np.maximum(edge, stroke(S, arc, 10, seed=54, dry=0.55, pool=0.1, bristles=12))
    inner = wash(m, 55, 0.14, 2.0)
    out[f"cone{deg}_base"] = over(colorize(inner, 0.7, paper_seed=56), colorize(edge, 0.6, paper_seed=57))
    fill = wash(m, 58, 0.44, 2.5)
    out[f"cone{deg}_fill"] = colorize(fill, 0.85, paper_seed=59)
    out[f"cone{deg}_flash"] = colorize(np.clip(np.maximum(fill * 1.4, edge), 0, 1), 1.0, *FLASH, paper_seed=60)


# ─────────────────────────────────────────────────────────────── 도넛
def donut_set(out, inner_frac=0.42):
    Ro = S * 0.46
    Ri = Ro * inner_frac
    outer = stroke(S, circle_path(S, Ro, -100, 356, seed=61, wobble=0.004), S * 0.05, seed=62, dry=0.6, pool=0.2, bristles=14)
    innr = stroke(S, circle_path(S, Ri, 80, 350, seed=63, wobble=0.006), S * 0.04, seed=64, dry=0.6, pool=0.2, bristles=12)
    yy, xx = np.mgrid[0:S, 0:S]
    d = np.hypot(xx + 0.5 - S / 2, yy + 0.5 - S / 2)
    ring = (d <= Ro - 3) & (d >= Ri + 3)
    out["donut_base"] = over(colorize(wash(ring, 65, 0.12, 2.0), 0.7, paper_seed=66), colorize(np.maximum(outer, innr), 0.6, paper_seed=67))
    for k in range(DONUT_FRAMES):
        frac = (k + 1) / DONUT_FRAMES
        rin = Ro - (Ro - Ri) * frac
        m = (d <= Ro - 2) & (d >= rin)
        out[f"donut_fill_{k}"] = colorize(wash(m, 68, 0.42, 2.2), 0.85, paper_seed=69)
    fl = np.maximum(wash(ring, 70, 0.6, 2.0), np.maximum(outer, innr))
    out["donut_flash"] = colorize(np.clip(fl, 0, 1), 1.0, *FLASH, paper_seed=71)


# ─────────────────────────────────────────────────────────────── 표식·숫자
def marks(out):
    ring = stroke(S, circle_path(S, S * 0.4, -120, 340, seed=81, wobble=0.01), S * 0.06, seed=82, dry=0.5, pool=0.3)
    cross = np.zeros((S, S), np.float32)
    for k, (p0, p1) in enumerate((((S * 0.5, S * 0.02), (S * 0.5, S * 0.3)), ((S * 0.5, S * 0.98), (S * 0.5, S * 0.7)),
                                   ((S * 0.02, S * 0.5), (S * 0.3, S * 0.5)), ((S * 0.98, S * 0.5), (S * 0.7, S * 0.5)))):
        cross = np.maximum(cross, stroke(S, line_path(p0, p1, 120, 1, 83 + k), S * 0.045, seed=84 + k, dry=0.4, pool=0.35))
    dot = stroke(S, circle_path(S, S * 0.06, 0, 360, seed=88, n=120), S * 0.08, seed=89, dry=0.2, pool=0.5)
    out["mark_ground"] = colorize(np.maximum(np.maximum(ring, cross), dot), 1.0, paper_seed=90)
    # 머리 위 ! (세로)
    bang = stroke(S, line_path((S * 0.52, S * 0.06), (S * 0.49, S * 0.66), 200, 3, 91), S * 0.16, seed=92, dry=0.35, pool=0.5, taper=(0.2, 0.3))
    bang = np.maximum(bang, stroke(S, circle_path(S, S * 0.045, 0, 360, cy=S * 0.85, seed=93, n=120), S * 0.11, seed=94, dry=0.1, pool=0.6))
    halo = ndimage.gaussian_filter(bang, 6) * 0.6
    a = colorize(np.clip(bang, 0, 1), 1.0, paper_seed=95)
    h = colorize(np.clip(halo, 0, 1), 0.8, (255, 220, 190), (255, 160, 120), (255, 240, 220))
    out["mark_head"] = over(h, a)
    # 순서 숫자 (붓글씨체)
    f = gfx.font("BlackHanSans.ttf", 200)
    for n in range(1, 10):
        big = Image.new("L", (S * 2, S * 2), 0)
        d = ImageDraw.Draw(big)
        bb = d.textbbox((0, 0), str(n), font=f)
        d.text(((S * 2 - (bb[2] - bb[0])) / 2 - bb[0], (S * 2 - (bb[3] - bb[1])) / 2 - bb[1]), str(n), font=f, fill=255)
        bb = big.getbbox()
        crop = big.crop(bb)
        sc = (S * 0.72) / max(crop.size)
        crop = crop.resize((int(crop.size[0] * sc), int(crop.size[1] * sc)), Image.LANCZOS)
        im = Image.new("L", (S, S), 0)
        im.paste(crop, ((S - crop.size[0]) // 2, (S - crop.size[1]) // 2))
        dens = np.asarray(im, np.float32) / 255
        dens = dens * (0.75 + 0.25 * paper(S, 100 + n, 0.5))
        glow = ndimage.gaussian_filter(dens, 5) * 0.7
        out[f"num_{n}"] = over(colorize(np.clip(glow, 0, 1), 0.9, (255, 240, 220), (255, 200, 170), (255, 250, 240)),
                               colorize(np.clip(dens * 1.2, 0, 1), 1.0, (120, 8, 8), (60, 0, 0), (200, 30, 20)))


# ─────────────────────────────────────────────────────────────── 스핑크스 석화 마법진
def rune_sphinx(out):
    dens = np.zeros((S, S), np.float32)
    c = S / 2
    for k, (r, w, sd) in enumerate(((0.47, 0.03, 1), (0.40, 0.02, 2), (0.24, 0.025, 3), (0.12, 0.02, 4))):
        dens = np.maximum(dens, stroke(S, circle_path(S, S * r, -90 + k * 40, 358, seed=110 + sd, wobble=0.003), S * w, seed=120 + sd, dry=0.5, pool=0.15, bristles=10))
    # 12 상형 문자 (눈·앙크·새·물결)
    for i in range(12):
        a = i / 12 * 2 * math.pi
        gx, gy = c + math.cos(a) * S * 0.435, c + math.sin(a) * S * 0.435
        kind = i % 4
        s = S * 0.028
        if kind == 0:     # 눈
            pts = [(gx + math.cos(t) * s * 1.4, gy + math.sin(t) * s * 0.6) for t in np.linspace(0, 2 * math.pi, 40)]
            dens = np.maximum(dens, stroke(S, pts, 3, seed=130 + i, dry=0.3, pool=0))
        elif kind == 1:   # 앙크
            pts = [(gx + math.cos(t) * s * 0.6, gy - s * 0.8 + math.sin(t) * s * 0.8) for t in np.linspace(0, 2 * math.pi, 30)]
            dens = np.maximum(dens, stroke(S, pts, 2.6, seed=140 + i, dry=0.3, pool=0))
            dens = np.maximum(dens, stroke(S, line_path((gx, gy), (gx, gy + s * 1.6), 30), 3, seed=150 + i, dry=0.3, pool=0))
            dens = np.maximum(dens, stroke(S, line_path((gx - s, gy + s * 0.3), (gx + s, gy + s * 0.3), 30), 3, seed=160 + i, dry=0.3, pool=0))
        elif kind == 2:   # 물결
            pts = [(gx - s * 1.3 + t * s * 2.6, gy + math.sin(t * 9) * s * 0.4) for t in np.linspace(0, 1, 40)]
            dens = np.maximum(dens, stroke(S, pts, 3, seed=170 + i, dry=0.3, pool=0))
        else:             # 새 (V)
            dens = np.maximum(dens, stroke(S, [(gx - s * 1.2, gy - s * 0.6), (gx, gy + s * 0.5), (gx + s * 1.2, gy - s * 0.6)], 3, seed=180 + i, dry=0.3, pool=0))
    # 가운데 눈 (호루스)
    pts = [(c + math.cos(t) * S * 0.07, c + math.sin(t) * S * 0.035) for t in np.linspace(0, 2 * math.pi, 80)]
    dens = np.maximum(dens, stroke(S, pts, 6, seed=190, dry=0.3, pool=0.2))
    dens = np.maximum(dens, stroke(S, circle_path(S, S * 0.018, 0, 360, n=60, seed=191), 8, seed=192, dry=0.1, pool=0.4))
    for i in range(8):
        a = i / 8 * 2 * math.pi + 0.2
        p0 = (c + math.cos(a) * S * 0.13, c + math.sin(a) * S * 0.13)
        p1 = (c + math.cos(a) * S * 0.23, c + math.sin(a) * S * 0.23)
        dens = np.maximum(dens, stroke(S, line_path(p0, p1, 60, 1, 200 + i), 4, seed=210 + i, dry=0.5, pool=0.2))
    out["rune_sphinx"] = colorize(dens, 1.0, paper_seed=220)


def pools(out):
    R = np.random.default_rng(5)
    yy, xx = np.mgrid[0:S, 0:S]
    c = S / 2
    d = np.hypot(xx - c, yy - c)
    ang = np.arctan2(yy - c, xx - c)
    # 독: 짙은 먹빛 초록 웅덩이 + 가장자리 흘러내림 + 거품
    blob = d < S * 0.34 * (1 + 0.14 * np.sin(ang * 5 + 1) + 0.08 * np.sin(ang * 11 + 3))
    dens = wash(blob, 230, 0.8, 2.5)
    for k in range(10):
        a_ = R.uniform(0, 2 * np.pi)
        p0 = (c + np.cos(a_) * S * 0.28, c + np.sin(a_) * S * 0.28)
        p1 = (c + np.cos(a_) * S * R.uniform(0.38, 0.47), c + np.sin(a_) * S * R.uniform(0.38, 0.47))
        dens = np.maximum(dens, stroke(S, line_path(p0, p1, 60, 2, 240 + k), S * R.uniform(0.03, 0.06), seed=250 + k, dry=0.5, pool=0.2, bristles=8))
    inner = ndimage.gaussian_filter((d < S * 0.2).astype(np.float32), 8)
    base = colorize(dens, 0.95, (40, 150, 60), (8, 36, 16), (150, 255, 110), paper_seed=260)
    glow = colorize(np.clip(inner * 0.9, 0, 1), 0.55, (170, 255, 120), (90, 220, 80), (220, 255, 190))
    bub = np.zeros((S, S), np.float32)
    for k in range(12):
        bx, by = c + R.normal(0, S * 0.12, 2)
        rr = R.uniform(3, 8)
        ring = np.clip(1.4 - np.abs(np.hypot(xx - bx, yy - by) - rr), 0, 1)
        bub = np.maximum(bub, ring)
    out["poison"] = over(base, glow, colorize(bub, 0.9, (210, 255, 180), (120, 220, 110), (240, 255, 230)))
    # 그을음: 먹 튄 검붉은 자국 + 불씨 균열
    blob2 = d < S * 0.30 * (1 + 0.2 * np.sin(ang * 7 + 2) + 0.12 * np.sin(ang * 13))
    dens2 = wash(blob2, 270, 0.85, 2.5)
    for k in range(14):
        a_ = R.uniform(0, 2 * np.pi)
        p0 = (c + np.cos(a_) * S * 0.2, c + np.sin(a_) * S * 0.2)
        p1 = (c + np.cos(a_) * S * R.uniform(0.36, 0.48), c + np.sin(a_) * S * R.uniform(0.36, 0.48))
        dens2 = np.maximum(dens2, stroke(S, line_path(p0, p1, 60, 3, 280 + k), S * R.uniform(0.025, 0.05), seed=290 + k, dry=0.7, pool=0.3, bristles=8))
    crack = np.zeros((S, S), np.float32)
    for k in range(7):
        a_ = R.uniform(0, 2 * np.pi)
        pts = [(c, c)]
        for j in range(8):
            a_ += R.uniform(-0.5, 0.5)
            x, y = pts[-1]
            pts.append((x + np.cos(a_) * S * 0.04, y + np.sin(a_) * S * 0.04))
        crack = np.maximum(crack, stroke(S, [p for i in range(len(pts) - 1) for p in line_path(pts[i], pts[i + 1], 12)], 3.5, seed=300 + k, dry=0.3, pool=0, bristles=4))
    out["scorch"] = over(colorize(dens2, 0.92, (70, 20, 16), (14, 4, 4), (150, 50, 30), paper_seed=310),
                         colorize(ndimage.gaussian_filter(crack, 1.5) * 1.5, 1.0, (255, 150, 40), (255, 90, 20), (255, 230, 150)))


def build_all():
    out = {}
    circle_set(out)
    rect_set(out)
    for deg in (60, 90, 120):
        cone_set(out, deg)
    donut_set(out)
    marks(out)
    rune_sphinx(out)
    pools(out)
    return {k: img(v) for k, v in out.items()}


def flat_model(tex_ref, uv=(0, 0, 16, 16)):
    """바닥 평면 (1x1 블록, 가운데 원점). 위/아래 면"""
    return {"textures": {"0": tex_ref, "particle": tex_ref},
            "elements": [{"from": [0, 8, 0], "to": [16, 8, 16], "shade": False, "light_emission": 15,
                          "faces": {"up": {"uv": list(uv), "texture": "#0"}, "down": {"uv": list(uv), "texture": "#0"}}}]}


def upright_model(tex_ref):
    """세워진 평면 (머리 위 표식용 — 빌보드로 사용)"""
    return {"textures": {"0": tex_ref, "particle": tex_ref},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "shade": False, "light_emission": 15,
                          "faces": {"north": {"uv": [0, 0, 16, 16], "texture": "#0"}, "south": {"uv": [0, 0, 16, 16], "texture": "#0"}}}]}


def export(pack):
    imgs = build_all()
    names = []
    for name, im in imgs.items():
        ref = pack.texture(f"tele/{name}", im)
        if name == "mark_head":
            pack.item_model(f"tele/{name}", upright_model(ref))
        else:
            pack.item_model(f"tele/{name}", flat_model(ref))
        names.append(name)
    return imgs
