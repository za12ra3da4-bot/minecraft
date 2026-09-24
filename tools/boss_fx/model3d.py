"""입체 아이템 모델 빌더 — 큐보이드 요소 + 면마다 전용 UV 칸 + 재질별 HD 채색

사용:
    m = M3("xiphos", density=6)
    m.box((7, 0, 7.5), (9, 6, 8.5), "leather")
    ...
    m.save(parent_display="handheld", diag=True)

- diag=True : 모든 요소를 (8,8,8) 기준 z축 -45° 로 돌려 바닐라 스프라이트와 같은 대각선
              (손잡이 왼쪽 아래 → 끝 오른쪽 위) 으로 만든다 → 바닐라 손 자세(display)가 그대로 맞는다.
- 면 텍스처는 요소 크기 x density 픽셀로 아틀라스에 선반식으로 채워 넣는다 (겹침 없음).
"""
import json
import math
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "resourcepack", "olympus_pack", "assets", "oly")
VAN = os.path.join(HERE, "vanilla")

PAL = {
    "steel": [(52, 56, 66), (96, 102, 116), (150, 158, 172), (198, 206, 218), (240, 246, 252)],
    "dsteel": [(22, 22, 28), (40, 40, 50), (62, 62, 76), (92, 92, 110), (140, 140, 160)],
    "bronze": [(78, 46, 18), (122, 78, 32), (170, 116, 52), (212, 160, 82), (244, 212, 138)],
    "gold": [(112, 76, 10), (170, 124, 22), (224, 180, 52), (250, 222, 108), (255, 248, 200)],
    "leather": [(40, 22, 12), (66, 38, 20), (96, 58, 32), (126, 80, 46), (160, 110, 70)],
    "wood": [(58, 36, 18), (88, 56, 28), (120, 80, 42), (150, 104, 58), (184, 138, 84)],
    "bone": [(110, 96, 70), (158, 142, 106), (204, 190, 152), (232, 222, 192), (250, 246, 230)],
    "red": [(70, 12, 10), (112, 20, 16), (160, 32, 24), (208, 60, 40), (240, 120, 90)],
    "purple": [(36, 10, 56), (70, 24, 104), (112, 50, 160), (160, 96, 212), (220, 170, 250)],
    "green": [(14, 44, 18), (28, 80, 32), (52, 128, 50), (96, 180, 80), (170, 230, 140)],
    "venom": [(20, 60, 10), (46, 110, 20), (90, 170, 40), (150, 220, 80), (220, 255, 170)],
    "teal": [(10, 44, 50), (20, 80, 88), (40, 130, 136), (90, 186, 184), (170, 236, 226)],
    "white": [(120, 120, 116), (170, 170, 164), (212, 212, 206), (236, 236, 230), (252, 252, 248)],
    "fur": [(92, 56, 14), (140, 92, 26), (190, 136, 46), (226, 178, 80), (250, 222, 140)],
    "mane": [(70, 34, 10), (110, 56, 18), (150, 84, 28), (190, 120, 44), (226, 170, 80)],
    "black": [(12, 12, 16), (26, 26, 32), (44, 44, 54), (66, 66, 80), (100, 100, 120)],
    "soul": [(40, 10, 70), (90, 30, 150), (150, 80, 220), (200, 150, 255), (245, 225, 255)],
    "ember": [(90, 16, 4), (160, 40, 8), (230, 100, 20), (255, 170, 50), (255, 240, 150)],
    "string": [(170, 164, 150), (200, 194, 180), (226, 220, 206), (242, 238, 226), (255, 255, 250)],
    "skin": [(30, 70, 60), (46, 104, 88), (70, 140, 118), (104, 176, 150), (150, 214, 188)],
    "eye": [(120, 90, 0), (200, 160, 0), (250, 220, 40), (255, 245, 140), (255, 255, 230)],
    "leaf": [(18, 60, 22), (30, 96, 34), (52, 140, 52), (90, 184, 76), (150, 222, 120)],
    "marble": [(170, 162, 148), (206, 198, 184), (230, 224, 212), (244, 240, 230), (254, 252, 246)],
    "silver": [(90, 98, 112), (140, 150, 166), (190, 200, 214), (224, 232, 242), (252, 254, 255)],
    "moon": [(40, 70, 130), (60, 110, 190), (100, 160, 236), (160, 206, 255), (230, 244, 255)],
}

rng = np.random.default_rng(77)


def tone(mat, t):
    p = PAL[mat]
    t = float(np.clip(t, 0, 4))
    i = int(t)
    if i >= 4:
        return np.array(p[4], dtype=float)
    f = t - i
    return np.array(p[i], dtype=float) * (1 - f) + np.array(p[i + 1], dtype=float) * f


def paint(mat, w, h, face, opt):
    """면 하나 (w x h 픽셀, v=0 이 위). 방향 음영은 게임이 넣으므로 여기선 재질 결 · 가장자리 · 무늬만"""
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    u = (xs + 0.5) / w
    v = (ys + 0.5) / h
    noise = rng.random((h, w)) - 0.5
    base = 2.2 + noise * 0.25
    along = opt.get("along", "v")          # 결 방향 (v = 세로)
    L = v if along == "v" else u
    C = u if along == "v" else v
    if mat in ("steel", "dsteel", "silver"):
        base = 2.0 + (1 - np.abs(C - 0.5) * 2) * 0.9 + noise * 0.15
        if opt.get("fuller") and face in ("north", "south"):
            fl = np.abs(C - 0.5) < max(0.5 / w * 1.2, 0.09)
            base = np.where(fl, 1.1, base)
            base = np.where(np.abs(C - 0.5 - 0.14) < 0.5 / w * 1.2, 3.4, base)
        if opt.get("edge"):
            base = np.where((C < 1.2 / w) | (C > 1 - 1.2 / w), 3.9, base)
        base += (1 - L) * 0.35 * (1 if opt.get("tiplight") else 0)
    elif mat in ("bronze", "gold"):
        base = 2.3 + noise * 0.3
        edge = (u < 1.0 / w) | (v < 1.0 / h)
        edge2 = (u > 1 - 1.0 / w) | (v > 1 - 1.0 / h)
        base = np.where(edge, 3.5, base)
        base = np.where(edge2, 1.2, base)
        if opt.get("engrave") and w >= 6 and h >= 6:
            patt = ((np.floor(xs / 2) + np.floor(ys / 2)) % 3 == 0) & ~edge & ~edge2
            base = np.where(patt, base - 0.8, base)
    elif mat == "leather":
        stripe = ((xs + ys * (1 if along == "v" else -1)) % 4) < 1.3
        base = np.where(stripe, 1.0, 2.3) + noise * 0.3
    elif mat == "wood":
        grain = np.sin(C * w * 1.7 + np.sin(L * 9 + noise) * 0.8)
        base = 2.1 + grain * 0.55 + noise * 0.2
    elif mat in ("bone",):
        band = (np.sin(L * h * 0.9) > 0.75)
        base = np.where(band, 1.6, 2.6) + (1 - L) * 0.4 + noise * 0.2
    elif mat in ("fur", "mane"):
        strand = np.sin(C * w * 2.3 + noise * 3 + L * 4)
        base = 2.1 + strand * 0.7 + (1 - L) * 0.3
    elif mat in ("green", "venom", "teal", "skin"):
        cell = 3.0
        row = np.floor(ys / cell)
        uu = (xs + (row % 2) * cell / 2) % cell / cell
        vv = ys % cell / cell
        sc = (vv > 0.7) | ((np.abs(uu - 0.5) > 0.42) & (vv > 0.35))
        base = np.where(sc, 1.2, 2.5 + (0.5 - vv) * 0.8) + noise * 0.15
    elif mat in ("ember", "soul"):
        base = 2.2 + np.sin(xs * 1.3 + ys * 0.7 + noise * 2) * 0.8
    elif mat == "eye":
        d = np.hypot(u - 0.5, v - 0.5)
        base = 4 - d * 5
    elif mat in ("red", "purple", "black", "white", "marble", "leaf", "string", "moon"):
        base = 2.2 + noise * 0.35
        if mat == "marble":
            base += np.where(np.abs(np.sin(xs * 0.6 + ys * 1.1 + noise * 3)) < 0.08, -0.9, 0)
    if opt.get("gem"):
        d = np.hypot(u - 0.35, v - 0.35)
        base = 3.9 - d * 4.5
    # 요소 모서리 어둡게 (작은 AO)
    if w >= 3 and h >= 3 and not opt.get("noao"):
        base = np.where((xs == 0) | (ys == 0), base + 0.25, base)
        base = np.where((xs == w - 1) | (ys == h - 1), base - 0.45, base)
    out = np.zeros((h, w, 4))
    for yy in range(h):
        for xx in range(w):
            out[yy, xx, :3] = tone(mat, base[yy, xx])
    out[..., 3] = 255
    return out


class M3:
    def __init__(self, name, density=6, sheet=128):
        self.name = name
        self.density = density
        self.sheet = sheet
        self.els = []

    def box(self, frm, to, mat, faces=None, rot=None, **opt):
        self.els.append({"from": list(frm), "to": list(to), "mat": mat, "faces": faces, "rot": rot, "opt": opt})
        return self

    def seg(self, p0, p1, w, z=8.0, d=1.0, mat="steel", wz=None, **opt):
        """XY 평면의 막대 p0→p1 (굵기 w, 깊이 d, z 중심). 방향은 22.5° 단위로 맞춘다.
        긴 축을 X 또는 Y 로 골라 회전을 ±45° 안에 넣는다 (마인크래프트 요소 회전 제한)."""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        th = math.degrees(math.atan2(dy, dx))
        th = round(th / 22.5) * 22.5
        cx, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        a = ((th + 90) % 180) - 90          # -90..90
        if abs(a) <= 45:                     # 긴 축 X
            frm = (cx - L / 2, cy - w / 2, z - d / 2)
            to = (cx + L / 2, cy + w / 2, z + d / 2)
            rot = a
            opt.setdefault("along", "u")
        else:                                # 긴 축 Y
            rot = a - 90 if a > 0 else a + 90
            frm = (cx - w / 2, cy - L / 2, z - d / 2)
            to = (cx + w / 2, cy + L / 2, z + d / 2)
            opt.setdefault("along", "v")
        r = {"angle": rot, "axis": "z", "origin": [round(cx, 4), round(cy, 4), z]} if abs(rot) > 1e-6 else None
        frm = tuple(round(v, 4) for v in frm)
        to = tuple(round(v, 4) for v in to)
        return self.box(frm, to, mat, rot=r, **opt)

    def mirror_z(self):
        """앞뒤 반전 (z → 16 - z). 인벤토리 카메라는 +z 쪽(south)을 본다 → 얼굴을 +z 로"""
        for e in self.els:
            f, t = e["from"], e["to"]
            f[2], t[2] = 16 - t[2], 16 - f[2]
            if e["faces"]:
                sw = {"north": "south", "south": "north"}
                e["faces"] = [sw.get(x, x) for x in e["faces"]]
            r = e["rot"]
            if r:
                r = dict(r)
                r["origin"] = [r["origin"][0], r["origin"][1], 16 - r["origin"][2]]
                if r["axis"] in ("x", "y"):
                    r["angle"] = -r["angle"]
                e["rot"] = r
        return self

    def _face_size(self, e, f):
        x0, y0, z0 = e["from"]
        x1, y1, z1 = e["to"]
        dx, dy, dz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
        if f in ("north", "south"):
            return dx, dy
        if f in ("east", "west"):
            return dz, dy
        return dx, dz

    def build(self, diag=False):
        D = self.density
        faces_all = ["north", "south", "east", "west", "up", "down"]
        req = []
        for i, e in enumerate(self.els):
            for f in (e["faces"] or faces_all):
                w, h = self._face_size(e, f)
                pw, ph = max(1, int(round(w * D))), max(1, int(round(h * D)))
                req.append((i, f, pw, ph))
        # 선반 채우기 (높이 큰 순)
        S = self.sheet
        while True:
            placed = {}
            x = y = shelf = 0
            ok = True
            for i, f, pw, ph in sorted(req, key=lambda r: -r[3]):
                if x + pw > S:
                    x, y = 0, y + shelf
                    shelf = 0
                if y + ph > S or pw > S:
                    ok = False
                    break
                placed[(i, f)] = (x, y, pw, ph)
                x += pw
                shelf = max(shelf, ph)
            if ok:
                break
            S *= 2
        atlas = np.zeros((S, S, 4))
        elements = []
        for i, e in enumerate(self.els):
            fd = {}
            for f in (e["faces"] or faces_all):
                x, y, pw, ph = placed[(i, f)]
                opt = dict(e["opt"])
                if f in ("up", "down") and "along" not in opt:
                    opt["along"] = "v"
                atlas[y:y + ph, x:x + pw] = paint(e["mat"], pw, ph, f, opt)
                k = 16.0 / S
                fd[f] = {"uv": [round(x * k, 4), round(y * k, 4), round((x + pw) * k, 4), round((y + ph) * k, 4)],
                         "texture": "#0"}
            el = {"from": e["from"], "to": e["to"], "faces": fd}
            if e["rot"]:
                el["rotation"] = e["rot"]
            elif diag:
                el["rotation"] = {"angle": -45, "axis": "z", "origin": [8, 8, 8]}
            elements.append(el)
        return elements, atlas

    def save(self, display, diag=False, extra=None):
        elements, atlas = self.build(diag)
        tex = f"oly:item/gear3d/{self.name}"
        p = os.path.join(ROOT, "textures", "item", "gear3d", self.name + ".png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8), "RGBA").save(p, optimize=True)
        mdl = {"gui_light": "front", "textures": {"0": tex, "particle": tex}, "elements": elements, "display": display}
        if extra:
            mdl.update(extra)
        mp = os.path.join(ROOT, "models", "gear", self.name + ".json")
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        with open(mp, "w", encoding="utf-8") as fh:
            json.dump(mdl, fh, ensure_ascii=False, separators=(",", ":"))
            fh.write("\n")
        return mdl


# ── 바닐라 표시 변환 (1.21.11)
HANDHELD = {
    "thirdperson_righthand": {"rotation": [0, -90, 55], "translation": [0, 4.0, 0.5], "scale": [0.85, 0.85, 0.85]},
    "thirdperson_lefthand": {"rotation": [0, 90, -55], "translation": [0, 4.0, 0.5], "scale": [0.85, 0.85, 0.85]},
    "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
    "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
}
GENERATED = {
    "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.55, 0.55, 0.55]},
    "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.55, 0.55, 0.55]},
    "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "firstperson_lefthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
    "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    "gui": {"rotation": [20, -30, 0], "scale": [0.95, 0.95, 0.95]},
}
BOW = {
    "thirdperson_righthand": {"rotation": [-80, 260, -40], "translation": [-1, -2, 2.5], "scale": [0.9, 0.9, 0.9]},
    "thirdperson_lefthand": {"rotation": [-80, -280, 40], "translation": [-1, -2, 2.5], "scale": [0.9, 0.9, 0.9]},
    "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
    "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
}
CROSSBOW = {
    "thirdperson_righthand": {"rotation": [-90, 0, -60], "translation": [2, 0.1, -3], "scale": [0.9, 0.9, 0.9]},
    "thirdperson_lefthand": {"rotation": [-90, 0, 30], "translation": [2, 0.1, -3], "scale": [0.9, 0.9, 0.9]},
    "firstperson_righthand": {"rotation": [-90, 0, -55], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "firstperson_lefthand": {"rotation": [-90, 0, 35], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
    "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
}
SPEAR_HAND = {
    "firstperson_righthand": {"rotation": [-20, 90, -35], "translation": [3.13, 2.0, 0.13], "scale": [1.36, 1.36, 0.68]},
    "firstperson_lefthand": {"rotation": [-20, -90, 35], "translation": [3.13, 2.0, 0.13], "scale": [1.36, 1.36, 0.68]},
    "thirdperson_righthand": {"rotation": [5, 270, -40], "translation": [0, 2, 2], "scale": [1.7, 1.7, 0.85]},
    "thirdperson_lefthand": {"rotation": [5, -270, 40], "translation": [0, 2, 2], "scale": [1.7, 1.7, 0.85]},
}


def vanilla_display(name):
    return json.load(open(os.path.join(VAN, name)))["display"]
