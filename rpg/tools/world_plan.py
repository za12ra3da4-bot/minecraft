"""스팀펑크 RPG 오픈월드 설계도 (4000 x 4000 블록, 좌표 -2000 ~ 2000) → rpg/preview/world_plan.png"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "preview")
os.makedirs(OUT, exist_ok=True)

S = 2000                    # 그림 크기 (1픽셀 = 2블록)
K = S / 4000


def P(x, z):
    return ((x + 2000) * K, (z + 2000) * K)


FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
def font(n):
    return ImageFont.truetype(FONT, n)


# (이름, 레벨, 중심 x, z, 반지름, 색, 테마)
REGIONS = [
    ("녹슨 평원", "Lv.1–10", 0, 1050, 520, (170, 150, 90), "버려진 태엽 기계가 떠도는 초원 · 풍차 · 고철 더미"),
    ("폐광산 언덕", "Lv.10–20", -1050, 1050, 480, (120, 105, 95), "무너진 갱도 · 굴착기 · 광석 골렘"),
    ("태엽 숲", "Lv.20–30", 1050, 1000, 500, (70, 120, 70), "톱니 나무 · 기계 짐승 · 태엽 대성당"),
    ("유황 늪지", "Lv.30–40", -1250, 0, 520, (95, 120, 60), "독가스 정제소 · 늪 괴물 · 파이프 미로"),
    ("구리 사막", "Lv.30–40", 1250, 0, 520, (200, 150, 80), "고대 거상 발굴지 · 모래 폭풍 · 유적"),
    ("서리 첨탑 산맥", "Lv.40–50", -1050, -1050, 520, (180, 200, 215), "빙하 관측소 · 얼어붙은 기관차"),
    ("화산 제련소", "Lv.50–60", 1050, -1050, 520, (150, 60, 45), "용암 용광로 · 불의 기계 군단"),
    ("에테르 첨탑 (하늘섬)", "Lv.60–70", 0, -1300, 480, (140, 150, 210), "떠 있는 섬 (y 220~320) · 하늘 해적 · 레이드"),
    ("코그시티 협곡", "Lv.25–35", 0, 0, 430, (135, 120, 110), "중앙 공업 수도 주변 · 증기 협곡"),
]

# (이름, x, z, 설명)
TOWNS = [
    ("브라스헤이븐", 0, 1600, "시작 항구 도시"),
    ("코그시티", 0, 0, "중앙 수도 · 거래소 · 강화소"),
    ("머크워터", -1500, 250, "늪 마을"),
    ("코퍼샌드", 1500, 250, "사막 오아시스 마을"),
    ("프로스트게이트", -1350, -700, "북서 요새"),
    ("애쉬포지", 1350, -700, "화산 대장장이 마을"),
    ("스카이포트", 0, -900, "하늘섬 비행선 항구"),
]

# (이름, 레벨, x, z, 종류)  종류: D=던전  R=레이드
DUNGEONS = [
    ("폭주한 기관실", "Lv.18", -1200, 1250, "D"),
    ("태엽 대성당", "Lv.28", 1250, 1200, "D"),
    ("유황 정제소", "Lv.38", -1000, -250, "D"),
    ("잠든 거상의 무덤", "Lv.38", 950, -250, "D"),
    ("얼어붙은 관측소", "Lv.48", -700, -1450, "D"),
    ("용광로의 심장", "Lv.58", 750, -1550, "D"),
    ("하늘 전함 리바이어던", "Lv.70 레이드", 0, -1650, "R"),
]

# (이름, x, z)
BOSSES = [
    ("태엽 기사단장 클락워든", 380, 1250),
    ("폭주한 굴착기 보어 킹", -900, 1300),
    ("태엽 거목 오르골", 750, 1150),
    ("늪의 정화조 괴물", -1100, 300),
    ("모래 거상 사하르", 1100, 300),
    ("서리 기관차 윈터라인", -1450, -1000),
    ("용광로 군주 이그니스", 1250, -950),
]

# 증기 기차 철도 (마을 연결)
RAIL = [(0, 1600), (0, 0), (-1500, 250), (-1350, -700), (0, -900), (1350, -700), (1500, 250), (0, 0)]
RAIL2 = [(0, 1600), (-900, 1500), (-1500, 250)]
RAIL3 = [(0, 1600), (900, 1500), (1500, 250)]


def blob(cx, cz, r, seed):
    R = np.random.default_rng(seed)
    pts = []
    ph = R.uniform(0, 6.28, 4)
    for i in range(72):
        a = 2 * math.pi * i / 72
        k = 1 + 0.12 * math.sin(3 * a + ph[0]) + 0.08 * math.sin(5 * a + ph[1]) + 0.05 * math.sin(9 * a + ph[2])
        pts.append(P(cx + math.cos(a) * r * k, cz + math.sin(a) * r * k))
    return pts


def main():
    im = Image.new("RGB", (S, S), (38, 70, 104))                     # 바다
    d = ImageDraw.Draw(im)
    # 대륙 (바다 테두리 안)
    land = blob(0, 0, 1880, 7)
    d.polygon(land, fill=(96, 110, 80))
    # 지역
    for i, (nm, lv, x, z, r, col, desc) in enumerate(REGIONS):
        d.polygon(blob(x, z, r, 20 + i), fill=col)
    im = im.filter(ImageFilter.GaussianBlur(3))
    d = ImageDraw.Draw(im, "RGBA")
    # 격자 (500 블록)
    for v in range(-2000, 2001, 500):
        a = P(v, -2000); b = P(v, 2000)
        d.line([a, b], fill=(255, 255, 255, 40), width=1)
        a = P(-2000, v); b = P(2000, v)
        d.line([a, b], fill=(255, 255, 255, 40), width=1)
        d.text(P(v + 8, -1990), f"x {v}", fill=(230, 230, 230), font=font(16))
        d.text(P(-1990, v + 8), f"z {v}", fill=(230, 230, 230), font=font(16))
    # 철도
    for line in (RAIL, RAIL2, RAIL3):
        pts = [P(x, z) for x, z in line]
        d.line(pts, fill=(40, 30, 25, 255), width=9, joint="curve")
        d.line(pts, fill=(210, 170, 90, 255), width=4, joint="curve")
    # 지역 이름
    for nm, lv, x, z, r, col, desc in REGIONS:
        cx, cy = P(x, z - r * 0.55)
        for txt, f, c in ((nm, font(34), (255, 255, 255)), (lv, font(24), (255, 225, 140))):
            w = d.textlength(txt, font=f)
            d.text((cx - w / 2 + 2, cy + 2), txt, fill=(0, 0, 0, 160), font=f)
            d.text((cx - w / 2, cy), txt, fill=c, font=f)
            cy += f.size + 4
        w = d.textlength(desc, font=font(16))
        d.text((cx - w / 2, cy), desc, fill=(240, 240, 240), font=font(16))
    # 마을
    for nm, x, z, desc in TOWNS:
        cx, cy = P(x, z)
        d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(250, 220, 120), outline=(60, 40, 20), width=4)
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(60, 40, 20))
        d.text((cx + 22, cy - 16), nm, fill=(255, 245, 200), font=font(24), stroke_width=3, stroke_fill=(40, 25, 10))
        d.text((cx + 22, cy + 10), desc, fill=(230, 230, 230), font=font(15), stroke_width=2, stroke_fill=(20, 15, 10))
    # 던전 · 레이드
    for nm, lv, x, z, kind in DUNGEONS:
        cx, cy = P(x, z)
        col = (180, 90, 255) if kind == "D" else (255, 60, 60)
        s = 15 if kind == "D" else 22
        d.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], fill=col, outline=(20, 10, 30), width=3)
        d.text((cx + s + 6, cy - 12), f"{nm} ({lv})", fill=(245, 225, 255), font=font(18), stroke_width=3, stroke_fill=(30, 10, 40))
    # 필드 보스
    for nm, x, z in BOSSES:
        cx, cy = P(x, z)
        d.regular_polygon((cx, cy, 13), 3, fill=(230, 50, 40), outline=(40, 0, 0))
        d.text((cx + 16, cy - 10), nm, fill=(255, 210, 200), font=font(16), stroke_width=3, stroke_fill=(40, 0, 0))
    # 제목 + 범례
    d.rectangle([20, S - 250, 620, S - 20], fill=(20, 16, 12, 220), outline=(200, 160, 80), width=3)
    d.text((40, S - 240), "에테르 대륙 — 오픈월드 설계도", fill=(255, 220, 140), font=font(30))
    d.text((40, S - 195), "4000 × 4000 블록 (좌표 -2000 ~ 2000) · 격자 500칸", fill=(230, 230, 230), font=font(18))
    y = S - 160
    for sym, txt in (("town", "마을 (비행선 정류장 · 기차역)"), ("dun", "던전 (파티 입장)"), ("raid", "레이드"), ("boss", "필드 보스"), ("rail", "증기 기차 철도")):
        if sym == "town":
            d.ellipse([44, y + 2, 64, y + 22], fill=(250, 220, 120), outline=(60, 40, 20), width=3)
        elif sym == "dun":
            d.polygon([(54, y), (66, y + 12), (54, y + 24), (42, y + 12)], fill=(180, 90, 255))
        elif sym == "raid":
            d.polygon([(54, y), (66, y + 12), (54, y + 24), (42, y + 12)], fill=(255, 60, 60))
        elif sym == "boss":
            d.regular_polygon((54, y + 12, 11), 3, fill=(230, 50, 40))
        else:
            d.line([(40, y + 12), (70, y + 12)], fill=(210, 170, 90), width=5)
        d.text((84, y), txt, fill=(240, 240, 240), font=font(20))
        y += 28
    im.save(os.path.join(OUT, "world_plan.png"))


if __name__ == "__main__":
    main()
