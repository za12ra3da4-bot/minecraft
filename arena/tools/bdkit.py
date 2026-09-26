"""블록 디스플레이 조립 도구

 부품 하나 = block_display 하나:  모델 점 p∈[0,1]^3 →  T + R·(S∘p)
 (마크 transformation 의 left_rotation = R, scale = S, translation = T, right_rotation = 없음)

 좌표: 픽셀 단위(16 = 1블록)로 만들고 마지막에 블록 단위로 바꾼다.
   +y 위,  +z 앞(엔티티가 보는 쪽),  x 좌우.  발밑 가운데가 원점.
 묶음 회전(팔 들기 등)은 rotate(부품들, 축, 각도, 중심) 로 한다.
"""
import math

import numpy as np


def _rx(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _ry(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rz(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def rot(yaw=0.0, pitch=0.0, roll=0.0):
    """R = Ry(yaw) · Rx(pitch) · Rz(roll)"""
    return _ry(yaw) @ _rx(pitch) @ _rz(roll)


def quat(R):
    m = R
    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        w = 0.25 * s; x = (m[2, 1] - m[1, 2]) / s; y = (m[0, 2] - m[2, 0]) / s; z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w = (m[2, 1] - m[1, 2]) / s; x = 0.25 * s; y = (m[0, 1] + m[1, 0]) / s; z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w = (m[0, 2] - m[2, 0]) / s; x = (m[0, 1] + m[1, 0]) / s; y = 0.25 * s; z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w = (m[1, 0] - m[0, 1]) / s; x = (m[0, 2] + m[2, 0]) / s; y = (m[1, 2] + m[2, 1]) / s; z = 0.25 * s
    return (x, y, z, w)


class Part:
    __slots__ = ("block", "R", "S", "T", "glow", "spin")

    def __init__(self, block, R, S, T, glow=False, spin=False):
        self.block = block
        self.R = np.asarray(R, float)
        self.S = np.asarray(S, float)
        self.T = np.asarray(T, float)
        self.glow = glow
        self.spin = spin


class Model:
    def __init__(self):
        self.parts = []

    # 축 정렬 상자 (픽셀 좌표 두 모서리)
    def box(self, block, x0, y0, z0, x1, y1, z1, glow=False):
        lo = np.minimum([x0, y0, z0], [x1, y1, z1]); hi = np.maximum([x0, y0, z0], [x1, y1, z1])
        p = Part(block, np.eye(3), hi - lo, lo, glow)
        self.parts.append(p)
        return p

    # 가운데 · 크기 · 회전으로 상자
    def cbox(self, block, c, s, yaw=0.0, pitch=0.0, roll=0.0, glow=False):
        R = rot(yaw, pitch, roll)
        s = np.asarray(s, float)
        p = Part(block, R, s, np.asarray(c, float) - R @ (s / 2), glow)
        self.parts.append(p)
        return p

    # 두 점을 잇는 막대 (굵기 w×d, 단면은 up 벡터 기준)
    def rod(self, block, a, b, w, d=None, glow=False, twist=0.0):
        a = np.asarray(a, float); b = np.asarray(b, float)
        d = w if d is None else d
        v = b - a; L = np.linalg.norm(v)
        y = v / L
        ref = np.array([0, 0, 1.0]) if abs(y[2]) < 0.9 else np.array([1.0, 0, 0])
        x = np.cross(y, ref); x /= np.linalg.norm(x)
        z = np.cross(x, y)
        R = np.stack([x, y, z], 1) @ _ry(twist)
        s = np.array([w, L, d])
        c = (a + b) / 2
        p = Part(block, R, s, c - R @ (s / 2), glow)
        self.parts.append(p)
        return p

    def mark(self):
        return len(self.parts)

    def since(self, k):
        return self.parts[k:]

    def add(self, other, R=None, t=(0, 0, 0)):
        R = np.eye(3) if R is None else R
        for p in other.parts:
            self.parts.append(Part(p.block, R @ p.R, p.S, R @ p.T + np.asarray(t, float), p.glow, p.spin))
        return self


def rotate(parts, R, pivot):
    pivot = np.asarray(pivot, float)
    for p in parts:
        p.T = pivot + R @ (p.T - pivot)
        p.R = R @ p.R


def move(parts, d):
    for p in parts:
        p.T = p.T + np.asarray(d, float)


def mirror_x(m, parts):
    """좌우 대칭 복사 (회전은 x 반전 행렬로 켤레)"""
    F = np.diag([-1.0, 1, 1])
    out = []
    for p in parts:
        # 상자 모서리 8개를 뒤집은 뒤 같은 모양이 되도록: R' = F R F, 원점은 x축 반대 모서리
        R2 = F @ p.R @ F
        corner = p.T + p.R @ np.array([p.S[0], 0, 0])
        T2 = F @ corner
        q = Part(p.block, R2, p.S.copy(), T2, p.glow, p.spin)
        m.parts.append(q)
        out.append(q)
    return out


# ─────────────────────────────────────────────────────────────── 내보내기
def _f(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") + "f" if abs(v) > 1e-6 else "0f"


def summon_lines(model, at_prefix, x, y, z, yaw, scale, tags, view=1.0, px=16.0, spin_tag='"bg_spin"'):
    """모델(픽셀 좌표) → summon 명령들. scale = 모델 1블록(16px) 당 실제 블록 수"""
    k = scale / px
    out = []
    for p in model.parts:
        q = quat(p.R)
        S = p.S * k; T = p.T * k
        tg = list(dict.fromkeys(list(tags) + ([spin_tag] if p.spin else [])))
        name = p.block
        props = ""
        if "[" in name:
            name, pr = name[:-1].split("[")
            props = ",Properties:{" + ",".join(f'{a}:"{b}"' for a, b in (kv.split("=") for kv in pr.split(","))) + "}"
        bright = ",brightness:{sky:15,block:15}" if p.glow else ""
        out.append(f'{at_prefix} block_display ~{x:.3f} ~{y:.3f} ~{z:.3f} {{Tags:[{",".join(tg)}],Rotation:[{yaw:.1f}f,0f],'
                   f'block_state:{{Name:"minecraft:{name}"{props}}},view_range:{view}f,teleport_duration:2{bright},'
                   f'transformation:{{left_rotation:[{",".join(_f(v) for v in q)}],right_rotation:[0f,0f,0f,1f],'
                   f'translation:[{",".join(_f(v) for v in T)}],scale:[{",".join(_f(v) for v in S)}]}}}}')
    return out


# ─────────────────────────────────────────────────────────────── 미리보기 메쉬
_TEX = {}


def _tex_for(mesh, block):
    import blocks as B
    from PIL import Image
    bid = block.split("[")[0]
    key = ("bd", bid)
    if key in _TEX:
        return _TEX[key]
    try:
        top, side, bot = B.block_tex(bid, {})
        ims = []
        for n in (top, side, bot):
            a = B.load_tex(n)
            ims.append(Image.fromarray((a * 255).astype(np.uint8), "RGBA"))
    except Exception:
        ims = [Image.new("RGBA", (16, 16), (255, 0, 255, 255))] * 3
    ids = tuple(mesh.texture(("bd", bid, i), im) for i, im in enumerate(ims))
    _TEX[key] = ids
    return ids


TRANSLUCENT = ("glass", "ice", "slime", "honey_block")


def add_to_mesh(mesh, model, origin, yaw, scale, sun, px=16.0, time_spin=0.0):
    import render as RR
    _TEX.clear()
    k = scale / px
    Ry = _ry(-yaw)
    o = np.asarray(origin, float)
    corners = np.array([[x, y, z] for x in (0, 1) for y in (0, 1) for z in (0, 1)], float)
    # 면: (꼭짓점 인덱스 4개, 법선 축, 텍스처 0=위 1=옆 2=아래)
    faces = [((0, 1, 3, 2), (-1, 0, 0), 1), ((4, 6, 7, 5), (1, 0, 0), 1), ((0, 4, 5, 1), (0, -1, 0), 2),
             ((2, 3, 7, 6), (0, 1, 0), 0), ((0, 2, 6, 4), (0, 0, -1), 1), ((1, 5, 7, 3), (0, 0, 1), 1)]
    for p in model.parts:
        R = p.R
        T = p.T
        if p.spin and time_spin:
            R = _ry(time_spin) @ R; T = _ry(time_spin) @ T
        W = np.array([o + Ry @ ((T + R @ (p.S * c)) * k) for c in corners])
        tids = _tex_for(mesh, p.block)
        tr = any(s in p.block for s in TRANSLUCENT)
        for idx, n, ti in faces:
            nw = Ry @ R @ np.array(n, float)
            if p.glow:
                light = (1.25, 1.25, 1.25)
            else:
                light = RR.face_light(nw, sun)
            a, b, c, d = (W[i] for i in idx)
            mesh.quad(a, b, c, d, (0, 0, 1, 1), tids[ti], flags=2 if tr else 0, light=light)
