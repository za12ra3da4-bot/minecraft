"""지형: 높이맵 + 구역 + 물 + 길 → 블록 기둥 칠하기"""
import math

import numpy as np
from scipy import ndimage

from layout import *
from noise import fbm, ridge, smoothstep, value_noise

S = SIZE


def seg_dist(px, pz, a, b):
    """점 배열 (px,pz) 와 선분 a-b 거리, 선분 위 비율 t"""
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    L2 = vx * vx + vz * vz + 1e-9
    t = np.clip(((px - ax) * vx + (pz - az) * vz) / L2, 0, 1)
    qx = ax + vx * t; qz = az + vz * t
    return np.hypot(px - qx, pz - qz), t


def wiggle_path(a, b, seed, amp=6.0, n=24):
    """a→b 사이를 부드럽게 휘는 경로 점들"""
    r = np.random.default_rng(seed)
    pts = []
    ax, az = a; bx, bz = b
    L = math.hypot(bx - ax, bz - az)
    nx, nz = -(bz - az) / L, (bx - ax) / L
    ph1, ph2 = r.random() * 6.28, r.random() * 6.28
    for i in range(n + 1):
        t = i / n
        w = math.sin(t * math.pi)
        off = amp * w * (0.7 * math.sin(t * 5.1 + ph1) + 0.3 * math.sin(t * 11.3 + ph2))
        pts.append((ax + (bx - ax) * t + nx * off, az + (bz - az) * t + nz * off))
    return pts


class Terrain:
    def __init__(self, seed=7):
        self.seed = seed
        x = np.arange(S, dtype=float)
        self.X, self.Z = np.meshgrid(x, x, indexing="ij")
        self.dC = np.hypot(self.X - C[0], self.Z - C[1])
        self.H = np.full((S, S), float(G))
        self.water = np.full((S, S), -1, np.int32)      # 물 표면 블록 y
        self.zone = np.full((S, S), "", dtype=object)
        self.no_veg = np.zeros((S, S), bool)            # 나무/풀 금지
        self.road = np.zeros((S, S), np.float32)        # 0..1 (길 가중)
        self.road_kind = np.zeros((S, S), np.int8)      # 1 포장 대로, 2 흙길, 3 자갈길
        self.feature = np.zeros((S, S), np.float32)     # 구조물 근처 (언덕 억제)
        self.paths = []                                  # (kind, pts, width)

    # ─────────────────────────────── 스탬프
    def disc_w(self, c, r, fall):
        d = np.hypot(self.X - c[0], self.Z - c[1])
        return 1 - smoothstep(r, r + fall, d), d

    def stamp(self, c, r, fall, h):
        w, d = self.disc_w(c, r, fall)
        self.H = self.H * (1 - w) + h * w
        return w, d

    def ramp(self, a, b, ha, hb, width, fall=2.5):
        d, t = seg_dist(self.X, self.Z, a, b)
        w = 1 - smoothstep(width / 2, width / 2 + fall, d)
        h = ha + (hb - ha) * t
        self.H = self.H * (1 - w) + h * w
        return w

    # ─────────────────────────────── 생성
    def generate(self):
        sd = self.seed
        base = fbm(S, sd) * 2.4
        # 구조물이 있는 곳은 언덕을 누른다
        feat = np.zeros((S, S))
        feat = np.maximum(feat, 1 - smoothstep(MOAT_OUT + 4, MOAT_OUT + 16, self.dC))
        for t in TEAMS:
            w, _ = self.disc_w(team_base(t), BASE_R + 4, 14)
            feat = np.maximum(feat, w)
        for a in ALTARS:
            w, _ = self.disc_w(altar_pos(a), 22, 12)
            feat = np.maximum(feat, w)
        for l in LAIRS:
            w, _ = self.disc_w(lair_pos(l), LAIR_R + 10, 8)
            feat = np.maximum(feat, w)
        # 대로 주변
        for t in TEAMS:
            d, _ = seg_dist(self.X, self.Z, C, team_base(t))
            feat = np.maximum(feat, 1 - smoothstep(6, 16, d))
        self.feature = feat
        free = 1 - feat
        hills = (np.clip(ridge(S, sd + 5, 40), 0, 1) ** 2.2) * 9 + np.clip(fbm(S, sd + 9, ((48, 1.0), (24, 0.5))) , 0, 1) * 6
        self.H = G + base + hills * free

        # 경계 산맥
        m = np.maximum(np.abs(self.X - C[0]), np.abs(self.Z - C[1]))
        mnt = smoothstep(114, 126, m)
        peaks = G + 22 + fbm(S, sd + 11, ((24, 1.0), (12, 0.5), (6, 0.25))) * 9
        self.H = self.H * (1 - mnt) + peaks * mnt

        # 중앙 광장 + 수로
        self.stamp(C, MOAT_IN - 1, 5, G + 1)
        w_moat = (smoothstep(MOAT_IN - 0.5, MOAT_IN + 0.5, self.dC) * (1 - smoothstep(MOAT_OUT - 0.5, MOAT_OUT + 0.5, self.dC)))
        self.H = np.where(w_moat > 0.5, G - 3, self.H)
        self.water = np.where(w_moat > 0.5, G, self.water)
        self.zone[self.dC < MOAT_OUT + 2] = "plaza"
        # 수로 바깥 둔치
        ring = (self.dC >= MOAT_OUT + 0.5) & (self.dC < MOAT_OUT + 6)
        self.H = np.where(ring, np.minimum(self.H, G + 1) * 0.5 + (G + 1) * 0.5, self.H)

        # 본진 고원
        for t, (dirv, _, _, _) in TEAMS.items():
            b = team_base(t)
            self.stamp(b, BASE_R, 3, BASE_H)
            w, d = self.disc_w(b, BASE_R + 8, 0.1)
            self.zone[(d < BASE_R + 6)] = "base_" + t
            # 진입 경사로: 중앙 방향 + 양 대각
            for ang in (0, 50, -50):
                vx, vz = rot(dirv[0] * -1, dirv[1] * -1, ang)   # 중심 방향 = -dir
                a = (b[0] + vx * (BASE_R - 3), b[1] + vz * (BASE_R - 3))
                e = (b[0] + vx * (BASE_R + 11), b[1] + vz * (BASE_R + 11))
                self.ramp(a, e, BASE_H, G + 0.5, 7 if ang == 0 else 6)

        # 제단
        self.altar_terrain()
        # 보스 투기장
        self.lair_terrain()

        # 길
        self.make_paths()
        self.flatten_paths()

        self.Hi = np.round(self.H).astype(np.int32)
        # 수로/물 칸은 정수 높이 강제
        self.Hi = np.where(self.water >= 0, np.minimum(self.Hi, self.water - 1), self.Hi)

    def altar_terrain(self):
        # 아레스: 화산 메사
        a = altar_pos("ares")
        self.stamp(a, 15, 3, G + 9)
        for tgt in (team_base("red"), team_base("blue"), C):
            v = unit(tgt[0] - a[0], tgt[1] - a[1])
            self.ramp((a[0] + v[0] * 11, a[1] + v[1] * 11), (a[0] + v[0] * 29, a[1] + v[1] * 29), G + 9, G + 0.5, 6)
        _, d = self.disc_w(a, 1, 1)
        self.zone[(d < 21) & (self.zone == "")] = "ares"

        # 아테나: 대리석 테라스
        a = altar_pos("athena")
        self.stamp(a, 18, 7, G + 2)
        _, d = self.disc_w(a, 1, 1)
        self.zone[(d < 32) & (self.zone == "")] = "athena"

        # 헤르메스: 협곡 속 첨탑
        a = altar_pos("hermes")
        _, d = self.disc_w(a, 1, 1)
        rim = (d >= 8.5) & (d < 16.5)
        n = value_noise(S, 6, self.seed + 21)
        self.stamp(a, 21, 6, G + 3)
        self.H = np.where(rim, G - 10 + n * 2, self.H)
        self.H = np.where(d < 8.5, G + 9 + (d < 6) * 0, self.H)
        self.water = np.where(rim, G - 8, self.water)
        self.zone[(d < 32) & (self.zone == "")] = "hermes"
        self.chasm = rim

        # 데메테르: 가라앉은 숲 분지
        a = altar_pos("demeter")
        self.stamp(a, 16, 9, G - 3)
        _, d = self.disc_w(a, 1, 1)
        pond_c = (a[0] - 7, a[1] + 6)
        _, dp = self.disc_w(pond_c, 1, 1)
        pond = dp < 5.5
        self.H = np.where(pond, G - 6, self.H)
        self.water = np.where(pond, G - 4, self.water)
        self.zone[(d < 32) & (self.zone == "")] = "demeter"

    def lair_terrain(self):
        for lid, (dirv, boss, name) in LAIRS.items():
            c = lair_pos(lid)
            floor = {"forge": G + 1, "sands": G - 2, "quarry": G - 4, "garden": G + 1}[lid]
            wall = {"forge": G + 13, "sands": G + 11, "quarry": G + 12, "garden": G + 7}[lid]
            n = fbm(S, self.seed + 40 + len(lid), ((12, 1.0), (6, 0.5), (3, 0.25)))
            w_wall, d = self.disc_w(c, LAIR_R + 7, 3)
            self.H = self.H * (1 - w_wall) + (wall + n * 3) * w_wall
            if lid == "quarry":
                # 채석장: 계단식 벽
                for i, rr in enumerate((LAIR_R + 5, LAIR_R + 3, LAIR_R + 1)):
                    inner = d < rr
                    self.H = np.where(inner, np.minimum(self.H, wall - 4 * (i + 1)), self.H)
            self.H = np.where(d < LAIR_R + 0.5, floor, self.H)
            self.zone[(d < LAIR_R + 9)] = "lair_" + lid
            # 입구 3개: 중심 방향, 양옆 본진 방향
            toward = unit(C[0] - c[0], C[1] - c[1])
            side1 = (-dirv[0], 0)
            side2 = (0, -dirv[1])
            for v in (toward, side1, side2):
                v = unit(*v)
                a = (c[0] + v[0] * (LAIR_R - 2), c[1] + v[1] * (LAIR_R - 2))
                e = (c[0] + v[0] * (LAIR_R + 16), c[1] + v[1] * (LAIR_R + 16))
                outer_h = G + 1
                self.ramp(a, e, floor, outer_h, 7, fall=1.5)
            if lid == "sands":
                self.water = np.where((d < 3.5), -1, self.water)

    def make_paths(self):
        P = self.paths
        # 대로: 본진 → 광장
        for t in TEAMS:
            b = team_base(t)
            v = unit(C[0] - b[0], C[1] - b[1])
            a = (b[0] + v[0] * (BASE_R + 2), b[1] + v[1] * (BASE_R + 2))
            e = (C[0] - v[0] * (PLAZA_R - 1), C[1] - v[1] * (PLAZA_R - 1))
            P.append(("paved", [a, e], 7))
        # 본진 → 이웃 제단 (흙길)
        seed = 100
        for t in TEAMS:
            b = team_base(t)
            for a_id in ALTARS:
                ap = altar_pos(a_id)
                if dist(b, ap) < 90:
                    v = unit(ap[0] - b[0], ap[1] - b[1])
                    st = (b[0] + v[0] * (BASE_R + 3), b[1] + v[1] * (BASE_R + 3))
                    en = (ap[0] - v[0] * 16, ap[1] - v[1] * 16)
                    seed += 1
                    P.append(("dirt", wiggle_path(st, en, seed, 5), 5))
        # 제단 → 중앙 (자갈길, 대각 다리까지)
        for a_id in ALTARS:
            ap = altar_pos(a_id)
            v = unit(C[0] - ap[0], C[1] - ap[1])
            st = (ap[0] + v[0] * 16, ap[1] + v[1] * 16)
            en = (C[0] - v[0] * (PLAZA_R - 1), C[1] - v[1] * (PLAZA_R - 1))
            seed += 1
            P.append(("gravel", wiggle_path(st, en, seed, 3), 5))
        # 제단 → 보스 투기장
        for lid in LAIRS:
            lp = lair_pos(lid)
            for a_id in ALTARS:
                ap = altar_pos(a_id)
                if dist(lp, ap) < 60:
                    v = unit(lp[0] - ap[0], lp[1] - ap[1])
                    st = (ap[0] + v[0] * 16, ap[1] + v[1] * 16)
                    en = (lp[0] - v[0] * (LAIR_R + 14), lp[1] - v[1] * (LAIR_R + 14))
                    seed += 1
                    P.append(("dirt", wiggle_path(st, en, seed, 2, 10), 4))

    def flatten_paths(self):
        for kind, pts, width in self.paths:
            # 경로 표본 높이 → 1D 스무딩
            dense = []
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                n = max(2, int(dist(a, b)))
                for k in range(n):
                    t = k / n
                    dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
            dense.append(pts[-1])
            hs = np.array([self.H[int(np.clip(p[0], 0, S - 1)), int(np.clip(p[1], 0, S - 1))] for p in dense])
            hs = ndimage.gaussian_filter1d(hs, 4, mode="nearest")
            hs = np.round(hs * 2) / 2
            code = {"paved": 1, "dirt": 2, "gravel": 3}[kind]
            for i in range(len(dense) - 1):
                a, b = dense[i], dense[i + 1]
                x0 = int(min(a[0], b[0]) - width - 4); x1 = int(max(a[0], b[0]) + width + 4)
                z0 = int(min(a[1], b[1]) - width - 4); z1 = int(max(a[1], b[1]) + width + 4)
                x0, z0 = max(x0, 0), max(z0, 0); x1, z1 = min(x1, S - 1), min(z1, S - 1)
                sx = self.X[x0:x1 + 1, z0:z1 + 1]; sz = self.Z[x0:x1 + 1, z0:z1 + 1]
                d, t = seg_dist(sx, sz, a, b)
                h = hs[i] + (hs[i + 1] - hs[i]) * t
                w = 1 - smoothstep(width / 2, width / 2 + 3, d)
                sub = self.H[x0:x1 + 1, z0:z1 + 1]
                wat = self.water[x0:x1 + 1, z0:z1 + 1] >= 0
                w = np.where(wat, 0, w)
                self.H[x0:x1 + 1, z0:z1 + 1] = sub * (1 - w) + h * w
                core = (d <= width / 2) & ~wat
                rk = self.road_kind[x0:x1 + 1, z0:z1 + 1]
                rk[core & (rk == 0)] = code
                rw = self.road[x0:x1 + 1, z0:z1 + 1]
                np.maximum(rw, (1 - smoothstep(width / 2 - 1, width / 2 + 1, d)).astype(np.float32), out=rw)
        self.no_veg |= self.road > 0.3


def unit(x, z):
    L = math.hypot(x, z) + 1e-9
    return (x / L, z / L)


def rot(x, z, deg):
    a = math.radians(deg)
    return (x * math.cos(a) - z * math.sin(a), x * math.sin(a) + z * math.cos(a))
