"""32x32 픽셀아트 — 픽셀을 한 줄씩 직접 찍어 만든 무기 · 스킬 효과 · 마법진

 표기: 스프라이트마다 팔레트(글자 → 색)와 '찍기' 목록.
   put(x, y, "문자열")   : (x, y) 부터 오른쪽으로 한 글자씩 찍음  ('.' = 건너뜀)
   dg(y, k, "문자열")    : 대각선 무기 축(x + y = 31)에서 k 칸 옆부터 찍음 (x = 31 - y + k)
 무기는 마인크래프트 손 아이템처럼 왼쪽 아래 손잡이 → 오른쪽 위 끝.
"""
from PIL import Image

O = (22, 16, 28, 255)
T = None


class Sprite:
    def __init__(self, pal, n=32):
        self.n = n
        self.pal = dict(pal)
        self.pal.setdefault("o", O)
        self.px = {}

    def put(self, x, y, s):
        for i, ch in enumerate(s):
            if ch == ".":
                continue
            if ch == " ":
                self.px.pop((x + i, y), None)
                continue
            if 0 <= x + i < self.n and 0 <= y < self.n:
                self.px[(x + i, y)] = ch

    def dg(self, y, k, s):
        self.put(31 - y + k, y, s)

    def rows(self, y0, lines, x0=0):
        for j, line in enumerate(lines):
            self.put(x0, y0 + j, line)

    def image(self):
        im = Image.new("RGBA", (self.n, self.n), (0, 0, 0, 0))
        for (x, y), ch in self.px.items():
            c = self.pal[ch]
            im.putpixel((x, y), c if len(c) == 4 else c + (255,))
        return im


# ─────────────────────────────────────────── 공통 팔레트
STEEL = {"W": (244, 250, 255), "L": (196, 206, 222), "M": (146, 156, 178), "D": (96, 104, 128)}
GOLD = {"g": (255, 226, 120), "G": (222, 164, 44), "d": (150, 96, 22)}
LEATHER = {"l": (132, 82, 48), "k": (86, 50, 28)}
WOOD = {"w": (150, 102, 60), "v": (98, 62, 34)}


def P(*ds):
    out = {}
    for d in ds:
        out.update(d)
    return out


# ═══════════════════════════════════════════ 무기 8종
def thunder():
    """폭풍의 검 — 푸른 룬이 새겨진 롱소드, 금 가드, 사파이어"""
    s = Sprite(P(STEEL, GOLD, LEATHER, {"b": (110, 200, 255), "B": (40, 120, 230), "s": (40, 90, 230), "S": (170, 220, 255)}))
    s.dg(0, -1, "oo")
    s.dg(1, -2, "oWo")
    s.dg(2, -2, "oWLo")
    s.dg(3, -2, "oWLMo")
    s.dg(4, -2, "oWLMDo")
    s.dg(5, -2, "oWbMDo")
    s.dg(6, -2, "oWLBDo")
    s.dg(7, -2, "oWbMDo")
    s.dg(8, -2, "oWLMDo")
    s.dg(9, -2, "oWbBDo")
    s.dg(10, -2, "oWLMDo")
    s.dg(11, -2, "oWbMDo")
    s.dg(12, -2, "oWLBDo")
    s.dg(13, -2, "oWbMDo")
    s.dg(14, -2, "oWLMDo")
    s.dg(15, -2, "oWbBDo")
    s.dg(16, -2, "oWLMDo")
    s.dg(17, -2, "oWLMDo")
    # 손잡이 (가죽 감기)
    s.dg(20, -2, "olklo")
    s.dg(21, -2, "oklko")
    s.dg(22, -2, "olklo")
    s.dg(23, -2, "oklko")
    s.dg(24, -2, "olklo")
    # 가드 (축에 수직, 금)
    s.put(7, 13, "oo")
    s.put(7, 14, "ogGo")
    s.put(8, 15, "ogGo")
    s.put(9, 16, "ogGo")
    s.put(10, 17, "ogG")
    s.put(11, 18, "ogSGo")
    s.put(12, 19, "ogsGo")
    s.put(13, 20, "ogGo")
    s.put(14, 21, "ogGo")
    s.put(15, 22, "oddo")
    s.put(16, 23, "oo")
    # 폼멜
    s.put(4, 25, "ogGo")
    s.put(3, 26, "ogSdo")
    s.put(3, 27, "oGsdo")
    s.put(4, 28, "ooo")
    return s


def dragon():
    """처형자의 도끼 — 넓은 초승달 도끼날, 뒷날 가시, 루비, 가죽 감은 자루"""
    s = Sprite(P(STEEL, GOLD, LEATHER, WOOD, {"r": (255, 90, 50), "R": (200, 20, 40), "Q": (255, 150, 150)}))
    s.dg(3, 0, "oo")
    s.dg(4, -1, "oMLo")
    s.dg(5, -1, "oMLo")
    s.dg(6, -1, "oDMo")
    for y in range(7, 18):
        s.dg(y, -1, "owvo")
    for y in range(18, 25):
        s.dg(y, -1, "olko" if y % 2 else "oklo")
    for y in range(25, 28):
        s.dg(y, -1, "owvo")
    s.dg(28, -1, "oGdo")
    s.dg(29, 0, "oo")
    # 도끼날 (축 왼쪽 위로 넓게)
    s.put(24, 4, "o")
    s.put(23, 5, "oW")
    s.put(21, 6, "oWL")
    s.put(18, 7, "oWLLMD")
    s.put(15, 8, "oWLLMMDD")
    s.put(13, 9, "oWLLrMMDD")
    s.put(11, 10, "oWLLLrMMDR")
    s.put(10, 11, "oWLLrrMMDQ")
    s.put(9, 12, "oWLLLMMMDR")
    s.put(9, 13, "oWLLMMDDD")
    s.put(10, 14, "oWLMMDD")
    s.put(11, 15, "oWMDo")
    s.put(12, 16, "oWo")
    # 뒷날 가시
    s.put(24, 9, "DMo")
    s.put(23, 10, "DMLMo")
    s.put(22, 11, "DMo")
    return s


def wind():
    """질풍의 단검 — 휘어진 은빛 단검, 깃털 가드, 에메랄드"""
    s = Sprite(P(STEEL, {"e": (90, 255, 170), "E": (20, 160, 90), "n": (40, 110, 80), "N": (22, 70, 50), "f": (236, 240, 248), "F": (170, 180, 200)}))
    s.dg(5, 1, "oo")
    s.dg(6, -1, "oWLo")
    s.dg(7, -2, "oWLMo")
    s.dg(8, -2, "oWeMo")
    s.dg(9, -2, "oWLMo")
    s.dg(10, -2, "oWeMo")
    s.dg(11, -2, "oWLMo")
    s.dg(12, -2, "oWeMo")
    s.dg(13, -2, "oWLMo")
    s.dg(14, -2, "oWLDo")
    # 깃털 가드
    s.put(9, 12, "oo")
    s.put(8, 13, "ofFo")
    s.put(9, 14, "ofFFo")
    s.put(10, 15, "offFo")
    s.put(12, 16, "oFfLLo")
    s.put(13, 17, "oLEeMo")
    s.put(14, 18, "oMLffo")
    s.put(16, 19, "oFffo")
    s.put(17, 20, "oFFfo")
    s.put(19, 21, "oFfo")
    s.put(20, 22, "oo")
    # 손잡이 · 폼멜
    s.dg(19, -2, "onNno")
    s.dg(20, -2, "oNnNo")
    s.dg(21, -2, "onNno")
    s.dg(22, -2, "oNnNo")
    s.put(6, 23, "oLMo")
    s.put(5, 24, "oLeEo")
    s.put(5, 25, "oMEDo")
    s.put(6, 26, "ooo")
    return s


def phoenix():
    """성기사의 망치 — 금테 두른 강철 망치머리, 태양 문장 토파즈, 강철 자루"""
    s = Sprite(P(STEEL, GOLD, LEATHER, {"t": (255, 200, 60), "T": (255, 250, 200), "h": (78, 84, 104), "H": (50, 54, 70)}))
    # 머리 (축에 수직으로 긴 강철 덩어리)
    s.put(23, 1, "oo")
    s.put(21, 2, "oLLo")
    s.put(19, 3, "oWLgLo")
    s.put(18, 4, "oWLgtgMo")
    s.put(19, 5, "oLgTtgMDo")
    s.put(20, 6, "oLgtgMDDo")
    s.put(21, 7, "oMgMDDo")
    s.put(22, 8, "oMDDo")
    s.put(24, 9, "oo")
    s.put(25, 2, "oo")
    s.put(26, 3, "oMo")
    s.put(27, 4, "oDo")
    s.put(28, 5, "oo")
    # 금 테두리 (머리 양 끝)
    s.put(17, 5, "og")
    s.put(18, 6, "oG")
    s.put(29, 3, "o")
    # 자루
    for y in range(9, 30):
        if 18 <= y <= 24:
            s.dg(y, -1, "olko" if y % 2 else "oklo")
        else:
            s.dg(y, -1, "ohHo")
    s.dg(12, -2, "oggGo")
    s.dg(17, -2, "oggGo")
    s.dg(25, -2, "oggGo")
    s.dg(29, -1, "oGdo")
    s.dg(30, 0, "oo")
    return s


def blackiron():
    """흑기사의 대검 — 넓고 톱니진 검은 날, 붉은 룬, 뿔 가드, 루비"""
    s = Sprite({"W": (150, 150, 170), "L": (104, 104, 124), "M": (74, 74, 92), "D": (46, 46, 60), "r": (255, 60, 50), "R": (160, 10, 20),
                "h": (60, 58, 70), "H": (34, 32, 42), "q": (220, 30, 50), "Q": (255, 160, 160), "l": (110, 24, 30), "k": (70, 14, 18)})
    s.dg(0, 0, "oo")
    s.dg(1, -1, "oWo")
    s.dg(2, -2, "oWLo")
    s.dg(3, -3, "oWLMo")
    for y in range(4, 17):
        rune = "r" if y % 3 else "R"
        notch = "o" if y % 2 else " "
        s.dg(y, -4, "oWL" + rune + "MDo")
        if y % 2 == 0:
            s.dg(y, -5, "o")
    s.dg(17, -4, "oWLMMDo")
    # 뿔 가드
    s.put(5, 11, "oo")
    s.put(5, 12, "ohHo")
    s.put(6, 13, "ohHo")
    s.put(7, 14, "ohHo")
    s.put(8, 15, "ohhHo")
    s.put(9, 16, "ohhHo")
    s.put(10, 17, "ohh")
    s.put(11, 18, "ohQqHo")
    s.put(12, 19, "ohqHHo")
    s.put(14, 20, "ohHo")
    s.put(16, 21, "ohHo")
    s.put(18, 22, "ohHo")
    s.put(20, 23, "oo")
    # 손잡이 · 폼멜
    s.dg(20, -2, "olklo")
    s.dg(21, -2, "oklko")
    s.dg(22, -2, "olklo")
    s.dg(23, -2, "oklko")
    s.put(4, 24, "ohHo")
    s.put(3, 25, "ohQqo")
    s.put(3, 26, "oHqRo")
    s.put(4, 27, "ooo")
    return s


def tiger():
    """늑대 발톱 — 털 소매 건틀릿, 판금 손등, 강철 발톱 셋"""
    s = Sprite(P(STEEL, LEATHER, {"f": (240, 236, 226), "F": (196, 188, 172), "a": (190, 110, 255), "A": (120, 50, 200)}))
    # 털 소매
    s.rows(22, [
        ".....oooo",
        "...oofFfFoo",
        "..ofFfFfFfFo",
        ".ofFfFfFfFfo",
        ".oFfFfFfFfo",
        "..oFfFfFfo",
        "...oFfFoo",
        "....ooo",
    ], x0=0)
    # 가죽 팔목 · 판금 손등
    s.rows(14, [
        ".........oooo",
        "........oDMLo",
        ".......olDMLLo",
        "......olkDMLWo",
        ".....olklDaMLo",
        "....olklkMAMLo",
        "....oklklDMLo",
        "....olklkDMo",
        ".....oklklo",
        "......oooo",
    ], x0=6)
    # 발톱 셋 (대각선 위로)
    for j, (x, y) in enumerate(((19, 13), (21, 15), (23, 17))):
        s.put(x, y, "oLo")
        s.put(x + 1, y - 1, "oWo")
        s.put(x + 2, y - 2, "oLo")
        s.put(x + 3, y - 3, "oWo")
        s.put(x + 4, y - 4, "oLo")
        s.put(x + 5, y - 5, "oWo")
        s.put(x + 6, y - 6, "oo")
    return s


def staff():
    """대마법사의 지팡이 — 비틀린 나무, 금 갈퀴, 빛나는 자수정 구슬"""
    s = Sprite(P(GOLD, WOOD, {"p": (230, 170, 255), "P": (170, 80, 240), "q": (110, 30, 180), "Z": (255, 240, 255)}))
    # 구슬 (오른쪽 위)
    s.rows(1, [
        "......oooo",
        "....ooPPPPoo",
        "...oPpZpPPqo",
        "..oPpZZpPPqo",
        "..oPppPPPqqo",
        "..oPPPPPqqqo",
        "...oPPPqqqo",
        "....ooqqoo",
        "......oo",
    ], x0=20)
    # 금 갈퀴
    s.put(19, 5, "og")
    s.put(18, 6, "ogG")
    s.put(18, 7, "oGgo")
    s.put(19, 8, "oGgG")
    s.put(20, 9, "oGgGo")
    s.put(22, 10, "oGdo")
    s.put(29, 5, "go")
    s.put(29, 7, "Go")
    s.put(27, 9, "gGo")
    # 자루 (비틀림: 명암 번갈아)
    for y in range(10, 31):
        s.dg(y, -1, "owvo" if (y // 2) % 2 else "ovwo")
    s.dg(13, -2, "oggGo")
    s.dg(20, -2, "oggGo")
    s.dg(27, -2, "oggGo")
    return s


def peachwood():
    """불사조의 창 — 불꽃 모양 금 창날, 강철 끝, 붉은 리본, 루비"""
    s = Sprite(P(STEEL, GOLD, WOOD, {"c": (220, 40, 40), "C": (140, 16, 24), "r": (255, 80, 60), "R": (180, 20, 30), "F": (255, 160, 60)}))
    s.dg(0, 0, "oo")
    s.dg(1, -1, "oWo")
    s.dg(2, -1, "oWLo")
    s.dg(3, -2, "oWLMo")
    s.dg(4, -2, "oWLMo")
    s.dg(5, -2, "oWFMo")
    # 불꽃 금 날개
    s.put(20, 5, "oo")
    s.put(20, 6, "ogGo")
    s.put(21, 7, "oggGo")
    s.put(20, 8, "ogFgGo")
    s.put(20, 9, "ogGRgo")
    s.put(29, 6, "oo")
    s.put(28, 7, "oGo")
    s.put(27, 8, "oGdo")
    s.put(26, 9, "oGdo")
    s.put(22, 10, "ogrGdo")
    s.put(23, 11, "oGdo")
    s.dg(6, -2, "oWLMo")
    s.dg(7, -1, "oLMo")
    # 자루
    for y in range(12, 30):
        s.dg(y, -1, "owvo")
    s.dg(12, -2, "oggGo")
    s.dg(29, -1, "oGdo")
    s.dg(30, 0, "oo")
    # 붉은 리본 (자루에서 휘날림)
    s.put(15, 13, "occo")
    s.put(13, 14, "occCo")
    s.put(11, 15, "occCo")
    s.put(10, 16, "ocCo")
    s.put(9, 17, "oCo")
    s.put(9, 18, "oo")
    s.put(20, 14, "ocCo")
    s.put(21, 15, "occCo")
    s.put(23, 16, "ocCo")
    s.put(24, 17, "oCo")
    s.put(25, 18, "oo")
    return s


WEAPONS = {"thunder": thunder, "dragon": dragon, "wind": wind, "phoenix": phoenix,
           "blackiron": blackiron, "tiger": tiger, "staff": staff, "peachwood": peachwood}


def preview(path, sprites, scale=8, bg=(60, 56, 64)):
    ims = [f().image() for f in sprites]
    W = Image.new("RGBA", (len(ims) * (32 * scale + 16) + 16, 32 * scale + 32), bg + (255,))
    for i, im in enumerate(ims):
        W.alpha_composite(im.resize((32 * scale, 32 * scale), Image.NEAREST), (16 + i * (32 * scale + 16), 16))
    W.convert("RGB").save(path)


# ═══════════════════════════════════════════ 상점 GUI (3줄 상자, GUI 픽셀 1:1 = 176 x 168)
def shop_gui():
    W, H = 176, 168
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = im.load()

    def p(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            px[x, y] = c + (255,) if len(c) == 3 else c

    def hline(x0, x1, y, c):
        for x in range(x0, x1 + 1):
            p(x, y, c)

    def vline(x, y0, y1, c):
        for y in range(y0, y1 + 1):
            p(x, y, c)
    OUT = (34, 20, 10)
    GD, GM, GL, GH = (120, 76, 22), (190, 136, 48), (232, 184, 84), (255, 234, 150)
    # 바탕 (어두운 남보라)
    for y in range(H):
        for x in range(W):
            t = y / H
            p(x, y, (int(26 - 8 * t), int(22 - 6 * t), int(30 - 6 * t)))
    # 붉은 상단 띠 (위쪽 물결 가장자리 + 세로 그라데이션)
    for y in range(4, 16):
        for x in range(4, W - 4):
            wave = 5 + (1 if (x // 3) % 4 == 0 else 0) + (1 if (x // 7) % 5 == 2 else 0)
            if y < wave:
                continue
            t = (y - 4) / 12
            p(x, y, (int(150 - 60 * t), int(26 - 12 * t), int(30 - 14 * t)))
    # 그리스 문양 (띠 오른쪽, 금)
    def meander(x0, y0, n, col, sh):
        pat = ["#######.", "#.....#.", "#.###.#.", "#.#...#.", "#.#####."]
        for k in range(n):
            for j, row in enumerate(pat):
                for i, ch in enumerate(row):
                    if ch == "#":
                        p(x0 + k * 8 + i, y0 + j, col)
                        p(x0 + k * 8 + i + 1, y0 + j + 1, sh) if (i + 1 < 8 and row[i + 1] == ".") else None
    meander(W - 76, 8, 8, GL, GD)
    # 칸 (금 둥근 테두리 + 안쪽 어둠 + 윗줄 반사)
    def slot(x0, y0, rich):
        for y in range(18):
            for x in range(18):
                edge = x in (0, 17) or y in (0, 17)
                corner = (x in (0, 17)) and (y in (0, 17))
                if corner:
                    continue
                if edge:
                    c = GL if (y == 0 or x == 0) else GD
                    if not rich:
                        c = (150, 108, 52) if (y == 0 or x == 0) else (84, 56, 26)
                    p(x0 + x, y0 + y, c)
                elif x in (1, 16) or y in (1, 16):
                    p(x0 + x, y0 + y, (14, 10, 14) if rich else (20, 16, 20))
                else:
                    t = (y - 2) / 14
                    base = (int(34 - 14 * t), int(30 - 12 * t), int(40 - 14 * t))
                    if y == 2 and 3 <= x <= 14:
                        base = (58, 52, 66)
                    p(x0 + x, y0 + y, base)
        if rich:
            p(x0 + 1, y0 + 1, GH)
    for r in range(3):
        for c in range(9):
            slot(7 + c * 18, 17 + r * 18, True)
    # 양피지 띠 (찢긴 가장자리 + 그리스 문양)
    for y in range(71, 83):
        for x in range(4, W - 4):
            top = 71 + ((x * 7) % 5 == 0) + ((x * 13) % 11 == 0)
            bot = 82 - ((x * 5) % 7 == 0)
            if y < top or y > bot:
                continue
            n = ((x * 31 + y * 17) % 13) / 13
            p(x, y, (int(222 - 24 * n), int(204 - 26 * n), int(160 - 30 * n)))
    meander(W - 76, 74, 8, GM, GD)
    # 플레이어 인벤토리 · 단축바 (얇은 금선 칸)
    def grid_slot(x0, y0):
        for y in range(18):
            for x in range(18):
                if x in (0, 17) or y in (0, 17):
                    p(x0 + x, y0 + y, (104, 72, 34) if (x == 0 or y == 0) else (60, 40, 20))
                else:
                    p(x0 + x, y0 + y, (22, 18, 24) if (x + y) % 2 else (24, 20, 26))
    for r in range(3):
        for c in range(9):
            grid_slot(7 + c * 18, 83 + r * 18)
    for c in range(9):
        grid_slot(7 + c * 18, 141)
    # 금 액자 (4줄) + 모서리 리벳
    for i, c in enumerate((OUT, GD, GL, GM)):
        hline(i, W - 1 - i, i, c if i != 2 else GH)
        hline(i, W - 1 - i, H - 1 - i, c if i != 2 else GD)
        vline(i, i, H - 1 - i, c if i != 2 else GH)
        vline(W - 1 - i, i, H - 1 - i, c if i != 2 else GD)
    for (cx, cy) in ((3, 3), (W - 4, 3), (3, H - 4), (W - 4, H - 4)):
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                d = dx * dx + dy * dy
                if d <= 10:
                    p(cx + dx, cy + dy, OUT if d > 6 else (GH if dx + dy < -1 else (GL if dx + dy < 2 else GD)))
    return im


# ─────────────────────────────────────────── 다시 찍은 무기 3종
def wind():
    """질풍의 단검 — 짧고 날렵한 은빛 날(초록 바람 룬), 휜 은 가드, 초록 가죽, 에메랄드"""
    s = Sprite(P(STEEL, {"e": (110, 255, 180), "E": (20, 170, 100), "n": (50, 130, 90), "N": (26, 80, 56), "s": (40, 200, 120), "S": (190, 255, 220)}))
    s.dg(6, 0, "oo")
    s.dg(7, -1, "oWo")
    s.dg(8, -2, "oWLo")
    s.dg(9, -2, "oWLMo")
    s.dg(10, -2, "oWeMo")
    s.dg(11, -2, "oWLMo")
    s.dg(12, -2, "oWeDo")
    s.dg(13, -2, "oWLMo")
    s.dg(14, -2, "oWeMo")
    s.dg(15, -2, "oWLDo")
    s.dg(16, -2, "oWLMo")
    # 휜 가드 (양끝이 날 쪽으로 휨)
    s.put(10, 13, "oo")
    s.put(10, 14, "oWo")
    s.put(10, 15, "oLMo")
    s.put(11, 16, "oLMo")
    s.put(12, 17, "oLSMo")
    s.put(13, 18, "oLsMo")
    s.put(15, 19, "oLMo")
    s.put(16, 20, "oLMo")
    s.put(17, 21, "oMWo")
    s.put(19, 22, "oo")
    # 손잡이 · 폼멜
    s.dg(20, -2, "onNno")
    s.dg(21, -2, "oNnNo")
    s.dg(22, -2, "onNno")
    s.put(6, 23, "oLMo")
    s.put(5, 24, "oLSEo")
    s.put(5, 25, "oMEDo")
    s.put(6, 26, "ooo")
    return s


def tiger():
    """늑대 발톱 — 금속 손잡이 위로 나란히 뻗은 휜 강철 발톱 셋 + 털 장식"""
    s = Sprite(P(STEEL, LEATHER, {"f": (240, 236, 226), "F": (196, 188, 172), "a": (200, 130, 255), "A": (120, 50, 200)}))
    for k0 in (-6, -1, 4):
        top = 4 + (k0 + 6) // 2
        for y in range(top, 16 + (k0 + 6) // 3):
            s.dg(y, k0, "oWLo" if y > top + 1 else ("oWo" if y == top + 1 else "oo"))
    # 손등 판 (축에 수직 막대)
    s.put(7, 14, "oo")
    s.put(7, 15, "oLMo")
    s.put(8, 16, "oLMMo")
    s.put(9, 17, "oLaMDo")
    s.put(10, 18, "oLAaMDo")
    s.put(12, 19, "oLMDDo")
    s.put(14, 20, "oMDDo")
    s.put(16, 21, "oDDo")
    s.put(18, 22, "oo")
    # 손잡이
    s.dg(21, -2, "olklo")
    s.dg(22, -2, "oklko")
    s.dg(23, -2, "olklo")
    # 털 술
    s.put(3, 24, "ofFfo")
    s.put(2, 25, "ofFfFfo")
    s.put(2, 26, "oFfFfo")
    s.put(3, 27, "oFfo")
    s.put(4, 28, "oo")
    return s


def phoenix():
    """성기사의 망치 — 큰 강철 망치머리(금테 · 태양 토파즈) + 강철 자루"""
    s = Sprite(P(STEEL, GOLD, LEATHER, {"t": (255, 200, 60), "T": (255, 250, 200), "h": (78, 84, 104), "H": (50, 54, 70)}))
    # 머리: 축(x+y=31) 둘레 회전 사각형 — p = x+y-31 (가로 폭), t = y-x (세로 길이)
    for y in range(0, 16):
        for x in range(12, 32):
            pp, tt = x + y - 31, y - x
            if abs(pp) <= 11 and -25 <= tt <= -17:
                edge = abs(pp) == 11 or tt in (-25, -17)
                rim = abs(pp) == 10 or tt in (-24, -18)
                if edge:
                    ch = "o"
                elif rim:
                    ch = "g" if (pp < 0 or tt == -26) else "G"
                else:
                    ch = "W" if pp <= -7 else ("L" if pp <= -2 else ("M" if pp <= 4 else "D"))
                s.put(x, y, ch)
    # 태양 문장 (가운데 토파즈)
    s.put(24, 6, "gtg")
    s.put(23, 7, "gtTtg")
    s.put(24, 8, "gtg")
    s.put(25, 5, "g")
    s.put(25, 9, "G")
    # 자루
    for y in range(8, 31):
        if 8 <= y <= 9:
            s.dg(y, -1, "ohHo")
            continue
        if 20 <= y <= 25:
            s.dg(y, -1, "olko" if y % 2 else "oklo")
        else:
            s.dg(y, -1, "ohHo")
    s.dg(10, -2, "oggGo")
    s.dg(16, -2, "oggGo")
    s.dg(26, -2, "oggGo")
    s.dg(30, -1, "oGdo")
    # 머리를 자루 위에 다시 (자루가 머리를 덮지 않게)
    for y in range(0, 12):
        for x in range(12, 32):
            pp, tt = x + y - 31, y - x
            if abs(pp) <= 11 and -25 <= tt <= -17:
                edge = abs(pp) == 11 or tt in (-25, -17)
                rim = abs(pp) == 10 or tt in (-24, -18)
                ch = "o" if edge else (("g" if (pp < 0 or tt == -24) else "G") if rim else ("W" if pp <= -7 else ("L" if pp <= -2 else ("M" if pp <= 4 else "D"))))
                s.put(x, y, ch)
    s.put(25, 3, "gtg")
    s.put(24, 4, "gtTtg")
    s.put(25, 5, "gtg")
    return s


WEAPONS.update({"wind": wind, "tiger": tiger, "phoenix": phoenix})


# ═══════════════════════════════════════════ 빛 효과 도우미 (픽셀 단위 색 단계 + 반투명 번짐)
def glow_sprite(core, pal, halo=(255, 255, 255), halo_a=(120, 60)):
    """core: {(x,y): 문자} → 주변 1~2칸에 반투명 번짐 픽셀을 찍은 이미지"""
    n = 32 if max(max(x, y) for x, y in core) < 32 else 64
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    for r, a in ((2, halo_a[1]), (1, halo_a[0])):
        for (x, y) in core:
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if abs(dx) + abs(dy) == r or (r == 1 and abs(dx) + abs(dy) <= 1):
                        X, Y = x + dx, y + dy
                        if 0 <= X < n and 0 <= Y < n and (X, Y) not in core and im.getpixel((X, Y))[3] < a:
                            im.putpixel((X, Y), halo + (a,))
    for (x, y), ch in core.items():
        c = pal[ch]
        im.putpixel((x, y), c + (255,) if len(c) == 3 else c)
    return im


def ring_cells(cx, cy, r0, r1):
    out = []
    for y in range(64):
        for x in range(64):
            d = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5
            if r0 <= d < r1:
                out.append((x, y, d))
    return out


def line_cells(x0, y0, x1, y1):
    """브레젠험 직선"""
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy
    return pts


import math as _m

RUNES = [["#.#", ".#.", "#.#"], ["###", "#..", "###"], [".#.", "###", ".#."], ["#..", "###", "..#"], ["##.", "#.#", ".##"], ["#.#", "###", "#.#"]]


def magic_circle(c1, c2, c3, seed=0, star=6):
    """64x64 마법진: 바깥 두 줄 고리 + 룬 띠 + 별 + 안쪽 고리 (색 3단계 + 번짐)"""
    core = {}
    for x, y, d in ring_cells(32, 32, 29.2, 30.6):
        core[(x, y)] = "A"
    for x, y, d in ring_cells(32, 32, 24.2, 25.2):
        core[(x, y)] = "B"
    for k in range(12):
        a = k / 12 * 2 * _m.pi + seed * 0.3
        cx, cy = 32 + _m.cos(a) * 27.3, 32 + _m.sin(a) * 27.3
        g = RUNES[(k + seed) % len(RUNES)]
        for j, row in enumerate(g):
            for i, ch in enumerate(row):
                if ch == "#":
                    core[(int(cx) - 1 + i, int(cy) - 1 + j)] = "A"
    pts = [(int(32 + _m.cos(k / star * 2 * _m.pi - _m.pi / 2) * 23), int(32 + _m.sin(k / star * 2 * _m.pi - _m.pi / 2) * 23)) for k in range(star)]
    step = 2 if star in (5, 6) else 3
    for k in range(star):
        for (x, y) in line_cells(*pts[k], *pts[(k + step) % star]):
            core[(x, y)] = "C"
    for x, y, d in ring_cells(32, 32, 9.2, 10.2):
        core[(x, y)] = "B"
    return glow_sprite(core, {"A": c1, "B": c2, "C": c3}, halo=c2, halo_a=(110, 45))


# ═══════════════════════════════════════════ 무기 스킬 효과 (32x32, 바닥에 깔림 — 위쪽 = 앞)
def fx_thunder():
    core = {}
    bolt = [(15, 1), (16, 2), (15, 3), (14, 4), (15, 5), (17, 6), (18, 7), (17, 8), (16, 9), (15, 10), (14, 11), (15, 12), (17, 13), (19, 14), (18, 15),
            (17, 16), (15, 17), (14, 18), (15, 19), (16, 20), (17, 21), (16, 22), (15, 23), (14, 24), (15, 25), (16, 26)]
    for (x, y) in bolt:
        core[(x, y)] = "W"; core[(x + 1, y)] = "b"; core[(x - 1, y)] = "b"
    for (x, y) in [(10, 8), (9, 9), (8, 10), (21, 17), (22, 18), (23, 19), (12, 20), (11, 21), (20, 6), (21, 5)]:
        core[(x, y)] = "b"
    for x, y, d in ring_cells(16, 27, 5, 6.2):
        if y < 32 and y > 22:
            core[(x, y)] = "B"
    return glow_sprite(core, {"W": (240, 250, 255), "b": (120, 200, 255), "B": (60, 120, 255)}, halo=(80, 150, 255))


def fx_crescent():
    core = {}
    for y in range(32):
        for x in range(32):
            d1 = ((x - 16) ** 2 + (y - 26) ** 2) ** 0.5
            d2 = ((x - 16) ** 2 + (y - 30) ** 2) ** 0.5
            if 13 <= d1 <= 17 and d2 > 15 and y < 26:
                core[(x, y)] = "W" if d1 < 14.2 else ("r" if d1 < 15.8 else "R")
    return glow_sprite(core, {"W": (255, 240, 220), "r": (255, 110, 70), "R": (200, 30, 30)}, halo=(255, 60, 40))


def fx_wind():
    core = {}
    for k in range(3):
        for i in range(90):
            t = i / 89 * 5.4
            r = 2 + t * 2.3
            a = t + k * 2.094
            x, y = int(16 + _m.cos(a) * r), int(16 + _m.sin(a) * r)
            core[(x, y)] = "W" if t < 2 else ("g" if t < 4 else "G")
    return glow_sprite(core, {"W": (220, 255, 240), "g": (100, 250, 190), "G": (30, 190, 130)}, halo=(60, 220, 160))


def fx_barrier():
    core = {}
    for x, y, d in ring_cells(16, 16, 12.3, 14):
        if x < 32 and y < 32:
            core[(x, y)] = "Y"
    shield = ["....#######....", "...#.......#...", "...#.......#...", "...#...#...#...", "...#...#...#...", "...#.#####.#...", "...#...#...#...",
              "....#..#..#....", ".....#...#.....", "......#.#......", ".......#......."]
    for j, row in enumerate(shield):
        for i, ch in enumerate(row):
            if ch == "#":
                core[(9 + i, 10 + j)] = "W"
    for k in range(8):
        a = k / 8 * 2 * _m.pi
        core[(int(16 + _m.cos(a) * 10), int(16 + _m.sin(a) * 10))] = "y"
    return glow_sprite(core, {"W": (255, 250, 220), "Y": (255, 200, 70), "y": (255, 230, 140)}, halo=(255, 190, 60))


def fx_blood():
    core = {}
    for y in range(1, 31):
        w = 1 if y < 5 or y > 26 else 2
        for x in range(16 - w, 16 + w):
            core[(x, y)] = "W" if x == 16 - w + 1 and 6 < y < 25 else "r"
    for (x, y) in [(12, 9), (11, 10), (20, 14), (21, 15), (21, 16), (11, 20), (12, 21), (19, 23), (19, 24)]:
        core[(x, y)] = "R"
    return glow_sprite(core, {"W": (255, 200, 200), "r": (230, 30, 40), "R": (150, 10, 20)}, halo=(200, 20, 30))


def fx_claw():
    core = {}
    for k in range(3):
        x0 = 6 + k * 8
        for y in range(3, 29):
            x = x0 + (y - 3) // 4 + (1 if 10 < y < 20 else 0)
            core[(x, y)] = "W" if 8 < y < 24 else "p"
            core[(x + 1, y)] = "p"
    return glow_sprite(core, {"W": (240, 220, 255), "p": (180, 110, 255)}, halo=(140, 70, 230))


def fx_staff():
    core = {}
    for x, y, d in ring_cells(16, 16, 11.5, 13.2):
        if x < 32 and y < 32:
            core[(x, y)] = "P"
    for x, y, d in ring_cells(16, 16, 3, 4.4):
        core[(x, y)] = "W"
    for k in range(8):
        a = k / 8 * 2 * _m.pi + 0.3
        pts = line_cells(16 + int(_m.cos(a) * 5), 16 + int(_m.sin(a) * 5), 16 + int(_m.cos(a + 0.25) * 11), 16 + int(_m.sin(a + 0.25) * 11))
        for (x, y) in pts:
            core[(x, y)] = "p"
    return glow_sprite(core, {"W": (250, 230, 255), "p": (210, 150, 255), "P": (150, 70, 230)}, halo=(150, 80, 240))


def fx_fire():
    core = {}
    for k in range(10):
        a = k / 10 * 2 * _m.pi
        cx, cy = 16 + _m.cos(a) * 11, 16 + _m.sin(a) * 11
        flame = ["..#..", ".###.", ".#Y#.", "##Y##", ".#W#."]
        for j, row in enumerate(flame):
            for i, ch in enumerate(row):
                if ch != ".":
                    X, Y = int(cx) - 2 + i, int(cy) - 3 + j
                    if 0 <= X < 32 and 0 <= Y < 32:
                        core[(X, Y)] = {"#": "R", "Y": "Y", "W": "W"}[ch]
    return glow_sprite(core, {"W": (255, 250, 210), "Y": (255, 200, 60), "R": (240, 90, 30)}, halo=(255, 110, 30))


SKILL_FX = {"wfx_thunder": fx_thunder, "wfx_crescent": fx_crescent, "wfx_wind": fx_wind, "wfx_barrier": fx_barrier,
            "wfx_blood": fx_blood, "wfx_claw": fx_claw, "wfx_staff": fx_staff, "wfx_fire": fx_fire}



# ═══════════════════════════════════════════ 리소스팩 등록 (무기 · 스킬 효과 · 마법진)
TEAM_RING = {"red": ((255, 130, 110), (220, 40, 40), (255, 210, 190)), "blue": ((140, 190, 255), (40, 100, 230), (210, 235, 255)),
             "green": ((140, 255, 150), (40, 180, 70), (210, 255, 210)), "yellow": ((255, 230, 120), (220, 170, 30), (255, 245, 200)),
             "neutral": ((235, 230, 215), (160, 150, 130), (255, 255, 245))}
BOSS_RING = {"talos": ((255, 170, 90), (230, 90, 20), (255, 220, 170)), "sphinx": ((140, 200, 255), (50, 120, 230), (210, 235, 255)),
             "ladon": ((140, 255, 160), (40, 190, 80), (210, 255, 215)), "cyclops": ((240, 200, 140), (190, 130, 60), (255, 235, 200))}


def export(pack):
    import decor2d as D2
    for wid, fn in WEAPONS.items():
        ref = pack.texture(f"weapon/{wid}", fn().image())
        pack.item_model(f"weapon/{wid}", {"parent": "minecraft:item/handheld", "textures": {"layer0": ref}})
    for name, fn in SKILL_FX.items():
        pack.texture(f"tele/{name}", fn())
    for k, (t, cols) in enumerate(TEAM_RING.items()):
        ref = pack.texture(f"pixel/cap_ring_{t}", magic_circle(*cols, seed=k, star=6))
        pack.item_model(f"deco/cap_ring_{t}", D2.flat_model(ref))
    for k, (b, cols) in enumerate(BOSS_RING.items()):
        ref = pack.texture(f"pixel/summon_{b}", magic_circle(*cols, seed=10 + k, star=(5, 6, 7, 8)[k]))
        pack.item_model(f"deco/summon_circle_{b}", D2.flat_model(ref))
    ref = pack.texture("pixel/rune_ring", magic_circle((255, 225, 120), (215, 160, 40), (255, 242, 190), seed=20, star=8))
    pack.item_model("deco/rune_ring", D2.flat_model(ref))
    pack.item_model("deco/rune_ring_big", D2.flat_model(ref))
