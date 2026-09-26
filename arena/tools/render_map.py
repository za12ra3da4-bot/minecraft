"""맵 미리보기 렌더: python3 render_map.py [shot ...]"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "mapgen"))

from layout import *
import render as R
from build_map import load

OUT = os.path.join(os.path.dirname(HERE), "preview")


def shots():
    ax, az = altar_pos("ares"); tx, tz = altar_pos("athena"); hx, hz = altar_pos("hermes"); dx, dz = altar_pos("demeter")
    bx, bz = team_base("red")
    s = {
        "overview": dict(cam=(C[0] + 150, 175, C[1] + 215), target=(C[0], 12, C[1] - 5), fov=48),
        "top": dict(cam=(C[0], 300, C[1] + 0.001), target=(C[0], 0, C[1]), ortho=4.0, W=1024, H=1024, ss=1),
        "temple": dict(cam=(C[0] + 58, G + 42, C[1] + 70), target=(C[0], G + 10, C[1]), fov=52),
        "temple_in": dict(cam=(C[0] + 12, G + 12, C[1] + 26), target=(C[0], G + 11, C[1]), fov=72),
        "ares": dict(cam=(ax - 40, G + 36, az + 38), target=(ax, G + 10, az), fov=55),
        "athena": dict(cam=(tx - 42, G + 26, tz - 30), target=(tx, G + 3, tz), fov=55),
        "hermes": dict(cam=(hx + 40, G + 30, hz - 36), target=(hx, G + 4, hz), fov=55),
        "demeter": dict(cam=(dx + 38, G + 24, dz + 40), target=(dx, G - 2, dz), fov=55),
        "base": dict(cam=(bx + 42, BASE_H + 36, bz + 50), target=(bx, BASE_H, bz), fov=55),
    }
    s["lobby"] = dict(cam=(C[0] + 26, 100, C[1] + 30), target=(C[0], 85, C[1]), fov=60)
    for lid in LAIRS:
        lx, lz = lair_pos(lid)
        v = (C[0] - lx, C[1] - lz)
        s["lair_" + lid] = dict(cam=(lx + v[0] * 0.55, G + 32, lz + v[1] * 0.55), target=(lx, G, lz), fov=55)
    return s


def main(names):
    w = load()
    pal = R.Palette(w.pal)
    S = shots()
    for n in names or S.keys():
        p = S[n]
        t = time.time()
        W = p.get("W", 1280); H = p.get("H", 720)
        im = R.render(w.vox, pal, W, H, p["cam"], p["target"], fov=p.get("fov", 60), ortho_scale=p.get("ortho"),
                      ss=p.get("ss", 2), fog_dist=1e9 if p.get("ortho") else 600)
        im.save(os.path.join(OUT, f"map_{n}.png"))
        print(n, f"{time.time() - t:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
