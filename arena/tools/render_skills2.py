"""새 특수무기 8종 + 보스 무기 4종 스킬 사용 장면 → arena/preview/skills_new12.png"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "rp"))
import render as R
import scene as SC
import weapons_legend2 as WL

OUT = os.path.join(HERE, "..", "preview")
SUN = np.array((-0.45, 0.78, -0.35)); SUN /= np.linalg.norm(SUN)
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

# ── 작은 투기장 (잔디 + 길 + 돌)
N = 40
STATES = ["air", "grass_block", "dirt", "dirt_path", "stone_bricks", "mossy_stone_bricks", "cobblestone", "oak_leaves[distance=7,persistent=true,waterlogged=false]", "oak_log[axis=y]"]


def arena():
    v = np.zeros((N, 10, N), np.uint16)
    v[:, 0:3, :] = 2
    v[:, 3, :] = 1
    rng = np.random.default_rng(3)
    for x in range(N):
        for z in range(N):
            if abs(x - N // 2) <= 2 and rng.random() < 0.85:
                v[x, 3, z] = 3
    for x in range(N):
        for z in (0, N - 1):
            v[x, 4:6, z] = 4 if rng.random() < 0.7 else 5
    for z in range(N):
        for x in (0, N - 1):
            v[x, 4:6, z] = 4 if rng.random() < 0.7 else 5
    for tx, tz in ((6, 30), (33, 8), (34, 33)):
        v[tx, 4:8, tz] = 8
        v[tx - 2:tx + 3, 7:9, tz - 2:tz + 3] = 7
        v[tx, 9, tz] = 7
    return v


VOX = arena()
PAL = R.Palette(STATES)
G = 4.0   # 땅 높이
CX, CZ = N / 2, 6.0


# ── 모양 도우미
_cache = {}


def weapon_img(wid):
    if wid not in _cache:
        _cache[wid] = WL.paint(wid, 128)
    return _cache[wid]


def glow_tex(col, soft=True, n=64):
    yy, xx = np.mgrid[0:n, 0:n]
    d = np.hypot(xx - n / 2 + 0.5, yy - n / 2 + 0.5) / (n / 2)
    a = np.clip(1 - d, 0, 1) ** (1.6 if soft else 0.6)
    core = np.clip(1 - d * 2.2, 0, 1)
    rgb = np.array(col, np.float32)[None, None] * (1 - core[..., None]) + 255 * core[..., None]
    return Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), "RGBA")


def star_tex(col, n=64):
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = n / 2
    for w, a in ((6, 90), (3, 255)):
        d.polygon([(c, 2), (c + w, c - w), (n - 2, c), (c + w, c + w), (c, n - 2), (c - w, c + w), (2, c), (c - w, c - w)], fill=tuple(col) + (a,))
    return im.filter(ImageFilter.GaussianBlur(1.2))


def bolt_tex(col, seed, n=(64, 256)):
    r = np.random.default_rng(seed)
    im = Image.new("RGBA", n, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(n[0] / 2, 0)]
    for i in range(1, 12):
        pts.append((n[0] / 2 + r.uniform(-18, 18), n[1] * i / 11))
    d.line(pts, fill=tuple(col) + (160,), width=12, joint="curve")
    im = im.filter(ImageFilter.GaussianBlur(4))
    d = ImageDraw.Draw(im)
    d.line(pts, fill=(255, 255, 255, 255), width=4, joint="curve")
    return im


class Scene:
    def __init__(self, cam, target):
        self.m = R.Mesh()
        self.cam, self.target = np.array(cam, float), np.array(target, float)
        _, f, r, u = R.look(self.cam, self.target)
        self.r, self.u = np.array(r), np.array(u)

    def tex(self, key, img):
        return self.m.texture(key, img)

    def quad(self, tid, c, ru, uu, flags=0, light=(1.15, 1.12, 1.1)):
        c = np.asarray(c, float); ru = np.asarray(ru, float); uu = np.asarray(uu, float)
        self.m.quad(c - ru - uu, c + ru - uu, c + ru + uu, c - ru + uu, (0, 0, 1, 1), tid, flags, light)

    def bill(self, key, img, c, s, add=True):
        tid = self.tex(key, img)
        self.quad(tid, c, self.r * s, self.u * s, flags=(6 if add else 2), light=(1, 1, 1))

    def weapon(self, wid, c, tip, normal, size, ghost=False):
        """무기 그림 판: 날끝 방향 tip, 판 법선 normal"""
        t = np.asarray(tip, float); t /= np.linalg.norm(t)
        n = np.asarray(normal, float); n /= np.linalg.norm(n)
        s = np.cross(n, t); s /= np.linalg.norm(s)
        h = size / 2
        ru = (t + s) / math.sqrt(2) * h
        uu = (t - s) / math.sqrt(2) * h
        img = weapon_img(wid)
        if ghost:
            a = np.asarray(img).astype(np.float32).copy(); a[..., 3] *= 0.45
            tid = self.tex(f"w_{wid}_g", Image.fromarray(a.astype(np.uint8)))
            self.quad(tid, c, ru, uu, flags=6, light=(1, 1, 1))
        else:
            tid = self.tex(f"w_{wid}", img)
            self.quad(tid, c, ru, uu, flags=0, light=(1.25, 1.2, 1.18))
            self.quad(tid, c, -ru, uu, flags=0, light=(1.0, 0.98, 0.96))   # 뒷면 (거울)

    def block(self, col, c, size, yaw=0.0, tilt=0.0, key=None):
        tid = SC._solid(self.m, key or f"b{col}", col)
        a, b = math.radians(yaw), math.radians(tilt)
        Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
        M = np.eye(4); M[:3, :3] = Ry @ Rx; M[:3, 3] = c
        sx, sy, sz = size
        SC.box(self.m, tid, (-sx / 2, 0, -sz / 2), (sx / 2, sy, sz / 2), M, SUN)

    def player(self, x, z, yaw, team, y=G, pose=0.0):
        SC.player(self.m, x, y, z, yaw, team, SUN, pose)

    def ring(self, key, col, c, r, n=40, s=0.25, y_wave=0.0, arc=(0, 360)):
        img = glow_tex(col)
        for i in range(n):
            a = math.radians(arc[0] + (arc[1] - arc[0]) * i / n)
            self.bill(key, img, (c[0] + math.cos(a) * r, c[1] + math.sin(i * 0.7) * y_wave, c[2] + math.sin(a) * r), s)

    def line(self, key, col, a, b, n=20, s=0.2):
        img = glow_tex(col)
        a = np.asarray(a, float); b = np.asarray(b, float)
        for i in range(n + 1):
            self.bill(key, img, a + (b - a) * i / n, s)

    def cloud(self, key, col, c, spread, n, s=(0.2, 0.5), seed=1, star=False):
        r = np.random.default_rng(seed)
        img = star_tex(col) if star else glow_tex(col)
        for _ in range(n):
            p = np.asarray(c, float) + r.normal(0, 1, 3) * np.asarray(spread, float)
            self.bill(key, img, p, r.uniform(*s))

    def render(self, W=560, H=360):
        return R.render(VOX, PAL, W, H, tuple(self.cam), tuple(self.target), fov=52, mesh=self.m, ss=2, fog_dist=300)


def cam_default(tx=CX, tz=12.0):
    return (tx + 8.5, G + 6.5, tz - 9.0), (tx, G + 1.2, tz)


# ── 장면들 (시전자 = 레드, 앞쪽 = +z)
def s_frost():
    sc = Scene(*cam_default())
    sc.player(CX, CZ, 0, "red")
    sc.weapon("frost", (CX + 0.35, G + 1.25, CZ + 0.5), (0, 1, 0.15), (1, 0, 0), 1.6)
    for k, dx in enumerate((-1.6, 0, 1.6)):
        a = np.array((CX, G + 1.4, CZ + 1)); b = np.array((CX + dx, G + 1.2, CZ + 13))
        sc.line("fa", (120, 200, 255), a + (b - a) * 0.35, b, 16, 0.14)
        sc.bill("fs", star_tex((200, 240, 255)), a + (b - a) * 0.7, 0.3)
    for ex, ez in ((CX - 1.6, CZ + 13), (CX + 1.6, CZ + 13)):
        sc.player(ex, ez, 180, "blue")
        for i in range(6):
            a = math.radians(i * 60 + 15)
            sc.block((150, 205, 250), (ex + math.cos(a) * 0.7, G - 0.2, ez + math.sin(a) * 0.7), (0.35, 1.6 + (i % 3) * 0.3, 0.35), i * 60, 20 * (1 if i % 2 else -1), key="ice")
        sc.block((110, 170, 240), (ex, G - 0.2, ez + 0.9), (0.5, 2.2, 0.5), 20, 10, key="ice2")
        sc.cloud("sn", (220, 245, 255), (ex, G + 1.2, ez), (0.9, 0.7, 0.9), 20, (0.08, 0.18), seed=int(ex), star=True)
    return sc


def s_storm():
    sc = Scene(*cam_default())
    sc.player(CX, CZ, 0, "red", pose=1)
    sc.weapon("storm", (CX, G + 2.3, CZ + 6), (0, -0.25, 1), (1, 0, 0), 2.6)
    sc.line("st", (120, 180, 255), (CX, G + 1.6, CZ + 1), (CX, G + 2.3, CZ + 5), 12, 0.12)
    hit = np.array((CX, G, CZ + 12))
    sc.player(hit[0], hit[2], 180, "blue")
    sc.bill("bolt", bolt_tex((140, 190, 255), 1), hit + (0, 5.5, 0), 5.5)
    sc.cloud("sp", (170, 210, 255), hit + (0, 1, 0), (1.2, 0.8, 1.2), 30, (0.1, 0.3), seed=4)
    prev = hit + (0, 1, 0)
    for k, (ex, ez) in enumerate(((CX + 4, CZ + 15), (CX - 3.5, CZ + 17))):
        sc.player(ex, ez, 200, "blue")
        to = np.array((ex, G + 1, ez))
        sc.line(f"ch{k}", (255, 240, 140), prev, to, 18, 0.13)
        sc.cloud("sp2", (255, 250, 180), to, (0.3, 0.5, 0.3), 10, (0.1, 0.2), seed=10 + k)
        prev = to
    return sc


def s_scythe():
    sc = Scene((CX + 6, G + 5.5, CZ - 5), (CX, G + 1, CZ + 1))
    sc.player(CX, CZ, 30, "red", pose=1)
    for k in range(3):
        a = math.radians(40 + k * 45)
        c = (CX + math.cos(a) * 1.6, G + 1.0, CZ + math.sin(a) * 1.6)
        sc.weapon("scythe", c, (math.cos(a + 1.3), 0, math.sin(a + 1.3)), (0, 1, 0), 3.2, ghost=(k < 2))
    sc.ring("soul", (70, 230, 190), (CX, G + 1.0, CZ), 2.6, 36, 0.22, 0.1, (0, 300))
    for ex, ez in ((CX + 2.2, CZ + 2.2), (CX - 2.4, CZ + 1.5)):
        sc.player(ex, ez, 200, "blue")
        sc.line("dr", (90, 255, 200), (ex, G + 1, ez), (CX, G + 1.1, CZ), 10, 0.1)
    sc.cloud("hr", (255, 80, 90), (CX, G + 2.3, CZ), (0.4, 0.2, 0.4), 4, (0.12, 0.18), seed=3, star=True)
    return sc


def s_lance():
    sc = Scene(*cam_default())
    px = np.array((CX, G, CZ + 6))
    sc.player(px[0], px[2], 0, "red", pose=1)
    sc.weapon("lance", px + (0.35, 1.1, 1.6), (0, 0.05, 1), (1, 0, 0), 3.2)
    for k in range(4):
        sc.player(CX, CZ + 1.2 * k, 0, "red") if k == -1 else None
    sc.line("tr", (255, 240, 170), (CX, G + 1, CZ), px + (0, 1, 0), 22, 0.22)
    sc.cloud("tw", (255, 230, 120), (CX, G + 1, CZ + 3), (0.3, 0.3, 2.2), 30, (0.08, 0.2), seed=5, star=True)
    sc.player(CX + 0.4, CZ + 9.5, 180, "blue", y=G + 2.2)
    sc.cloud("gl", (255, 250, 200), (CX + 0.4, G + 3.2, CZ + 9.5), (0.35, 0.8, 0.35), 18, (0.12, 0.25), seed=6)
    return sc


def s_skull():
    sc = Scene(*cam_default())
    sc.player(CX, CZ, 0, "red", pose=1)
    sc.weapon("skull", (CX + 0.35, G + 1.3, CZ + 0.6), (0, 1, 0.2), (1, 0, 0), 1.8)
    hit = np.array((CX, G + 0.2, CZ + 11))
    sc.block((225, 215, 190), (CX, G + 1.4, CZ + 6), (0.55, 0.55, 0.55), 10, key="skull")
    sc.block((40, 30, 30), (CX - 0.12, G + 1.62, CZ + 6.27), (0.12, 0.12, 0.05), key="eye")
    sc.block((40, 30, 30), (CX + 0.12, G + 1.62, CZ + 6.27), (0.12, 0.12, 0.05), key="eye")
    sc.line("sk", (120, 255, 90), (CX, G + 1.6, CZ + 1.5), (CX, G + 1.6, CZ + 5.6), 12, 0.13)
    sc.cloud("pc", (90, 220, 60), hit + (0, 0.6, 0), (2.2, 0.5, 2.2), 70, (0.25, 0.6), seed=7)
    sc.cloud("pw", (150, 70, 190), hit + (0, 0.8, 0), (1.8, 0.5, 1.8), 18, (0.2, 0.4), seed=8)
    for ex, ez in ((CX - 1, CZ + 11), (CX + 1.5, CZ + 12)):
        sc.player(ex, ez, 180, "blue")
    return sc


def s_chakram():
    sc = Scene(*cam_default())
    sc.player(CX, CZ, 0, "red", pose=1)
    c = np.array((CX + 0.5, G + 1.3, CZ + 7))
    sc.weapon("chakram", c, (0, 0, 1), (0, 1, 0), 2.0)
    sc.ring("fr", (255, 160, 40), c, 1.1, 24, 0.18)
    for i in range(12):
        t = i / 12
        sc.bill("tr2", glow_tex((255, 190, 70)), (CX + 0.5 + math.sin(t * math.pi) * 1.4, G + 1.3, CZ + 1 + t * 5.8), 0.22)
    sc.player(CX + 0.7, CZ + 8, 180, "blue")
    sc.cloud("sp3", (255, 220, 120), c, (0.8, 0.4, 0.8), 14, (0.1, 0.2), seed=9, star=True)
    return sc


def s_chain():
    sc = Scene(*cam_default())
    sc.player(CX, CZ, 0, "red", pose=1)
    sc.weapon("chain", (CX + 0.3, G + 1.3, CZ + 0.6), (0, 0.8, 0.6), (1, 0, 0), 1.8)
    tg = np.array((CX + 1, G, CZ + 6))
    sc.player(tg[0], tg[2], 180, "blue", y=G + 0.5)
    sc.line("cn", (160, 160, 170), (CX + 0.3, G + 1.4, CZ + 1), tg + (0, 1.5, 0), 30, 0.1)
    sc.line("cr", (255, 90, 80), (CX + 0.3, G + 1.4, CZ + 1), tg + (0, 1.5, 0), 8, 0.2)
    for k in range(3):
        sc.player(tg[0], tg[2] + 1.2 + k * 1.1, 180, "blue") if False else None
    sc.cloud("ar", (255, 255, 255), tg + (0, 1.2, 1.6), (0.2, 0.2, 1.0), 14, (0.05, 0.12), seed=11)
    sc.cloud("st", (255, 240, 120), tg + (0, 2.3, 0), (0.3, 0.1, 0.3), 5, (0.12, 0.2), seed=12, star=True)
    return sc


def s_gauntlet():
    sc = Scene(*cam_default())
    sc.player(CX, CZ, 0, "red", pose=1)
    sc.weapon("gauntlet", (CX + 0.4, G + 1.1, CZ + 0.5), (0, 0.3, 1), (1, 0, 0), 1.3)
    cols = [(120, 118, 114), (140, 138, 132), (104, 100, 96)]
    for k in range(9):
        z = CZ + 1.5 + k * 1.3
        h = 0.6 + min(k, 5) * 0.35
        sc.block(cols[k % 3], (CX, G, z), (1.1, h, 1.1), k * 17, 0, key=f"st{k % 3}")
        sc.cloud(f"du{k}", (180, 160, 130), (CX, G + 0.3, z), (0.5, 0.2, 0.5), 6, (0.15, 0.3), seed=20 + k)
    sc.player(CX + 0.1, CZ + 9.3, 180, "blue", y=G + 3.0)
    sc.cloud("em", (255, 140, 40), (CX, G + 1, CZ + 6), (0.8, 1.0, 4), 20, (0.06, 0.12), seed=13)
    return sc


def s_talos():
    sc = Scene(*cam_default())
    for k in range(3):
        z = CZ + k * 2.6
        last = k == 2
        sc.player(CX, z, 0, "red", pose=1) if last else sc.cloud(f"af{k}", (230, 150, 70), (CX, G + 1, z), (0.25, 0.5, 0.25), 20, (0.15, 0.3), seed=30 + k)
        sc.weapon("b_talos", (CX + 0.4, G + 1.2, z + 1.2), (0.15, 0.25, 1), (1, 0, 0), 2.6, ghost=not last)
    sc.cloud("cp", (230, 140, 60), (CX, G + 0.3, CZ + 3), (0.6, 0.2, 3), 40, (0.08, 0.18), seed=33)
    sc.player(CX + 0.8, CZ + 7.5, 180, "blue")
    sc.cloud("hit", (255, 200, 120), (CX + 0.8, G + 1.2, CZ + 7.3), (0.4, 0.5, 0.3), 16, (0.12, 0.26), seed=34, star=True)
    sc.ring("aura", (255, 170, 60), (CX, G + 0.1, CZ + 5.2), 1.1, 20, 0.2)
    return sc


def s_sphinx():
    sc = Scene((CX + 7, G + 6, CZ - 4), (CX, G + 1.8, CZ + 2))
    c = np.array((CX, G, CZ + 2))
    sc.player(c[0], c[2], 20, "red")
    sc.weapon("b_sphinx", c + (0, 4.0, 0), (1, 1, 0), (0.3, 0, -1), 2.2)
    r = np.random.default_rng(5)
    for i in range(16):
        a = math.radians(i * 22.5)
        rr = 3 + (i % 5) * 0.9
        col = (236, 200, 120) if i % 3 else ((214, 180, 110) if i % 4 else (240, 190, 60))
        sc.block(col, (c[0] + math.cos(a) * rr, G + 0.3 + (i % 4) * 0.7, c[2] + math.sin(a) * rr), (0.4, 0.4, 0.4), i * 22, 30, key=f"sd{i % 3}")
    sc.cloud("sand", (240, 200, 120), c + (0, 1.2, 0), (4, 1.2, 4), 90, (0.15, 0.35), seed=40)
    for ex, ez in ((CX + 3.5, CZ + 5), (CX - 4, CZ + 4)):
        sc.player(ex, ez, 220, "blue")
    return sc


def s_ladon():
    sc = Scene(*cam_default())
    sc.player(CX, CZ, 0, "red", pose=1)
    for k, a in enumerate((-32, 0, 32)):
        d = np.array((math.sin(math.radians(a)), 0, math.cos(math.radians(a))))
        base = np.array((CX, G + 1.2, CZ))
        sc.weapon("b_ladon", base + d * 3.5, d, (0, 1, 0.3), 3.4)
        sc.line(f"wl{k}", (90, 220, 60), base + d * 1, base + d * 6.5, 14, 0.14)
    for ex, ez in ((CX - 2.8, CZ + 6), (CX + 0.3, CZ + 7), (CX + 3.2, CZ + 5.5)):
        sc.player(ex, ez, 180, "blue")
        sc.cloud(f"po{ex}", (110, 230, 70), (ex, G + 1.2, ez), (0.4, 0.6, 0.4), 12, (0.1, 0.22), seed=int(ex * 7))
    return sc


def s_cyclops():
    sc = Scene((CX + 11, G + 6.5, CZ - 2), (CX, G + 3, CZ + 8))
    sc.player(CX, CZ, 0, "red", pose=1)
    sc.weapon("b_cyclops", (CX + 0.4, G + 1.8, CZ + 0.4), (0, 1, 0.3), (1, 0, 0), 2.0)
    fr = np.array((CX, G + 2.5, CZ)); to = np.array((CX, G + 0.8, CZ + 14))
    for i in range(1, 12):
        f = i / 12
        p = fr + (to - fr) * f + np.array((0, 4 * 4 * f * (1 - f), 0))
        sc.bill("smk", glow_tex((230, 150, 80)), p, 0.35)
    p = fr + (to - fr) * 0.75 + np.array((0, 4 * 4 * 0.75 * 0.25, 0))
    for k, col in enumerate(((120, 118, 114), (104, 120, 90), (140, 136, 130), (110, 106, 100), (130, 126, 120))):
        sc.block(col, p + ((k % 2) * 0.5 - 0.3, (k % 3) * 0.3 - 0.4, (k % 2) * 0.4 - 0.2), (1.2, 1.1, 1.2), k * 70, 25, key=f"bo{k}")
    hit = np.array((CX, G, CZ + 15))
    sc.ring("sh", (255, 190, 110), hit + (0, 0.1, 0), 3, 40, 0.3)
    sc.cloud("deb", (150, 140, 128), hit + (0, 0.6, 0), (2.2, 0.6, 2.2), 50, (0.12, 0.3), seed=50)
    for ex, ez in ((CX - 1.8, CZ + 15), (CX + 1.8, CZ + 16)):
        sc.player(ex, ez, 180, "blue", y=G + 1.8)
    return sc


SCENES = [
    ("frost", "서리 여왕의 장궁", "빙결 사격 — 얼음 화살 3발, 맞은 자리 얼음 가시", s_frost),
    ("storm", "폭풍의 삼지창", "폭풍 투척 — 낙뢰 후 번개가 3명에게 튐", s_storm),
    ("scythe", "망자의 낫", "영혼 수확 — 한 바퀴 베고 맞은 만큼 회복", s_scythe),
    ("lance", "성광의 기병창", "성광 돌격 — 길 위의 적을 띄우고 발광", s_lance),
    ("skull", "저주받은 해골 지팡이", "저주의 해골 — 폭발 + 4초 독 구름", s_skull),
    ("chakram", "태양의 원반", "태양 원반 — 날아갔다 돌아오며 두 번 벰", s_chakram),
    ("chain", "사냥꾼의 사슬낫", "사슬 끌어오기 — 앞의 적을 끌어와 기절", s_chain),
    ("gauntlet", "거인의 건틀렛", "대지 분쇄 — 돌기둥이 줄지어 솟음", s_gauntlet),
    ("b_talos", "탈로스의 청동 대검 (보스)", "청동 폭주 — 3연속 돌진 + 저항 · 힘", s_talos),
    ("b_sphinx", "스핑크스의 모래시계 (보스)", "모래폭풍 — 반경 7 구속 V · 실명", s_sphinx),
    ("b_ladon", "히드라의 삼두 채찍 (보스)", "삼두 채찍질 — 세 갈래 독 · 시듦", s_ladon),
    ("b_cyclops", "외눈 거인의 곤봉 (보스)", "거암 투척 — 바위가 떨어져 땅을 뒤흔듦", s_cyclops),
]


def main():
    W, H = 560, 360
    cols = 3
    rows = (len(SCENES) + cols - 1) // cols
    pad, lab = 14, 64
    sheet = Image.new("RGB", (cols * (W + pad) + pad, rows * (H + lab + pad) + pad + 70), (24, 22, 28))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 18), "왕관 쟁탈전 — 새 특수무기 · 보스 전용 무기 스킬", fill=(255, 220, 140), font=ImageFont.truetype(FONT, 34))
    for i, (wid, name, desc, fn) in enumerate(SCENES):
        im = fn().render(W, H)
        x = pad + (i % cols) * (W + pad)
        y = 70 + pad + (i // cols) * (H + lab + pad)
        sheet.paste(im, (x, y))
        ic = weapon_img(wid).resize((56, 56), Image.NEAREST)
        sheet.paste(ic, (x + 2, y + H + 4), ic)
        boss = wid.startswith("b_")
        d.text((x + 64, y + H + 6), name, fill=(255, 120, 110) if boss else (255, 214, 120), font=ImageFont.truetype(FONT, 22))
        d.text((x + 64, y + H + 34), desc, fill=(225, 225, 230), font=ImageFont.truetype(FONT, 17))
        print(wid, flush=True)
    sheet.save(os.path.join(OUT, "skills_new12.png"))


if __name__ == "__main__":
    main()
