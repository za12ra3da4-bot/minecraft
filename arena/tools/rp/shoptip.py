"""상점 무기 설명창(툴팁) 속 스킬 미리보기 영상

 무기 아이템에 tooltip_style "bg:w_<무기>" 를 주면 마우스를 올렸을 때 설명창 배경이
   assets/bg/textures/gui/sprites/tooltip/w_<무기>_background.png  (움직이는 그림 · FRAMES 장 · 2틱마다)
 로 바뀐다. 배경은 설명창 크기에 맞게 늘어나므로(stretch) 설명창 크기를 고정한다 (a50 bgWShopItem):
   글자 영역 폭 180 · 줄 수 15 (이름 1 + 설명 6 + 영상 8) → 설명창 204 x 176 (글자 영역 + 테두리 12씩)
   위 84px = 글자가 올라가는 판, 아래 = 영상 (30장 · 1틱 = 1.5초)
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

TW, TH = 204, 176            # 설명창 전체 (픽셀 = 화면 GUI 1칸)
VX0, VY0, VX1, VY1 = 12, 86, 192, 164      # 영상 칸
VW, VH = VX1 - VX0, VY1 - VY0
FRAMES = 30
FT = 1                       # 한 장 1틱 → 1.5초 (부드럽게)
HIT = 0.40                   # 터지는 순간 (영상 비율)
STOP = 2                     # 터질 때 멈칫하는 장 수 (히트스톱)
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


def back_out(t, k=1.7):
    """살짝 넘쳤다 돌아오는 움직임"""
    t = max(0.0, min(1.0, t)) - 1
    return 1 + t * t * ((k + 1) * t + k)


def ease_in(t):
    t = max(0.0, min(1.0, t))
    return t * t * t


def timeline(f):
    """장 번호 → 영상 시간 (터지는 순간 STOP 장 동안 멈춤) + 멈춘 장인지"""
    hf = int(round(HIT * FRAMES))
    if f < hf:
        return f / FRAMES, False
    if f < hf + STOP:
        return HIT, True
    rest = FRAMES - hf - STOP
    return HIT + (f - hf - STOP + 1) / rest * (1 - HIT), False


def speed_lines(im, cx, cy, col, strength):
    """만화 집중선 (터지는 순간)"""
    W, H = im.size
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(int(cx * 7 + cy * 13) % 1000)
    R0 = max(W, H)
    for i in range(46):
        ang = rng.uniform(0, 2 * math.pi)
        r_in = rng.uniform(0.32, 0.55) * R0
        w = rng.uniform(1.0, 3.2)
        x0, y0 = cx + math.cos(ang) * r_in, cy + math.sin(ang) * r_in
        x1, y1 = cx + math.cos(ang) * R0, cy + math.sin(ang) * R0
        px, py = -math.sin(ang) * w, math.cos(ang) * w
        d.polygon([(x0, y0), (x1 + px, y1 + py), (x1 - px, y1 - py)], fill=(255, 255, 255, int(200 * strength)))
    im = im.convert("RGBA")
    im.alpha_composite(lay)
    return im.convert("RGB")


def scene(st, wid, f, tex, wtex, imp, skins, skill):
    R = st.R
    ground_fx, kind, shape, caster_skin = SPEC[wid]
    acc = ACCENT[kind]
    t, frozen = timeline(f)
    after = t - HIT
    a = after / (1 - HIT) if after >= 0 else -1.0
    sun = np.array([-0.45, 0.78, -0.35]); sun /= np.linalg.norm(sun)
    o = st.origin
    Y = st.floor
    mesh = R.Mesh()
    rng = np.random.default_rng(f * 31 + len(wid))
    # 위치 (시전자 = o, 앞 = +z)
    me = o.copy()
    foes = [(1.1, 6.0), (-1.4, 6.8)]
    if shape == "self":
        foes = [(2.3, 1.6), (-2.3, 1.2)]
    elif shape == "cone":
        foes = [(0.9, 3.0), (-1.2, 3.5)]
    elif shape == "dash":
        foes = [(0.6, 3.6), (-0.7, 5.0)]
        me = o + np.array([0, 0, 4.4 * ease((t - 0.12) / (HIT - 0.12))])
    jump = 0.0
    if shape == "self" and t < HIT:
        u = max(0.0, (t - 0.1) / (HIT - 0.1))
        jump = 1.1 * math.sin(math.pi * u) if u > 0 else 0.0           # 뛰어올랐다가 내리꽂음
    tgt = me.copy() if shape == "self" else o + np.array({"far": (0, 0, 6.4), "cone": (0, 0, 2.8), "dash": (0, 0, 3.2), "shot": (1.1, 0, 6.0)}[shape])
    tgt[1] = o[1]
    gs = {"far": 5.5, "self": 6.5, "cone": 6.0, "dash": 5.5, "shot": 4.5}[shape]
    # 카메라: 천천히 돌며, 터질 때 확 당기고 흔들림
    phi = -0.28 + 0.42 * (f / FRAMES)
    base = np.array([-5.0, 3.6, -6.6])
    cam_off = np.array([base[0] * math.cos(phi) - base[2] * math.sin(phi), base[1], base[0] * math.sin(phi) + base[2] * math.cos(phi)])
    look_at = (me + tgt) / 2 + np.array([0, 1.1, 0])
    zoom = 1.0
    if a >= 0:
        zoom = 1 - 0.15 * math.exp(-a * 7)
    elif t > HIT - 0.12:
        zoom = 1 - 0.08 * (t - (HIT - 0.12)) / 0.12
    cam = look_at + cam_off * zoom
    if 0 <= a < 0.18 or frozen:
        k = 0.12 * (1 - max(a, 0) / 0.18)
        cam = cam + rng.uniform(-k, k, 3)
    _, fwd, cam_right, cam_up = R.look(cam, look_at)
    # 바닥 효과 (시전부터 빙글빙글 커지며 빛나다가 터짐)
    grow = back_out(t / HIT)
    fade = 1.0 if t < 0.74 else max(0.0, 1 - (t - 0.74) / 0.26)
    gyaw = t * 3.0 if shape in ("self", "far", "shot") else 0.0
    ground_quad(mesh, "g_" + ground_fx, tex[ground_fx], tgt, gs * (0.3 + 0.7 * grow), Y + 0.02, gyaw, fade * (0.5 + 0.5 * min(1, grow)), add=kind in ADDITIVE)
    # 날아가는 것 (빛 구슬 + 꼬리)
    if shape == "shot" and 0.12 < t < HIT:
        u = ease((t - 0.12) / (HIT - 0.12))
        st0 = me + np.array([-0.35, 1.3, 0.6])
        en = tgt + np.array([0, 1.0, 0])
        yy, xx = np.mgrid[0:64, 0:64]
        rr = np.sqrt((xx - 32) ** 2 + (yy - 32) ** 2) / 32
        arr = np.zeros((64, 64, 4), np.float32)
        arr[..., :3] = np.array(acc) / 255 * 0.6 + 0.4
        arr[..., 3] = np.clip(1 - rr, 0, 1) ** 1.6
        orb = Image.fromarray((arr * 255).astype(np.uint8), "RGBA")
        for j in range(5):
            uu = max(0.0, u - j * 0.06)
            pp = st0 + (en - st0) * uu
            sz = 0.95 * (1 - j * 0.16)
            billboard(mesh, f"orb{j}", orb, pp, sz, sz, cam_right, pp[1] - sz / 2, alpha=1 - j * 0.18, add=True, light=1.4)
    # 터진 뒤: 자국 · 충격파 두 겹 · 기둥(늘었다 줄었다) · 파편
    if a >= 0:
        ground_quad(mesh, "crater", imp["crater"], tgt, gs * 0.8, Y + 0.03, 0, 1 - a)
        for j, (dl, sc) in enumerate(((0.0, 1.7), (0.1, 1.15))):
            aa = (a - dl) / 0.42
            if 0 <= aa < 1:
                ground_quad(mesh, f"shock{j}", imp["shock"], tgt, gs * (0.3 + sc * ease(aa)), Y + 0.06 + j * 0.01, 0, 1 - aa, add=True)
        if a < 0.5:
            u = a / 0.5
            sy = 1.25 * math.sin(math.pi * min(1.0, u * 1.4)) if u < 0.7 else max(0.0, 1 - (u - 0.7) / 0.3) * 0.6
            sx = 1.6 - 0.9 * u                                             # 처음엔 납작하고 넓게 → 위로 길게
            billboard(mesh, "burst", imp["burst"], tgt, 1.2 * sx + 0.2, 3.4 * max(0.15, sy), cam_right, Y, alpha=min(1.0, 2.2 * (1 - u) + 0.1),
                      add=kind in ADDITIVE, light=1.2)
        if a < 0.8 and kind in DEBRIS:
            import blocks as B
            rr_ = np.random.default_rng(11)
            for i in range(12):
                ang = rr_.uniform(0, 2 * math.pi); dist = rr_.uniform(1.0, 2.8)
                u = a / 0.8
                c = tgt + np.array([math.cos(ang) * dist * ease(u), 0, math.sin(ang) * dist * ease(u)])
                c[1] = Y + 0.15 + 2.8 * 4 * u * (1 - u) * rr_.uniform(0.6, 1.1)
                nm = DEBRIS[kind][i % 2]
                bt = Image.fromarray((B.load_tex(nm) * 255).astype(np.uint8), "RGBA")
                cube(mesh, "deb_" + nm, bt, c, 0.28 * (1 - max(0, u - 0.75) * 4), u * 9 + i, R.face_light((0, 1, 0), sun))
    # 적: 맞으면 번쩍번쩍 붉어지고, 공중으로 떠올랐다 떨어지며 빙글 돌고, 숫자가 튀어오름
    for i, (fx, fz) in enumerate(foes):
        hurt = 0.0; push = 0.0; lift = 0.0; spin = 0.0
        if a >= 0:
            hurt = 1.0 if (a < 0.35 and f % 2 == 0) or frozen else max(0.0, 0.6 - a * 2)
            u = min(1.0, a / 0.55)
            push = 1.5 * ease(u)
            lift = 0.85 * 4 * u * (1 - u)
            spin = a * 7 * (1 if i == 0 else -1)
        p = o + np.array([fx, 0, fz])
        dv = p - tgt; dv[1] = 0
        dl = np.linalg.norm(dv) or 1
        p = p + dv / dl * push
        p[1] += lift
        yaw_f = math.atan2(me[0] - p[0], me[2] - p[2]) + spin
        nm = FOES[(i + len(wid)) % len(FOES)]
        if nm == caster_skin:
            nm = FOES[(i + len(wid) + 2) % len(FOES)]
        idle = 0.18 * math.sin(f / FRAMES * 2 * math.pi * 2 + i)
        player(mesh, R, sun, nm, skins[nm], p, yaw_f, arm=0.25 + (1.6 if 0 <= a < 0.5 else 0) , arm_side=0.4 if 0 <= a < 0.5 else 0,
               legs=idle if a < 0 else 0.6 * math.sin(a * 20), hurt=hurt)
        if 0 <= a < 0.85:
            img = num_img("7" if i == 0 else "5", (255, 154, 60))
            pop = back_out(min(1.0, a / 0.2))
            billboard(mesh, f"num{i}", img, p, 0.95 * pop, 0.48 * pop, cam_right, Y + 2.1 + a * 1.3 + lift * 0.5,
                      alpha=1 if a < 0.6 else (0.85 - a) / 0.25, light=1.25)
    # 시전자: 몸을 틀며 무기를 머리 위로 → 순식간에 내려침 → 천천히 원래 자세
    wind_end = HIT - 0.1
    if t < wind_end:
        u = back_out(t / wind_end)
        arm = 0.3 + 2.7 * u
        twist = -0.55 * u
    elif t < HIT:
        u = ease_in((t - wind_end) / (HIT - wind_end))
        arm = 3.0 - 2.9 * u
        twist = -0.55 + 0.95 * u
    else:
        u = ease(min(1.0, (t - HIT) / 0.45))
        arm = 0.1 + 0.4 * u
        twist = 0.4 * (1 - u)
    legs = 0.0
    if shape == "dash" and 0.12 < t < HIT:
        legs = 0.7 * math.sin(f * 1.6)
    elif t >= wind_end - 0.05 and t < HIT + 0.2:
        legs = 0.35                                                       # 한 발 내딛기
    pos = me + np.array([0, jump, 0])
    player(mesh, R, sun, caster_skin, skins[caster_skin], pos, twist, arm=arm, arm_side=0.12, legs=legs, wtex=wtex)
    # 스킬 이름 (머리 위로 튀어오름)
    if 0.03 < t < 0.75 and skill:
        ti = text_img(f"« {skill} »", acc)
        if ti is not None:
            pop = back_out(min(1.0, (t - 0.03) / 0.12))
            h = 0.46 * pop
            billboard(mesh, "name", ti, pos, h * ti.width / ti.height, h, cam_right, Y + 2.25 + jump + 0.25 * min(1, t * 3), light=1.25)
    fov = 54
    im = R.render(st.vox, st.pal, VW, VH, cam, look_at, fov=fov, mesh=mesh, ss=3, sun=tuple(sun), fog_dist=60,
                  sky_top=(0.22, 0.30, 0.52), sky_hor=(0.62, 0.58, 0.62), fog_col=(0.55, 0.53, 0.60))
    # 터지는 순간: 멈칫 + 번쩍 + 집중선
    if frozen or 0 <= after < 0.05:
        c, fw, rt, up = R.look(cam, look_at)
        v = np.array([tgt[0], Y + 1.0, tgt[2]]) - c
        z = v @ fw
        focal = (VW * 0.5) / math.tan(math.radians(fov) * 0.5)
        sx = VW / 2 + (v @ rt) / z * focal
        sy_ = VH / 2 - (v @ up) / z * focal
        st_ = 1.0 if frozen else 0.5
        im = Image.blend(im, Image.new("RGB", im.size, tuple(int(c_ * 0.5 + 127) for c_ in acc)), 0.4 * st_)
        im = speed_lines(im, sx, sy_, acc, st_)
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


def preview(path, read, wids=("thunder", "dragon", "wind", "scythe", "gauntlet", "b_cyclops"), pick=(3, 9, 12, 14, 18, 24)):
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
