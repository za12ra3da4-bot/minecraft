"""상점 무기 설명창(툴팁) 속 스킬 미리보기 영상

 무기 아이템에 tooltip_style "bg:w_<무기>" 를 주면 마우스를 올렸을 때 설명창 배경이
   assets/bg/textures/gui/sprites/tooltip/w_<무기>_background.png  (움직이는 그림 · FRAMES 장 · 2틱마다)
 로 바뀐다. 배경은 설명창 크기에 맞게 늘어나므로(stretch) 설명창 크기를 고정한다 (a50 bgWShopItem):
   글자 영역 폭 230 · 줄 수 18 (이름 1 + 설명 6 + 영상 11) → 설명창 254 x 206 (글자 영역 + 테두리 12씩)
   위 84px = 글자가 올라가는 판, 아래 = 영상
 영상: 3D 렌더 (arena/tools/render.py) — 마크 기본 스킨 플레이어가 무기를 들어 휘두르면
   실제 게임의 바닥 효과(tele/wfx_* · fx2_*) → 타격 연출(impactfx) → 맞은 적이 붉게 밀려나며 숫자
 주의: 세로로 이어 붙인 애니메이션은 mcmeta 에 한 장 크기(width · height)를 꼭 적는다
       (안 적으면 마크가 정사각형으로 자르려다 실패해서 검정·보라 깨진 그림이 나옴)
"""
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path[:0] = [HERE, TOOLS]

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import impactfx

TW, TH = 254, 206            # 설명창 전체 (픽셀 = 화면 GUI 1칸)
VX0, VY0, VX1, VY1 = 12, 86, 242, 196      # 영상 칸
VW, VH = VX1 - VX0, VY1 - VY0
FRAMES = 20
FT = 2                       # 한 장 2틱 → 2초
HIT = 0.36                   # 터지는 순간 (영상 비율)
SKINS = os.path.join(TOOLS, ".cache", "skins")
SKIN_URL = "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.21.11/assets/minecraft/textures/entity/player/wide/{}.png"

# 무기 → (바닥 효과 그림, 타격 종류, 모양, 시전자 스킨)
#   모양: far(앞쪽 먼 곳에 떨어짐) · self(내 주위) · cone(앞 부채꼴) · dash(앞으로 돌진) · shot(날아가 맞음)
SPEC = {
    "thunder": ("wfx_thunder", "thunder", "far", "steve"),
    "dragon": ("wfx_crescent", "fire", "cone", "kai"),
    "wind": ("wfx_wind", "gale", "dash", "alex"),
    "phoenix": ("wfx_barrier", "holy", "self", "sunny"),
    "blackiron": ("wfx_blood", "blood", "dash", "noor"),
    "tiger": ("wfx_claw", "arcane", "cone", "zuri"),
    "staff": ("wfx_staff", "arcane", "self", "ari"),
    "peachwood": ("wfx_fire", "fire", "self", "makena"),
    "frost": ("fx2_frost_burst", "frost", "shot", "alex"),
    "storm": ("fx2_storm_strike", "thunder", "shot", "efe"),
    "scythe": ("fx2_scythe_ring", "soul", "self", "noor"),
    "lance": ("fx2_lance_streak", "holy", "dash", "steve"),
    "skull": ("fx2_skull_miasma", "venom", "shot", "zuri"),
    "chakram": ("fx2_chakram_sun", "holy", "shot", "sunny"),
    "chain": ("fx2_chain_hook", "blood", "shot", "kai"),
    "gauntlet": ("fx2_gauntlet_fissure", "stone", "dash", "efe"),
    "b_talos": ("fx2_talos_gear", "fire", "dash", "steve"),
    "b_sphinx": ("fx2_sphinx_vortex", "sand", "self", "ari"),
    "b_ladon": ("fx2_ladon_fan", "venom", "cone", "makena"),
    "b_cyclops": ("fx2_cyclops_crater", "stone", "far", "kai"),
}
ACCENT = {"thunder": (120, 200, 255), "fire": (255, 140, 50), "gale": (140, 230, 200), "holy": (255, 215, 110), "blood": (230, 50, 60),
          "arcane": (190, 120, 255), "frost": (160, 220, 255), "soul": (90, 240, 230), "venom": (130, 230, 80), "stone": (210, 190, 150),
          "sand": (240, 200, 110)}
DEBRIS = {"fire": ("magma", "blackstone"), "sand": ("sandstone", "chiseled_sandstone"), "venom": ("slime_block", "moss_block"),
          "stone": ("cobblestone", "coarse_dirt"), "arcane": ("amethyst_block", "purple_stained_glass"), "blood": ("redstone_block", "nether_wart_block"),
          "frost": ("packed_ice", "blue_ice"), "soul": ("soul_soil", "soul_sand")}
ADDITIVE = {"thunder", "holy", "arcane", "frost", "soul", "fire", "gale"}
FOES = ["alex", "efe", "noor", "zuri", "steve", "kai"]


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 2


def _skin(name):
    p = os.path.join(SKINS, name + ".png")
    if not os.path.exists(p):
        os.makedirs(SKINS, exist_ok=True)
        import urllib.request
        urllib.request.urlretrieve(SKIN_URL.format(name), p)
    return Image.open(p).convert("RGBA")


# ─────────────────────────────────────────── 마크 플레이어 모델 (스킨 64x64)
def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def _box(mesh, R, sun, tex, M, pivot, lo, hi, uv0, size, light_mul=(1, 1, 1), grow=0.0, flags=0):
    """플레이어 한 부위. 지역 좌표(픽셀): 앞 = +z, 플레이어 오른쪽 = -x. M = 3x3 회전(부위), pivot = 월드 위치(블록)
       uv0 = 스킨 상의 기준점, size = (w, h, d) 픽셀"""
    w, h, d = size
    u, v = uv0
    x0, y0, z0 = (np.array(lo, float) - grow)
    x1, y1, z1 = (np.array(hi, float) + grow)
    S = 1 / 16 * 0.9375

    def P(x, y, z):
        return pivot + M @ (np.array([x, y, z]) * S)
    faces = [  # (네 점: 왼아래 · 오른아래 · 오른위 · 왼위,  스킨 영역,  법선)
        ((P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)), (u + d, v + d, u + d + w, v + d + h), (0, 0, 1)),            # 앞
        ((P(x1, y0, z0), P(x0, y0, z0), P(x0, y1, z0), P(x1, y1, z0)), (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h), (0, 0, -1)),  # 뒤
        ((P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), P(x0, y1, z0)), (u, v + d, u + d, v + d + h), (-1, 0, 0)),                    # 오른쪽
        ((P(x1, y0, z1), P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1)), (u + d + w, v + d, u + 2 * d + w, v + d + h), (1, 0, 0)),     # 왼쪽
        ((P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0), P(x0, y1, z0)), (u + d, v, u + d + w, v + d), (0, 1, 0)),                    # 위
        ((P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1)), (u + d + w, v, u + d + 2 * w, v + d), (0, -1, 0)),          # 아래
    ]
    for (a, b, c, e), (uu0, vv0, uu1, vv1), n in faces:
        lt = R.face_light(M @ np.array(n, float), sun)
        lt = tuple(lt[i] * light_mul[i] for i in range(3))
        mesh.quad(a, b, c, e, (uu0 / 64, vv0 / 64, uu1 / 64, vv1 / 64), tex, flags=flags, light=lt)


def player(mesh, R, sun, skin_key, skin, pos, yaw, arm=0.0, arm_side=0.0, legs=0.0, hurt=0.0, wtex=None, wscale=1.0):
    """pos = 발 위치(블록), yaw = 바라보는 방향(라디안, 0 = +z), arm = 오른팔 들어 올린 각(라디안, + = 앞으로/위로)"""
    t = mesh.texture(skin_key, skin)
    Y = _ry(yaw)
    base = np.array(pos, float)
    S = 1 / 16 * 0.9375
    mul = (1, 1, 1) if hurt <= 0 else (1 + 0.7 * hurt, 1 - 0.55 * hurt, 1 - 0.55 * hurt)
    # 다리
    for side, uv, ouv, sw in ((-1, (0, 16), (0, 32), 1), (1, (16, 48), (0, 48), -1)):
        M = Y @ _rx(legs * sw)
        piv = base + Y @ (np.array([side * 2, 12, 0]) * S)
        _box(mesh, R, sun, t, M, piv, (-2, -12, -2), (2, 0, 2), uv, (4, 12, 4), mul)
        _box(mesh, R, sun, t, M, piv, (-2, -12, -2), (2, 0, 2), ouv, (4, 12, 4), mul, grow=0.25)
    # 몸
    piv = base + Y @ (np.array([0, 12, 0]) * S)
    _box(mesh, R, sun, t, Y, piv, (-4, 0, -2), (4, 12, 2), (16, 16), (8, 12, 4), mul)
    _box(mesh, R, sun, t, Y, piv, (-4, 0, -2), (4, 12, 2), (16, 32), (8, 12, 4), mul, grow=0.25)
    # 머리
    piv = base + Y @ (np.array([0, 24, 0]) * S)
    _box(mesh, R, sun, t, Y, piv, (-4, 0, -4), (4, 8, 4), (0, 0), (8, 8, 8), mul)
    _box(mesh, R, sun, t, Y, piv, (-4, 0, -4), (4, 8, 4), (32, 0), (8, 8, 8), mul, grow=0.5)
    # 왼팔 (+x)
    M = Y @ _rx(-legs * 0.8)
    piv = base + Y @ (np.array([6, 22, 0]) * S)
    _box(mesh, R, sun, t, M, piv, (-2, -12, -2), (2, 0, 2), (32, 48), (4, 12, 4), mul)
    _box(mesh, R, sun, t, M, piv, (-2, -12, -2), (2, 0, 2), (48, 48), (4, 12, 4), mul, grow=0.25)
    # 오른팔 (-x): 앞으로 들어 올림 (x 축 회전) + 옆으로 벌림 (z 축)
    M = Y @ _rz(-arm_side) @ _rx(-arm)
    piv = base + Y @ (np.array([-6, 22, 0]) * S)
    _box(mesh, R, sun, t, M, piv, (-2, -12, -2), (2, 0, 2), (40, 16), (4, 12, 4), mul)
    _box(mesh, R, sun, t, M, piv, (-2, -12, -2), (2, 0, 2), (40, 32), (4, 12, 4), mul, grow=0.25)
    # 무기: 손에 쥔 그림 (손잡이 = 그림 왼아래, 날 = 오른위 → 팔 방향 앞쪽으로)
    if wtex is not None:
        wt = mesh.texture("w_" + skin_key + str(id(wtex)), wtex)
        L = 1.15 * wscale
        hand = piv + M @ (np.array([0, -11, 0]) * S)
        # 팔 지역 좌표에서 그림 평면 = yz 평면, 손잡이에서 날끝이 (앞 + 아래) 방향
        fwd = M @ np.array([0, 0, 1.0]); dn = M @ np.array([0, -1.0, 0])
        a = hand - fwd * 0.18 * L - dn * 0.18 * L
        bq = a + fwd * L
        c = bq + dn * L
        d = a + dn * L
        # 그림의 왼아래(손잡이) = a, 오른위(날끝) = c
        mesh.quad(a, bq, c, d, (0, 0, 1, 1), wt, flags=0, light=(1.1, 1.1, 1.1))


# ─────────────────────────────────────────── 효과 판 (바닥 · 세로 · 숫자)
def _alpha(img, a):
    if a >= 0.999:
        return img
    arr = np.asarray(img).astype(np.float32)
    arr[..., 3] *= max(0.0, a)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def ground_quad(mesh, key, img, c, d, y, yaw=0.0, alpha=1.0, add=False):
    if d <= 0.05 or alpha <= 0.02:
        return
    t = mesh.texture(f"{key}_{round(alpha, 2)}", _alpha(img, alpha))
    r = d / 2
    ca, sa = math.cos(yaw), math.sin(yaw)

    def P(u, v):
        return np.array([c[0] + u * ca + v * sa, y, c[2] - u * sa + v * ca])
    mesh.quad(P(-r, -r), P(r, -r), P(r, r), P(-r, r), (0, 0, 1, 1), t, flags=6 if add else 2, light=(1.0, 1.0, 1.0))


def billboard(mesh, key, img, c, wd, ht, cam_right, y0, alpha=1.0, add=False, light=1.0):
    if ht <= 0.05 or wd <= 0.05 or alpha <= 0.02:
        return
    t = mesh.texture(f"{key}_{round(alpha, 2)}", _alpha(img, alpha))
    r = np.array(cam_right, float); r[1] = 0; r /= (np.linalg.norm(r) + 1e-9)
    b = np.array([c[0], y0, c[2]])
    up = np.array([0, 1.0, 0])
    mesh.quad(b - r * wd / 2, b + r * wd / 2, b + r * wd / 2 + up * ht, b - r * wd / 2 + up * ht, (0, 0, 1, 1), t,
              flags=6 if add else 2, light=(light, light, light))


def cube(mesh, key, tex, c, s, rot, light):
    t = mesh.texture(key, tex)
    M = _ry(rot) @ _rx(rot * 0.7)
    corners = [np.array(c) + M @ (np.array([x, y, z]) * s) for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)]
    for idx in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        mesh.quad(*(corners[i] for i in idx), (0, 0, 1, 1), t, flags=0, light=light)


_NUM = {}


def num_img(txt, col):
    """마크 글자처럼 픽셀 숫자 (그림자 포함)"""
    key = (txt, col)
    if key in _NUM:
        return _NUM[key]
    G = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111", "4": "101101111001001",
         "5": "111100111001111", "6": "111100111101111", "7": "111001001001001", "8": "111101111101111", "9": "111101111001111"}
    W = len(txt) * 4 + 1
    im = Image.new("RGBA", (W * 4, 7 * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k, ch in enumerate(txt):
        g = G[ch]
        for i, b in enumerate(g):
            if b == "1":
                X = (k * 4 + i % 3) * 4; Yy = (i // 3) * 4
                d.rectangle([X + 4, Yy + 4, X + 7, Yy + 7], fill=(60, 30, 10, 255))
                d.rectangle([X, Yy, X + 3, Yy + 3], fill=col + (255,))
    _NUM[key] = im
    return im


_TXT = {}


def text_img(txt, col):
    if (txt, col) in _TXT:
        return _TXT[(txt, col)]
    f = None
    for p in ("C:/Windows/Fonts/malgunbd.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"):
        if os.path.exists(p):
            f = ImageFont.truetype(p, 40)
            break
    if f is None:
        return None
    w = int(f.getlength(txt)) + 12
    im = Image.new("RGBA", (w, 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((7, 7), txt, font=f, fill=(30, 20, 10, 255))
    d.text((4, 4), txt, font=f, fill=col + (255,))
    _TXT[(txt, col)] = im
    return im


# ─────────────────────────────────────────── 장면
class Stage:
    """투기장 바닥 (복셀) + 팔레트 — 한 번만 만든다"""

    def __init__(self):
        import render as R
        self.R = R
        N = 40
        self.N = N
        vox = np.zeros((N, 14, N), np.int32)
        states = ["air", "polished_andesite", "stone_bricks", "chiseled_stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks",
                  "quartz_pillar", "sea_lantern"]
        rng = np.random.default_rng(3)
        for x in range(N):
            for z in range(N):
                k = 2
                if (x // 3 + z // 3) % 2 == 0:
                    k = 1
                r = rng.random()
                if r < 0.06:
                    k = 4
                elif r < 0.1:
                    k = 5
                if x % 8 == 4 and z % 8 == 4:
                    k = 3
                vox[x, 3, z] = k
        # 뒤쪽 기둥 줄 (거리감)
        for x in range(4, N, 7):
            for y in range(4, 10):
                vox[x, y, N - 6] = 6
            vox[x, 10, N - 6] = 7
        self.vox = vox
        self.pal = R.Palette(states)
        self.floor = 4.0
        self.origin = np.array([N / 2, self.floor, 12.0])     # 시전자 발 위치


def scene(st, wid, f, tex, wtex, imp, skins, skill):
    R = st.R
    ground_fx, kind, shape, caster_skin = SPEC[wid]
    acc = ACCENT[kind]
    t = f / FRAMES
    after = t - HIT
    a = after / (1 - HIT) if after >= 0 else -1.0
    sun = np.array([-0.45, 0.78, -0.35]); sun /= np.linalg.norm(sun)
    o = st.origin
    Y = st.floor
    mesh = R.Mesh()
    # 위치 (시전자 = o, 앞 = +z)
    me = o.copy()
    foes = [(1.1, 6.0), (-1.4, 7.0)]
    if shape == "self":
        foes = [(2.3, 1.8), (-2.4, 1.2)]
    elif shape == "cone":
        foes = [(0.9, 3.0), (-1.3, 3.6)]
    elif shape == "dash":
        foes = [(0.6, 3.4), (-0.7, 5.0)]
        me = o + np.array([0, 0, 4.4 * ease((t - 0.08) / 0.3)])
    if shape == "self":
        tgt = me.copy()
    else:
        tgt = o + np.array({"far": (0, 0, 6.4), "cone": (0, 0, 2.8), "dash": (0, 0, 3.0), "shot": (1.1, 0, 6.0)}[shape])
    gs = {"far": 5.5, "self": 7.0, "cone": 6.5, "dash": 6.0, "shot": 4.5}[shape]
    # 카메라: 시전자 오른쪽 뒤 위에서 앞을 내려다봄
    look_at = (me + tgt) / 2 + np.array([0, 0.9, 0])
    cam = o + np.array([-3.6, 3.0, -4.2])
    _, fwd, cam_right, _ = R.look(cam, look_at)
    # 바닥 효과 (시전부터 커져 터질 때 가장 크게, 끝에 사라짐)
    grow = ease(t / HIT)
    fade = 1.0 if t < 0.72 else max(0.0, 1 - (t - 0.72) / 0.28)
    gyaw = 0.0 if shape in ("cone", "dash") else (t * 2.0 if shape == "self" else 0.0)
    ground_quad(mesh, "g_" + ground_fx, tex[ground_fx], tgt, gs * (0.45 + 0.55 * grow), Y + 0.02, gyaw, fade * (0.55 + 0.45 * grow), add=kind in ADDITIVE)
    # 날아가는 것
    if shape == "shot" and t < HIT:
        u = ease(t / HIT)
        p = me + np.array([-0.35, 1.3, 0.6]) + (tgt + np.array([0, 1.0, 0]) - me - np.array([-0.35, 1.3, 0.6])) * u
        orb = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        yy, xx = np.mgrid[0:64, 0:64]
        rr = np.sqrt((xx - 32) ** 2 + (yy - 32) ** 2) / 32
        arr = np.zeros((64, 64, 4), np.float32)
        arr[..., :3] = np.array(acc) / 255 * 0.6 + 0.4
        arr[..., 3] = np.clip(1 - rr, 0, 1) ** 1.6
        orb = Image.fromarray((arr * 255).astype(np.uint8), "RGBA")
        billboard(mesh, "orb", orb, p, 0.9, 0.9, cam_right, p[1] - 0.45, add=True, light=1.4)
    # 터진 뒤: 자국 · 충격파 · 기둥 · 파편
    if a >= 0:
        ground_quad(mesh, "crater", imp["crater"], tgt, gs * 0.75, Y + 0.03, 0, 1 - a)
        if a < 0.45:
            ground_quad(mesh, "shock", imp["shock"], tgt, gs * (0.4 + 1.5 * ease(a / 0.45)), Y + 0.06, 0, 1 - a / 0.45, add=True)
        if a < 0.55:
            k2 = math.sin(math.pi * min(1.0, a / 0.55))
            bw = 1.8 * k2 + 0.3
            billboard(mesh, "burst", imp["burst"], tgt, bw, 3.6 * (0.45 + 0.55 * k2), cam_right, Y, alpha=min(1, 1.6 * k2 + 0.2),
                      add=kind in ADDITIVE, light=1.15)
        if a < 0.75 and kind in DEBRIS:
            import blocks as B
            rr_ = np.random.default_rng(11)
            for i in range(10):
                ang = rr_.uniform(0, 2 * math.pi); dist = rr_.uniform(0.9, 2.4)
                u = a / 0.75
                c = tgt + np.array([math.cos(ang) * dist * u, 0, math.sin(ang) * dist * u])
                c[1] = Y + 0.15 + 2.4 * 4 * u * (1 - u) * rr_.uniform(0.6, 1.1)
                nm = DEBRIS[kind][i % 2]
                bt = Image.fromarray((B.load_tex(nm) * 255).astype(np.uint8), "RGBA")
                cube(mesh, "deb_" + nm, bt, c, 0.26 * (1 - max(0, u - 0.7) * 3), u * 7 + i, R.face_light((0, 1, 0), sun))
    # 적 (맞으면 붉게 · 밀려남 · 숫자)
    for i, (fx, fz) in enumerate(foes):
        hurt = 0.0; push = 0.0
        if a >= 0:
            hurt = max(0.0, 1 - a * 3)
            push = 0.9 * ease(a * 2.2)
        p = o + np.array([fx, 0, fz])
        dv = p - tgt; dv[1] = 0
        dl = np.linalg.norm(dv) or 1
        p = p + dv / dl * push
        yaw_f = math.atan2(me[0] - p[0], me[2] - p[2])
        nm = FOES[(i + len(wid)) % len(FOES)]
        if nm == caster_skin:
            nm = FOES[(i + len(wid) + 2) % len(FOES)]
        player(mesh, R, sun, nm, skins[nm], p, yaw_f, arm=0.25, legs=0.15 * math.sin(t * 12 + i), hurt=hurt)
        if 0 <= a < 0.8:
            img = num_img("7" if i == 0 else "5", (255, 154, 60))
            billboard(mesh, f"num{i}", img, p, 0.9, 0.45, cam_right, Y + 2.1 + a * 1.1, alpha=1 if a < 0.6 else (0.8 - a) / 0.2, light=1.2)
    # 시전자: 무기를 머리 위로 들었다가 앞으로 휘두름
    if t < HIT:
        arm = 0.4 + 2.4 * ease(t / HIT)
    else:
        arm = 2.8 - 2.2 * ease(min(1.0, after * 6)) if after < 0.4 else 0.6 + 0.4 * (1 - min(1, (t - 0.76) * 4))
    legs = 0.5 * math.sin(t * 18) if shape == "dash" and 0.08 < t < HIT else 0.0
    player(mesh, R, sun, caster_skin, skins[caster_skin], me, 0.0, arm=arm, arm_side=0.15, legs=legs, wtex=wtex)
    # 스킬 이름 (머리 위)
    if 0.04 < t < 0.7 and skill:
        ti = text_img(f"« {skill} »", acc)
        if ti is not None:
            h = 0.42
            billboard(mesh, "name", ti, me, h * ti.width / ti.height, h, cam_right, Y + 2.25 + 0.3 * min(1, t * 3), light=1.25)
    im = R.render(st.vox, st.pal, VW, VH, cam, look_at, fov=52, mesh=mesh, ss=3, sun=tuple(sun), fog_dist=60,
                  sky_top=(0.22, 0.30, 0.52), sky_hor=(0.62, 0.58, 0.62), fog_col=(0.55, 0.53, 0.60))
    # 터지는 순간 번쩍
    if 0 <= after < 0.07:
        fl = Image.new("RGB", im.size, acc)
        im = Image.blend(im, fl, 0.35 * (1 - after / 0.07))
    return im


def panel(wid):
    """설명창 판 (영상 칸 바깥) — 어두운 판 + 무기 색 테두리"""
    acc = ACCENT[SPEC[wid][1]]
    im = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3, 3, TW - 4, TH - 4], radius=5, fill=(16, 10, 24, 240))
    d.rounded_rectangle([3, 3, TW - 4, TH - 4], radius=5, outline=acc + (255,), width=1)
    d.rounded_rectangle([5, 5, TW - 6, TH - 6], radius=4, outline=tuple(int(c * 0.45) for c in acc) + (255,), width=1)
    d.line([(12, 24), (TW - 12, 24)], fill=tuple(int(c * 0.7) for c in acc) + (200,), width=1)
    d.rectangle([VX0 - 2, VY0 - 2, VX1 + 1, VY1 + 1], outline=acc + (255,), width=1)
    return im


def frames(st, wid, tex, wtex, skins, skill=""):
    kind = SPEC[wid][1]
    imp = {"shock": impactfx.shock(kind), "crater": impactfx.crater(kind), "burst": impactfx.burst(kind)}
    base = panel(wid)
    out = Image.new("RGBA", (TW, TH * FRAMES))
    for f in range(FRAMES):
        fr = base.copy()
        fr.paste(scene(st, wid, f, tex, wtex, imp, skins, skill).convert("RGBA"), (VX0, VY0))
        out.alpha_composite(fr, (0, TH * f))
    return out


# 스킬 이름 (상점 설명 '우클릭 ○○:' 의 ○○)
SKILL = {"thunder": "심판의 낙뢰", "dragon": "화염 선풍", "wind": "질풍 삼연격", "phoenix": "신성 강타", "blackiron": "피의 돌진",
         "tiger": "그림자 교차", "staff": "비전 폭발", "peachwood": "불창의 비", "frost": "빙결 사격", "storm": "폭풍 투척",
         "scythe": "영혼 수확", "lance": "성광 돌격", "skull": "저주의 해골", "chakram": "태양 원반", "chain": "사슬 끌어오기",
         "gauntlet": "대지 분쇄", "b_talos": "청동 폭주", "b_sphinx": "시간의 모래폭풍", "b_ladon": "삼두 채찍질", "b_cyclops": "거암 투척"}


def _inputs(read):
    tex = {}
    for wid, (g, _, _, _) in SPEC.items():
        tex[g] = Image.open(io.BytesIO(read(f"assets/bg/textures/item/tele/{g}.png"))).convert("RGBA")
    skins = {n: _skin(n) for n in set(FOES) | {s[3] for s in SPEC.values()}}
    return tex, skins


def export(pack, read):
    """read(path) → 이미 팩에 들어 있는 그림 bytes (바닥 효과 · 무기 그림)"""
    tex, skins = _inputs(read)
    st = Stage()
    blank = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    for wid in SPEC:
        wtex = Image.open(io.BytesIO(read(f"assets/bg/textures/item/weapon/{wid}.png"))).convert("RGBA")
        strip = frames(st, wid, tex, wtex, skins, SKILL.get(wid, ""))
        base = f"assets/bg/textures/gui/sprites/tooltip/w_{wid}"
        pack.png(f"{base}_background.png", strip)
        pack.put(f"{base}_background.png.mcmeta", {"animation": {"frametime": FT, "interpolate": False, "width": TW, "height": TH},
                                                   "gui": {"scaling": {"type": "stretch"}}})
        pack.png(f"{base}_frame.png", blank)
        pack.put(f"{base}_frame.png.mcmeta", {"gui": {"scaling": {"type": "stretch"}}})
        print("  tooltip", wid)


def preview(path, read, wids=("thunder", "dragon", "wind", "scythe", "gauntlet", "b_cyclops"), pick=(2, 6, 8, 10, 13, 17)):
    tex, skins = _inputs(read)
    st = Stage()
    rows = []
    for wid in wids:
        wtex = Image.open(io.BytesIO(read(f"assets/bg/textures/item/weapon/{wid}.png"))).convert("RGBA")
        imp = {"shock": impactfx.shock(SPEC[wid][1]), "crater": impactfx.crater(SPEC[wid][1]), "burst": impactfx.burst(SPEC[wid][1])}
        row = Image.new("RGB", ((VW + 6) * len(pick), VH + 6), (30, 30, 30))
        for i, f in enumerate(pick):
            row.paste(scene(st, wid, f, tex, wtex, imp, skins, SKILL.get(wid, "")), (i * (VW + 6) + 3, 3))
        rows.append(row)
    out = Image.new("RGB", (rows[0].width, rows[0].height * len(rows)))
    for i, r in enumerate(rows):
        out.paste(r, (0, r.height * i))
    out.save(path)
