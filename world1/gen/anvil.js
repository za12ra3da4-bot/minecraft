// =====================================================================
//  NBT 쓰기 + Anvil(.mca) 리전 파일 내보내기  — Minecraft Java 1.21 청크 형식
// =====================================================================
import fs from 'node:fs';
import zlib from 'node:zlib';
import path from 'node:path';
import { STATES, resolveConn, AIR } from './registry.js';
import { get, getPlaced, secGet, terrainAt, height, waterTop, biome, BIOMES, col, HALF, CH, MIN_Y } from './world.js';

export const DATA_VERSION = 3955; // 1.21.1 — 더 높은 버전 서버는 불러올 때 자동 변환

// ── NBT 인코더
class W {
  constructor() { this.buf = Buffer.alloc(1 << 16); this.n = 0; }
  need(k) { if (this.n + k > this.buf.length) { const b = Buffer.alloc(Math.max(this.buf.length * 2, this.n + k)); this.buf.copy(b, 0, 0, this.n); this.buf = b; } }
  u8(v) { this.need(1); this.buf.writeUInt8(v & 255, this.n); this.n += 1; }
  i8(v) { this.need(1); this.buf.writeInt8(v, this.n); this.n += 1; }
  i16(v) { this.need(2); this.buf.writeInt16BE(v, this.n); this.n += 2; }
  i32(v) { this.need(4); this.buf.writeInt32BE(v, this.n); this.n += 4; }
  u32(v) { this.need(4); this.buf.writeUInt32BE(v >>> 0, this.n); this.n += 4; }
  i64(v) { this.need(8); this.buf.writeBigInt64BE(BigInt(v), this.n); this.n += 8; }
  str(s) { const b = Buffer.from(s, 'utf8'); this.i16(b.length); this.need(b.length); b.copy(this.buf, this.n); this.n += b.length; }
  out() { return this.buf.subarray(0, this.n); }
}
const T = { end: 0, byte: 1, short: 2, int: 3, long: 4, float: 5, double: 6, byteArray: 7, string: 8, list: 9, compound: 10, intArray: 11, longArray: 12 };
export const nbt = {
  byte: v => ({ t: 'byte', v }), short: v => ({ t: 'short', v }), int: v => ({ t: 'int', v }), long: v => ({ t: 'long', v }),
  string: v => ({ t: 'string', v }), list: (et, v) => ({ t: 'list', et, v }), compound: v => ({ t: 'compound', v }),
  longArray: (hi, lo) => ({ t: 'longArray', hi, lo }), float: v => ({ t: 'float', v }), double: v => ({ t: 'double', v }),
};
function payload(w, tag) {
  switch (tag.t) {
    case 'byte': w.i8(tag.v); break;
    case 'short': w.i16(tag.v); break;
    case 'int': w.i32(tag.v); break;
    case 'long': w.i64(tag.v); break;
    case 'float': w.need(4); w.buf.writeFloatBE(tag.v, w.n); w.n += 4; break;
    case 'double': w.need(8); w.buf.writeDoubleBE(tag.v, w.n); w.n += 8; break;
    case 'string': w.str(tag.v); break;
    case 'list':
      w.u8(tag.v.length ? T[tag.et] : T.end); w.i32(tag.v.length);
      for (const e of tag.v) payload(w, e);
      break;
    case 'compound':
      for (const [k, e] of Object.entries(tag.v)) { w.u8(T[e.t]); w.str(k); payload(w, e); }
      w.u8(T.end);
      break;
    case 'longArray':
      w.i32(tag.hi.length);
      for (let i = 0; i < tag.hi.length; i++) { w.u32(tag.hi[i]); w.u32(tag.lo[i]); }
      break;
    default: throw new Error('tag ' + tag.t);
  }
}
export function encodeRoot(compound, name = '') {
  const w = new W(); w.u8(T.compound); w.str(name); payload(w, compound); return w.out();
}

// ── 팔레트 인덱스를 long 배열로 (1.16+ 방식: long 경계를 넘지 않음)
function pack(indices, count, bits) {
  const per = Math.floor(64 / bits), n = Math.ceil(count / per);
  const hi = new Uint32Array(n), lo = new Uint32Array(n);
  for (let i = 0; i < count; i++) {
    const v = indices[i], li = Math.floor(i / per), off = (i % per) * bits;
    if (off + bits <= 32) lo[li] = (lo[li] | (v << off)) >>> 0;
    else if (off >= 32) hi[li] = (hi[li] | (v << (off - 32))) >>> 0;
    else { lo[li] = (lo[li] | (v << off)) >>> 0; hi[li] = (hi[li] | (v >>> (32 - off))) >>> 0; }
  }
  return { hi, lo };
}

function paletteEntry(id) {
  const st = STATES[id];
  const v = { Name: nbt.string('minecraft:' + st.name) };
  const ks = Object.keys(st.props);
  if (ks.length) v.Properties = nbt.compound(Object.fromEntries(ks.map(k => [k, nbt.string(String(st.props[k]))])));
  return nbt.compound(v);
}

// 섹션 16³ 의 최종 블록 id (연결형 블록 속성 확정 포함)
const connCache = new Map();
function sectionIds(cx, sy, cz, out) {
  const placed = secGet(cx, sy, cz);
  const x0 = cx * 16, y0 = sy * 16, z0 = cz * 16;
  let i = 0;
  for (let y = 0; y < 16; y++) for (let z = 0; z < 16; z++) for (let x = 0; x < 16; x++, i++) {
    let id = placed ? placed[i] : 0;
    if (!id) id = terrainAt(x0 + x, y0 + y, z0 + z);
    else if (STATES[id].def.conn) id = resolveConn(get, x0 + x, y0 + y, z0 + z, id);
    out[i] = id;
  }
}

function chunkNbt(cx, cz) {
  // 이 청크의 지형 최고 높이
  let maxH = MIN_Y, minH = 9999;
  for (let x = 0; x < 16; x++) for (let z = 0; z < 16; z++) {
    const c = col(cx * 16 + x, cz * 16 + z);
    maxH = Math.max(maxH, height[c], waterTop[c]); minH = Math.min(minH, height[c]);
  }
  const bio = BIOMES[biome[col(cx * 16 + 8, cz * 16 + 8)]] || 'plains';
  const sections = [];
  const ids = new Uint16Array(4096), idx = new Uint16Array(4096);
  for (let sy = -4; sy < 20; sy++) {
    const placed = secGet(cx, sy, cz);
    const top = sy * 16 + 15, bot = sy * 16;
    let palette;
    if (!placed && bot > maxH) {
      palette = [AIR]; // 빈 하늘
    } else {
      sectionIds(cx, sy, cz, ids);
      const map = new Map(); palette = [];
      for (let i = 0; i < 4096; i++) {
        let p = map.get(ids[i]);
        if (p === undefined) { p = palette.length; map.set(ids[i], p); palette.push(ids[i]); }
        idx[i] = p;
      }
    }
    const bs = { palette: nbt.list('compound', palette.map(paletteEntry)) };
    if (palette.length > 1) {
      const bits = Math.max(4, Math.ceil(Math.log2(palette.length)));
      const { hi, lo } = pack(idx, 4096, bits);
      bs.data = nbt.longArray(hi, lo);
    }
    sections.push(nbt.compound({
      Y: nbt.byte(sy),
      block_states: nbt.compound(bs),
      biomes: nbt.compound({ palette: nbt.list('string', [nbt.string('minecraft:' + (sy * 16 > 150 && bio !== 'jagged_peaks' && bio !== 'snowy_slopes' ? bio : bio))]) }),
    }));
  }
  return nbt.compound({
    DataVersion: nbt.int(DATA_VERSION),
    xPos: nbt.int(cx), zPos: nbt.int(cz), yPos: nbt.int(-4),
    Status: nbt.string('minecraft:full'),
    LastUpdate: nbt.long(0), InhabitedTime: nbt.long(0),
    isLightOn: nbt.byte(0),
    sections: nbt.list('compound', sections),
    block_entities: nbt.list('compound', []),
    block_ticks: nbt.list('compound', []), fluid_ticks: nbt.list('compound', []),
    PostProcessing: nbt.list('list', []),
    structures: nbt.compound({ References: nbt.compound({}), starts: nbt.compound({}) }),
  });
}

// ── level.dat: 스폰, 월드 경계, 경계 밖은 평평한 바다(평지 생성기), 게임 규칙
export function exportLevelDat(worldDir, o) {
  const { spawn, name = 'Arden', border = 2000 } = o;
  const s = nbt.string, b = nbt.byte, i = nbt.int, l = nbt.long;
  const layer = (block, height) => nbt.compound({ block: s('minecraft:' + block), height: i(height) });
  const rules = {
    doFireTick: 'false', mobGriefing: 'false', doInsomnia: 'false', doTraderSpawning: 'false', doPatrolSpawning: 'false',
    disableRaids: 'true', spawnRadius: '0', keepInventory: 'false', announceAdvancements: 'true',
  };
  const data = nbt.compound({
    DataVersion: i(DATA_VERSION),
    version: i(19133),
    Version: nbt.compound({ Id: i(DATA_VERSION), Name: s('1.21.1'), Series: s('main'), Snapshot: b(0) }),
    LevelName: s(name),
    GameType: i(2), Difficulty: b(2), hardcore: b(0), allowCommands: b(1), initialized: b(1),
    SpawnX: i(spawn[0]), SpawnY: i(spawn[1]), SpawnZ: i(spawn[2]), SpawnAngle: nbt.float(180),
    Time: l(0), DayTime: l(1000), LastPlayed: l(Date.now()),
    raining: b(0), rainTime: i(120000), thundering: b(0), thunderTime: i(120000), clearWeatherTime: i(0),
    BorderCenterX: nbt.double(0), BorderCenterZ: nbt.double(0), BorderSize: nbt.double(border),
    BorderSafeZone: nbt.double(5), BorderDamagePerBlock: nbt.double(0.2), BorderWarningBlocks: nbt.double(5), BorderWarningTime: nbt.double(15),
    BorderSizeLerpTarget: nbt.double(border), BorderSizeLerpTime: l(0),
    GameRules: nbt.compound(Object.fromEntries(Object.entries(rules).map(([k, v]) => [k, s(v)]))),
    DataPacks: nbt.compound({ Enabled: nbt.list('string', [s('vanilla')]), Disabled: nbt.list('string', []) }),
    WorldGenSettings: nbt.compound({
      seed: l(20260928), generate_features: b(0), bonus_chest: b(0),
      dimensions: nbt.compound({
        'minecraft:overworld': nbt.compound({
          type: s('minecraft:overworld'),
          generator: nbt.compound({
            type: s('minecraft:flat'),
            settings: nbt.compound({
              biome: s('minecraft:ocean'), lakes: b(0), features: b(0),
              layers: nbt.list('compound', [layer('bedrock', 1), layer('stone', 90), layer('sand', 10), layer('water', 27)]),
            }),
          }),
        }),
        'minecraft:the_nether': nbt.compound({
          type: s('minecraft:the_nether'),
          generator: nbt.compound({ type: s('minecraft:noise'), settings: s('minecraft:nether'), biome_source: nbt.compound({ type: s('minecraft:multi_noise'), preset: s('minecraft:nether') }) }),
        }),
        'minecraft:the_end': nbt.compound({
          type: s('minecraft:the_end'),
          generator: nbt.compound({ type: s('minecraft:noise'), settings: s('minecraft:end'), biome_source: nbt.compound({ type: s('minecraft:the_end') }) }),
        }),
      }),
    }),
  });
  fs.writeFileSync(path.join(worldDir, 'level.dat'), zlib.gzipSync(encodeRoot(nbt.compound({ Data: data }))));
}

export function exportRegions(dir, onProgress) {
  fs.mkdirSync(dir, { recursive: true });
  const c0 = -HALF / 16, c1 = HALF / 16 - 1;
  const r0 = Math.floor(c0 / 32), r1 = Math.floor(c1 / 32);
  let done = 0, bytes = 0;
  const total = (c1 - c0 + 1) ** 2;
  for (let rx = r0; rx <= r1; rx++) for (let rz = r0; rz <= r1; rz++) {
    const header = Buffer.alloc(8192);
    const chunks = [];
    let sector = 2;
    const ts = Math.floor(Date.now() / 1000);
    for (let lz = 0; lz < 32; lz++) for (let lx = 0; lx < 32; lx++) {
      const cx = rx * 32 + lx, cz = rz * 32 + lz;
      if (cx < c0 || cx > c1 || cz < c0 || cz > c1) continue;
      const raw = encodeRoot(chunkNbt(cx, cz));
      const comp = zlib.deflateSync(raw, { level: 6 });
      const len = comp.length + 1;
      const sectors = Math.ceil((len + 4) / 4096);
      if (sectors > 255) throw new Error(`chunk ${cx},${cz} too large (${sectors} sectors)`);
      const b = Buffer.alloc(sectors * 4096);
      b.writeUInt32BE(len, 0); b.writeUInt8(2, 4); comp.copy(b, 5);
      const hi = (lx + lz * 32) * 4;
      header.writeUInt32BE(((sector << 8) | sectors) >>> 0, hi);
      header.writeUInt32BE(ts, 4096 + hi);
      chunks.push(b); sector += sectors;
      if (++done % 500 === 0 && onProgress) onProgress(done, total);
    }
    if (!chunks.length) continue;
    const file = path.join(dir, `r.${rx}.${rz}.mca`);
    const data = Buffer.concat([header, ...chunks]);
    fs.writeFileSync(file, data);
    bytes += data.length;
  }
  return { chunks: done, bytes };
}
