"""전설 무기 8종 — 고퀄 판타지 (생물 장식 · 날개막 · 눈 · 가시 · 줄무늬) 128px"""
import math

import numpy as np
from PIL import Image
from scipy import ndimage

from icon2d import *
from icon2d import S, XX, YY, U, V

ICE = Mat((140, 210, 255), spec=1.0, shin=70, env=0.5, rough=0.03, glow=(120, 200, 255), sky=(230, 250, 255), ground=(30, 70, 140))
BLUEWING = Mat((70, 150, 255), spec=0.5, shin=30, rough=0.02, glow=(90, 170, 255))
RED = Mat((200, 30, 40), spec=0.6, shin=30, env=0.2, rough=0.05, sky=(255, 140, 140), ground=(60, 0, 6))
REDWING = Mat((210, 40, 40), spec=0.3, shin=16, rough=0.02)
BONE = Mat((232, 222, 196), spec=0.35, shin=20, grain="stone", rough=0.12)
MANTIS = Mat((120, 200, 60), spec=0.6, shin=30, env=0.25, rough=0.04, sky=(220, 255, 180), ground=(20, 60, 10))
MANTIS_D = Mat((60, 120, 30), spec=0.5, shin=30, env=0.2, rough=0.05)
LEAF = Mat((150, 220, 80), spec=0.3, shin=16, rough=0.03, glow=(170, 255, 90))
FEATHER_O = Mat((255, 140, 40), spec=0.2, shin=10, grain="fur", rough=0.2)
FEATHER_R = Mat((220, 40, 30), spec=0.2, shin=10, grain="fur", rough=0.2)
OBSIDIAN = Mat((40, 30, 44), spec=0.9, shin=60, env=0.4, rough=0.05, sky=(130, 110, 150), ground=(10, 6, 12))
EYE_W = Mat((250, 240, 230), spec=0.8, shin=60, rough=0.02)
IRIS = Mat((230, 30, 30), spec=1.0, shin=80, rough=0.02, glow=(255, 40, 40))
WASP_Y = Mat((250, 200, 30), spec=0.8, shin=50, env=0.3, rough=0.03, sky=(255, 245, 190), ground=(120, 70, 0))
WASP_K = Mat((34, 26, 20), spec=0.8, shin=50, env=0.3, rough=0.03)
GLASSWING = Mat((210, 230, 240), spec=0.6, shin=40, rough=0.01)
CRYSTAL = Mat((180, 90, 255), spec=1.0, shin=90, env=0.4, rough=0.02, glow=(190, 110, 255), sky=(245, 220, 255), ground=(50, 10, 90))
BLOOD = Mat((170, 16, 30), spec=0.9, shin=60, env=0.4, rough=0.03, sky=(255, 150, 150), ground=(40, 0, 6))


def veins(pts_list, w=3.2):
    d = np.zeros((S, S), np.float32)
    for pts in pts_list:
        d = np.maximum(d, line_dens(pts, w))
    return d


def spikes(c, u0, u1, v, side, n, mat, seed, h=16, w=7):
    for k in range(n):
        u = u0 + (u1 - u0) * (k + 0.5) / n
        c.part(poly([(u - w, v), (u + w, v), (u + w * 0.6, v + side * h)]), mat, seed + k, shape="blade", height=0.9)


def thunder():
    """창공 나비검 — 얼음빛 결정 날 + 나비 날개 가드"""
    c = Canvas()
    for s_, (a, b) in ((1, (0, 1)), (-1, (0, 1))):
        wing1 = smooth_poly([(190, s_ * 10), (150, s_ * 40), (120, s_ * 88), (150, s_ * 110), (200, s_ * 96), (222, s_ * 50)], 12)
        wing2 = smooth_poly([(200, s_ * 10), (230, s_ * 50), (262, s_ * 92), (290, s_ * 80), (270, s_ * 40), (230, s_ * 12)], 12)
        c.part(wing1, BLUEWING, 10 + s_, shape="flat", bevel=10, alpha=0.9)
        c.part(wing2, BLUEWING, 12 + s_, shape="flat", bevel=10, alpha=0.9)
        c.part(veins([[(200, s_ * 12), (150, s_ * 90)], [(200, s_ * 12), (190, s_ * 96)], [(200, s_ * 12), (140, s_ * 60)],
                     [(210, s_ * 12), (270, s_ * 76)], [(210, s_ * 12), (245, s_ * 60)]], 1.8) > 0.4, Mat((10, 20, 60), spec=0.2, shin=10), 900, shape="flat", bevel=1, outline=0)
        for (uu, vv) in ((150, 90), (175, 98), (262, 78)):
            c.part(disc(uu, s_ * vv, 5), Mat((250, 250, 255), spec=0.5, shin=20), 20 + uu, bevel=3)
    c.part(disc(52, 0, 14), SAPPHIRE, 1, bevel=10)
    c.part(profile([(64, 8), (180, 9)]), Mat((40, 50, 80), spec=0.5, shin=30, grain="leather", rough=0.2), 2, bevel=6)
    for u in range(70, 180, 14):
        c.part(profile([(u, 10), (u + 5, 10)]), STEEL, 30 + u, bevel=3)
    c.part(disc(198, 0, 16), STEEL, 3, bevel=10)
    c.part(disc(198, 0, 9), SAPPHIRE, 4, bevel=6)
    blade = profile([(214, 12), (250, 15), (430, 11), (500, 7), (536, 0.5)])
    c.part(blade, ICE, 5, shape="blade", height=1.1, ang=AX_ANG)
    for k in range(6):
        u = 250 + k * 45
        c.ink(line_dens([(u, -12), (u + 18, 0), (u, 12)], 1.4), (40, 90, 170), 0.6)
    c.emissive(line_dens([(220, 0), (520, 0)], 2.2), (180, 230, 255), 1.4)
    return c


def dragon():
    """홍룡 도끼 — 용 날개막 도끼날 + 뼈 가시 + 빛나는 용의 눈"""
    c = Canvas()
    c.part(profile([(6, 8), (20, 11), (420, 11)]), OBSIDIAN, 1, bevel=8, ang=AX_ANG)
    spikes(c, 40, 320, 11, 1, 7, BONE, 50, h=14, w=6)
    spikes(c, 60, 300, -11, -1, 6, BONE, 60, h=12, w=6)
    memb = smooth_poly([(330, -10), (300, -70), (330, -130), (380, -150), (430, -140), (470, -110), (455, -60), (440, -10)], 14)
    c.part(memb, REDWING, 10, shape="flat", bevel=12, alpha=0.92, ang=AX_ANG + 90)
    c.part(veins([[(380, -12), (320, -120)], [(390, -12), (372, -146)], [(400, -12), (428, -138)], [(410, -12), (462, -100)]], 3.0) > 0.4, Mat((60, 6, 10), spec=0.2, shin=10), 900, shape="flat", bevel=1, outline=0)
    for (a, b) in (((380, -12), (320, -120)), ((390, -12), (372, -146)), ((400, -12), (428, -138)), ((410, -12), (462, -100))):
        c.part(line_dens([a, b], 7) > 0.5, BONE, 20 + a[0], bevel=3)
    edge = smooth_poly([(300, -70), (330, -130), (380, -150), (430, -140), (470, -110), (480, -120), (440, -158), (380, -168), (318, -146), (288, -80)], 12)
    c.part(edge, STEEL, 30, shape="blade", height=0.7)
    head = smooth_poly([(400, 14), (430, 30), (480, 26), (520, 10), (530, -4), (480, -14), (430, -12)], 10)
    c.part(head, RED, 40, bevel=14)
    c.part(poly([(470, 24), (500, 48), (486, 22)]), BONE, 41, shape="blade", height=1)
    c.part(poly([(450, 26), (470, 50), (462, 24)]), BONE, 42, shape="blade", height=1)
    c.part(disc(486, 4, 8), gem((255, 200, 40)), 43, bevel=5)
    c.part(profile([(424, 14), (440, 14)]), GOLD, 44, bevel=5)
    return c


def wind():
    """사마귀 칼날 — 톱니 초록 곡도 + 잎 지느러미 + 작은 눈"""
    c = Canvas()
    c.part(profile([(40, 9), (180, 10)]), MANTIS_D, 1, bevel=7, ang=AX_ANG)
    for u in range(50, 180, 16):
        c.part(profile([(u, 11), (u + 6, 11)]), MANTIS, 10 + u, bevel=4)
    c.part(disc(40, 0, 13), EMERALD, 2, bevel=8)
    for s_ in (1, -1):
        fin = poly([(210, s_ * 8), (150, s_ * 30), (120, s_ * 70), (165, s_ * 52), (150, s_ * 88), (200, s_ * 50), (215, s_ * 12)])
        c.part(fin, LEAF, 20 + s_, shape="flat", bevel=8, alpha=0.95)
        c.part(veins([[(190, s_ * 10), (170, s_ * 60)], [(195, s_ * 20), (208, s_ * 44)]], 1.6) > 0.4, Mat((30, 70, 10), spec=0.2, shin=10), 900, shape="flat", bevel=1, outline=0)
    blade = smooth_poly([(210, -14), (300, -22), (390, -18), (470, -2), (530, 30), (500, 24), (440, 16), (360, 14), (280, 14), (210, 12)], 12)
    c.part(blade, MANTIS, 30, shape="blade", height=1.0, ang=AX_ANG)
    for k in range(10):
        u = 230 + k * 28
        vv = -20 + (k / 9) * 18
        c.part(poly([(u, vv), (u + 12, vv - 2), (u + 4, vv - 13)]), MANTIS_D, 40 + k, shape="blade", height=1)
    c.part(disc(222, 0, 9), EYE_W, 60, bevel=6)
    c.part(disc(223, 0, 5), gem((40, 200, 60)), 61, bevel=4)
    c.emissive(line_dens([(230, 2), (320, 4), (420, 8), (500, 20)], 2.0), (190, 255, 120), 1.2)
    return c


def phoenix():
    """불사조 황금 망치 — 깃털 장식 금 망치머리 + 루비 태양"""
    c = Canvas()
    c.part(profile([(10, 9), (400, 10)]), Mat((110, 40, 30), spec=0.3, shin=16, grain="wood", rough=0.3), 1, bevel=8, ang=AX_ANG)
    for u in (40, 140, 260, 360):
        c.part(profile([(u - 5, 12), (u + 5, 12)]), GOLD, 2 + u, bevel=4)
    for k, s_ in enumerate((1, -1, 1, -1, 1, -1)):
        base_u = 400 + (k // 2) * 18
        f = smooth_poly([(base_u, s_ * 30), (base_u - 60, s_ * (70 + k * 6)), (base_u - 110 + k * 10, s_ * (80 + k * 4)), (base_u - 40, s_ * 50)], 10)
        c.part(f, FEATHER_O if k % 2 == 0 else FEATHER_R, 20 + k, shape="flat", bevel=10, ang=AX_ANG + 60 * s_)
    head = profile([(380, 58), (470, 58)])
    c.part(head, GOLD, 30, bevel=14)
    for u in (380, 462):
        c.part(profile([(u, 62), (u + 8, 62)]), Mat((200, 60, 40), spec=0.8, shin=50, env=0.3), 31 + u, bevel=5)
    c.part(profile([(470, 20), (505, 12), (520, 0.5)]), GOLD, 33, shape="blade", height=1)
    c.part(disc(425, 0, 26), RUBY, 34, bevel=18)
    rays = np.zeros((S, S), np.float32)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        rays = np.maximum(rays, line_dens([(425 + math.cos(a) * 30, math.sin(a) * 30), (425 + math.cos(a) * 46, math.sin(a) * 46)], 3.4))
    c.emissive(rays, (255, 200, 80), 1.3)
    return c


def blackiron():
    """심연의 눈 대검 — 톱니 흑요석 날 + 붉은 핏줄 + 가드의 거대한 눈"""
    c = Canvas()
    c.part(disc(40, 0, 14), OBSIDIAN, 1, bevel=9)
    c.part(profile([(52, 10), (150, 11)]), Mat((80, 14, 20), spec=0.3, shin=16, grain="leather", rough=0.2), 2, bevel=6)
    pts = [(190, 30)]
    for k in range(9):
        u = 205 + k * 34
        pts += [(u, 34 - k * 1.4), (u + 17, 24 - k * 1.2)]
    pts += [(510, 12), (540, 0)]
    blade = poly(pts + [(u, -v) for u, v in pts[::-1]])
    c.part(blade, OBSIDIAN, 10, shape="blade", height=1.0, ang=AX_ANG)
    R = rng(4)
    vv = []
    for k in range(7):
        u0 = 220 + k * 40
        vv.append([(u0, 0), (u0 + 20, R.uniform(-18, 18)), (u0 + 34, R.uniform(-24, 24))])
    c.emissive(veins(vv, 2.2) * (blade.astype(np.float32)), (255, 40, 40), 1.3)
    c.emissive(line_dens([(200, 0), (520, 0)], 2.4), (255, 60, 40), 1.2)
    guard = smooth_poly([(150, 0), (160, 50), (140, 86), (170, 76), (200, 40), (212, 0), (200, -40), (170, -76), (140, -86), (160, -50)], 12)
    c.part(guard, OBSIDIAN, 20, bevel=12)
    spikes(c, 150, 200, 60, 1, 2, BLOOD, 30, h=22, w=8)
    spikes(c, 150, 200, -60, -1, 2, BLOOD, 34, h=22, w=8)
    eye = smooth_poly([(152, 0), (170, 28), (190, 30), (208, 0), (190, -30), (170, -28)], 10)
    c.part(eye, EYE_W, 40, bevel=10)
    c.part(disc(180, 0, 18), IRIS, 41, bevel=10)
    c.part(profile([(174, 1), (180, 5), (186, 1)]) & (np.abs(V) < 16), Mat((10, 6, 8), spec=0.2, shin=10), 42, shape="flat", bevel=2, outline=0)
    pupil = (np.abs(U - 180) < 3.5) & (np.abs(V) < 14)
    c.part(pupil, Mat((8, 4, 6), spec=0.2, shin=10), 43, shape="flat", bevel=1, outline=0)
    return c


def tiger():
    """말벌 독침 — 노랑·검정 줄무늬 독침 날 + 투명 날개 + 갈색 손잡이"""
    c = Canvas()
    c.part(profile([(40, 9), (170, 10)]), LEATHER, 1, bevel=6, ang=AX_ANG)
    for u in range(50, 170, 15):
        c.part(profile([(u, 11), (u + 5, 11)]), WASP_K, 2 + u, bevel=3)
    c.part(disc(36, 0, 12), TOPAZ, 3, bevel=8)
    for s_ in (1, -1):
        w1 = smooth_poly([(200, s_ * 12), (150, s_ * 60), (130, s_ * 110), (170, s_ * 118), (220, s_ * 70)], 12)
        w2 = smooth_poly([(210, s_ * 12), (220, s_ * 60), (250, s_ * 96), (280, s_ * 84), (246, s_ * 30)], 12)
        c.part(w1, GLASSWING, 10 + s_, shape="flat", bevel=8, alpha=0.6)
        c.part(w2, GLASSWING, 12 + s_, shape="flat", bevel=8, alpha=0.6)
        c.part(veins([[(205, s_ * 12), (140, s_ * 110)], [(205, s_ * 12), (190, s_ * 100)], [(205, s_ * 40), (160, s_ * 80)],
                     [(215, s_ * 12), (265, s_ * 88)], [(230, s_ * 40), (250, s_ * 70)]], 1.5) > 0.4, Mat((60, 50, 30), spec=0.2, shin=10), 900, shape="flat", bevel=1, outline=0)
    thorax = smooth_poly([(180, 0), (190, 22), (225, 26), (240, 0), (225, -26), (190, -22)], 10)
    c.part(thorax, WASP_K, 20, bevel=14)
    body = profile([(236, 24), (300, 30), (400, 24), (470, 14), (515, 5), (540, 0.5)])
    for k in range(8):
        u0 = 236 + k * 36
        band = body & (U >= u0) & (U < u0 + 36)
        c.part(band, WASP_Y if k % 2 == 0 else WASP_K, 30 + k, bevel=16, ang=AX_ANG + 90)
    c.part(profile([(500, 6), (548, 0.5)]), STEEL, 40, shape="blade", height=1)
    return c


def staff():
    """공허의 수정 지팡이 — 비틀린 흑목 + 보라 수정 다발 + 떠다니는 파편"""
    c = Canvas()
    shaft = profile([(8, 7), (380, 12)])
    c.part(shaft, Mat((60, 36, 50), spec=0.3, shin=16, grain="wood", rough=0.3), 1, bevel=9, ang=AX_ANG, extra_h=np.sin(U * 0.15 + V * 0.3) * 3)
    for u in (60, 180, 300):
        c.part(profile([(u - 5, 14), (u + 5, 14)]), Mat((170, 120, 220), spec=0.8, shin=50, env=0.3), 10 + u, bevel=5)
    for s_ in (1, -1):
        claw = smooth_poly([(370, s_ * 8), (400, s_ * 46), (450, s_ * 60), (470, s_ * 50), (430, s_ * 40), (400, s_ * 12)], 10)
        c.part(claw, OBSIDIAN, 20 + s_, bevel=6)
    c.glow += np.array((180, 90, 255), np.float32)[None, None, :] * ndimage.gaussian_filter(disc(460, 0, 50).astype(np.float32), 20)[..., None] * 1.4
    shards = [((460, 0), 40, 0), ((430, -30), 26, -30), ((430, 30), 26, 30), ((500, -20), 22, -15), ((500, 22), 20, 20)]
    for i, ((u, v), L, tilt) in enumerate(shards):
        a = math.radians(tilt)
        du, dv = math.cos(a), math.sin(a)
        pts = [(u - du * L * 0.2 - dv * 10, v - dv * L * 0.2 + du * 10), (u + du * L, v + dv * L), (u - du * L * 0.2 + dv * 10, v - dv * L * 0.2 - du * 10), (u - du * L * 0.6, v - dv * L * 0.6)]
        c.part(poly(pts), CRYSTAL, 30 + i, shape="blade", height=1.0)
    for (u, v, r) in ((520, 50, 6), (540, -44, 5), (400, 70, 5)):
        c.part(disc(u, v, r), CRYSTAL, 50 + u, bevel=4)
    return c


def peachwood():
    """진홍 낫창 — 붉은 창날 + 휘어진 낫날 + 사슬 + 불꽃 리본"""
    c = Canvas()
    c.part(profile([(10, 8), (400, 9)]), OBSIDIAN, 1, bevel=7, ang=AX_ANG)
    for u in range(40, 380, 60):
        c.part(profile([(u, 11), (u + 8, 11)]), BLOOD, 2 + u, bevel=4)
    scythe = smooth_poly([(400, -10), (380, -60), (330, -110), (270, -130), (300, -104), (350, -64), (380, -20)], 12)
    c.part(scythe, BLOOD, 30, shape="blade", height=0.8)
    c.emissive(line_dens([(392, -24), (372, -62), (330, -100), (290, -118)], 2.4), (255, 80, 60), 1.2)
    head = profile([(400, 16), (430, 20), (480, 14), (520, 6), (548, 0.5)])
    c.part(head, BLOOD, 40, shape="blade", height=1.1, ang=AX_ANG)
    c.part(profile([(390, 18), (410, 18)]), GOLD, 41, bevel=6)
    c.part(disc(400, 0, 9), RUBY, 42, bevel=6)
    for s_ in (1,):
        rib = smooth_poly([(390, s_ * 16), (350, s_ * 50), (300, s_ * 76), (270, s_ * 70), (320, s_ * 44), (370, s_ * 18)], 10)
        c.part(rib, Mat((255, 110, 40), spec=0.2, shin=10, grain="cloth", rough=0.2, glow=(255, 120, 40)), 50, shape="flat", bevel=8)
    return c


WEAPONS = {"thunder": thunder, "dragon": dragon, "wind": wind, "phoenix": phoenix,
           "blackiron": blackiron, "tiger": tiger, "staff": staff, "peachwood": peachwood}


def paint(wid, out=128):
    return WEAPONS[wid]().image(out=out, glow_strength=0.9)


ART = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))), "art", "weapons")


WFX_OF = {"thunder": "wfx_thunder", "dragon": "wfx_crescent", "wind": "wfx_wind", "phoenix": "wfx_barrier",
          "blackiron": "wfx_blood", "tiger": "wfx_claw", "staff": "wfx_staff", "peachwood": "wfx_fire"}


def export(pack):
    import os
    for wid in WEAPONS:
        f = os.path.join(ART, f"{wid}.png")
        img = Image.open(f).convert("RGBA") if os.path.exists(f) else paint(wid)     # 직접 그린 그림 우선
        ref = pack.texture(f"weapon/{wid}", img)
        # 스킬 효과: 직접 그린 빛 효과 (skillfx) — 바닥 마법진 (tele/wfx_* 덮어씀) + 솟아오르는 세로 효과
        import skillfx
        pack.texture(f"tele/{WFX_OF[wid]}", skillfx.ground(wid))
        r2 = pack.texture(f"skillart/{wid}", skillfx.burst(wid))
        pack.item_model(f"fx/{wid}", {"textures": {"0": r2, "particle": r2}, "elements": [{
            "from": [0, -8, 8], "to": [16, 24, 8], "shade": False, "light_emission": 15,
            "faces": {"north": {"uv": [16, 0, 0, 16], "texture": "#0"}, "south": {"uv": [0, 0, 16, 16], "texture": "#0"}}}]})
        pack.item_model(f"weapon/{wid}", {"parent": "minecraft:item/handheld", "textures": {"layer0": ref}})
    # 추가 8종 + 보스 전용 4종 (직접 그린 그림이 있으면 그걸 씀)
    import weapons_legend2
    for wid in weapons_legend2.WEAPONS2:
        f = os.path.join(ART, f"{wid}.png")
        img = Image.open(f).convert("RGBA") if os.path.exists(f) else weapons_legend2.paint(wid)
        ref = pack.texture(f"weapon/{wid}", img)
        pack.item_model(f"weapon/{wid}", {"parent": "minecraft:item/handheld", "textures": {"layer0": ref}})


def preview(path):
    ims = [paint(w, 256) for w in WEAPONS]
    W = Image.new("RGBA", (4 * 272 + 16, 2 * 272 + 16), (128, 128, 128, 255))
    for i, im in enumerate(ims):
        x, y = 16 + (i % 4) * 272, 16 + (i // 4) * 272
        W.paste(Image.new("RGBA", (256, 256), (139, 139, 139, 255)), (x, y))
        W.alpha_composite(im, (x, y))
    W.convert("RGB").save(path)
