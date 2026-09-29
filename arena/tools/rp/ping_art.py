"""지휘 깃발 (핑) 그림 — 픽셀 아트
  ping/flag   : 손에 드는 아이템 (지휘 깃발)
  ping/attack : 공중에 뜨는 공격 표시 (붉은 핀 + 교차한 칼)
  ping/help   : 공중에 뜨는 도움 요청 표시 (금빛 핀 + 방패 + 느낌표)
  공중 표시는 세로 판 모델 (빛 15 · 그림자 없음) → item_display billboard 로 항상 나를 본다
"""
import numpy as np
from PIL import Image, ImageDraw

OUT = (12, 6, 10, 255)


def _outline(im):
    a = np.asarray(im).copy()
    al = a[..., 3] > 0
    ol = np.zeros_like(al)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        ol |= np.roll(np.roll(al, dy, 0), dx, 1)
    ol &= ~al
    a[ol] = OUT
    return Image.fromarray(a, "RGBA")


def _pin(body, ring, icon_fn):
    """32x32 지도 핀: 둥근 머리 + 아래 뾰족 · 금 테 · 가운데 밝은 원 속 아이콘"""
    N = 32
    yy, xx = np.mgrid[0:N, 0:N] + 0.5
    cx, cy, R = 16, 13, 11.2
    head = (xx - cx) ** 2 + (yy - cy) ** 2 <= R * R
    # 아래 뾰족 (삼각형)
    tip = (yy >= cy) & (yy <= 30) & (np.abs(xx - cx) <= (30 - yy) * 0.62)
    shape = head | tip
    a = np.zeros((N, N, 4), np.uint8)
    hi, mid, lo = body
    a[shape] = mid + (255,)
    # 명암: 위 · 왼쪽 밝게, 아래 · 오른쪽 어둡게
    lit = shape & ((xx - cx) + (yy - cy) < -6)
    dark = shape & ((xx - cx) + (yy - cy) > 7)
    a[lit] = hi + (255,)
    a[dark] = lo + (255,)
    # 금 테 (머리 안쪽 고리)
    r2 = (xx - cx) ** 2 + (yy - cy) ** 2
    rim = (r2 <= 8.6 ** 2) & (r2 > 7.4 ** 2)
    a[rim] = ring + (255,)
    inner = r2 <= 7.4 ** 2
    a[inner] = (250, 244, 226, 255)
    a[inner & ((xx - cx) + (yy - cy) > 5)] = (214, 204, 186, 255)
    # 반짝임
    for (px, py) in ((9, 6), (10, 5), (8, 7)):
        a[py, px] = (255, 255, 255, 255)
    im = Image.fromarray(a, "RGBA")
    icon_fn(ImageDraw.Draw(im), cx, cy)
    return _outline(im)


def _swords(d, cx, cy):
    """교차한 칼 두 자루: 은빛 날 · 금 코등이 · 갈색 손잡이"""
    for s in (-1, 1):
        # 날 (칼끝 위쪽 → 코등이)
        d.line([(cx - 5 * s, cy - 5), (cx + 2 * s, cy + 2)], fill=(70, 74, 92, 255), width=3)
        d.line([(cx - 5 * s, cy - 5), (cx + 2 * s, cy + 2)], fill=(216, 224, 236, 255), width=1)
        # 코등이 (날과 수직)
        d.line([(cx + 1 * s, cy + 4), (cx + 4 * s, cy + 1)], fill=(236, 170, 40, 255), width=1)
        # 손잡이
        d.point([(cx + 3 * s, cy + 3), (cx + 4 * s, cy + 4)], fill=(120, 70, 30, 255))
        d.point([(cx + 5 * s, cy + 5)], fill=(236, 170, 40, 255))
    d.point([(cx - 5, cy - 5), (cx + 5, cy - 5)], fill=(255, 255, 255, 255))


def _shield(d, cx, cy):
    S = (40, 110, 210, 255); E = (20, 40, 90, 255)
    d.polygon([(cx - 5, cy - 5), (cx + 5, cy - 5), (cx + 5, cy), (cx, cy + 6), (cx - 5, cy)], fill=E)
    d.polygon([(cx - 4, cy - 4), (cx + 4, cy - 4), (cx + 4, cy), (cx, cy + 5), (cx - 4, cy)], fill=S)
    d.rectangle([cx - 1, cy - 3, cx, cy + 0], fill=(255, 255, 255, 255))
    d.rectangle([cx - 1, cy + 2, cx, cy + 3], fill=(255, 255, 255, 255))


def attack():
    return _pin(((255, 110, 90), (214, 40, 36), (120, 16, 20)), (255, 206, 90), _swords)


def help_():
    return _pin(((255, 230, 120), (236, 176, 36), (150, 90, 12)), (255, 250, 210), _shield)


def flag():
    """손에 드는 지휘 깃발 (32x32)"""
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 깃대 (대각선)
    for i in range(24):
        x, y = 6 + i * 0.5, 29 - i
        d.point([(int(x), int(y))], fill=(120, 76, 40, 255))
        d.point([(int(x) + 1, int(y))], fill=(84, 50, 24, 255))
    d.rectangle([17, 3, 19, 5], fill=(255, 210, 80, 255))
    # 깃발 천 (물결 · 붉은 금)
    pts = [(18, 6), (29, 7), (26, 11), (30, 15), (19, 16)]
    d.polygon(pts, fill=(206, 40, 40, 255))
    d.polygon([(18, 6), (29, 7), (27, 9), (18, 9)], fill=(240, 80, 70, 255))
    d.line([(19, 15), (29, 15)], fill=(130, 16, 20, 255))
    # 문장 (금 별)
    d.point([(23, 10), (22, 11), (23, 11), (24, 11), (23, 12), (22, 13), (24, 13)], fill=(255, 220, 90, 255))
    return _outline(im)


def board_model(ref):
    """세로 판 (앞뒤 두 면) · 빛 15"""
    return {"textures": {"0": ref, "particle": ref}, "elements": [
        {"from": [0, 0, 8], "to": [16, 16, 8], "shade": False, "light_emission": 15,
         "faces": {"north": {"uv": [16, 0, 0, 16], "texture": "#0"}, "south": {"uv": [0, 0, 16, 16], "texture": "#0"}}}]}


def export(pack):
    ref = pack.texture("ping/flag", flag())
    pack.item_model("ping/flag", {"parent": "minecraft:item/generated", "textures": {"layer0": ref}})
    for name, fn in (("attack", attack), ("help", help_)):
        ref = pack.texture(f"ping/{name}", fn())
        pack.item_model(f"ping/{name}", board_model(ref))


if __name__ == "__main__":
    import sys
    W = Image.new("RGBA", (3 * 34 * 8, 34 * 8), (60, 70, 80, 255))
    for i, fn in enumerate((flag, attack, help_)):
        W.alpha_composite(fn().resize((256, 256), Image.NEAREST), (i * 272 + 8, 8))
    W.save(sys.argv[1] if len(sys.argv) > 1 else "ping.png")
