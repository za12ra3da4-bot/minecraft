"""메뉴 창 배경 (상자 GUI 위에 폰트 글리프로 덮는다) — assets/oly/textures/gui/*.png + font oly:gui

바닐라 상자 텍스처(generic_54)는 건드리지 않는다 → 일반 상자는 그대로, 올림포스 메뉴만 바뀐다.
창 크기 = 176 x (114 + 18 x 줄수). 슬롯 자리는 바닐라와 1픽셀까지 같다:
  메뉴 칸 (8 + 18c, 18 + 18r), 내 인벤토리 (8 + 18c, 32 + 18R + 18r), 핫바 (8 + 18c, 90 + 18R)
  (R = 메뉴 줄 수, 좌표는 16x16 안쪽의 왼쪽 위)

- main6 : 올림포스 메뉴 (6줄) — 신전 정면. 박공의 메달(4), 기둥머리 버튼(19~25), 기둥의 명판(31), 기단의 닫기(49)
- grid3 / grid4 / grid6 : 다른 메뉴 — 대리석 판 + 오목한 슬롯
"""
import math
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "resourcepack", "olympus_pack", "assets", "oly")
rng = np.random.default_rng(5)

W = 176
C = lambda *v: np.array(v + ((255,) if len(v) == 3 else ()), dtype=float)  # noqa: E731

OUT = C(46, 32, 22)
MARBLE = [C(176, 166, 150), C(206, 198, 182), C(228, 221, 206), C(243, 238, 226), C(252, 250, 244)]
BRONZE = [C(74, 46, 20), C(118, 76, 34), C(164, 112, 52), C(206, 156, 78), C(242, 208, 128)]
GOLD = [C(110, 76, 14), C(170, 124, 26), C(222, 176, 56), C(248, 220, 110), C(255, 248, 196)]
RED = [C(70, 16, 12), C(118, 28, 20), C(156, 44, 30)]
SLOT_IN = C(120, 110, 98)
SLOT_DK = C(78, 68, 58)
SLOT_LT = C(250, 246, 236)


class Canvas:
    def __init__(self, h):
        self.h = h
        self.a = np.zeros((h, W, 4))

    def px(self, x, y, c):
        if 0 <= x < W and 0 <= y < self.h:
            self.a[y, x] = c

    def rect(self, x0, y0, x1, y1, c):
        self.a[max(0, y0):min(self.h, y1), max(0, x0):min(W, x1)] = c

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y + 1, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x + 1, y1, c)

    def save(self, name):
        p = os.path.join(ROOT, "textures", "gui", name + ".png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        Image.fromarray(np.clip(self.a, 0, 255).astype(np.uint8), "RGBA").save(p, optimize=True)
        return p


def marble_fill(cv, x0, y0, x1, y1, seed=0):
    """대리석: 부드러운 톤 + 가는 결 (디더링 4단)"""
    h, w = y1 - y0, x1 - x0
    r = np.random.default_rng(seed)
    base = r.random((h // 6 + 3, w // 6 + 3))
    ys, xs = np.mgrid[0:h, 0:w] / 6.0
    x0i, y0i = xs.astype(int), ys.astype(int)
    fx, fy = xs - x0i, ys - y0i
    v = (base[y0i, x0i] * (1 - fx) + base[y0i, x0i + 1] * fx) * (1 - fy) + (base[y0i + 1, x0i] * (1 - fx) + base[y0i + 1, x0i + 1] * fx) * fy
    vein = np.abs(np.sin((xs * 0.9 + ys * 1.7) + v * 5.5))
    t = 0.55 + (v - 0.5) * 0.35
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    for yy in range(h):
        for xx in range(w):
            tt = t[yy, xx] + (bayer[yy % 4, xx % 4] - 0.5) * 0.18
            idx = 3 if tt > 0.62 else 2 if tt > 0.42 else 1
            c = MARBLE[idx]
            if vein[yy, xx] < 0.06:
                c = MARBLE[1]
            cv.px(x0 + xx, y0 + yy, c)


def bevel_frame(cv, x0, y0, x1, y1, ramp, thick=3):
    """청동/금 테두리: 바깥 어두운 선, 왼쪽 위 밝게, 오른쪽 아래 어둡게"""
    for i in range(thick):
        c_tl = ramp[3 - min(i, 1)] if i < thick - 1 else ramp[2]
        c_br = ramp[1] if i < thick - 1 else ramp[2]
        cv.hline(x0 + i, x1 - i, y0 + i, c_tl)
        cv.vline(x0 + i, y0 + i, y1 - i, c_tl)
        cv.hline(x0 + i, x1 - i, y1 - 1 - i, c_br)
        cv.vline(x1 - 1 - i, y0 + i, y1 - i, c_br)
    cv.hline(x0 + 1, x1 - 1, y0, OUT)
    cv.hline(x0 + 1, x1 - 1, y1 - 1, OUT)
    cv.vline(x0, y0 + 1, y1 - 1, OUT)
    cv.vline(x1 - 1, y0 + 1, y1 - 1, OUT)
    cv.px(x0 + 1, y0 + 1, ramp[4])


def slot(cv, sx, sy, kind="plain"):
    """(sx, sy) = 16x16 안쪽의 왼쪽 위. 바닐라처럼 오목하게 (위·왼쪽 어둡고 아래·오른쪽 밝게)"""
    x0, y0 = sx - 1, sy - 1
    if kind in ("gold", "bronze"):
        ramp = GOLD if kind == "gold" else BRONZE
        # 바깥 장식 테 (슬롯 둘레 1px 더)
        cv.rect(x0 - 1, y0 - 1, x0 + 19, y0 + 19, OUT)
        cv.rect(x0, y0, x0 + 18, y0 + 18, ramp[2])
        cv.hline(x0, x0 + 18, y0, ramp[4])
        cv.vline(x0, y0, y0 + 18, ramp[3])
        cv.hline(x0, x0 + 18, y0 + 17, ramp[0])
        cv.vline(x0 + 17, y0, y0 + 18, ramp[1])
        for (cx, cy) in ((x0, y0), (x0 + 17, y0), (x0, y0 + 17), (x0 + 17, y0 + 17)):
            cv.px(cx, cy, ramp[4] if (cx, cy) == (x0, y0) else ramp[0])
    cv.hline(x0 + 1, x0 + 17, y0 + 1, SLOT_DK)
    cv.vline(x0 + 1, y0 + 1, y0 + 17, SLOT_DK)
    cv.hline(x0 + 1, x0 + 17, y0 + 16, SLOT_LT)
    cv.vline(x0 + 16, y0 + 1, y0 + 17, SLOT_LT)
    cv.rect(x0 + 2, y0 + 2, x0 + 16, y0 + 16, SLOT_IN)
    # 안쪽 은은한 그라디언트
    for i in range(14):
        cv.hline(x0 + 2, x0 + 16, y0 + 2 + i, SLOT_IN * (0.93 + 0.07 * i / 13) if i else SLOT_IN * 0.88)
    for i in range(14):
        cv.a[y0 + 2 + i, x0 + 2 + 13 if i else x0 + 2, 3] = 255


def meander(cv, x0, x1, y, ramp=GOLD, bg=RED):
    """그리스 메안더(뇌문) 띠, 높이 7"""
    cv.rect(x0, y, x1, y + 7, bg[1])
    cv.hline(x0, x1, y, OUT)
    cv.hline(x0, x1, y + 6, OUT)
    unit = ["#####.", "#...#.", "#.#.#.", "#.###.", "#.....", "######"]
    for x in range(x0, x1):
        k = (x - x0) % 6
        for yy in range(5):
            ch = unit[yy][k] if yy < 5 else "#"
            if ch == "#":
                cv.px(x, y + 1 + yy, ramp[3] if yy < 2 else ramp[2])


def rosette(cv, cx, cy, ramp=GOLD):
    for dx, dy in ((0, -2), (2, 0), (0, 2), (-2, 0)):
        cv.px(cx + dx, cy + dy, ramp[3])
    for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        cv.px(cx + dx, cy + dy, ramp[2])
    cv.px(cx, cy, ramp[4])


def window(rows, seed):
    """공통 창 틀 + 대리석 + 아래쪽 내 인벤토리(오목 슬롯). 메뉴 칸 영역은 부르는 쪽이 그린다"""
    h = 114 + 18 * rows
    cv = Canvas(h)
    # 둥근 모서리 창
    marble_fill(cv, 0, 0, W, h, seed)
    bevel_frame(cv, 0, 0, W, h, BRONZE, 3)
    for (x, y) in ((0, 0), (W - 1, 0), (0, h - 1), (W - 1, h - 1)):
        cv.px(x, y, C(0, 0, 0, 0)[:4] * 0)
    for (x, y) in ((3, 3), (W - 4, 3), (3, h - 4), (W - 4, h - 4)):
        rosette(cv, x + (2 if x < 10 else -2), y + (2 if y < 10 else -2))
    # 내 인벤토리 위 띠 (라벨 '인벤토리' 가 여기 뜬다 → 밝은 대리석 판)
    by = 17 + 18 * rows
    # '인벤토리' 글자가 y = 창높이 - 94 에 뜨므로 밝은 명판으로 비워 둔다. 오른쪽 끝만 메안더
    cv.hline(5, W - 5, by + 1, BRONZE[2])
    cv.hline(5, W - 5, by + 2, OUT)
    meander(cv, 96, W - 6, by + 4)
    cv.hline(5, W - 5, by + 12, OUT)
    cv.hline(5, W - 5, by + 13, BRONZE[3])
    top_inv = 32 + 18 * rows
    for r in range(3):
        for c in range(9):
            slot(cv, 8 + 18 * c, top_inv + 18 * r)
    hot = 90 + 18 * rows
    cv.rect(6, hot - 3, W - 6, hot - 2, BRONZE[1])
    for c in range(9):
        slot(cv, 8 + 18 * c, hot)
    return cv


def grid(rows):
    cv = window(rows, 10 + rows)
    for r in range(rows):
        for c in range(9):
            slot(cv, 8 + 18 * c, 18 + 18 * r)
    return cv


def main6():
    """올림포스 메뉴 — 신전 정면. 메뉴 칸 영역 y 17..125"""
    rows = 6
    cv = window(rows, 42)
    top, bot = 17, 17 + 18 * rows
    # 하늘 대신 깊은 붉은 벽 (신전 안쪽)
    for y in range(top, bot):
        t = (y - top) / (bot - top)
        col = RED[2] * (1 - t) + RED[0] * t
        cv.rect(5, y, W - 5, y + 1, col)
    # 박공 (삼각 지붕) — 꼭짓점은 제목 줄 위, 밑변 y=40
    apex = (88, 4)
    for y in range(apex[1], 41):
        half = int((y - apex[1]) * 2.2)
        x0, x1 = 88 - half, 88 + half
        x0, x1 = max(6, x0), min(W - 6, x1)
        cv.rect(x0, y, x1, y + 1, MARBLE[2] if y > apex[1] + 2 else MARBLE[3])
        cv.px(x0, y, OUT)
        cv.px(x1 - 1, y, OUT)
        cv.px(x0 + 1, y, MARBLE[4])
    # 박공 안쪽(팀파눔) 금빛 부조 선
    for y in range(12, 38):
        half = int((y - 9) * 2.2) - 5
        if half > 0:
            cv.px(88 - half, y, GOLD[2])
            cv.px(88 + half - 1, y, GOLD[1])
    # 엔타블러처 (y 40..52): 코니스 + 메안더
    cv.rect(5, 38, W - 5, 42, MARBLE[3])
    cv.hline(5, W - 5, 38, OUT)
    cv.hline(5, W - 5, 41, MARBLE[1])
    meander(cv, 5, W - 5, 43)
    cv.rect(5, 50, W - 5, 53, MARBLE[2])
    cv.hline(5, W - 5, 52, OUT)
    # 기둥 7개 (버튼 칸 19~25 = c 1..7) — 기둥머리가 버튼 칸, 아래로 세로 홈
    for c in range(1, 8):
        sx = 8 + 18 * c
        # 기둥 몸통 y 72..~110 (기단 위)
        for y in range(71, bot - 20):
            cv.rect(sx + 1, y, sx + 15, y + 1, MARBLE[2])
            for fx in (sx + 3, sx + 7, sx + 11):
                cv.px(fx, y, MARBLE[0])
                cv.px(fx + 1, y, MARBLE[4])
            cv.px(sx + 1, y, MARBLE[4])
            cv.px(sx + 14, y, MARBLE[0])
            cv.px(sx, y, OUT)
            cv.px(sx + 15, y, OUT)
        # 이오니아식 소용돌이 (기둥머리 양옆)
        for side in (-1, 1):
            cx = sx + (1 if side < 0 else 14) + side * 2
            cy = 56
            for a in range(0, 360, 30):
                cv.px(cx + round(math.cos(math.radians(a)) * 2), cy + round(math.sin(math.radians(a)) * 2), GOLD[2])
            cv.px(cx, cy, GOLD[4])
        slot(cv, sx, 54, "gold")
    # 기단 (계단 3단) y bot-20 .. bot
    for i, y in enumerate(range(bot - 20, bot, 6)):
        x0 = 5 + max(0, 2 - i) * 4
        cv.rect(x0, y, W - x0, y + 6, MARBLE[3 - (i % 2)])
        cv.hline(x0, W - x0, y, MARBLE[4])
        cv.hline(x0, W - x0, y + 5, MARBLE[0])
    # 메달 (4) — 팀파눔 가운데
    slot(cv, 8 + 18 * 4, 18, "gold")
    # 명판 (31) — 가운데 기둥에 박힌 청동판
    slot(cv, 8 + 18 * 4, 18 + 18 * 3, "bronze")
    # 닫기 (49) — 기단 가운데
    slot(cv, 8 + 18 * 4, 18 + 18 * 5, "bronze")
    # 메뉴 칸 둘레 테
    cv.vline(4, top, bot, OUT)
    cv.vline(W - 5, top, bot, OUT)
    return cv


GLYPHS = {  # 글리프 → (파일, 줄 수)
    "": ("menu_main", 6),
    "": ("menu_grid3", 3),
    "": ("menu_grid4", 4),
    "": ("menu_grid6", 6),
}


def build():
    main6().save("menu_main")
    for r in (3, 4, 6):
        grid(r).save(f"menu_grid{r}")
    providers = [{"type": "minecraft:space", "advances": {"": -8, "": -169}}]
    for ch, (f, rows) in GLYPHS.items():
        providers.append({"type": "minecraft:bitmap", "file": f"oly:gui/{f}.png",
                          "ascent": 13, "height": 114 + 18 * rows, "chars": [ch]})
    import json
    p = os.path.join(ROOT, "font", "gui.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump({"providers": providers}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


if __name__ == "__main__":
    build()
    print("gui ok")
