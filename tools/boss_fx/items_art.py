"""플레이어 아이템 스프라이트 (32x32, 바닐라의 2배 해상도) — 병종 장비 · 메뉴 · 보스 유물 · 사건 유물

방향은 바닐라와 같다: 검·도끼·삼지창 = 끝이 오른쪽 위 / 창(손) = 끝이 왼쪽 위 / 활 = 활대가 왼쪽 위를 감싼다.
"""
import math
from pixel import Sheet

S = Sheet.s


def poly(d, pts):
    d.polygon([(S(x), S(y)) for x, y in pts], fill=255)


def ell(d, x0, y0, x1, y1):
    d.ellipse([S(x0), S(y0), S(x1), S(y1)], fill=255)


def line(d, pts, w):
    d.line([(S(x), S(y)) for x, y in pts], fill=255, width=max(1, int(S(w))), joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse([S(x - w / 2), S(y - w / 2), S(x + w / 2), S(y + w / 2)], fill=255)


def bez(p0, p1, p2, n=24):
    out = []
    for k in range(n + 1):
        t = k / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


def along(a, b, t, off=0.0):
    """a→b 선분의 t 지점에서 수직으로 off 만큼"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    return (a[0] + dx * t + nx * off, a[1] + dy * t + ny * off)


def blade(d, a, b, widths):
    """a(손잡이 쪽) → b(끝) 칼날. widths = [(t, 반폭), ...] (좌우 대칭)"""
    left = [along(a, b, t, w) for t, w in widths]
    right = [along(a, b, t, -w) for t, w in reversed(widths)]
    poly(d, left + [b] + right)


def guard(d, c, a, b, half, th):
    """칼날 방향에 수직인 코등이"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    pts = [(c[0] + nx * half - ux * th, c[1] + ny * half - uy * th),
           (c[0] + nx * half + ux * th, c[1] + ny * half + uy * th),
           (c[0] - nx * half + ux * th, c[1] - ny * half + uy * th),
           (c[0] - nx * half - ux * th, c[1] - ny * half - uy * th)]
    poly(d, pts)


def bake(fn, size=64):
    """플레이어 아이템은 64px (GUI 배율 4 에서 1:1)"""
    sh = Sheet(size)
    fn(sh)
    return sh.bake()


# ═════════════════════════════════════════ 병종 장비
def infantry_sword(sh):                      # 보병의 검 — 곧은 철검, 청동 코등이
    a, b = (8, 24), (28, 4)
    d = sh.layer("steel")
    blade(d, a, b, [(0, 2.0), (0.7, 1.9), (0.9, 1.4)])
    d = sh.layer("white")
    line(d, [along(a, b, 0.05), along(a, b, 0.8)], 0.7)
    d = sh.layer("bronze")
    guard(d, a, a, b, 4.2, 1.1)
    d = sh.layer("fur")
    line(d, [a, (4, 28)], 2.2)
    d = sh.layer("bronze")
    ell(d, 1.8, 27.5, 5.2, 30.8)


def xiphos(sh):                               # 크시포스 — 잎 모양 청동 칼날
    a, b = (8, 24), (28, 4)
    d = sh.layer("gold")
    blade(d, a, b, [(0, 1.5), (0.35, 1.9), (0.65, 2.9), (0.85, 1.8)])
    d = sh.layer("bronze")
    line(d, [along(a, b, 0.02), along(a, b, 0.85)], 0.8)
    d = sh.layer("bronze")
    guard(d, a, a, b, 3.6, 1.2)
    d = sh.layer("dark")
    line(d, [a, (4.5, 27.5)], 2.3)
    d = sh.layer("gold")
    ell(d, 2, 27, 5.5, 30.5)


def kopis(sh):                                # 기병도 — 앞으로 굽은 외날 칼
    d = sh.layer("steel")
    pts = bez((9, 23), (18, 20), (28, 3), 20)
    back = bez((7, 20), (15, 12), (28, 3), 20)
    poly(d, pts + list(reversed(back)))
    d = sh.layer("white")
    line(d, bez((9.5, 21.5), (17, 17), (26, 5.5), 16), 0.6)
    d = sh.layer("bronze")
    guard(d, (8, 22.5), (8, 22.5), (18, 12), 3.2, 1.0)
    d = sh.layer("fur")
    line(d, [(8, 23), (4.5, 26.5)], 2.3)
    d = sh.layer("bronze")
    poly(d, [(2, 26), (5, 28.5), (3.5, 30.5), (1, 29)])     # 새 머리 폼멜


def parazonium(sh):                           # 단검 — 넓고 짧은 칼날, 상아 폼멜
    a, b = (12, 20), (26, 6)
    d = sh.layer("stone")
    blade(d, a, b, [(0, 2.6), (0.5, 2.1), (0.85, 1.2)])
    d = sh.layer("white")
    line(d, [along(a, b, 0.05), along(a, b, 0.75)], 0.6)
    d = sh.layer("bronze")
    guard(d, a, a, b, 3.8, 1.0)
    d = sh.layer("fur")
    line(d, [a, (7.5, 24.5)], 2.3)
    d = sh.layer("bone")
    ell(d, 4.5, 23.5, 9, 28)


def dory_gui(sh):                             # 도루 (인벤토리) — 끝이 오른쪽 위
    d = sh.layer("fur")
    line(d, [(4, 28), (22, 10)], 1.6)
    d = sh.layer("bronze")
    poly(d, [(2, 29.5), (5.5, 27.5), (4.5, 26.5), (2.5, 30.5)])
    line(d, [(3.5, 28.5), (6, 26)], 2.2)
    d = sh.layer("steel")
    blade(d, (20, 12), (30, 2), [(0, 1.3), (0.45, 3.0), (0.8, 1.6)])
    d = sh.layer("bronze")
    guard(d, (20, 12), (20, 12), (30, 2), 1.6, 0.9)


def dory_hand(sh):                            # 도루 (손) — 바닐라처럼 끝이 왼쪽 위, 길고 가늘다
    d = sh.layer("fur")
    line(d, [(28, 29), (8, 9)], 1.4)
    d = sh.layer("bronze")
    line(d, [(26, 27), (30, 31)], 2.0)
    d = sh.layer("steel")
    blade(d, (9, 10), (1, 2), [(0, 1.2), (0.45, 2.4), (0.8, 1.3)])
    d = sh.layer("bronze")
    guard(d, (9, 10), (9, 10), (1, 2), 1.5, 0.8)


def siege_hammer(sh):                         # 공성 망치 — 청동 숫양 머리
    d = sh.layer("fur")
    line(d, [(3, 29), (20, 12)], 2.6)
    c = (21, 11)
    u = (0.7071, -0.7071)        # 자루 방향
    n = (0.7071, 0.7071)         # 수직

    def P(a, b):
        return (c[0] + n[0] * a + u[0] * b, c[1] + n[1] * a + u[1] * b)
    d = sh.layer("bronze")
    poly(d, [P(-8, -3.5), P(8, -3.5), P(8, 3.5), P(-8, 3.5)])
    d = sh.layer("dark")
    poly(d, [P(6.5, -3.5), P(8, -3.5), P(8, 3.5), P(6.5, 3.5)])      # 치는 면
    d = sh.layer("gold")
    for a in (-2.5, 2.5):
        x, y = P(4, a)
        ell(d, x - 2, y - 2, x + 2, y + 2)
    d = sh.layer("steel")
    for a in (-5, -1.5):
        poly(d, [P(a, -3.6), P(a + 1.2, -3.6), P(a + 1.2, 3.6), P(a, 3.6)])  # 쇠 띠


def corinthian(sh):                           # 코린트식 투구 — 청동, 붉은 말총 볏
    d = sh.layer("red")
    poly(d, [(4, 10), (10, 3), (22, 2), (29, 7), (26, 10), (14, 7)])
    d = sh.layer("bronze")
    poly(d, [(7, 11), (15, 7), (24, 9), (27, 15), (26, 24), (22, 29), (18, 29), (18, 22), (14, 20), (11, 25), (8, 24), (6, 17)])
    d = sh.layer("dark")
    poly(d, [(13, 14), (21, 13), (19, 17), (17, 17), (16, 27), (14, 27), (14, 18)])   # 눈구멍 + 코가리개 틈
    d = sh.layer("gold")
    line(d, [(8, 12), (15, 8.5), (23, 10)], 0.9)


def hoplon_face(size=64):
    """호플론 방패 앞면 (원형, 청동 테 + 붉은 바탕 + 베르기나의 별). 3D 모델 텍스처"""
    sh = Sheet(size)
    u = 32  # 그리는 좌표는 0..32
    c = u / 2
    d = sh.layer("bronze")
    ell(d, 0.5, 0.5, u - 0.5, u - 0.5)
    d = sh.layer("red")
    ell(d, u * 0.12, u * 0.12, u * 0.88, u * 0.88)
    d = sh.layer("gold")
    pts = []
    for k in range(32):
        a = math.radians(k * 360 / 32 - 90)
        r = u * (0.33 if k % 2 == 0 else 0.1)
        pts.append((c + math.cos(a) * r, c + math.sin(a) * r))
    poly(d, pts)
    d = sh.layer("bronze")
    ell(d, c - u * 0.08, c - u * 0.08, c + u * 0.08, c + u * 0.08)
    return sh.bake(outline=False)


def hoplon_back(size=64):
    sh = Sheet(size)
    u = 32
    d = sh.layer("bronze")
    ell(d, 0.5, 0.5, u - 0.5, u - 0.5)
    d = sh.layer("fur")
    ell(d, u * 0.08, u * 0.08, u * 0.92, u * 0.92)
    d = sh.layer("dark")
    line(d, [(u * 0.2, u * 0.5), (u * 0.8, u * 0.5)], u * 0.06)
    return sh.bake(outline=False)


def bow_art(kind, pull):
    """kind = archer(스키타이 반곡궁) / chimera(뼈와 불꽃). pull 0 = 쉬는 활, 1..3 = 당김"""
    def fn(sh):
        top, bot = (27, 2), (2, 27)
        mid = (4 + pull * 0.4, 4 + pull * 0.4)
        limb = "fur" if kind == "archer" else "bone"
        d = sh.layer(limb)
        pts = bez(top, mid, bot, 30)
        for i in range(len(pts) - 1):
            t = i / (len(pts) - 1)
            w = 2.4 - abs(t - 0.5) * 2.2
            line(d, [pts[i], pts[i + 1]], max(1.1, w))
        # 반곡 끝
        if kind == "archer":
            line(d, [top, (29.5, 4.5)], 1.2)
            line(d, [bot, (4.5, 29.5)], 1.2)
        else:
            d2 = sh.layer("fire")
            line(d2, [top, (30, 1)], 1.3)
            line(d2, [bot, (1, 30)], 1.3)
        d = sh.layer("dark" if kind == "archer" else "red")
        ell(d, 5.2, 5.2, 9, 9)                                # 손잡이
        # 시위
        d = sh.layer("white")
        if pull == 0:
            line(d, [top, bot], 0.9)
        else:
            k = [0, 3.5, 6, 8][pull]
            p = (14.5 + k, 14.5 + k)
            line(d, [top, p], 0.9)
            line(d, [p, bot], 0.9)
            # 화살 (당길수록 촉이 활대 쪽으로 물러난다)
            d = sh.layer("fur" if kind == "archer" else "bone")
            tip = (1.5 + pull * 1.2, 1.5 + pull * 1.2)
            line(d, [p, tip], 1.3)
            d = sh.layer("steel" if kind == "archer" else "fire")
            poly(d, [(tip[0] - 1.8, tip[1] - 1.8), (tip[0] + 3.0, tip[1] - 0.4), (tip[0] - 0.4, tip[1] + 3.0)])
            d = sh.layer("white" if kind == "archer" else "red")
            poly(d, [(p[0] - 1, p[1] - 1), (p[0] + 2.5, p[1] - 0.3), (p[0] + 1.5, p[1] + 1.5), (p[0] - 0.3, p[1] + 2.5)])
    return fn
    return fn


def crossbow_art(state):
    """아르테미스의 석궁 — 은빛, 초승달 활대. state: standby / pull0..2 / arrow"""
    def fn(sh):
        d = sh.layer("dark")
        line(d, [(29, 29), (7, 7)], 3.4)                      # 개머리 (앞이 왼쪽 위)
        d = sh.layer("steel")
        line(d, [(26, 26), (8, 8)], 1.2)
        d = sh.layer("white")
        pts = bez((1.5, 19), (7, 7), (19, 1.5), 24)           # 활대: 개머리에 수직, 앞으로 휜 초승달
        for i in range(len(pts) - 1):
            t = i / (len(pts) - 1)
            line(d, [pts[i], pts[i + 1]], 2.8 - abs(t - 0.5) * 2.6)
        d = sh.layer("water")
        ell(d, 8, 8, 12, 12)
        back = {"standby": 0, "pull0": 3, "pull1": 5.5, "pull2": 8, "arrow": 8}[state]
        p = (13 + back, 13 + back)
        d = sh.layer("wave")
        line(d, [(1.5, 19), p], 0.9)
        line(d, [(19, 1.5), p], 0.9)
        d = sh.layer("steel")
        ell(d, p[0] - 1.1, p[1] - 1.1, p[0] + 1.1, p[1] + 1.1)
        if state == "arrow":
            d = sh.layer("gold")
            line(d, [p, (4, 4)], 1.2)
            d = sh.layer("white")
            poly(d, [(1.5, 1.5), (6.5, 3), (3, 6.5)])
    return fn


# ═════════════════════════════════════════ 메뉴
def olympus_menu(sh):                         # 올림포스 메뉴 — 월계관 속 신전
    d = sh.layer("scale")
    for side in (-1, 1):
        for k in range(7):
            a = math.radians(200 - k * 22) if side < 0 else math.radians(-20 + k * 22)
            x, y = 16 + math.cos(a) * 12.5 * side * (-1 if side < 0 else 1), 17 + math.sin(a) * -12
            x = 16 + math.cos(math.radians(110 + k * 22)) * 12.5 * (-side)
            y = 17 + math.sin(math.radians(110 + k * 22)) * 12.5
            ell(d, x - 2.2, y - 1.4, x + 2.2, y + 1.4)
    d = sh.layer("white")
    poly(d, [(8, 12), (16, 7), (24, 12)])                 # 박공
    for x in (9.5, 13.5, 17.5, 21.5):
        poly(d, [(x - 1, 13), (x + 1, 13), (x + 1, 21), (x - 1, 21)])
    poly(d, [(7.5, 21), (24.5, 21), (24.5, 23.5), (7.5, 23.5)])
    d = sh.layer("gold")
    ell(d, 14.4, 8.6, 17.6, 11.2)


def hero_emblem(sh):                          # 영웅 권능 — 청동 원판 + 번개
    d = sh.layer("bronze")
    ell(d, 3, 3, 29, 29)
    d = sh.layer("red")
    ell(d, 6.5, 6.5, 25.5, 25.5)
    d = sh.layer("gold")
    poly(d, [(18, 6), (10, 17), (15, 17), (12, 26), (22, 13), (17, 13), (20, 6)])


# ═════════════════════════════════════════ 보스 유물
def labrys(sh):                               # 미노타우로스의 라브리스
    d = sh.layer("fur")
    line(d, [(4, 29), (23, 10)], 2.2)
    d = sh.layer("red")
    poly(d, [(8, 22), (11, 19), (12.5, 25.5), (9, 27.5)])      # 매단 붉은 천
    d = sh.layer("steel")
    # 자루에 수직인 초승달 양날
    poly(d, [(22, 11), (26, 3), (29.5, 2), (31, 6), (30, 11), (26, 15)])
    poly(d, [(20, 13), (16, 5), (12, 4), (10, 8), (11, 13), (16, 16)])
    d = sh.layer("white")
    line(d, [(28.5, 3), (30.5, 8)], 0.8)
    line(d, [(11, 6), (10.8, 10.5)], 0.8)
    d = sh.layer("bronze")
    ell(d, 18.5, 9.5, 23.5, 14.5)


def lion_pelt(sh):                            # 네메아 사자의 가죽
    d = sh.layer("fur")
    poly(d, [(6, 12), (26, 12), (29, 28), (22, 25), (16, 30), (10, 25), (3, 28)])
    d = sh.layer("gold")
    pts = []
    for k in range(20):
        a = math.radians(k * 18)
        r = 9.5 if k % 2 == 0 else 7.2
        pts.append((16 + math.cos(a) * r, 10 + math.sin(a) * r * 0.85))
    poly(d, pts)
    d = sh.layer("fur")
    ell(d, 11, 5, 21, 15)
    d = sh.layer("dark")
    ell(d, 12.8, 8.2, 14.6, 10)
    ell(d, 17.4, 8.2, 19.2, 10)
    poly(d, [(14.8, 12), (17.2, 12), (16, 13.6)])


def cerberus_collar(sh):                      # 케르베로스의 목걸이 — 가시 목줄 + 영혼불 보석 셋
    d = sh.layer("dark")
    d.ellipse([S(4), S(5), S(28), S(29)], outline=255, width=int(S(4.2)))
    d = sh.layer("steel")
    for k in range(10):
        a = math.radians(k * 36 - 90)
        x, y = 16 + math.cos(a) * 12, 17 + math.sin(a) * 12
        poly(d, [(x + math.cos(a) * 3.4, y + math.sin(a) * 3.4), (x + math.cos(a + 1.6) * 1.4, y + math.sin(a + 1.6) * 1.4),
                 (x + math.cos(a - 1.6) * 1.4, y + math.sin(a - 1.6) * 1.4)])
    d = sh.layer("bronze")
    for k in range(10):
        a = math.radians(k * 36 - 72)
        x, y = 16 + math.cos(a) * 10, 17 + math.sin(a) * 10
        ell(d, x - 0.8, y - 0.8, x + 0.8, y + 0.8)
    d = sh.layer("soul")
    for cx, cy in ((9.5, 25), (16, 28), (22.5, 25)):
        poly(d, [(cx, cy - 3.2), (cx + 2.4, cy), (cx, cy + 2.6), (cx - 2.4, cy)])


def hydra_fang(sh):                           # 히드라의 독니
    d = sh.layer("poison")
    pts = bez((9, 23), (20, 18), (29, 2), 20)
    back = bez((7, 20), (13, 10), (29, 2), 20)
    poly(d, pts + list(reversed(back)))
    d = sh.layer("white")
    line(d, bez((10, 21), (18, 15), (27, 4), 16), 0.6)
    d = sh.layer("scale")
    line(d, [(8, 22), (3, 27)], 2.8)
    d = sh.layer("eye")
    ell(d, 1.5, 26.5, 5, 30)
    d = sh.layer("poison")
    ell(d, 21, 16, 23, 18.5)
    ell(d, 22.3, 19.5, 23.8, 21.5)


def medusa_head(sh):                          # 메두사의 머리
    d = sh.layer("scale")
    for k in range(9):
        a = math.radians(180 + k * 22.5)
        x0, y0 = 16 + math.cos(a) * 7, 15 + math.sin(a) * 7
        x1, y1 = 16 + math.cos(a) * 13, 15 + math.sin(a) * 12
        line(d, bez((x0, y0), (x1 + 2, (y0 + y1) / 2), (x1, y1), 12), 2.2)
        ell(d, x1 - 1.8, y1 - 1.6, x1 + 1.8, y1 + 1.6)
    d = sh.layer("jade")
    ell(d, 9, 9, 23, 26)
    d = sh.layer("eye")
    ell(d, 11.5, 15, 14.5, 17.5)
    ell(d, 17.5, 15, 20.5, 17.5)
    d = sh.layer("red")
    poly(d, [(13.5, 21.5), (18.5, 21.5), (16, 23.5)])
    d = sh.layer("blood")
    poly(d, [(12, 26), (20, 26), (18, 30), (14, 30)])


def scylla_trident(sh):                       # 스킬라의 삼지창
    d = sh.layer("water")
    line(d, [(3, 29), (20, 12)], 1.8)
    d = sh.layer("jade")
    for c in ((17, 12), (21, 16)):                        # 갈래 받침
        pass
    poly(d, [(15, 13), (19, 9), (23, 13), (19, 17)])
    d = sh.layer("steel")
    line(d, [(19, 13), (29, 3)], 1.4)
    line(d, [(17, 11), (22, 3)], 1.2)
    line(d, [(21, 15), (29, 10)], 1.2)
    poly(d, [(28, 1), (31, 4), (29, 4.5)])
    poly(d, [(21, 1), (23.5, 3), (21.5, 4)])
    poly(d, [(28, 8.5), (31, 11), (28.5, 11.5)])
    d = sh.layer("flesh")
    for k in range(4):
        t = 0.2 + k * 0.17
        x, y = 3 + (20 - 3) * t, 29 + (12 - 29) * t
        ell(d, x - 1.8, y - 0.9, x + 1.2, y + 1.9)


def chimera_bow_states():
    return [bow_art("chimera", p) for p in range(4)]


# ═════════════════════════════════════════ 사건 유물
def hephaestus_sword(sh):                     # 헤파이스토스의 검 — 달궈진 날
    a, b = (8, 24), (28, 4)
    d = sh.layer("dark")
    blade(d, a, b, [(0, 2.3), (0.7, 2.2), (0.9, 1.5)])
    d = sh.layer("hellfire")
    blade(d, along(a, b, 0.05, 1.3), along(a, b, 0.97, 0.2), [(0, 0.6), (0.8, 0.6)])
    d = sh.layer("fire")
    line(d, [along(a, b, 0.05, -0.8), along(a, b, 0.85, -0.8)], 0.7)
    d = sh.layer("steel")
    guard(d, a, a, b, 4.5, 1.4)
    d = sh.layer("dark")
    line(d, [a, (4, 28)], 2.4)
    d = sh.layer("steel")
    poly(d, [(1, 27), (5, 26), (6, 30), (2, 31)])         # 망치 폼멜


def hades_helm(sh):                           # 하데스의 투구 — 검은 쇠, 보랏빛 볏과 연기
    d = sh.layer("soul")
    poly(d, [(5, 9), (11, 3), (22, 2), (28, 6), (25, 9), (15, 6)])
    d = sh.layer("dark")
    poly(d, [(7, 11), (15, 7), (24, 9), (27, 15), (26, 24), (22, 29), (18, 29), (18, 22), (14, 20), (11, 25), (8, 24), (6, 17)])
    d = sh.layer("soul")
    poly(d, [(13, 14), (21, 13), (19, 17), (17, 17), (16, 27), (14, 27), (14, 18)])
    d = sh.layer("steel")
    line(d, [(8, 12), (15, 8.5), (23, 10)], 0.9)


def golden_apple(sh):                         # 헤스페리데스의 황금 사과
    d = sh.layer("gold")
    ell(d, 5, 9, 17.5, 28)
    ell(d, 14.5, 9, 27, 28)
    d = sh.layer("fur")
    line(d, [(16, 11), (17, 5)], 1.4)
    d = sh.layer("scale")
    poly(d, [(17.5, 6.5), (24, 3), (27, 5), (21, 8.5)])
    d = sh.layer("white")
    ell(d, 8.5, 13, 11, 16)
    ell(d, 26, 17, 28, 19)
    ell(d, 3, 21, 4.6, 22.6)


ITEMS = {
    # key: (base item, CMD, [(sprite_name, fn)], kind)
    "infantry_sword": ("iron_sword", 7201, "handheld"),
    "dory": ("iron_spear", 7202, "spear"),
    "dagger": ("stone_sword", 7203, "handheld"),
    "archer_bow": ("bow", 7204, "bow"),
    "kopis": ("iron_sword", 7205, "handheld"),
    "xiphos": ("iron_sword", 7206, "handheld"),
    "hoplon": ("shield", 7207, "shield"),
    "siege_hammer": ("iron_axe", 7208, "handheld"),
    "corinthian": ("golden_helmet", 7209, "generated"),
    "menu": ("nether_star", 7301, "generated"),
    "hero": ("nether_star", 7302, "generated"),
    "labrys": ("netherite_axe", 7101, "handheld"),
    "lion_pelt": ("golden_chestplate", 7102, "generated"),
    "chimera_bow": ("bow", 7103, "bow"),
    "cerberus_collar": ("totem_of_undying", 7104, "generated"),
    "hydra_fang": ("netherite_sword", 7105, "handheld"),
    "medusa_head": ("skeleton_skull", 7106, "generated"),
    "scylla_trident": ("trident", 7107, "trident"),
    "hephaestus_sword": ("iron_sword", 7401, "handheld"),
    "hades_helm": ("golden_helmet", 7402, "generated"),
    "artemis_crossbow": ("crossbow", 7403, "crossbow"),
    "golden_apple": ("golden_apple", 7404, "generated"),
}

SPRITES = {
    "infantry_sword": infantry_sword, "kopis": kopis, "xiphos": xiphos, "dagger": parazonium,
    "dory": dory_gui, "dory_in_hand": dory_hand, "siege_hammer": siege_hammer, "corinthian": corinthian,
    "menu": olympus_menu, "hero": hero_emblem, "labrys": labrys, "lion_pelt": lion_pelt,
    "cerberus_collar": cerberus_collar, "hydra_fang": hydra_fang, "medusa_head": medusa_head,
    "scylla_trident": scylla_trident, "hephaestus_sword": hephaestus_sword, "hades_helm": hades_helm,
    "golden_apple": golden_apple,
    "archer_bow": bow_art("archer", 0), "archer_bow_pulling_0": bow_art("archer", 1),
    "archer_bow_pulling_1": bow_art("archer", 2), "archer_bow_pulling_2": bow_art("archer", 3),
    "chimera_bow": bow_art("chimera", 0), "chimera_bow_pulling_0": bow_art("chimera", 1),
    "chimera_bow_pulling_1": bow_art("chimera", 2), "chimera_bow_pulling_2": bow_art("chimera", 3),
    "artemis_crossbow": crossbow_art("standby"), "artemis_crossbow_pulling_0": crossbow_art("pull0"),
    "artemis_crossbow_pulling_1": crossbow_art("pull1"), "artemis_crossbow_pulling_2": crossbow_art("pull2"),
    "artemis_crossbow_arrow": crossbow_art("arrow"),
}
