"""복수의 신 네메시스 — 지나치게 앞서간 자에게 응보를 내리는 여신. 보랏빛 두건과 은빛 가면,
   빛나는 보라 눈, 머리 뒤의 후광, 검보라 깃털 날개. 오른손에 응보의 검, 왼손에 정의의 저울.
   다리 대신 땅 위에 떠서 미끄러진다 (치맛자락 · 뒤로 끌리는 옷자락이 흔들림).

 역전 이벤트 전용 (a80-nemesis.sk) — 미니 보스 목록에는 들어가지 않는다
 파츠: 몸통 · 머리 · 후광 · 팔 6 · 검 · 저울 3 · 날개 6 · 옷자락 6
"""
import numpy as np

from modelkit import *

ROBE = Mat((74, 36, 110), var=0.08, edge_dark=0.30, top_light=0.22)
ROBE_D = Mat((44, 20, 70), var=0.08, edge_dark=0.30, top_light=0.18)
SASH = Mat((104, 50, 150), var=0.05, edge_dark=0.28, top_light=0.2, pattern=greek_band(0.5, (240, 204, 110), (54, 26, 12)))
GOLD = Mat((222, 176, 80), var=0.05, edge_dark=0.34, top_light=0.28, pattern=metal((150, 108, 40), 0.3, 0.02))
GOLD_T = Mat((246, 206, 116), var=0.04, edge_dark=0.30, top_light=0.26, pattern=metal((160, 120, 50), 0.28, 0.0))
SILVER = Mat((200, 204, 222), var=0.05, edge_dark=0.30, top_light=0.30, pattern=metal((130, 116, 170), 0.32, 0.02))
FEATHER = Mat((44, 28, 64), var=0.10, edge_dark=0.25, top_light=0.18, pattern=feathers((156, 96, 214), (18, 10, 28)))
FEATHER_D = Mat((30, 18, 46), var=0.10, edge_dark=0.25, top_light=0.16, pattern=feathers((120, 70, 180), (12, 6, 20)))
LEATHER = Mat((60, 34, 24), var=0.08, edge_dark=0.25, top_light=0.15)
EYE = Mat((232, 150, 255), var=0.04, edge_dark=0.0, top_light=0.0)
BLADE = Mat((176, 104, 255), var=0.05, edge_dark=0.10, top_light=0.10)
GLOWV = Mat((206, 132, 255), var=0.06, edge_dark=0.0, top_light=0.0)
HALO = Mat((236, 186, 255), var=0.04, edge_dark=0.0, top_light=0.0)


def mask_face(a, w, h):
    """은빛 가면: 눈구멍 자리 어둡게 · 코 능선 · 입 선"""
    cx = w // 2
    ey = int(h * 0.42)
    a[ey - 1:ey + 2, 1:cx - 1, :3] *= 0.35
    a[ey - 1:ey + 2, cx + 1:w - 1, :3] *= 0.35
    a[ey + 2:int(h * 0.8), cx - 1:cx + 1, :3] = np.minimum(255, a[ey + 2:int(h * 0.8), cx - 1:cx + 1, :3] * 1.3)
    a[int(h * 0.86), cx - 2:cx + 2, :3] *= 0.45


def plate(a, w, h):
    """흉갑: 가운데 능선 + 아래 테두리"""
    cx = w // 2
    a[:, cx - 1:cx + 1, :3] = np.minimum(255, a[:, cx - 1:cx + 1, :3] * 1.25)
    a[h - 1, :, :3] *= 0.5
    for y in range(2, h - 2, 3):
        a[y, 1:3, :3] *= 0.7
        a[y, w - 3:w - 1, :3] *= 0.7


def blade_face(a, w, h):
    """검날: 가운데 밝은 심 + 끝으로 갈수록 밝게"""
    if w >= 3:
        c = w // 2
        a[:, c, :3] = np.minimum(255, a[:, c, :3] * 1.45)
    t = np.linspace(0.85, 1.25, h)[:, None, None]
    a[..., :3] = np.minimum(255, a[..., :3] * t)


def tatter(a, w, h):
    r = np.random.default_rng(w * 37 + h * 11)
    for x in range(w):
        cut = int(r.integers(0, max(1, h // 3)))
        if cut:
            a[h - cut:, x, 3] = 0


def build():
    P = {}
    # ── 허리 아래: 넓어지는 치마 (떠 있음)
    P["skirt"] = Part("skirt", [
        *rbox((-4.6, -5.0, -3.3), (4.6, 0.6, 3.3), ROBE, r=0.9),
        *rbox((-5.4, -10.0, -4.0), (5.4, -4.4, 4.0), ROBE, r=1.0),
        Box((-5.9, -14.5, -4.5), (5.9, -9.4, 4.5), ROBE_D, {"north": tatter, "south": tatter, "east": tatter, "west": tatter}),
        Box((-5.0, -0.6, -3.6), (5.0, 1.1, 3.6), GOLD),
        Box((-1.4, -13.0, 4.0), (1.4, -0.6, 4.6), SASH),
        Box((-6.0, -10.2, -4.6), (6.0, -9.4, 4.6), GOLD_T),
    ])
    # ── 상체: 옷 + 은 흉갑 + 금 목둘레
    P["torso"] = Part("torso", [
        *rbox((-4.4, 0, -2.8), (4.4, 9.2, 2.8), ROBE, r=0.9),
        *rbox((-4.0, 3.0, 2.2), (4.0, 8.8, 3.6), SILVER, {"south": plate}, r=0.5),
        Box((-3.2, 8.4, -2.5), (3.2, 9.8, 2.7), GOLD),
        Box((-0.5, 4.2, 3.55), (0.5, 7.4, 3.8), GLOWV, glow=True),
        Box((-4.6, 0.0, -3.0), (4.6, 1.2, 3.0), GOLD_T),
    ])
    # ── 머리: 두건 + 은빛 가면 + 빛나는 눈 + 금관
    P["head"] = Part("head", [
        *rbox((-3.7, -0.6, -3.9), (3.7, 7.4, 2.9), ROBE_D, r=1.1),
        Box((-2.8, 0.4, 2.3), (2.8, 6.0, 3.4), SILVER, {"south": mask_face}),
        Box((-2.3, 3.0, 3.38), (-0.8, 3.9, 3.62), EYE, glow=True),
        Box((0.8, 3.0, 3.38), (2.3, 3.9, 3.62), EYE, glow=True),
        Box((-3.0, 6.0, 2.0), (3.0, 7.0, 3.3), GOLD),
        Box((-0.5, 7.0, 2.4), (0.5, 9.6, 3.1), GOLD_T),
        Box((-2.4, 7.0, 2.2), (-1.4, 8.6, 2.9), GOLD_T),
        Box((1.4, 7.0, 2.2), (2.4, 8.6, 2.9), GOLD_T),
        Box((-0.35, 8.2, 3.05), (0.35, 8.9, 3.3), GLOWV, glow=True),
    ])
    # ── 후광 (머리 뒤 빛나는 고리)
    P["halo"] = Part("halo", [
        Box((-2.6, 5.4, -0.3), (2.6, 6.4, 0.3), HALO, glow=True),
        Box((-2.6, -6.4, -0.3), (2.6, -5.4, 0.3), HALO, glow=True),
        Box((-6.4, -2.6, -0.3), (-5.4, 2.6, 0.3), HALO, glow=True),
        Box((5.4, -2.6, -0.3), (6.4, 2.6, 0.3), HALO, glow=True),
        Box((-2.6, 5.4, -0.3), (2.6, 6.4, 0.3), HALO, rot=("z", 45, (0, 0, 0)), glow=True),
        Box((-2.6, 5.4, -0.3), (2.6, 6.4, 0.3), HALO, rot=("z", -45, (0, 0, 0)), glow=True),
        Box((-2.6, -6.4, -0.3), (2.6, -5.4, 0.3), HALO, rot=("z", 45, (0, 0, 0)), glow=True),
        Box((-2.6, -6.4, -0.3), (2.6, -5.4, 0.3), HALO, rot=("z", -45, (0, 0, 0)), glow=True),
        Box((-0.5, 6.4, -0.3), (0.5, 8.6, 0.3), HALO, glow=True),
    ])
    # ── 어깨 · 팔
    for s, sg in (("l", 1), ("r", -1)):
        P["pauldron_" + s] = Part("pauldron_" + s, [
            *rbox((-2.7, -2.0, -3.2), (2.7, 1.8, 3.2), GOLD, r=0.8),
            Box((sg * 0.6 - 0.6, 1.8, -1.0), (sg * 0.6 + 0.6, 3.6, 1.0), GOLD_T),
        ])
        P["arm_" + s] = Part("arm_" + s, [*rbox((-1.8, -7.0, -1.8), (1.8, 0.4, 1.8), ROBE, r=0.6)])
        P["fore_" + s] = Part("fore_" + s, [
            *rbox((-2.1, -6.6, -2.1), (2.1, 0.0, 2.1), ROBE, r=0.6),
            Box((-2.3, -6.9, -2.3), (2.3, -5.6, 2.3), GOLD),
            *rbox((-1.3, -9.2, -1.3), (1.3, -6.6, 1.3), SILVER, r=0.4),
        ])
    # ── 응보의 검 (오른손, 손에서 앞으로 뻗음)
    P["sword"] = Part("sword", [
        Box((-0.55, -0.55, -2.2), (0.55, 0.55, 1.6), LEATHER),
        Box((-0.8, -0.8, -3.0), (0.8, 0.8, -2.2), GOLD_T),
        Box((-0.3, -0.3, -3.25), (0.3, 0.3, -3.0), GLOWV, glow=True),
        Box((-2.8, -0.7, 1.6), (2.8, 0.7, 2.5), GOLD),
        Box((-0.8, -0.3, 2.5), (0.8, 0.3, 19.0), BLADE, {"up": blade_face, "down": blade_face}, glow=True),
        Box((-0.4, -0.2, 19.0), (0.4, 0.2, 20.6), BLADE, glow=True),
    ])
    # ── 정의의 저울 (왼손에 매달림) + 양쪽 접시 (흔들림)
    P["scales"] = Part("scales", [
        Box((-0.35, -1.5, -0.35), (0.35, 1.2, 0.35), GOLD),
        Box((-5.2, -1.5, -0.35), (5.2, -0.8, 0.35), GOLD),
        Box((-0.7, 1.2, -0.7), (0.7, 1.8, 0.7), GOLD_T),
        Box((-0.45, -2.3, -0.45), (0.45, -1.5, 0.45), GLOWV, glow=True),
    ])
    for s in ("l", "r"):
        P["pan_" + s] = Part("pan_" + s, [
            Box((-0.15, -4.4, -0.15), (0.15, 0.0, 0.15), GOLD_T),
            Box((-1.9, -4.4, -0.12), (1.9, -4.1, 0.12), GOLD_T),
            Box((-2.2, -5.0, -2.2), (2.2, -4.4, 2.2), GOLD),
        ])
    # ── 날개 (3마디 · 아래로 깃털) — 왼쪽은 +X, 오른쪽은 -X 로 뻗는다
    segs = [(9.0, 9.0, FEATHER_D), (8.0, 12.0, FEATHER), (7.0, 15.0, FEATHER)]
    for s, sg in (("l", 1), ("r", -1)):
        for k, (L, drop, fm) in enumerate(segs):
            x0, x1 = (0.0, L) if sg > 0 else (-L, 0.0)
            bx = [Box((x0, -2.4, -0.6), (x1, 1.8, 0.6), FEATHER_D),
                  Box((x0 + sg * 0.3 if sg > 0 else x0, -drop, -0.35), (x1 if sg > 0 else x1 - 0.3, -2.4, 0.35), fm,
                      {"north": tatter, "south": tatter})]
            if k == 2:
                bx.append(Box((x0, -drop - 0.9, -0.4), (x1, -drop + 0.1, 0.4), GLOWV, glow=True))
            P[f"wing{k}_{s}"] = Part(f"wing{k}_{s}", bx)
    # ── 뒤로 끌리는 옷자락 3갈래 × 2마디
    for c in range(3):
        for seg in range(2):
            P[f"veil{c}_{seg}"] = Part(f"veil{c}_{seg}", [
                Box((-1.9, -7.4, -0.3), (1.9, 0.2, 0.3), ROBE_D, {"north": tatter, "south": tatter} if seg == 1 else None)])
    parts = list(P.values())

    R = Rig("nemesis", 2.0)
    R.bone("skirt", None, (0, 19.0, 0), P["skirt"])
    R.bone("torso", "skirt", (0, 0.8, 0), P["torso"], rest=(2, 0, 0))
    R.bone("head", "torso", (0, 9.6, 0.3), P["head"], rest=(-2, 0, 0))
    R.bone("halo", "head", (0, 4.2, -4.6), P["halo"])
    for s, sg in (("l", 1), ("r", -1)):
        R.bone("pauldron_" + s, "torso", (sg * 5.0, 8.0, 0), P["pauldron_" + s], rest=(0, 0, sg * 8))
        R.bone("arm_" + s, "torso", (sg * 5.4, 7.4, 0), P["arm_" + s], rest=(0, 0, sg * 6))
    R.bone("fore_l", "arm_l", (0, -7.0, 0), P["fore_l"], rest=(-62, 0, 0))
    R.bone("fore_r", "arm_r", (0, -7.0, 0), P["fore_r"], rest=(-40, 0, 0))
    R.bone("sword", "fore_r", (0, -8.2, 0), P["sword"], rest=(-70, 0, 0))
    R.bone("scales", "fore_l", (0, -9.6, 0), P["scales"], rest=(62, 0, 0))
    R.bone("pan_l", "scales", (4.85, -1.2, 0), P["pan_l"])
    R.bone("pan_r", "scales", (-4.85, -1.2, 0), P["pan_r"])
    for s, sg in (("l", 1), ("r", -1)):
        R.bone("wing0_" + s, "torso", (sg * 2.0, 6.8, -3.2), P["wing0_" + s], rest=(0, sg * 22, sg * 38))
        R.bone("wing1_" + s, "wing0_" + s, (sg * 8.6, 0.2, 0), P["wing1_" + s], rest=(0, sg * 10, sg * 6))
        R.bone("wing2_" + s, "wing1_" + s, (sg * 7.6, 0.2, 0), P["wing2_" + s], rest=(0, sg * 8, -sg * 34))
    for c in range(3):
        x = -3.6 + c * 3.6
        R.bone(f"veil{c}_0", "skirt", (x, -1.0, -4.0 - abs(x) * 0.05), P[f"veil{c}_0"], rest=(14, 0, 0))
        R.bone(f"veil{c}_1", f"veil{c}_0", (0, -7.0, 0), P[f"veil{c}_1"], rest=(10, 0, 0))
    return R, parts, anims()


def P_(*ds, **kw):
    out = {}
    for d in ds:
        out.update(d)
    out.update(kw)
    return out


def wings(spread=0.0, flap=0.0, back=0.0):
    """spread: 펼침(+) · flap: 위아래 · back: 뒤로 젖힘"""
    d = {}
    for s, sg in (("l", 1), ("r", -1)):
        d["wing0_" + s] = (0, sg * (back - spread * 0.4), sg * (flap + spread))
        d["wing1_" + s] = (0, 0, sg * (flap * 0.6 + spread * 0.5))
        d["wing2_" + s] = (0, 0, sg * (flap * 0.4 + spread * 0.3))
    return d


def veil(t, amp=1.0, lift=0.0):
    d = {}
    for c in range(3):
        for seg in range(2):
            d[f"veil{c}_{seg}"] = (lift * (1 if seg == 0 else 0.5) + amp * 5 * np.sin(t + c * 1.1 + seg * 0.8), 0, amp * 3 * np.sin(t * 0.7 + c))
    return d


def pans(t, amp=1.0):
    return {"pan_l": (amp * 6 * np.sin(t), 0, amp * 4 * np.sin(t + 1)), "pan_r": (amp * 6 * np.sin(t + 2), 0, amp * 4 * np.sin(t + 3))}


def anims():
    A = {}
    A["idle"] = dict(loop=True, keys=[
        (P_(wings(0, -6, 0), veil(0), pans(0), torso=(2, 0, 0), head=(0, 0, 0), halo=(0, 0, 0), sword=(60, 10, 0), _root=(0, 0, 0)), 20),
        (P_(wings(4, 8, 0), veil(np.pi), pans(np.pi), torso=(-1, 0, 0), head=(-3, 0, 0), halo=(0, 0, 45), sword=(70, 10, 0), _root=(0, 1.0, 0)), 20),
    ])
    glide = []
    for i in range(4):
        ph = i / 4 * 2 * np.pi
        glide.append((P_(wings(10, 14 * np.sin(ph), 18), veil(ph * 2, 1.6, 34), pans(ph, 1.6),
                         skirt=(12, 0, 0), torso=(10, 0, 0), head=(-14, 0, 0), halo=(0, 0, 22.5 * i),
                         arm_l=(18, 0, 6), arm_r=(24, 0, -6), sword=(-100, -20, 0), _root=(0, 0.6 * np.sin(ph), 0)), 5))
    A["glide"] = dict(loop=True, keys=glide)
    A["slash"] = dict(loop=False, keys=[
        (P_(wings(14, 18, 6), veil(0, 1.2, 10), pans(0, 1.5), arm_r=(-158, 0, -26), fore_r=(-30, 0, 0), torso=(-8, 24, 0), head=(0, -14, 0), halo=(0, 0, 30), sword=(120, 70, 0)), 7),
        (P_(wings(2, -18, 10), veil(1, 1.6, 30), pans(1, 2), arm_r=(-28, 0, 24), fore_r=(-10, 0, 0), torso=(14, -30, 0), head=(6, 18, 0), halo=(0, 0, 60), sword=(-180, -60, 0), _root=(0, -0.6, 1.2)), 3),
        (P_(wings(2, -14, 10), veil(2, 1.2, 20), pans(2, 1.5), arm_r=(-20, 0, 20), fore_r=(-10, 0, 0), torso=(12, -24, 0), head=(4, 14, 0), halo=(0, 0, 75), sword=(-180, -80, 0)), 5),
        (P_(wings(0, -6, 0), veil(3), pans(3), torso=(2, 0, 0), halo=(0, 0, 90), sword=(60, 10, 0)), 8),
    ])
    A["death"] = dict(loop=False, keys=[
        (P_(wings(-20, -30, 10), veil(0, 0.4, -6), pans(0, 0.4), torso=(24, 0, 8), head=(30, 0, 10), arm_l=(20, 0, 20), arm_r=(20, 0, -20), _root=(0, -3, 0)), 14),
        (P_(wings(-34, -50, 20), veil(0, 0.2, -10), pans(0, 0.2), skirt=(30, 0, 0), torso=(50, 0, 10), head=(30, 0, 20), arm_l=(40, 0, 30), arm_r=(40, 0, -30), _root=(0, -12, -2)), 20),
    ])
    return A


INFO = dict(hitbox="wither_skeleton", hit_scale=1.7, portrait=dict(bone="head", dist=1.6, cy=3.4, cz=2.6))
