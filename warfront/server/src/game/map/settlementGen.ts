import {
  CITY_TYPE_STATS,
  CellFlag,
  NAME_STYLES,
  Terrain,
  getNation,
  type CityDef,
  type CityType,
  type NameStyleId,
  type NationId,
  type ResourceKind,
  type Rng,
  type TerritoryDef,
} from '@warfront/shared';
import { cellAtWorld, type MapContext } from './MapContext';
import type { TerritoryDraft } from './territoryGen';

export interface SettlementResult {
  territories: TerritoryDef[];
  cities: CityDef[];
  /** Capital city id per nation. */
  capitals: Map<NationId, number>;
}

class NameGenerator {
  private used = new Set<string>();

  constructor(private rng: Rng) {}

  next(styleId: NameStyleId): string {
    const style = NAME_STYLES[styleId];
    for (let attempt = 0; attempt < 40; attempt++) {
      let name: string;
      if (attempt < 3 && this.rng.chance(0.12)) name = this.rng.pick(style.whole);
      else name = this.rng.pick(style.prefixes) + this.rng.pick(style.suffixes);
      if (!this.used.has(name)) {
        this.used.add(name);
        return name;
      }
    }
    const base = this.rng.pick(style.prefixes) + this.rng.pick(style.suffixes);
    let i = 2;
    while (this.used.has(`${base} ${i}`)) i++;
    const name = `${base} ${i}`;
    this.used.add(name);
    return name;
  }
}

function pickResource(rng: Rng, terrain: Terrain, coastal: boolean, southern: boolean): ResourceKind {
  if (terrain === Terrain.HILLS) return rng.chance(0.5) ? 'IRON' : 'COAL';
  if (terrain === Terrain.FOREST) return rng.chance(0.75) ? 'TIMBER' : 'HORSES';
  const r = rng.next();
  if (southern && r < 0.3) return 'WINE';
  if (coastal && r < 0.45) return 'GRAIN';
  if (r < 0.62) return 'GRAIN';
  if (r < 0.82) return 'HORSES';
  return rng.chance(0.5) ? 'COAL' : 'TIMBER';
}

/** Towns, names, population, industry and resources for every territory. */
export function generateSettlements(
  ctx: MapContext,
  drafts: TerritoryDraft[],
  home: (NationId | null)[],
  capitalTerritories: number[],
): SettlementResult {
  const { def, rng, cs } = ctx;
  const names = new NameGenerator(rng);
  const area = drafts.reduce((s, d) => s + d.cells, 0) / drafts.length;
  const types: CityType[] = drafts.map(() => 'VILLAGE');
  const capitalSet = new Set(capitalTerritories);
  capitalTerritories.forEach((t) => (types[t] = 'CAPITAL'));

  const resources = drafts.map((d) => pickResource(rng, d.terrain, d.coastal, d.cy > def.height * 0.6));

  const scored = drafts
    .filter((d) => !capitalSet.has(d.id))
    .map((d) => ({
      d,
      score: rng.next() * 0.6 + (d.riverside ? 0.45 : 0) + (d.coastal ? 0.3 : 0) + (d.terrain === Terrain.PLAINS ? 0.2 : 0) + Math.min(0.3, d.cells / area / 4),
    }))
    .sort((a, b) => b.score - a.score);
  const cityCount = Math.round(drafts.length * def.cityShare);
  const makeCity = (d: TerritoryDraft): CityType => {
    if (d.coastal && rng.chance(0.6)) return 'PORT';
    if (d.terrain === Terrain.HILLS || resources[d.id] === 'IRON' || resources[d.id] === 'COAL') return rng.chance(0.7) ? 'INDUSTRIAL_CITY' : 'CITY';
    return rng.chance(0.15) ? 'INDUSTRIAL_CITY' : 'CITY';
  };
  for (let i = 0; i < Math.min(cityCount, scored.length); i++) types[scored[i].d.id] = makeCity(scored[i].d);

  // Every nation gets at least two production towns besides its capital.
  for (const slot of def.nations) {
    const own = drafts.filter((d) => home[d.id] === slot.nation);
    let producing = own.filter((d) => types[d.id] !== 'VILLAGE').length;
    const villages = own
      .filter((d) => types[d.id] === 'VILLAGE')
      .sort((a, b) => b.cells - a.cells);
    for (const v of villages) {
      if (producing >= 3) break;
      types[v.id] = makeCity(v);
      producing++;
    }
  }

  const cities: CityDef[] = [];
  const territories: TerritoryDef[] = [];
  const capitals = new Map<NationId, number>();
  for (const d of drafts) {
    const owner = home[d.id];
    const style: NameStyleId = owner ? getNation(owner).nameStyle : 'generic';
    const name = names.next(style);
    const type = types[d.id];
    const stats = CITY_TYPE_STATS[type];
    const cityId = cities.length;
    cities.push({ id: cityId, name, type, territoryId: d.id, x: d.cx, y: d.cy });
    if (type === 'CAPITAL' && owner) capitals.set(owner, cityId);

    const terrainFactor = d.terrain === Terrain.HILLS ? 0.75 : d.terrain === Terrain.FOREST ? 0.85 : 1.1;
    const sizeFactor = Math.max(0.6, Math.min(1.6, Math.sqrt(d.cells / area)));
    const population = Math.round((rng.range(14_000, 36_000) * stats.population * terrainFactor * sizeFactor) / 100) * 100;
    const res = resources[d.id];
    const industry = Math.round(rng.range(2, 5) * stats.industry + (res === 'IRON' || res === 'COAL' ? 3 : 0) + (res === 'TIMBER' ? 1 : 0));
    territories.push({
      id: d.id,
      name,
      cx: d.cx,
      cy: d.cy,
      neighbors: d.neighbors,
      population,
      industry,
      resource: res,
      cityId,
      cells: d.cells,
      coastal: d.coastal,
      terrain: d.terrain,
    });

    // Town footprint on the grid (defence bonus + rendering).
    const radius = type === 'CAPITAL' ? 2 : type === 'VILLAGE' ? 0 : 1;
    for (let oy = -radius; oy <= radius; oy++) {
      for (let ox = -radius; ox <= radius; ox++) {
        const c = cellAtWorld(ctx, d.cx + ox * cs, d.cy + oy * cs);
        if (c >= 0 && ctx.territory[c] === d.id) ctx.flags[c] |= CellFlag.TOWN;
      }
    }
  }
  return { territories, cities, capitals };
}
