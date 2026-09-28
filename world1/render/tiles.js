// =====================================================================
//  블록 텍스처 아틀라스 (16×16, 절차 생성, 바닐라 색감 근사) → RGBA 버퍼
// =====================================================================
import { mulberry, hash3 } from '../gen/noise.js';

export const TS = 16, COLS = 16;
const tiles = [];            // {name, fn}
export const TILE = {};      // name -> index
function T(name, fn) { TILE[name] = tiles.length; tiles.push({ name, fn }); }

const each = (f) => { for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) f(x, y); };
const blob = (x, y, s, i, sc = 3) => hash3(Math.floor(x / sc), Math.floor(y / sc), s, i);
const bevel = (x, y) => (x === 0 || y === 0 ? 1.12 : (x === 15 || y === 15 ? 0.8 : 1));

function noise(c, amp = 0.18, extra) {
  return (put, R, i) => each((x, y) => { let k = 1 + (R() - 0.5) * amp * 2; if (extra) k = extra(x, y, k, R, i); put(x, y, c, k); });
}
function stoneLike(c, spots = 0.18) {
  return (put, R, i) => each((x, y) => {
    let k = 0.92 + R() * 0.16;
    if (blob(x, y, 1, i, 2) < spots) k *= 0.84;
    if (blob(x, y, 2, i, 3) > 0.86) k *= 1.08;
    put(x, y, c, k);
  });
}
function cobble(c, mossy) {
  return (put, R) => {
    const pts = []; for (let i = 0; i < 9; i++) pts.push([R() * 16, R() * 16, 0.78 + R() * 0.38]);
    each((x, y) => {
      let d1 = 99, d2 = 99, ci = 0;
      for (let i = 0; i < 9; i++) for (let ox = -16; ox <= 16; ox += 16) for (let oy = -16; oy <= 16; oy += 16) {
        const d = Math.hypot(x + 0.5 - pts[i][0] - ox, y + 0.5 - pts[i][1] - oy);
        if (d < d1) { d2 = d1; d1 = d; ci = i; } else if (d < d2) d2 = d;
      }
      let col = c, k = pts[ci][2] * (0.95 + R() * 0.1) - d1 * 0.02;
      if (d2 - d1 < 1.1) { col = [c[0] * 0.6, c[1] * 0.6, c[2] * 0.6]; k = 1; }
      if (mossy && blob(x, y, 4, 7, 3) > 0.5 && d2 - d1 >= 1.1) { col = [82, 112, 48]; k = 0.9 + R() * 0.2; }
      put(x, y, col, k);
    });
  };
}
function stoneBricks(c, variant) {
  return (put, R, i) => each((x, y) => {
    const row = Math.floor(y / 8), sx = row === 0 ? 15 : 7, ly = y % 8;
    let k = 0.94 + R() * 0.1, col = c;
    if (ly === 7 || x === sx) { col = [c[0] * 0.66, c[1] * 0.66, c[2] * 0.66]; k = 1; }
    else if (ly === 0 || x === (sx + 1) % 16) k *= 1.1;
    else if (ly === 6 || x === (sx + 15) % 16) k *= 0.88;
    if (variant === 'mossy' && blob(x, y, 5, i, 3) > 0.55) { col = [86, 112, 56]; k = 0.85 + R() * 0.25; }
    if (variant === 'cracked' && (Math.abs(x - 5 - Math.floor(y / 3)) < 1 && y > 2 && y < 13)) { col = [70, 70, 70]; k = 1; }
    put(x, y, col, k);
  });
}
function chiseled(c) {
  return (put, R) => each((x, y) => {
    let k = 0.95 + R() * 0.08;
    const e = Math.min(x, y, 15 - x, 15 - y);
    if (e === 0) k = 0.7; else if (e === 1) k = 1.12; else if (e === 3) k = 0.8; else if (e >= 5 && Math.hypot(x - 7.5, y - 7.5) < 2.5) k = 0.82;
    put(x, y, c, k);
  });
}
function bricks(c, mortar) {
  return (put, R) => each((x, y) => {
    const row = Math.floor(y / 4);
    const seam = row % 2 ? (x === 3 || x === 11) : (x === 7 || x === 15);
    if (y % 4 === 3 || seam) put(x, y, mortar, 0.92 + R() * 0.1);
    else put(x, y, c, (0.86 + R() * 0.22) * (y % 4 === 0 ? 1.08 : 1));
  });
}
function planks(c) {
  return (put, R) => each((x, y) => {
    const board = Math.floor(y / 4), sx = board % 2 ? 11 : 4;
    let k = 1 + (R() - 0.5) * 0.1 + ((x + board * 3) % 7 === 0 ? -0.07 : 0);
    if (y % 4 === 3) k = 0.7; else if (x === sx) k = 0.78; else if (y % 4 === 0) k *= 1.05;
    put(x, y, c, k);
  });
}
function bark(c, stripes = [0.8, 1.08]) {
  return (put, R) => each((x, y) => {
    let k = 1 + (R() - 0.5) * 0.2 + (x % 4 === 0 ? stripes[0] - 1 : 0) + (x % 4 === 2 ? stripes[1] - 1 : 0);
    if (hash3(x, Math.floor(y / 3), 9, 1) < 0.12) k *= 0.8;
    put(x, y, c, k);
  });
}
function birchBark() {
  return (put, R) => each((x, y) => {
    let c = [216, 215, 210], k = 0.94 + R() * 0.1;
    if (hash3(Math.floor(x / 3), y, 3, 1) < 0.14) c = [50, 50, 46];
    put(x, y, c, k);
  });
}
function logTop(inner, outer) {
  return (put, R) => each((x, y) => {
    const d = Math.max(Math.abs(x - 7.5), Math.abs(y - 7.5));
    if (d > 6.6) put(x, y, outer, 0.9 + R() * 0.2);
    else put(x, y, inner, (Math.floor(d * 1.1) % 2 ? 0.86 : 1) * (0.95 + R() * 0.08));
  });
}
function wool(c) { return noise(c, 0.05, (x, y, k) => k * ((x + 2 * y) % 5 === 0 ? 0.94 : 1)); }
function leaves(c, holes = 0.18, flowers) {
  return (put, R) => each((x, y) => {
    if (R() < holes) { put(x, y, [0, 0, 0], 1, 0); return; }
    if (flowers && R() < 0.1) { put(x, y, flowers, 0.9 + R() * 0.2); return; }
    put(x, y, c, 0.7 + R() * 0.5);
  });
}
function tilesPat(c) {
  return (put, R) => each((x, y) => {
    let k = 0.9 + R() * 0.15;
    const row = Math.floor(y / 4), off = row % 2 ? 4 : 0;
    if (y % 4 === 3 || (x + off) % 8 === 7) k = 0.58; else if (y % 4 === 0) k *= 1.1;
    put(x, y, c, k);
  });
}
function glassTile(tint, a = 30) {
  return (put) => each((x, y) => {
    const edge = x === 0 || y === 0 || x === 15 || y === 15;
    if (edge) put(x, y, [tint[0] * 0.95, tint[1] * 0.95, tint[2] * 0.95], 1, 230);
    else if ((x - y === 3 || x - y === -6) && x > 3 && x < 12) put(x, y, [240, 246, 250], 1, 70);
    else put(x, y, tint, 1, a);
  });
}
function stained(c) {
  return (put) => each((x, y) => {
    const edge = x === 0 || y === 0 || x === 15 || y === 15;
    const lead = x === 7 || y === 7;
    if (edge || lead) put(x, y, [40, 40, 44], 1, 255);
    else put(x, y, c, 0.92 + hash3(x, y, 1, c[0]) * 0.16, 200);
  });
}
function cross(fn) { return (put, R, i) => { each((x, y) => put(x, y, [0, 0, 0], 1, 0)); fn(put, R, i); }; }
function blades(c, h = 13) {
  return cross((put, R) => {
    for (let b = 0; b < 7; b++) {
      const bx = 1 + Math.floor(R() * 14), bh = 5 + Math.floor(R() * (h - 4));
      for (let y = 0; y < bh; y++) {
        const x = Math.round(bx + (y / bh) * (R() - 0.5) * 3);
        if (x >= 0 && x < 16) put(x, 15 - y, c, 0.75 + (y / bh) * 0.4);
      }
    }
  });
}
function flower(petal, center, stem = [60, 120, 40]) {
  return cross((put, R) => {
    for (let y = 6; y < 16; y++) put(7, y, stem, 0.9);
    put(6, 11, stem); put(8, 12, stem); put(5, 10, stem, 0.9); put(9, 13, stem, 0.9);
    for (let dx = -2; dx <= 2; dx++) for (let dy = -2; dy <= 2; dy++) if (Math.abs(dx) + Math.abs(dy) <= 3) put(7 + dx, 4 + dy, petal, 0.85 + R() * 0.3);
    put(7, 4, center);
  });
}
function crop(c, top, age = 7) {
  return cross((put, R) => {
    for (let b = 0; b < 5; b++) {
      const bx = 1 + b * 3;
      for (let y = 0; y < 14; y++) put(bx, 15 - y, y > 9 ? top : c, 0.8 + R() * 0.3);
      put(bx + 1, 3, top); put(bx - 1 < 0 ? 0 : bx - 1, 4, top);
    }
  });
}
function doorTile(c, windowed) {
  return (put, R) => each((x, y) => {
    const edge = x <= 1 || x >= 14 || y <= 1 || y >= 14;
    let k = (0.9 + R() * 0.12) * (edge ? 0.78 : 1) * (x % 4 === 3 ? 0.85 : 1);
    if (windowed && y >= 3 && y <= 9 && x >= 3 && x <= 12 && x !== 7 && x !== 8 && y !== 6) { put(x, y, [0, 0, 0], 1, 0); return; }
    if ((x === 12 && y === 8)) { put(x, y, [60, 60, 60]); return; }
    put(x, y, c, k);
  });
}
function trapTile(c) {
  return (put, R) => each((x, y) => {
    const edge = x <= 1 || x >= 14 || y <= 1 || y >= 14;
    const brace = Math.abs(x - y) <= 1 || Math.abs(x + y - 15) <= 1;
    if (!edge && (x === 7 || x === 8) && (y === 4 || y === 11)) { put(x, y, [0, 0, 0], 1, 0); return; }
    let k = (0.9 + R() * 0.12) * (edge ? 0.78 : 1) * (x % 4 === 3 ? 0.86 : 1);
    if (!edge && brace) k *= 0.8;
    put(x, y, c, k);
  });
}

// ── 자연 블록
const GRASS = [104, 158, 58], FOL = [72, 128, 46];
T('stone', stoneLike([125, 125, 125]));
T('andesite', stoneLike([136, 136, 137], 0.3));
T('polished_andesite', noise([132, 134, 133], 0.04, (x, y, k) => k * bevel(x, y)));
T('granite', stoneLike([149, 103, 86], 0.3));
T('diorite', stoneLike([190, 190, 192], 0.3));
T('tuff', stoneLike([108, 109, 102], 0.35));
T('calcite', noise([224, 225, 221], 0.05));
T('cobblestone', cobble([122, 122, 122]));
T('mossy_cobblestone', cobble([118, 118, 118], true));
T('cobbled_deepslate', cobble([78, 78, 82]));
T('gravel', (put, R) => each((x, y) => { const r = R(); put(x, y, r < 0.3 ? [100, 94, 92] : r < 0.6 ? [150, 142, 140] : [128, 122, 120], 0.9 + R() * 0.15); }));
T('dirt', noise([134, 96, 67], 0.14, (x, y, k, R) => { const r = R(); return r < 0.08 ? k * 0.72 : r < 0.13 ? k * 1.2 : k; }));
T('coarse_dirt', noise([118, 86, 60], 0.18, (x, y, k, R) => (R() < 0.2 ? k * 0.7 : k)));
T('grass_top', noise(GRASS, 0.16, (x, y, k, R) => (R() < 0.06 ? k * 0.82 : k)));
T('grass_side', (put, R) => each((x, y) => {
  const g = y <= 2 || (y === 3 && R() < 0.65) || (y === 4 && R() < 0.22);
  put(x, y, g ? GRASS : [134, 96, 67], g ? 0.84 + R() * 0.3 : 0.86 + R() * 0.26);
}));
T('podzol_top', noise([92, 64, 32], 0.2, (x, y, k, R) => (R() < 0.15 ? k * 1.25 : k)));
T('podzol_side', (put, R) => each((x, y) => put(x, y, y <= 3 ? [92, 64, 32] : [134, 96, 67], 0.86 + R() * 0.26)));
T('moss_block', noise([89, 110, 45], 0.15));
T('sand', noise([219, 207, 163], 0.07));
T('sandstone', (put, R) => each((x, y) => put(x, y, [216, 203, 155], (0.94 + R() * 0.06) * (y < 3 ? 1.04 : y > 12 ? 0.95 : 1))));
T('sandstone_top', noise([219, 207, 160], 0.05));
T('smooth_sandstone', noise([223, 214, 170], 0.03));
T('snow_block', noise([246, 250, 252], 0.025));
T('ice', noise([160, 190, 250], 0.05));
T('clay', noise([160, 166, 179], 0.05));
T('bedrock', stoneLike([80, 80, 80], 0.5));
T('deepslate', noise([80, 80, 86], 0.18, (x, y, k) => k * (y % 4 === 0 ? 0.84 : 1)));
T('farmland', noise([96, 62, 38], 0.1, (x, y, k) => k * (y % 4 === 0 ? 0.8 : 1)));
T('path_top', noise([148, 122, 72], 0.16));
T('path_side', (put, R) => each((x, y) => put(x, y, y <= 1 ? [148, 122, 72] : [134, 96, 67], 0.86 + R() * 0.24)));
T('water', (put, R) => each((x, y) => put(x, y, [48, 98, 204], ((x + y * 2) % 9 < 2 ? 1.18 : 0.94 + R() * 0.08), 175)));
// ── 건축 석재
T('stone_bricks', stoneBricks([123, 122, 122]));
T('mossy_stone_bricks', stoneBricks([118, 120, 114], 'mossy'));
T('cracked_stone_bricks', stoneBricks([118, 117, 117], 'cracked'));
T('chiseled_stone_bricks', chiseled([122, 121, 121]));
T('smooth_stone', noise([160, 160, 160], 0.03, (x, y, k) => k * (y === 0 || y === 15 ? 0.85 : 1)));
T('bricks', bricks([150, 74, 58], [168, 158, 150]));
T('mud_bricks', bricks([140, 106, 79], [110, 84, 64]));
T('packed_mud', noise([142, 107, 80], 0.08));
T('deepslate_tiles', tilesPat([56, 56, 60]));
T('deepslate_bricks', bricks([72, 72, 76], [44, 44, 48]));
T('polished_deepslate', noise([72, 72, 76], 0.06, (x, y, k) => k * bevel(x, y)));
T('blackstone', stoneLike([46, 40, 48]));
T('polished_blackstone_bricks', bricks([54, 48, 58], [30, 26, 34]));
T('white_terracotta', noise([210, 180, 162], 0.05));
T('terracotta', noise([152, 94, 67], 0.05));
T('gold_block', noise([246, 208, 62], 0.06, (x, y, k) => k * bevel(x, y)));
T('copper_block', noise([192, 107, 79], 0.1, (x, y, k) => k * bevel(x, y)));
T('amethyst_block', noise([134, 98, 190], 0.14));
// ── 나무
T('oak_planks', planks([162, 130, 78]));
T('spruce_planks', planks([114, 84, 50]));
T('dark_oak_planks', planks([66, 43, 20]));
T('birch_planks', planks([196, 178, 122]));
T('oak_log', bark([108, 84, 50]));
T('spruce_log', bark([58, 38, 18]));
T('dark_oak_log', bark([60, 46, 26]));
T('birch_log', birchBark());
T('oak_log_top', logTop([176, 144, 88], [108, 84, 50]));
T('spruce_log_top', logTop([124, 92, 54], [58, 38, 18]));
T('dark_oak_log_top', logTop([78, 56, 30], [60, 46, 26]));
T('birch_log_top', logTop([200, 184, 128], [216, 215, 210]));
T('stripped_oak_log', bark([176, 142, 86], [0.93, 1.03]));
T('stripped_spruce_log', bark([118, 88, 52], [0.93, 1.03]));
T('stripped_dark_oak_log', bark([96, 72, 46], [0.93, 1.03]));
T('stripped_birch_log', bark([196, 176, 118], [0.93, 1.03]));
T('stripped_oak_log_top', logTop([176, 144, 88], [176, 142, 86]));
T('stripped_spruce_log_top', logTop([124, 92, 54], [118, 88, 52]));
T('stripped_dark_oak_log_top', logTop([78, 56, 30], [96, 72, 46]));
T('stripped_birch_log_top', logTop([200, 184, 128], [196, 176, 118]));
T('oak_leaves', leaves([60, 110, 36]));
T('spruce_leaves', leaves([46, 80, 50], 0.12));
T('birch_leaves', leaves([98, 136, 62]));
T('dark_oak_leaves', leaves([44, 86, 26], 0.12));
T('azalea_leaves', leaves([92, 130, 44], 0.1));
T('flowering_azalea_leaves', leaves([92, 130, 44], 0.1, [210, 110, 200]));
T('bookshelf', (put, R) => each((x, y) => {
  if (y <= 1 || y >= 14 || y === 7 || y === 8) { put(x, y, [162, 130, 78], 0.9 + R() * 0.1); return; }
  const book = Math.floor(x / 2) + (y > 8 ? 3 : 0);
  const cs = [[140, 40, 40], [40, 70, 130], [60, 110, 50], [150, 120, 50], [90, 50, 110], [120, 80, 40]];
  put(x, y, cs[book % cs.length], x % 2 ? 0.75 : 1);
}));
T('crafting_top', planks([150, 112, 64]));
T('crafting_side', planks([140, 102, 60]));
T('hay_side', (put, R) => each((x, y) => (y === 3 || y === 4 || y === 11 || y === 12) ? put(x, y, [150, 60, 36], 0.9 + R() * 0.15) : put(x, y, [206, 172, 58], (0.85 + R() * 0.2) * (x % 3 === 0 ? 0.88 : 1))));
T('hay_top', noise([212, 180, 64], 0.12));
T('pumpkin_side', (put, R) => each((x, y) => put(x, y, [214, 124, 28], (0.9 + R() * 0.1) * (x % 4 === 0 ? 0.8 : 1))));
T('pumpkin_top', noise([200, 118, 30], 0.08));
// ── 양털 · 유리 · 금속
for (const [n, c] of [['white', [234, 236, 236]], ['red', [160, 39, 34]], ['blue', [53, 57, 157]], ['yellow', [248, 198, 39]], ['green', [84, 109, 27]],
  ['purple', [121, 42, 172]], ['black', [21, 21, 26]], ['brown', [114, 71, 40]]]) T(`${n}_wool`, wool(c));
T('glass', glassTile([200, 225, 235]));
for (const [n, c] of [['red', [170, 50, 50]], ['blue', [60, 80, 180]], ['yellow', [230, 200, 60]], ['purple', [130, 60, 180]], ['cyan', [60, 140, 160]],
  ['lime', [120, 190, 40]], ['orange', [220, 120, 40]], ['magenta', [190, 70, 170]], ['light_blue', [100, 160, 220]]]) T(`${n}_glass`, stained(c));
T('iron_bars', cross((put) => each((x, y) => { if (x % 5 === 2 || y === 0 || y === 15) put(x, y, [100, 100, 104], x % 5 === 2 ? 1 : 0.8); })));
T('chain', cross((put) => each((x, y) => { if (x >= 6 && x <= 9 && (y % 6 < 4 ? (x === 6 || x === 9) : (y % 6 === 4 || y % 6 === 5))) put(x, y, [60, 64, 76]); })));
T('lantern', (put, R) => each((x, y) => {
  const frame = x <= 1 || x >= 14 || y <= 2 || y >= 13;
  put(x, y, frame ? [50, 50, 58] : [255, 200, 110], frame ? 1 : 0.9 + R() * 0.15);
}));
T('glowstone', noise([250, 200, 110], 0.12, (x, y, k, R, i) => (blob(x, y, 8, i, 2) > 0.8 ? 1.2 : k)));
T('sea_lantern', noise([200, 230, 220], 0.06, (x, y, k) => k * bevel(x, y)));
T('shroomlight', noise([240, 150, 70], 0.12));
T('cobweb', cross((put) => each((x, y) => { if (x === y || x === 15 - y || x === 8 || y === 8 || (Math.abs(Math.hypot(x - 7.5, y - 7.5) - 5) < 0.6)) put(x, y, [230, 230, 235], 1, 200); })));
T('flower_pot', noise([120, 64, 44], 0.08));
// ── 문 · 덧창
for (const [w, c] of [['oak', [150, 118, 70]], ['spruce', [100, 74, 44]], ['dark_oak', [72, 48, 24]], ['birch', [206, 190, 140]]]) {
  T(`${w}_door_top`, doorTile(c, w !== 'dark_oak'));
  T(`${w}_door_bottom`, doorTile(c, false));
  T(`${w}_trapdoor`, trapTile(c));
}
// ── 식물
T('short_grass', blades(FOL));
T('tall_grass', blades(FOL, 16));
T('fern', blades([66, 118, 50], 12));
T('sugar_cane', cross((put) => each((x, y) => { if (x === 4 || x === 11) put(x, y, [140, 190, 90], y % 4 === 0 ? 0.8 : 1); })));
T('poppy', flower([200, 30, 30], [40, 30, 20]));
T('dandelion', flower([250, 220, 40], [240, 170, 20]));
T('cornflower', flower([80, 110, 220], [60, 80, 170]));
T('oxeye_daisy', flower([240, 240, 240], [240, 200, 40]));
T('allium', flower([180, 110, 220], [150, 80, 190]));
T('azure_bluet', flower([230, 235, 240], [240, 220, 120]));
T('red_tulip', flower([220, 50, 40], [220, 50, 40]));
T('orange_tulip', flower([240, 130, 40], [240, 130, 40]));
T('white_tulip', flower([240, 240, 235], [240, 240, 235]));
T('blue_orchid', flower([60, 170, 230], [40, 140, 210]));
T('lily_of_the_valley', flower([245, 245, 245], [245, 245, 245]));
T('rose_bush', flower([200, 30, 40], [150, 20, 30], [50, 100, 40]));
T('lilac', flower([200, 150, 210], [180, 120, 200], [50, 100, 40]));
T('sweet_berry_bush', blades([50, 90, 50], 10));
T('lily_pad', cross((put) => each((x, y) => { const d = Math.hypot(x - 7.5, y - 7.5); if (d < 7.5 && !(x > 7 && Math.abs(y - 7.5) < 1)) put(x, y, [40, 110, 40], 0.9 + (d / 30)); })));
T('wheat', crop([150, 150, 50], [200, 170, 70]));
T('carrots', crop([60, 130, 40], [230, 130, 30]));
T('potatoes', crop([60, 130, 40], [80, 150, 50]));

export const ROWS = Math.ceil(tiles.length / COLS);
export function buildAtlasRGBA() {
  const W = COLS * TS, Hh = ROWS * TS, buf = Buffer.alloc(W * Hh * 4);
  const cl = v => Math.max(0, Math.min(255, Math.round(v)));
  tiles.forEach((t, i) => {
    const ox = (i % COLS) * TS, oy = Math.floor(i / COLS) * TS;
    const R = mulberry(i * 7919 + 13);
    const put = (x, y, c, k = 1, a = 255) => { const p = ((oy + y) * W + ox + x) * 4; buf[p] = cl(c[0] * k); buf[p + 1] = cl(c[1] * k); buf[p + 2] = cl(c[2] * k); buf[p + 3] = cl(a); };
    for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) put(x, y, [255, 0, 255]);
    t.fn(put, R, i);
  });
  return { W, H: Hh, buf };
}
export function tileNames() { return tiles.map(t => t.name); }
