"""아이템 모델 미리보기 — 인벤토리(GUI 표시 변환) 와 3/4 입체"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

from render_rig import FACE_CORNERS, rot_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..", "..", "resourcepack", "olympus_pack", "assets")
SH = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.6, "west": 0.6}


def tex_path(t):
    ns, p = t.split(":")
    return os.path.join(PACK, ns, "textures", p + ".png")


def euler(r):
    return rot_matrix("z", r[2]) @ rot_matrix("y", r[1]) @ rot_matrix("x", r[0])


def render_model(mp, size=160, view="gui", yaw=30, pitch=25):
    mdl = json.load(open(mp))
    while "elements" not in mdl and str(mdl.get("parent", "")).startswith("oly:"):
        ns, p = mdl["parent"].split(":")
        par = json.load(open(os.path.join(PACK, ns, "models", p + ".json")))
        disp = dict(par.get("display", {}), **mdl.get("display", {}))
        mdl = dict(par, display=disp)
    texs = {k: np.asarray(Image.open(tex_path(v)).convert("RGBA"), dtype=float)
            for k, v in mdl["textures"].items() if not v.startswith("#")}
    V = np.eye(3)
    if view == "gui":
        g = mdl.get("display", {}).get("gui")
        if g:
            V = euler(g.get("rotation", [0, 0, 0]))
    else:
        V = rot_matrix("x", pitch) @ rot_matrix("y", yaw)
    img = np.zeros((size, size, 4))
    zb = np.full((size, size), -1e9)
    sc = size / 18.0
    for el in mdl["elements"]:
        f, t = el["from"], el["to"]
        rot = el.get("rotation")
        for fn, fd in el["faces"].items():
            pts = np.array(FACE_CORNERS[fn](f, t), dtype=float)
            if rot:
                R = rot_matrix(rot["axis"], rot["angle"])
                o = np.array(rot["origin"], dtype=float)
                pts = (pts - o) @ R.T + o
            p = (pts - 8) @ V.T
            sx = p[:, 0] * sc + size / 2
            sy = size / 2 - p[:, 1] * sc
            z = p[:, 2]
            tex = texs[fd["texture"].lstrip("#")]
            A = tex.shape[0] / 16.0
            u0, v0, u1, v1 = [c * A for c in fd["uv"]]
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
                ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
                zz = w0 * z[tri[0]] + w1 * z[tri[1]] + w2 * z[tri[2]]
                uu = w0 * tuv[tri[0]][0] + w1 * tuv[tri[1]][0] + w2 * tuv[tri[2]][0]
                vv = w0 * tuv[tri[0]][1] + w1 * tuv[tri[1]][1] + w2 * tuv[tri[2]][1]
                ui = np.clip(np.floor(uu).astype(int), 0, tex.shape[1] - 1)
                vi = np.clip(np.floor(vv).astype(int), 0, tex.shape[0] - 1)
                col = tex[vi, ui]
                sub = zb[y0:y1 + 1, x0:x1 + 1]
                ok = ins & (col[..., 3] > 8) & (zz > sub)
                sub[ok] = zz[ok]
                tg = img[y0:y1 + 1, x0:x1 + 1]
                tg[ok, :3] = col[ok, :3] * SH[fn]
                tg[ok, 3] = 255
    return Image.fromarray(img.astype(np.uint8), "RGBA")


if __name__ == "__main__":
    render_model(sys.argv[1]).save(sys.argv[2])
