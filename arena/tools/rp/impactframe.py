"""타격 순간 화면 연출 (만화 집중선) — 시전자 화면에 타이틀로 0.3초

 글꼴 그림 한 장은 256 픽셀을 넘으면 안 그려지므로 가로 3조각(각 192x256)을 이어 붙인 글자 3개.
 bg:fx 글꼴 (U+E9A0~) — 기본 글꼴이 참조. 타이틀은 4배로 그려지고 색 코드가 그림에 곱해지므로
 흰 선으로 그려 두고 무기 색(&b · &6 ...)을 앞에 붙여 물들인다 (a39 bgImpactFrame).
 화면 가운데가 비어 있어 시야를 가리지 않는다.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import hud as H

CH0 = 0xE9A0
UNITS_H = 72                 # 글자 높이 (타이틀 4배 → GUI 288)
TILE_W, TILE_H = 192, 256
NT = 3
ASCENT = UNITS_H // 2 - 3    # 타이틀 글자 기준선 → 화면 가운데에 오게


def render():
    W, Ht = TILE_W * NT, TILE_H
    SS = 3
    im = Image.new("L", (W * SS, Ht * SS), 0)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    cx, cy = W * SS / 2, Ht * SS / 2
    R0 = math.hypot(cx, cy) * 1.05
    for i in range(70):
        a = rng.uniform(0, 2 * math.pi)
        rin = rng.uniform(0.42, 0.62)
        w = rng.uniform(1.2, 4.2) * SS
        # 가운데 쪽 시작점은 타원 (화면이 가로로 길어서)
        x0 = cx + math.cos(a) * cx * rin
        y0 = cy + math.sin(a) * cy * rin
        x1 = cx + math.cos(a) * R0
        y1 = cy + math.sin(a) * R0
        px, py = -math.sin(a) * w, math.cos(a) * w
        d.polygon([(x0, y0), (x1 + px, y1 + py), (x1 - px, y1 - py)], fill=int(rng.uniform(150, 235)))
    im = im.filter(ImageFilter.GaussianBlur(SS * 0.6)).resize((W, Ht), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255
    # 가장자리 쪽 진하게 (가운데로 갈수록 흐려짐)
    yy, xx = np.mgrid[0:Ht, 0:W]
    rr = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - Ht / 2) / (Ht / 2)) ** 2)
    a = a * np.clip((rr - 0.35) / 0.5, 0, 1)
    out = np.zeros((Ht, W, 4), np.uint8)
    out[..., :3] = 255
    out[..., 3] = np.clip(a * 0.85 * 255, 0, 255).astype(np.uint8)
    out[a * 0.85 * 255 < 20] = 0
    return Image.fromarray(out, "RGBA")


def export(pack):
    """그림 조각 · bg:fx 글꼴 → 타이틀에 넣을 문자열"""
    img = render()
    prov, s = [], ""
    for i in range(NT):
        t = img.crop((i * TILE_W, 0, (i + 1) * TILE_W, TILE_H)).copy()
        px = t.load()
        if px[TILE_W - 1, 0][3] == 0:
            px[TILE_W - 1, 0] = (0, 0, 0, 1)            # 폭 계산이 조각 전체가 되도록
        ch = chr(CH0 + i)
        fname = f"font/impact_frame_{i}.png"
        pack.png(f"assets/{H.NS}/textures/{fname}", t)
        prov.append({"type": "bitmap", "file": f"{H.NS}:{fname}", "height": UNITS_H, "ascent": ASCENT, "chars": [ch]})
        s += ch + (H.sp(-1) if i < NT - 1 else "")
    pack.put(f"assets/{H.NS}/font/fx.json", {"providers": prov})
    return s
