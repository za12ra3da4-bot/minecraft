import {
  Rng,
  bytesToBase64,
  encodeRLE,
  getMapDef,
  type MapData,
  type MapDef,
  type NationId,
} from '@warfront/shared';
import { generateGeo, geoDimensions } from './geoGen';
import type { MapContext } from './MapContext';
import { assignHomeNations } from './nationGen';
import { generateRivers } from './riverGen';
import { generateRoads } from './roadGen';
import { generateSettlements } from './settlementGen';
import { generateTerrain } from './terrainGen';
import { generateTerritories } from './territoryGen';

/** Server-side generated map: transport data plus raw grids for the simulation. */
export interface GeneratedMap {
  def: MapDef;
  data: MapData;
  terrain: Uint8Array;
  flags: Uint8Array;
  territoryGrid: Int16Array;
  /** Nation each territory starts with (if that nation is in play). */
  homeNation: (NationId | null)[];
  /** Capital city id per map nation. */
  capitals: Map<NationId, number>;
}

const cache = new Map<string, GeneratedMap>();

/** Generates (or returns the cached) map. Maps are deterministic per definition seed. */
export function getGeneratedMap(mapId: string): GeneratedMap {
  const cached = cache.get(mapId);
  if (cached) return cached;
  const def = getMapDef(mapId);
  if (!def) throw new Error(`Unknown map ${mapId}`);
  const map = generateMap(def);
  cache.set(mapId, map);
  return map;
}

export function generateMap(def: MapDef): GeneratedMap {
  if (def.geo) def = { ...def, ...geoDimensions(def.geo) };
  const cols = Math.round(def.width / def.cellSize);
  const rows = Math.round(def.height / def.cellSize);
  const ctx: MapContext = {
    def,
    rng: new Rng(def.seed),
    cols,
    rows,
    cs: def.cellSize,
    elev: new Float32Array((cols + 1) * (rows + 1)),
    relief: new Float32Array((cols + 1) * (rows + 1)),
    heights: new Uint8Array((cols + 1) * (rows + 1)),
    terrain: new Uint8Array(cols * rows),
    flags: new Uint8Array(cols * rows),
    territory: new Int16Array(cols * rows).fill(-1),
  };

  let rivers, territories, cities, capitals, home;
  if (def.geo) {
    ({ rivers, territories, cities, capitals, home } = generateGeo(ctx));
  } else {
    generateTerrain(ctx);
    rivers = generateRivers(ctx);
    const { drafts, capitalTerritories } = generateTerritories(ctx);
    home = assignHomeNations(ctx, drafts, capitalTerritories);
    ({ territories, cities, capitals } = generateSettlements(ctx, drafts, home, capitalTerritories));
  }
  const { roads, bridges } = generateRoads(ctx, territories, cities);

  const data: MapData = {
    id: def.id,
    name: def.name,
    seed: def.seed,
    width: def.width,
    height: def.height,
    cellSize: def.cellSize,
    cols,
    rows,
    heights: bytesToBase64(ctx.heights),
    terrain: encodeRLE(ctx.terrain),
    flags: encodeRLE(ctx.flags),
    territoryGrid: encodeRLE(ctx.territory),
    rivers,
    roads,
    bridges,
    territories,
    cities,
  };
  return {
    def,
    data,
    terrain: ctx.terrain,
    flags: ctx.flags,
    territoryGrid: ctx.territory,
    homeNation: home,
    capitals,
  };
}
