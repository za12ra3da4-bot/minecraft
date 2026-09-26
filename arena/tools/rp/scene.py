"""미리보기 장면 도우미: 장판 데칼 · 간이 플레이어 · 보스 배치"""
import math

import numpy as np
from PIL import Image

import render as R


def decal(mesh, img, key, cx, y, cz, sx, sz, yaw=0.0, fwd_offset=0.0, alpha=1.0, glow=True):
    """바닥 데칼: (cx,cz) 중심, 크기 sx(좌우) x sz(앞뒤), yaw(마크 방향 °), fwd_offset: 앞쪽으로 밀기"""
    if alpha < 1.0:
        a = np.asarray(img).astype(np.float32).copy()
        a[..., 3] *= alpha
        img = Image.fromarray(a.astype(np.uint8))
        key = f"{key}@{alpha:.2f}"
    tid = mesh.texture(key, img)
    r = math.radians(yaw)
    f = np.array([-math.sin(r), 0, math.cos(r)])       # 마크 yaw 전방
    s = np.array([math.cos(r), 0, math.sin(r)])
    c = np.array([cx, y, cz]) + f * fwd_offset
    hw, hl = sx / 2, sz / 2
    p0 = c - s * hw + f * hl      # 이미지 위쪽 = 앞
    p1 = c + s * hw + f * hl
    p2 = c + s * hw - f * hl
    p3 = c - s * hw - f * hl
    # quad(p0..p3): p0=(u0,v1) p1=(u1,v1) p2=(u1,v0) p3=(u0,v0) → v0(이미지 위)를 앞으로
    mesh.quad(p3, p2, p1, p0, (0, 0, 1, 1), tid, flags=(2 | (1 if glow else 0)), light=(1.15, 1.1, 1.1))


PLAYER_COLORS = {"red": (200, 40, 36), "blue": (50, 90, 200), "green": (60, 170, 60), "yellow": (220, 190, 40)}


def _solid(mesh, key, col):
    im = Image.new("RGBA", (4, 4), tuple(col) + (255,))
    return mesh.texture(key, im)


def box(mesh, tid, lo, hi, M, sun):
    x0, y0, z0 = lo; x1, y1, z1 = hi
    faces = {
        "s": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        "n": [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
        "e": [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
        "w": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
        "u": [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
        "d": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
    }
    for k, cs in faces.items():
        pts = [(M @ np.array([*c, 1.0]))[:3] for c in cs]
        n = np.cross(pts[1] - pts[0], pts[3] - pts[0])
        mesh.quad(pts[0], pts[1], pts[2], pts[3], (0, 0, 1, 1), tid, 0, R.face_light(n, sun))


def player(mesh, x, y, z, yaw, team, sun, pose=0.0):
    """간이 플레이어 (갑옷 입은 병사 느낌)"""
    col = PLAYER_COLORS[team]
    t_skin = _solid(mesh, "p_skin", (214, 170, 132))
    t_team = _solid(mesh, f"p_{team}", col)
    t_armor = _solid(mesh, "p_armor", (170, 170, 176))
    t_leg = _solid(mesh, "p_leg", (70, 64, 80))
    t_hair = _solid(mesh, "p_hair", (70, 46, 30))
    t_sword = _solid(mesh, "p_sword", (220, 225, 235))
    a = math.radians(-yaw)
    M = np.array([[math.cos(a), 0, math.sin(a), x], [0, 1, 0, y], [-math.sin(a), 0, math.cos(a), z], [0, 0, 0, 1]])
    u = 1 / 16
    box(mesh, t_leg, (-4 * u, 0, -2 * u), (-0.2 * u, 12 * u, 2 * u), M, sun)
    box(mesh, t_leg, (0.2 * u, 0, -2 * u), (4 * u, 12 * u, 2 * u), M, sun)
    box(mesh, t_team, (-4 * u, 12 * u, -2 * u), (4 * u, 24 * u, 2 * u), M, sun)
    box(mesh, t_armor, (-4.4 * u, 18 * u, -2.4 * u), (4.4 * u, 24.4 * u, 2.4 * u), M, sun)
    box(mesh, t_skin, (-4 * u, 24 * u, -4 * u), (4 * u, 32 * u, 4 * u), M, sun)
    box(mesh, t_armor, (-4.4 * u, 28 * u, -4.4 * u), (4.4 * u, 32.6 * u, 4.4 * u), M, sun)
    box(mesh, t_team, (-8 * u, 12 * u, -2 * u), (-4 * u, 24 * u, 2 * u), M, sun)
    # 오른팔 앞으로 (검)
    Ma = M @ R.tr(6 * u, 22 * u, 0) @ R.rx(-70 + pose * 30) if hasattr(R, "tr") else M
    box(mesh, t_team, (4 * u, 12 * u, -2 * u), (8 * u, 24 * u, 2 * u), M, sun)
    box(mesh, t_sword, (5.5 * u, 11 * u, 1 * u), (6.5 * u, 12 * u, 14 * u), M, sun)
