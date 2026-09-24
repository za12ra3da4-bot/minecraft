"""보스 파츠에 입체 디테일을 덧붙인다 (발톱 · 송곳니 · 가시 · 목걸이 · 코뚜레 · 갑옷 · 금관 · 따개비)

- 원래 요소는 그대로, 새 요소만 뒤에 붙인다 → 리그 · 애니메이션 · UUID 영향 없음
- 새 요소의 면은 아틀라스(1024)의 빈 아래쪽에 배정해 재질별로 칠한다
- 원본 모델은 tools/boss_fx/boss_src/models/<보스>/ 에 한 번 보관하고 매번 원본에서 시작한다
파츠 모델 공간: +z = 앞, +y = 위 (item_display 의 180° 회전과 리그의 뒤집기가 상쇄된다)
"""
import copy
import glob
import json
import os
import shutil

import numpy as np
from PIL import Image

from boss_hd import BOSSES, SRC
from model3d import paint

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..", "..", "resourcepack", "olympus_pack", "assets", "oly")
N = 1024
D = 10          # 새 요소 텍스처 밀도 (픽셀 / 모델 단위)
Y0 = 330        # 아틀라스에서 새 요소를 쓰기 시작할 줄 (원본은 위쪽 ~260 까지)


def src_models(boss):
    d = os.path.join(SRC, "models", boss)
    if not os.path.isdir(d):
        os.makedirs(d)
        for f in glob.glob(os.path.join(PACK, "models", "boss", boss, "*.json")):
            shutil.copy(f, d)
    return d


def bbox(els):
    lo = [min(e["from"][i] for e in els) for i in range(3)]
    hi = [max(e["to"][i] for e in els) for i in range(3)]
    return lo, hi


def B(frm, to, mat, rot=None, **opt):
    return {"from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to], "mat": mat, "rot": rot, "opt": opt}


def claws(lo, hi, mat="bone"):
    y0, z1 = lo[1], hi[2]
    out = []
    for x in np.linspace(lo[0] + 1.0, hi[0] - 1.9, 4):
        out.append(B((x, y0 - 0.2, z1 - 0.4), (x + 0.9, y0 + 1.1, z1 + 1.7), mat,
                     {"angle": 22.5, "axis": "x", "origin": [x + 0.45, y0 + 0.5, z1]}, tiplight=True))
    return out


def fangs(lo, hi, up=True, big=1.0, mat="bone"):
    """턱 앞 모서리의 송곳니 두 개 + 앞니 둘. up=True 면 아래턱에서 위로"""
    y = hi[1] if up else lo[1]
    z1 = hi[2]
    L = 1.6 * big
    out = []
    for x in (lo[0] + 0.6, hi[0] - 1.4):
        y0, y1 = (y, y + L) if up else (y - L, y)
        out.append(B((x, y0, z1 - 1.3), (x + 0.8, y1, z1 - 0.5), mat, tiplight=True))
    for x in (lo[0] + (hi[0] - lo[0]) * 0.36, lo[0] + (hi[0] - lo[0]) * 0.58):
        y0, y1 = (y, y + L * 0.45) if up else (y - L * 0.45, y)
        out.append(B((x, y0, z1 - 0.9), (x + 0.55, y1, z1 - 0.35), mat))
    return out


def spikes_row(xc, ytop, zs, h=2.6, w=1.4, mat="bone", back=True):
    out = []
    for z in zs:
        out.append(B((xc - w / 2, ytop - 0.4, z - w / 2), (xc + w / 2, ytop + h, z + w / 2), mat,
                     {"angle": -22.5 if back else 22.5, "axis": "x", "origin": [xc, ytop, z]}, tiplight=True))
    return out


def collar(lo, hi, zc, mat="black", spike="steel"):
    x0, x1 = lo[0] - 0.6, hi[0] + 0.6
    y0, y1 = lo[1] - 0.6, hi[1] + 0.6
    z0, z1 = zc - 1.2, zc + 1.2
    out = [B((x0, y1 - 1.0, z0), (x1, y1, z1), mat), B((x0, y0, z0), (x1, y0 + 1.0, z1), mat),
           B((x0, y0, z0), (x0 + 1.0, y1, z1), mat), B((x1 - 1.0, y0, z0), (x1, y1, z1), mat)]
    cx = (x0 + x1) / 2
    for x in (cx - 4, cx, cx + 4):
        out.append(B((x - 0.5, y1, zc - 0.5), (x + 0.5, y1 + 1.8, zc + 0.5), spike, tiplight=True))
    for y in ((y0 + y1) / 2 - 3, (y0 + y1) / 2 + 3):
        out.append(B((x1, y - 0.5, zc - 0.5), (x1 + 1.8, y + 0.5, zc + 0.5), spike, tiplight=True))
        out.append(B((x0 - 1.8, y - 0.5, zc - 0.5), (x0, y + 0.5, zc + 0.5), spike, tiplight=True))
    out.append(B((cx - 1.0, y0 - 1.6, zc - 0.4), (cx + 1.0, y0, zc + 0.9), "gold"))      # 고리
    return out


def details(boss, part, els):
    lo, hi = bbox(els)
    quad = boss in ("nemean_lion", "chimera", "cerberus", "hydra")
    add = []
    if quad and part.endswith("_lo") and part.startswith("leg"):
        add += claws(lo, hi, "bone" if boss != "cerberus" else "dsteel")
    if boss in ("nemean_lion", "chimera") and part == "jaw":
        add += fangs(lo, hi, up=True, big=1.1)
    if boss == "cerberus" and part.endswith("_h_j"):
        add += fangs(lo, hi, up=True, big=1.0)
    if boss == "cerberus" and part in ("hl", "hm", "hr"):
        add += collar(lo, hi, lo[2] + 2.5)
    if boss == "hydra" and part.endswith("_j"):
        add += fangs(lo, hi, up=True, big=0.9)
    if boss == "hydra" and part.endswith("_0") and part.startswith("n"):
        add += spikes_row(8, hi[1], (lo[2] + 3, lo[2] + 8), h=1.8, w=1.0)
    if boss == "hydra" and part == "body":
        add += spikes_row(8, hi[1], [lo[2] + 4 + k * 5.4 for k in range(8)], h=3.0, w=1.6)
    if boss == "hydra" and part.startswith("tail"):
        add += spikes_row(8, hi[1], (lo[2] + 2.5, lo[2] + 6.5), h=1.6, w=1.0)
    if boss == "scylla" and part.endswith("_h_j"):
        add += fangs(lo, hi, up=True, big=0.7)
    if boss == "scylla" and part == "base":
        rs = np.random.default_rng(4)
        for k in range(14):
            side = k % 4
            s = rs.uniform(0.9, 1.8)
            yy = rs.uniform(lo[1] + 2, hi[1] - 4)
            t = rs.uniform(lo[0] + 2, hi[0] - 4)
            if side == 0:
                f, to = (t, yy, hi[2] - 0.3), (t + s, yy + s, hi[2] + s * 0.7)
            elif side == 1:
                f, to = (t, yy, lo[2] - s * 0.7), (t + s, yy + s, lo[2] + 0.3)
            elif side == 2:
                f, to = (hi[0] - 0.3, yy, t), (hi[0] + s * 0.7, yy + s, t + s)
            else:
                f, to = (lo[0] - s * 0.7, yy, t), (lo[0] + 0.3, yy + s, t + s)
            add.append(B(f, to, "bone"))
    if boss == "chimera" and part == "snake_h":
        add += fangs(lo, hi, up=False, big=1.2)
    if boss == "minotaur" and part == "head":
        # 코뚜레 (주둥이 앞 아래에 매달린 금 고리)
        zf = hi[2]
        add += [B((6.3, 8.0, zf - 0.3), (7.0, 10.6, zf + 0.5), "gold"), B((9.0, 8.0, zf - 0.3), (9.7, 10.6, zf + 0.5), "gold"),
                B((6.3, 7.3, zf - 0.3), (9.7, 8.0, zf + 0.5), "gold")]
    if boss == "minotaur" and part in ("arml", "armr"):
        add += [B((lo[0] - 0.9, hi[1] - 2.2, lo[2] - 0.9), (hi[0] + 0.9, hi[1] + 1.0, hi[2] + 0.9), "bronze", engrave=True),
                B((lo[0] - 0.5, hi[1] - 4.4, lo[2] - 0.5), (hi[0] + 0.5, hi[1] - 2.2, hi[2] + 0.5), "bronze"),
                B((7.3, hi[1] + 1.0, 7.3), (8.7, hi[1] + 2.6, 8.7), "steel", tiplight=True)]
    if boss == "medusa" and part == "head":
        add += [B((lo[0] - 0.4, hi[1] - 2.6, lo[2] - 0.4), (hi[0] + 0.4, hi[1] - 1.5, hi[2] + 0.4), "gold", engrave=True),
                B((7.3, hi[1] - 3.0, hi[2] + 0.3), (8.7, hi[1] - 1.2, hi[2] + 0.8), "red", gem=True)]
    if boss == "medusa" and part in ("arml_lo", "armr_lo"):
        add += [B((lo[0] - 0.4, hi[1] - 3.0, lo[2] - 0.4), (hi[0] + 0.4, hi[1] - 1.8, hi[2] + 0.4), "gold", engrave=True)]
    return add


def fix_medusa_bow(els):
    """활을 손 기준으로 45° 세운다 (애니메이션 자세에서 활이 허리춤에 가로로 눕던 것)"""
    lo, hi = bbox(els)
    zc = (lo[2] + hi[2]) / 2
    out = []
    for e in els:
        e = copy.deepcopy(e)
        if "rotation" not in e:
            e["rotation"] = {"angle": 45, "axis": "x", "origin": [8, 8, zc]}
        out.append(e)
    return out


def pack_faces(req, y0=Y0):
    placed = {}
    x = 0
    y = y0
    shelf = 0
    for key, pw, ph in sorted(req, key=lambda r: -r[2]):
        if x + pw > N:
            x, y, shelf = 0, y + shelf, 0
        if y + ph > N:
            raise RuntimeError("아틀라스 공간 부족")
        placed[key] = (x, y, pw, ph)
        x += pw
        shelf = max(shelf, ph)
    return placed


def apply(boss):
    d = src_models(boss)
    tex_path = os.path.join(PACK, "textures", "item", "boss", boss + ".png")
    atlas = np.asarray(Image.open(tex_path).convert("RGBA"), dtype=float).copy()
    assert atlas.shape[0] == N, "먼저 boss_paint.py 로 1024 아틀라스를 만들 것"
    atlas[Y0:, :] = 0
    todo = {}
    req = []
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        part = os.path.basename(f)[:-5]
        mdl = json.load(open(f))
        els = mdl["elements"]
        if boss == "medusa" and part == "bow":
            els = fix_medusa_bow(els)
        add = details(boss, part, els)
        todo[part] = (mdl, els, add)
        for i, e in enumerate(add):
            dx, dy, dz = [abs(e["to"][k] - e["from"][k]) for k in range(3)]
            for face, (w, h) in (("north", (dx, dy)), ("south", (dx, dy)), ("east", (dz, dy)), ("west", (dz, dy)),
                                 ("up", (dx, dz)), ("down", (dx, dz))):
                req.append(((part, i, face), max(2, int(round(w * D))), max(2, int(round(h * D)))))
    placed = pack_faces(req)
    total = 0
    for part, (mdl, els, add) in todo.items():
        new = list(els)
        for i, e in enumerate(add):
            faces = {}
            for face in ("north", "south", "east", "west", "up", "down"):
                x, y, pw, ph = placed[(part, i, face)]
                atlas[y:y + ph, x:x + pw] = paint(e["mat"], pw, ph, face, dict(e["opt"]))
                k = 16.0 / N
                faces[face] = {"uv": [round(x * k, 5), round(y * k, 5), round((x + pw) * k, 5), round((y + ph) * k, 5)], "texture": "#0"}
            el = {"from": e["from"], "to": e["to"], "faces": faces}
            if e["rot"]:
                el["rotation"] = e["rot"]
            new.append(el)
            total += 1
        mdl = dict(mdl, elements=new)
        with open(os.path.join(PACK, "models", "boss", boss, part + ".json"), "w", encoding="utf-8") as fh:
            json.dump(mdl, fh, separators=(",", ":"))
    Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8), "RGBA").save(tex_path, optimize=True)
    return total


if __name__ == "__main__":
    import sys
    for b in (sys.argv[1:] or BOSSES):
        print(b, "+", apply(b), "요소")
