"""보스 리그 미리보기 렌더러 (서버 없이 확인용)

spawn.mcfunction 의 item_display (item_model + transformation) 를 읽어, 리소스팩 모델(큐보이드)을
3/4 시점 정사영으로 그린다. 텍스처 업그레이드 전/후 비교에 쓴다.
python3 render_rig.py minotaur [atlas.png] out.png
"""
import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..")
PACK = os.path.join(REPO, "resourcepack", "olympus_pack", "assets", "oly")


def load_spawn(boss):
    parts = []
    for line in open(os.path.join(REPO, boss, "spawn.mcfunction"), encoding="utf-8"):
        m = re.search(r"item_model':'oly:([a-z_]+)/([a-z0-9_]+)'.*?transformation:\[([^\]]+)\]", line)
        if m:
            v = [float(x.rstrip("f")) for x in m.group(3).split(",")]
            parts.append((m.group(2), np.array(v).reshape(4, 4)))
    return parts


def rot_matrix(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


FACE_CORNERS = {
    "north": lambda f, t: [(t[0], t[1], f[2]), (f[0], t[1], f[2]), (f[0], f[1], f[2]), (t[0], f[1], f[2])],
    "south": lambda f, t: [(f[0], t[1], t[2]), (t[0], t[1], t[2]), (t[0], f[1], t[2]), (f[0], f[1], t[2])],
    "east": lambda f, t: [(t[0], t[1], t[2]), (t[0], t[1], f[2]), (t[0], f[1], f[2]), (t[0], f[1], t[2])],
    "west": lambda f, t: [(f[0], t[1], f[2]), (f[0], t[1], t[2]), (f[0], f[1], t[2]), (f[0], f[1], f[2])],
    "up": lambda f, t: [(f[0], t[1], f[2]), (t[0], t[1], f[2]), (t[0], t[1], t[2]), (f[0], t[1], t[2])],
    "down": lambda f, t: [(f[0], f[1], t[2]), (t[0], f[1], t[2]), (t[0], f[1], f[2]), (f[0], f[1], f[2])],
}
SHADE = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.6, "west": 0.6}


def faces_of(boss, part, M):
    mdl = json.load(open(os.path.join(PACK, "models", "boss", boss, part + ".json")))
    out = []
    for el in mdl["elements"]:
        f, t = el["from"], el["to"]
        rot = el.get("rotation")
        for fname, fd in el["faces"].items():
            pts = np.array(FACE_CORNERS[fname](f, t), dtype=float)
            if rot:
                R = rot_matrix(rot["axis"], rot["angle"])
                o = np.array(rot["origin"], dtype=float)
                pts = (pts - o) @ R.T + o
            local = pts / 16.0 - 0.5
            # 게임의 item_display 는 아이템 모델을 Y 축으로 180° 돌려서 그린다 (ItemDisplay 렌더러)
            local = local * np.array([-1.0, 1.0, -1.0])
            world = (np.c_[local, np.ones(4)] @ M.T)[:, :3]
            out.append((world, fd["uv"], SHADE[fname]))
    return out


def render(boss, atlas_path, out_path, yaw=35, pitch=20, size=560):
    atlas = np.asarray(Image.open(atlas_path).convert("RGBA"), dtype=float)
    A = atlas.shape[0] / 16.0
    faces = []
    for part, M in load_spawn(boss):
        faces += faces_of(boss, part, M)
    Ry = rot_matrix("y", yaw)
    Rx = rot_matrix("x", pitch)
    V = Rx @ Ry
    allp = np.concatenate([f[0] for f in faces]) @ V.T
    mn, mx = allp.min(0), allp.max(0)
    scale = (size * 0.86) / max(mx[0] - mn[0], mx[1] - mn[1])
    img = np.zeros((size, size, 4))
    img[..., :3] = (40, 42, 48)
    img[..., 3] = 255
    zbuf = np.full((size, size), -1e9)
    cx = (mn[0] + mx[0]) / 2
    cy = (mn[1] + mx[1]) / 2
    for world, uv, sh in faces:
        p = world @ V.T
        sx = (p[:, 0] - cx) * scale + size / 2
        sy = size / 2 - (p[:, 1] - cy) * scale
        z = p[:, 2]
        u0, v0, u1, v1 = [c * A for c in uv]
        tuv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        for tri in ((0, 1, 2), (0, 2, 3)):
            xs, ys = sx[list(tri)], sy[list(tri)]
            x0, x1 = int(max(0, math.floor(xs.min()))), int(min(size - 1, math.ceil(xs.max())))
            y0, y1 = int(max(0, math.floor(ys.min()))), int(min(size - 1, math.ceil(ys.max())))
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            (ax, ay), (bx, by), (qx, qy) = zip(xs, ys)
            den = (by - qy) * (ax - qx) + (qx - bx) * (ay - qy)
            if abs(den) < 1e-9:
                continue
            w0 = ((by - qy) * (gx - qx) + (qx - bx) * (gy - qy)) / den
            w1 = ((qy - ay) * (gx - qx) + (ax - qx) * (gy - qy)) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not inside.any():
                continue
            zz = w0 * z[tri[0]] + w1 * z[tri[1]] + w2 * z[tri[2]]
            uu = w0 * tuv[tri[0]][0] + w1 * tuv[tri[1]][0] + w2 * tuv[tri[2]][0]
            vv = w0 * tuv[tri[0]][1] + w1 * tuv[tri[1]][1] + w2 * tuv[tri[2]][1]
            ui = np.clip(np.floor(np.minimum(uu, atlas.shape[1] - 1e-3)).astype(int), 0, atlas.shape[1] - 1)
            vi = np.clip(np.floor(np.minimum(vv, atlas.shape[0] - 1e-3)).astype(int), 0, atlas.shape[0] - 1)
            col = atlas[vi, ui]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            ok = inside & (zz < 1e8) & (col[..., 3] > 8) & (-zz > sub)
            sub[ok] = -zz[ok]
            tgt = img[y0:y1 + 1, x0:x1 + 1]
            tgt[ok, :3] = col[ok, :3] * sh
    Image.fromarray(img.astype(np.uint8), "RGBA").save(out_path)


if __name__ == "__main__":
    boss = sys.argv[1]
    atlas = sys.argv[2] if len(sys.argv) > 3 else os.path.join(PACK, "textures", "item", "boss", boss + ".png")
    render(boss, atlas, sys.argv[-1])


# ── spawn.mcfunction 이 없는 보스: 애니메이션 프레임 + 파츠 순서(프레임 좌표로 역산)
LEGS = ["legfl", "legfl_lo", "legbl", "legbl_lo", "legfr", "legfr_lo", "legbr", "legbr_lo"]
ORDER = {
    "cerberus": ["body"] + LEGS + ["hl", "hl_h", "hl_h_e", "hl_h_j", "hm", "hm_h", "hm_h_e", "hm_h_j",
                                   "hr", "hr_h", "hr_h_e", "hr_h_j", "tail0", "tail1", "tail2", "tail3", "flame"],
    "chimera": ["body"] + LEGS + ["mane", "head", "eyes", "jaw", "maw", "goat", "goat_h", "ghornr1", "ghornr2", "ghornr3",
                                  "ghornl1", "ghornl2", "ghornl3", "tail0", "tail1", "tail2", "tail3", "tail4", "tail5", "snake_h"],
    "hydra": ["body"] + LEGS + ["tail0", "tail1", "tail2", "tail3", "tail4"]
    + [f"n{k}_{p}" for k in range(7) for p in ("0", "1", "2", "3", "h", "he", "j")],
    "medusa": [f"coil{i}" for i in range(12)] + ["waist", "torso", "head", "head_e"]
    + [f"hair{i}{b}" for i in range(9) for b in ("", "b")] + ["arml", "arml_lo", "armr", "armr_lo", "bow"],
}
FRAME = {"cerberus": "idle/0", "chimera": "attack/0", "hydra": "idle/0", "medusa": "gaze/0"}


def load_frame(boss):
    parts = {}
    for line in open(os.path.join(REPO, boss, FRAME[boss] + ".mcfunction"), encoding="utf-8"):
        m = re.search(r"6f6c7962-0000-000\d-0000-([0-9a-f]{12}).*?transformation:\[([^\]]+)\]", line)
        if m:
            v = [float(x.rstrip("f")) for x in m.group(2).split(",")]
            parts[int(m.group(1), 16)] = np.array(v).reshape(4, 4)
    names = ORDER[boss]
    return [(names[i], M) for i, M in sorted(parts.items()) if i < len(names)]


_load_spawn = load_spawn


def load_spawn(boss):  # noqa: F811
    if os.path.exists(os.path.join(REPO, boss, "spawn.mcfunction")):
        return _load_spawn(boss)
    return load_frame(boss)
