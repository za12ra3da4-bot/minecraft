"""스킬 이펙트 모델/텍스처 — assets/oly/{models,items}/fx/*.json, textures/item/fx/*.png

- 바닥 데칼(ring, crack, pool, hellgate, sigil, whirlpool): 1블록 평면, 디스플레이 transformation 으로 키운다.
- ring / pool 은 회색조 + tintindex 0 → 아이템 정의의 minecraft:custom_model_data 색으로 보스마다 물들인다.
- 입체(fireball, venom, serpent, spike, tentacle, shell, claw): 작은 큐보이드 묶음.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "resourcepack", "olympus_pack", "assets", "oly")
rng = np.random.default_rng(7)


def save_png(name, arr):
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    p = os.path.join(ROOT, "textures", "item", "fx", name + ".png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    Image.fromarray(arr, "RGBA").save(p, optimize=True)


def wjson(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def value_noise(n, cell, seed):
    r = np.random.default_rng(seed)
    g = r.random((n // cell + 2, n // cell + 2))
    ys, xs = np.mgrid[0:n, 0:n] / cell
    x0, y0 = xs.astype(int), ys.astype(int)
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def fbm(n, seed, octaves=(16, 8, 4, 2)):
    out = np.zeros((n, n))
    w = 0
    amp = 1.0
    for i, c in enumerate(octaves):
        out += value_noise(n, c, seed + i) * amp
        w += amp
        amp *= 0.55
    return out / w


def ramp(t, stops):
    """t(0..1) 배열 → RGB, stops=[(t, (r,g,b)), ...]"""
    t = np.clip(t, 0, 1)
    out = np.zeros(t.shape + (3,))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1)
        k = ((t - t0) / max(1e-6, t1 - t0))[m][:, None]
        out[m] = np.array(c0) * (1 - k) + np.array(c1) * k
    return out


def quantize(rgb, levels=6):
    return np.round(rgb / 255 * (levels - 1)) / (levels - 1) * 255


def polar(n):
    ys, xs = np.mgrid[0:n, 0:n] + 0.5
    c = n / 2
    dx, dy = xs - c, ys - c
    return np.hypot(dx, dy) / c, np.arctan2(dy, dx)


# ──────────────────────────────────────────── 텍스처
def tex_ring():
    n = 64
    r, a = polar(n)
    nz = fbm(n, 11)
    edge = 0.80 + (nz - 0.5) * 0.10
    band = (r > edge) & (r < 0.97 + (nz - 0.5) * 0.04)
    inner_glow = np.clip(1 - np.abs(r - edge) / 0.05, 0, 1)
    v = 170 + nz * 60 + inner_glow * 40
    rgb = np.stack([v, v, v], -1)
    alpha = np.where(band, 235, 0) + np.where((r > edge - 0.08) & (r <= edge), 90 * (1 - (edge - r) / 0.08), 0)
    # 안쪽 잔물결 (얇은 동심원)
    wave = (np.abs(r - 0.55 - (nz - 0.5) * 0.05) < 0.025)
    alpha = np.where(wave, 120, alpha)
    save_png("ring", np.dstack([quantize(rgb, 8), alpha]))


def tex_crack():
    n = 64
    img = np.zeros((n, n, 4))
    rnd = random.Random(3)
    core = np.zeros((n, n))
    rim = np.zeros((n, n))

    def walk(x, y, ang, length, width):
        for _ in range(length):
            ang += rnd.uniform(-0.5, 0.5)
            x += math.cos(ang)
            y += math.sin(ang)
            ix, iy = int(x), int(y)
            for dx in range(-width - 1, width + 2):
                for dy in range(-width - 1, width + 2):
                    xx, yy = ix + dx, iy + dy
                    if 0 <= xx < n and 0 <= yy < n:
                        d = math.hypot(dx, dy)
                        if d <= width:
                            core[yy, xx] = 1
                        elif d <= width + 1.5:
                            rim[yy, xx] = 1
            if rnd.random() < 0.08 and length > 8:
                walk(x, y, ang + rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.1), length // 2, max(0, width - 1))
            if not (1 < x < n - 2 and 1 < y < n - 2):
                return

    for k in range(7):
        a = k / 7 * math.tau + rnd.uniform(-0.2, 0.2)
        walk(n / 2, n / 2, a, 30, 1)
    nz = fbm(n, 5)
    glow = ramp(nz, [(0, (255, 90, 20)), (0.6, (255, 170, 40)), (1, (255, 240, 150))])
    rimc = ramp(nz, [(0, (26, 14, 10)), (1, (60, 34, 22))])
    rgb = np.where(core[..., None] > 0, glow, rimc)
    alpha = np.where(core > 0, 255, np.where(rim > 0, 230, 0))
    # 튄 돌조각
    for _ in range(40):
        x, y = rnd.randrange(n), rnd.randrange(n)
        if math.hypot(x - n / 2, y - n / 2) < n / 2 - 2 and alpha[y, x] == 0:
            rgb[y, x] = (70, 58, 48)
            alpha[y, x] = 255
    # 중심 충격 자국
    r, _ = polar(n)
    hole = r < 0.14 + (nz - 0.5) * 0.08
    rgb[hole] = (40, 22, 14)
    alpha[hole] = 255
    save_png("crack", np.dstack([quantize(rgb, 8), alpha]))


def tex_pool():
    n = 64
    r, a = polar(n)
    nz = fbm(n, 21)
    shape = r < 0.78 + (nz - 0.5) * 0.35 + 0.06 * np.sin(a * 5)
    v = 150 + nz * 70
    rim = shape & (r > 0.62 + (nz - 0.5) * 0.35 + 0.06 * np.sin(a * 5))
    v = np.where(rim, v + 50, v)
    rgb = np.stack([v, v, v], -1)
    alpha = np.where(shape, 205, 0).astype(float)
    alpha = np.where(rim, 240, alpha)
    rnd = random.Random(8)
    for _ in range(12):  # 거품
        cx, cy, rr = rnd.randrange(14, 50), rnd.randrange(14, 50), rnd.uniform(1.2, 3)
        ys, xs = np.mgrid[0:n, 0:n]
        d = np.hypot(xs - cx, ys - cy)
        m = (np.abs(d - rr) < 0.8) & shape
        rgb[m] = 255
        alpha[m] = 255
    save_png("pool", np.dstack([quantize(rgb, 8), alpha]))


GLYPHS = [  # 5x7 그리스 문자풍 룬
    ["#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#"],   # Π
    ["#####", ".#...", "..#..", "...#.", "..#..", ".#...", "#####"],   # Σ
    ["..#..", ".###.", "#.#.#", "#.#.#", ".###.", "..#..", "..#.."],   # Φ
    ["#.#.#", "#.#.#", "#.#.#", ".###.", "..#..", "..#..", "..#.."],   # Ψ
    [".###.", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "##.##"],   # Ω
    ["..#..", "..#..", ".#.#.", ".#.#.", "#...#", "#...#", "#####"],   # Δ
]


def tex_hellgate():
    n = 64
    r, a = polar(n)
    nz = fbm(n, 31)
    rgb = np.zeros((n, n, 3))
    alpha = np.zeros((n, n))
    stone = (r > 0.74) & (r < 0.98)
    rgb[stone] = ramp(nz[stone], [(0, (34, 28, 34)), (1, (78, 66, 74))])
    alpha[stone] = 255
    # 소용돌이 안쪽
    sw = (np.sin(a * 3 + r * 14 + nz * 4) + 1) / 2
    inner = r <= 0.74
    t = np.clip(sw * 0.7 + (1 - r) * 0.5, 0, 1)
    rgb[inner] = ramp(t[inner], [(0, (8, 2, 14)), (0.5, (70, 16, 110)), (0.85, (160, 70, 230)), (1, (240, 190, 255))])
    alpha[inner] = 245
    # 테두리 룬
    for k in range(12):
        g = GLYPHS[k % len(GLYPHS)]
        ang = k / 12 * math.tau
        cx, cy = n / 2 + math.cos(ang) * n * 0.43, n / 2 + math.sin(ang) * n * 0.43
        for yy, row in enumerate(g):
            for xx, ch in enumerate(row):
                if ch == "#":
                    px, py = int(cx - 2 + xx * 0.8), int(cy - 3 + yy * 0.8)
                    if 0 <= px < n and 0 <= py < n:
                        rgb[py, px] = (220, 120, 255)
    rim = (np.abs(r - 0.74) < 0.03) | (np.abs(r - 0.98) < 0.025)
    rgb[rim] = (14, 8, 18)
    save_png("hellgate", np.dstack([quantize(rgb, 10), alpha]))


def tex_sigil():
    n = 64
    r, a = polar(n)
    nz = fbm(n, 41)
    rgb = ramp(nz, [(0, (84, 84, 80)), (1, (150, 150, 142))])
    alpha = np.where(r < 0.97, 225, 0).astype(float)
    groove = np.abs(r - 0.72) < 0.06
    rgb[groove] = ramp(nz[groove], [(0, (30, 90, 80)), (1, (80, 200, 170))])
    # 뱀 머리 표시(한쪽이 굵다)
    snake = (np.abs(r - 0.72) < 0.1) & (np.abs(((a + math.pi) % math.tau) - 0.3) < 0.25)
    rgb[snake] = (60, 170, 140)
    rim = np.abs(r - 0.95) < 0.03
    rgb[rim] = (48, 48, 46)
    # 갈라짐
    rnd = random.Random(4)
    for k in range(6):
        ang = rnd.uniform(0, math.tau)
        for s in range(18):
            rr = 0.2 + s * 0.028
            x = int(n / 2 + math.cos(ang + s * 0.05) * rr * n / 2)
            y = int(n / 2 + math.sin(ang + s * 0.05) * rr * n / 2)
            rgb[y, x] = (40, 40, 38)
    inner = r < 0.2
    rgb[inner] = ramp(nz[inner], [(0, (40, 110, 96)), (1, (120, 230, 200))])
    save_png("sigil", np.dstack([quantize(rgb, 8), alpha]))


def tex_whirlpool():
    n = 64
    r, a = polar(n)
    nz = fbm(n, 51)
    arm = (np.sin(a * 3 - np.log(r + 0.05) * 6 + nz * 2.5) + 1) / 2
    t = np.clip(arm * 0.8 + (1 - r) * 0.3, 0, 1)
    rgb = ramp(t, [(0, (8, 36, 80)), (0.5, (26, 90, 160)), (0.8, (90, 180, 230)), (1, (235, 250, 255))])
    alpha = np.clip((1 - r) * 700, 0, 230)
    alpha[r > 0.98] = 0
    save_png("whirlpool", np.dstack([quantize(rgb, 8), alpha]))


def tex_claw():
    n = 32
    rgb = np.zeros((n, n, 3))
    alpha = np.zeros((n, n))
    for off in (-8, 0, 8):
        for t in np.linspace(0, 1, 120):
            x = 6 + off + t * 18
            y = 4 + t * 24 + math.sin(t * math.pi) * -3
            w = math.sin(t * math.pi) * 1.3
            for dx in np.arange(-w - 1, w + 1.01, 0.5):
                xx, yy = int(x + dx), int(y - dx * 0.4)
                if 0 <= xx < n and 0 <= yy < n:
                    core = abs(dx) <= w * 0.45
                    c = (255, 255, 240) if core else (250, 200, 80)
                    rgb[yy, xx] = c
                    alpha[yy, xx] = 255 if core else 200
    save_png("claw", np.dstack([rgb, alpha]))


def tex_solid(name, n, stops, seed, spots=None):
    nz = fbm(n, seed, octaves=(4, 2, 1))
    rgb = ramp(nz, stops)
    if spots:
        rnd = random.Random(seed)
        for _ in range(spots[0]):
            x, y = rnd.randrange(n), rnd.randrange(n)
            rgb[y, x] = spots[1]
    alpha = np.full((n, n), 255.0)
    save_png(name, np.dstack([quantize(rgb, 8), alpha]))


def tex_serpent():
    n = 32
    nz = fbm(n, 61, octaves=(4, 2, 1))
    rgb = ramp(nz, [(0, (18, 70, 36)), (0.6, (40, 130, 60)), (1, (120, 210, 110))])
    # 비늘 격자
    for y in range(0, 16):
        for x in range(0, 32):
            if (x + (y // 2) * 2) % 4 == 0 and y % 2 == 0:
                rgb[y, x] = rgb[y, x] * 0.6
    rgb[16:24, :] = ramp(nz[16:24, :], [(0, (180, 160, 70)), (1, (240, 220, 130))])   # 배
    rgb[24:28, 0:8] = (255, 220, 40)     # 눈
    rgb[25:27, 3:5] = (10, 10, 10)
    rgb[24:32, 8:32] = (150, 20, 30)     # 입 안
    alpha = np.full((n, n), 255.0)
    save_png("serpent", np.dstack([rgb, alpha]))


def tex_tentacle():
    n = 32
    nz = fbm(n, 71, octaves=(8, 4, 2))
    rgb = ramp(nz, [(0, (46, 18, 70)), (0.55, (96, 44, 130)), (1, (170, 100, 200))])
    for y in range(3, 32, 6):  # 빨판
        for x in (5, 21):
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    d = math.hypot(dx, dy)
                    if d <= 2.3:
                        rgb[(y + dy) % n, (x + dx) % n] = (230, 180, 200) if d > 1.2 else (120, 60, 90)
    rgb[:, 12:14] = rgb[:, 12:14] * 0.7
    alpha = np.full((n, n), 255.0)
    save_png("tentacle", np.dstack([quantize(rgb, 10), alpha]))


def tex_shell():
    n = 32
    nz = fbm(n, 81, octaves=(8, 4, 2))
    rgb = ramp(nz, [(0, (86, 86, 82)), (0.6, (130, 130, 124)), (1, (190, 190, 182))])
    rnd = random.Random(9)
    for _ in range(5):
        x, y = rnd.randrange(n), rnd.randrange(n)
        for _ in range(14):
            x = (x + rnd.choice((-1, 0, 1))) % n
            y = (y + 1) % n
            rgb[y, x] = (52, 52, 50)
    alpha = np.full((n, n), 235.0)
    save_png("shell", np.dstack([quantize(rgb, 8), alpha]))


# ──────────────────────────────────────────── 모델
def face(uv, tex="#0", tint=False):
    f = {"uv": uv, "texture": tex}
    if tint:
        f["tintindex"] = 0
    return f


def box(frm, to, uv=(0, 0, 16, 16), tint=False, rot=None, shade=False, faces="all"):
    fs = {}
    for k in ("north", "south", "east", "west", "up", "down"):
        if faces == "all" or k in faces:
            fs[k] = face(list(uv), tint=tint)
    e = {"from": list(frm), "to": list(to), "shade": shade, "faces": fs}
    if rot:
        e["rotation"] = rot
    return e


def mirror_z(elements):
    """모델을 앞뒤로 뒤집는다 (z → 16 - z). 게임의 item_display 는 모델을 Y 축 180° 돌려 그리므로,
    '앞(+z)'이 보스가 보는 방향이 되어야 하는 모델(뱀 머리 · 촉수 · 뿔가시)은 -z 쪽으로 만들어 둔다."""
    out = []
    swap = {"north": "south", "south": "north"}
    for e in elements:
        e = json.loads(json.dumps(e))
        f, t = e["from"], e["to"]
        f[2], t[2] = 16 - t[2], 16 - f[2]
        e["faces"] = {swap.get(k, k): v for k, v in e["faces"].items()}
        r = e.get("rotation")
        if r:
            r["origin"][2] = 16 - r["origin"][2]
            if r["axis"] in ("x", "y"):
                r["angle"] = -r["angle"]
        out.append(e)
    return out


def model(name, elements, tex):
    wjson(os.path.join(ROOT, "models", "fx", name + ".json"),
          {"textures": {"0": f"oly:item/fx/{tex}", "particle": f"oly:item/fx/{tex}"}, "elements": elements})


def item(name, tint=False):
    m = {"type": "minecraft:model", "model": f"oly:fx/{name}"}
    if tint:
        m["tints"] = [{"type": "minecraft:custom_model_data", "index": 0, "default": -1}]
    wjson(os.path.join(ROOT, "items", "fx", name + ".json"), {"model": m})


def decal(name, tint=False):
    model(name, [box((0, 7.95, 0), (16, 8.05, 16), tint=tint, faces=("up", "down"))], name)
    item(name, tint)


def build_models():
    for n, t in (("ring", True), ("pool", True), ("crack", False), ("hellgate", False),
                 ("sigil", False), ("whirlpool", False)):
        decal(n, t)
    # 발톱 자국 — 세로 평면 (디스플레이 yaw 로 방향을 맞춘다)
    model("claw", [box((0, 0, 7.95), (16, 16, 8.05), faces=("north", "south"))], "claw")
    item("claw")
    # 불덩이 / 독 덩어리 — 둥근 덩어리
    blob = [box((4, 4, 4), (12, 12, 12)), box((5, 3, 5), (11, 13, 11)),
            box((3, 5, 5), (13, 11, 11)), box((5, 5, 3), (11, 11, 13))]
    model("fireball", blob, "fireball")
    item("fireball")
    model("venom", blob + [box((10, 10, 9), (13, 13, 12)), box((3, 3, 5), (6, 6, 8))], "venom")
    item("venom")
    # 뱀 머리 화살 — 앞(+z)이 주둥이
    model("serpent", mirror_z([
        box((5, 6, 4), (11, 11, 14), uv=(0, 0, 8, 8)),        # 머리
        box((5.5, 4, 5), (10.5, 6, 14), uv=(4, 12, 16, 16)),  # 벌린 아래턱
        box((4.5, 9, 9), (5.5, 10, 10), uv=(0, 12, 2, 14)),   # 눈
        box((10.5, 9, 9), (11.5, 10, 10), uv=(0, 12, 2, 14)),
        box((6, 6.5, -6), (10, 10, 4), uv=(0, 0, 16, 4)),     # 목
        box((6.5, 7, 13.5), (9.5, 7.5, 16.5), uv=(8, 12, 12, 14)),  # 혀
    ]), "serpent")
    item("serpent")
    # 뿔가시 — 땅에서 솟는 휘어진 뿔
    model("spike", mirror_z([
        box((4, 0, 4), (12, 7, 12)),
        box((5, 6, 5), (11, 13, 11), rot={"angle": 22.5, "axis": "x", "origin": [8, 6, 8]}),
        box((6, 12, 7), (10, 19, 11), rot={"angle": 22.5, "axis": "x", "origin": [8, 12, 9]}),
        box((7, 18, 9), (9, 25, 11), rot={"angle": 45, "axis": "x", "origin": [8, 18, 10]}),
    ]), "spike")
    item("spike")
    # 촉수 — 네 마디, 위로 갈수록 가늘고 앞으로 굽는다
    model("tentacle", mirror_z([
        box((4, -8, 4), (12, 2, 12), uv=(0, 0, 8, 10)),
        box((4.5, 1, 4.5), (11.5, 10, 11.5), uv=(8, 0, 16, 10), rot={"angle": 22.5, "axis": "x", "origin": [8, 1, 8]}),
        box((5.5, 9, 7.5), (10.5, 18, 12.5), uv=(0, 8, 8, 16), rot={"angle": 22.5, "axis": "x", "origin": [8, 9, 10]}),
        box((6.5, 17, 11), (9.5, 25, 14), uv=(8, 8, 16, 16), rot={"angle": 45, "axis": "x", "origin": [8, 17, 12.5]}),
        box((7, 24, 15), (9, 29, 17), uv=(4, 4, 8, 8), rot={"angle": 45, "axis": "x", "origin": [8, 24, 16]}),
    ]), "tentacle")
    item("tentacle")
    # 석화 껍질 — 플레이어를 감싸는 네 벽 + 뚜껑 (y -2..30 = 2블록)
    model("shell", [
        box((1, -2, 1), (15, 30, 2), faces=("north", "south")),
        box((1, -2, 14), (15, 30, 15), faces=("north", "south")),
        box((1, -2, 2), (2, 30, 14), faces=("east", "west")),
        box((14, -2, 2), (15, 30, 14), faces=("east", "west")),
        box((1, 29, 1), (15, 30, 15), faces=("up", "down")),
    ], "shell")
    item("shell")


def build():
    tex_ring()
    tex_crack()
    tex_pool()
    tex_hellgate()
    tex_sigil()
    tex_whirlpool()
    tex_claw()
    tex_solid("fireball", 16, [(0, (150, 30, 8)), (0.5, (240, 110, 20)), (0.8, (255, 200, 50)), (1, (255, 250, 200))], 91)
    tex_solid("venom", 16, [(0, (20, 70, 12)), (0.6, (80, 170, 40)), (1, (200, 250, 120))], 92, spots=(8, (230, 255, 170)))
    tex_solid("spike", 16, [(0, (120, 100, 70)), (0.6, (200, 184, 146)), (1, (246, 238, 214))], 93)
    tex_serpent()
    tex_tentacle()
    tex_shell()
    build_models()


if __name__ == "__main__":
    build()
    print("fx ok")
