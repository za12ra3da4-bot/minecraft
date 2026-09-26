"""갇히는 곳 찾기 · 고치기

 플레이어 이동을 흉내 낸다 (걷기 · 1.25칸 점프 · 떨어지기 · 헤엄 · 사다리)
   R = 본진에서 갈 수 있는 곳,  E = 본진으로 돌아갈 수 있는 곳
   R - E = 들어가면 못 나오는 곳 (구덩이 · 우물 · 벽 사이 틈 · 좁은 골짜기)
 고치기: 갇힌 곳마다 밖으로 이어지는 계단을 쌓고, 한 칸짜리 틈은 메운다 → 다시 검사, 없어질 때까지
"""
import collections
import math

import numpy as np

import blocks as B

JUMP = 1.25
BODY = 1.8

NOCOL = ("torch", "rail", "button", "pressure_plate", "sign", "banner", "flower", "short_grass", "tall_grass", "fern",
         "vine", "lever", "redstone_wire", "tripwire", "cobweb", "sapling", "mushroom", "dead_bush", "seagrass", "kelp",
         "sugar_cane", "lightning_rod", "chain", "lantern", "candle", "rose", "tulip", "orchid", "allium", "bluet",
         "daisy", "poppy", "dandelion", "cornflower", "lily_of", "wither_rose", "bamboo", "sweet_berry", "cave_vines",
         "glow_lichen", "moss_carpet", "pink_petals", "hanging_roots", "spore_blossom", "light", "structure_void",
         "end_rod", "fire", "leaf_litter", "firefly_bush", "bush", "wildflowers")
CLIMB = ("ladder", "vine", "scaffolding", "twisting_vines", "weeping_vines", "cave_vines")


def col_height(state):
    """칸 안에서 부딪히는 높이 (0 = 통과, 1 = 꽉 참, 1.5 = 울타리 · 담)  / 물 = -1 / 사다리 = -2"""
    bid, _ = B.parse(state)
    if bid == "air" or bid.endswith("_air"):
        return 0.0
    if bid in ("water", "bubble_column") or "waterlogged=true" in state and B.describe(state).kind == 0:
        return -1.0
    if bid == "lava":
        return -1.0
    if any(bid == c or bid.endswith(c) for c in CLIMB):
        return -2.0
    if bid.endswith("_carpet"):
        return 0.0625
    if bid.endswith("_wall_torch") or bid.endswith("_wall_sign") or bid.endswith("_wall_banner") or bid.endswith("_wall_hanging_sign"):
        return 0.0
    if any(k in bid for k in NOCOL) and not bid.endswith("_block"):
        return 0.0
    if bid.endswith("_fence") or bid.endswith("_wall") or bid.endswith("_fence_gate") or bid.endswith("_pane") or bid == "iron_bars":
        return 1.5
    d = B.describe(state)
    if d.kind in (0, 3):
        return 0.0
    if d.kind in (5, 6):
        return -1.0
    if not d.boxes:
        return 0.0
    return float(max(b[4] for b in d.boxes))


class Nav:
    def __init__(self, world):
        self.w = world
        ch = np.array([col_height(s) for s in world.pal], np.float32)
        self.H = ch[world.vox]                    # [x, y, z]
        self.X, self.Y, self.Z = world.vox.shape
        self._build()

    def _free(self, x, z, lo, hi):
        """(x, z) 기둥의 [lo, hi) 높이에 부딪히는 게 없나 (물 · 사다리는 통과)"""
        if not (0 <= x < self.X and 0 <= z < self.Z):
            return False
        H = self.H
        for k in range(max(0, int(math.floor(lo)) - 1), min(self.Y, int(math.ceil(hi)) + 1)):
            h = H[x, k, z]
            if h > 0 and k + h > lo + 1e-3 and k < hi - 1e-3:
                return False
        return True

    def _build(self):
        H = self.H
        X, Y, Z = self.X, self.Y, self.Z
        self.cols = {}                            # (x, z) → [(F, kind)] kind 0 서기 1 물 2 사다리
        for x in range(X):
            for z in range(Z):
                col = H[x, :, z]
                nz = np.nonzero(col)[0]
                if len(nz) == 0:
                    continue
                out = []
                for y in nz:
                    h = col[y]
                    if h > 0:
                        F = y + float(h)
                        if F + BODY <= Y and self._free(x, z, F, F + BODY):
                            out.append((F, 0))
                    elif h == -1 and y + 1 < Y and col[y + 1] <= 0:
                        out.append((float(y), 1))
                    elif h == -2:
                        out.append((float(y), 2))
                if out:
                    self.cols[(x, z)] = sorted(out)
        self.nodes = []
        self.idx = {}
        for (x, z), lst in self.cols.items():
            for F, k in lst:
                self.idx[(x, z, F)] = len(self.nodes)
                self.nodes.append((x, z, F, k))

    def edges(self, i):
        x, z, F, k = self.nodes[i]
        cols = self.cols
        # 헤엄 · 사다리: 위아래로
        if k in (1, 2):
            for F2, k2 in cols.get((x, z), ()):
                if F2 != F and abs(F2 - F) <= 1.5 and self._free(x, z, min(F, F2) + 0.01, max(F, F2) + BODY - 0.01 if F2 > F else F + 0.99):
                    yield self.idx[(x, z, F2)]
        reach = JUMP + (0.3 if k in (1, 2) else 0.0)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            lst = cols.get((nx, nz))
            if not lst:
                continue
            # 올라서기 · 뛰어오르기
            for F2, k2 in lst:
                if F < F2 <= F + reach:
                    if self._free(x, z, F + BODY, F2 + BODY):
                        yield self.idx[(nx, nz, F2)]
            # 같은 높이로 걸어 들어가서 떨어지기
            if self._free(nx, nz, F + 0.01, F + BODY):
                best = None
                for F2, k2 in lst:
                    if F2 <= F + 0.01 and self._free(nx, nz, F2 + 0.01, F + BODY):
                        best = F2
                if best is not None:
                    yield self.idx[(nx, nz, best)]
                # 물 · 사다리 칸으로 들어가기
                for F2, k2 in lst:
                    if k2 in (1, 2) and F - 1 <= F2 <= F + 1:
                        yield self.idx[(nx, nz, F2)]

    def near(self, pos):
        x, y, z = int(math.floor(pos[0])), pos[1], int(math.floor(pos[2]))
        best = None
        for F, k in self.cols.get((x, z), ()):
            if best is None or abs(F - y) < abs(best - y):
                best = F
        return None if best is None else self.idx[(x, z, best)]

    def analyze(self, seeds):
        n = len(self.nodes)
        fwd = [list(self.edges(i)) for i in range(n)]
        rev = [[] for _ in range(n)]
        for i, e in enumerate(fwd):
            for j in e:
                rev[j].append(i)

        def bfs(start, g):
            seen = np.zeros(n, bool)
            q = collections.deque()
            for s in start:
                if s is not None and not seen[s]:
                    seen[s] = True
                    q.append(s)
            while q:
                i = q.popleft()
                for j in g[i]:
                    if not seen[j]:
                        seen[j] = True
                        q.append(j)
            return seen

        s = [self.near(p) for p in seeds]
        R = bfs(s, fwd)
        E = bfs(s, rev)
        # 넉백 · 돌진 스킬로 튕겨 들어갈 수 있는 곳도 포함 (옆 칸에서 2.5칸 위 · 6칸 아래까지)
        extra = []
        for i in np.nonzero(~E & ~R)[0]:
            x, z, F, k = self.nodes[i]
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                for F2, k2 in self.cols.get((x + dx, z + dz), ()):
                    j = self.idx[(x + dx, z + dz, F2)]
                    if R[j] and F2 - 6 < F <= F2 + 2.5 and self._free(x, z, max(F, F2) + 0.01, max(F, F2) + BODY):
                        extra.append(i)
        if extra:
            R = bfs(list(np.nonzero(R)[0]) + extra, fwd)
        self.R, self.E, self.fwd = R, E, fwd
        trap = R & ~E
        # 덩어리로 묶기
        comp = -np.ones(n, np.int32)
        comps = []
        for i in np.nonzero(trap)[0]:
            if comp[i] >= 0:
                continue
            cid = len(comps)
            q = [i]
            comp[i] = cid
            mem = []
            while q:
                a = q.pop()
                mem.append(a)
                for b in list(fwd[a]) + rev[a]:
                    if trap[b] and comp[b] < 0:
                        comp[b] = cid
                        q.append(b)
            comps.append(mem)
        return comps


FACING = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}


def _full(world, x, y, z):
    if not world.inb(x, y, z):
        return False
    s = world.pal[world.vox[x, y, z]]
    d = B.describe(s)
    return d.kind == 1 and len(d.boxes) == 1 and d.boxes[0] == (0, 0, 0, 1, 1, 1)


def fix(world, seeds, log=print, max_iter=12):
    """갇히는 곳이 없어질 때까지 고친다 → 바뀐 칸 목록 [(x, y, z, state)]
       작은 구멍(12칸 이하)은 메우고, 큰 곳(도랑 · 해자 · 연못 · 골짜기)은 벽에 사다리를 12칸마다 붙인다"""
    changed = {}

    def put(x, y, z, st):
        world.set(x, y, z, st)
        changed[(x, y, z)] = world.pal[world.vox[x, y, z]]

    for it in range(max_iter):
        nav = Nav(world)
        comps = nav.analyze(seeds)
        if not comps:
            log(f"[escape] 갇히는 곳 없음 (검사 {it + 1}번)")
            break
        log(f"[escape] {it + 1}번째 검사: 갇히는 곳 {len(comps)}개 ({sum(map(len, comps))}칸)")
        for comp in comps:
            cset = set(comp)
            # 밖으로 나가는 벽: (갇힌 칸, 벽 방향, 벽 위 높이)
            exits = []
            for i in comp:
                x, z, F, k = nav.nodes[i]
                for (dx, dz) in FACING:
                    for F2, k2 in nav.cols.get((x + dx, z + dz), ()):
                        j = nav.idx[(x + dx, z + dz, F2)]
                        if nav.E[j] and F2 > F:
                            exits.append((F2 - F, i, dx, dz, F2))
            if not exits:
                continue
            if len(comp) <= 12:
                # 메우기: 갇힌 칸 바닥을 가장 낮은 출구 높이 - 1 까지 올린다
                low = min(e[0] for e in exits)
                for i in comp:
                    x, z, F, k = nav.nodes[i]
                    y0 = int(math.floor(F))
                    top = max(y0 + 1, int(math.ceil(F + low - 1.0 - 1e-6)))
                    below = world.get(x, y0 - 1, z) if y0 >= 1 else "stone"
                    st = below if y0 >= 1 and nav.H[x, y0 - 1, z] == 1 else "stone"
                    for y in range(y0, top):
                        if nav.H[x, y, z] <= 0 or nav.H[x, y, z] < 1:
                            put(x, y, z, st)
                continue
            # 사다리: 가장 먼 곳부터 12칸 안에 사다리가 없으면 하나 붙인다
            pos = {i: (nav.nodes[i][0], nav.nodes[i][1]) for i in comp}
            ladders = []
            exits.sort(key=lambda e: e[0])
            order = sorted(comp, key=lambda i: (pos[i][0], pos[i][1]))
            for i in order:
                px, pz = pos[i]
                if any(abs(px - lx) + abs(pz - lz) <= 12 for lx, lz in ladders):
                    continue
                cand = [e for e in exits if abs(pos[e[1]][0] - px) + abs(pos[e[1]][1] - pz) <= 8]
                done = False
                for h, a, dx, dz, F2 in sorted(cand, key=lambda e: (e[0] > 6, abs(pos[e[1]][0] - px) + abs(pos[e[1]][1] - pz))):
                    x, z, F, k = nav.nodes[a]
                    y0, y1 = int(math.floor(F)), int(math.ceil(F2)) - 1
                    wx, wz = x + dx, z + dz
                    ok = all(_full(world, wx, y, wz) for y in range(y0, y1 + 1))
                    ok = ok and all(nav.H[x, y, z] in (0, -1) for y in range(y0, y1 + 1))
                    if not ok:
                        continue
                    for y in range(y0, y1 + 1):
                        wet = nav.H[x, y, z] == -1
                        put(x, y, z, f"ladder[facing={FACING[(dx, dz)]},waterlogged={'true' if wet else 'false'}]")
                    ladders.append((x, z))
                    done = True
                    break
                if not done and not ladders:
                    # 사다리를 못 붙이면 가장 낮은 출구 앞에 돌계단 기둥
                    h, a, dx, dz, F2 = exits[0]
                    x, z, F, k = nav.nodes[a]
                    for y in range(int(math.floor(F)), int(math.ceil(F2)) - 1):
                        put(x, y, z, "cobblestone")
                    ladders.append((x, z))
            log(f"[escape]   {len(comp)}칸 → 사다리 {len(ladders)}개")
    return [(x, y, z, st) for (x, y, z), st in sorted(changed.items())]
