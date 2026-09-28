// =====================================================================
//  구조물 생성 순서 (먼저 지은 것이 땅을 예약한다)
// =====================================================================
import { buildCastle } from './castle.js';
import { buildCathedral } from './cathedral.js';
import { buildSquare, buildTownHall, buildTavern, buildHarbor, stoneBridge } from './civic.js';
import { cityStreets, paveStreets, cityWalls, lineHouses, streetLamps, cityGardens } from './city.js';
import { buildRoads } from './roads.js';
import { buildVillages, buildFarmsteads } from './villages.js';
import { CITY } from '../plan.js';
import { buildLandmarks } from './landmarks.js';
import { buildNature } from './nature.js';
import { chimneys } from './house.js';
import { waterTop, height, col, inside } from '../world.js';

const log = (...a) => console.log(((performance.now() / 1000).toFixed(1) + 's'), ...a);
const wet = (x, z) => inside(x, z) && waterTop[col(x, z)] > height[col(x, z)];

export const stats = {};
export function buildAll(info) {
  buildCastle(); log('  성');
  buildCathedral(); log('  대성당');
  buildSquare(); buildTownHall(); buildTavern(); log('  광장·시청·여관·길드');
  cityWalls(); log('  성벽');
  const streets = cityStreets();
  paveStreets(streets); log('  거리', streets.length);
  const bank = buildHarbor(info.riverPath); log('  항구');
  let far = bank(39) + 1; while (far < 330 && wet(far, 39)) far++;
  stoneBridge(bank(39) - 3, 39, far + 3, 39, 7, 68); log('  동문 다리');
  streetLamps(streets);
  stats.cityHouses = lineHouses(streets); log('  도시 집', stats.cityHouses);
  stats.gardens = cityGardens(); log('  뒤뜰', stats.gardens);
  stats.bridges = buildRoads(); log('  도로 · 다리', stats.bridges);
  stats.landmarks = buildLandmarks(); log('  명소');
  stats.villageHouses = buildVillages(); log('  마을 집', stats.villageHouses);
  stats.farmsteads = buildFarmsteads(CITY.x, CITY.z, CITY.R); log('  농가', stats.farmsteads);
  const n = buildNature(); stats.trees = n.trees; stats.plants = n.plants; log('  나무', n.trees, '풀꽃', n.plants);
  stats.chimneys = chimneys.length;
}
