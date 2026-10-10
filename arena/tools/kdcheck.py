"""경도 도시 걸어 다니기 검사 — 도둑 시작 자리에서 사람이 걸어서(점프 1칸 · 사다리 · 계단 · 떨어지기) 갈 수 있는 곳을 다 찾고
 · 건물마다 1층 안이 닿는지 · 문 칸이 뚫려 있는지 · 층마다 올라갈 수 있는지
 · 표지(털이 장소 · 감옥 · 구출 · 탈출 · 경찰 출동)가 닿는지
 를 출력한다.   python3 kdcheck.py
"""
import sys
from collections import deque

import numpy as np

import copsgen as G

PASS_KEYS = ("air", "carpet", "torch", "button", "pressure_plate", "lever", "sign", "ladder", "vine",
             "poppy", "dandelion", "cornflower", "azure_bluet", "short_grass", "fern", "rail", "banner",
             "redstone_wire", "tripwire", "_door", "lantern[hanging=true", "end_rod", "lightning_rod", "chain", "snow[")
LOW_KEYS = ("_slab[type=bottom", "_stairs", "daylight_detector")


def classify(name):
    if name.startswith("potted_") or name == "lantern[hanging=false,waterlogged=false]":
        return 2                                   # 작은 장애물 (못 지나감)
    if "trapdoor" in name:
        if "open=true" in name:
            return 0
        return 1 if "half=bottom" in name else 2
    if any(k in name for k in LOW_KEYS):
        return 1
    if name == "air" or name.split("[")[0] == "light" or any(k in name for k in PASS_KEYS):
        return 0
    return 2                                       # 단단함


def analyze(v, pal):
    cls = np.array([classify(n) for n in pal], np.uint8)[v]       # 0 통과 · 1 낮음(밟고 올라섬) · 2 단단
    ladder = np.array(["ladder" in n for n in pal])[v]
    Nx, Hy, Nz = v.shape
    passable = cls == 0
    # 설 수 있는 칸 (발 칸 y): 발이 통과/낮음 · 머리 통과 · (발이 낮음이면 머리 위 하나 더) · 받침 (아래 단단 or 발이 낮음 or 사다리)
    stand = np.zeros_like(passable)
    feet_ok = cls[:, 1:-2, :] <= 1
    head_ok = passable[:, 2:-1, :]
    low = cls[:, 1:-2, :] == 1
    head2 = passable[:, 3:, :]
    below_solid = cls[:, :-3, :] == 2
    st = feet_ok & head_ok & (~low | head2) & (below_solid | low | ladder[:, 1:-2, :])
    stand[:, 1:-2, :] = st
    seen = np.zeros_like(stand)
    q = deque()
    return cls, ladder, stand, seen, q


def flood(v, pal, starts):
    cls, ladder, stand, seen, q = analyze(v, pal)
    Nx, Hy, Nz = v.shape
    passable = cls == 0
    for s in starts:
        if stand[s]:
            seen[s] = True
            q.append(s)
    while q:
        x, y, z = q.popleft()
        cand = []
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Z = x + dx, z + dz
            if not (0 <= X < Nx and 0 <= Z < Nz):
                continue
            # 같은 높이 / 한 칸 위(점프: 내 머리 위가 비어야) / 아래로 떨어지기
            cand.append((X, y, Z))
            if y + 2 < Hy and passable[x, y + 2, z]:
                cand.append((X, y + 1, Z))
            # 떨어지기: 옆 칸 발·머리가 비어 있으면 아래로 받침 찾을 때까지 (최대 24)
            if 0 < y < Hy - 1 and passable[X, y, Z] and passable[X, y + 1, Z] and not stand[X, y, Z]:
                yy = y - 1
                while yy > 0 and y - yy <= 24:
                    if stand[X, yy, Z]:
                        cand.append((X, yy, Z))
                        break
                    if cls[X, yy, Z] == 2:
                        break
                    yy -= 1
        if ladder[x, y, z] or ladder[x, y + 1, z]:
            cand += [(x, y + 1, z), (x, y - 1, z)]
        for c in cand:
            if 0 < c[1] < Hy - 2 and stand[c] and not seen[c]:
                seen[c] = True
                q.append(c)
    return seen, stand, cls


def fxz(side, x0, z0, x1, z1, t, out=0):
    if side == "s":
        return x0 + t, z1 + out
    if side == "n":
        return x1 - t, z0 - out
    if side == "e":
        return x1 + out, z1 - t
    return x0 - out, z0 + t


def main():
    v, marks = G.build()
    pal = G.PAL
    C, FL = G.C, G.FL

    def g(x, y, z):          # 도시 좌표 → 격자
        return (C + int(np.floor(x)), FL + int(np.floor(y)), C + int(np.floor(z)))

    starts = [g(m[0], m[1], m[2]) for k, m in marks.items() if k.startswith("thief_")]
    seen, stand, cls = flood(v, pal, starts)
    print(f"닿는 칸 {int(seen.sum())} / 설 수 있는 칸 {int(stand.sum())}")
    bad = 0
    # 표지
    for k, m in sorted(marks.items()):
        if isinstance(m, str) or k.startswith("thief_") or k in ("wait", "jail"):     # 감옥 안은 일부러 닫힘
            continue
        gx, gy, gz = g(m[0], m[1], m[2])
        ok = any(seen[gx + dx, gy + dy, gz + dz] for dx in (-1, 0, 1) for dz in (-1, 0, 1) for dy in (-1, 0, 1))
        if not ok:
            bad += 1
            print(f"  ✗ 표지 {k} {m[:3]} 에 못 감")
    # 건물
    for b, floors, doors in G.BLDG:
        x0, z0, x1, z1 = b
        for f in range(floors):
            y = FL + 5 * f + 1
            sub = seen[C + x0 + 1:C + x1, y, C + z0 + 1:C + z1]
            canst = stand[C + x0 + 1:C + x1, y, C + z0 + 1:C + z1]
            if canst.sum() == 0:
                continue
            frac = sub.sum() / canst.sum()
            if frac < 0.6:
                bad += 1
                print(f"  ✗ 건물 {b} {f + 1}층: 안쪽 {frac:.0%} 만 닿음 (문 {doors})")
                if f > 0:
                    break
        # 문: 문 칸 2×3 이 비었는지 · 바로 바깥 2칸 · 바로 안 2칸 (발 · 머리) 이 비었는지 · 바깥이 닿는지
        for d in doors:
            w = (x1 - x0 + 1) if d in "sn" else (z1 - z0 + 1)
            m = w // 2 - 1
            probs = []
            reach_out = False
            for t in (m, m + 1):
                for out, hs in ((0, (1, 2, 3)), (1, (1, 2, 3)), (2, (1, 2, 3)), (3, (1, 2)), (4, (1, 2)), (5, (1, 2)), (6, (1, 2)),
                                (-1, (1, 2)), (-2, (1, 2))):
                    X, Z = fxz(d, x0, z0, x1, z1, t, out)
                    for hy in hs:
                        n = pal[v[C + X, FL + hy, C + Z]]
                        if classify(n) != 0 and not (out >= 3 and hy == 1 and classify(n) == 1):
                            probs.append(f"{'문' if out == 0 else ('밖' if out > 0 else '안')}{abs(out)} y+{hy} {n}")
                    if out == 1 and seen[C + X, FL + 1, C + Z]:
                        reach_out = True
            if probs or not reach_out:
                bad += 1
                print(f"  ✗ 건물 {b} 문 {d}: {'바깥에서 못 옴 · ' if not reach_out else ''}{'; '.join(sorted(set(probs))[:6])}")
    print("문 앞에서 치운 거리 시설", G.STATS.get("props_removed"))
    print("문제", bad)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
