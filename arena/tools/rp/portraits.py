"""보스바 초상화: 보스 머리를 가까이서 렌더 → .cache/portraits/<id>.png"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import render as R
from world import World
import bossgen as BG

OUT = os.path.join(os.path.dirname(HERE), ".cache", "portraits")
BG_COL = {"talos": ((90, 40, 20), (20, 10, 8)), "sphinx": ((40, 70, 140), (10, 16, 36)),
          "ladon": ((30, 110, 90), (6, 26, 22)), "cyclops": ((110, 70, 40), (22, 14, 10))}


def render_one(bid, size=256):
    m, Rg, parts, anims, atlas = BG.load(bid)
    info = getattr(m, "INFO", {}).get("portrait", {})
    bone = info.get("bone", "head")
    pose = anims["idle"]["keys"][0][0]
    W = Rg.world(pose)
    k = Rg.k
    M = W[bone]
    w = World(8, 8, 8)
    w.set(0, 0, 0, "stone")
    pal = R.Palette(w.pal)
    sun = np.array((-0.3, 0.8, 0.6)); sun /= np.linalg.norm(sun)
    mesh = R.Mesh()
    base = np.array((200.0, 0.0, 200.0))
    BG.add_to_mesh(mesh, Rg, None, atlas.image(), pose, tuple(base), 0, sun, bid)
    # 머리 뼈의 정면(+Z)·위(+Y) 방향 (월드, yaw 0)
    fwd = M[:3, 2] / np.linalg.norm(M[:3, 2]); up = M[:3, 1] / np.linalg.norm(M[:3, 1])
    center = base + (M @ np.array([0, info.get("cy", 3.0) / 16, info.get("cz", 2.0) / 16, 1]))[:3] * k
    d = info.get("dist", 1.6) * k
    side = np.cross(up, fwd)
    cam = center + fwd * d + up * d * 0.05 + side * d * 0.35
    hx, hy, hz = center
    im = R.render(w.vox, pal, size, size, cam, (hx, hy, hz), fov=40, mesh=mesh, ss=2, sky_top=(0, 0, 0), sky_hor=(0, 0, 0), fog_dist=1e9, post=False,
                  amb_col=(0.75, 0.75, 0.8))
    arr = np.asarray(im).astype(np.float32)
    # 배경 (검정) → 원형 그라데이션
    top, bot = BG_COL.get(bid, ((60, 60, 60), (10, 10, 10)))
    yy, xx = np.mgrid[0:size, 0:size]
    rr = np.hypot(xx - size / 2, yy - size / 2) / (size / 2)
    bgc = np.array(top)[None, None, :] * (1 - rr[..., None]) + np.array(bot)[None, None, :] * rr[..., None]
    mask = (arr.sum(2) < 3)[..., None]
    arr = np.where(mask, bgc, arr)
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, f"{bid}.png"))
    return out


def render_all():
    for b in BG.BOSS_IDS:
        render_one(b)
