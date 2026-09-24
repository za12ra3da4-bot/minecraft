"""스킬 아이콘 일러스트 (64px 아이템 + 32px 폰트) — icons.py 의 구도를 일러스트 조명으로 다시 그린다"""
import math

import numpy as np
from PIL import Image, ImageDraw

import icons
from paint import R, Painting, ellipse

# 픽셀 재질 → 일러스트 재질
MAP = {"bronze": "bronze", "steel": "steel", "bone": "bone", "fire": "ember", "hellfire": "ember", "soul": "soulfire",
       "poison": "venom", "stone": "marble", "eye": "gem_amber", "blood": "red", "wave": "silver", "water": "gem_blue",
       "flesh": "purple", "fur": "fur", "dark": "black", "scale": "green", "jade": "teal", "red": "red", "white": "marble",
       "gold": "gold"}

FIELD = {  # 보스별 에나멜 바탕 (어둠, 밝음)
    "minotaur": ((40, 6, 4), (150, 36, 20)), "nemean_lion": ((50, 26, 4), (176, 110, 30)),
    "chimera": ((44, 12, 4), (170, 60, 20)), "cerberus": ((14, 6, 24), (84, 40, 130)),
    "hydra": ((6, 26, 12), (40, 120, 60)), "medusa": ((4, 30, 28), (30, 130, 116)),
    "scylla": ((4, 14, 40), (30, 80, 160)), "common": ((30, 24, 16), (120, 96, 60)),
}


class MaskSheet:
    """icons.py 의 그리기 함수가 쓰는 Sheet 흉내 (0..32 좌표 → 512 마스크)"""

    def __init__(self):
        self.layers = []
        icons.Sheet.K = R / 32.0

    def layer(self, material):
        im = Image.new("L", (R, R), 0)
        self.layers.append((material, im))
        return ImageDraw.Draw(im)


def frame(p, boss):
    """청동 메달 틀 + 에나멜 바탕 (가운데 밝은 방사형)"""
    rr = []
    for i in range(160):
        a = i / 160 * 2 * math.pi
        # 둥근 사각형
        c, s = math.cos(a), math.sin(a)
        k = (abs(c) ** 5 + abs(s) ** 5) ** (-1 / 5)
        rr.append((0.5 + c * k * 0.49, 0.5 + s * k * 0.49))
    p.shape("bronze", rr, bevel=0.05)
    inner = [(0.5 + (x - 0.5) * 0.84, 0.5 + (y - 0.5) * 0.84) for x, y in rr]
    ys, xs = np.mgrid[0:R, 0:R] / R
    d = np.hypot(xs - 0.5, ys - 0.42)
    dark, light = FIELD[boss]
    t = np.clip(1 - d * 1.9, 0, 1) ** 1.4
    col = np.array(dark, float) + (np.array(light, float) - np.array(dark, float)) * t[..., None]
    cov = p.mask(inner)
    p.shape("black", inner, bevel=0.02, height=0.3)
    p.rgb = p.rgb * (1 - cov[..., None]) + col * cov[..., None] * (0.85 + 0.15 * np.random.default_rng(2).random((R, R)))[..., None]
    for x, y in ((0.1, 0.1), (0.9, 0.1), (0.1, 0.9), (0.9, 0.9)):
        p.shape("gold", ellipse((x, y), 0.028, 0.028), bevel=0.02, height=1.4)


def render(boss, fn, size=64):
    p = Painting()
    frame(p, boss)
    sh = MaskSheet()
    fn(sh)
    for mat, im in sh.layers:
        cov = np.asarray(im, dtype=float) / 255.0
        if cov.max() < 0.5:
            continue
        m = MAP[mat]
        p.shape_mask(m, cov, bevel=0.03)
    return p.finish(size=size)


def build_all(out_item, out_font):
    import os
    for i, (boss, key, fn, label) in enumerate(icons.ICONS):
        name = f"{boss}_{key}"
        big = render(boss, fn, 64)
        big.save(os.path.join(out_item, name + ".png"), optimize=True)
        big.resize((32, 32), Image.LANCZOS).save(os.path.join(out_font, name + ".png"), optimize=True)


if __name__ == "__main__":
    S = "/tmp/claude-0/-home-user-minecraft/2d68590e-6d8d-5099-8a63-c0ef9e8e5738/scratchpad/"
    W = Image.new("RGBA", (9 * 136, 4 * 136), (40, 38, 36, 255))
    for i, (boss, key, fn, label) in enumerate(icons.ICONS):
        im = render(boss, fn, 64).resize((128, 128), Image.NEAREST)
        W.alpha_composite(im, ((i % 9) * 136 + 4, (i // 9) * 136 + 4))
    W.save(S + "icons_ill.png")
