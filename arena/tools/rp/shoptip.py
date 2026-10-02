"""상점 무기 설명창(툴팁) 속 스킬 미리보기 영상

 무기 아이템에 tooltip_style "bg:w_<무기>" 를 주면 마우스를 올렸을 때 설명창 배경이
   assets/bg/textures/gui/sprites/tooltip/w_<무기>_background.png  (움직이는 그림 · 16장 · 2틱마다)
 로 바뀐다. 배경은 설명창 크기에 맞게 늘어나므로(stretch) 설명창 크기를 고정한다 (a50 bgWShopItem):
   글자 영역 폭 230 · 줄 수 18 (이름 1 + 설명 6 + 영상 11) → 설명창 254 x 206 (글자 영역 + 테두리 12씩)
   위 84px = 글자가 올라가는 판, 아래 = 영상 (스킬 쓰는 장면: 시전 → 터짐 → 맞은 적 · 숫자 → 사라짐)
 그림 재료: 실제 게임의 바닥 효과(tele/wfx_* · fx2_*), 무기 그림(weapon/*), 타격 연출(impactfx)
"""
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import impactfx

TW, TH = 254, 206            # 설명창 전체 (픽셀 = 화면 GUI 1칸)
VX0, VY0, VX1, VY1 = 12, 86, 242, 196      # 영상 칸
FRAMES = 16
FT = 2                       # 한 장 2틱 → 1.6초

# 무기 → (바닥 효과 그림, 타격 종류, 모양)
#   모양: far(앞쪽 먼 곳에 떨어짐) · self(내 주위) · cone(앞 부채꼴) · dash(앞으로 돌진) · shot(날아가 맞음)
SPEC = {
    "thunder": ("wfx_thunder", "thunder", "far"),
    "dragon": ("wfx_crescent", "fire", "cone"),
    "wind": ("wfx_wind", "gale", "dash"),
    "phoenix": ("wfx_barrier", "holy", "self"),
    "blackiron": ("wfx_blood", "blood", "dash"),
    "tiger": ("wfx_claw", "arcane", "cone"),
    "staff": ("wfx_staff", "arcane", "self"),
    "peachwood": ("wfx_fire", "fire", "self"),
    "frost": ("fx2_frost_burst", "frost", "shot"),
    "storm": ("fx2_storm_strike", "thunder", "shot"),
    "scythe": ("fx2_scythe_ring", "soul", "self"),
    "lance": ("fx2_lance_streak", "holy", "dash"),
    "skull": ("fx2_skull_miasma", "venom", "shot"),
    "chakram": ("fx2_chakram_sun", "holy", "shot"),
    "chain": ("fx2_chain_hook", "blood", "shot"),
    "gauntlet": ("fx2_gauntlet_fissure", "stone", "dash"),
    "b_talos": ("fx2_talos_gear", "fire", "dash"),
    "b_sphinx": ("fx2_sphinx_vortex", "sand", "self"),
    "b_ladon": ("fx2_ladon_fan", "venom", "cone"),
    "b_cyclops": ("fx2_cyclops_crater", "stone", "far"),
}
ACCENT = {"thunder": (120, 200, 255), "fire": (255, 140, 50), "gale": (140, 230, 200), "holy": (255, 215, 110), "blood": (230, 50, 60),
          "arcane": (190, 120, 255), "frost": (160, 220, 255), "soul": (90, 240, 230), "venom": (130, 230, 80), "stone": (210, 190, 150),
          "sand": (240, 200, 110)}

# ─────────────────────────────────────────── 작은 원근 장면 (영상 칸 230 x 110)
VW, VH = VX1 - VX0, VY1 - VY0
SS = 2                        # 2배로 그린 뒤 줄임
F = 160.0 * SS
CAM = np.array([5.2, 3.1, -1.6])
YAW = math.radians(-48)
PITCH = math.radians(20)


def proj(x, y, z):
    p = np.array([x, y, z], float) - CAM
    cy, sy = math.cos(YAW), math.sin(YAW)
    x1 = p[0] * cy - p[2] * sy
    z1 = p[0] * sy + p[2] * cy
    cp, sp = math.cos(PITCH), math.sin(PITCH)
    Y = p[1] * cp + z1 * sp
    Z = -p[1] * sp + z1 * cp
    Z = max(Z, 0.3)
    return (VW * SS / 2 + F * x1 / Z, VH * SS * 0.42 - F * Y / Z, Z)


def _coeffs(src, dst):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def _alpha(img, a):
    if a >= 0.999:
        return img
    arr = np.asarray(img).astype(np.float32)
    arr[..., 3] *= max(0.0, a)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def decal(img, tex, cx, cz, d, yaw=0.0, alpha=1.0, y=0.0):
    if d <= 0.05 or alpha <= 0.01:
        return
    tex = _alpha(tex, alpha)
    w, h = tex.size
    r = d / 2
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    pts = []
    for (u, v) in ((-1, 1), (1, 1), (1, -1), (-1, -1)):
        lx, lz = u * r, v * r
        pts.append(proj(cx + lx * ca + lz * sa, y, cz - lx * sa + lz * ca)[:2])
    t = tex.transform(img.size, Image.PERSPECTIVE, _coeffs([(0, 0), (w, 0), (w, h), (0, h)], pts), Image.BILINEAR)
    img.alpha_composite(t)


def billboard(img, tex, x, z, wd, ht, y0=0.0, alpha=1.0):
    if ht <= 0.05 or alpha <= 0.01:
        return
    sx, sy, Z = proj(x, y0, z)
    _, sy2, _ = proj(x, y0 + ht, z)
    hp = max(2, int(sy - sy2)); wp = max(2, int(F * wd / Z))
    t = _alpha(tex.resize((wp, hp), Image.LANCZOS), alpha)
    img.alpha_composite(t, (int(sx - wp / 2), int(sy - hp)))


def figure(img, x, z, body, hurt=0.0, lean=0.0):
    """블록 사람 (머리 · 몸 · 다리)"""
    d = ImageDraw.Draw(img)
    sx, sy, Z = proj(x, 0, z)
    k = F / Z
    w = 0.6 * k
    dx = lean * k
    leg = (45, 52, 85); skin = (210, 165, 125)
    if hurt > 0:
        mix = lambda c: tuple(int(c[i] * (1 - hurt) + (255, 60, 60)[i] * hurt) for i in range(3))
        leg, skin, body = mix(leg), mix(skin), mix(body)
    d.rectangle([sx - w / 2, sy - 0.75 * k, sx + w / 2, sy], fill=leg)
    d.rectangle([sx - w / 2 + dx * 0.5, sy - 1.45 * k, sx + w / 2 + dx * 0.5, sy - 0.75 * k], fill=body)
    d.rectangle([sx - w * 0.42 + dx, sy - 1.9 * k, sx + w * 0.42 + dx, sy - 1.45 * k], fill=skin)
    return sx, sy, k


def weapon(img, wtex, sx, sy, k, ang):
    s = max(6, int(1.3 * k))
    t = wtex.resize((s, s), Image.LANCZOS).rotate(ang, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(t, (int(sx - t.width / 2), int(sy - t.height / 2)))


def cube(img, x, y, z, s, col):
    sx, sy, Z = proj(x, y, z)
    p = max(2, int(F * s / Z))
    ImageDraw.Draw(img).rectangle([sx - p / 2, sy - p / 2, sx + p / 2, sy + p / 2], fill=col)


def number(img, x, y, z, txt, col):
    """작은 픽셀 숫자 (설명창 안이라 글꼴 대신 3x5 점 글자)"""
    G = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111", "4": "101101111001001",
         "5": "111100111001111", "6": "111100111101111", "7": "111001001001001", "8": "111101111101111", "9": "111101111001111", ".": "000000000000010"}
    sx, sy, Z = proj(x, y, z)
    px = max(2, int(F * 0.09 / Z))
    d = ImageDraw.Draw(img)
    cx = sx - len(txt) * 4 * px / 2
    for ch in txt:
        g = G.get(ch)
        if g:
            for i, b in enumerate(g):
                if b == "1":
                    X = cx + (i % 3) * px; Y = sy + (i // 3) * px
                    d.rectangle([X + px * 0.35, Y + px * 0.35, X + px * 1.35, Y + px * 1.35], fill=(40, 20, 10))
                    d.rectangle([X, Y, X + px - 1, Y + px - 1], fill=col)
        cx += 4 * px


def ease(t):
    return 1 - (1 - max(0.0, min(1.0, t))) ** 2


def scene(wid, f, tex, wtex, imp):
    """f = 0..FRAMES-1"""
    ground_fx, kind, shape = SPEC[wid]
    img = Image.new("RGBA", (VW * SS, VH * SS), (0, 0, 0, 0))
    # 배경: 저녁 하늘 + 돌바닥
    sky = np.zeros((VH * SS, VW * SS, 4), np.uint8)
    for yy in range(VH * SS):
        t = yy / (VH * SS)
        sky[yy, :, :3] = (np.array((38, 44, 66)) * (1 - t) + np.array((22, 24, 32)) * t).astype(np.uint8)
    sky[..., 3] = 255
    img = Image.fromarray(sky, "RGBA")
    tile = Image.new("RGBA", (256, 256))
    dt = ImageDraw.Draw(tile)
    R = np.random.default_rng(5)
    for i in range(8):
        for j in range(8):
            v = int(R.integers(-10, 10))
            dt.rectangle([i * 32, j * 32, i * 32 + 31, j * 32 + 31], fill=(92 + v, 88 + v, 84 + v, 255))
    decal(img, tile, 0, 5, 22)
    acc = ACCENT[kind]
    t = f / FRAMES
    # 위치
    me = [0.0, 0.0]
    foes = [(0.9, 5.4), (-1.3, 6.2)]
    if shape == "self":
        foes = [(1.9, 1.6), (-2.1, 1.0)]
    if shape == "cone":
        foes = [(0.8, 2.6), (-1.1, 3.0)]
    hit_at = 0.36               # 터지는 순간 (영상 비율)
    if shape == "dash":
        me[1] = 4.2 * ease((t - 0.1) / 0.3)
        foes = [(0.5, 3.0), (-0.6, 4.4)]
    target = {"far": (0.0, 5.8), "self": (me[0], me[1]), "cone": (0, 2.4), "dash": (0, 2.6), "shot": (0.9, 5.4)}[shape]
    after = t - hit_at
    # 바닥 효과 (시전부터 나타나 커지고, 끝에 사라짐)
    gs = {"far": 5.0, "self": 6.5, "cone": 6.0, "dash": 5.5, "shot": 4.0}[shape]
    grow = ease(t / hit_at)
    fade = 1.0 if t < 0.75 else max(0.0, 1 - (t - 0.75) / 0.25)
    yaw = 0 if shape in ("cone", "dash") else (t * 120 if shape == "self" else 0)
    decal(img, tex[ground_fx], target[0], target[1], gs * (0.4 + 0.6 * grow), yaw=yaw, alpha=fade * (0.6 + 0.4 * grow))
    # 터진 뒤: 자국 · 충격파 · 기둥 · 파편
    if after >= 0:
        a = after / (1 - hit_at)
        decal(img, imp["crater"], target[0], target[1], gs * 0.7, alpha=1 - a)
        if a < 0.45:
            decal(img, imp["shock"], target[0], target[1], gs * (0.4 + 1.6 * ease(a / 0.45)), alpha=1 - a / 0.45)
        if a < 0.5:
            k2 = math.sin(math.pi * min(1, a / 0.5))
            billboard(img, imp["burst"], target[0], target[1], 1.6 * k2 + 0.2, 3.2 * (0.4 + 0.6 * k2))
        if a < 0.7:
            Rr = np.random.default_rng(7)
            cols = [tuple(int(c * 0.6) for c in acc) + (255,), (70, 66, 62, 255)]
            for i in range(10):
                ang = Rr.uniform(0, 2 * math.pi); dist = Rr.uniform(0.8, 2.2)
                u = a / 0.7
                cube(img, target[0] + math.cos(ang) * dist * u, 2.2 * 4 * u * (1 - u) * Rr.uniform(0.6, 1.1), target[1] + math.sin(ang) * dist * u, 0.18, cols[i % 2])
    # 날아가는 것 (shot)
    if shape == "shot" and t < hit_at:
        u = ease(t / hit_at)
        bx, bz = me[0] + (target[0] - me[0]) * u, me[1] + 0.8 + (target[1] - me[1] - 0.8) * u
        sx, sy, Z = proj(bx, 1.2, bz)
        r = max(3, int(F * 0.28 / Z))
        glow = Image.new("RGBA", img.size)
        ImageDraw.Draw(glow).ellipse([sx - r * 2, sy - r * 2, sx + r * 2, sy + r * 2], fill=acc + (110,))
        glow = glow.filter(ImageFilter.GaussianBlur(r))
        img.alpha_composite(glow)
        ImageDraw.Draw(img).ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 255, 255, 255))
    # 적 (맞으면 붉게 · 뒤로 밀림 · 숫자)
    for i, (fx, fz) in enumerate(foes):
        hurt = 0.0; push = 0.0
        if after >= 0:
            a = after / (1 - hit_at)
            hurt = max(0.0, 1 - a * 2.5)
            push = 0.9 * ease(a * 2)
        dx, dz = fx - target[0], fz - target[1]
        dl = math.hypot(dx, dz) or 1
        figure(img, fx + dx / dl * push, fz + dz / dl * push, (90, 100, 120) if i else (120, 70, 70), hurt)
        if after >= 0 and after / (1 - hit_at) < 0.75:
            a = after / (1 - hit_at)
            number(img, fx + dx / dl * push, 2.3 + a * 1.0, fz + dz / dl * push, "7" if i == 0 else "5", (255, 154, 60))
    # 나 (무기를 들어 올렸다가 휘두름)
    sx, sy, k = figure(img, me[0], me[1], (60, 90, 170), lean=0.15 if t < hit_at else -0.1)
    ang = 40 + 110 * ease(t / hit_at) if t < hit_at else 150 - 60 * min(1, after * 3)
    weapon(img, wtex, sx + 0.45 * k, sy - 1.35 * k, k, ang - 90)
    # 터지는 순간 번쩍
    if 0 <= after < 0.08:
        fl = Image.new("RGBA", img.size, acc + (int(90 * (1 - after / 0.08)),))
        img.alpha_composite(fl)
    return img.resize((VW, VH), Image.LANCZOS)


def panel(wid):
    """설명창 판 (영상 칸 바깥) — 어두운 판 + 무기 색 테두리"""
    kind = SPEC[wid][1]
    acc = ACCENT[kind]
    im = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3, 3, TW - 4, TH - 4], radius=5, fill=(16, 10, 24, 238))
    d.rounded_rectangle([3, 3, TW - 4, TH - 4], radius=5, outline=acc + (255,), width=1)
    d.rounded_rectangle([5, 5, TW - 6, TH - 6], radius=4, outline=tuple(int(c * 0.45) for c in acc) + (255,), width=1)
    # 이름 아래 구분선
    d.line([(12, 24), (TW - 12, 24)], fill=tuple(int(c * 0.7) for c in acc) + (200,), width=1)
    # 영상 칸 틀
    d.rectangle([VX0 - 2, VY0 - 2, VX1 + 1, VY1 + 1], outline=acc + (255,), width=1)
    d.rectangle([VX0 - 1, VY0 - 1, VX1, VY1], fill=(0, 0, 0, 255))
    return im


def frames(wid, tex, wtex):
    kind = SPEC[wid][1]
    imp = {"shock": impactfx.shock(kind), "crater": impactfx.crater(kind), "burst": impactfx.burst(kind)}
    base = panel(wid)
    out = Image.new("RGBA", (TW, TH * FRAMES))
    for f in range(FRAMES):
        fr = base.copy()
        fr.alpha_composite(scene(wid, f, tex, wtex, imp), (VX0, VY0))
        out.alpha_composite(fr, (0, TH * f))
    return out


def export(pack, read):
    """read(path) → 이미 팩에 들어 있는 그림 bytes (바닥 효과 · 무기 그림)"""
    tex = {}
    for wid, (g, _, _) in SPEC.items():
        tex[g] = Image.open(io.BytesIO(read(f"assets/bg/textures/item/tele/{g}.png"))).convert("RGBA")
    blank = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    for wid in SPEC:
        wtex = Image.open(io.BytesIO(read(f"assets/bg/textures/item/weapon/{wid}.png"))).convert("RGBA")
        strip = frames(wid, tex, wtex)
        base = f"assets/bg/textures/gui/sprites/tooltip/w_{wid}"
        pack.png(f"{base}_background.png", strip)
        pack.put(f"{base}_background.png.mcmeta", {"animation": {"frametime": FT, "interpolate": False}, "gui": {"scaling": {"type": "stretch"}}})
        pack.png(f"{base}_frame.png", blank)
        pack.put(f"{base}_frame.png.mcmeta", {"gui": {"scaling": {"type": "stretch"}}})


def preview(path, read, wids=("thunder", "dragon", "wind", "scythe", "gauntlet", "b_cyclops")):
    tex = {}
    for wid, (g, _, _) in SPEC.items():
        tex[g] = Image.open(io.BytesIO(read(f"assets/bg/textures/item/tele/{g}.png"))).convert("RGBA")
    rows = []
    for wid in wids:
        wtex = Image.open(io.BytesIO(read(f"assets/bg/textures/item/weapon/{wid}.png"))).convert("RGBA")
        st = frames(wid, tex, wtex)
        pick = [0, 4, 6, 8, 11, 14]
        row = Image.new("RGBA", (TW * len(pick), TH))
        for i, f in enumerate(pick):
            row.alpha_composite(st.crop((0, TH * f, TW, TH * (f + 1))), (TW * i, 0))
        rows.append(row)
    out = Image.new("RGB", (rows[0].width, TH * len(rows)), (60, 60, 60))
    for i, r in enumerate(rows):
        out.paste(r.convert("RGB"), (0, TH * i), r)
    out.save(path)
