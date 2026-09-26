"""보스 모델 → 리소스팩 파츠 + 데이터팩 함수 + 미리보기 메시"""
import importlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "bosses"))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np
from PIL import Image

from modelkit import *

BOSS_IDS = ["talos", "sphinx", "ladon", "cyclops"]


def load(bid):
    m = importlib.import_module(bid)
    R, parts, anims = m.build()
    atlas = bake_parts(parts, tpu=2, atlas_size=256, seed=sum(map(ord, bid)) * 131)
    return m, R, parts, anims, atlas


def part_uuid(bi, pi):
    return f"62670000-{bi + 1:04x}-4000-8000-{pi:012x}"


def uuid_ints(u):
    h = u.replace("-", "")
    out = []
    for i in range(4):
        v = int(h[i * 8:(i + 1) * 8], 16)
        if v >= 2 ** 31:
            v -= 2 ** 32
        out.append(v)
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  미리보기 메시
# ─────────────────────────────────────────────────────────────────────────────
def corners(b, f):
    x0, y0, z0 = b.frm; x1, y1, z1 = b.to
    return {
        "south": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        "north": [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
        "east": [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
        "west": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
        "up": [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
        "down": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
    }[f]


def rot_elem(p, rot):
    ax, ang, org = rot
    p = np.array(p, float) - org
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    x, y, z = p
    if ax == "x":
        p = np.array([x, c * y - s * z, s * y + c * z])
    elif ax == "y":
        p = np.array([c * x + s * z, y, -s * x + c * z])
    else:
        p = np.array([c * x - s * y, s * x + c * y, z])
    return p + org


def add_to_mesh(mesh, R, parts_by_bone, atlas_img, pose, pos, yaw, sun, key, extra_mat=None):
    import render as RR
    tid = mesh.texture(key, atlas_img)
    AW, AH = atlas_img.size
    mats = R.display_mats(pose)
    a = math.radians(-yaw)
    Yaw = np.array([[math.cos(a), 0, math.sin(a), 0], [0, 1, 0, 0], [-math.sin(a), 0, math.cos(a), 0], [0, 0, 0, 1]])
    for bone, M in mats.items():
        part = R.bones[bone].part
        full = tr(*pos) @ Yaw @ (extra_mat if extra_mat is not None else np.eye(4)) @ M @ ry(180)
        for b in part.boxes:
            for f in FACES:
                if f not in b.uv:
                    continue
                cs = corners(b, f)
                if b.rot:
                    cs = [rot_elem(c, (b.rot[0], b.rot[1], np.array(b.rot[2], float))) for c in cs]
                pts = []
                for c in cs:
                    v = full @ np.array([c[0] / 16, c[1] / 16, c[2] / 16, 1.0])
                    pts.append(v[:3])
                n = np.cross(pts[1] - pts[0], pts[3] - pts[0])
                x0, y0, x1, y1 = b.uv[f]
                uv = (x0 / AW, y0 / AH, x1 / AW, y1 / AH)
                glow = part.glow or not b.shade
                light = (1.25, 1.2, 1.1) if glow else RR.face_light(n, sun)
                mesh.quad(pts[0], pts[1], pts[2], pts[3], uv, tid, flags=1 if glow else 0, light=light)


def export(pack, dp_dir):
    """리소스팩 파츠 + 데이터팩 함수 전부"""
    meta = {}
    for bi, bid in enumerate(BOSS_IDS):
        m, R, parts, anims, atlas = load(bid)
        img = atlas.image()
        ref = pack.texture(f"boss/{bid}", img)
        for p in parts:
            pack.item_model(f"boss/{bid}/{p.name}", model_json(p, ref, img.size[0], img.size[1]))
        fdir = os.path.join(dp_dir, "boss", bid)
        os.makedirs(os.path.join(fdir, "anim"), exist_ok=True)
        bones = [n for n in R.order if R.bones[n].part is not None]
        rest = R.display_mats({})
        # 소환 (실행 위치 = 히트박스)
        lines = []
        for pi, n in enumerate(bones):
            u = part_uuid(bi, pi)
            ints = uuid_ints(u)
            M = rest[n]
            part = R.bones[n].part
            bright = ",brightness:{sky:15,block:15}" if part.glow else ""
            lines.append(
                f"summon minecraft:item_display ~ ~ ~ {{UUID:[I;{ints[0]},{ints[1]},{ints[2]},{ints[3]}],"
                f"Tags:[\"bg\",\"bgb\",\"bgb_{bid}\",\"bgb_part\"],item:{{id:\"minecraft:paper\",count:1,"
                f"components:{{\"minecraft:item_model\":\"bg:boss/{bid}/{part.name}\"}}}},item_display:\"none\","
                f"transformation:{mat_str(M)},teleport_duration:2,interpolation_duration:0,view_range:3.0f,shadow_radius:0f{bright}}}")
        lines.append(f"function bg:boss/{bid}/tp")
        write(os.path.join(fdir, "spawn.mcfunction"), lines)
        write(os.path.join(fdir, "remove.mcfunction"), [f"kill @e[type=item_display,tag=bgb_{bid}]"])
        # 위치 동기화 (히트박스로 실행: execute as <hb> at @s run function ...)
        write(os.path.join(fdir, "tp.mcfunction"), [f"execute rotated as @s as @e[type=item_display,tag=bgb_{bid},distance=..16] run tp @s ~ ~ ~ ~ 0"])
        am = {}
        for an, spec in anims.items():
            keys = spec["keys"]
            adir = os.path.join(fdir, "anim", an)
            os.makedirs(adir, exist_ok=True)
            for k, (pose, ticks) in enumerate(keys):
                mats = R.display_mats(pose)
                ls = []
                for pi, n in enumerate(bones):
                    ls.append(f"data merge entity {part_uuid(bi, pi)} {{transformation:{mat_str(mats[n])},start_interpolation:0,interpolation_duration:{int(ticks)}}}")
                write(os.path.join(adir, f"{k}.mcfunction"), ls)
            am[an] = {"loop": bool(spec.get("loop")), "ticks": [int(t) for _, t in keys]}
        meta[bid] = {"anims": am, "parts": len(bones), "info": getattr(m, "INFO", {})}
    return meta


def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
