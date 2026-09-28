// =====================================================================
//  1세계 생성기 진입점
//    node --max-old-space-size=12000 gen/main.js [--no-export] [--no-map] [--out <폴더>]
//    기본 출력: out/world  (level.dat + region/*.mca)
// =====================================================================
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { generateTerrain } from './terrain.js';
import { buildAll } from './build/index.js';
import { exportRegions, exportLevelDat } from './anvil.js';
import { writeMap, topOf } from './mapimg.js';
import { sectionCount } from './world.js';
import { GATES } from './plan.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const argv = process.argv.slice(2);
const args = new Set(argv);
const t = () => ((performance.now() / 1000).toFixed(1) + 's');

export function generate() {
  console.log(t(), '지형 생성');
  const info = generateTerrain();
  console.log(t(), '구조물 생성');
  buildAll(info);
  console.log(t(), '구조물 섹션', sectionCount());
  return info;
}

// 스폰: 남문 바깥 길 위
export function spawnPoint() {
  const x = GATES.south.x, z = GATES.south.z + 28;
  return [x, topOf(x, z)[0] + 1, z];
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  generate();
  const outDir = argv.includes('--out') ? path.resolve(argv[argv.indexOf('--out') + 1]) : path.join(ROOT, 'out', 'world');
  if (!args.has('--no-map')) {
    fs.mkdirSync(path.join(ROOT, 'out'), { recursive: true });
    writeMap(path.join(ROOT, 'out', 'map.png'));
    console.log(t(), '지도 저장 out/map.png');
  }
  if (!args.has('--no-export')) {
    const r = exportRegions(path.join(outDir, 'region'), (d, n) => process.stdout.write(`\r  청크 ${d}/${n}`));
    console.log('\n' + t(), `리전 저장 청크 ${r.chunks}개, ${(r.bytes / 1e6).toFixed(1)}MB`);
    const sp = spawnPoint();
    exportLevelDat(outDir, { spawn: sp, name: 'Arden' });
    console.log(t(), `level.dat 저장 (스폰 ${sp.join(', ')}) → ${outDir}`);
  }
}
