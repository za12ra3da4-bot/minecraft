"""사용자가 서버에서 직접 고친 올림포스 맵 (arena/art/maps/olympus_user.schem — WorldEdit //schem save)

 · 올림포스: 고친 맵을 통째로 그대로 짓는다 (/전장 건설 해도 고친 성 · 천장이 사라지지 않게) + 길가 나무 치우기만 덧씀
 · 다른 맵: 고친 본진 성 네 개를 같은 자리에 그대로 옮겨 심고 (흙 · 풀 · 나무만 맵 테마로), 높이 69 투명 천장(배리어)도 똑같이

 스키매틱 → 맵 로컬 좌표: 스키매틱 칸 (x+1, y, z+1) = 맵 (x, y, z)  (맵 블록과 98.6% 일치하는 위치를 찾아 맞춤)
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from layout import *

SCHEM = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "maps", "olympus_user.schem")
SHIFT = (1, 0, 1)
CASTLE_R = 29            # 본진 중심에서 이만큼 (성벽 21 + 탑 · 경사로 시작)
CASTLE_Y0 = BASE_H - 5   # 이 높이부터 위를 옮김 (아래는 그 맵의 땅)

_cache = None


def user_map():
    """(vox[x,y,z] 팔레트 번호, 팔레트 이름 목록) — 맵 크기 256x96x256 으로 잘라 맞춤"""
    global _cache
    if _cache is None:
        if not os.path.exists(SCHEM):
            return None
        import schem
        vox, names, _ = schem.read(SCHEM)
        dx, dy, dz = SHIFT
        v = vox[dx:dx + SIZE, dy:dy + HEIGHT, dz:dz + SIZE]
        names = ["air" if n.split("[")[0] in ("cave_air", "void_air") else n for n in names]
        _cache = (v, names)
    return _cache


def _put(w, mask, uv, names, conv=None):
    """mask 칸에 사용자 블록을 넣음 (conv: 이름 → 이름, 테마 바꾸기)"""
    ids = np.zeros(len(names), np.int64)
    for i, n in enumerate(names):
        n2 = conv(n) if conv else n
        ids[i] = 0 if n2 == "air" else w.id(n2)
    w.vox[mask] = ids[uv[mask]].astype(np.uint16)


def whole(w):
    """올림포스: 고친 맵 통째로 + 길가 나무 치우기"""
    um = user_map()
    if um is None:
        print("[userbase] 고친 맵 파일 없음 — 생성한 맵 그대로")
        return False
    uv, names = um
    tree_fix = getattr(w, "road_tree_fix", [])
    full = np.ones(uv.shape, bool)
    _put(w, full, uv, names)
    # 길가 나무 (생성 맵에서 치운 칸): 사용자 맵에서도 아직 나무 블록이면 치움
    n = 0
    for x, y, z, st in tree_fix:
        cur = w.pal[w.vox[x, y, z]].split("[")[0]
        if cur.endswith(("_leaves", "_log", "_wood")):
            w.vox[x, y, z] = w.id(st) if st != "air" else 0
            n += 1
    print(f"[userbase] 올림포스 = 직접 고친 맵 그대로 (길가 나무 {n}칸 치움)")
    return True


def castles(w, theme, conv):
    """다른 맵: 고친 성 네 개 + 천장"""
    um = user_map()
    if um is None:
        return
    uv, names = um
    X, Z = np.meshgrid(np.arange(SIZE), np.arange(SIZE), indexing="ij")
    col = np.zeros((SIZE, SIZE), bool)
    for t in TEAMS:
        bx, bz = team_base(t)
        col |= np.hypot(X - bx, Z - bz) <= CASTLE_R
    m = np.zeros(uv.shape, bool)
    m[:, CASTLE_Y0:, :] = col[:, None, :]
    # 성 영역: 위쪽은 사용자 것으로 덮음 (그 맵에 있던 나무 · 눈 등은 지움)
    _put(w, m, uv, names, conv)
    # 천장 (높이 69 배리어) — 그 맵에서 비어 있는 칸만
    bid = np.array([n.split("[")[0] for n in names])
    bar = (bid == "barrier")[uv]
    bar &= (w.vox == 0)
    w.vox[bar] = w.id("barrier")
    print(f"[userbase] {theme}: 고친 성 4개 옮김 ({int(m.sum())}칸 영역) · 천장 배리어 {int(bar.sum())}칸")
