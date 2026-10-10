"""경찰과 도둑 전용 아이템 그림 (32×32 도트) — bg:kd/<이름> (item_model 컴포넌트)

 baton 경찰봉 · radio 무전기 · smoke 연막탄 · shoes 운동화 · bag 돈가방
"""
from PIL import Image, ImageDraw

INK = (14, 14, 22, 255)


def _outline(im):
    src = im.copy().load()
    px = im.load()
    W, H = im.size
    for y in range(H):
        for x in range(W):
            if src[x, y][3]:
                continue
            if any(0 <= x + dx < W and 0 <= y + dy < H and src[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = INK
    return im


def baton():
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 검은 몸통 (대각선) + 은색 손잡이 + 옆 손잡이 + 반짝임
    for i in range(18):
        x, y = 8 + i, 23 - i
        d.rectangle((x, y - 1, x + 2, y + 1), fill=(36, 38, 52, 255))
        d.point((x + 1, y - 1), fill=(90, 96, 130, 255))
    for i in range(6):
        x, y = 4 + i, 27 - i
        d.rectangle((x, y - 1, x + 2, y + 1), fill=(180, 186, 200, 255))
        d.point((x + 1, y - 1), fill=(240, 244, 255, 255))
    d.rectangle((10, 20, 14, 21), fill=(60, 64, 84, 255))
    d.rectangle((13, 17, 14, 21), fill=(60, 64, 84, 255))
    d.rectangle((25, 4, 27, 6), fill=(120, 170, 255, 255))
    d.point((26, 5), fill=(255, 255, 255, 255))
    return _outline(im)


def radio():
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((19, 2, 20, 10), fill=(40, 40, 50, 255))                 # 안테나
    d.rectangle((18, 2, 21, 3), fill=(230, 50, 50, 255))
    d.rounded_rectangle((9, 9, 23, 29), radius=2, fill=(34, 40, 60, 255))
    d.rounded_rectangle((10, 10, 22, 28), radius=2, fill=(52, 62, 92, 255))
    d.rectangle((11, 11, 21, 16), fill=(120, 230, 140, 255))            # 화면
    d.line((12, 13, 15, 13), fill=(30, 90, 40, 255)); d.line((12, 15, 18, 15), fill=(30, 90, 40, 255))
    for yy in (19, 22, 25):                                              # 스피커
        d.line((12, yy, 20, yy), fill=(24, 28, 40, 255))
    d.point((21, 18), fill=(255, 80, 80, 255))
    d.rectangle((7, 14, 8, 20), fill=(240, 180, 40, 255))               # 옆 버튼
    return _outline(im)


def smoke():
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, 21, 28), radius=3, fill=(96, 104, 96, 255))
    d.rounded_rectangle((11, 11, 20, 27), radius=3, fill=(132, 142, 130, 255))
    d.rectangle((11, 17, 20, 19), fill=(240, 200, 40, 255))              # 노란 띠
    d.rectangle((13, 6, 18, 10), fill=(70, 74, 80, 255))
    d.ellipse((18, 3, 24, 9), outline=(200, 200, 210, 255))              # 안전핀 고리
    d.line((14, 21, 14, 25), fill=(170, 180, 168, 255))
    for cx, cy, r in ((7, 8, 3), (4, 13, 2), (26, 13, 2)):               # 연기
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(220, 224, 230, 220))
    return _outline(im)


def shoes():
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(6, 14), (14, 12), (18, 18), (27, 20), (28, 25), (5, 25)], fill=(220, 40, 50, 255))
    d.polygon([(6, 14), (14, 12), (16, 15), (7, 17)], fill=(255, 110, 110, 255))
    d.rectangle((4, 25, 28, 27), fill=(245, 245, 250, 255))              # 흰 밑창
    d.line((4, 27, 28, 27), fill=(170, 170, 180, 255))
    for x in (11, 14, 17):                                               # 끈
        d.line((x, 16, x + 2, 15), fill=(255, 255, 255, 255))
    d.line((20, 21, 26, 22), fill=(255, 255, 255, 255))                  # 줄무늬
    for x, y in ((2, 16), (1, 19), (2, 22)):                             # 속도선
        d.line((x, y, x + 2, y), fill=(140, 220, 255, 255))
    return _outline(im)


def bag():
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((6, 11, 26, 29), fill=(150, 110, 60, 255))
    d.ellipse((7, 12, 25, 27), fill=(186, 140, 80, 255))
    d.polygon([(12, 12), (20, 12), (22, 7), (10, 7)], fill=(160, 118, 66, 255))
    d.rectangle((11, 10, 21, 11), fill=(90, 60, 30, 255))                # 묶은 끈
    # 금색 $ 표시
    G, GD = (255, 214, 60, 255), (170, 120, 20, 255)
    for x, y in ((15, 15), (16, 15), (17, 15), (14, 16), (14, 17), (15, 18), (16, 18), (17, 19), (17, 20),
                 (14, 21), (15, 21), (16, 21), (16, 14), (16, 22)):
        d.point((x, y), fill=G)
        d.point((x + 1, y + 1), fill=GD) if (x + 1, y + 1) not in () else None
    d.ellipse((9, 15, 12, 18), fill=(220, 180, 120, 255))                # 빛
    return _outline(im)


def exit_door():
    """나가기 버튼: 빨간 문 + 흰 화살표"""
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((6, 3, 21, 29), fill=(120, 30, 34, 255))
    d.rectangle((8, 5, 19, 28), fill=(200, 50, 56, 255))
    d.rectangle((8, 5, 19, 7), fill=(240, 100, 100, 255))
    d.rectangle((10, 10, 17, 15), fill=(160, 36, 42, 255)); d.rectangle((10, 18, 17, 25), fill=(160, 36, 42, 255))
    d.rectangle((16, 17, 17, 18), fill=(255, 220, 80, 255))               # 손잡이
    d.polygon([(19, 12), (25, 12), (25, 9), (30, 15), (25, 21), (25, 18), (19, 18)], fill=(255, 255, 255, 255))
    d.polygon([(20, 13), (26, 13), (26, 11), (29, 15), (26, 19), (26, 17), (20, 17)], fill=(140, 230, 140, 255))
    return _outline(im)


ITEMS = {"baton": (baton, "handheld"), "radio": (radio, "generated"), "smoke": (smoke, "generated"),
         "shoes": (shoes, "generated"), "bag": (bag, "generated"), "exit": (exit_door, "generated")}


def export(pack):
    for name, (fn, parent) in ITEMS.items():
        ref = pack.texture(f"kd/{name}", fn())
        pack.item_model(f"kd/{name}", {"parent": f"minecraft:item/{parent}", "textures": {"layer0": ref}})


if __name__ == "__main__":
    import sys
    ims = [fn() for fn, _ in ITEMS.values()]
    out = Image.new("RGBA", (40 * len(ims), 40), (40, 42, 50, 255))
    for i, im in enumerate(ims):
        out.alpha_composite(im, (4 + 40 * i, 4))
    out.resize((out.size[0] * 6, 240), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else "kditems.png")
