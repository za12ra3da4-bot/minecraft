"""건축 프리미티브"""
import math

import numpy as np

import blocks as B
from layout import *

FACINGS = ["north", "east", "south", "west"]
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
DXZ = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


def stairs(mat, facing, half="bottom"):
    return f"{mat}_stairs[facing={facing},half={half},shape=straight,waterlogged=false]"


def slab(mat, typ="bottom"):
    return f"{mat}_slab[type={typ},waterlogged=false]"


def wall(mat):
    return f"{mat}_wall"


def facing_to(dx, dz):
    """(dx,dz) 방향을 바라보는 facing"""
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


class Builder:
    def __init__(self, w, T, seed=11):
        self.w = w
        self.T = T
        self.r = np.random.default_rng(seed)

    # ── 기본
    def set(self, x, y, z, s):
        self.w.set(int(x), int(y), int(z), s)

    def fill(self, x0, y0, z0, x1, y1, z1, s):
        self.w.fill(int(x0), int(y0), int(z0), int(x1), int(y1), int(z1), s)

    def air(self, x0, y0, z0, x1, y1, z1):
        self.fill(x0, y0, z0, x1, y1, z1, "air")

    def gy(self, x, z):
        """지형 높이 (구조물 무시)"""
        x = int(np.clip(x, 0, SIZE - 1)); z = int(np.clip(z, 0, SIZE - 1))
        return int(self.T.Hi[x, z])

    def top(self, x, z):
        return self.w.top(int(x), int(z))

    def rand(self):
        return self.r.random()

    def choice(self, items, p=None):
        if p is not None:
            p = np.array(p, float); p /= p.sum()
        return items[self.r.choice(len(items), p=p)]

    def foundation(self, x0, z0, x1, z1, y, mat="stone_bricks", depth=8):
        """구조물 아래 빈 곳 채우기 (지형 아래로)"""
        for x in range(int(x0), int(x1) + 1):
            for z in range(int(z0), int(z1) + 1):
                g = self.gy(x, z)
                if g < y:
                    self.fill(x, max(g - 1, y - depth), z, x, y, z, mat)

    def clear_above(self, x0, z0, x1, z1, y, h=30):
        self.air(x0, y, z0, x1, y + h, z1)

    # ── 공통 재질 섞기
    def mix(self, table):
        items = [a for a, _ in table]
        ws = [b for _, b in table]
        return self.choice(items, ws)

    # ─────────────────────────────── 그리스 기둥
    def column(self, x, z, y0, h, mat="quartz", broken=None, style="doric", base_mat=None, width=3):
        """3x3 (또는 1x1) 기둥. broken=높이 (중간이 부서짐)"""
        x, z = int(x), int(z)
        top_y = y0 + h
        pillar = "quartz_pillar[axis=y]" if mat == "quartz" else mat
        smooth = {"quartz": "smooth_quartz", "sandstone": "smooth_sandstone", "blackstone": "polished_blackstone",
                  "stone": "smooth_stone", "calcite": "calcite", "deepslate": "polished_deepslate"}.get(mat, mat)
        stair_m = {"quartz": "quartz", "sandstone": "smooth_sandstone", "blackstone": "polished_blackstone",
                   "stone": "stone_brick", "calcite": "polished_diorite", "deepslate": "polished_deepslate"}.get(mat, "stone_brick")
        if base_mat is None:
            base_mat = smooth
        if width == 1:
            end = top_y if broken is None else y0 + broken
            self.fill(x, y0, z, x, end - 1, z, pillar)
            if broken is None:
                self.set(x, top_y, z, smooth)
            return
        # 받침
        self.fill(x - 1, y0, z - 1, x + 1, y0, z + 1, base_mat)
        for f, (dx, dz) in DXZ.items():
            self.set(x + dx * 2, y0, z + dz * 2, stairs(stair_m, OPP[f]))
        end = top_y if broken is None else y0 + broken
        # 기둥 몸통: + 모양 + 중심
        for y in range(y0 + 1, end):
            self.set(x, y, z, pillar)
            for dx, dz in DXZ.values():
                self.set(x + dx, y, z + dz, pillar)
            if y == y0 + 1:
                for dx in (-1, 1):
                    for dz in (-1, 1):
                        self.set(x + dx, y, z + dz, stairs(stair_m, facing_to(-dx, 0) if self.rand() < 0.5 else facing_to(0, -dz)))
        if broken is None:
            # 주두 (capital)
            self.fill(x - 1, top_y, z - 1, x + 1, top_y, z + 1, smooth)
            for f, (dx, dz) in DXZ.items():
                for k in (-1, 0, 1):
                    px = x + dx * 2 + (k if dx == 0 else 0)
                    pz = z + dz * 2 + (k if dz == 0 else 0)
                    self.set(px, top_y, pz, stairs(stair_m, OPP[f], "top"))
        else:
            # 부서진 윗면
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if abs(dx) + abs(dz) == 2:
                        continue
                    r = self.rand()
                    if r < 0.35:
                        self.set(x + dx, end, z + dz, slab(stair_m))
                    elif r < 0.55:
                        self.set(x + dx, end, z + dz, pillar)
                        if self.rand() < 0.4:
                            self.set(x + dx, end + 1, z + dz, slab(stair_m))
                    elif r < 0.7 and end - 1 > y0 + 1:
                        self.set(x + dx, end - 1, z + dz, "air")

    def fallen_column(self, x, y, z, length, axis="x", mat="quartz"):
        pillar = f"quartz_pillar[axis={axis}]" if mat == "quartz" else mat
        smooth = "smooth_quartz" if mat == "quartz" else mat
        segs = []
        i = 0
        while i < length:
            seg = min(length - i, int(self.r.integers(2, 5)))
            for k in range(seg):
                px = x + (i + k if axis == "x" else 0)
                pz = z + (i + k if axis == "z" else 0)
                self.set(px, y, pz, pillar)
                # 둥근 느낌: 옆 슬랩
                if axis == "x":
                    self.set(px, y, pz - 1, slab("quartz" if mat == "quartz" else "stone_brick"))
                    self.set(px, y, pz + 1, slab("quartz" if mat == "quartz" else "stone_brick"))
                else:
                    self.set(px - 1, y, pz, slab("quartz" if mat == "quartz" else "stone_brick"))
                    self.set(px + 1, y, pz, slab("quartz" if mat == "quartz" else "stone_brick"))
                self.set(px, y + 1, pz, slab("quartz" if mat == "quartz" else "stone_brick"))
            i += seg + (1 if self.rand() < 0.5 else 0)

    # ─────────────────────────────── 불
    def brazier(self, x, y, z, soul=False, tall=2, mat="polished_blackstone"):
        """받침대 위 화로 (y = 받침 시작)"""
        for k in range(tall):
            self.set(x, y + k, z, wall(mat + "_brick") if mat == "polished_blackstone" else wall(mat))
        top = y + tall
        self.set(x, top, z, "chiseled_polished_blackstone" if mat == "polished_blackstone" else "chiseled_stone_bricks")
        self.set(x, top + 1, z, "soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]" if soul else "campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")

    def big_brazier(self, x, y, z, soul=False):
        """3x3 대형 화로"""
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    self.set(x, y, z, "polished_blackstone")
                    self.set(x, y + 1, z, "polished_blackstone")
                else:
                    f = facing_to(-dx, -dz) if abs(dx) != abs(dz) else facing_to(-dx, 0)
                    self.set(x + dx, y, z + dz, stairs("polished_blackstone", f, "top") if abs(dx) + abs(dz) == 1 else "polished_blackstone_wall")
        self.set(x, y + 2, z, "magma_block")
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if abs(dx) + abs(dz) == 1:
                    self.set(x + dx, y + 1, z + dz, "gold_block" if not soul else "polished_blackstone_bricks")
                    self.set(x + dx, y + 2, z + dz, "soul_fire" if soul else "fire")
        self.set(x, y + 3, z, "soul_fire" if soul else "fire")

    # ─────────────────────────────── 나무
    def leaves(self, x, y, z, s):
        if self.w.is_air(x, y, z):
            self.set(x, y, z, s)

    def blob(self, cx, cy, cz, rx, ry, rz, s, density=1.0):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            for y in range(int(cy - ry - 1), int(cy + ry + 2)):
                for z in range(int(cz - rz - 1), int(cz + rz + 2)):
                    d = ((x - cx) / (rx + 0.01)) ** 2 + ((y - cy) / (ry + 0.01)) ** 2 + ((z - cz) / (rz + 0.01)) ** 2
                    if d <= 1.0 and (d < 0.6 or self.rand() < density):
                        self.leaves(x, y, z, s)

    def tree(self, x, y, z, kind="oak", size=1.0):
        """y = 지면 블록 위 첫 칸"""
        r = self.rand
        if kind in ("oak", "birch", "cherry", "olive", "golden"):
            log = {"oak": "oak_log", "birch": "birch_log", "cherry": "cherry_log", "olive": "dark_oak_log", "golden": "oak_log"}[kind]
            leaf = {"oak": "oak_leaves", "birch": "birch_leaves", "cherry": "cherry_leaves",
                    "olive": "azalea_leaves", "golden": "flowering_azalea_leaves"}[kind]
            leaf += "[distance=7,persistent=true,waterlogged=false]"
            h = int((5 + r() * 3) * size)
            if kind == "olive":
                h = int((3 + r() * 2) * size)
            for k in range(h):
                self.set(x, y + k, z, log + "[axis=y]")
            # 가지
            nb = 2 + int(r() * 2 * size)
            tops = [(x, y + h, z)]
            for i in range(nb):
                ang = r() * 6.28
                L = int(2 + r() * 2 * size)
                by = y + int(h * (0.5 + r() * 0.35))
                px, pz = x, z
                for s in range(1, L + 1):
                    px = x + round(math.cos(ang) * s)
                    pz = z + round(math.sin(ang) * s)
                    ax = "x" if abs(math.cos(ang)) > abs(math.sin(ang)) else "z"
                    self.set(px, by + s // 2, pz, log + f"[axis={ax}]")
                tops.append((px, by + L // 2 + 1, pz))
            for (tx, ty, tz) in tops:
                rr = (2.2 + r() * 1.2) * size
                self.blob(tx, ty, tz, rr, rr * 0.7, rr, leaf, 0.7)
        elif kind == "spruce":
            leaf = "spruce_leaves[distance=7,persistent=true,waterlogged=false]"
            h = int((9 + r() * 5) * size)
            for k in range(h):
                self.set(x, y + k, z, "spruce_log[axis=y]")
            for k in range(3, h + 1):
                rad = (h - k) / h * 3.8 * size + 0.5
                if (k % 2) == 0:
                    rad *= 0.7
                for dx in range(-4, 5):
                    for dz in range(-4, 5):
                        if dx * dx + dz * dz <= rad * rad and (dx or dz or k >= h):
                            self.leaves(x + dx, y + k, z + dz, leaf)
            self.leaves(x, y + h, z, leaf)
            self.leaves(x, y + h + 1, z, leaf)
        elif kind == "dark_oak":
            leaf = "dark_oak_leaves[distance=7,persistent=true,waterlogged=false]"
            h = int((6 + r() * 3) * size)
            self.fill(x, y, z, x + 1, y + h, z + 1, "dark_oak_log[axis=y]")
            for i in range(4):
                ang = r() * 6.28
                L = int(2 + r() * 3)
                by = y + h - 2
                for s in range(1, L + 1):
                    px = x + round(math.cos(ang) * s); pz = z + round(math.sin(ang) * s)
                    self.set(px, by + s // 2, pz, "dark_oak_log[axis=y]")
                self.blob(px, by + L // 2 + 1, pz, 3.2 * size, 2.0, 3.2 * size, leaf, 0.75)
            self.blob(x + 0.5, y + h + 1, z + 0.5, 4.5 * size, 2.5, 4.5 * size, leaf, 0.7)
        elif kind == "dead":
            h = int(4 + r() * 3)
            for k in range(h):
                self.set(x, y + k, z, "stripped_dark_oak_log[axis=y]")
            for i in range(2):
                ang = r() * 6.28
                for s in range(1, 3):
                    self.set(x + round(math.cos(ang) * s), y + h - 1 + s // 2, z + round(math.sin(ang) * s), "stripped_dark_oak_log[axis=y]")

    def bush(self, x, y, z, leaf="oak_leaves"):
        s = leaf + "[distance=7,persistent=true,waterlogged=false]"
        self.blob(x, y, z, 1.3 + self.rand(), 0.9, 1.3 + self.rand(), s, 0.65)

    # ─────────────────────────────── 폐허
    def ruin_wall(self, x0, z0, x1, z1, y, h, mat_table, window=True):
        """(x0,z0)→(x1,z1) 직선 벽, 들쭉날쭉한 윗선"""
        n = int(max(abs(x1 - x0), abs(z1 - z0)))
        prof = h
        for i in range(n + 1):
            t = i / max(1, n)
            x = round(x0 + (x1 - x0) * t); z = round(z0 + (z1 - z0) * t)
            prof = int(np.clip(prof + self.r.integers(-1, 2), 1, h + 1))
            if self.rand() < 0.08:
                prof = max(1, prof - 2)
            for k in range(prof):
                if window and 2 <= k <= 3 and i % 5 == 2 and prof > 4:
                    continue
                self.set(x, y + k, z, self.mix(mat_table))
            if self.rand() < 0.5:
                sm = self.mix(mat_table)
                sm_base = {"stone_bricks": "stone_brick", "mossy_stone_bricks": "mossy_stone_brick", "cracked_stone_bricks": "stone_brick",
                           "cobblestone": "cobblestone", "mossy_cobblestone": "mossy_cobblestone", "quartz_bricks": "quartz",
                           "smooth_quartz": "smooth_quartz", "calcite": "polished_diorite", "sandstone": "sandstone",
                           "cut_sandstone": "cut_sandstone", "polished_blackstone_bricks": "polished_blackstone_brick",
                           "blackstone": "blackstone", "tuff_bricks": "tuff_brick", "deepslate_bricks": "deepslate_brick",
                           "andesite": "andesite", "polished_andesite": "polished_andesite", "stone": "stone"}.get(sm)
                if sm_base:
                    self.set(x, y + prof, z, slab(sm_base))

    def rubble(self, x, y, z, rad, mats):
        for dx in range(-rad, rad + 1):
            for dz in range(-rad, rad + 1):
                d = math.hypot(dx, dz)
                if d > rad + 0.3:
                    continue
                if self.rand() < 0.75 - d / (rad + 1) * 0.5:
                    gy = self.top(x + dx, z + dz)
                    if gy < 0:
                        continue
                    s = self.mix(mats)
                    self.set(x + dx, gy + 1, z + dz, s)
                    if d < rad * 0.4 and self.rand() < 0.4:
                        self.set(x + dx, gy + 2, z + dz, self.mix(mats))

    def arch(self, cx, cz, y, span, h, axis, mat="stone_bricks", st="stone_brick", depth=1):
        """반원 아치 (axis = 'x' 면 x방향으로 벌어짐)"""
        half = span / 2
        for i in range(-int(half) - 1, int(half) + 2):
            # 기둥
            for d in range(depth):
                px = cx + (i if axis == "x" else d)
                pz = cz + (d if axis == "x" else i)
                if abs(i) >= half:
                    self.fill(px, y, pz, px, y + h, pz, mat)
                else:
                    ah = y + h - 1 - int(round(math.sqrt(max(0, half * half - i * i)) * (h - 2) / half * 0.6))
                    top = y + h
                    self.fill(px, max(ah, y + 2), pz, px, top, pz, mat)
                    f = ("west" if i < 0 else "east") if axis == "x" else ("north" if i < 0 else "south")
                    if abs(i) > half * 0.4 and ah - 1 >= y:
                        self.set(px, ah - 1, pz, stairs(st, OPP[f], "top"))
