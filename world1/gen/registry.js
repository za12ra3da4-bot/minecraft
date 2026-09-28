// =====================================================================
//  블록 레지스트리 — 블록 상태 ↔ 숫자 id, 렌더용 모델/텍스처 정보
//  id 0 = 미지정(지형이 채움), id 1 = 공기
// =====================================================================

export const DEFS = {};
// model: cube | column | slab | stairs | fence | pane | wall | cross | crop | lantern | trapdoor | door | flat | pot | chain | water | carpet
// cat:   opaque | cutout | trans | emit
function def(name, model, tex, cat = 'opaque', extra = {}) {
  if (typeof tex === 'string') tex = { top: tex, side: tex, bottom: tex };
  DEFS[name] = { name, model, tex, cat, full: (model === 'cube' || model === 'column') && cat !== 'trans', ...extra };
}

// ── 자연
def('air', 'none', 'none', 'none');
for (const n of ['stone', 'andesite', 'polished_andesite', 'granite', 'diorite', 'cobblestone', 'mossy_cobblestone', 'gravel', 'dirt', 'coarse_dirt',
  'sand', 'snow_block', 'bedrock', 'deepslate', 'stone_bricks', 'mossy_stone_bricks', 'cracked_stone_bricks', 'chiseled_stone_bricks',
  'bricks', 'deepslate_tiles', 'deepslate_bricks', 'polished_deepslate', 'cobbled_deepslate', 'oak_planks', 'spruce_planks', 'dark_oak_planks', 'birch_planks',
  'white_terracotta', 'terracotta', 'calcite', 'mud_bricks', 'packed_mud', 'gold_block', 'white_wool', 'red_wool', 'blue_wool', 'yellow_wool', 'green_wool',
  'purple_wool', 'black_wool', 'clay', 'tuff', 'moss_block', 'smooth_sandstone', 'amethyst_block', 'copper_block', 'blackstone', 'polished_blackstone_bricks'])
  def(n, 'cube', n);
def('smooth_stone', 'cube', 'smooth_stone');
def('grass_block', 'cube', { top: 'grass_top', side: 'grass_side', bottom: 'dirt' }, 'opaque', { tint: 'grass' });
def('podzol', 'cube', { top: 'podzol_top', side: 'podzol_side', bottom: 'dirt' });
def('sandstone', 'cube', { top: 'sandstone_top', side: 'sandstone', bottom: 'sandstone_top' });
def('farmland', 'cube', { top: 'farmland', side: 'dirt', bottom: 'dirt' });
def('dirt_path', 'cube', { top: 'path_top', side: 'path_side', bottom: 'dirt' }, 'opaque', { h: 15 });
def('hay_block', 'column', { top: 'hay_top', side: 'hay_side', bottom: 'hay_top' });
def('pumpkin', 'cube', { top: 'pumpkin_top', side: 'pumpkin_side', bottom: 'pumpkin_top' });
def('bookshelf', 'cube', { top: 'oak_planks', side: 'bookshelf', bottom: 'oak_planks' });
def('crafting_table', 'cube', { top: 'crafting_top', side: 'crafting_side', bottom: 'oak_planks' });
def('glowstone', 'cube', 'glowstone', 'emit');
def('sea_lantern', 'cube', 'sea_lantern', 'emit');
def('shroomlight', 'cube', 'shroomlight', 'emit');
def('water', 'water', 'water', 'trans');
def('glass', 'cube', 'glass', 'cutout');
def('ice', 'cube', 'ice', 'trans');
for (const w of ['oak', 'spruce', 'birch', 'dark_oak']) {
  def(`${w}_log`, 'column', { top: `${w}_log_top`, side: `${w}_log`, bottom: `${w}_log_top` });
  def(`stripped_${w}_log`, 'column', { top: `stripped_${w}_log_top`, side: `stripped_${w}_log`, bottom: `stripped_${w}_log_top` });
  def(`${w}_leaves`, 'cube', `${w}_leaves`, 'cutout', { leaves: true, full: false });
}
def('azalea_leaves', 'cube', 'azalea_leaves', 'cutout', { leaves: true, full: false });
def('flowering_azalea_leaves', 'cube', 'flowering_azalea_leaves', 'cutout', { leaves: true, full: false });

// ── 계단 · 반블록 (재질 → 텍스처)
const SHAPED = {
  stone_brick: 'stone_bricks', mossy_stone_brick: 'mossy_stone_bricks', cobblestone: 'cobblestone', mossy_cobblestone: 'mossy_cobblestone',
  polished_andesite: 'polished_andesite', andesite: 'andesite', brick: 'bricks', deepslate_tile: 'deepslate_tiles', deepslate_brick: 'deepslate_bricks',
  polished_deepslate: 'polished_deepslate', oak: 'oak_planks', spruce: 'spruce_planks', dark_oak: 'dark_oak_planks', birch: 'birch_planks',
  sandstone: 'sandstone', smooth_stone: 'smooth_stone', mud_brick: 'mud_bricks', cobbled_deepslate: 'cobbled_deepslate', granite: 'granite',
  polished_blackstone_brick: 'polished_blackstone_bricks',
};
for (const [m, t] of Object.entries(SHAPED)) {
  if (m !== 'smooth_stone') def(`${m}_stairs`, 'stairs', t);
  def(`${m}_slab`, 'slab', t);
}
// 울타리 · 담장 · 판유리
for (const w of ['oak', 'spruce', 'dark_oak', 'birch']) def(`${w}_fence`, 'fence', `${w}_planks`, 'opaque', { conn: 'fence' });
for (const [n, t] of [['cobblestone_wall', 'cobblestone'], ['mossy_cobblestone_wall', 'mossy_cobblestone'], ['stone_brick_wall', 'stone_bricks'],
  ['mossy_stone_brick_wall', 'mossy_stone_bricks'], ['deepslate_tile_wall', 'deepslate_tiles'], ['mud_brick_wall', 'mud_bricks'], ['andesite_wall', 'andesite'],
  ['cobbled_deepslate_wall', 'cobbled_deepslate'], ['polished_blackstone_brick_wall', 'polished_blackstone_bricks']])
  def(n, 'wall', t, 'opaque', { conn: 'wall' });
def('glass_pane', 'pane', 'glass', 'cutout', { conn: 'pane' });
def('iron_bars', 'pane', 'iron_bars', 'cutout', { conn: 'pane' });
for (const c of ['red', 'blue', 'yellow', 'purple', 'cyan', 'lime', 'orange', 'magenta', 'light_blue'])
  def(`${c}_stained_glass_pane`, 'pane', `${c}_glass`, 'trans', { conn: 'pane' });
for (const c of ['purple', 'light_blue', 'red', 'blue', 'yellow'])
  def(`${c}_stained_glass`, 'cube', `${c}_glass`, 'trans');
// 문 · 덧창
for (const w of ['oak', 'spruce', 'dark_oak', 'birch']) {
  def(`${w}_door`, 'door', { top: `${w}_door_top`, side: `${w}_door_bottom`, bottom: `${w}_door_bottom` }, 'cutout');
  def(`${w}_trapdoor`, 'trapdoor', `${w}_trapdoor`, 'cutout');
}
// 소품
def('lantern', 'lantern', 'lantern', 'emit');
def('chain', 'chain', 'chain', 'cutout');
def('lily_pad', 'flat', 'lily_pad', 'cutout', { tint: 'foliage' });
for (const c of ['white', 'red', 'blue', 'green', 'brown']) def(`${c}_carpet`, 'carpet', `${c}_wool`);
def('cobweb', 'cross', 'cobweb', 'cutout');
for (const p of ['short_grass', 'fern']) def(p, 'cross', p, 'cutout', { tint: 'grass' });
def('tall_grass', 'cross', 'tall_grass', 'cutout', { tint: 'grass', tall: true });
def('large_fern', 'cross', 'fern', 'cutout', { tint: 'grass', tall: true });
for (const p of ['poppy', 'dandelion', 'cornflower', 'oxeye_daisy', 'allium', 'azure_bluet', 'red_tulip', 'orange_tulip', 'white_tulip', 'blue_orchid', 'lily_of_the_valley'])
  def(p, 'cross', p, 'cutout');
def('rose_bush', 'cross', 'rose_bush', 'cutout', { tall: true });
def('lilac', 'cross', 'lilac', 'cutout', { tall: true });
def('sweet_berry_bush', 'cross', 'sweet_berry_bush', 'cutout');
def('wheat', 'crop', 'wheat', 'cutout');
def('carrots', 'crop', 'carrots', 'cutout');
def('potatoes', 'crop', 'potatoes', 'cutout');
def('sugar_cane', 'cross', 'sugar_cane', 'cutout', { tint: 'grass' });
for (const p of ['poppy', 'red_tulip', 'azure_bluet', 'dandelion', 'fern', 'oxeye_daisy']) def(`potted_${p}`, 'pot', p, 'cutout');

// =====================================================================
//  상태 테이블
// =====================================================================
export const STATES = [];
const byKey = new Map();
function keyOf(name, props) {
  const ks = props ? Object.keys(props).sort() : [];
  return 'minecraft:' + name + (ks.length ? '[' + ks.map(k => k + '=' + props[k]).join(',') + ']' : '');
}
export function S(name, props = null) {
  const key = keyOf(name, props);
  let id = byKey.get(key);
  if (id !== undefined) return id;
  const d = DEFS[name];
  if (!d) throw new Error('unknown block ' + name);
  id = STATES.length;
  STATES.push({ id, name, props: props || {}, def: d, key });
  byKey.set(key, id);
  return id;
}
STATES.push({ id: 0, name: '__unset', props: {}, def: DEFS.air, key: '__unset' });
export const AIR = S('air');

// 자주 쓰는 헬퍼
export const stairs = (m, facing, half = 'bottom', shape) => S(`${m}_stairs`, shape ? { facing, half, shape } : { facing, half });
export const slab = (m, type = 'bottom') => S(`${m}_slab`, { type });
export const log = (w, axis = 'y') => S(w, { axis });
export const leaves = n => S(n, { persistent: 'true' });
export const isFull = id => id > 1 && STATES[id].def.full;
export const isAirish = id => id <= 1;

// =====================================================================
//  연결형 블록 (울타리 · 판유리 · 담장) — 이웃을 보고 속성 결정
// =====================================================================
const DIR4 = [['north', 0, -1], ['south', 0, 1], ['west', -1, 0], ['east', 1, 0]];
export function resolveConn(get, x, y, z, id) {
  const st = STATES[id];
  const c = st.def.conn;
  if (!c) return id;
  const p = {};
  let n = 0;
  const conns = {};
  for (const [d, dx, dz] of DIR4) {
    const nb = get(x + dx, y, z + dz);
    const nd = STATES[nb]?.def;
    let ok = false;
    if (nd && nb > 1) {
      if (nd.full && nd.cat !== 'cutout') ok = true;
      else if (c === 'fence' && nd.conn === 'fence') ok = true;
      else if ((c === 'pane' || c === 'wall') && (nd.conn === 'pane' || nd.conn === 'wall')) ok = true;
    }
    conns[d] = ok; if (ok) n++;
  }
  if (c === 'wall') {
    const above = get(x, y + 1, z);
    const tall = above > 1 && STATES[above].def.full;
    for (const [d] of DIR4) p[d] = conns[d] ? (tall ? 'tall' : 'low') : 'none';
    const straight = n === 2 && ((conns.north && conns.south) || (conns.east && conns.west));
    const aboveId = above > 1 ? STATES[above].def : null;
    p.up = (!straight || (aboveId && aboveId.model !== 'none' && !aboveId.full)) ? 'true' : 'false';
  } else {
    for (const [d] of DIR4) p[d] = conns[d] ? 'true' : 'false';
  }
  return S(st.name, p);
}
