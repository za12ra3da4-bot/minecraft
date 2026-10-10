"""경찰과 도둑 전용 아이템 그림 (32×32 도트) — bg:kd/<이름> (item_model 컴포넌트)

 baton 경찰봉 · radio 무전기 · smoke 연막탄 · shoes 운동화 · bag 돈가방 · exit 나가기

 그리는 법 (모든 아이템 같은 규칙 → 한 세트처럼 보임)
   부품 = 모양(마스크) + 색 사다리(어둠 → 밝음 5~6칸, 그림자는 푸른 쪽 · 빛은 노란 쪽으로 색이 돎)
   부품마다 가장자리까지 거리로 '볼록한 높이' 를 만들고, 왼쪽 위 빛으로 비춰 사다리 칸을 고름 (둥근 입체감)
   새 부품을 올릴 때 오른쪽 아래로 1칸 그림자 · 바깥 테두리는 옆 색을 어둡게 한 색 (검정 한 색 테두리 X)
"""
import math

import numpy as np
from PIL import Image
from scipy import ndimage

S = 32
LIGHT = np.array([-0.55, -0.65, 0.52])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
INK = np.array([20, 14, 32])


def ramp(base, n=6, hue=18):
    """밝기 사다리: 어두운 쪽은 푸르고 채도 높게, 밝은 쪽은 노랗고 하얗게"""
    import colorsys
    r, g, b = [c / 255 for c in base]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    out = []
    for i in range(n):
        t = i / (n - 1) - 0.5                       # -0.5 … 0.5
        hh = (h - t * hue / 360) % 1.0               # 어두우면 +(파랑), 밝으면 -(노랑) 쪽으로
        ll = min(0.97, max(0.05, l + t * 0.62))
        ss = min(1.0, max(0.0, s * (1.0 - t * 0.5)))
        rr, gg, bb = colorsys.hls_to_rgb(hh, ll, ss)
        out.append((int(rr * 255), int(gg * 255), int(bb * 255)))
    return out


class Icon:
    def __init__(self):
        self.rgb = np.zeros((S, S, 3), np.float32)
        self.a = np.zeros((S, S), bool)
        self.yy, self.xx = np.mgrid[0:S, 0:S].astype(np.float32) + 0.5

    # ── 모양 만들기
    def poly(self, pts):
        from PIL import ImageDraw
        im = Image.new("L", (S * 4, S * 4), 0)
        ImageDraw.Draw(im).polygon([(x * 4, y * 4) for x, y in pts], fill=255)
        return np.asarray(im.resize((S, S), Image.BOX)) > 110

    def ellipse(self, cx, cy, rx, ry):
        return ((self.xx - cx) / rx) ** 2 + ((self.yy - cy) / ry) ** 2 <= 1.0

    def rrect(self, x0, y0, x1, y1, r=0):
        m = (self.xx > x0) & (self.xx < x1 + 1) & (self.yy > y0) & (self.yy < y1 + 1)
        if r:
            for cx, cy in ((x0 + r, y0 + r), (x1 + 1 - r, y0 + r), (x0 + r, y1 + 1 - r), (x1 + 1 - r, y1 + 1 - r)):
                corner = (np.abs(self.xx - cx) <= r) & (np.abs(self.yy - cy) <= r) & \
                         ((self.xx < x0 + r) | (self.xx > x1 + 1 - r)) & ((self.yy < y0 + r) | (self.yy > y1 + 1 - r))
                m &= ~corner | (((self.xx - cx) ** 2 + (self.yy - cy) ** 2) <= r * r)
        return m

    def seg(self, x0, y0, x1, y1, r):
        """선분 둘레 반지름 r (둥근 막대)"""
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = np.clip(((self.xx - x0) * dx + (self.yy - y0) * dy) / max(L2, 1e-6), 0, 1)
        return (self.xx - (x0 + t * dx)) ** 2 + (self.yy - (y0 + t * dy)) ** 2 <= r * r

    # ── 칠하기
    def part(self, mask, base, bevel=3.0, shadow=True, flat=None, spec=True, n=6, light=None):
        """mask 를 볼록하게 칠함. flat=k 면 사다리 k 칸 한 색"""
        mask = mask.astype(bool)
        if not mask.any():
            return
        R = np.array(ramp(base, n), np.float32)
        if shadow:
            sh = np.zeros_like(mask)
            sh[1:, 1:] = mask[:-1, :-1]
            sh &= self.a & ~mask
            self.rgb[sh] = self.rgb[sh] * 0.62 + INK * 0.38
        if flat is not None:
            self.rgb[mask] = R[flat]
            self.a |= mask
            return
        d = ndimage.distance_transform_edt(np.pad(mask, 1))[1:-1, 1:-1]
        u = np.clip(d / bevel, 0, 1)
        h = np.sqrt(1 - (1 - u) ** 2) * bevel
        h = ndimage.gaussian_filter(h, 0.6)
        gy, gx = np.gradient(h)
        nz = np.ones_like(h)
        nrm = np.sqrt(gx * gx + gy * gy + nz * nz)
        L = LIGHT if light is None else light / np.linalg.norm(light)
        lam = (-gx * L[0] - gy * L[1] + nz * L[2]) / nrm
        idx = np.clip(((lam - 0.15) / 0.85) * (n - 1.6) + 0.4, 0, n - 2).round().astype(int)
        if spec:
            idx[(lam > 0.97) & (d > 1.2)] = n - 1
        self.rgb[mask] = R[idx[mask]]
        self.a |= mask

    def dots(self, cells, color):
        for x, y in cells:
            if 0 <= x < S and 0 <= y < S:
                self.rgb[y, x] = color
                self.a[y, x] = True

    def line(self, x0, y0, x1, y1, color):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        self.dots([(round(x0 + (x1 - x0) * i / max(1, n - 1)), round(y0 + (y1 - y0) * i / max(1, n - 1))) for i in range(n)], color)

    def glow(self, cx, cy, r, color, k=0.55):
        """빛 번짐 (투명한 곳에는 반투명으로)"""
        d = np.sqrt((self.xx - cx) ** 2 + (self.yy - cy) ** 2)
        w = np.clip(1 - d / r, 0, 1) ** 1.6 * k
        self.glow_layer = getattr(self, "glow_layer", np.zeros((S, S, 4), np.float32))
        c = np.array(color, np.float32)
        self.glow_layer[..., :3] = self.glow_layer[..., :3] * (1 - w[..., None]) + c * w[..., None]
        self.glow_layer[..., 3] = np.maximum(self.glow_layer[..., 3], w)

    def image(self):
        # 바깥 테두리: 바로 옆 색을 어둡게 (아래 · 오른쪽은 더 어둡게)
        rgb = self.rgb.copy()
        a = self.a
        out = np.zeros((S, S, 4), np.float32)
        out[a, :3] = rgb[a]
        out[a, 3] = 255
        edge = ndimage.binary_dilation(a) & ~a
        for y, x in zip(*np.nonzero(edge)):
            cs, dark = [], 0.0
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < S and 0 <= Y < S and a[Y, X]:
                    cs.append(rgb[Y, X])
                    if dx < 0 or dy < 0:
                        dark = max(dark, 0.18)
            c = np.mean(cs, 0)
            out[y, x, :3] = c * (0.30 - dark) + INK * (0.70 + dark)
            out[y, x, 3] = 255
        g = getattr(self, "glow_layer", None)
        if g is not None:
            m = out[..., 3] == 0
            out[m, :3] = g[m, :3]
            out[m, 3] = g[m, 3] * 255
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


# ═════════════════════════════════════════════════════════════════ 아이템
def baton():
    """삼단 경찰봉 — 왼쪽 아래 고무 손잡이 → 오른쪽 위 크롬 봉 · 파란 경광 띠"""
    I = Icon()
    # 봉 (가늘어지는 3단)
    I.part(I.seg(13, 18, 26.5, 4.5, 1.7), (150, 160, 184), bevel=1.7)
    I.part(I.seg(11.5, 19.5, 20.5, 10.5, 2.2), (156, 166, 190), bevel=2.2)
    I.part(I.seg(27, 4, 27.6, 3.4, 2.3), (176, 186, 210), bevel=1.8)                    # 끝 구슬
    # 이음 고리
    I.part(I.seg(20.0, 11.0, 21.2, 9.8, 2.5), (110, 118, 140), bevel=1.6)
    I.part(I.seg(13.6, 17.4, 14.6, 16.4, 2.7), (110, 118, 140), bevel=1.6)
    # 손잡이 (검은 고무 + 홈)
    I.part(I.seg(4.5, 27.5, 12.5, 19.5, 3.0), (48, 50, 66), bevel=2.6)
    for k in range(5):
        cx, cy = 5.2 + k * 1.6, 26.8 - k * 1.6
        I.line(cx - 1.8, cy - 1.8, cx + 1.8, cy + 1.8, (24, 22, 36))
    # 끝 마개 + 파란 띠
    I.part(I.seg(3.4, 28.6, 4, 28, 3.1), (70, 74, 96), bevel=1.6)
    I.part(I.seg(11.8, 20.2, 12.8, 19.2, 3.2), (60, 120, 240), bevel=1.4)
    I.dots([(12, 18)], (190, 230, 255))
    I.glow(27.6, 3.4, 4.5, (200, 230, 255), 0.45)
    return I.image()


def radio():
    """무전기 — 남색 몸통 · 초록 화면 (신호 막대) · 스피커 구멍 · 노란 PTT · 빨간 불"""
    I = Icon()
    I.part(I.seg(20.5, 2.5, 20.5, 9, 1.3), (60, 62, 80), bevel=1.2)                 # 안테나
    I.part(I.ellipse(20.5, 2.6, 1.6, 1.4), (230, 60, 60), bevel=1.2)
    I.part(I.rrect(17, 7, 22, 10, 1), (52, 56, 76), bevel=1.4)                      # 안테나 받침
    I.part(I.rrect(7, 13, 9, 21, 1), (240, 180, 40), bevel=1.2)                     # 옆 PTT 버튼
    I.part(I.rrect(9, 9, 23, 29, 3), (52, 66, 112), bevel=3.2)                      # 몸통
    I.part(I.rrect(11, 11, 21, 17, 1), (28, 40, 52), flat=1, shadow=False)           # 화면 틀
    I.part(I.rrect(12, 12, 20, 16, 0), (110, 230, 140), bevel=1.5, shadow=False)     # 화면
    for k, hgt in enumerate((1, 2, 3, 4)):                                           # 신호 막대
        x = 13 + k * 2
        I.dots([(x, 16 - j) for j in range(hgt)], (24, 96, 44))
    I.dots([(19, 13), (19, 14)], (24, 96, 44))
    for yy in (20, 22, 24, 26):                                                       # 스피커 구멍
        I.dots([(x, yy) for x in range(12, 21, 2)], (26, 32, 58))
        I.dots([(x + 1, yy + 1) for x in range(12, 21, 2)], (96, 112, 168))
    I.part(I.ellipse(12.5, 9.8, 1.3, 1.3), (200, 204, 220), bevel=1.2)               # 손잡이 노브
    I.dots([(21, 19)], (255, 70, 60)); I.dots([(22, 19)], (255, 170, 150))           # 불
    I.glow(21.5, 19.5, 3.5, (255, 80, 70), 0.4)
    return I.image()


def smoke():
    """연막탄 — 올리브 통 · 노란 띠 · 위 손잡이(스푼) · 안전핀 고리 · 피어오르는 연기"""
    I = Icon()
    # 연기 (뒤)
    for cx, cy, r, c in ((7, 9, 4.2, (206, 212, 222)), (12, 5, 3.4, (222, 226, 234)),
                         (4, 15, 2.8, (190, 196, 210)), (17, 3, 2.4, (232, 236, 242))):
        I.part(I.ellipse(cx, cy, r, r * 0.9), c, bevel=r * 0.9, n=5)
    # 통
    I.part(I.rrect(11, 12, 22, 29, 3), (104, 118, 84), bevel=4.0, light=np.array([-1.0, -0.15, 0.55]))
    I.part(I.rrect(11, 18, 22, 21, 0), (236, 196, 48), bevel=1.0, shadow=False, light=np.array([-1.0, -0.15, 0.55]))
    for x in range(12, 22, 3):                                                        # 띠 글자 느낌
        I.dots([(x, 19), (x + 1, 19)], (120, 84, 20))
    I.part(I.rrect(11, 27, 22, 29, 1), (80, 88, 66), bevel=1.0, shadow=False)        # 바닥 테
    # 뚜껑 + 스푼
    I.part(I.rrect(13, 8, 20, 12, 1), (126, 132, 140), bevel=1.6)
    I.part(I.poly([(19, 9), (22, 9), (24, 14), (24, 22), (22.5, 22), (22.5, 14.5), (20.5, 11)]), (150, 156, 166), bevel=1.0)
    # 안전핀 고리
    ring = I.ellipse(26, 7, 3.2, 3.2) & ~I.ellipse(26, 7, 1.9, 1.9)
    I.part(ring, (214, 214, 226), bevel=0.9)
    I.line(20, 9, 23, 8, (180, 180, 196))
    return I.image()


def shoes():
    """대시 운동화 — 빨간 겉감 · 흰 밑창 · 하늘 번개 줄 · 흰 끈 · 뒤로 속도선"""
    I = Icon()
    for k, (y, x0) in enumerate(((15, 1), (19, 0), (23, 2))):                         # 속도선
        I.dots([(x, y) for x in range(x0, x0 + 3 - (k == 1))], (130, 220, 255))
        I.dots([(x0 + 3, y)], (220, 248, 255))
    # 겉감
    upper = I.poly([(5, 13), (12, 11), (16, 16), (24, 18), (28.5, 20.5), (29.5, 25), (5, 25)])
    I.part(upper, (214, 44, 56), bevel=3.0)
    I.part(I.poly([(5, 13), (12, 11), (13.2, 13), (6, 15)]), (250, 236, 236), bevel=1.0)    # 발목 테
    I.part(I.poly([(21, 18), (24, 18), (28.5, 20.5), (29.5, 23), (24, 23)]), (240, 70, 80), bevel=1.6)  # 앞코
    # 번개 줄
    I.part(I.poly([(9, 22), (14, 18.5), (13.5, 20.5), (19, 18.5), (13, 23.5), (13.5, 21.5)]), (110, 210, 255), bevel=1.0, shadow=False)
    # 끈 (가로 줄 + 매듭)
    for k in range(4):
        x, y = 12.5 + k * 2, 13.5 + k * 1.2
        I.line(x, y, x + 2, y - 1, (250, 250, 255))
        I.dots([(round(x), round(y) + 1)], (120, 30, 40))
    # 밑창
    I.part(I.rrect(4, 24, 30, 27, 1), (236, 236, 244), bevel=1.4)
    I.part(I.rrect(4, 27, 30, 28, 0), (120, 196, 255), bevel=0.8, shadow=False)      # 쿠션 줄
    for x in range(6, 30, 3):
        I.dots([(x, 26)], (176, 178, 196))
    I.part(I.rrect(4, 14, 6, 21, 1), (40, 40, 56), bevel=1.0)                         # 뒤꿈치 탭
    return I.image()


def bag():
    """돈가방 — 불룩한 삼베 자루 · 묶은 끈 · 금빛 $ · 삐져나온 지폐 · 금화"""
    I = Icon()
    I.part(I.poly([(12, 6), (15, 3), (19, 4), (21, 7)]), (110, 190, 90), bevel=1.2)    # 지폐
    I.part(I.poly([(17, 5), (22, 2), (24, 4), (20, 8)]), (130, 206, 106), bevel=1.2)
    I.dots([(20, 4), (21, 4)], (60, 120, 50))
    I.part(I.ellipse(16, 20, 11, 9.5), (176, 128, 70), bevel=5.5)                      # 자루
    I.part(I.poly([(11, 13), (13, 8), (19, 8), (21, 13)]), (164, 118, 62), bevel=2.0)  # 목
    I.part(I.rrect(11, 10, 21, 12, 1), (102, 62, 34), bevel=1.0)                       # 끈
    I.part(I.ellipse(22.5, 11.5, 1.6, 1.3), (102, 62, 34), bevel=1.0)                  # 매듭
    I.line(23, 12, 25, 15, (92, 56, 30))
    # 바느질 (아래 둥근 선)
    for t in range(200, 340, 14):
        a = math.radians(t)
        I.dots([(round(16 + math.cos(a) * 8.5), round(20 - math.sin(a) * 7.0))], (128, 88, 46))
    # 금빛 $ (돋을새김)
    G = ((15, 15), (16, 15), (17, 15), (18, 15), (14, 16), (14, 17), (15, 18), (16, 18), (17, 18), (18, 19),
         (18, 20), (14, 21), (15, 21), (16, 21), (17, 21), (16, 14), (16, 22))
    I.dots([(x + 1, y + 1) for x, y in G], (110, 70, 30))
    I.dots(G, (255, 214, 70))
    I.dots([(15, 15), (14, 16), (16, 14)], (255, 246, 190))
    # 금화
    for cx, cy in ((25.5, 27), (28, 25.5)):
        I.part(I.ellipse(cx, cy, 2.6, 1.9), (240, 190, 50), bevel=1.2)
    I.dots([(25, 26), (27, 25)], (255, 250, 200))
    return I.image()


def exit_door():
    """나가기 — 빛이 새는 반쯤 열린 문 · 초록 비상구 화살표"""
    I = Icon()
    I.glow(17, 17, 12, (255, 236, 160), 0.38)
    I.part(I.rrect(5, 3, 22, 29, 1), (98, 66, 50), bevel=1.6)                          # 문틀
    I.part(I.rrect(7, 5, 20, 29, 0), (255, 232, 150), bevel=4.0, shadow=False)         # 열린 틈 빛
    door = I.poly([(7, 5), (13.5, 7), (13.5, 30), (7, 30)])
    I.part(door, (196, 52, 58), bevel=1.6)                                             # 열린 문짝 (원근)
    I.dots([(12, 18), (12, 19)], (255, 214, 80))                                       # 손잡이
    I.dots([(9, 10), (10, 10), (11, 11), (9, 22), (10, 22), (11, 22)], (150, 30, 40))
    arrow = I.poly([(15, 14), (22, 14), (22, 10), (30, 17), (22, 24), (22, 20), (15, 20)])
    I.part(arrow, (70, 200, 90), bevel=2.2)
    I.part(I.poly([(16, 15), (23, 15), (23, 12.5), (27, 15.5)]), (190, 255, 196), flat=3, shadow=False)
    return I.image()


ITEMS = {"baton": (baton, "handheld"), "radio": (radio, "generated"), "smoke": (smoke, "generated"),
         "shoes": (shoes, "generated"), "bag": (bag, "generated"), "exit": (exit_door, "generated")}


def export(pack):
    for name, (fn, parent) in ITEMS.items():
        ref = pack.texture(f"kd/{name}", fn())
        pack.item_model(f"kd/{name}", {"parent": f"minecraft:item/{parent}", "textures": {"layer0": ref}})


def preview(path, scale=10):
    from PIL import ImageDraw, ImageFont
    ims = [fn() for fn, _ in ITEMS.values()]
    names = ["경찰봉", "무전기", "연막탄", "운동화", "돈가방", "나가기"]
    cell = S * scale + 24
    out = Image.new("RGBA", (cell * len(ims) + 24, S * scale + 120), (34, 36, 46, 255))
    d = ImageDraw.Draw(out)
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 26)
    for i, im in enumerate(ims):
        x = 24 + i * cell
        d.rectangle((x - 6, 18, x + S * scale + 6, 30 + S * scale), fill=(52, 54, 66, 255))
        out.alpha_composite(im.resize((S * scale, S * scale), Image.NEAREST), (x, 24))
        out.alpha_composite(im.resize((64, 64), Image.NEAREST), (x, S * scale + 44))   # 핫바 크기 느낌
        d.text((x + 80, S * scale + 58), names[i], font=font, fill=(220, 226, 240))
    out.save(path)


if __name__ == "__main__":
    import sys
    preview(sys.argv[1] if len(sys.argv) > 1 else "kditems.png")
