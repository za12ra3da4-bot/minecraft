"""머리 위 이름 밑 체력바 (스코어보드 below_name + 글꼴 글자)

 체력 비율 0~100% 를 21단계(5%씩) 글자로 그려 둔다 → Skript(a32-hpbar.sk)가 사람마다
   scoreboard players display numberformat <이름> bg_hp fixed {text:"<글자>",font:"bg:hpbar"}
 로 이름 밑 숫자 자리에 막대를 띄운다. 색: 60% 넘으면 초록 · 30% 넘으면 노랑 · 그 아래 빨강
 글꼴 그림 한 장 256 픽셀 제한 → 3칸 x 7줄 격자 (칸 64x12)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw

import hud as H

STEPS = 21
CW, CH = 64, 12              # 칸 크기 (2픽셀 = 글자 1칸)
COLS = 3
CH0 = 0xE000                 # bg:hpbar 글꼴 전용이라 다른 글꼴과 안 겹침


def bar(i):
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, CW - 1, CH - 1], fill=(12, 10, 14, 230))           # 테두리
    d.rectangle([2, 2, CW - 3, CH - 3], fill=(58, 52, 58, 220))            # 빈 칸
    f = i / (STEPS - 1)
    w = round((CW - 4) * f)
    if w > 0:
        col = (70, 220, 90) if f > 0.6 else ((240, 200, 60) if f > 0.3 else (230, 60, 60))
        hi = tuple(min(255, c + 70) for c in col)
        lo = tuple(int(c * 0.65) for c in col)
        d.rectangle([2, 2, 2 + w - 1, CH - 3], fill=col + (255,))
        d.rectangle([2, 2, 2 + w - 1, 3], fill=hi + (255,))                # 윗면 반짝
        d.rectangle([2, CH - 4, 2 + w - 1, CH - 3], fill=lo + (255,))      # 아랫면 그늘
    for k in range(1, 10):                                                 # 10% 눈금
        x = 2 + round((CW - 4) * k / 10)
        d.line([(x, 2), (x, CH - 3)], fill=(0, 0, 0, 70))
    return im


def export(pack):
    rows = (STEPS + COLS - 1) // COLS
    sheet = Image.new("RGBA", (CW * COLS, CH * rows), (0, 0, 0, 0))
    chars = []
    for r in range(rows):
        line = ""
        for c in range(COLS):
            i = r * COLS + c
            if i < STEPS:
                sheet.alpha_composite(bar(i), (c * CW, r * CH))
                line += chr(CH0 + i)
            else:
                line += "\u0000"
        chars.append(line)
    pack.png(f"assets/{H.NS}/textures/font/hpbar.png", sheet)
    pack.put(f"assets/{H.NS}/font/hpbar.json", {"providers": [
        {"type": "bitmap", "file": f"{H.NS}:font/hpbar.png", "height": 6, "ascent": 6, "chars": chars}]})
    return [chr(CH0 + i) for i in range(STEPS)]
