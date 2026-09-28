// =====================================================================
//  집 생성기 — 한 채씩 전부 다르게
//   양식: tudor(목조 골조) · burgher(밝은 목조) · stone(석조) · brick(벽돌)
//         cottage(시골) · mountain(산악) · fisher(어촌)
//   요소: 돌 기단, 돌출 2층(제티)+까치발, 창문+덧창+창턱+화단, 문+차양+랜턴,
//         박공 지붕(측면/정면), 도머, 굴뚝, 돌출 창(오리엘), 박공 창, 도르래 들보, 실내 바닥·조명
// =====================================================================
import { S, AIR, mix, one, Frame, mulberry, matBlock, coneRoof } from './lib.js';
import { H, col, height, reserve, set } from '../world.js';

export const chimneys = [];

const STYLES = {
  tudor: r => ({
    base: mix([['cobblestone', 4], ['stone_bricks', 2], ['mossy_cobblestone', 1], ['andesite', 1]], 11),
    ground: r() < 0.6 ? 'stone' : 'timber',
    frame: r() < 0.7 ? 'dark_oak_log' : 'stripped_dark_oak_log',
    infill: mix(r() < 0.25 ? [['white_terracotta', 3], ['calcite', 2]] : [['calcite', 8], ['white_terracotta', 1]], 12),
    roof: pick(r, ['dark_oak', 'dark_oak', 'deepslate_tile', 'spruce', 'brick', 'cobbled_deepslate', 'granite']),
    wood: pick(r, ['spruce', 'dark_oak']), floor: 'spruce_planks', jetty: r() < 0.75, P: 4, braces: r() < 0.5,
  }),
  burgher: r => ({
    base: mix([['stone_bricks', 3], ['cobblestone', 2], ['mossy_stone_bricks', 1]], 13),
    ground: r() < 0.5 ? 'stone' : 'timber',
    frame: pick(r, ['spruce_log', 'stripped_spruce_log', 'oak_log']),
    infill: mix(pick(r, [[['mud_bricks', 1]], [['smooth_sandstone', 1]], [['white_terracotta', 3], ['mud_bricks', 1]], [['birch_planks', 1]]]), 14),
    roof: pick(r, ['brick', 'spruce', 'deepslate_tile', 'dark_oak', 'granite', 'mud_brick']),
    wood: pick(r, ['spruce', 'oak']), floor: 'oak_planks', jetty: r() < 0.55, P: pick(r, [3, 4]), braces: r() < 0.3,
  }),
  stone: r => ({
    base: mix([['stone_bricks', 5], ['cobblestone', 1]], 15),
    ground: 'stone',
    wall: mix([['stone_bricks', 6], ['mossy_stone_bricks', 1.5], ['cracked_stone_bricks', 1.5], ['andesite', 1]], 16),
    quoin: pick(r, ['polished_andesite', 'chiseled_stone_bricks', 'stone_bricks']),
    trim: pick(r, ['polished_andesite', 'smooth_stone']),
    roof: pick(r, ['deepslate_tile', 'deepslate_tile', 'dark_oak', 'polished_deepslate', 'cobbled_deepslate']),
    wood: 'dark_oak', floor: 'dark_oak_planks', jetty: false, P: 4, masonry: true,
  }),
  brick: r => ({
    base: mix([['stone_bricks', 3], ['polished_andesite', 1]], 17),
    ground: 'stone',
    wall: mix([['bricks', 1]], 18), quoin: 'stone_bricks', trim: pick(r, ['stone_bricks', 'polished_andesite']),
    roof: pick(r, ['deepslate_tile', 'dark_oak', 'spruce']),
    wood: pick(r, ['spruce', 'dark_oak']), floor: 'spruce_planks', jetty: false, P: 4, masonry: true,
  }),
  cottage: r => ({
    base: mix([['cobblestone', 3], ['mossy_cobblestone', 2]], 19),
    ground: 'timber',
    frame: pick(r, ['stripped_oak_log', 'oak_log', 'stripped_spruce_log']),
    infill: mix(pick(r, [[['oak_planks', 1]], [['white_terracotta', 1]], [['spruce_planks', 1]], [['mud_bricks', 1]]]), 20),
    roof: pick(r, ['spruce', 'oak', 'dark_oak', 'mud_brick', 'spruce']),
    wood: pick(r, ['oak', 'spruce']), floor: 'oak_planks', jetty: false, P: 4, braces: false,
  }),
  mountain: r => ({
    base: mix([['cobblestone', 3], ['stone', 1], ['mossy_cobblestone', 1]], 21),
    ground: 'stone',
    frame: 'spruce_log', infill: mix([['spruce_planks', 3], ['stripped_spruce_log', 1]], 22),
    roof: pick(r, ['spruce', 'deepslate_tile', 'cobbled_deepslate']),
    wood: 'spruce', floor: 'spruce_planks', jetty: false, P: 4, braces: false,
  }),
  fisher: r => ({
    base: mix([['spruce_planks', 1]], 23),
    ground: 'timber',
    frame: 'stripped_spruce_log', infill: mix(pick(r, [[['oak_planks', 1]], [['spruce_planks', 1]], [['birch_planks', 1]]]), 24),
    roof: pick(r, ['spruce', 'oak', 'dark_oak']),
    wood: 'spruce', floor: 'spruce_planks', jetty: false, P: 4, braces: false,
  }),
};
function pick(r, a) { return a[Math.floor(r() * a.length)]; }

// ox,oz: 정면 오른쪽 모서리의 월드 좌표.  front: 정면이 향하는 방위.
export function house(ox, oy, oz, front, w, d, o = {}) {
  const r = mulberry(o.seed ?? (ox * 73856093 ^ oz * 19349663));
  const st = STYLES[o.style || 'tudor'](r);
  const F = new Frame(ox, oy, oz, front);
  const floors = o.floors ?? 2;
  const FH = 4;
  const wallTop = floors * FH;
  const jetty = o.jetty ?? st.jetty;
  const P = st.P;
  const wood = st.wood;
  const planks = S(`${wood}_planks`);
  const floorB = S(st.floor);
  const frameLog = st.frame;

  // 층별 외곽 (제티는 정면으로 1칸)
  const vf = k => (jetty && k >= 1 ? -1 : 0);
  const vb = () => d - 1;

  // ── 기초 · 땅 고르기
  const [ax, az] = F.w(0, 0), [bx, bz] = F.w(w - 1, d - 1);
  const x0 = Math.min(ax, bx) - 1, x1 = Math.max(ax, bx) + 1, z0 = Math.min(az, bz) - 1, z1 = Math.max(az, bz) + 1;
  for (let u = -1; u <= w; u++) for (let v = -1; v <= d; v++) {
    const [x, z] = F.w(u, v);
    const h = H(x, z);
    const inner = u >= 0 && u < w && v >= 0 && v < d;
    if (inner) for (let y = Math.min(h - oy, 0) - 1; y <= 0; y++) F.set(u, v, y, y === 0 ? floorB : st.base);
    for (let y = 1; y <= Math.max(0, h - oy) + 2; y++) if (inner || y > 0) { if (inner || h > oy) F.set(u, v, y, AIR); }
  }

  const isPost = (i, len) => i === 0 || i === len - 1 || (i % P === 0 && i < len - 2 && i > 1);
  const setWall = (u, v, y, id) => F.set(u, v, y, id);

  // ── 벽
  for (let k = 0; k < floors; k++) {
    const yB = k * FH; // 이 층의 들보 줄
    const fv = vf(k), bv = vb(k);
    const len = bv - fv + 1;
    // 실내 비우기 + 바닥
    for (let u = 1; u < w - 1; u++) for (let v = fv + 1; v < bv; v++) {
      if (k > 0) F.set(u, v, yB, floorB);
      for (let y = yB + 1; y < yB + FH; y++) F.set(u, v, y, AIR);
    }
    const stoneFloor = st.masonry || (k === 0 && st.ground === 'stone');
    const walls = [
      { cells: [...Array(w).keys()].map(u => [u, fv]), out: 'front', i: c => c[0], n: w, axis: 'u' },
      { cells: [...Array(w).keys()].map(u => [u, bv]), out: 'back', i: c => c[0], n: w, axis: 'u' },
      { cells: [...Array(len).keys()].map(i => [0, fv + i]), out: 'left', i: c => c[1] - fv, n: len, axis: 'v' },
      { cells: [...Array(len).keys()].map(i => [w - 1, fv + i]), out: 'right', i: c => c[1] - fv, n: len, axis: 'v' },
    ];
    for (const W of walls) {
      const od = { front: [0, -1], back: [0, 1], left: [-1, 0], right: [1, 0] }[W.out];
      for (const c of W.cells) {
        const [u, v] = c, i = W.i(c);
        const corner = i === 0 || i === W.n - 1;
        const post = isPost(i, W.n);
        for (let y = yB; y < yB + FH; y++) {
          const ly = y - yB;
          let id;
          if (stoneFloor) {
            const wallMix = st.wall || st.base;
            id = corner ? one(st.quoin || 'stone_bricks') : (ly === 0 && k > 0 ? S(st.trim || 'stone_bricks') : wallMix);
          } else {
            if (corner || post) id = S(frameLog, { axis: 'y' });
            else if (ly === 0) id = S(frameLog, { axis: F.axis(W.axis) });
            else id = st.infill;
            if (!corner && !post && st.braces && ly >= 1 && (i % P === 1 || i % P === P - 1) && W.n > 5 && W.out !== 'front') {
              // 사선 버팀대 느낌: 모서리 칸에 벗긴 통나무
              if ((ly === 1 && i % P === 1) || (ly === 3 && i % P === P - 1)) id = S(frameLog.startsWith('stripped') ? frameLog : 'stripped_' + frameLog, { axis: 'y' });
            }
          }
          if (k === 0 && ly === 0) id = st.base;
          setWall(u, v, y, id);
        }
        // 창문: 기둥 사이 칸의 가운데
        if (!corner && !post) {
          const pi = i % P, panelMid = P === 4 ? 2 : 1;
          const isWin = P === 4 ? pi === panelMid : true;
          const doorHere = k === 0 && W.out === 'front' && u === o.doorU;
          if (isWin && !doorHere && W.n > 3) {
            const tall = k === 0 ? (st.masonry ? 2 : 1 + (r() < 0.5 ? 1 : 0)) : 2;
            const wy0 = yB + (tall === 2 ? 1 : 2);
            for (let y = wy0; y < wy0 + tall; y++) setWall(u, v, y, S('glass_pane'));
            if (st.masonry) {
              // 아치 머리돌
              setWall(u, v, wy0 + tall, S(`${st.trim === 'smooth_stone' ? 'stone_brick' : 'stone_brick'}_stairs`, { facing: F.dir(W.out === 'front' ? 'back' : W.out === 'back' ? 'front' : W.out === 'left' ? 'right' : 'left'), half: 'top' }));
            }
            // 창턱
            const [su, sv] = [u + od[0], v + od[1]];
            if (F.get(su, sv, wy0 - 1) === AIR || F.get(su, sv, wy0 - 1) <= 1) {
              if (W.out === 'front' && r() < 0.55) F.set(su, sv, wy0 - 1, S(pick(r, ['flowering_azalea_leaves', 'azalea_leaves', 'flowering_azalea_leaves']), { persistent: 'true' }));
              else F.stairs(su, sv, wy0 - 1, st.masonry ? 'stone_brick' : wood, W.out === 'front' ? 'back' : W.out === 'back' ? 'front' : W.out === 'left' ? 'right' : 'left', 'top');
            }
            // 덧창 (나무 양식, P=4)
            if (!st.masonry && P === 4 && (W.out === 'front' || r() < 0.4)) {
              for (const side of [-1, 1]) {
                const shu = W.axis === 'u' ? u + side : u + od[0], shv = W.axis === 'u' ? v + od[1] : v + side;
                const [wu, wv] = W.axis === 'u' ? [shu, shv] : [shu, shv];
                const inWall = W.axis === 'u' ? [u + side, v] : [u, v + side];
                // 덧창은 벽 바깥 칸, 창 옆
                const pu = inWall[0] + od[0], pv = inWall[1] + od[1];
                for (let y = wy0; y < wy0 + tall; y++) if (F.get(pu, pv, y) <= 1) F.trapdoor(pu, pv, y, st.wood === 'oak' ? 'spruce' : 'dark_oak', W.out, true);
              }
            }
          }
        }
      }
    }
    // 제티 까치발 + 들보
    if (jetty && k === 1) {
      for (let u = 0; u < w; u++) {
        if (isPost(u, w)) F.stairs(u, -1, FH - 1, wood, 'back', 'top');
      }
    }
  }

  // ── 문
  const doorU = o.doorU ?? Math.max(1, Math.min(w - 2, Math.floor(w / 2) + (r() < 0.5 ? 0 : -1)));
  F.set(doorU, 0, 1, AIR); F.set(doorU, 0, 2, AIR);
  F.door(doorU, 0, 1, st.wood === 'oak' ? 'oak' : st.wood, 'back', r() < 0.5 ? 'left' : 'right');
  F.set(doorU, 0, 3, st.masonry ? S('chiseled_stone_bricks') : S(frameLog, { axis: F.axis('u') }));
  // 차양 + 랜턴
  if (!(jetty)) {
    for (let u = doorU - 1; u <= doorU + 1; u++) F.stairs(u, -1, 3, st.roof === 'brick' ? 'spruce' : (st.roof.includes('deepslate') ? 'dark_oak' : st.roof), 'back');
  }
  const lu = doorU + (doorU + 1 < w - 1 ? 1 : -1);
  if (F.get(lu, -1, 3) <= 1) { F.set(lu, -1, 3, S(`${wood === 'oak' ? 'oak' : 'spruce'}_fence`)); }
  F.lantern(lu, -1, 2, true);
  // 문 앞 계단 (기초가 높을 때)
  const [fx, fz] = F.w(doorU, -1);
  if (H(fx, fz) < oy) F.stairs(doorU, -1, 0, 'stone_brick', 'back');
  // 상점 앞면
  if (o.shop) {
    const colors = pick(r, [['red_wool', 'white_wool'], ['blue_wool', 'white_wool'], ['green_wool', 'white_wool'], ['yellow_wool', 'red_wool']]);
    for (let u = 1; u < w - 1; u++) {
      if (u === doorU) continue;
      for (let y = 1; y <= 2; y++) F.set(u, 0, y, S('glass_pane'));
      if (!jetty) F.set(u, -1, 3, S(colors[u % 2]));
    }
  }

  // ── 오리엘(돌출 창): 3층 이상, 제티 없는 정면 가운데 2층
  if (floors >= 3 && !jetty && w >= 7 && r() < 0.6) {
    const c = Math.floor(w / 2), k = 1, yB = k * FH;
    for (let u = c - 1; u <= c + 1; u++) {
      F.stairs(u, -1, yB, st.masonry ? 'stone_brick' : wood, 'back', 'top');
      for (let y = yB + 1; y <= yB + 3; y++) F.set(u, -1, y, u === c ? S('glass_pane') : (st.masonry ? S(st.quoin || 'stone_bricks') : S(frameLog, { axis: 'y' })));
      F.set(u, 0, yB + 2, S('glass_pane'));
      F.slab(u, -1, yB + FH, st.masonry ? 'stone_brick' : wood, 'bottom');
    }
  }

  // ── 지붕
  const frontGable = o.frontGable ?? (w <= 9 && r() < 0.55);
  const roof = st.roof;
  const vMin = vf(floors - 1), vMax = vb(floors - 1);
  const yR = wallTop + 1;
  const ov = 1;
  const gableFill = (u, v, y, center) => {
    if (st.masonry) F.set(u, v, y, st.wall || st.base);
    else F.set(u, v, y, center ? S(frameLog, { axis: 'y' }) : st.infill);
  };
  let ridgeY = yR;
  // 가파른 지붕(2:1): 한 칸 들어갈 때 두 칸 올라간다 — 북유럽 구시가 느낌
  const steep = o.steep ?? (r() < (st.masonry ? 0.35 : 0.45));
  // 지붕 한 줄: slope 방향 두 줄(a,b)과 층(l). 교차 축은 cross(i) 로 좌표를 만든다
  const roofRows = (lo, hi, alongFrom, alongTo, put, gable, clearIn) => {
    for (let l = 0; ; l++) {
      const a = lo + l, b = hi - l;
      if (a > b) break;
      const y0 = steep ? yR + 2 * l : yR + l;
      ridgeY = steep ? y0 + 1 : y0;
      for (let t = alongFrom; t <= alongTo; t++) {
        if (a === b) { put(t, a, y0, 'full'); if (steep) put(t, a, y0 + 1, 'full'); put(t, a, ridgeY + 1, 'slab'); }
        else {
          if (steep) { put(t, a, y0, 'full'); put(t, b, y0, 'full'); put(t, a, y0 + 1, 'up'); put(t, b, y0 + 1, 'down'); }
          else { put(t, a, y0, 'up'); put(t, b, y0, 'down'); }
          if (l === 0) { put(t, a, y0 - 1, 'eaveA'); put(t, b, y0 - 1, 'eaveB'); }
        }
      }
      for (let yy = y0; yy <= (steep ? y0 + 1 : y0); yy++) { gable(a, b, yy); clearIn(a, b, yy); }
    }
  };
  if (!frontGable) {
    roofRows(vMin - ov, vMax + ov, -ov, w - 1 + ov,
      (u, v, y, k) => {
        if (k === 'full') F.set(u, v, y, S(matBlock(roof)));
        else if (k === 'slab') F.slab(u, v, y, roof, 'bottom');
        else if (k === 'up') F.stairs(u, v, y, roof, 'back');
        else if (k === 'down') F.stairs(u, v, y, roof, 'front');
        else if (k === 'eaveA') F.stairs(u, v, y, roof, 'front', 'top');
        else if (k === 'eaveB') F.stairs(u, v, y, roof, 'back', 'top');
      },
      (a, b, y) => { for (const gu of [0, w - 1]) for (let v = a + 1; v < b; v++) gableFill(gu, v, y, v === Math.floor((vMin + vMax) / 2)); },
      (a, b, y) => { for (let u = 1; u < w - 1; u++) for (let v = a + 1; v < b; v++) F.set(u, v, y, AIR); });
    // 박공 창
    const midV = Math.floor((vMin + vMax) / 2);
    if (vMax - vMin >= 5) for (const gu of [0, w - 1]) F.set(gu, midV + (gu ? 1 : -1) * 0, yR + 1, S('glass_pane'));
    // 도머
    if (!steep && w >= 9 && r() < 0.75) {
      const cnt = w >= 13 ? 2 : 1;
      for (let q = 0; q < cnt; q++) {
        const du = cnt === 1 ? Math.floor(w / 2) - 1 : (q === 0 ? 2 : w - 5);
        const vv = vMin;
        for (let u = du - 1; u <= du + 3; u++) for (let v = vv - 1; v <= vv + 2; v++) for (let y = yR; y <= yR + 2; y++) F.set(u, v, y, AIR);
        for (let v = vv; v <= vv + 2; v++) for (let y = yR; y <= yR + 1; y++) { F.set(du, v, y, st.masonry ? st.wall : S(frameLog, { axis: 'y' })); F.set(du + 2, v, y, st.masonry ? st.wall : st.infill); }
        for (let y = yR; y <= yR + 1; y++) { F.set(du + 1, vv, y, S('glass_pane')); F.set(du, vv, y, st.masonry ? S(st.quoin) : S(frameLog, { axis: 'y' })); F.set(du + 2, vv, y, st.masonry ? S(st.quoin) : S(frameLog, { axis: 'y' })); }
        for (let v = vv - 1; v <= vv + 2; v++) {
          F.stairs(du - 1, v, yR + 2, roof, 'right'); F.stairs(du + 3, v, yR + 2, roof, 'left');
          F.stairs(du, v, yR + 3, roof, 'right'); F.stairs(du + 2, v, yR + 3, roof, 'left');
          F.set(du + 1, v, yR + 4, S(matBlock(roof)));
          F.set(du + 1, v, yR + 2, AIR); F.set(du + 1, v, yR + 3, S(matBlock(roof)));
        }
        F.set(du + 1, vv, yR + 2, st.masonry ? st.wall : st.infill);
        // 도머 뒤로 원래 지붕 다시 잇기
        for (let u = du - 1; u <= du + 3; u++) { F.stairs(u, vv - 1, yR, roof, 'back'); F.stairs(u, vv - 1, yR - 1, roof, 'front', 'top'); }
      }
    }
  } else {
    roofRows(-ov, w - 1 + ov, vMin - ov, vMax + ov,
      (v, u, y, k) => {
        if (k === 'full') F.set(u, v, y, S(matBlock(roof)));
        else if (k === 'slab') F.slab(u, v, y, roof, 'bottom');
        else if (k === 'up') F.stairs(u, v, y, roof, 'right');
        else if (k === 'down') F.stairs(u, v, y, roof, 'left');
        else if (k === 'eaveA') F.stairs(u, v, y, roof, 'left', 'top');
        else if (k === 'eaveB') F.stairs(u, v, y, roof, 'right', 'top');
      },
      (a, b, y) => { for (const gv of [vMin, vMax]) for (let u = a + 1; u < b; u++) gableFill(u, gv, y, u === Math.floor(w / 2) && !st.masonry); },
      (a, b, y) => { for (let u = a + 1; u < b; u++) for (let v = vMin + 1; v < vMax; v++) F.set(u, v, y, AIR); });
    // 정면 박공: 창 2개 + 도르래 들보
    const c = Math.floor(w / 2);
    const gy = yR + 1;
    if (w >= 7) { F.set(c - 1, vMin, gy, S('glass_pane')); F.set(c + 1 - (w % 2 ? 0 : 1) + (w % 2 ? 0 : 1), vMin, gy, S('glass_pane')); }
    F.set(c, vMin, gy + 1 + (w >= 9 ? 1 : 0), S('glass_pane'));
    if (r() < 0.45 && w >= 7) {
      const hy = Math.min(ridgeY - 1, gy + 3);
      F.log(c, vMin - 1, hy, st.masonry ? 'dark_oak_log' : frameLog.replace('stripped_', ''), 'v');
      F.log(c, vMin - 2, hy, st.masonry ? 'dark_oak_log' : frameLog.replace('stripped_', ''), 'v');
      F.set(c, vMin - 2, hy - 1, S('chain', { axis: 'y' }));
    }
  }

  // ── 모서리 원뿔탑 (큰 석조·목조 집)
  if ((o.turret ?? (floors >= 3 && w >= 9 && r() < 0.4)) && !jetty) {
    const tu = r() < 0.5 ? 0 : w - 1, tv = 0;
    const [tx, , tz] = F.wx(tu, tv, 0);
    const tb = FH + 1, tt = wallTop + 3;
    const tm = st.masonry ? (st.wall || st.base) : st.infill;
    for (let dx = -2; dx <= 2; dx++) for (let dz = -2; dz <= 2; dz++) {
      const d = Math.hypot(dx, dz);
      if (d > 2.4) continue;
      for (let y = oy + tb; y <= oy + tt; y++) {
        const edge = d > 1.4;
        const win = edge && (y - oy - tb) % 4 === 2 && (dx === 0 || dz === 0);
        set(tx + dx, y, tz + dz, win ? S('glass_pane') : edge ? (typeof tm === 'function' ? tm(tx + dx, y, tz + dz) : tm) : AIR);
      }
      if (d > 1.4) set(tx + dx, oy + tb - 1, tz + dz, S(`${st.masonry ? 'stone_brick' : wood}_stairs`, { facing: Math.abs(dx) >= Math.abs(dz) ? (dx > 0 ? 'west' : 'east') : (dz > 0 ? 'north' : 'south'), half: 'top' }));
    }
    const rm = roof === 'brick' || roof === 'mud_brick' ? 'deepslate_tile' : roof;
    coneRoof(tx, oy + tt + 1, tz, 3.1, rm, 2.6, 'dark_oak_fence');
  }
  // ── 발코니 (2층 정면)
  if (!jetty && !st.masonry && floors >= 2 && w >= 7 && (o.balcony ?? r() < 0.3)) {
    const c = Math.floor(w / 2);
    for (let u = c - 2; u <= c + 2; u++) {
      F.slab(u, -1, FH, wood, 'top');
      F.set(u, -1, FH + 1, S(`${wood === 'oak' ? 'oak' : wood}_fence`));
    }
    F.set(c, 0, FH + 1, AIR); F.set(c, 0, FH + 2, AIR);
    F.door(c, 0, FH + 1, wood === 'oak' ? 'oak' : wood, 'back');
    F.stairs(c - 2, -1, FH - 1, wood, 'back', 'top'); F.stairs(c + 2, -1, FH - 1, wood, 'back', 'top');
  }

  // ── 굴뚝
  if (o.chimney ?? r() < 0.7) {
    const cu = frontGable ? (r() < 0.5 ? 1 : w - 2) : (r() < 0.5 ? 0 : w - 1);
    const cv = frontGable ? Math.floor((vMin + vMax) / 2) + 1 : Math.max(1, Math.floor(d / 2) + 1);
    const cm = st.masonry ? S('stone_bricks') : S(pick(r, ['bricks', 'stone_bricks', 'cobblestone']));
    const top = ridgeY + 2;
    for (let y = 1; y <= top; y++) F.set(cu, cv, y, cm);
    F.set(cu, cv, top + 1, S(st.masonry ? 'stone_brick_wall' : 'cobblestone_wall'));
    const [cx, cy, cz] = F.wx(cu, cv, top + 1);
    chimneys.push([cx, cy + 1, cz]);
  }

  // ── 실내 조명 · 가구
  for (let k = 0; k < floors; k++) {
    F.lantern(Math.floor(w / 2), Math.floor(d / 2), k * FH + FH - 1, true);
    if (k === 0 && d > 4) {
      for (let u = 1; u < w - 1; u++) if (r() < 0.45) F.set(u, d - 2, 1, S(pick(r, ['bookshelf', 'crafting_table', 'bookshelf'])));
    }
  }
  reserve(x0, z0, x1, z1, 2);
  return { x0, z0, x1, z1, top: oy + ridgeY };
}
