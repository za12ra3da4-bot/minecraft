"""상점 전설 무기 4종 — 3D 아이템 모델 (손잡이 = 모델 원점, 날은 위로)"""
from modelkit import *

GOLD = Mat((240, 192, 72), var=0.05, edge_dark=0.36, top_light=0.35, pattern=metal((168, 108, 28), 0.35, 0.0))
SILVER = Mat((214, 222, 232), var=0.04, edge_dark=0.32, top_light=0.4, pattern=metal((130, 140, 160), 0.4, 0.0))
IRON_D = Mat((58, 56, 64), var=0.05, edge_dark=0.3, top_light=0.25, pattern=metal((30, 28, 34), 0.3, 0.0))
CRIMSON = Mat((168, 24, 30), var=0.05, edge_dark=0.34, top_light=0.3, pattern=metal((90, 10, 14), 0.3, 0.0))
LEATHER = Mat((70, 40, 26), var=0.06, edge_dark=0.3, top_light=0.2, pattern=stripes((70, 40, 26), (48, 26, 16), 1, vertical=False))
TEAL = Mat((40, 150, 150), var=0.05, edge_dark=0.3, top_light=0.25, pattern=stripes((40, 150, 150), (24, 100, 104), 1, vertical=False))
WOOD = Mat((74, 46, 30), var=0.05, edge_dark=0.3, top_light=0.2, pattern=stripes((74, 46, 30), (54, 32, 20), 1))
FEATHER = Mat((246, 246, 240), var=0.04, edge_dark=0.28, top_light=0.2, pattern=stripes((246, 246, 240), (196, 204, 214), 1))
G_BLUE = Mat((150, 225, 255), var=0.04, edge_dark=0.0, top_light=0.0)
G_RED = Mat((255, 90, 60), var=0.04, edge_dark=0.0, top_light=0.0)
G_TEAL = Mat((120, 255, 220), var=0.04, edge_dark=0.0, top_light=0.0)
G_GOLD = Mat((255, 236, 150), var=0.04, edge_dark=0.0, top_light=0.0)


def mirror(boxes):
    out = []
    for b in boxes:
        out.append(Box((-b.to[0], b.frm[1], b.frm[2]), (-b.frm[0], b.to[1], b.to[2]), b.mat, glow=not b.shade))
    return boxes + out


def zeus():
    """제우스의 뇌전검: 금빛 날 + 푸른 번개 심, 번개 날개 가드"""
    b = [Box((-1.7, 4, -0.45), (1.7, 19, 0.45), GOLD), Box((-1.1, 19, -0.4), (1.1, 21, 0.4), GOLD),
         Box((-0.5, 21, -0.3), (0.5, 23, 0.3), GOLD),
         Box((-0.55, 5, -0.6), (0.55, 20, 0.6), G_BLUE, glow=True)]
    for k in range(3):                                   # 번개 지그재그 새김
        y = 7 + k * 4
        b += [Box((-1.3, y, -0.55), (-0.3, y + 1.2, 0.55), G_BLUE, glow=True), Box((0.3, y + 1.8, -0.55), (1.3, y + 3, 0.55), G_BLUE, glow=True)]
    b += mirror([Box((1.2, 2.4, -1.0), (5.2, 4.0, 1.0), GOLD), Box((4.4, 3.2, -0.7), (6.4, 6.0, 0.7), GOLD),
                 Box((5.6, 5.4, -0.5), (6.8, 7.4, 0.5), G_BLUE, glow=True), Box((2.0, 2.9, -1.1), (3.8, 3.5, 1.1), G_BLUE, glow=True)])
    b += [Box((-1.4, 2.2, -1.2), (1.4, 4.2, 1.2), GOLD), Box((-0.7, 2.6, -1.3), (0.7, 3.8, 1.3), G_BLUE, glow=True)]
    b += [Box((-0.7, -4, -0.7), (0.7, 2.2, 0.7), LEATHER), Box((-0.85, -1.2, -0.85), (0.85, -0.6, 0.85), GOLD), Box((-0.85, 1.0, -0.85), (0.85, 1.6, 0.85), GOLD)]
    b += rbox((-1.4, -6.4, -1.4), (1.4, -4, 1.4), GOLD, r=0.5) + [Box((-0.7, -5.8, -1.5), (0.7, -4.6, 1.5), G_BLUE, glow=True)]
    return b


def ares():
    """아레스의 전쟁도끼: 검붉은 양날 도끼, 불타는 룬"""
    b = [Box((-0.7, -9, -0.7), (0.7, 17, 0.7), WOOD)]
    for y in (-8.4, -3, 4, 10):
        b.append(Box((-0.85, y, -0.85), (0.85, y + 0.8, 0.85), IRON_D))
    b += [Box((-1.6, 11, -1.1), (1.6, 18, 1.1), IRON_D), Box((-0.5, 18, -0.5), (0.5, 22.5, 0.5), IRON_D)]
    wing = []
    for i, (x0, x1, y0, y1) in enumerate(((1.6, 3.6, 11.5, 17.5), (3.6, 5.6, 10.5, 18.5), (5.6, 7.2, 9.5, 19.5), (7.2, 8.4, 9.0, 20.2))):
        wing.append(Box((x0, y0, -0.55), (x1, y1, 0.55), CRIMSON if i < 3 else IRON_D))
    wing += [Box((2.2, 13.8, -0.65), (6.6, 15.2, 0.65), G_RED, glow=True), Box((8.0, 8.6, -0.4), (8.8, 10.2, 0.4), IRON_D),
             Box((8.0, 19.4, -0.4), (8.8, 21.0, 0.4), IRON_D)]
    b += mirror(wing)
    b += [Box((-0.9, -11, -0.9), (0.9, -9, 0.9), IRON_D), Box((-0.4, -11.6, -0.4), (0.4, -11, 0.4), G_RED, glow=True)]
    return b


def hermes():
    """헤르메스의 날개 단검: 은빛 곡선 날 + 날개 가드"""
    b = [Box((-1.2, 3, -0.4), (1.2, 10, 0.4), SILVER), Box((-0.8, 10, -0.35), (1.4, 13, 0.35), SILVER),
         Box((-0.2, 13, -0.3), (1.6, 15, 0.3), SILVER), Box((0.6, 15, -0.25), (1.6, 16.5, 0.25), SILVER),
         Box((-0.35, 4, -0.5), (0.35, 12, 0.5), G_TEAL, glow=True)]
    feath = []
    for k in range(4):
        feath.append(Box((1.2 + k * 1.1, 1.8 + k * 0.7, -0.35), (2.4 + k * 1.1, 3.2 + k * 1.3, 0.35), FEATHER))
    b += mirror(feath)
    b += [Box((-1.4, 1.6, -0.9), (1.4, 3.0, 0.9), SILVER), Box((-0.5, 1.9, -1.0), (0.5, 2.7, 1.0), G_TEAL, glow=True)]
    b += [Box((-0.6, -3.5, -0.6), (0.6, 1.6, 0.6), TEAL), Box((-0.9, -4.6, -0.9), (0.9, -3.5, 0.9), SILVER)]
    return b


def athena():
    """아테나의 지혜의 창: 금빛 잎날 창날 + 부엉이 눈 보석"""
    b = [Box((-0.55, -16, -0.55), (0.55, 13, 0.55), WOOD)]
    for y in (-15, -2, 3, 11):
        b.append(Box((-0.7, y, -0.7), (0.7, y + 0.8, 0.7), GOLD))
    b += [Box((-1.0, 13, -0.8), (1.0, 15, 0.8), GOLD), Box((-2.0, 15, -0.4), (2.0, 18, 0.4), GOLD),
          Box((-1.5, 18, -0.35), (1.5, 20.5, 0.35), GOLD), Box((-0.8, 20.5, -0.3), (0.8, 22.5, 0.3), GOLD),
          Box((-0.3, 22.5, -0.2), (0.3, 23.8, 0.2), GOLD), Box((-0.4, 15.5, -0.5), (0.4, 21.5, 0.5), G_GOLD, glow=True)]
    b += mirror([Box((1.0, 12.4, -0.5), (3.6, 13.4, 0.5), GOLD), Box((3.0, 12.8, -0.4), (3.8, 15.0, 0.4), GOLD)])
    b += rbox((-1.4, 9.4, -1.4), (1.4, 12.2, 1.4), SILVER, r=0.6) + [Box((-0.5, 10.3, -1.5), (0.5, 11.3, 1.5), G_BLUE, glow=True)]
    return b


WEAPONS = {"zeus": zeus, "ares": ares, "hermes": hermes, "athena": athena}
DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, -90, 0], "translation": [0, 1.5, 0.8], "scale": [0.85, 0.85, 0.85]},
    "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [0, 1.5, 0.8], "scale": [0.85, 0.85, 0.85]},
    "firstperson_righthand": {"rotation": [0, -90, 20], "translation": [1.1, 2.2, 1.1], "scale": [0.6, 0.6, 0.6]},
    "firstperson_lefthand": {"rotation": [0, 90, -20], "translation": [1.1, 2.2, 1.1], "scale": [0.6, 0.6, 0.6]},
    "gui": {"rotation": [0, 0, -45], "translation": [0, 0, 0], "scale": [0.42, 0.42, 0.42]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.4, 0.4, 0.4]},
    "fixed": {"rotation": [0, 0, -45], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]},
}


def export(pack):
    out = {}
    for wid, fn in WEAPONS.items():
        boxes = fn()
        part = Part("weapon_" + wid, boxes)
        at = bake_parts([part], tpu=4, atlas_size=128, seed=len(wid) * 17)
        img = at.image()
        ref = pack.texture(f"weapon/{wid}", img)
        js = model_json(part, ref, img.size[0], img.size[1])
        js["display"] = DISPLAY
        pack.item_model(f"weapon/{wid}", js)
        out[wid] = (part, img)
    return out
