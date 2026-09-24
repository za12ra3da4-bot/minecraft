"""보스 텍스처 HD (512 → 1024) — UV · 리그 · 애니메이션은 그대로

모델 UV 는 0..16 비율 좌표라 아틀라스 크기를 두 배로 해도 같은 자리를 가리킨다.
원본을 2배로 키운 뒤, 면마다 재질을 판정해 질감과 명암을 새로 입힌다 (원본의 그림은 살린다).
  재질: fur(털) · skin(피부) · scale(비늘) · horn(뿔·발톱) · metal(금속) · wood · cloth · flesh(촉수) · eye
python3 boss_hd.py [보스 ...]   (원본은 tools/boss_fx/boss_src/<보스>.png 에 한 번만 보관)
"""
import colorsys
import glob
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..", "..", "resourcepack", "olympus_pack", "assets", "oly")
SRC = os.path.join(HERE, "boss_src")
BOSSES = ["minotaur", "nemean_lion", "chimera", "cerberus", "hydra", "medusa", "scylla"]
N = 1024

rng = np.random.default_rng(11)


def smooth_noise(h, w, sy, sx, seed):
    r = np.random.default_rng(seed)
    g = r.random((int(h / sy) + 3, int(w / sx) + 3))
    ys, xs = np.mgrid[0:h, 0:w]
    fy, fx = ys / sy, xs / sx
    y0, x0 = fy.astype(int), fx.astype(int)
    ty, tx = fy - y0, fx - x0
    ty, tx = ty * ty * (3 - 2 * ty), tx * tx * (3 - 2 * tx)
    a = g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx
    b = g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx
    return (a * (1 - ty) + b * ty) * 2 - 1


def classify(boss, part, rgb):
    r, g, b = rgb / 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hd = h * 360
    if part.endswith(("eyes", "_e", "_he")) or "eye" in part:
        return "eye"
    if v > 0.9 and s > 0.45:
        return "eye"
    if "horn" in part:
        return "horn"
    if boss == "minotaur" and part == "axe":
        return "metal" if s < 0.2 else "wood"
    if boss == "medusa" and part == "bow":
        return "metal" if (s > 0.45 and 30 < hd < 60) else "wood"
    if s > 0.6 and 38 < hd < 56 and v > 0.7 and boss in ("minotaur", "medusa", "scylla", "cerberus", "hydra"):
        return "metal"                       # 금 장식 (네발 짐승의 황갈색 털은 제외)
    if s < 0.12 and v > 0.72 and boss not in ("medusa",):
        return "horn"                        # 발굽 · 발톱 · 이빨 (밝은 무채색)
    if 70 < hd < 170 and s > 0.2:
        return "scale"
    if boss == "scylla" and part.startswith(("t", "base")):
        return "flesh"
    if boss == "scylla" and part.startswith("dog"):
        return "fur"
    if (hd > 270 or hd < 12) and s > 0.45 and part.startswith(("loin", "waist", "torso")):
        return "cloth"
    if boss in ("medusa", "scylla"):
        if part in ("torso", "waist") and s < 0.2:
            return "cloth"
        return "skin"
    if boss == "minotaur":
        if part in ("torso", "arml", "armr", "arml_lo", "armr_lo", "handl", "handr"):
            return "skin"
        if part in ("loin_f", "loin_b"):
            return "cloth"
        if part == "head" and v > 0.5:
            return "skin"                    # 주둥이
    return "fur"


def pattern(cls, h, w, face, seed):
    """밝기 변조 (-..+). 결 방향: 옆면은 세로(v), 윗면/아랫면은 가로"""
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    side = face in ("north", "south", "east", "west")
    if cls == "fur":
        st = smooth_noise(h, w, 9.0 if side else 2.2, 1.3 if side else 7.0, seed)
        clump = smooth_noise(h, w, 16, 10, seed + 1)
        m = st * 0.16 + clump * 0.07
        if side:
            m -= (ys / max(1, h - 1)) ** 2 * 0.1            # 털끝 쪽 어둡게
        return m
    if cls == "scale":
        cell = 5.0
        row = np.floor(ys / (cell * 0.8))
        u = ((xs + (row % 2) * cell / 2) % cell) / cell
        vv = (ys % (cell * 0.8)) / (cell * 0.8)
        d = np.hypot(u - 0.5, (vv - 0.25) * 1.2)
        m = np.where(d < 0.52, 0.12 - d * 0.35, -0.2)
        return m + smooth_noise(h, w, 20, 20, seed) * 0.05
    if cls == "skin":
        return smooth_noise(h, w, 14, 14, seed) * 0.06 + (rng.random((h, w)) - 0.5) * 0.03
    if cls == "horn":
        return np.sin(ys * (1.3 if side else 0.3)) * 0.06 + smooth_noise(h, w, 6, 30, seed) * 0.06
    if cls == "metal":
        band = np.exp(-((ys / max(1, h - 1) - 0.3) ** 2) / 0.02) * 0.28
        return band + smooth_noise(h, w, 1.5, 24, seed) * 0.06
    if cls == "wood":
        return np.sin(xs * 0.9 + smooth_noise(h, w, 12, 3, seed) * 3) * 0.08
    if cls == "cloth":
        weave = (((xs.astype(int) + ys.astype(int)) % 2) - 0.5) * 0.05
        fold = np.sin(xs / max(2, w) * np.pi * 5) * 0.08
        return weave + fold
    if cls == "flesh":
        return smooth_noise(h, w, 7, 7, seed) * 0.12 + smooth_noise(h, w, 2.5, 2.5, seed + 3) * 0.05
    return np.zeros((h, w))


def shade_face(region, cls, face, seed):
    h, w, _ = region.shape
    rgb = region[..., :3].astype(float)
    a = region[..., 3]
    if cls == "eye" or h < 2 or w < 2:
        return region
    mean = rgb.reshape(-1, 3).mean(0)
    # 원본의 그림은 살리고(0.6) 잡음은 줄인다(평균 0.4)
    base = rgb * 0.6 + mean * 0.4
    m = pattern(cls, h, w, face, seed)
    ys = np.arange(h)[:, None] / max(1, h - 1)
    if face in ("north", "south", "east", "west"):
        m = m + (0.08 - ys * 0.2)                            # 위 밝고 아래 그늘
    elif face == "up":
        m = m + 0.06
    else:
        m = m - 0.12
    # 모서리 AO · 윗모서리 하이라이트
    e = np.zeros((h, w))
    e[0, :] += 0.08
    e[:, 0] -= 0.05
    e[:, -1] -= 0.05
    e[-1, :] -= 0.12
    if h > 6 and w > 6:
        e[1, :] += 0.04
    m = m + e
    if cls == "metal":
        m = m * 1.2
    out = np.clip(base * (1 + m)[..., None], 0, 255)
    res = region.copy().astype(float)
    res[..., :3] = out
    res[..., 3] = a
    return res


def upgrade(boss):
    os.makedirs(SRC, exist_ok=True)
    tex = os.path.join(PACK, "textures", "item", "boss", boss + ".png")
    src = os.path.join(SRC, boss + ".png")
    if not os.path.exists(src):
        shutil.copy(tex, src)                                # 원본 512 보관 (다시 돌려도 원본에서 시작)
    old = Image.open(src).convert("RGBA")
    k = N / old.width
    big = np.asarray(old.resize((N, N), Image.NEAREST), dtype=float)
    out = big.copy()
    seen = set()
    stats = {}
    for f in sorted(glob.glob(os.path.join(PACK, "models", "boss", boss, "*.json"))):
        part = os.path.basename(f)[:-5]
        for ei, el in enumerate(json.load(open(f))["elements"]):
            for face, fd in el["faces"].items():
                u0, v0, u1, v1 = fd["uv"]
                x0, x1 = sorted((u0 * N / 16, u1 * N / 16))
                y0, y1 = sorted((v0 * N / 16, v1 * N / 16))
                x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
                key = (x0, y0, x1, y1)
                if key in seen or x1 - x0 < 1 or y1 - y0 < 1:
                    continue
                seen.add(key)
                reg = big[y0:y1, x0:x1]
                if reg[..., 3].max() == 0:
                    continue
                cls = classify(boss, part, reg[..., :3].reshape(-1, 3).mean(0))
                stats[cls] = stats.get(cls, 0) + 1
                out[y0:y1, x0:x1] = shade_face(reg, cls, face, hash((boss, part, ei, face)) % 100000)
    Image.fromarray(out.astype(np.uint8), "RGBA").save(tex, optimize=True)
    return stats


if __name__ == "__main__":
    for b in (sys.argv[1:] or BOSSES):
        print(b, upgrade(b))
