// 내보낸 리전 파일을 독립 NBT 파서로 다시 읽어 블록 단위로 원본과 비교
//   NBT_LIB=<prismarine-nbt 경로> node tools/validate.js [샘플 청크 수]
import fs from 'node:fs';
import zlib from 'node:zlib';
import path from 'node:path';
import { createRequire } from 'node:module';
import { generate } from '../gen/main.js';
import { get, getPlaced, terrainAt } from '../gen/world.js';
import { STATES, resolveConn } from '../gen/registry.js';

const require = createRequire(import.meta.url);
const nbtLib = require(process.env.NBT_LIB || 'prismarine-nbt');
const dir = path.resolve('out/world/region');
generate();

function readChunk(cx, cz) {
  const rx = Math.floor(cx / 32), rz = Math.floor(cz / 32);
  const buf = fs.readFileSync(path.join(dir, `r.${rx}.${rz}.mca`));
  const i = ((cx & 31) + (cz & 31) * 32) * 4;
  const loc = buf.readUInt32BE(i), off = (loc >>> 8) * 4096, cnt = loc & 255;
  if (!loc) return null;
  const len = buf.readUInt32BE(off), type = buf[off + 4];
  if (type !== 2) throw new Error('compression ' + type);
  if (len + 4 > cnt * 4096) throw new Error('length overflow');
  return zlib.inflateSync(buf.subarray(off + 5, off + 4 + len));
}
const want = (x, y, z) => { let id = getPlaced(x, y, z) || terrainAt(x, y, z); if (getPlaced(x, y, z) && STATES[id].def.conn) id = resolveConn(get, x, y, z, id); return STATES[id].key; };
const keyOf = e => { const p = e.Properties ? Object.entries(e.Properties).sort().map(([k, v]) => `${k}=${v}`) : []; return e.Name + (p.length ? '[' + p.join(',') + ']' : ''); };

const samples = [[0, 0], [0, 1], [-1, -7], [15, 35], [-40, 20], [3, -44], [-62, -63], [62, 62], ...Array.from({ length: +(process.argv[2] || 12) }, (_, i) => [((i * 37) % 120) - 60, ((i * 53) % 120) - 60])];
let blocks = 0, bad = 0;
for (const [cx, cz] of samples) {
  const raw = readChunk(cx, cz);
  const { parsed } = await nbtLib.parse(raw);
  const root = nbtLib.simplify(parsed);
  if (root.xPos !== cx || root.zPos !== cz || root.Status !== 'minecraft:full' || root.yPos !== -4) throw new Error('header ' + JSON.stringify([root.xPos, root.zPos, root.Status]));
  for (const s of root.sections) {
    const pal = s.block_states.palette.map(keyOf);
    const data = s.block_states.data;
    const bits = pal.length > 1 ? Math.max(4, Math.ceil(Math.log2(pal.length))) : 0;
    const per = bits ? Math.floor(64 / bits) : 0;
    if (bits && data.length !== Math.ceil(4096 / per)) throw new Error('data length');
    for (let i = 0; i < 4096; i++) {
      let p = 0;
      if (bits) {
        const L = data[Math.floor(i / per)];
        const v = (BigInt.asUintN(32, BigInt(L[0])) << 32n) | BigInt.asUintN(32, BigInt(L[1]));
        p = Number((v >> BigInt((i % per) * bits)) & ((1n << BigInt(bits)) - 1n));
      }
      const x = cx * 16 + (i & 15), z = cz * 16 + ((i >> 4) & 15), y = s.Y * 16 + (i >> 8);
      blocks++;
      if (pal[p] !== want(x, y, z)) { if (bad++ < 5) console.log('MISMATCH', x, y, z, pal[p], want(x, y, z)); }
    }
  }
}
console.log(`검사 청크 ${samples.length}개, 블록 ${blocks}개, 불일치 ${bad}개`);
if (bad) process.exit(1);
