// =====================================================================
//  마인크래프트풍 16×16 블록 텍스처 아틀라스 (절차 생성)
// =====================================================================
import * as THREE from 'three';

export const TS = 16, TC = 8, TR = 7;
export const TILE_NAMES = [
  'stone', 'cobble', 'sbrick', 'deep', 'dirt', 'grass_top', 'grass_side', 'pl_spruce',
  'pl_dark', 'pl_oak', 'log_side', 'log_top', 'copper', 'cutcop', 'weath', 'oxid',
  'gold', 'iron', 'glass', 'window', 'wool', 'plaster', 'leaves', 'lamp',
  'bricks', 'water', 'diron', 'black', 'red', 'brown', 'canvas', 'roof_red',
  'roof_teal', 'roof_cop', 'polish', 'mossy', 'crystal', 'brass', 'grate', 'foam',
  'hay_side', 'hay_top', 'path', 'flower', 'dtiles', 'window_dim',
];
export const T = {};
TILE_NAMES.forEach((n, i) => (T[n] = i));

export function mulberry(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export function h3(x, y, z, s = 0) {
  let n = Math.imul(x | 0, 374761393) ^ Math.imul(y | 0, 668265263) ^ Math.imul(z | 0, 1440662683) ^ Math.imul(s | 0, 2246822519);
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  n ^= n >>> 16;
  return (n >>> 0) / 4294967296;
}

export function buildAtlas() {
  const cv = document.createElement('canvas');
  cv.width = TC * TS; cv.height = TR * TS;
  const ctx = cv.getContext('2d');
  const im = ctx.createImageData(cv.width, cv.height);
  const D = im.data;
  const cl = v => Math.max(0, Math.min(255, Math.round(v)));

  function draw(name, fn) {
    const i = T[name];
    const ox = (i % TC) * TS, oy = Math.floor(i / TC) * TS;
    const R = mulberry(i * 7919 + 13);
    const put = (x, y, c, k = 1, a = 255) => {
      const p = ((oy + y) * cv.width + (ox + x)) * 4;
      D[p] = cl(c[0] * k); D[p + 1] = cl(c[1] * k); D[p + 2] = cl(c[2] * k); D[p + 3] = cl(a);
    };
    for (let y = 0; y < TS; y++) for (let x = 0; x < TS; x++) put(x, y, [255, 0, 255]);
    fn(put, R, i);
  }
  const each = f => { for (let y = 0; y < TS; y++) for (let x = 0; x < TS; x++) f(x, y); };
  const blob = (x, y, s, i, sc = 3) => h3(Math.floor(x / sc), Math.floor(y / sc), s, i);
  const bevel = (x, y) => (x === 0 || y === 0 ? 1.12 : (x === 15 || y === 15 ? 0.8 : 1));

  draw('stone', (put, R) => each((x, y) => {
    let k = 0.92 + R() * 0.16;
    if (blob(x, y, 1, 3, 2) < 0.18) k *= 0.84;
    if (blob(x, y, 2, 5, 3) > 0.85) k *= 1.08;
    put(x, y, [124, 124, 124], k);
  }));

  // 조약돌: 보로노이 셀
  function cobble(put, R, mossy) {
    const pts = [];
    for (let i = 0; i < 9; i++) pts.push([R() * 16, R() * 16, 0.75 + R() * 0.4]);
    each((x, y) => {
      let d1 = 99, d2 = 99, c = 0;
      for (let i = 0; i < pts.length; i++) for (let ox = -16; ox <= 16; ox += 16) for (let oy = -16; oy <= 16; oy += 16) {
        const d = Math.hypot(x + 0.5 - pts[i][0] - ox, y + 0.5 - pts[i][1] - oy);
        if (d < d1) { d2 = d1; d1 = d; c = i; } else if (d < d2) d2 = d;
      }
      let col = [122, 122, 122], k = pts[c][2] * (0.95 + R() * 0.1) - d1 * 0.02;
      if (d2 - d1 < 1.1) { col = [72, 72, 72]; k = 1; }
      if (mossy && blob(x, y, 4, 7, 3) > 0.52 && d2 - d1 >= 1.1) { col = [86, 118, 52]; k = 0.9 + R() * 0.2; }
      put(x, y, col, k);
    });
  }
  draw('cobble', (put, R) => cobble(put, R, false));
  draw('mossy', (put, R) => cobble(put, R, true));

  draw('sbrick', (put, R) => each((x, y) => {
    const row = Math.floor(y / 8), sx = row === 0 ? 15 : 7, ly = y % 8;
    let k = 0.94 + R() * 0.1;
    let c = [128, 128, 126];
    if (ly === 7 || x === sx) { c = [84, 84, 84]; k = 1; }
    else if (ly === 0 || x === (sx + 1) % 16) k *= 1.12;
    else if (ly === 6 || x === (sx + 15) % 16) k *= 0.86;
    if (blob(x, y, 6, 2, 2) < 0.12) k *= 0.9;
    put(x, y, c, k);
  }));

  draw('deep', (put, R) => each((x, y) => {
    let k = 0.88 + R() * 0.22;
    if (y % 4 === 0) k *= 0.82;
    put(x, y, [70, 70, 78], k);
  }));
  draw('dtiles', (put, R) => each((x, y) => {
    let k = 0.9 + R() * 0.15;
    if (x % 8 === 7 || y % 8 === 7) k = 0.55; else if (x % 8 === 0 || y % 8 === 0) k *= 1.15;
    put(x, y, [62, 62, 68], k);
  }));

  draw('dirt', (put, R) => each((x, y) => {
    let k = 0.86 + R() * 0.26;
    const r = R();
    if (r < 0.08) k *= 0.72; else if (r < 0.13) k *= 1.2;
    put(x, y, [134, 96, 67], k);
  }));
  const GR = [96, 158, 54];
  draw('grass_top', (put, R) => each((x, y) => {
    let k = 0.84 + R() * 0.3;
    if (R() < 0.06) k *= 0.8;
    put(x, y, GR, k);
  }));
  draw('flower', (put, R) => each((x, y) => {
    let k = 0.84 + R() * 0.3;
    const r = R();
    if (r < 0.025) put(x, y, [230, 60, 60]);
    else if (r < 0.045) put(x, y, [250, 220, 70]);
    else if (r < 0.06) put(x, y, [240, 240, 250]);
    else if (r < 0.07) put(x, y, [120, 140, 250]);
    else put(x, y, GR, k);
  }));
  draw('grass_side', (put, R) => each((x, y) => {
    const g = y <= 2 || (y === 3 && R() < 0.65) || (y === 4 && R() < 0.22);
    if (g) put(x, y, GR, 0.84 + R() * 0.3);
    else { let k = 0.86 + R() * 0.26; if (R() < 0.08) k *= 0.72; put(x, y, [134, 96, 67], k); }
  }));
  draw('path', (put, R) => each((x, y) => put(x, y, [148, 122, 72], 0.85 + R() * 0.25)));

  function planks(name, c) {
    draw(name, (put, R) => each((x, y) => {
      const board = Math.floor(y / 4), sx = board % 2 ? 11 : 4;
      let k = 1 + (R() - 0.5) * 0.1 + ((x + board * 3) % 7 === 0 ? -0.07 : 0);
      if (y % 4 === 3) k = 0.68;
      else if (x === sx) k = 0.76;
      else if (y % 4 === 0) k *= 1.06;
      put(x, y, c, k);
    }));
  }
  planks('pl_spruce', [114, 84, 50]);
  planks('pl_dark', [70, 46, 22]);
  planks('pl_oak', [166, 134, 82]);

  draw('log_side', (put, R) => each((x, y) => {
    let k = 1 + (R() - 0.5) * 0.22 + (x % 4 === 0 ? -0.2 : 0) + (x % 4 === 2 ? 0.08 : 0);
    if (h3(x, Math.floor(y / 3), 9, 1) < 0.1) k *= 0.8;
    put(x, y, [74, 52, 30], k);
  }));
  draw('log_top', (put, R) => each((x, y) => {
    const d = Math.hypot(x - 7.5, y - 7.5);
    if (d > 7) put(x, y, [74, 52, 30], 0.9 + R() * 0.2);
    else put(x, y, [158, 118, 72], (Math.floor(d * 1.25) % 2 ? 0.84 : 1) * (0.95 + R() * 0.08));
  }));

  draw('copper', (put, R, i) => each((x, y) => {
    let k = 0.88 + blob(x, y, 3, i, 3) * 0.26 + (R() - 0.5) * 0.08;
    k *= bevel(x, y);
    put(x, y, [196, 108, 76], k);
  }));
  function cutPattern(name, colFn) {
    draw(name, (put, R, i) => each((x, y) => {
      const sx = x % 8, sy = y % 8;
      let k = 1 + (R() - 0.5) * 0.1;
      if (sx === 7 || sy === 7) k = 0.7; else if (sx === 0 || sy === 0) k = 1.16;
      put(x, y, colFn(x, y, R, i), k);
    }));
  }
  cutPattern('cutcop', (x, y, R, i) => (blob(x, y, 5, i, 2) > 0.8 ? [224, 142, 104] : [192, 106, 74]));
  cutPattern('weath', (x, y, R, i) => (blob(x, y, 6, i, 2) > 0.45 ? [100, 160, 124] : [170, 118, 86]));
  cutPattern('oxid', (x, y, R, i) => (blob(x, y, 7, i, 2) > 0.82 ? [60, 128, 104] : [80, 160, 132]));

  draw('gold', (put, R, i) => each((x, y) => {
    let k = 0.94 + R() * 0.1;
    k *= bevel(x, y) * (x === 1 || y === 1 ? 1.05 : 1);
    const c = R() < 0.03 ? [255, 250, 210] : [246, 206, 62];
    put(x, y, c, k);
  }));
  draw('brass', (put, R) => each((x, y) => {
    let k = (0.92 + R() * 0.12) * bevel(x, y);
    if ((x === 3 || x === 12) && (y === 3 || y === 12)) k = 0.7;
    put(x, y, [204, 156, 72], k);
  }));
  draw('iron', (put, R) => each((x, y) => {
    let k = (0.95 + R() * 0.06) * bevel(x, y);
    if (y % 4 === 0 && x > 0 && x < 15) k *= 0.94;
    put(x, y, [220, 220, 222], k);
  }));
  draw('diron', (put, R) => each((x, y) => {
    let k = (0.9 + R() * 0.15) * bevel(x, y);
    let c = [64, 64, 70];
    if ((x === 2 || x === 13) && (y === 2 || y === 13)) c = [128, 128, 136];
    put(x, y, c, k);
  }));
  draw('glass', (put, R) => each((x, y) => {
    const edge = x === 0 || y === 0 || x === 15 || y === 15;
    if (edge) put(x, y, [220, 238, 245], 1, 235);
    else if ((x - y === 3 || x - y === 4 || x - y === -6) && x > 2 && x < 13) put(x, y, [240, 250, 255], 1, 150);
    else put(x, y, [190, 225, 240], 1, 30);
  }));
  function windowTile(name, lit) {
    draw(name, (put, R) => each((x, y) => {
      const frame = x <= 1 || y <= 1 || x >= 14 || y >= 14 || x === 7 || x === 8 || y === 7 || y === 8;
      if (frame) put(x, y, [58, 38, 20], 0.9 + R() * 0.15);
      else if (lit) put(x, y, [255, 196 - y * 3, 98 - y * 2], 0.9 + R() * 0.12);
      else put(x, y, [40, 52, 66], 0.9 + R() * 0.2);
    }));
  }
  windowTile('window', true);
  windowTile('window_dim', false);
  draw('wool', (put, R) => each((x, y) => put(x, y, [234, 236, 236], (0.95 + R() * 0.06) * ((x + 2 * y) % 5 === 0 ? 0.95 : 1))));
  draw('plaster', (put, R) => each((x, y) => put(x, y, [228, 222, 206], 0.94 + R() * 0.07)));
  draw('red', (put, R) => each((x, y) => put(x, y, [164, 40, 36], (0.92 + R() * 0.1) * ((x + 2 * y) % 5 === 0 ? 0.93 : 1))));
  draw('brown', (put, R) => each((x, y) => put(x, y, [112, 70, 40], (0.92 + R() * 0.1) * ((x + 2 * y) % 5 === 0 ? 0.93 : 1))));
  draw('canvas', (put, R) => each((x, y) => put(x, y, [216, 196, 142], (0.93 + R() * 0.08) * ((x + y) % 2 ? 0.96 : 1.02))));
  draw('black', (put, R) => each((x, y) => put(x, y, [30, 30, 34], 0.85 + R() * 0.3)));
  draw('leaves', (put, R) => each((x, y) => {
    if (R() < 0.17) { put(x, y, [0, 0, 0], 1, 0); return; }
    let k = 0.72 + R() * 0.5;
    put(x, y, [58, 112, 42], k);
  }));
  draw('lamp', (put, R, i) => each((x, y) => {
    const b = blob(x, y, 8, i, 2);
    if (b > 0.85) put(x, y, [255, 246, 205]);
    else put(x, y, [252, 196, 104], 0.82 + b * 0.3);
  }));
  draw('crystal', (put, R) => each((x, y) => {
    let c = [150, 92, 222], k = 0.9 + R() * 0.15;
    if ((x + y) % 5 === 0) c = [232, 202, 255];
    else if ((x - y + 16) % 7 === 0) c = [106, 58, 176];
    put(x, y, c, k);
  }));
  draw('bricks', (put, R) => each((x, y) => {
    const row = Math.floor(y / 4);
    const seam = row % 2 ? (x === 3 || x === 11) : (x === 7 || x === 15);
    if (y % 4 === 3 || seam) put(x, y, [172, 162, 152], 0.9 + R() * 0.1);
    else put(x, y, [150, 74, 56], (0.88 + R() * 0.2) * (y % 4 === 0 ? 1.08 : 1));
  }));
  draw('water', (put, R) => each((x, y) => {
    let k = 0.9 + R() * 0.1;
    if ((x + y * 2) % 9 < 2) k = 1.25;
    put(x, y, [52, 110, 222], k, 190);
  }));
  draw('foam', (put, R) => each((x, y) => put(x, y, [236, 246, 255], 0.94 + R() * 0.06, 225)));
  function roof(name, c) {
    draw(name, (put, R) => each((x, y) => {
      const row = Math.floor(y / 4), w = y % 4;
      let k = (1.1 - w * 0.07) * (0.94 + R() * 0.1);
      if (w === 3) k = 0.6;
      else if (x % 8 === (row % 2 ? 2 : 6)) k *= 0.72;
      put(x, y, c, k);
    }));
  }
  roof('roof_red', [176, 72, 48]);
  roof('roof_teal', [74, 150, 124]);
  roof('roof_cop', [198, 112, 72]);
  draw('polish', (put, R) => each((x, y) => put(x, y, [138, 140, 138], (0.96 + R() * 0.06) * bevel(x, y))));
  draw('grate', (put, R) => each((x, y) => {
    if (x % 4 >= 1 && x % 4 <= 2 && y % 4 >= 1 && y % 4 <= 2) put(x, y, [0, 0, 0], 1, 0);
    else put(x, y, [196, 108, 76], (0.9 + R() * 0.15) * bevel(x, y));
  }));
  draw('hay_side', (put, R) => each((x, y) => {
    if (y === 3 || y === 4 || y === 11 || y === 12) put(x, y, [150, 60, 36], 0.9 + R() * 0.15);
    else put(x, y, [206, 172, 58], (0.85 + R() * 0.2) * (x % 3 === 0 ? 0.88 : 1));
  }));
  draw('hay_top', (put, R) => each((x, y) => put(x, y, [212, 180, 64], (0.85 + R() * 0.2) * (Math.floor(Math.hypot(x - 7.5, y - 7.5)) % 2 ? 0.9 : 1))));

  ctx.putImageData(im, 0, 0);
  const tex = new THREE.CanvasTexture(cv);
  tex.magFilter = THREE.NearestFilter;
  tex.minFilter = THREE.NearestFilter;
  tex.generateMipmaps = false;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// 연기 입자 텍스처 (픽셀 퍼프)
export function puffTexture() {
  const cv = document.createElement('canvas'); cv.width = cv.height = 16;
  const g = cv.getContext('2d');
  const R = mulberry(99);
  for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) {
    const d = Math.hypot(x - 7.5, y - 7.5) / 7.5 + (R() - 0.5) * 0.25;
    if (d > 1) continue;
    const v = 200 + R() * 55;
    g.fillStyle = `rgba(${v},${v},${v},${Math.min(1, (1 - d) * 1.6)})`;
    g.fillRect(x, y, 1, 1);
  }
  const t = new THREE.CanvasTexture(cv);
  t.magFilter = THREE.NearestFilter; t.minFilter = THREE.NearestFilter; t.generateMipmaps = false;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
