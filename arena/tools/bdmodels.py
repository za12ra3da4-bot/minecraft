"""맵 장식 — 전부 블록 디스플레이 조립 (기본 아이템 · 갑옷 거치대 · 현수막 없음)

 모든 모델은 픽셀 단위 (16px = 1블록), 원점 = 장식 좌표.
   석상 · 꽂힌 무기: 원점 = 발밑(땅)       떠 있는 것 · 벽 장식: 원점 = 가운데
 build(model_key, sc, d) → Model  (없으면 None)
"""
import math

import numpy as np

from bdkit import Model, rotate, rot, move, mirror_x

GOLD = "gold_block"
DARK = "black_concrete"

TEAM = {
    "red": dict(wool="red_wool", conc="red_concrete", glass="red_stained_glass", core="shroomlight", deep="red_nether_bricks"),
    "blue": dict(wool="blue_wool", conc="blue_concrete", glass="light_blue_stained_glass", core="sea_lantern", deep="lapis_block"),
    "green": dict(wool="lime_wool", conc="lime_concrete", glass="lime_stained_glass", core="verdant_froglight", deep="green_concrete"),
    "yellow": dict(wool="yellow_wool", conc="yellow_concrete", glass="yellow_stained_glass", core="ochre_froglight", deep="gold_block"),
}


def scale(m, k):
    for p in m.parts:
        p.T = p.T * k
        p.S = p.S * k
    return m


def spin_all(m):
    for p in m.parts:
        p.spin = True
    return m


# ─────────────────────────────────────────────────────────────── 공용 부품
def gem(m, c, w, h, outer, core=None, yaw=45.0, steps=5):
    """다이아몬드 모양 보석: 45° 돌린 상자를 층층이 (가운데 굵고 위아래 뾰족) + 빛나는 속"""
    c = np.asarray(c, float)
    prof = [0.34, 0.72, 1.0, 0.72, 0.34] if steps == 5 else [0.3, 0.62, 0.9, 1.0, 0.8, 0.55, 0.3]
    n = len(prof)
    hh = h / n
    for i, f in enumerate(prof):
        y = c[1] - h / 2 + hh * (i + 0.5)
        m.cbox(outer, (c[0], y, c[2]), (w * f, hh * 1.02, w * f), yaw=yaw)
    if core:
        m.cbox(core, c, (w * 0.42, h * 0.5, w * 0.42), yaw=yaw, glow=True)


def ring(m, block, c, r, t, n=12, tilt=0.0, th=None, glow=False):
    """n 조각 고리 (반지름 r, 굵기 t, 기울기 tilt)"""
    th = t if th is None else th
    seg = 2 * r * math.tan(math.pi / n) * 1.04
    R0 = rot(0, tilt, 0)
    c = np.asarray(c, float)
    for i in range(n):
        a = 360.0 * i / n
        pos = R0 @ np.array([math.sin(math.radians(a)) * r, 0, math.cos(math.radians(a)) * r])
        p = m.cbox(block, (0, 0, 0), (seg, th, t), yaw=a, glow=glow)
        p.R = R0 @ p.R
        p.T = c + pos - p.R @ (p.S / 2)


def kite_shield(m, field, rim, emblem, w=10.0, h=13.0, t=1.0, z=0.0, cy=0.0, emb_block=GOLD):
    """앞(+z)을 보는 연 모양 방패. 가운데 = (0, cy, z)"""
    k0 = m.mark()
    top = h * 0.5
    rows = [(1.0, 0.52), (0.9, 0.14), (0.74, 0.12), (0.52, 0.11), (0.28, 0.11)]
    y = top
    for f, hh in rows:
        H = h * hh
        m.box(field, -w * f / 2, y - H, -t / 2, w * f / 2, y, t / 2)
        m.box(rim, -w * f / 2 - 0.7, y - H - 0.35, -t / 2 - 0.35, w * f / 2 + 0.7, y + 0.35, t / 2 - 0.1)
        y -= H
    # 윗테
    m.box(rim, -w / 2 - 0.8, top - 0.6, -t / 2 - 0.3, w / 2 + 0.8, top + 0.8, t / 2 + 0.3)
    ez = t / 2 + 0.25
    e = emb_block
    if emblem == "cross":
        m.box(e, -0.9, -h * 0.28, ez - 0.4, 0.9, h * 0.36, ez)
        m.box(e, -w * 0.32, h * 0.08, ez - 0.4, w * 0.32, h * 0.2, ez)
    elif emblem == "chevron":
        m.cbox(e, (-w * 0.17, 0.4, ez - 0.2), (w * 0.44, 1.7, 0.4), roll=-38)
        m.cbox(e, (w * 0.17, 0.4, ez - 0.2), (w * 0.44, 1.7, 0.4), roll=38)
        m.cbox(e, (0, h * 0.26, ez - 0.2), (2.2, 2.2, 0.4), roll=45)
    elif emblem == "leaf":
        m.cbox(e, (0, h * 0.06, ez - 0.2), (w * 0.34, w * 0.34, 0.4), roll=45)
        m.box(e, -0.45, -h * 0.3, ez - 0.4, 0.45, h * 0.1, ez)
        m.cbox("lime_concrete" if e == GOLD else GOLD, (0, h * 0.06, ez), (w * 0.16, w * 0.16, 0.4), roll=45)
    elif emblem == "sun":
        for r_ in (0, 45):
            m.cbox(e, (0, h * 0.08, ez - 0.2), (w * 0.52, 1.3, 0.4), roll=r_)
            m.cbox(e, (0, h * 0.08, ez - 0.2), (w * 0.52, 1.3, 0.4), roll=r_ + 90)
        m.cbox(e, (0, h * 0.08, ez), (3.0, 3.0, 0.5), roll=0)
    elif emblem == "crown":
        crown_badge(m, (0, h * 0.06, ez - 0.2), w * 0.55, e)
    move(m.since(k0), (0, cy, z))
    return m.since(k0)


def crown_badge(m, c, w, block):
    x, y, z = c
    m.box(block, x - w / 2, y - w * 0.22, z - 0.2, x + w / 2, y, z + 0.2)
    for i, f in enumerate((-0.5, -0.25, 0, 0.25, 0.5)):
        hh = w * (0.42 if i % 2 == 0 else 0.28)
        px = x + f * (w - 1.0)
        m.box(block, px - 0.5, y, z - 0.2, px + 0.5, y + hh, z + 0.2)


# ─────────────────────────────────────────────────────────────── 기사 석상
KNIGHTS = {
    # 테마: 갑옷 · 보조 갑옷 · 장식 · 망토 · 깃털 · 눈빛 · 무기
    "god_ares": dict(a="polished_blackstone", b="smooth_basalt", g=GOLD, cape="red_wool", plume="orange_wool",
                     eye="ochre_froglight", weapon="greatsword", blade="iron_block", emb="red_concrete"),
    "god_athena": dict(a="iron_block", b="smooth_quartz", g=GOLD, cape="blue_wool", plume="white_wool",
                       eye="sea_lantern", weapon="spear_shield", blade="iron_block", emb="blue_concrete"),
    "god_hermes": dict(a="calcite", b="smooth_quartz", g=GOLD, cape="light_blue_wool", plume="white_wool",
                       eye="pearlescent_froglight", weapon="spear", blade="diamond_block", emb="light_blue_concrete"),
    "god_demeter": dict(a="polished_andesite", b="moss_block", g=GOLD, cape="green_wool", plume="lime_wool",
                        eye="verdant_froglight", weapon="staff", blade="emerald_block", emb="lime_concrete"),
    "hoplite": dict(a="smooth_quartz", b="quartz_bricks", g=GOLD, cape="white_wool", plume="red_wool",
                    eye="ochre_froglight", weapon="greatsword", blade="iron_block", emb="red_concrete"),
    "hoplite_broken": dict(a="stone", b="mossy_cobblestone", g="andesite", cape=None, plume=None,
                           eye=None, weapon="broken", blade="cobblestone", emb="mossy_stone_bricks"),
}


def _arm(m, a, b_, shoulder, elbow, hand, glove=True):
    m.rod(a, shoulder, elbow, 3.0, 3.0)
    m.rod(a, elbow, hand, 2.8, 2.8)
    m.cbox(b_, elbow, (3.4, 2.2, 3.4))
    if glove:
        m.cbox(a, hand, (2.6, 2.6, 2.6))


def knight(kind):
    T = KNIGHTS[kind]
    m = Model()
    A, Bm, G = T["a"], T["b"], T["g"]
    broken = T["weapon"] == "broken"
    # 다리
    for s in (-1, 1):
        x = 2.2 * s
        m.box(A, x - 1.9, 0, -1.9, x + 1.9, 2.3, 2.9)            # 철신
        m.box(G, x - 2.0, 1.9, 2.2, x + 2.0, 2.4, 3.0)             # 발끝 장식
        m.box(A, x - 1.7, 2.3, -1.7, x + 1.7, 10.5, 1.7)          # 정강이
        m.cbox(G, (x, 7.0, 1.85), (3.0, 2.0, 0.8))                 # 무릎
        m.box(Bm, x - 1.85, 10.0, -1.85, x + 1.85, 13.0, 1.85)    # 허벅지
    # 허리 · 치마 갑옷
    m.box(Bm, -4.6, 11.6, -2.6, 4.6, 14.6, 2.6)
    for s in (-1, 1):
        m.cbox(A, (2.4 * s, 11.9, 2.75), (4.2, 4.6, 0.7), pitch=10)
        m.cbox(A, (4.4 * s, 12.1, 0), (0.7, 4.4, 4.8), roll=-8 * s)
    if T["cape"]:
        m.box(T["cape"], -1.7, 7.6, 2.5, 1.7, 14.2, 3.1)           # 앞 휘장 천
        m.box(G, -1.7, 7.2, 2.4, 1.7, 7.8, 3.2)
    m.box(G, -4.8, 14.2, -2.8, 4.8, 15.3, 2.8)                 # 허리띠
    m.cbox(G, (0, 14.75, 2.95), (1.8, 1.8, 0.6))
    # 몸통 · 흉갑
    m.box(A, -4.4, 15.0, -2.4, 4.4, 23.4, 2.4)
    m.cbox(Bm, (0, 19.6, 2.45), (7.8, 6.8, 1.4), pitch=-6)
    m.cbox(A, (0, 17.0, 2.6), (6.4, 1.2, 1.2))
    m.cbox(G, (0, 20.2, 3.25), (1.1, 4.4, 0.5))                # 가슴 십자
    m.cbox(G, (0, 21.0, 3.25), (3.6, 1.1, 0.5))
    m.box(Bm, -3.1, 23.0, -2.1, 3.1, 24.6, 2.1)                # 목가리개
    # 어깨 갑옷
    for s in (-1, 1):
        m.cbox(Bm, (5.7 * s, 22.6, 0), (4.8, 3.2, 5.6), roll=-17 * s)
        m.cbox(A, (6.3 * s, 21.0, 0), (4.2, 1.6, 5.2), roll=-24 * s)
        m.cbox(G, (7.6 * s, 20.6, 0), (1.0, 1.4, 5.8), roll=-24 * s)
    # 투구
    head0 = m.mark()
    m.box(A, -3.2, 24.2, -3.2, 3.2, 30.8, 3.2)
    m.box(Bm, -3.4, 24.2, -3.4, 3.4, 25.2, 3.4)
    m.box(G, -3.45, 29.6, -3.45, 3.45, 30.5, 3.45)
    m.box(G, -0.45, 24.6, 3.15, 0.45, 30.4, 3.6)               # 콧대
    if T["eye"]:
        m.box(DARK, -2.7, 27.2, 3.05, 2.7, 28.2, 3.3)
        for s in (-1, 1):
            m.box(T["eye"], 0.5 * s, 27.35, 3.1, 2.3 * s, 28.05, 3.4, glow=True)
    else:
        m.box(DARK, -2.6, 27.3, 3.1, 2.6, 28.1, 3.35)
    m.box(DARK, -2.4, 25.6, 3.15, 2.4, 26.0, 3.3)                # 숨구멍
    if T["plume"]:
        m.cbox(G, (0, 31.1, 0), (1.6, 1.0, 1.6))
        m.cbox(T["plume"], (0, 32.6, -0.8), (1.3, 3.2, 6.4), pitch=-14)
        m.cbox(T["plume"], (0, 30.2, -4.4), (1.2, 4.2, 2.4), pitch=24)
    head = m.since(head0)
    # 망토
    if T["cape"]:
        m.cbox(T["cape"], (0, 15.8, -3.35), (9.2, 15.0, 0.9), pitch=7)
        m.cbox(T["cape"], (0, 6.2, -4.7), (10.2, 5.0, 0.9), pitch=13)
        m.cbox(G, (0, 3.7, -5.3), (10.4, 0.8, 1.0), pitch=13)
        for s in (-1, 1):
            m.cbox(G, (3.6 * s, 23.2, -2.6), (1.8, 1.8, 1.0))       # 망토 걸쇠
    # 무기 · 팔
    w = T["weapon"]
    sh = {s: np.array([5.3 * s, 21.6, 0.2]) for s in (-1, 1)}
    if w == "greatsword":
        # 칼끝을 땅에 꽂고 두 손을 칼자루 위에
        z = 6.2
        m.rod(T["blade"], (0, 0.2, z), (0, 14.6, z), 2.2, 0.55)
        m.rod(DARK, (0, 1.5, z + 0.05), (0, 13.6, z + 0.05), 0.5, 0.6)          # 피홈
        m.cbox(G, (0, 14.9, z), (8.4, 1.3, 1.5))
        for s in (-1, 1):
            m.cbox(G, (4.4 * s, 15.3, z), (1.5, 1.5, 1.5), yaw=45, pitch=35)
        m.rod("dark_oak_planks", (0, 15.4, z), (0, 18.8, z), 1.1)
        m.cbox(G, (0, 19.4, z), (2.0, 2.0, 2.0), yaw=45, pitch=35)
        m.cbox(T["emb"], (0, 15.0, z + 0.8), (1.2, 1.2, 0.3), roll=45, glow=True)
        for s in (-1, 1):
            _arm(m, A, Bm, sh[s], (4.8 * s, 17.4, 3.4), (1.0 * s, 17.2, z))
    elif w in ("spear", "spear_shield", "staff"):
        hx, hz = 6.3, 2.2
        # 오른손: 창/지팡이를 세워 잡음
        _arm(m, A, Bm, sh[1], (6.0, 16.6, 1.0), (hx, 14.6, hz))
        if w == "staff":
            m.rod("stripped_dark_oak_log", (hx, 0, hz), (hx, 33, hz), 1.3)
            for i in range(4):
                a = math.radians(i * 90 + 45)
                m.rod(G, (hx, 32, hz), (hx + math.cos(a) * 2.4, 36.4, hz + math.sin(a) * 2.4), 0.7)
            gem(m, (hx, 36.6, hz), 3.4, 5.6, "lime_stained_glass", "verdant_froglight")
            for i in range(3):
                a = math.radians(i * 120)
                m.cbox("azalea_leaves", (hx + math.cos(a) * 1.4, 31.4, hz + math.sin(a) * 1.4), (2.0, 1.4, 2.0), yaw=i * 30)
        else:
            m.rod("dark_oak_planks", (hx, 0, hz), (hx, 36, hz), 1.1)
            m.cbox(G, (hx, 36.4, hz), (1.8, 1.0, 1.8))
            m.cbox(T["blade"], (hx, 39.6, hz), (2.4, 5.6, 0.6))
            m.cbox(T["blade"], (hx, 42.6, hz), (1.5, 1.5, 0.6), roll=45)
            m.cbox(T["cape"], (hx, 34.4, hz), (1.8, 2.6, 1.8))      # 술
        if w == "spear_shield":
            # 왼손: 큰 방패를 앞에
            _arm(m, A, Bm, sh[-1], (-6.4, 17.2, 2.4), (-4.2, 14.8, 5.6))
            k = m.mark()
            kite_shield(m, T["emb"], G, "chevron", w=9.0, h=14.0, t=1.0)
            rotate(m.since(k), rot(-14, 4, 0), (0, 0, 0))
            move(m.since(k), (-4.0, 13.2, 7.0))
        elif w == "staff":
            # 왼손: 빛나는 구슬을 앞으로
            _arm(m, A, Bm, sh[-1], (-6.0, 17.6, 3.0), (-3.6, 18.6, 7.2))
            gem(m, (-3.6, 21.6, 7.4), 2.6, 3.4, "lime_stained_glass", "verdant_froglight")
        else:
            # 왼손: 허리에
            _arm(m, A, Bm, sh[-1], (-6.9, 17.4, -0.4), (-4.9, 14.6, 1.4))
    elif w == "broken":
        # 부서진 석상: 오른팔 없음 · 투구는 발밑에 굴러 있음 · 몸이 기울어짐
        _arm(m, A, Bm, sh[-1], (-6.4, 16.6, 1.2), (-5.6, 12.6, 3.6))
        m.rod(Bm, (5.2, 21.2, 0), (6.6, 18.6, 0.4), 3.0)          # 잘린 팔
    if broken:
        # 머리는 떨어져 발 옆에 굴러 있음
        hs = set(id(h) for h in head)
        m.parts = [p for p in m.parts if id(p) not in hs]
        rotate(m.parts, rot(0, 5, 7), (0, 0, 0))
        m.cbox(A, (8.0, 3.0, 6.5), (6.4, 6.4, 6.4), yaw=35, roll=80)
        m.cbox(Bm, (8.0, 3.0, 6.5), (6.8, 1.0, 6.8), yaw=35, roll=80)
        m.cbox(DARK, (5.2, 3.9, 8.3), (0.4, 5.0, 1.0), yaw=35, roll=80)
        # 부서진 조각들
        for (x, z, s_, yw) in ((-6.5, 5.0, 2.4, 20), (3.0, 8.5, 1.8, 50), (-3.5, -6.0, 2.0, 70)):
            m.cbox("cobblestone", (x, s_ / 2, z), (s_, s_ * 0.8, s_ * 1.2), yaw=yw, roll=12)
        m.cbox("moss_block", (1.0, 23.0, -1.0), (7.0, 1.0, 4.0), roll=9, pitch=6)
    return m


# ─────────────────────────────────────────────────────────────── 팀 표식 (깃발 대신)
def team_standard(t, pole_top):
    """깃대에 걸린 팀 문장 방패 + 깃대 위에 떠서 도는 팀 수정"""
    C = TEAM[t]
    m = Model()
    emb = {"red": "cross", "blue": "chevron", "green": "leaf", "yellow": "sun"}[t]
    k = m.mark()
    kite_shield(m, C["conc"], GOLD, emb, w=10, h=13, t=1.0, emb_block=GOLD if t != "yellow" else "red_concrete")
    move(m.since(k), (0, 0, 2.6))
    # 방패 걸쇠
    m.box("dark_oak_planks", -1.0, 5.0, 0.8, 1.0, 6.6, 2.4)
    m.box(GOLD, -5.4, 6.6, 0.8, 5.4, 7.4, 1.8)
    # 떠 있는 수정
    k = m.mark()
    y = pole_top + 16 * 1.3
    gem(m, (0, y, 0), 7.0, 12.0, C["glass"], C["core"])
    ring(m, GOLD, (0, y, 0), 7.0, 0.8, n=8, tilt=18)
    for p in m.since(k):
        p.spin = True
    return m


def crest(t):
    """벽에 거는 큰 팀 문장 (방패 + 왕관 + 금 테두리 날개)"""
    C = TEAM[t]
    m = Model()
    emb = {"red": "cross", "blue": "chevron", "green": "leaf", "yellow": "sun"}[t]
    kite_shield(m, C["conc"], GOLD, emb, w=16, h=20, t=1.2, emb_block=GOLD if t != "yellow" else "red_concrete")
    crown_badge(m, (0, 11.4, 0), 12, GOLD)
    for i, (x, y_) in enumerate(((-4, 13.6), (0, 14.4), (4, 13.6))):
        m.cbox(C["glass"], (x, y_ + 0.4, 0.4), (1.4, 1.4, 1.0), roll=45)
    for s in (-1, 1):
        for j in range(4):
            m.cbox(GOLD if j % 2 == 0 else "smooth_quartz", (s * (10 + j * 1.6), 5 - j * 2.4, -0.2), (7.0 - j * 1.1, 1.6, 0.8), roll=s * (12 + j * 9))
    return m


# ─────────────────────────────────────────────────────────────── 제단 수정 · 왕관
ELEMENT = {
    "ares": ("red_stained_glass", "shroomlight", "orange_stained_glass"),
    "athena": ("light_blue_stained_glass", "sea_lantern", "white_stained_glass"),
    "hermes": ("white_stained_glass", "pearlescent_froglight", "light_blue_stained_glass"),
    "demeter": ("lime_stained_glass", "verdant_froglight", "green_stained_glass"),
}


def sigil(aid, sc):
    outer, core, shard = ELEMENT[aid]
    m = Model()
    h = 16 * sc * 0.72
    gem(m, (0, 0, 0), h * 0.5, h, outer, core, steps=7)
    ring(m, GOLD, (0, 0, 0), h * 0.52, 1.2, n=16, tilt=20)
    ring(m, GOLD, (0, 0, 0), h * 0.44, 0.9, n=14, tilt=-35)
    for i in range(4):
        a = math.radians(i * 90 + 45)
        gem(m, (math.cos(a) * h * 0.62, math.sin(i) * 3, math.sin(a) * h * 0.62), h * 0.13, h * 0.24, shard, core)
    return spin_all(m)


def crown(sc):
    """왕좌 위에 떠서 도는 커다란 황금 왕관 (보석 4개 = 네 팀)"""
    m = Model()
    R = 16 * sc * 0.36
    H = R * 0.55
    n = 16
    ring(m, GOLD, (0, 0, 0), R, 2.0, n=n, th=H * 0.5)
    ring(m, "raw_gold_block", (0, -H * 0.3, 0), R + 0.6, 1.4, n=n, th=1.6)
    ring(m, "raw_gold_block", (0, H * 0.22, 0), R + 0.5, 1.2, n=n, th=1.2)
    cols = ["red", "blue", "green", "yellow"]
    for i in range(8):
        a = math.radians(i * 45)
        x, z = math.sin(a) * R, math.cos(a) * R
        big = i % 2 == 0
        hh = H * (1.25 if big else 0.8)
        # 뾰족한 가지 (층층이 좁아짐)
        for j, f in enumerate((1.0, 0.7, 0.42)):
            m.cbox(GOLD, (x, H * 0.25 + hh * (j + 0.5) / 3, z), (3.6 * f, hh / 3 * 1.04, 1.6), yaw=math.degrees(a))
        m.cbox(GOLD, (x, H * 0.25 + hh + 1.0, z), (1.8, 1.8, 1.8), yaw=45, pitch=35)
        if big:
            C = TEAM[cols[i // 2]]
            gem(m, (x * 1.04, 0, z * 1.04), 3.2, 4.2, C["glass"], C["core"])
        else:
            m.cbox("diamond_block", (x * 1.04, 0, z * 1.04), (1.6, 1.6, 1.0), yaw=math.degrees(a), roll=45)
    # 벨벳 덮개 + 위 십자 보주
    m.cbox("red_wool", (0, H * 0.15, 0), (R * 1.6, H * 0.6, R * 1.6), yaw=22.5)
    m.cbox("red_wool", (0, H * 0.55, 0), (R * 1.2, H * 0.5, R * 1.2), yaw=22.5)
    m.cbox(GOLD, (0, H * 0.95, 0), (R * 0.5, R * 0.5, R * 0.5), yaw=45)
    m.cbox(GOLD, (0, H * 0.95 + R * 0.5, 0), (1.2, R * 0.5, 1.2))
    m.cbox(GOLD, (0, H * 0.95 + R * 0.55, 0), (R * 0.36, 1.2, 1.2))
    return spin_all(m)


# ─────────────────────────────────────────────────────────────── 무기 (땅에 꽂힘)
def great_sword(L):
    m = Model()
    blade = L * 0.7
    m.rod("iron_block", (0, -3, 0), (0, blade, 0), 3.0, 0.7)
    m.rod("light_gray_concrete", (0, -3, 0.1), (0, blade - 2, 0.1), 0.8, 0.75)
    m.cbox("iron_block", (0, -3.5, 0), (2.0, 2.0, 0.7), roll=45)
    m.cbox("polished_blackstone", (0, blade + 0.6, 0), (L * 0.28, 1.6, 1.6))
    for s in (-1, 1):
        m.cbox(GOLD, (s * L * 0.14, blade + 1.2, 0), (1.8, 1.8, 1.8), yaw=45, pitch=35)
    m.cbox("red_concrete", (0, blade + 0.6, 0.9), (1.2, 1.2, 0.3), roll=45, glow=True)
    m.rod("dark_oak_planks", (0, blade + 1.4, 0), (0, L * 0.94, 0), 1.3)
    for i in range(3):
        m.cbox("polished_blackstone", (0, blade + 2.4 + i * 1.4, 0), (1.5, 0.4, 1.5))
    m.cbox(GOLD, (0, L * 0.97, 0), (2.2, 2.2, 2.2), yaw=45, pitch=35)
    return m


def spear(L):
    m = Model()
    m.rod("dark_oak_planks", (0, -3, 0), (0, L * 0.8, 0), 1.2)
    m.cbox(GOLD, (0, L * 0.8, 0), (1.8, 1.2, 1.8))
    m.cbox("iron_block", (0, L * 0.8 + 3.6, 0), (2.6, 6.0, 0.6))
    m.cbox("iron_block", (0, L * 0.8 + 6.6, 0), (1.8, 1.8, 0.6), roll=45)
    m.cbox("red_wool", (0, L * 0.8 - 2.2, 0), (2.0, 2.6, 2.0))
    return m


def giant_club(L):
    m = Model()
    for i in range(5):
        f = i / 4
        w = 7 + f * 11
        m.cbox("stripped_spruce_log" if i % 2 else "spruce_log", (0, L * (0.1 + f * 0.8), 0), (w, L * 0.21, w), yaw=i * 17)
    m.cbox("iron_block", (0, L * 0.2, 0), (4.2, 1.2, 4.2))
    for i in range(10):
        a = i * 2.4
        y = L * (0.55 + (i % 5) * 0.08)
        r = 3 + (y / L) * 4
        m.cbox("iron_block", (math.cos(a) * r, y, math.sin(a) * r), (1.6, 1.6, 1.6), yaw=math.degrees(a), pitch=35, roll=45)
    return m


def battle_shield(t_block="red_concrete"):
    m = Model()
    kite_shield(m, t_block, "iron_block", "cross", w=12, h=16, t=1.2, emb_block="iron_block")
    m.cbox("cobblestone", (2.5, 3, 0.8), (2.0, 2.0, 0.4), roll=30)   # 흠집
    return m


# ─────────────────────────────────────────────────────────────── 벽 장식 · 소품
def wall_sconce():
    """벽 화로: 쇠 받침 + 금 그릇 + 불꽃 (벽 = -z, 앞 = +z) + 위에 왕관 문장 방패"""
    m = Model()
    m.box("polished_blackstone", -2.5, -8, -1.0, 2.5, 4, 0.2)
    m.rod("polished_blackstone", (0, -6, 0), (0, -1, 6), 1.6)
    m.cbox(GOLD, (0, -0.2, 6.4), (7.0, 1.4, 7.0), yaw=45)
    m.cbox(GOLD, (0, 1.0, 6.4), (8.4, 1.2, 8.4))
    m.cbox("polished_blackstone", (0, -1.4, 6.4), (3.0, 1.2, 3.0), yaw=45)
    m.cbox("shroomlight", (0, 3.2, 6.4), (4.4, 3.6, 4.4), yaw=20, glow=True)
    m.cbox("orange_stained_glass", (0, 4.6, 6.4), (5.4, 5.6, 5.4), yaw=65)
    m.cbox("yellow_stained_glass", (0, 7.4, 6.4), (2.8, 3.4, 2.8), yaw=10)
    k = m.mark()
    kite_shield(m, "purple_concrete", GOLD, "crown", w=9, h=11, t=1.0)
    move(m.since(k), (0, 13, 0.4))
    return m


def trophy():
    """깃대에 건 전리품: 붉은 방패 + 교차한 두 검"""
    m = Model()
    for s in (-1, 1):
        k = m.mark()
        m.add(great_sword(26))
        rotate(m.since(k), rot(0, 0, 38 * s), (0, 0, 0))
        move(m.since(k), (0, -9, 1.4))
    k = m.mark()
    kite_shield(m, "red_concrete", GOLD, "cross", w=10, h=13, t=1.0)
    move(m.since(k), (0, 0, 3.0))
    return m


def weathervane():
    """바람개비: 도는 화살 + 방위 막대 + 작은 수정 (깃대 위)"""
    m = Model()
    m.rod("iron_block", (0, 0, 0), (0, 14, 0), 1.0)
    for s in (0, 90):
        m.cbox("iron_block", (0, 6, 0), (12, 0.7, 0.7), yaw=s)
    for s, (x, z) in enumerate(((6.8, 0), (-6.8, 0), (0, 6.8), (0, -6.8))):
        m.cbox(GOLD, (x, 6, z), (1.4, 1.4, 1.4), yaw=45, pitch=35)
    k = m.mark()
    m.cbox("iron_block", (0, 11, 0), (1.0, 0.8, 16))
    m.cbox(GOLD, (0, 11, 9.2), (0.6, 3.2, 3.2), pitch=45)
    m.cbox("white_wool", (0, 11.6, -7.6), (0.5, 4.0, 5.0), pitch=-10)
    m.cbox("light_blue_wool", (0, 10.4, -7.6), (0.5, 2.4, 4.4), pitch=10)
    gem(m, (0, 15.4, 0), 2.6, 3.6, "light_blue_stained_glass", "sea_lantern")
    for p in m.since(k):
        p.spin = True
    return m


def owl():
    m = Model()
    S = "smooth_quartz"
    m.cbox(S, (0, 5.0, 0), (7.0, 8.0, 6.0))
    m.cbox(S, (0, 5.4, 0.6), (8.0, 6.0, 5.2))
    m.cbox("calcite", (0, 4.4, 2.8), (5.0, 5.4, 1.2))           # 가슴 깃
    for s in (-1, 1):
        m.cbox("quartz_bricks", (4.2 * s, 5.2, -0.4), (1.4, 7.0, 5.0), roll=6 * s)   # 날개
        m.cbox(GOLD, (1.6 * s, 0.6, 1.8), (1.6, 1.2, 2.2))      # 발톱
    m.cbox(S, (0, 11.2, 0.2), (7.4, 5.2, 6.0))                  # 머리
    for s in (-1, 1):
        m.cbox(S, (2.8 * s, 14.4, 0.2), (1.4, 2.6, 1.4), roll=-18 * s)   # 귀깃
        m.cbox("calcite", (1.7 * s, 11.6, 3.2), (2.8, 2.8, 0.6))
        m.cbox("ochre_froglight", (1.7 * s, 11.6, 3.5), (1.4, 1.4, 0.4), glow=True)
    m.cbox(GOLD, (0, 10.2, 3.5), (1.0, 1.6, 1.0), pitch=20)
    return m


def sphinx_head():
    """스핑크스 머리: 사암 얼굴 + 청금 · 금 줄무늬 두건 + 수염 (앞 = +z)"""
    m = Model()
    F = "smooth_sandstone"
    m.box(F, -7, 0, -6, 7, 16, 6)                                 # 얼굴 · 머리
    # 두건 (위 · 양옆 늘어짐, 줄무늬)
    for i in range(6):
        blk = "lapis_block" if i % 2 == 0 else GOLD
        m.box(blk, -9, 13 - i * 0.0 + i * 0.9, -7, 9, 14.2 + i * 0.9, 5.5)
    m.box("lapis_block", -9.5, 18.5, -7.2, 9.5, 19.6, 5.6)
    for s in (-1, 1):
        for i in range(7):
            blk = "lapis_block" if i % 2 == 0 else GOLD
            m.box(blk, 7 * s, 12 - i * 2.2, -6.5, 10 * s, 14 - i * 2.2, 4.5)
        m.box(GOLD, 7.2 * s, -3.4, -2.5, 10.2 * s, -2.4, 4.6)
    m.cbox("red_sandstone", (0, 19.9, -0.6), (3.6, 3.0, 2.6))    # 이마 장식
    m.cbox(GOLD, (0, 18.8, 5.8), (2.6, 3.6, 1.2))
    # 눈 · 코 · 입
    for s in (-1, 1):
        m.box(DARK, 2.0 * s - 1.8, 9.6, 5.9, 2.0 * s + 1.8, 10.8, 6.2)
        m.box("lapis_block", 2.0 * s - 2.4, 11.2, 5.9, 2.0 * s + 2.4, 11.8, 6.25)
        m.box("ochre_froglight", 2.0 * s - 0.6, 9.8, 6.1, 2.0 * s + 0.6, 10.6, 6.35, glow=True)
    m.cbox(F, (0, 7.2, 6.6), (2.2, 4.6, 1.6), pitch=-10)
    m.box("sandstone", -2.6, 3.4, 5.9, 2.6, 4.2, 6.3)
    # 수염
    m.box(GOLD, -1.4, -5, 3.0, 1.4, 0.4, 5.6)
    for i in range(3):
        m.box("lapis_block", -1.5, -4.2 + i * 1.8, 5.5, 1.5, -3.6 + i * 1.8, 5.8)
    m.cbox("sandstone", (3, -1, 0), (8, 3, 8), yaw=20, roll=8)   # 깨진 목
    move(m.parts, (0, 5.5, 0))
    return m


def bronze_debris():
    m = Model()
    rng = np.random.default_rng(7)
    parts = ["cut_copper", "exposed_copper", "weathered_cut_copper", "copper_block", "exposed_cut_copper"]
    for i in range(9):
        a = rng.uniform(0, 6.28); d = rng.uniform(0, 9)
        s = rng.uniform(3, 7)
        m.cbox(parts[i % 5], (math.cos(a) * d, s * 0.35, math.sin(a) * d), (s, s * 0.7, s * rng.uniform(0.7, 1.4)),
               yaw=rng.uniform(0, 90), pitch=rng.uniform(-20, 20), roll=rng.uniform(-25, 25))
    # 골렘 머리 조각 (빛나는 눈 하나)
    m.cbox("copper_block", (-3, 5, 4), (9, 8, 8), yaw=25, roll=-14)
    m.cbox("ochre_froglight", (-3.6, 5.8, 8.1), (2.4, 1.4, 0.6), yaw=25, roll=-14, glow=True)
    m.rod("oxidized_copper", (4, 0, -3), (10, 10, -6), 3.0)
    return m


def golden_apple():
    m = Model()
    m.cbox(GOLD, (0, 0, 0), (6.0, 5.4, 6.0), glow=True)
    m.cbox(GOLD, (0, -0.3, 0), (7.2, 3.8, 4.6), glow=True)
    m.cbox(GOLD, (0, -0.3, 0), (4.6, 3.8, 7.2), glow=True)
    m.cbox("raw_gold_block", (0, -2.8, 0), (3.0, 0.8, 3.0))
    m.rod("dark_oak_planks", (0, 2.4, 0), (0.6, 5.0, 0.2), 0.8)
    m.cbox("azalea_leaves", (1.9, 4.2, 0.2), (3.0, 0.6, 1.8), roll=-25)
    return m


def winged_crest():
    """박공 부조: 날개 달린 왕관 문장 (벽에 붙음, 앞 = +z)"""
    m = Model()
    kite_shield(m, "purple_concrete", GOLD, "crown", w=14, h=18, t=1.4)
    for s in (-1, 1):
        for j in range(6):
            L = 16 - j * 1.6
            m.cbox(GOLD if j % 2 == 0 else "smooth_quartz", (s * (8 + L / 2 - j * 0.2), 7 - j * 2.6, -0.2), (L, 2.2, 1.0),
                   roll=s * (8 + j * 7))
    crown_badge(m, (0, 11.8, 0), 12, GOLD)
    return m


# ─────────────────────────────────────────────────────────────── 이름 → 모델
def build(model, sc, d):
    """반환: (Model, 기본 y 보정 px) — None 이면 장식 없음"""
    kind = d.get("kind")
    if kind == "statue":
        if model not in KNIGHTS:
            return None
        return scale(knight(model), sc)
    if model.startswith("deco/flag_"):
        t = model.split("_")[-1]
        pole_top = 16 * 1.8 if sc > 2 else 16 * 0.8    # 본진 깃대(등불 위) · 망루 울타리 끝
        return team_standard(t, pole_top)
    if model.startswith("deco/crest_"):
        return scale(crest(model.split("_")[-1]), sc / 3.0 * 1.1)
    if model.startswith("deco/sigil_"):
        return sigil(model.split("_")[-1], sc)
    if model == "deco/zeus_bolt":
        return crown(sc)
    if model == "deco/banner_olympus":
        return scale(wall_sconce(), 1.4)
    if model == "deco/war_banner":
        return scale(trophy(), 1.3)
    if model == "deco/wind_ribbon":
        m = weathervane(); move(m.parts, (0, 17, 0)); return scale(m, 1.4)
    if model == "deco/eagle_relief":
        return scale(winged_crest(), sc / 5 * 2.2)
    if model == "deco/great_sword":
        return great_sword(16 * sc * 1.2)
    if model == "deco/spear":
        return spear(16 * sc * 1.3)
    if model == "deco/giant_club":
        return giant_club(16 * sc * 1.2)
    if model == "deco/shield":
        return scale(battle_shield(), sc / 2.2 * 1.6)
    if model == "deco/owl":
        return scale(owl(), sc / 1.8 * 1.5)
    if model == "deco/sphinx_head":
        return scale(sphinx_head(), sc / 5 * 2.6)
    if model == "deco/bronze_debris":
        return scale(bronze_debris(), sc / 3 * 1.4)
    if model in ("deco/peach", "minecraft:golden_apple"):
        return scale(golden_apple(), sc / 1.4 * 1.5)
    return None


# ─────────────────────────────────────────────────────────────── 보스 보상 상자
def treasure_chest(t):
    """받침 + 금띠 두른 보물 상자 (뚜껑 틈으로 빛) + 금화 더미 + 도는 팀 보석 + 빛기둥. 원점 = 바닥 가운데"""
    C = TEAM[t]
    m = Model()
    # 받침
    m.box("gilded_blackstone", -18, 0, -18, 18, 5, 18)
    m.box("polished_blackstone", -15, 5, -15, 15, 7.5, 15)
    for a in (0, 90, 180, 270):
        k = m.mark()
        m.box(GOLD, -18.4, 4.4, 17.6, 18.4, 5.4, 18.6, glow=True)
        m.cbox(C["core"], (0, 2.5, 18.2), (4, 2, 0.6), glow=True)
        rotate(m.since(k), rot(a), (0, 0, 0))
    y0 = 7.5
    W, D, H = 24, 16, 13
    # 몸통
    m.box("dark_oak_planks", -W / 2, y0, -D / 2, W / 2, y0 + H, D / 2)
    m.box("spruce_planks", -W / 2 + 1.2, y0 + 1.2, -D / 2 - 0.2, W / 2 - 1.2, y0 + H - 1.5, D / 2 + 0.2)
    # 금띠 (세로 · 가로 · 모서리)
    for x in (-W / 2 - 0.3, W / 2 - 1.7):
        m.box(GOLD, x, y0 - 0.2, -D / 2 - 0.3, x + 2.0, y0 + H, D / 2 + 0.3)
    for x in (-5.5, 3.5):
        m.box(GOLD, x, y0 - 0.2, -D / 2 - 0.4, x + 2.0, y0 + H, D / 2 + 0.4)
    m.box(GOLD, -W / 2 - 0.3, y0 - 0.3, -D / 2 - 0.3, W / 2 + 0.3, y0 + 1.4, D / 2 + 0.3)
    # 뚜껑 틈 빛
    m.box(C["core"], -W / 2 + 0.6, y0 + H, -D / 2 + 0.6, W / 2 - 0.6, y0 + H + 1.0, D / 2 - 0.6, glow=True)
    # 둥근 뚜껑 (층층이)
    ly = y0 + H + 1.0
    for i, (dd, hh) in enumerate(((D, 2.2), (D * 0.86, 2.0), (D * 0.62, 1.8), (D * 0.34, 1.4))):
        m.box("dark_oak_planks", -W / 2, ly, -dd / 2, W / 2, ly + hh, dd / 2)
        for x in (-W / 2 - 0.3, W / 2 - 1.7, -5.5, 3.5):
            m.box(GOLD, x, ly - 0.1, -dd / 2 - 0.3, x + 2.0, ly + hh + 0.2, dd / 2 + 0.3)
        ly += hh
    # 자물쇠 + 팀 보석
    m.box(GOLD, -2.6, y0 + H - 4.5, D / 2 + 0.2, 2.6, y0 + H + 3.2, D / 2 + 1.0, glow=True)
    m.cbox(C["glass"], (0, y0 + H - 0.6, D / 2 + 1.3), (2.6, 2.6, 0.8), roll=45)
    m.cbox(C["core"], (0, y0 + H - 0.6, D / 2 + 1.2), (1.4, 1.4, 0.6), roll=45, glow=True)
    # 금화 · 금괴 더미
    rng = np.random.default_rng(3)
    for i in range(14):
        a = rng.uniform(0, 6.28); d = rng.uniform(9, 14.5)
        big = i % 4 == 0
        s = (4.2, 2.0, 2.2) if big else (2.6, 0.6, 2.6)
        blk = "raw_gold_block" if i % 3 == 0 else GOLD
        m.cbox(blk, (math.cos(a) * d, y0 + s[1] / 2, math.sin(a) * d), s, yaw=math.degrees(a), roll=rng.uniform(-10, 10), glow=True)
    # 도는 팀 보석 4개 + 빛기둥
    k = m.mark()
    for i in range(4):
        a = math.radians(i * 90 + 45)
        gem(m, (math.cos(a) * 22, 38 + (i % 2) * 4, math.sin(a) * 22), 5.0, 8.0, C["glass"], C["core"])
    for p in m.since(k):
        p.spin = True
    m.box(C["glass"], -2.2, ly, -2.2, 2.2, ly + 190, 2.2, glow=True)
    m.box(C["core"], -0.8, ly, -0.8, 0.8, ly + 190, 0.8, glow=True)
    return m


# ─────────────────────────────────────────────────────────────── 상점 상인 NPC
def merchant():
    """떠돌이 상인: 보라 로브 + 금 장식, 넓은 챙 모자와 깃털, 흰 수염, 한 손엔 금화 주머니 · 한 손엔 금화.
       옆에 금화가 쌓인 작은 좌판. 원점 = 발밑, 앞 = +z"""
    m = Model()
    ROBE, ROBE2, TRIM = "purple_wool", "magenta_wool", GOLD
    SKIN, BEARD = "smooth_sandstone", "white_wool"
    LEATHER, HAT = "brown_wool", "dark_oak_planks"
    # 신발
    for s in (-1, 1):
        m.box(LEATHER, 2.0 * s - 1.7, 0, -1.6, 2.0 * s + 1.7, 1.6, 2.8)
    # 로브 (아래로 퍼짐)
    m.box(ROBE, -5.2, 1.2, -3.4, 5.2, 8.0, 3.4)
    m.box(ROBE, -4.8, 8.0, -3.0, 4.8, 14.0, 3.0)
    m.box(ROBE2, -1.4, 1.2, 3.35, 1.4, 14.0, 3.7)                 # 앞자락
    m.box(TRIM, -5.35, 1.0, -3.55, 5.35, 1.9, 3.55)                # 밑단 금테
    m.box(TRIM, -1.6, 1.2, 3.5, -1.2, 14.0, 3.9)
    m.box(TRIM, 1.2, 1.2, 3.5, 1.6, 14.0, 3.9)
    # 가죽 앞치마 · 허리띠 · 주머니들
    m.box(LEATHER, -3.6, 7.0, 3.1, 3.6, 13.6, 3.6)
    m.box("dark_oak_planks", -5.0, 13.4, -3.2, 5.0, 14.6, 3.2)
    m.cbox(GOLD, (0, 14.0, 3.35), (1.8, 1.6, 0.6))
    m.cbox(LEATHER, (-4.6, 12.0, 1.5), (2.2, 2.8, 2.2), yaw=-12)
    m.cbox("red_wool", (4.7, 11.8, 1.2), (2.0, 2.6, 2.0), yaw=15)
    # 몸통 · 망토깃
    m.box(ROBE, -4.4, 14.4, -2.4, 4.4, 22.0, 2.4)
    m.box(ROBE2, -4.9, 20.0, -2.8, 4.9, 22.6, 2.8)
    m.box(TRIM, -4.95, 21.8, -2.85, 4.95, 22.4, 2.85)
    m.box(ROBE, -4.0, 8.0, -4.2, 4.0, 21.5, -3.0)                 # 등 망토
    # 머리 · 수염
    m.box(SKIN, -3.2, 22.4, -3.0, 3.2, 28.6, 3.2)
    m.box(BEARD, -3.3, 19.4, 2.0, 3.3, 25.2, 3.6)
    m.cbox(BEARD, (0, 18.2, 3.0), (3.6, 2.6, 1.4), pitch=12)
    m.box("white_concrete", -2.8, 25.0, 3.15, 2.8, 25.6, 3.5)    # 콧수염
    m.cbox(SKIN, (0, 26.0, 3.5), (1.4, 1.8, 1.2))                 # 코
    for s in (-1, 1):
        m.box(DARK, 1.1 * s - 0.55, 26.8, 3.2, 1.1 * s + 0.55, 27.6, 3.3)
        m.box(BEARD, 1.1 * s - 0.9, 27.9, 3.2, 1.1 * s + 0.9, 28.3, 3.35)   # 눈썹
    # 모자: 넓은 챙 + 높은 관 + 금띠 + 깃털
    m.cbox(HAT, (0, 28.9, 0.2), (13.0, 0.9, 13.0), yaw=0)
    m.cbox(HAT, (0, 31.4, 0), (7.0, 4.4, 7.0))
    m.cbox(HAT, (0.4, 34.0, -0.4), (5.0, 1.6, 5.0), roll=6)
    m.box(GOLD, -3.6, 29.3, -3.6, 3.6, 30.4, 3.6)
    m.cbox("red_wool", (3.6, 33.0, -1.2), (0.6, 6.0, 1.8), roll=-24, pitch=-10)
    m.cbox("white_wool", (4.6, 35.2, -1.6), (0.5, 2.6, 1.4), roll=-30, pitch=-10)
    # 오른팔: 금화 주머니
    m.rod(ROBE, (5.2, 21.0, 0), (6.4, 16.4, 2.2), 3.0)
    m.rod(ROBE2, (6.4, 16.4, 2.2), (6.2, 13.0, 4.8), 2.8)
    m.cbox(SKIN, (6.2, 12.6, 5.0), (2.2, 2.2, 2.2))
    m.cbox(LEATHER, (6.2, 9.2, 5.2), (4.4, 4.6, 4.4), yaw=20)
    m.cbox(GOLD, (6.2, 11.8, 5.2), (2.2, 0.8, 2.2), yaw=20)
    m.cbox(GOLD, (6.8, 12.4, 5.4), (1.6, 0.5, 1.6), yaw=40, roll=20)
    # 왼팔: 금화를 들어 보임
    m.rod(ROBE, (-5.2, 21.0, 0), (-6.8, 17.6, 3.0), 3.0)
    m.rod(ROBE2, (-6.8, 17.6, 3.0), (-6.0, 21.6, 6.0), 2.8)
    m.cbox(SKIN, (-6.0, 22.4, 6.2), (2.2, 2.2, 2.2))
    m.cbox(GOLD, (-6.0, 24.6, 6.4), (2.6, 2.6, 0.5), roll=20, glow=True)
    # 옆 좌판 (오른쪽)
    k = m.mark()
    m.box("spruce_planks", 9, 0, -4, 21, 1, 5)
    for x, z in ((9.4, -3.6), (20.6, -3.6), (9.4, 4.6), (20.6, 4.6)):
        m.box("stripped_dark_oak_log", x - 0.6, 0, z - 0.6, x + 0.6, 9, z + 0.6)
    m.box("dark_oak_planks", 8.4, 9, -4.6, 21.6, 10.2, 5.6)
    m.box("red_wool", 8.8, 10.2, -4.2, 21.2, 10.6, 5.2)
    m.box(TRIM, 8.4, 9.6, 5.5, 21.6, 10.2, 5.9)
    rng = np.random.default_rng(5)
    for i in range(5):
        x = 11 + i * 2.2; hgt = 1 + (i % 3)
        for j in range(hgt):
            m.cbox(GOLD, (x, 11.0 + j * 0.7, 1.5 + (i % 2)), (1.8, 0.6, 1.8), yaw=rng.uniform(0, 40), glow=True)
    m.cbox("diamond_block", (18.6, 11.4, -1.6), (1.6, 1.6, 1.6), yaw=45, pitch=35)
    m.cbox("emerald_block", (16.8, 11.2, -2.4), (1.4, 1.4, 1.4), yaw=20, pitch=35)
    m.box("dark_oak_planks", 12, 10.6, -3.6, 16, 13.6, -0.4)                  # 작은 궤짝
    m.box(GOLD, 13.6, 11.4, -0.5, 14.4, 12.8, -0.2)
    # 좌판 지붕 (줄무늬 천)
    for i in range(6):
        m.cbox("purple_wool" if i % 2 == 0 else "yellow_wool", (15, 24.5, -3.2 + i * 1.9), (14, 0.8, 2.0), pitch=-14)
    for x in (8.8, 21.2):
        m.box("stripped_dark_oak_log", x - 0.5, 10.2, 5.0, x + 0.5, 23.6, 6.0)
        m.box("stripped_dark_oak_log", x - 0.5, 10.2, -4.6, x + 0.5, 26.6, -3.6)
    # 금화 간판 (좌판 위)
    m.cbox(TRIM, (15, 28.5, -3.9), (6.4, 6.4, 0.8), roll=45, glow=True)
    m.cbox("purple_concrete", (15, 28.5, -3.4), (4.6, 4.6, 0.8), roll=45)
    m.cbox(TRIM, (15, 28.5, -2.9), (2.2, 2.2, 0.6), glow=True)
    return m


# ─────────────────────────────────────────────────────────────── 병과 표식 (발판 위에서 도는 아이콘)
def class_icon(k):
    m = Model()
    if k == 0:          # 전사: 검
        m.rod("iron_block", (0, -8, 0), (0, 10, 0), 2.6, 0.6)
        m.cbox("iron_block", (0, -9, 0), (1.8, 1.8, 0.6), roll=45)
        m.cbox(GOLD, (0, 10.6, 0), (8.0, 1.4, 1.4))
        m.rod("dark_oak_planks", (0, 11.3, 0), (0, 15.2, 0), 1.2)
        m.cbox(GOLD, (0, 15.8, 0), (2.0, 2.0, 2.0), yaw=45, pitch=35)
        m.cbox("red_concrete", (0, 10.6, 0.8), (1.2, 1.2, 0.3), roll=45, glow=True)
    elif k == 1:        # 궁수: 활 + 화살
        prof = [(-1.0, -12), (1.2, -8), (2.4, -4), (2.8, 0), (2.4, 4), (1.2, 8), (-1.0, 12)]
        for (x0, y0), (x1, y1) in zip(prof, prof[1:]):
            m.rod("dark_oak_planks", (x0, y0, 0), (x1, y1, 0), 1.4, 1.2)
        m.cbox(GOLD, (2.8, 0, 0), (1.8, 3.0, 1.6))
        m.rod("white_wool", (-1.0, -12, 0), (-1.0, 12, 0), 0.4, 0.4)
        m.rod("dark_oak_planks", (-4.0, 0, 0), (10, 0, 0), 0.7, 0.7)       # 화살대
        m.cbox("iron_block", (10.8, 0, 0), (2.4, 1.6, 0.5), roll=45)
        m.cbox("white_wool", (-4.4, 0.8, 0), (2.4, 1.0, 0.3), roll=20)
        m.cbox("white_wool", (-4.4, -0.8, 0), (2.4, 1.0, 0.3), roll=-20)
    else:               # 수호자: 방패
        kite_shield(m, "light_gray_concrete", GOLD, "cross", w=12, h=15, t=1.2, emb_block=GOLD)
    for p in m.parts:
        p.spin = True
    return m
