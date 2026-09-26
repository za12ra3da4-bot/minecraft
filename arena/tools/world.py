"""복셀 월드 — 맵 생성기의 작업 공간

vox[x, y, z] = 팔레트 인덱스 (0 = air)
월드 좌표 = origin + (x, y, z)
"""
import numpy as np

import blocks as B


class World:
    def __init__(self, sx, sy, sz, origin=(0, 0, 0)):
        self.size = (sx, sy, sz)
        self.vox = np.zeros((sx, sy, sz), np.uint16)
        self.pal = ["air"]
        self.pid = {"air": 0}
        self.origin = origin
        # 블록 디스플레이 / 아이템 디스플레이 장식 (리소스팩 모델) — 맵 좌표 기준
        self.displays = []
        self.markers = {}

    # ── 팔레트
    def id(self, state):
        if state.startswith("minecraft:"):
            state = state[10:]
        i = self.pid.get(state)
        if i is None:
            i = len(self.pal)
            self.pal.append(state)
            self.pid[state] = i
        return i

    def inb(self, x, y, z):
        return 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]

    def set(self, x, y, z, state):
        if self.inb(x, y, z):
            self.vox[x, y, z] = self.id(state)

    def get(self, x, y, z):
        if self.inb(x, y, z):
            return self.pal[self.vox[x, y, z]]
        return "air"

    def is_air(self, x, y, z):
        return (not self.inb(x, y, z)) or self.vox[x, y, z] == 0

    def fill(self, x0, y0, z0, x1, y1, z1, state):
        xa, xb = sorted((x0, x1)); ya, yb = sorted((y0, y1)); za, zb = sorted((z0, z1))
        xa = max(xa, 0); ya = max(ya, 0); za = max(za, 0)
        xb = min(xb, self.size[0] - 1); yb = min(yb, self.size[1] - 1); zb = min(zb, self.size[2] - 1)
        if xa > xb or ya > yb or za > zb:
            return
        self.vox[xa:xb + 1, ya:yb + 1, za:zb + 1] = self.id(state)

    def replace_air(self, x, y, z, state):
        if self.inb(x, y, z) and self.vox[x, y, z] == 0:
            self.vox[x, y, z] = self.id(state)

    def solid(self, x, y, z):
        if not self.inb(x, y, z):
            return False
        v = self.vox[x, y, z]
        if v == 0:
            return False
        d = B.describe(self.pal[v])
        return d.kind == 1 and len(d.boxes) == 1 and d.boxes[0] == (0, 0, 0, 1, 1, 1)

    def top(self, x, z):
        """가장 높은 비공기 블록 y (없으면 -1)"""
        if not (0 <= x < self.size[0] and 0 <= z < self.size[2]):
            return -1
        col = self.vox[x, :, z]
        nz = np.nonzero(col)[0]
        return int(nz[-1]) if len(nz) else -1

    def display(self, kind, x, y, z, **kw):
        """장식 디스플레이 (item/block/text) — 맵 좌표 (실수)"""
        d = {"kind": kind, "pos": (x, y, z)}
        d.update(kw)
        self.displays.append(d)
        return d

    def mark(self, name, x, y, z, **kw):
        m = {"pos": (x, y, z)}
        m.update(kw)
        self.markers[name] = m
        return m

    # ── 벽/울타리/판유리 연결 계산 (스키매틱/명령 모두 정확한 상태로 내보내기 위해)
    def fix_connections(self):
        conn_types = {}
        for i, s in enumerate(self.pal):
            bid, p = B.parse(s)
            if bid.endswith("_wall") or bid.endswith("_fence") or bid.endswith("_pane") or bid == "iron_bars":
                conn_types[i] = bid
        if not conn_types:
            return
        full = np.zeros(len(self.pal), bool)
        for i, s in enumerate(self.pal):
            d = B.describe(s)
            full[i] = d.kind in (1, 4) and len(d.boxes) == 1 and d.boxes[0] == (0, 0, 0, 1, 1, 1)
        is_conn = np.zeros(len(self.pal), bool)
        for i in conn_types:
            is_conn[i] = True
        sx, sy, sz = self.size
        idx = np.argwhere(is_conn[self.vox])
        new = {}
        for x, y, z in idx:
            s = self.pal[self.vox[x, y, z]]
            bid, p = B.parse(s)
            wall = bid.endswith("_wall")
            fence = bid.endswith("_fence")
            dirs = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
            q = {}
            cnt = 0
            flags = {}
            for dn, (ddx, ddz) in dirs.items():
                nx, nz = x + ddx, z + ddz
                c = False
                if 0 <= nx < sx and 0 <= nz < sz:
                    nv = self.vox[nx, y, nz]
                    if nv != 0:
                        nb = B.parse(self.pal[nv])[0]
                        if full[nv]:
                            c = True
                        elif is_conn[nv]:
                            if wall:
                                c = nb.endswith("_wall") or nb.endswith("_pane") or nb == "iron_bars" or nb.endswith("_fence_gate")
                            elif fence:
                                c = nb.endswith("_fence") and (("nether" in nb) == ("nether" in bid))
                            else:
                                c = nb.endswith("_pane") or nb == "iron_bars" or nb.endswith("_wall")
                flags[dn] = c
                cnt += c
            if wall:
                above = self.vox[x, y + 1, z] if y + 1 < sy else 0
                tall = {}
                for dn in dirs:
                    tall[dn] = "none"
                    if flags[dn]:
                        tall[dn] = "low"
                        if above != 0 and (full[above] or is_conn[above]):
                            tall[dn] = "tall"
                straight = (flags["north"] and flags["south"] and not flags["east"] and not flags["west"]) or \
                           (flags["east"] and flags["west"] and not flags["north"] and not flags["south"])
                up = not straight
                if above != 0 and not full[above] and not is_conn[above]:
                    up = True
                if above != 0 and is_conn[above] and B.parse(self.pal[above])[0].endswith("_wall"):
                    up = up or not straight
                q = {"east": tall["east"], "north": tall["north"], "south": tall["south"], "up": "true" if up else "false",
                     "waterlogged": "false", "west": tall["west"]}
            else:
                q = {"east": str(flags["east"]).lower(), "north": str(flags["north"]).lower(),
                     "south": str(flags["south"]).lower(), "waterlogged": "false", "west": str(flags["west"]).lower()}
            ns = B.fmt(bid, q)
            new[(x, y, z)] = ns
        for (x, y, z), ns in new.items():
            self.vox[x, y, z] = self.id(ns)

    def used_states(self):
        u = np.unique(self.vox)
        return [self.pal[i] for i in u]
