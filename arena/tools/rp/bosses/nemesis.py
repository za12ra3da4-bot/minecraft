"""복수의 신 네메시스 — 지나치게 앞서간 자에게 응보를 내리는 여신. 키 8블록 남짓, 날개폭 16블록.

 · 흑요석 · 은 갑옷에 금 장식, 가슴에 빛나는 '심판의 눈' 보석
 · 날개 달린 은 투구 · 가면 틈으로 빛나는 눈 · 금관 · 뒤로 흩날리는 머리카락
 · 머리 뒤 두 겹 후광 (바깥 팔각 고리 + 빛살 8줄, 안쪽 고리)
 · 날개 두 쌍 (큰 위 날개 + 작은 아래 날개) — 덮깃 · 둘째깃 · 따로 움직이는 첫째깃(빛나는 끝)
 · 바닥에서 떠 있는 여러 겹 옷자락 (8자락 × 2마디, 금 단 · 찢긴 끝)
 · 오른손: 룬이 빛나는 날개 손잡이 대검 / 왼손: 정의의 저울 (흔들리는 접시 · 빛나는 구슬)
 · 몸 주위를 떠다니는 보라 수정 조각 4개

 역전 이벤트 전용 (a80-nemesis.sk) — 미니 보스 목록에는 들어가지 않는다
 애니메이션: rise(등장: 날개를 접었다가 활짝) · idle · glide · slash · death
"""
import numpy as np

from modelkit import *

# ── 재질
ROBE = Mat((70, 32, 112), var=0.07, edge_dark=0.28, top_light=0.22, pattern=stripes((70, 32, 112), (58, 24, 96), 3))
ROBE_D = Mat((40, 16, 66), var=0.08, edge_dark=0.28, top_light=0.18)
ROBE_IN = Mat((26, 10, 44), var=0.08, edge_dark=0.2, top_light=0.12)
GOLD = Mat((226, 178, 76), var=0.05, edge_dark=0.34, top_light=0.30, pattern=metal((150, 106, 36), 0.32, 0.02))
GOLD_B = Mat((236, 192, 96), var=0.04, edge_dark=0.32, top_light=0.28, pattern=combine(metal((150, 110, 40), 0.3, 0.0), greek_band(0.5, (255, 236, 160), (96, 58, 14))))
SILVER = Mat((206, 210, 228), var=0.05, edge_dark=0.30, top_light=0.32, pattern=metal((128, 112, 176), 0.34, 0.02))
OBSID = Mat((36, 26, 52), var=0.07, edge_dark=0.30, top_light=0.26, pattern=metal((110, 70, 170), 0.36, 0.03))
STEEL = Mat((112, 104, 146), var=0.05, edge_dark=0.25, top_light=0.25, pattern=metal((180, 150, 240), 0.3, 0.0))
FEATHER = Mat((34, 22, 54), var=0.10, edge_dark=0.22, top_light=0.18, pattern=feathers((140, 82, 210), (12, 6, 22)))
FEATHER_C = Mat((48, 30, 74), var=0.09, edge_dark=0.25, top_light=0.2, pattern=scales((16, 8, 28), 4, 1.3))
FEATHER_P = Mat((26, 16, 42), var=0.10, edge_dark=0.22, top_light=0.16, pattern=feathers((170, 100, 240), (10, 4, 18)))
HAIR = Mat((52, 22, 84), var=0.10, edge_dark=0.2, top_light=0.2, pattern=stripes((52, 22, 84), (36, 14, 62), 1))
LEATHER = Mat((58, 30, 22), var=0.08, edge_dark=0.25, top_light=0.15, pattern=stripes((58, 30, 22), (40, 20, 14), 1, vertical=False))
GLOW = Mat((212, 140, 255), var=0.05, edge_dark=0.0, top_light=0.0)
GLOW_W = Mat((248, 226, 255), var=0.03, edge_dark=0.0, top_light=0.0)
EYE = Mat((246, 196, 255), var=0.02, edge_dark=0.0, top_light=0.0)
CRYSTAL = Mat((190, 110, 255), var=0.10, edge_dark=0.15, top_light=0.25)


def mask_face(a, w, h):
    """은빛 가면: 눈 틈 어둡게 · 코 능선 · 뺨 선"""
    cx = w // 2
    ey = int(h * 0.48)
    a[ey - 1:ey + 2, 1:w - 1, :3] *= 0.25
    a[ey + 2:int(h * 0.85), cx - 1:cx + 1, :3] = np.minimum(255, a[ey + 2:int(h * 0.85), cx - 1:cx + 1, :3] * 1.35)
    for x in range(2, cx - 1, 2):
        a[int(h * 0.7), x, :3] *= 0.6
        a[int(h * 0.7), w - 1 - x, :3] *= 0.6


def plate(a, w, h):
    """흉갑: 가운데 능선 · 갈비 결 · 아래 테두리"""
    cx = w // 2
    a[:, cx - 1:cx + 1, :3] = np.minimum(255, a[:, cx - 1:cx + 1, :3] * 1.3)
    for y in range(3, h - 2, 4):
        a[y, 2:cx - 2, :3] *= 0.65
        a[y, cx + 2:w - 2, :3] *= 0.65
    a[h - 1, :, :3] *= 0.45


def runes(a, w, h):
    """검날 룬: 가운데 줄에 끊어진 빛"""
    for y in range(h):
        if (y // 3) % 3 != 2:
            a[y, :, :3] = np.minimum(255, a[y, :, :3] * 1.25)


def tatter(a, w, h):
    r = np.random.default_rng(w * 37 + h * 11)
    for x in range(w):
        cut = int(r.integers(0, max(1, h // 3)))
        if cut:
            a[h - cut:, x, 3] = 0


def taper(a, w, h):
    """첫째깃: 깃대에서 멀어질수록(오른쪽 끝) 좁아짐 — 위아래를 투명하게"""
    for x in range(w):
        k = int((x / max(1, w - 1)) ** 3.0 * (h // 2 - 1))
        if k > 0:
            a[:k, x, 3] = 0
            a[h - k:, x, 3] = 0


def build():
    P = {}
    B = []          # (name, parent, offset, part_key, rest)

    def part(name, boxes, glow=False):
        P[name] = Part(name, boxes, glow)
        return name

    def bone(name, parent, off, pk=None, rest=(0, 0, 0)):
        B.append((name, parent, off, pk, rest))

    # ═══ 허리 (뿌리) · 치마 안쪽 · 벨트
    part("core", [
        *rbox((-6.0, -2.0, -4.6), (6.0, 2.4, 4.6), OBSID, r=1.0),
        Box((-6.4, -0.4, -5.0), (6.4, 1.8, 5.0), GOLD_B),
        *rbox((-1.8, -1.6, 4.8), (1.8, 2.4, 5.8), GOLD, r=0.5),
        Box((-1.0, -0.8, 5.7), (1.0, 1.6, 6.2), GLOW, glow=True),
        *rbox((-7.0, -10.0, -5.4), (7.0, -1.6, 5.4), ROBE_IN, r=1.2),
        *rbox((-8.0, -18.0, -6.4), (8.0, -9.6, 6.4), ROBE_IN, r=1.2),
        Box((-8.6, -22.0, -7.0), (8.6, -17.6, 7.0), ROBE_IN, {"north": tatter, "south": tatter, "east": tatter, "west": tatter}),
    ])
    bone("core", None, (0, 25.0, 0), "core")
    # 엉덩이 갑옷 조각 4개
    for k, (ang, x, z) in enumerate(((0, 0, 5.2), (180, 0, -5.2), (90, 6.2, 0), (-90, -6.2, 0))):
        n = part(f"tasset{k}", [
            *rbox((-3.4, -7.0, -0.7), (3.4, 0.4, 0.7), SILVER, r=0.5),
            Box((-3.6, -7.6, -0.8), (3.6, -6.6, 0.8), GOLD),
            Box((-0.6, -6.0, 0.6), (0.6, -1.0, 0.95), GLOW, glow=True),
        ])
        bone(n, "core", (x, -0.8, z), n, rest=(-12, ang, 0))
    # 겉 옷자락 8자락 × 2마디
    for k in range(8):
        ang = k * 45
        r = 6.4
        x, z = r * np.sin(np.radians(ang)), r * np.cos(np.radians(ang))
        n0 = part(f"robe{k}_0", [
            Box((-3.0, -10.6, -0.45), (3.0, 0.4, 0.45), ROBE),
            Box((-3.2, -10.6, -0.55), (-2.4, 0.4, 0.55), GOLD),
            Box((2.4, -10.6, -0.55), (3.2, 0.4, 0.55), GOLD),
        ])
        n1 = part(f"robe{k}_1", [
            Box((-3.4, -12.0, -0.4), (3.4, 0.3, 0.4), ROBE_D, {"north": tatter, "south": tatter}),
            Box((-3.5, -1.0, -0.5), (3.5, 0.3, 0.5), GOLD_B),
        ])
        bone(n0, "core", (x, -1.4, z), n0, rest=(-9, ang, 0))
        bone(n1, n0, (0, -10.4, 0), n1, rest=(-4, 0, 0))

    # ═══ 배 · 가슴 (흉갑 + 심판의 눈 + 목가리개)
    part("abdomen", [
        *rbox((-5.2, 0, -3.8), (5.2, 7.4, 3.8), OBSID, r=1.0),
        *[Box((-4.8, y, 3.5), (4.8, y + 0.8, 4.1), GOLD) for y in (2.2, 5.2)],
        Box((-0.5, 0.6, 3.9), (0.5, 7.0, 4.3), GLOW, glow=True),
    ])
    bone("abdomen", "core", (0, 2.2, 0), "abdomen", rest=(2, 0, 0))
    part("chest", [
        *rbox((-8.4, 0, -5.0), (8.4, 11.6, 5.0), SILVER, r=1.6),
        *rbox((-7.6, 2.0, 4.2), (-0.6, 10.4, 6.2), SILVER, {"south": plate}, r=0.8),
        *rbox((0.6, 2.0, 4.2), (7.6, 10.4, 6.2), SILVER, {"south": plate}, r=0.8),
        *rbox((-2.6, 4.0, 5.6), (2.6, 9.0, 7.0), GOLD, r=0.6),
        Box((-1.7, 4.9, 6.9), (1.7, 8.1, 7.5), GLOW_W, glow=True),
        Box((-1.0, 5.6, 7.45), (1.0, 7.4, 7.7), EYE, glow=True),
        Box((-8.8, 10.0, -5.4), (8.8, 12.0, 5.4), GOLD_B),
        *rbox((-4.6, 11.4, -3.8), (4.6, 14.2, 3.8), OBSID, r=0.8),
        Box((-5.0, 13.6, -4.2), (5.0, 14.6, 4.2), GOLD),
        *rbox((-7.0, 1.0, -6.2), (7.0, 10.6, -4.6), OBSID, r=0.6),
        Box((-0.5, 1.6, -6.4), (0.5, 10.0, -6.0), GLOW, glow=True),
    ])
    bone("chest", "abdomen", (0, 7.0, 0), "chest", rest=(2, 0, 0))

    # ═══ 머리: 날개 투구 · 가면 · 빛나는 눈 · 금관
    helm_wings = []
    for sg in (1, -1):
        for k in range(3):
            xa, xb = (sg * 4.3 - 0.5, sg * 4.3 + 0.6) if sg > 0 else (sg * 4.3 - 0.6, sg * 4.3 + 0.5)
            helm_wings.append(Box((xa, 4.0 + k * 1.6, -1.0 - k * 0.6), (xb, 5.2 + k * 1.6, 3.0 - k * 0.6), GOLD,
                                  rot=("x", -22.5, (sg * 4.3, 4.0, 1.0))))
    part("head", [
        *rbox((-4.4, 0, -4.6), (4.4, 9.0, 4.2), SILVER, r=1.6),
        Box((-3.6, 1.0, 3.6), (3.6, 7.0, 4.8), SILVER, {"south": mask_face}),
        Box((-3.0, 4.0, 4.75), (-0.9, 4.9, 5.0), EYE, glow=True),
        Box((0.9, 4.0, 4.75), (3.0, 4.9, 5.0), EYE, glow=True),
        Box((-4.6, 7.0, -4.8), (4.6, 8.4, 4.4), GOLD_B),
        Box((-0.6, 8.4, 3.0), (0.6, 13.0, 4.2), GOLD), Box((-0.35, 12.0, 4.15), (0.35, 12.8, 4.4), GLOW, glow=True),
        Box((-2.8, 8.4, 2.6), (-1.8, 11.4, 3.6), GOLD), Box((1.8, 8.4, 2.6), (2.8, 11.4, 3.6), GOLD),
        Box((-4.4, 8.4, 1.2), (-3.6, 10.4, 2.2), GOLD), Box((3.6, 8.4, 1.2), (4.4, 10.4, 2.2), GOLD),
        *rbox((-1.4, 8.8, -4.6), (1.4, 11.0, 1.6), SILVER, r=0.5),
        *helm_wings,
    ])
    bone("head", "chest", (0, 14.2, 0.6), "head", rest=(-2, 0, 0))
    # 머리카락 5가닥 × 2마디 (투구 아래 뒤로)
    for k in range(5):
        x = -3.6 + k * 1.8
        n0 = part(f"hair{k}_0", [Box((-0.9, -9.0, -0.6), (0.9, 0.3, 0.6), HAIR)])
        n1 = part(f"hair{k}_1", [Box((-0.8, -9.0, -0.5), (0.8, 0.2, 0.5), HAIR, {"north": tatter, "south": tatter}),
                                 Box((-0.4, -9.6, -0.3), (0.4, -8.8, 0.3), GLOW, glow=True)])
        bone(n0, "head", (x, 2.0, -4.2), n0, rest=(26 + abs(k - 2) * 4, 0, (k - 2) * 6))
        bone(n1, n0, (0, -8.8, 0), n1, rest=(10, 0, 0))

    # ═══ 후광: 바깥 팔각 + 빛살 8줄 · 안쪽 고리
    def octa(R, th, d, mat):
        s = R * np.tan(np.radians(22.5))
        out = []
        for (y0, y1) in ((R - th, R), (-R, -R + th)):
            out += [Box((-s, y0, -d), (s, y1, d), mat, glow=True),
                    Box((-s, y0, -d), (s, y1, d), mat, rot=("z", 45, (0, 0, 0)), glow=True),
                    Box((-s, y0, -d), (s, y1, d), mat, rot=("z", -45, (0, 0, 0)), glow=True)]
        out += [Box((-R, -s, -d), (-R + th, s, d), mat, glow=True), Box((R - th, -s, -d), (R, s, d), mat, glow=True)]
        return out

    R_O, R_I = 14.0, 9.0
    halo_o = octa(R_O, 1.0, 0.35, GLOW_W)
    for (frm, to) in (((-0.5, R_O, -0.25), (0.5, R_O + 7.0, 0.25)), ((-0.5, -R_O - 4.0, -0.25), (0.5, -R_O, 0.25)),
                      ((R_O, -0.5, -0.25), (R_O + 5.0, 0.5, 0.25)), ((-R_O - 5.0, -0.5, -0.25), (-R_O, 0.5, 0.25))):
        halo_o.append(Box(frm, to, GLOW, glow=True))
    for ang in (45, -45):
        halo_o.append(Box((-0.5, R_O, -0.25), (0.5, R_O + 4.5, 0.25), GLOW, rot=("z", ang, (0, 0, 0)), glow=True))
        halo_o.append(Box((-0.5, -R_O - 4.5, -0.25), (0.5, -R_O, 0.25), GLOW, rot=("z", ang, (0, 0, 0)), glow=True))
    part("halo_o", halo_o, glow=True)
    part("halo_i", octa(R_I, 0.7, 0.3, GLOW), glow=True)
    bone("halo_o", "head", (0, 5.0, -8.0), "halo_o")
    bone("halo_i", "head", (0, 5.0, -7.2), "halo_i")

    # ═══ 어깨 · 팔 · 건틀릿
    for s, sg in (("l", 1), ("r", -1)):
        n = part("pauldron_" + s, [
            *rbox((-4.2, -3.0, -5.0), (4.2, 2.6, 5.0), SILVER, r=1.4),
            *rbox((-4.8, -4.6, -5.4), (4.8, -2.4, 5.4), OBSID, r=0.8),
            Box((-5.0, -5.2, -5.6), (5.0, -4.4, 5.6), GOLD_B),
            Box((-4.4, 1.6, -4.2), (4.4, 2.8, 4.2), GOLD),
        ])
        bone(n, "chest", (sg * 9.6, 11.4, 0), n, rest=(0, 0, sg * 12))
        n2 = part("spike_" + s, [
            Box((-0.9, 0, -0.9), (0.9, 6.0, 0.9), GOLD),
            Box((-0.5, 6.0, -0.5), (0.5, 8.4, 0.5), GOLD),
            Box((-0.3, 5.0, 0.85), (0.3, 7.0, 1.0), GLOW, glow=True),
            Box((-0.7, 0, -3.4), (0.7, 4.0, -2.0), GOLD),
            Box((-0.7, 0, 2.0), (0.7, 4.0, 3.4), GOLD),
        ])
        bone(n2, n, (sg * 1.0, 2.6, 0), n2, rest=(0, 0, -sg * 24))
        n = part("arm_" + s, [
            *rbox((-2.6, -11.0, -2.6), (2.6, 0.6, 2.6), OBSID, r=0.8),
            *rbox((-3.0, -6.0, -3.0), (3.0, -3.6, 3.0), GOLD, r=0.6),
        ])
        bone(n, "chest", (sg * 10.4, 9.4, 0), n, rest=(0, 0, sg * 8))
        n = part("fore_" + s, [
            *rbox((-3.0, -9.6, -3.0), (3.0, 0.4, 3.0), SILVER, r=1.0),
            *rbox((-3.5, -9.8, -3.5), (3.5, -6.6, 3.5), GOLD, r=0.7),
            Box((-0.4, -6.0, 2.9), (0.4, -1.0, 3.3), GLOW, glow=True),
            *rbox((-3.3, -0.8, -3.3), (3.3, 1.0, 3.3), OBSID, r=0.5),
        ])
        bone(n, "arm_" + s, (0, -11.0, 0), n, rest=(-30, 0, 0))
        n = part("hand_" + s, [
            *rbox((-2.4, -4.6, -2.2), (2.4, 0.4, 2.4), SILVER, r=0.8),
            *rbox((-2.6, -5.6, 0.4), (2.6, -3.6, 3.0), OBSID, r=0.6),
        ])
        bone(n, "fore_" + s, (0, -9.8, 0), n)

    # ═══ 응보의 대검 (손잡이 · 날개 코등이 / 룬이 빛나는 날)
    guard = []
    for sg in (1, -1):
        def xs(a, b):
            return (min(sg * a, sg * b), max(sg * a, sg * b))
        x0, x1 = xs(2.4, 8.0)
        guard.append(Box((x0, -0.9, 2.8), (x1, 0.9, 4.4), GOLD))
        x0, x1 = xs(7.0, 9.0)
        guard.append(Box((x0, -0.7, 3.0), (x1, 0.7, 7.4), GOLD))
        x0, x1 = xs(7.6, 8.6)
        guard.append(Box((x0, -0.4, 7.4), (x1, 0.4, 9.0), GLOW, glow=True))
    part("sword_hilt", [
        Box((-0.9, -0.9, -5.0), (0.9, 0.9, 2.6), LEATHER),
        *rbox((-1.5, -1.5, -7.2), (1.5, 1.5, -5.0), GOLD, r=0.5),
        Box((-0.8, -0.8, -7.9), (0.8, 0.8, -7.2), GLOW, glow=True),
        *rbox((-2.4, -1.4, 2.6), (2.4, 1.4, 4.6), GOLD, r=0.5),
        Box((-1.0, -1.45, 3.2), (1.0, 1.45, 4.2), GLOW_W, glow=True),
        *guard,
    ])
    part("sword_blade", [
        Box((-1.8, -0.55, 0), (1.8, 0.55, 22.0), STEEL),
        Box((-0.55, -0.62, 0.6), (0.55, 0.62, 21.0), GLOW, {"up": runes, "down": runes}, glow=True),
        Box((-1.95, -0.3, 0), (-1.6, 0.3, 22.0), GLOW_W, glow=True),
        Box((1.6, -0.3, 0), (1.95, 0.3, 22.0), GLOW_W, glow=True),
        Box((-1.1, -0.45, 22.0), (1.1, 0.45, 23.2), STEEL),
        Box((-0.4, -0.35, 23.2), (0.4, 0.35, 24.0), GLOW_W, glow=True),
    ])
    bone("sword_hilt", "hand_r", (0, -2.4, 0.4), "sword_hilt", rest=(-70, 0, 0))
    bone("sword_blade", "sword_hilt", (0, 0, 4.6), "sword_blade")

    # ═══ 정의의 저울 (왼손)
    part("scales", [
        Box((-0.5, -2.0, -0.5), (0.5, 3.0, 0.5), GOLD),
        *rbox((-1.4, 3.0, -1.4), (1.4, 5.8, 1.4), GOLD, r=0.6),
        Box((-1.0, 3.4, -1.0), (1.0, 5.4, 1.0), GLOW_W, glow=True),
        Box((-9.0, -2.0, -0.55), (9.0, -1.0, 0.55), GOLD_B),
        Box((-9.6, -2.4, -0.8), (-8.4, -0.6, 0.8), GOLD), Box((8.4, -2.4, -0.8), (9.6, -0.6, 0.8), GOLD),
        Box((-0.8, -3.0, -0.8), (0.8, -2.0, 0.8), GLOW, glow=True),
    ])
    bone("scales", "hand_l", (0, -4.0, 0.6), "scales", rest=(30, 0, 0))
    for s, sg in (("l", 1), ("r", -1)):
        n = part("pan_" + s, [
            Box((-0.2, -7.0, -0.2), (0.2, 0.0, 0.2), GOLD),
            Box((-3.0, -7.4, -0.15), (3.0, -7.0, 0.15), GOLD), Box((-0.15, -7.4, -3.0), (0.15, -7.0, 3.0), GOLD),
            *rbox((-3.6, -8.6, -3.6), (3.6, -7.4, 3.6), GOLD, r=0.4),
            Box((-2.6, -7.6, -2.6), (2.6, -7.3, 2.6), GLOW, glow=True),
        ])
        bone(n, "scales", (sg * 9.0, -1.6, 0), n)

    # ═══ 날개 (위 큰 날개 3마디 + 첫째깃 6 / 아래 작은 날개 2마디 + 첫째깃 4)
    def seg_part(name, sg, L, drop1, drop2, bar=1.6):
        x0, x1 = (0.0, L) if sg > 0 else (-L, 0.0)
        return part(name, [
            *rbox((x0, -bar, -1.2), (x1, bar, 1.2), OBSID, r=0.5),
            Box((x0, bar - 0.4, -1.3), (x1, bar + 0.4, 1.3), GOLD),
            Box((x0, -drop1, -0.7), (x1, -bar + 0.2, 0.7), FEATHER_C),
            Box((x0, -drop2, -0.45), (x1, -drop1 + 0.4, 0.45), FEATHER, {"north": tatter, "south": tatter}),
        ])

    def feather_part(name, sg, L, w=3.6):
        x0, x1 = (0.0, L) if sg > 0 else (-L, 0.0)
        tip = (x1 - 2.6, x1) if sg > 0 else (x0, x0 + 2.6)
        fn = {"north": taper, "south": taper} if sg > 0 else {"north": taper, "south": taper}
        return part(name, [
            Box((x0, -w / 2, -0.35), (x1, w / 2, 0.35), FEATHER_P, fn),
            Box((x0, -0.25, -0.42), (x1, 0.25, 0.42), OBSID),
            Box((tip[0], -0.6, -0.45), (tip[1], 0.6, 0.45), GLOW, glow=True),
        ])

    for s, sg in (("l", 1), ("r", -1)):
        # 위 날개
        seg_part(f"wu0_{s}", sg, 15.0, 8.0, 15.0)
        seg_part(f"wu1_{s}", sg, 14.0, 9.0, 20.0)
        seg_part(f"wu2_{s}", sg, 9.0, 6.0, 12.0, bar=1.3)
        bone(f"wu0_{s}", "chest", (sg * 3.0, 9.6, -5.6), f"wu0_{s}", rest=(0, sg * 24, sg * 34))
        bone(f"wu1_{s}", f"wu0_{s}", (sg * 14.4, 0, 0), f"wu1_{s}", rest=(0, sg * 8, sg * 10))
        bone(f"wu2_{s}", f"wu1_{s}", (sg * 13.4, 0, 0), f"wu2_{s}", rest=(0, sg * 6, -sg * 22))
        for k in range(6):
            n = feather_part(f"wp{k}_{s}", sg, 22.0 - k * 1.6)
            bone(n, f"wu2_{s}", (sg * (8.6 - k * 1.3), -0.6, 0.1 * k), n, rest=(0, sg * k * 2, sg * (6 - k * 13)))
        # 아래 날개
        seg_part(f"wl0_{s}", sg, 11.0, 6.0, 11.0, bar=1.3)
        seg_part(f"wl1_{s}", sg, 10.0, 6.0, 13.0, bar=1.1)
        bone(f"wl0_{s}", "chest", (sg * 2.6, 3.4, -5.2), f"wl0_{s}", rest=(0, sg * 30, -sg * 18))
        bone(f"wl1_{s}", f"wl0_{s}", (sg * 10.6, 0, 0), f"wl1_{s}", rest=(0, sg * 6, -sg * 16))
        for k in range(4):
            n = feather_part(f"wq{k}_{s}", sg, 16.0 - k * 1.8, w=3.0)
            bone(n, f"wl1_{s}", (sg * (9.4 - k * 1.6), -0.4, 0.1 * k), n, rest=(0, sg * k * 2, -sg * (10 + k * 12)))

    # ═══ 떠다니는 수정 조각 4개
    for k in range(4):
        n = part(f"shard{k}", [
            Box((-1.2, -1.2, -1.2), (1.2, 1.2, 1.2), CRYSTAL, glow=True),
            Box((-0.8, 1.2, -0.8), (0.8, 3.4, 0.8), CRYSTAL, glow=True),
            Box((-0.8, -3.4, -0.8), (0.8, -1.2, 0.8), CRYSTAL, glow=True),
            Box((-0.4, 3.4, -0.4), (0.4, 4.6, 0.4), GLOW_W, glow=True),
            Box((-0.4, -4.6, -0.4), (0.4, -3.4, 0.4), GLOW_W, glow=True),
        ], glow=True)
        ang = 45 + k * 90
        rr = 20.0
        bone(n, "core", (rr * np.sin(np.radians(ang)), 6.0 + (k % 2) * 8.0, rr * np.cos(np.radians(ang))), n, rest=(0, ang, 20))

    parts = list(P.values())
    R = Rig("nemesis", 2.4)
    for (name, parent, off, pk, rest) in B:
        R.bone(name, parent, off, P[pk] if pk else None, rest=rest)
    return R, parts, anims()


# ─────────────────────────────────────────────────────────────────────────────
#  포즈 도우미
# ─────────────────────────────────────────────────────────────────────────────
def P_(*ds, **kw):
    out = {}
    for d in ds:
        out.update(d)
    out.update(kw)
    return out


def wings(spread=0.0, flap=0.0, back=0.0, fan=0.0):
    """위 날개 spread(펼침 +)/flap(위아래)/back(뒤로 젖힘) · fan(첫째깃 부채꼴 +) · 아래 날개는 따라 움직임"""
    d = {}
    for s, sg in (("l", 1), ("r", -1)):
        d[f"wu0_{s}"] = (0, sg * (back - spread * 0.3), sg * (flap + spread))
        d[f"wu1_{s}"] = (0, sg * (back * 0.3), sg * (flap * 0.6 + spread * 0.6))
        d[f"wu2_{s}"] = (0, 0, sg * (flap * 0.4 + spread * 0.5))
        for k in range(6):
            d[f"wp{k}_{s}"] = (0, 0, -sg * fan * (k - 2.5) * 0.6)
        d[f"wl0_{s}"] = (0, sg * (back * 0.6 - spread * 0.2), sg * (-flap * 0.5 - spread * 0.6))
        d[f"wl1_{s}"] = (0, 0, sg * (-flap * 0.3 - spread * 0.3))
        for k in range(4):
            d[f"wq{k}_{s}"] = (0, 0, sg * fan * (k - 1.5) * 0.5)
    return d


def fold():
    """날개를 몸 쪽으로 접음 (등장 직전 · 쓰러질 때)"""
    d = {}
    for s, sg in (("l", 1), ("r", -1)):
        d[f"wu0_{s}"] = (0, sg * 70, -sg * 40)
        d[f"wu1_{s}"] = (0, sg * 60, -sg * 30)
        d[f"wu2_{s}"] = (0, sg * 40, -sg * 10)
        for k in range(6):
            d[f"wp{k}_{s}"] = (0, 0, sg * (k * 12 - 10))
        d[f"wl0_{s}"] = (0, sg * 60, sg * 20)
        d[f"wl1_{s}"] = (0, sg * 50, sg * 10)
    return d


def robe(t, amp=1.0, lift=0.0, back=0.0):
    """옷자락 흔들림 · lift(전체가 바깥으로 펄럭) · back(뒤쪽 자락이 뒤로 휘날림)"""
    d = {}
    for k in range(8):
        rear = max(0.0, -np.cos(np.radians(k * 45)))
        d[f"robe{k}_0"] = (-lift - back * rear + amp * 3 * np.sin(t + k * 0.8), 0, 0)
        d[f"robe{k}_1"] = (-lift * 0.6 - back * rear * 0.6 + amp * 5 * np.sin(t * 1.3 + k * 1.1), 0, 0)
    return d


def hair(t, amp=1.0, back=0.0):
    d = {}
    for k in range(5):
        d[f"hair{k}_0"] = (back + amp * 4 * np.sin(t + k * 0.9), 0, amp * 3 * np.sin(t * 0.8 + k))
        d[f"hair{k}_1"] = (back * 0.6 + amp * 6 * np.sin(t * 1.2 + k * 1.3), 0, 0)
    return d


def shards(t, amp=1.0):
    d = {}
    for k in range(4):
        d[f"shard{k}@t"] = (0, amp * 2.2 * np.sin(t + k * 1.6), 0)
        d[f"shard{k}"] = (0, 18 * np.sin(t * 0.5 + k), 10 * np.sin(t + k))
    return d


def pans(t, amp=1.0):
    return {"pan_l": (amp * 7 * np.sin(t), 0, amp * 5 * np.sin(t + 1)), "pan_r": (amp * 7 * np.sin(t + 2), 0, amp * 5 * np.sin(t + 3))}


def halo(t, amp=1.0):
    return {"halo_o": (0, 0, amp * 8 * np.sin(t)), "halo_i": (0, 0, -amp * 14 * np.sin(t + 0.6))}


SW_REST = (42, 0, 0)          # 칼끝이 앞 · 위로


def anims():
    A = {}
    idle = []
    for i in range(4):
        ph = i / 4 * 2 * np.pi
        idle.append((P_(wings(6 + 4 * np.sin(ph), 8 * np.sin(ph), 0, 2 * np.sin(ph)), robe(ph), hair(ph), shards(ph), pans(ph), halo(ph),
                        abdomen=(2 + np.sin(ph), 0, 0), chest=(1.5 * np.sin(ph + 1), 0, 0), head=(-1.5 * np.sin(ph), 0, 0),
                        arm_l=(0, 0, 4), arm_r=(0, 0, -4), sword_hilt=SW_REST, _root=(0, 1.2 * np.sin(ph), 0)), 12))
    A["idle"] = dict(loop=True, keys=idle)
    glide = []
    for i in range(4):
        ph = i / 4 * 2 * np.pi
        glide.append((P_(wings(14, 12 * np.sin(ph), 22, 6), robe(ph * 2, 1.6, 6, 26), hair(ph * 2, 1.4, 40), shards(ph, 1.4), pans(ph, 1.8), halo(ph),
                         core=(14, 0, 0), abdomen=(6, 0, 0), chest=(6, 0, 0), head=(-18, 0, 0),
                         arm_l=(20, 0, 10), arm_r=(30, 0, -12), fore_r=(10, 0, 0), sword_hilt=(-126, -30, 0), _root=(0, 0.8 * np.sin(ph), 0)), 5))
    A["glide"] = dict(loop=True, keys=glide)
    A["slash"] = dict(loop=False, keys=[
        (P_(wings(22, 22, 0, 10), robe(0, 1.2, 8), hair(0, 1.2, 10), shards(0, 1.2), pans(0, 1.6), halo(0, 2),
            arm_r=(-170, 0, -20), fore_r=(-40, 0, 0), chest=(-10, 26, 0), abdomen=(-4, 10, 0), head=(4, -18, 0),
            arm_l=(-30, 0, 30), sword_hilt=(-150, -90, 0), _root=(0, 1.6, -1.0)), 8),
        (P_(wings(4, -26, 16, 2), robe(1, 1.8, 30), hair(1, 1.6, 34), shards(1, 1.6), pans(1, 2.2), halo(1, 2),
            arm_r=(-24, 0, 26), fore_r=(-14, 0, 0), chest=(16, -32, 0), abdomen=(8, -12, 0), head=(8, 20, 0),
            arm_l=(10, 0, 20), sword_hilt=(-162, -90, 0), _root=(0, -1.0, 2.0)), 3),
        (P_(wings(4, -20, 14, 2), robe(2, 1.4, 22), hair(2, 1.3, 24), shards(2, 1.2), pans(2, 1.8), halo(2, 1.5),
            arm_r=(-18, 0, 22), fore_r=(-12, 0, 0), chest=(14, -26, 0), abdomen=(7, -10, 0), head=(6, 16, 0),
            arm_l=(8, 0, 16), sword_hilt=(132, 78, 0), _root=(0, -1.0, 2.0)), 6),
        (P_(wings(6, 0, 0, 0), robe(3), hair(3), shards(3), pans(3), halo(3), arm_l=(0, 0, 4), arm_r=(0, 0, -4), sword_hilt=SW_REST), 9),
    ])
    A["rise"] = dict(loop=False, keys=[
        (P_(fold(), robe(0, 0.3, -6), hair(0, 0.3, 10), shards(0, 0.4), pans(0, 0.3), halo(0, 0),
            core=(18, 0, 0), abdomen=(10, 0, 0), chest=(14, 0, 0), head=(30, 0, 0), arm_l=(30, 0, 30), arm_r=(30, 0, -30),
            fore_l=(-60, 0, 0), fore_r=(-60, 0, 0), sword_hilt=(150, 30, 0), _root=(0, -6.0, 0)), 1),
        (P_(fold(), robe(0.5, 0.4, -6), hair(0.5, 0.3, 10), shards(0.5, 0.6), pans(0.5, 0.3), halo(0.5, 0.5),
            core=(16, 0, 0), abdomen=(10, 0, 0), chest=(12, 0, 0), head=(26, 0, 0), arm_l=(30, 0, 30), arm_r=(30, 0, -30),
            fore_l=(-60, 0, 0), fore_r=(-60, 0, 0), sword_hilt=(150, 48, 0), _root=(0, -4.0, 0)), 24),
        (P_(wings(34, 30, -10, 14), robe(1, 2.0, 30), hair(1, 1.6, 40), shards(1, 2.0), pans(1, 2.0), halo(1, 2),
            core=(-8, 0, 0), chest=(-12, 0, 0), head=(-20, 0, 0), arm_l=(-40, 0, 60), arm_r=(-40, 0, -60),
            fore_l=(-20, 0, 0), fore_r=(-20, 0, 0), sword_hilt=(102, -18, 0), _root=(0, 4.0, 0)), 12),
        (P_(wings(30, 24, -6, 12), robe(2, 1.6, 22), hair(2, 1.4, 30), shards(2, 1.6), pans(2, 1.6), halo(2, 1.5),
            core=(-6, 0, 0), chest=(-10, 0, 0), head=(-16, 0, 0), arm_l=(-30, 0, 56), arm_r=(-150, 0, -10),
            fore_l=(-20, 0, 0), fore_r=(-10, 0, 0), sword_hilt=(-180, -60, 0), _root=(0, 3.0, 0)), 16),
        (P_(wings(6, 0, 0, 0), robe(3), hair(3), shards(3), pans(3), halo(3), arm_l=(0, 0, 4), arm_r=(0, 0, -4), sword_hilt=SW_REST), 12),
    ])
    A["death"] = dict(loop=False, keys=[
        (P_(wings(-10, -30, 14, -6), robe(0, 0.6, -8), hair(0, 0.6, -10), shards(0, 0.2), pans(0, 0.4), halo(0, 0),
            core=(10, 0, 0), chest=(26, 0, 10), head=(34, 0, 14), arm_l=(30, 0, 30), arm_r=(30, 0, -30), sword_hilt=(150, 0, 0), _root=(0, -5.0, 0)), 14),
        (P_(fold(), robe(0, 0.2, -12), hair(0, 0.2, -20), shards(0, 0.1), pans(0, 0.2), halo(0, 0),
            core=(40, 0, 0), chest=(50, 0, 12), head=(40, 0, 20), arm_l=(50, 0, 40), arm_r=(50, 0, -40), sword_hilt=(170, 0, 0), _root=(0, -16.0, -2.0)), 22),
    ])
    return A


INFO = dict(hitbox="wither_skeleton", hit_scale=2.0, portrait=dict(bone="head", dist=1.6, cy=4.6, cz=3.6))
