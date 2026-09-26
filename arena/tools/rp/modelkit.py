"""큐보이드 모델 키트: 박스 → 아이템 모델 JSON + 텍스처 아틀라스 (절차적 페인팅) + 뼈대 FK

좌표: 모델 단위 (16 = 1블록, 디스플레이 배율 1 기준). 각 파츠는 피벗이 (0,0,0).
앞 = +Z, 위 = +Y, 오른쪽(보스 기준 왼손) = +X
"""
import math

import numpy as np
from PIL import Image

FACES = ["north", "south", "east", "west", "up", "down"]


# ─────────────────────────────────────────────────────────────────────────────
#  재질 (face painter)
# ─────────────────────────────────────────────────────────────────────────────
def _rng(seed):
    return np.random.default_rng(seed & 0xFFFFFFFF)


def _smooth_noise(w, h, seed, cell=3):
    r = _rng(seed)
    gw, gh = w // cell + 3, h // cell + 3
    g = r.random((gh, gw))
    ys = np.linspace(0, gh - 3, h) if h > 1 else np.zeros(1)
    xs = np.linspace(0, gw - 3, w) if w > 1 else np.zeros(1)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
    a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def col(c):
    return np.array(c[:3], np.float32)


class Mat:
    """기본 재질: 색 + 노이즈 + 가장자리 명암"""

    def __init__(self, base, var=0.12, edge_dark=0.22, top_light=0.12, noise_cell=2, spots=None, pattern=None, alpha=255):
        self.base = col(base)
        self.var = var
        self.edge_dark = edge_dark
        self.top_light = top_light
        self.cell = noise_cell
        self.spots = spots          # (color, density, size)
        self.pattern = pattern      # fn(arr, face, w, h, rng)
        self.alpha = alpha

    def paint(self, w, h, face, seed):
        r = _rng(seed)
        n = _smooth_noise(w, h, seed, max(3, self.cell * 2))
        arr = np.ones((h, w, 3), np.float32) * self.base
        arr *= (1 - self.var * 0.5 + self.var * n)[..., None]
        # 세로 명암: 위 밝고 아래 어둡게 (손그림 느낌)
        if face not in ("up", "down") and h > 1:
            t = np.linspace(0, 1, h)[:, None, None]
            arr *= (1 + self.top_light) - t * self.top_light * 2.2
        if face == "up":
            arr *= 1 + self.top_light * 0.35
        if face == "down":
            arr *= 0.72
        # 테두리: 위 1px 하이라이트, 아래·양옆 1px 어두운 선
        if self.edge_dark > 0 and w > 2 and h > 2:
            if face not in ("down",):
                arr[0, :] = np.minimum(255, arr[0, :] * (1 + self.edge_dark * 0.9))
            arr[-1, :] *= 1 - self.edge_dark
            arr[:, 0] *= 1 - self.edge_dark * 0.45
            arr[:, -1] *= 1 - self.edge_dark * 0.6
        if self.spots:
            c, dens, sz = self.spots
            m = _smooth_noise(w, h, seed + 7, max(2, sz)) > (1 - dens)
            arr[m] = arr[m] * 0.5 + col(c) * 0.5
        out = np.zeros((h, w, 4), np.float32)
        out[..., :3] = arr
        out[..., 3] = self.alpha
        if self.pattern:
            self.pattern(out, face, w, h, r)
        return np.clip(out, 0, 255)


def rivets(spacing=6, color=(255, 230, 170), shadow=(60, 30, 10), margin=1):
    def fn(a, face, w, h, r):
        if w < 5 or h < 5:
            return
        for x in range(margin + 1, w - margin - 1, spacing):
            for y in (margin, h - margin - 1):
                a[y, x, :3] = color
                if y + 1 < h:
                    a[y + 1, x, :3] = shadow
    return fn


def greek_band(y_frac=0.5, color=(255, 214, 120), dark=(70, 40, 12)):
    """그리스 뇌문 띠"""
    def fn(a, face, w, h, r):
        if face in ("up", "down") or h < 6 or w < 6:
            return
        y0 = int(h * y_frac) - 2
        a[y0, :, :3] = dark; a[y0 + 4, :, :3] = dark
        for x in range(w):
            p = x % 6
            ys = {0: [1, 2, 3], 1: [1], 2: [1], 3: [1, 2, 3], 4: [3], 5: [3]}[p]
            for yy in ys:
                if 0 <= y0 + yy < h:
                    a[y0 + yy, x, :3] = color
    return fn


def stripes(c1, c2, width=2, vertical=True):
    def fn(a, face, w, h, r):
        for i in range(w if vertical else h):
            if (i // width) % 2:
                if vertical:
                    a[:, i, :3] = a[:, i, :3] * 0.3 + col(c2) * 0.7
                else:
                    a[i, :, :3] = a[i, :, :3] * 0.3 + col(c2) * 0.7
    return fn


def scales(color_dark, size=4, light=1.25):
    """비늘: 엇갈린 반원 — 각 비늘 위쪽 밝고 아래 테두리 어둡게"""
    def fn(a, face, w, h, r):
        cd = col(color_dark)
        for y in range(h):
            row = y // size
            off = (row % 2) * (size // 2)
            v = y % size
            for x in range(w):
                u = (x + off) % size
                edge = (v == size - 1) or (u == 0 and v >= size // 2)
                if edge:
                    a[y, x, :3] = a[y, x, :3] * 0.45 + cd * 0.55
                elif v <= 1 and 0 < u < size - 1:
                    a[y, x, :3] = np.minimum(255, a[y, x, :3] * light)
    return fn


def fur(dark, light):
    def fn(a, face, w, h, r):
        n = r.random((h, w))
        for x in range(w):
            for y in range(h):
                if n[y, x] > 0.93:
                    L = int(r.integers(1, 3))
                    for k in range(L):
                        if y + k < h:
                            a[y + k, x, :3] = col(dark) if (x + y) % 2 else col(light)
    return fn


def feathers(tip, dark):
    def fn(a, face, w, h, r):
        for y in range(h):
            row = y // 3
            for x in range(w):
                u = (x + row * 2) % 4
                if y % 3 == 2:
                    a[y, x, :3] = a[y, x, :3] * 0.6 + col(dark) * 0.4
                if u == 0:
                    a[y, x, :3] = a[y, x, :3] * 0.75
                if y % 3 == 1 and u in (1, 2):
                    a[y, x, :3] = a[y, x, :3] * 0.5 + col(tip) * 0.5
    return fn


def metal(streak=(64, 140, 118), spec=0.35, streaks=0.05):
    """금속: 위→아래 강한 명암 + 윗모서리 반사 + 드문 녹청 흘러내림"""
    def fn(a, face, w, h, r):
        if face in ("up", "down"):
            a[..., :3] *= 1.0 + spec * 0.15
            return
        if h >= 3:
            t = np.linspace(0, 1, h)[:, None, None]
            a[..., :3] *= (1 + spec * 0.9) - t * spec * 1.3
            a[0, :, :3] = np.minimum(255, a[0, :, :3] * (1 + spec * 1.2))
        for x in range(w):
            if r.random() < streaks:
                L = int(r.integers(2, max(3, h // 2 + 1)))
                y = int(r.integers(0, max(1, h // 3)))
                a[y:y + L, x, :3] = a[y:y + L, x, :3] * 0.5 + np.array(streak) * 0.5
    return fn


def combine(*fns):
    def fn(a, face, w, h, r):
        for f in fns:
            f(a, face, w, h, r)
    return fn


# ─────────────────────────────────────────────────────────────────────────────
#  박스 / 파츠
# ─────────────────────────────────────────────────────────────────────────────
class Box:
    def __init__(self, frm, to, mat, face_fn=None, rot=None, shade=True, skip=(), glow=False):
        self.frm = np.array(frm, float)
        self.to = np.array(to, float)
        self.mat = mat
        self.face_fn = face_fn or {}     # face → fn(arr, w, h)  (재질 위에 덧그림)
        self.rot = rot                    # (axis, angle, origin)  angle ∈ {-45,-22.5,0,22.5,45}
        self.shade = shade and not glow
        self.skip = set(skip)
        self.uv = {}


def rbox(frm, to, mat, face_fn=None, r=1.0, glow=False, skip=()):
    """모서리를 깎은 박스 (세 축 방향으로 한 번씩 늘인 3개 박스) → 둥근 실루엣"""
    x0, y0, z0 = frm; x1, y1, z1 = to
    r = min(r, (x1 - x0) / 3, (y1 - y0) / 3, (z1 - z0) / 3)
    if r <= 0.05:
        return [Box(frm, to, mat, face_fn, glow=glow, skip=skip)]
    soft = soft_mat(mat)
    return [
        Box((x0, y0 + r, z0 + r), (x1, y1 - r, z1 - r), soft, face_fn, glow=glow, skip=skip),
        Box((x0 + r, y0, z0 + r), (x1 - r, y1, z1 - r), soft, face_fn, glow=glow, skip=skip),
        Box((x0 + r, y0 + r, z0), (x1 - r, y1 - r, z1), mat, face_fn, glow=glow, skip=skip),
    ]


_soft = {}


def soft_mat(m):
    """모서리 단 면용: 테두리 선을 약하게"""
    k = id(m)
    if k not in _soft:
        import copy
        s = copy.copy(m)
        s.edge_dark = m.edge_dark * 0.3
        _soft[k] = s
    return _soft[k]


class Part:
    def __init__(self, name, boxes, glow=False):
        self.name = name
        self.boxes = boxes
        self.glow = glow


def face_size(b, face, tpu):
    d = b.to - b.frm
    sx, sy, sz = d
    if face in ("north", "south"):
        w, h = sx, sy
    elif face in ("east", "west"):
        w, h = sz, sy
    else:
        w, h = sx, sz
    return max(1, int(round(w * tpu))), max(1, int(round(h * tpu)))


class Atlas:
    def __init__(self, size=256):
        self.W = size
        self.H = size
        self.img = np.zeros((size, size, 4), np.float32)
        self.x = 0; self.y = 0; self.row = 0

    def alloc(self, w, h):
        if self.x + w > self.W:
            self.x = 0; self.y += self.row; self.row = 0
        if self.y + h > self.H:
            # 늘리기
            nh = self.H * 2
            ni = np.zeros((nh, self.W, 4), np.float32)
            ni[:self.H] = self.img
            self.img = ni; self.H = nh
        p = (self.x, self.y)
        self.x += w
        self.row = max(self.row, h)
        return p

    def image(self):
        # 정사각형(2의 거듭제곱)으로
        H = 1
        while H < self.H:
            H *= 2
        out = np.zeros((max(H, self.W), max(H, self.W), 4), np.uint8)
        out[:self.H, :self.W] = np.clip(self.img, 0, 255).astype(np.uint8)
        return Image.fromarray(out, "RGBA")


def bake_parts(parts, tpu=2, atlas_size=256, seed=1):
    """모든 파츠의 박스 면을 아틀라스에 칠한다. 반환: atlas"""
    at = Atlas(atlas_size)
    s = seed
    # 큰 면부터 배치
    items = []
    for p in parts:
        for b in p.boxes:
            for f in FACES:
                if f in b.skip:
                    continue
                w, h = face_size(b, f, tpu)
                items.append((h, w, p, b, f))
    items.sort(key=lambda t: (-t[0], -t[1]))
    for h, w, p, b, f in items:
        x, y = at.alloc(w, h)
        s += 1
        arr = b.mat.paint(w, h, f, s * 7919)
        fn = b.face_fn.get(f) or b.face_fn.get("*")
        if fn:
            fn(arr, w, h)
        at.img[y:y + h, x:x + w] = arr
        b.uv[f] = (x, y, x + w, y + h)
    return at


def model_json(part, tex_ref, atlas_w, atlas_h):
    els = []
    for b in part.boxes:
        frm = (b.frm + 8).tolist()
        to = (b.to + 8).tolist()
        for v in frm + to:
            assert -16 <= v <= 32, (part.name, frm, to)
        faces = {}
        for f in FACES:
            if f in b.skip or f not in b.uv:
                continue
            x0, y0, x1, y1 = b.uv[f]
            faces[f] = {"uv": [round(x0 * 16 / atlas_w, 4), round(y0 * 16 / atlas_h, 4),
                               round(x1 * 16 / atlas_w, 4), round(y1 * 16 / atlas_h, 4)], "texture": "#0"}
        e = {"from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to], "faces": faces}
        if not b.shade or part.glow:
            e["shade"] = False
            e["light_emission"] = 15
        if b.rot:
            ax, ang, org = b.rot
            e["rotation"] = {"axis": ax, "angle": ang, "origin": [o + 8 for o in org]}
        els.append(e)
    return {"textures": {"0": tex_ref, "particle": tex_ref}, "elements": els}


# ─────────────────────────────────────────────────────────────────────────────
#  뼈대 FK
# ─────────────────────────────────────────────────────────────────────────────
def rx(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]])


def ry(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]])


def rz(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


def tr(x, y, z):
    m = np.eye(4); m[:3, 3] = (x, y, z); return m


def sc(k):
    m = np.eye(4); m[0, 0] = m[1, 1] = m[2, 2] = k; return m


def euler(r):
    return ry(r[1]) @ rx(r[0]) @ rz(r[2])


class Bone:
    def __init__(self, name, parent, offset, part=None, rest=(0, 0, 0), scale=1.0):
        self.name = name
        self.parent = parent
        self.offset = np.array(offset, float)   # 단위
        self.part = part
        self.rest = np.array(rest, float)
        self.scale = scale


class Rig:
    def __init__(self, name, k):
        self.name = name
        self.k = k                   # 전체 배율
        self.bones = {}
        self.order = []

    def bone(self, name, parent, offset, part=None, rest=(0, 0, 0), scale=1.0):
        b = Bone(name, parent, offset, part, rest, scale)
        self.bones[name] = b
        self.order.append(name)
        return b

    def world(self, pose):
        """pose: {bone: (rx,ry,rz)} 또는 {'_root': (tx,ty,tz), '_rootrot': (..)}  → {bone: 4x4 (블록 단위, 배율 적용 전)}"""
        W = {}
        root_t = pose.get("_root", (0, 0, 0))
        root_r = pose.get("_rootrot", (0, 0, 0))
        for n in self.order:
            b = self.bones[n]
            r = b.rest + np.array(pose.get(n, (0, 0, 0)), float)
            off = b.offset / 16.0
            extra = pose.get(n + "@t", (0, 0, 0))
            off = off + np.array(extra, float) / 16.0
            if b.parent is None:
                M = tr(*(np.array(root_t, float) / 16.0)) @ euler(root_r) @ tr(*off) @ euler(r)
            else:
                M = W[b.parent] @ tr(*off) @ euler(r)
            W[n] = M
        return W

    def display_mats(self, pose):
        """파츠별 display transformation (행 우선 16 floats) — 아이템 디스플레이 Y180 뒤집힘 보정 포함"""
        W = self.world(pose)
        out = {}
        for n in self.order:
            b = self.bones[n]
            if b.part is None:
                continue
            M = sc(self.k) @ W[n] @ sc(b.scale) @ ry(180)
            out[n] = M
        return out


def mat_str(M):
    return "[" + ",".join(f"{v:.4f}f" for v in M.reshape(-1)) + "]"
