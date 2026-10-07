"""미리보기 렌더러

 - 복셀 월드: numba 레이트레이서 (텍스처, 태양 그림자, AO, 하늘광, 물/유리 반투명, 안개)
 - 아이템 디스플레이 모델/데칼: 삼각형 래스터라이저 (깊이 버퍼 공유, 반투명은 뒤→앞 블렌딩)
 - 모델 그림자: 태양 방향 섀도우맵

좌표: 월드 배열 vox[x, y, z],  x=동(+), y=위(+), z=남(+)
"""
import math

import numpy as np
from numba import njit, prange
from PIL import Image, ImageFilter

import blocks as B


# ─────────────────────────────────────────────────────────────────────────────
#  팔레트 → numba 배열
# ─────────────────────────────────────────────────────────────────────────────
class Palette:
    def __init__(self, states):
        B.composite_textures()
        P = len(states)
        self.kind = np.zeros(P, np.int32)
        self.nbox = np.zeros(P, np.int32)
        self.boxes = np.zeros((P, 6, 6), np.float32)
        self.ftex = np.zeros((P, 6), np.int32)
        self.tint = np.ones((P, 6, 3), np.float32)
        self.emit = np.zeros(P, np.float32)
        self.alpha = np.ones(P, np.float32)
        self.occ = np.zeros(P, np.float32)
        tex_index = {}
        texs = [np.zeros((16, 16, 4), np.float32)]
        for i, s in enumerate(states):
            d = B.describe(s)
            self.kind[i] = d.kind
            self.nbox[i] = len(d.boxes)
            for j, b in enumerate(d.boxes[:6]):
                self.boxes[i, j] = b
            for f in range(6):
                name = d.tex[f]
                if name is None:
                    continue
                if name not in tex_index:
                    tex_index[name] = len(texs)
                    texs.append(B.load_tex(name))
                self.ftex[i, f] = tex_index[name]
                if d.tint[f] is not None:
                    self.tint[i, f] = d.tint[f]
            self.emit[i] = d.emit
            self.alpha[i] = d.alpha
            if d.kind == 1:
                vol = sum((b[3] - b[0]) * (b[4] - b[1]) * (b[5] - b[2]) for b in d.boxes)
                self.occ[i] = min(1.0, vol)
            elif d.kind == 2:
                self.occ[i] = 0.6
        self.texs = np.stack(texs).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
#  레이 마칭
# ─────────────────────────────────────────────────────────────────────────────
@njit(cache=True, fastmath=True)
def _sample(texs, ti, face, lx, ly, lz):
    if face == 0:
        u = lz; v = 1.0 - ly
    elif face == 1:
        u = 1.0 - lz; v = 1.0 - ly
    elif face == 2:
        u = lx; v = 1.0 - lz
    elif face == 3:
        u = lx; v = lz
    elif face == 4:
        u = 1.0 - lx; v = 1.0 - ly
    else:
        u = lx; v = 1.0 - ly
    iu = int(u * 16.0)
    iv = int(v * 16.0)
    if iu < 0: iu = 0
    if iu > 15: iu = 15
    if iv < 0: iv = 0
    if iv > 15: iv = 15
    return texs[ti, iv, iu, 0], texs[ti, iv, iu, 1], texs[ti, iv, iu, 2], texs[ti, iv, iu, 3]


@njit(cache=True, fastmath=True)
def _march(vox, kind, nbox, boxes, ftex, tint, alpha, texs,
           ox, oy, oz, dx, dy, dz, tmax, shadow):
    """반환: hit, t, cx, cy, cz, face, pal, r, g, b, (투과 누적) ar, ag, ab, trans"""
    X = vox.shape[0]; Y = vox.shape[1]; Z = vox.shape[2]
    ar = 0.0; ag = 0.0; ab = 0.0; trans = 1.0
    # 그리드 AABB 진입
    t0 = 0.0; t1 = tmax
    for ax in range(3):
        if ax == 0:
            o = ox; d = dx; hi = X
        elif ax == 1:
            o = oy; d = dy; hi = Y
        else:
            o = oz; d = dz; hi = Z
        if abs(d) < 1e-9:
            if o < 0.0 or o > hi:
                return False, 0.0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, ar, ag, ab, trans
        else:
            ta = (0.0 - o) / d; tb = (hi - o) / d
            if ta > tb:
                ta, tb = tb, ta
            if ta > t0: t0 = ta
            if tb < t1: t1 = tb
    if t0 > t1:
        return False, 0.0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, ar, ag, ab, trans
    t = t0 + 1e-5
    px = ox + dx * t; py = oy + dy * t; pz = oz + dz * t
    cx = int(math.floor(px)); cy = int(math.floor(py)); cz = int(math.floor(pz))
    if cx >= X: cx = X - 1
    if cy >= Y: cy = Y - 1
    if cz >= Z: cz = Z - 1
    if cx < 0: cx = 0
    if cy < 0: cy = 0
    if cz < 0: cz = 0
    sx = 1 if dx > 0 else -1; sy = 1 if dy > 0 else -1; sz = 1 if dz > 0 else -1
    tdx = abs(1.0 / dx) if abs(dx) > 1e-9 else 1e30
    tdy = abs(1.0 / dy) if abs(dy) > 1e-9 else 1e30
    tdz = abs(1.0 / dz) if abs(dz) > 1e-9 else 1e30
    if abs(dx) > 1e-9:
        tmx = ((cx + (1 if dx > 0 else 0)) - ox) / dx
    else:
        tmx = 1e30
    if abs(dy) > 1e-9:
        tmy = ((cy + (1 if dy > 0 else 0)) - oy) / dy
    else:
        tmy = 1e30
    if abs(dz) > 1e-9:
        tmz = ((cz + (1 if dz > 0 else 0)) - oz) / dz
    else:
        tmz = 1e30
    t_in = t0
    last_tr = -1
    for _ in range(4096):
        if cx < 0 or cy < 0 or cz < 0 or cx >= X or cy >= Y or cz >= Z:
            break
        t_out = min(tmx, min(tmy, tmz))
        if t_in > t1:
            break
        pal = vox[cx, cy, cz]
        if pal != 0:
            k = kind[pal]
            if k == 3:
                # 십자 식물: 두 대각 평면
                best = 1e30; bu = 0.0; bv = 0.0; bface = 3
                lx0 = ox - cx; ly0 = oy - cy; lz0 = oz - cz
                for pl in range(2):
                    if pl == 0:
                        den = dx - dz
                        if abs(den) < 1e-9:
                            continue
                        tt = (lz0 - lx0) / den
                    else:
                        den = dx + dz
                        if abs(den) < 1e-9:
                            continue
                        tt = (1.0 - lx0 - lz0) / den
                    if tt < t_in - 1e-6 or tt > t_out + 1e-6 or tt >= best:
                        continue
                    lx = lx0 + dx * tt; ly = ly0 + dy * tt
                    if lx < 0.0 or lx > 1.0 or ly < 0.0 or ly > 1.0:
                        continue
                    ti = ftex[pal, 0]
                    iu = int(lx * 16.0); iv = int((1.0 - ly) * 16.0)
                    if iu > 15: iu = 15
                    if iv > 15: iv = 15
                    if iu < 0: iu = 0
                    if iv < 0: iv = 0
                    if texs[ti, iv, iu, 3] > 0.5:
                        best = tt; bu = lx; bv = ly
                if best < 1e29:
                    if shadow:
                        return True, best, cx, cy, cz, 3, pal, 0.0, 0.0, 0.0, ar, ag, ab, 0.0
                    ti = ftex[pal, 0]
                    iu = int(bu * 16.0); iv = int((1.0 - bv) * 16.0)
                    if iu > 15: iu = 15
                    if iv > 15: iv = 15
                    r = texs[ti, iv, iu, 0] * tint[pal, 0, 0]
                    g = texs[ti, iv, iu, 1] * tint[pal, 0, 1]
                    b = texs[ti, iv, iu, 2] * tint[pal, 0, 2]
                    return True, best, cx, cy, cz, 6, pal, r, g, b, ar, ag, ab, trans
            else:
                best = 1e30; bface = 0
                nb = nbox[pal]
                for bi in range(nb):
                    bx0 = cx + boxes[pal, bi, 0]; by0 = cy + boxes[pal, bi, 1]; bz0 = cz + boxes[pal, bi, 2]
                    bx1 = cx + boxes[pal, bi, 3]; by1 = cy + boxes[pal, bi, 4]; bz1 = cz + boxes[pal, bi, 5]
                    if k == 5 and by1 < cy + 0.99:
                        # 물: 위가 물이면 꽉 차게
                        if cy + 1 < Y and vox[cx, cy + 1, cz] == pal:
                            by1 = cy + 1.0
                    tn = -1e30; tf = 1e30; fn = 0
                    # x
                    if abs(dx) > 1e-9:
                        ta = (bx0 - ox) / dx; tb = (bx1 - ox) / dx
                        f = 0 if dx > 0 else 1
                        if ta > tb:
                            ta, tb = tb, ta
                        if ta > tn:
                            tn = ta; fn = f
                        if tb < tf: tf = tb
                    elif ox < bx0 or ox > bx1:
                        continue
                    if abs(dy) > 1e-9:
                        ta = (by0 - oy) / dy; tb = (by1 - oy) / dy
                        f = 2 if dy > 0 else 3
                        if ta > tb:
                            ta, tb = tb, ta
                        if ta > tn:
                            tn = ta; fn = f
                        if tb < tf: tf = tb
                    elif oy < by0 or oy > by1:
                        continue
                    if abs(dz) > 1e-9:
                        ta = (bz0 - oz) / dz; tb = (bz1 - oz) / dz
                        f = 4 if dz > 0 else 5
                        if ta > tb:
                            ta, tb = tb, ta
                        if ta > tn:
                            tn = ta; fn = f
                        if tb < tf: tf = tb
                    elif oz < bz0 or oz > bz1:
                        continue
                    if tn > tf or tf < t_in - 1e-6:
                        continue
                    if tn < t_in - 1e-4:
                        continue
                    if tn < best:
                        # 알파 확인
                        hx = ox + dx * tn - cx; hy = oy + dy * tn - cy; hz = oz + dz * tn - cz
                        ti = ftex[pal, fn]
                        r, g, b, a = _sample(texs, ti, fn, hx, hy, hz)
                        if a > 0.5 or k == 5:
                            best = tn; bface = fn
                if best < 1e29:
                    if k == 4 or k == 5:
                        # 반투명: 경계에서만 한 번 누적
                        if last_tr != pal:
                            hx = ox + dx * best - cx; hy = oy + dy * best - cy; hz = oz + dz * best - cz
                            r, g, b, a = _sample(texs, ftex[pal, bface], bface, hx, hy, hz)
                            al = alpha[pal]
                            if shadow:
                                trans *= (1.0 - al * 0.8)
                            else:
                                ar += trans * al * r * tint[pal, bface, 0]
                                ag += trans * al * g * tint[pal, bface, 1]
                                ab += trans * al * b * tint[pal, bface, 2]
                                trans *= (1.0 - al)
                            if trans < 0.03:
                                return True, best, cx, cy, cz, bface, pal, 0.0, 0.0, 0.0, ar, ag, ab, 0.0
                        elif k == 5 and not shadow:
                            # 물 속 흡수
                            ar += trans * 0.08 * 0.10
                            ag += trans * 0.08 * 0.22
                            ab += trans * 0.08 * 0.35
                            trans *= 0.92
                        last_tr = pal
                    else:
                        if shadow:
                            return True, best, cx, cy, cz, bface, pal, 0.0, 0.0, 0.0, ar, ag, ab, 0.0
                        hx = ox + dx * best - cx; hy = oy + dy * best - cy; hz = oz + dz * best - cz
                        r, g, b, a = _sample(texs, ftex[pal, bface], bface, hx, hy, hz)
                        r *= tint[pal, bface, 0]; g *= tint[pal, bface, 1]; b *= tint[pal, bface, 2]
                        return True, best, cx, cy, cz, bface, pal, r, g, b, ar, ag, ab, trans
                else:
                    if k != 4 and k != 5:
                        last_tr = -1
        else:
            last_tr = -1
        # 다음 칸
        if tmx < tmy:
            if tmx < tmz:
                cx += sx; t_in = tmx; tmx += tdx
            else:
                cz += sz; t_in = tmz; tmz += tdz
        else:
            if tmy < tmz:
                cy += sy; t_in = tmy; tmy += tdy
            else:
                cz += sz; t_in = tmz; tmz += tdz
    return False, 0.0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, ar, ag, ab, trans


@njit(cache=True, fastmath=True)
def _occ(vox, occ, x, y, z):
    if x < 0 or y < 0 or z < 0 or x >= vox.shape[0] or y >= vox.shape[1] or z >= vox.shape[2]:
        return 0.0
    return occ[vox[x, y, z]]


@njit(cache=True, fastmath=True)
def _sky(vox, occ, x, y, z):
    """하늘광: 위쪽 5방향으로 막혔는지"""
    tot = 0.0
    for k in range(5):
        if k == 0:
            ddx = 0; ddz = 0
        elif k == 1:
            ddx = 1; ddz = 0
        elif k == 2:
            ddx = -1; ddz = 0
        elif k == 3:
            ddx = 0; ddz = 1
        else:
            ddx = 0; ddz = -1
        vis = 1.0
        for s in range(1, 20):
            v = _occ(vox, occ, x + ddx * s // 2 if k > 0 else x, y + s, z + ddz * s // 2 if k > 0 else z)
            if v > 0.5:
                vis = 0.25 + 0.75 * min(1.0, (s - 1) / 30.0)
                break
        tot += vis * (1.6 if k == 0 else 0.85)
    return tot / 5.0


@njit(parallel=True, cache=True, fastmath=True)
def trace_image(vox, occ, kind, nbox, boxes, ftex, tint, emit, alpha, texs,
                W, H, cam, fwd, right, up, focal, ortho, oscale,
                sun, sun_col, amb_col, sky_top, sky_hor, fog_col, fog_dist,
                sm_use, sm_depth, sm_o, sm_r, sm_u, sm_d, sm_scale,
                out, depth):
    for py in prange(H):
        for px in range(W):
            sxp = px + 0.5 - W * 0.5
            syp = H * 0.5 - (py + 0.5)
            if ortho:
                ox = cam[0] + right[0] * sxp / oscale + up[0] * syp / oscale
                oy = cam[1] + right[1] * sxp / oscale + up[1] * syp / oscale
                oz = cam[2] + right[2] * sxp / oscale + up[2] * syp / oscale
                dx = fwd[0]; dy = fwd[1]; dz = fwd[2]
            else:
                ox = cam[0]; oy = cam[1]; oz = cam[2]
                dx = fwd[0] * focal + right[0] * sxp + up[0] * syp
                dy = fwd[1] * focal + right[1] * sxp + up[1] * syp
                dz = fwd[2] * focal + right[2] * sxp + up[2] * syp
                l = math.sqrt(dx * dx + dy * dy + dz * dz)
                dx /= l; dy /= l; dz /= l
            hit, t, cx, cy, cz, face, pal, r, g, b, ar, ag, ab, trans = _march(
                vox, kind, nbox, boxes, ftex, tint, alpha, texs, ox, oy, oz, dx, dy, dz, 5000.0, False)
            # 하늘
            hy = max(0.0, dy)
            skr = sky_hor[0] + (sky_top[0] - sky_hor[0]) * math.sqrt(hy)
            skg = sky_hor[1] + (sky_top[1] - sky_hor[1]) * math.sqrt(hy)
            skb = sky_hor[2] + (sky_top[2] - sky_hor[2]) * math.sqrt(hy)
            sd = dx * sun[0] + dy * sun[1] + dz * sun[2]
            if sd > 0.0:
                glow = sd ** 64 * 0.9 + sd ** 8 * 0.12
                skr += glow * sun_col[0]; skg += glow * sun_col[1]; skb += glow * sun_col[2]
            if not hit:
                out[py, px, 0] = ar + trans * skr
                out[py, px, 1] = ag + trans * skg
                out[py, px, 2] = ab + trans * skb
                depth[py, px] = 1e30
                continue
            hx = ox + dx * t; hy2 = oy + dy * t; hz = oz + dz * t
            # 법선
            nx = 0.0; ny = 0.0; nz = 0.0
            if face == 0: nx = -1.0
            elif face == 1: nx = 1.0
            elif face == 2: ny = -1.0
            elif face == 3: ny = 1.0
            elif face == 4: nz = -1.0
            elif face == 5: nz = 1.0
            else: ny = 1.0
            ff = 1.0
            if face == 0 or face == 1: ff = 0.72
            elif face == 4 or face == 5: ff = 0.86
            elif face == 2: ff = 0.55
            elif face == 6: ff = 0.9
            # 그림자
            ndl = nx * sun[0] + ny * sun[1] + nz * sun[2]
            if face == 6:
                ndl = 0.75
            sh = 0.0
            if ndl > 0.0:
                sox = hx + nx * 2e-3 + sun[0] * 1e-3
                soy = hy2 + ny * 2e-3 + sun[1] * 1e-3 + (0.02 if face == 6 else 0.0)
                soz = hz + nz * 2e-3 + sun[2] * 1e-3
                h2, _t, _a, _b, _c, _f, _p, _r, _g, _bb, _ar, _ag, _ab, tr2 = _march(
                    vox, kind, nbox, boxes, ftex, tint, alpha, texs, sox, soy, soz, sun[0], sun[1], sun[2], 400.0, True)
                sh = 0.0 if h2 else tr2
                if sm_use and sh > 0.0:
                    rx = hx - sm_o[0]; ry = hy2 - sm_o[1]; rz = hz - sm_o[2]
                    u = (rx * sm_r[0] + ry * sm_r[1] + rz * sm_r[2]) * sm_scale + sm_depth.shape[1] * 0.5
                    v = sm_depth.shape[0] * 0.5 - (rx * sm_u[0] + ry * sm_u[1] + rz * sm_u[2]) * sm_scale
                    iu = int(u); iv = int(v)
                    if iu >= 0 and iv >= 0 and iu < sm_depth.shape[1] and iv < sm_depth.shape[0]:
                        dd = rx * sm_d[0] + ry * sm_d[1] + rz * sm_d[2]
                        if sm_depth[iv, iu] < dd - 0.05:
                            sh = 0.0
            # AO
            qx = cx + int(nx); qy = cy + int(ny); qz = cz + int(nz)
            if face == 6:
                qx = cx; qy = cy; qz = cz
            fx = hx - cx; fy = hy2 - cy; fz = hz - cz
            ao = 1.0
            if face != 6:
                if face == 0 or face == 1:
                    a1 = fy; a2 = fz
                    o1n = _occ(vox, occ, qx, qy - 1, qz); o1p = _occ(vox, occ, qx, qy + 1, qz)
                    o2n = _occ(vox, occ, qx, qy, qz - 1); o2p = _occ(vox, occ, qx, qy, qz + 1)
                elif face == 2 or face == 3:
                    a1 = fx; a2 = fz
                    o1n = _occ(vox, occ, qx - 1, qy, qz); o1p = _occ(vox, occ, qx + 1, qy, qz)
                    o2n = _occ(vox, occ, qx, qy, qz - 1); o2p = _occ(vox, occ, qx, qy, qz + 1)
                else:
                    a1 = fx; a2 = fy
                    o1n = _occ(vox, occ, qx - 1, qy, qz); o1p = _occ(vox, occ, qx + 1, qy, qz)
                    o2n = _occ(vox, occ, qx, qy - 1, qz); o2p = _occ(vox, occ, qx, qy + 1, qz)
                w1n = (1.0 - a1) ** 2; w1p = a1 ** 2; w2n = (1.0 - a2) ** 2; w2p = a2 ** 2
                ao = 1.0 - 0.32 * (o1n * w1n + o1p * w1p + o2n * w2n + o2p * w2p)
                if ao < 0.45: ao = 0.45
            sky = _sky(vox, occ, qx, qy, qz)
            if sky > 1.0: sky = 1.0
            e = emit[pal]
            lr = amb_col[0] * sky * ao * ff + sun_col[0] * ndl * sh * (0.55 + 0.45 * ao)
            lg = amb_col[1] * sky * ao * ff + sun_col[1] * ndl * sh * (0.55 + 0.45 * ao)
            lb = amb_col[2] * sky * ao * ff + sun_col[2] * ndl * sh * (0.55 + 0.45 * ao)
            if e > 0.0:
                lr = lr * (1 - e) + 1.25 * e; lg = lg * (1 - e) + 1.2 * e; lb = lb * (1 - e) + 1.1 * e
            cr = r * lr; cg = g * lg; cb = b * lb
            # 안개
            fo = math.exp(-t / fog_dist)
            cr = cr * fo + fog_col[0] * (1 - fo)
            cg = cg * fo + fog_col[1] * (1 - fo)
            cb = cb * fo + fog_col[2] * (1 - fo)
            out[py, px, 0] = ar + trans * cr
            out[py, px, 1] = ag + trans * cg
            out[py, px, 2] = ab + trans * cb
            if ortho:
                depth[py, px] = t
            else:
                depth[py, px] = t * (dx * fwd[0] + dy * fwd[1] + dz * fwd[2])


# ─────────────────────────────────────────────────────────────────────────────
#  삼각형 래스터라이저 (모델 · 데칼)
# ─────────────────────────────────────────────────────────────────────────────
@njit(cache=True, fastmath=True)
def _proj(px, py, pz, cam, fwd, right, up, focal, ortho, oscale, W, H):
    rx = px - cam[0]; ry = py - cam[1]; rz = pz - cam[2]
    zc = rx * fwd[0] + ry * fwd[1] + rz * fwd[2]
    xc = rx * right[0] + ry * right[1] + rz * right[2]
    yc = rx * up[0] + ry * up[1] + rz * up[2]
    if ortho:
        return W * 0.5 + xc * oscale, H * 0.5 - yc * oscale, zc
    if zc < 0.05:
        zc = 0.05
    return W * 0.5 + xc / zc * focal, H * 0.5 - yc / zc * focal, zc


@njit(cache=True, fastmath=True)
def raster(tris, uvs, tid, flags, shade, tdata, toff, tw, th,
           W, H, cam, fwd, right, up, focal, ortho, oscale, out, depth, translucent_pass, fog_col, fog_dist):
    n = tris.shape[0]
    for i in range(n):
        tr = (flags[i] & 2) != 0
        if tr != translucent_pass:
            continue
        x0, y0, z0 = _proj(tris[i, 0, 0], tris[i, 0, 1], tris[i, 0, 2], cam, fwd, right, up, focal, ortho, oscale, W, H)
        x1, y1, z1 = _proj(tris[i, 1, 0], tris[i, 1, 1], tris[i, 1, 2], cam, fwd, right, up, focal, ortho, oscale, W, H)
        x2, y2, z2 = _proj(tris[i, 2, 0], tris[i, 2, 1], tris[i, 2, 2], cam, fwd, right, up, focal, ortho, oscale, W, H)
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-9:
            continue
        minx = int(max(0.0, math.floor(min(x0, min(x1, x2)))))
        maxx = int(min(W - 1.0, math.ceil(max(x0, max(x1, x2)))))
        miny = int(max(0.0, math.floor(min(y0, min(y1, y2)))))
        maxy = int(min(H - 1.0, math.ceil(max(y0, max(y1, y2)))))
        if minx > maxx or miny > maxy:
            continue
        iz0 = 1.0 / z0; iz1 = 1.0 / z1; iz2 = 1.0 / z2
        if ortho:
            iz0 = 1.0; iz1 = 1.0; iz2 = 1.0
        t = tid[i]
        w_ = tw[t]; h_ = th[t]; off = toff[t]
        sr = shade[i, 0]; sg = shade[i, 1]; sb = shade[i, 2]
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                pxf = xx + 0.5; pyf = yy + 0.5
                b0 = ((x1 - pxf) * (y2 - pyf) - (x2 - pxf) * (y1 - pyf)) / area
                b1 = ((x2 - pxf) * (y0 - pyf) - (x0 - pxf) * (y2 - pyf)) / area
                b2 = 1.0 - b0 - b1
                if b0 < -1e-6 or b1 < -1e-6 or b2 < -1e-6:
                    continue
                iz = b0 * iz0 + b1 * iz1 + b2 * iz2
                if ortho:
                    zz = b0 * z0 + b1 * z1 + b2 * z2
                else:
                    zz = 1.0 / iz
                if zz >= depth[yy, xx]:
                    continue
                u = (b0 * uvs[i, 0, 0] * iz0 + b1 * uvs[i, 1, 0] * iz1 + b2 * uvs[i, 2, 0] * iz2) / iz
                v = (b0 * uvs[i, 0, 1] * iz0 + b1 * uvs[i, 1, 1] * iz1 + b2 * uvs[i, 2, 1] * iz2) / iz
                iu = int(u * w_); iv = int(v * h_)
                if iu < 0: iu = 0
                if iv < 0: iv = 0
                if iu >= w_: iu = w_ - 1
                if iv >= h_: iv = h_ - 1
                k = off + iv * w_ + iu
                a = tdata[k, 3]
                if a < 0.04:
                    continue
                cr = tdata[k, 0] * sr; cg = tdata[k, 1] * sg; cb = tdata[k, 2] * sb
                fo = math.exp(-zz / fog_dist)
                cr = cr * fo + fog_col[0] * (1 - fo)
                cg = cg * fo + fog_col[1] * (1 - fo)
                cb = cb * fo + fog_col[2] * (1 - fo)
                if translucent_pass:
                    if (flags[i] & 4) != 0:
                        # 가산 블렌딩 (빛)
                        out[yy, xx, 0] += cr * a; out[yy, xx, 1] += cg * a; out[yy, xx, 2] += cb * a
                    else:
                        out[yy, xx, 0] = out[yy, xx, 0] * (1 - a) + cr * a
                        out[yy, xx, 1] = out[yy, xx, 1] * (1 - a) + cg * a
                        out[yy, xx, 2] = out[yy, xx, 2] * (1 - a) + cb * a
                else:
                    if a < 0.5:
                        continue
                    out[yy, xx, 0] = cr; out[yy, xx, 1] = cg; out[yy, xx, 2] = cb
                    depth[yy, xx] = zz


@njit(cache=True, fastmath=True)
def raster_depth(tris, flags, W, H, o, r, u, d, scale, depth):
    """태양 시점 정사영 깊이 (모델 그림자용)"""
    for i in range(tris.shape[0]):
        if (flags[i] & 1) != 0 or (flags[i] & 2) != 0:
            continue
        xs = np.zeros(3); ys = np.zeros(3); zs = np.zeros(3)
        for j in range(3):
            rx = tris[i, j, 0] - o[0]; ry = tris[i, j, 1] - o[1]; rz = tris[i, j, 2] - o[2]
            xs[j] = W * 0.5 + (rx * r[0] + ry * r[1] + rz * r[2]) * scale
            ys[j] = H * 0.5 - (rx * u[0] + ry * u[1] + rz * u[2]) * scale
            zs[j] = rx * d[0] + ry * d[1] + rz * d[2]
        area = (xs[1] - xs[0]) * (ys[2] - ys[0]) - (xs[2] - xs[0]) * (ys[1] - ys[0])
        if abs(area) < 1e-9:
            continue
        minx = int(max(0.0, math.floor(xs.min()))); maxx = int(min(W - 1.0, math.ceil(xs.max())))
        miny = int(max(0.0, math.floor(ys.min()))); maxy = int(min(H - 1.0, math.ceil(ys.max())))
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                pxf = xx + 0.5; pyf = yy + 0.5
                b0 = ((xs[1] - pxf) * (ys[2] - pyf) - (xs[2] - pxf) * (ys[1] - pyf)) / area
                b1 = ((xs[2] - pxf) * (ys[0] - pyf) - (xs[0] - pxf) * (ys[2] - pyf)) / area
                b2 = 1.0 - b0 - b1
                if b0 < -1e-6 or b1 < -1e-6 or b2 < -1e-6:
                    continue
                zz = b0 * zs[0] + b1 * zs[1] + b2 * zs[2]
                if zz < depth[yy, xx]:
                    depth[yy, xx] = zz


# ─────────────────────────────────────────────────────────────────────────────
#  메시 (아이템 디스플레이 모델 → 삼각형)
# ─────────────────────────────────────────────────────────────────────────────
class Mesh:
    """텍스처 아틀라스 + 삼각형 목록"""

    def __init__(self):
        self.tex = []        # (H,W,4) float
        self.tex_key = {}
        self.tris = []
        self.uvs = []
        self.tid = []
        self.flags = []
        self.shade = []

    def texture(self, key, img):
        if key in self.tex_key:
            return self.tex_key[key]
        a = np.asarray(img.convert("RGBA"), np.float32) / 255.0
        self.tex_key[key] = len(self.tex)
        self.tex.append(a)
        return self.tex_key[key]

    def quad(self, p0, p1, p2, p3, uv, t, flags=0, light=None):
        """p0..p3 반시계, uv = (u0,v0,u1,v1) 0..1  p0=(u0,v1) p1=(u1,v1) p2=(u1,v0) p3=(u0,v0)"""
        u0, v0, u1, v1 = uv
        self.tris.append([p0, p1, p2]); self.uvs.append([[u0, v1], [u1, v1], [u1, v0]])
        self.tris.append([p0, p2, p3]); self.uvs.append([[u0, v1], [u1, v0], [u0, v0]])
        for _ in range(2):
            self.tid.append(t); self.flags.append(flags)
            self.shade.append(light if light is not None else (1, 1, 1))

    def arrays(self):
        if not self.tris:
            z = np.zeros((0, 3, 3), np.float32)
            return z, np.zeros((0, 3, 2), np.float32), np.zeros(0, np.int32), np.zeros(0, np.int32), np.zeros((0, 3), np.float32), np.zeros((1, 4), np.float32), np.zeros(1, np.int64), np.ones(1, np.int32), np.ones(1, np.int32)
        offs = []; ws = []; hs = []; flat = []; o = 0
        for a in self.tex:
            offs.append(o); hs.append(a.shape[0]); ws.append(a.shape[1])
            flat.append(a.reshape(-1, 4)); o += a.shape[0] * a.shape[1]
        return (np.array(self.tris, np.float32), np.array(self.uvs, np.float32), np.array(self.tid, np.int32),
                np.array(self.flags, np.int32), np.array(self.shade, np.float32), np.concatenate(flat).astype(np.float32),
                np.array(offs, np.int64), np.array(ws, np.int32), np.array(hs, np.int32))


def face_light(n, sun, amb=(0.62, 0.66, 0.78), sun_col=(1.0, 0.93, 0.8), ff=None):
    n = np.asarray(n, float)
    n = n / (np.linalg.norm(n) + 1e-9)
    nd = max(0.0, float(np.dot(n, sun)))
    # 마인크래프트 아이템 조명 느낌: 위 밝고 아래 어둡게
    f = 0.75 + 0.25 * n[1] if ff is None else ff
    return tuple(amb[i] * f + sun_col[i] * nd * 0.75 for i in range(3))


# ─────────────────────────────────────────────────────────────────────────────
#  카메라 + 렌더 진입점
# ─────────────────────────────────────────────────────────────────────────────
def look(cam, target, roll_up=(0, 1, 0)):
    cam = np.asarray(cam, np.float64)
    f = np.asarray(target, np.float64) - cam
    f /= np.linalg.norm(f)
    r = np.cross(f, roll_up); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return cam, f, r, u


def render(vox, pal, W, H, cam, target, fov=60, ortho_scale=None, mesh=None, ss=2,
           sun=(-0.45, 0.78, -0.35), sun_col=(1.05, 0.95, 0.80), amb_col=(0.60, 0.63, 0.70),
           sky_top=(0.36, 0.56, 0.86), sky_hor=(0.78, 0.84, 0.90), fog_col=(0.74, 0.80, 0.88), fog_dist=420.0,
           post=True):
    Wr, Hr = W * ss, H * ss
    sun = np.array(sun, np.float64); sun /= np.linalg.norm(sun)
    c, f, r, u = look(cam, target)
    ortho = ortho_scale is not None
    oscale = (ortho_scale or 1.0) * ss
    focal = (Wr * 0.5) / math.tan(math.radians(fov) * 0.5)
    out = np.zeros((Hr, Wr, 3), np.float32)
    depth = np.full((Hr, Wr), 1e30, np.float32)
    # 모델 그림자맵
    sm_use = False
    sm = np.zeros((1, 1), np.float32)
    sm_o = np.zeros(3); sm_r = np.zeros(3); sm_u = np.zeros(3); sm_d = np.zeros(3); sm_scale = 1.0
    arr = None
    if mesh is not None and mesh.tris:
        arr = mesh.arrays()
        tris = arr[0]
        pts = tris.reshape(-1, 3)
        center = pts.mean(0)
        sm_d = -sun
        sm_o = center - sm_d * 200
        _, _, sm_r, sm_u = look(sm_o, center)
        ext = np.abs(pts - center).max() * 1.8 + 2
        SM = 2048
        sm_scale = SM / (2 * ext)
        sm = np.full((SM, SM), 1e30, np.float32)
        raster_depth(tris, arr[3], SM, SM, sm_o, sm_r, sm_u, sm_d, sm_scale, sm)
        sm_use = True
    trace_image(vox, pal.occ, pal.kind, pal.nbox, pal.boxes, pal.ftex, pal.tint, pal.emit, pal.alpha, pal.texs,
                Wr, Hr, c, f, r, u, focal, ortho, oscale,
                sun, np.array(sun_col), np.array(amb_col), np.array(sky_top), np.array(sky_hor),
                np.array(fog_col), fog_dist, sm_use, sm, sm_o, sm_r, sm_u, sm_d, sm_scale, out, depth)
    if arr is not None:
        tris, uvs, tid, flags, shade, tdata, toff, tw, th = arr
        raster(tris, uvs, tid, flags, shade, tdata, toff, tw, th, Wr, Hr, c, f, r, u, focal, ortho, oscale,
               out, depth, False, np.array(fog_col), fog_dist)
        # 반투명: 뒤→앞
        idx = np.where((flags & 2) != 0)[0]
        if len(idx):
            cen = tris[idx].mean(1)
            dd = (cen - c) @ f
            order = idx[np.argsort(-dd)]
            raster(tris[order], uvs[order], tid[order], flags[order], shade[order], tdata, toff, tw, th, Wr, Hr, c, f, r, u,
                   focal, ortho, oscale, out, depth, True, np.array(fog_col), fog_dist)
    img = np.clip(out, 0, 1)
    if post:
        # 살짝 대비/채도 + 비네팅
        g = img.mean(2, keepdims=True)
        img = np.clip(g + (img - g) * 1.12, 0, 1)
        img = np.clip((img - 0.5) * 1.06 + 0.5, 0, 1)
        yy, xx = np.mgrid[0:Hr, 0:Wr]
        vg = 1 - 0.22 * (((xx - Wr / 2) / (Wr / 2)) ** 2 + ((yy - Hr / 2) / (Hr / 2)) ** 2) ** 1.5
        img = img * np.clip(vg, 0.6, 1)[..., None]
    im = Image.fromarray((img * 255).astype(np.uint8))
    if ss > 1:
        im = im.resize((W, H), Image.LANCZOS)
    return im
