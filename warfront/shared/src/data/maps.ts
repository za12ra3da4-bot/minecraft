import type { DiploState } from '../types/game';
import type { NationId } from '../types/nation';

/** Ellipse in normalised map coordinates that raises (weight > 0) or sinks (weight < 0) the land. */
export interface LandShape {
  x: number;
  y: number;
  rx: number;
  ry: number;
  weight: number;
}

export interface MapRiver {
  /** Control points in normalised coordinates. */
  points: [number, number][];
  width: number;
}

export interface StartingArmyPlan {
  /** Total soldiers placed at game start. */
  total: number;
  /** Number of armies (including the grand army). */
  count: number;
  /** Size of the grand army placed near the capital (0 = none). */
  grand: number;
}

/** Mountain range in longitude/latitude degrees (real-world maps). */
export interface GeoMountain {
  lon: number;
  lat: number;
  rx: number;
  ry: number;
  weight: number;
}

export interface MapNationSlot {
  nation: NationId;
  /** Capital location in normalised coordinates (procedural maps). */
  anchor: [number, number];
  /** Relative share of claimed land. */
  share: number;
  armies: StartingArmyPlan;
}

export interface MapDef {
  id: string;
  /** Real-world geography dataset (shared/src/data/geo/<geo>.json); procedural when absent. */
  geo?: 'europe';
  mountains?: GeoMountain[];
  name: string;
  description: string;
  width: number;
  height: number;
  cellSize: number;
  seed: number;
  /** Base land bias. High values produce a land-only battlefield. */
  baseLand: number;
  /** How strongly the borders of the map sink into the sea (0 = no sea at edges). */
  edgeFalloff: number;
  landShapes: LandShape[];
  /** Noise feature size in world units. */
  noiseScale: number;
  /** Share of land cells that become hills. */
  hillShare: number;
  /** Share of land cells covered by forest. */
  forestShare: number;
  rivers: MapRiver[];
  territoryCount: number;
  /** Share of land owned by nations at start, the rest is unclaimed. */
  claimedShare: number;
  /** Share of territories (besides capitals) that receive a town. */
  cityShare: number;
  nations: MapNationSlot[];
  initialRelations: { a: NationId; b: NationId; state: DiploState }[];
  /** Historical alliances: every pair inside a bloc starts allied. */
  blocs?: NationId[][];
  /** Nations that start at peace with everyone. */
  neutrals?: NationId[];
}

export const MAPS: MapDef[] = [
  {
    id: 'europe',
    name: 'Europe 1812',
    geo: 'europe',
    description: 'June 1812: Napoleon\'s empire at its height. Real geography from Lisbon to Moscow, the French bloc against the Coalition, Austria and Prussia undecided.',
    width: 4800,
    height: 3872,
    cellSize: 16,
    seed: 1815,
    baseLand: 0,
    edgeFalloff: 0,
    landShapes: [],
    noiseScale: 700,
    hillShare: 0.13,
    forestShare: 0.2,
    rivers: [],
    territoryCount: 0,
    claimedShare: 1,
    cityShare: 0,
    mountains: [
      { lon: 10, lat: 46.4, rx: 4.6, ry: 1.1, weight: 0.85 },
      { lon: 0.5, lat: 42.7, rx: 2.8, ry: 0.45, weight: 0.75 },
      { lon: 22.5, lat: 48.8, rx: 3, ry: 0.9, weight: 0.55 },
      { lon: 25.6, lat: 46.3, rx: 1.2, ry: 1.8, weight: 0.55 },
      { lon: 24, lat: 45.5, rx: 3, ry: 0.6, weight: 0.5 },
      { lon: 13, lat: 63, rx: 3, ry: 4, weight: 0.7 },
      { lon: 8, lat: 61, rx: 2.5, ry: 2, weight: 0.7 },
      { lon: 18, lat: 43.6, rx: 3.5, ry: 1.4, weight: 0.55 },
      { lon: 24.5, lat: 42.6, rx: 2, ry: 0.6, weight: 0.5 },
      { lon: 13, lat: 42.5, rx: 1.2, ry: 3.6, weight: 0.5 },
      { lon: 33, lat: 38, rx: 6, ry: 1.6, weight: 0.5 },
      { lon: 36, lat: 40.8, rx: 6, ry: 0.7, weight: 0.45 },
      { lon: 43, lat: 42.8, rx: 4, ry: 0.8, weight: 0.85 },
      { lon: 3, lat: 45.3, rx: 1.3, ry: 1, weight: 0.4 },
      { lon: -4.5, lat: 57, rx: 1.8, ry: 1, weight: 0.45 },
      { lon: -4.5, lat: 40.5, rx: 3, ry: 1, weight: 0.35 },
      { lon: -3.3, lat: 37.1, rx: 1.5, ry: 0.4, weight: 0.5 },
      { lon: -5, lat: 33, rx: 6, ry: 1, weight: 0.6 },
      { lon: 10, lat: 50.8, rx: 3, ry: 1, weight: 0.3 },
      { lon: 13.5, lat: 50, rx: 2.5, ry: 1.2, weight: 0.35 },
      { lon: 21.5, lat: 39.5, rx: 1, ry: 1.8, weight: 0.5 },
    ],
    nations: [
      { nation: 'france', anchor: [0, 0], share: 1, armies: { total: 300_000, count: 30, grand: 108_000 } },
      { nation: 'britain', anchor: [0, 0], share: 1, armies: { total: 140_000, count: 16, grand: 58_456 } },
      { nation: 'prussia', anchor: [0, 0], share: 1, armies: { total: 120_000, count: 14, grand: 42_000 } },
      { nation: 'austria', anchor: [0, 0], share: 1, armies: { total: 200_000, count: 22, grand: 62_000 } },
      { nation: 'russia', anchor: [0, 0], share: 1, armies: { total: 320_000, count: 32, grand: 120_000 } },
      { nation: 'spain', anchor: [0, 0], share: 1, armies: { total: 120_000, count: 16, grand: 39_900 } },
      { nation: 'portugal', anchor: [0, 0], share: 1, armies: { total: 50_000, count: 6, grand: 18_000 } },
      { nation: 'sweden', anchor: [0, 0], share: 1, armies: { total: 70_000, count: 10, grand: 28_000 } },
      { nation: 'denmark', anchor: [0, 0], share: 1, armies: { total: 60_000, count: 8, grand: 20_000 } },
      { nation: 'ottoman', anchor: [0, 0], share: 1, armies: { total: 200_000, count: 22, grand: 60_000 } },
      { nation: 'warsaw', anchor: [0, 0], share: 1, armies: { total: 90_000, count: 10, grand: 36_000 } },
      { nation: 'rhine', anchor: [0, 0], share: 1, armies: { total: 130_000, count: 16, grand: 40_000 } },
      { nation: 'italy', anchor: [0, 0], share: 1, armies: { total: 80_000, count: 10, grand: 30_000 } },
      { nation: 'naples', anchor: [0, 0], share: 1, armies: { total: 60_000, count: 8, grand: 25_000 } },
    ],
    initialRelations: [],
    blocs: [
      ['france', 'rhine', 'warsaw', 'italy', 'naples', 'denmark'],
      ['britain', 'russia', 'spain', 'portugal', 'sweden'],
    ],
    neutrals: ['austria', 'prussia', 'ottoman'],
  },
  {
    id: 'valois',
    name: 'Valois Ridge',
    description: 'A dense battlefield of farms, woods and ridges. June 1815: Britain and Prussia stand together against the Emperor\'s last army.',
    width: 3600,
    height: 2400,
    cellSize: 12,
    seed: 6181,
    baseLand: 1.2,
    edgeFalloff: 0,
    landShapes: [{ x: 0.62, y: 0.12, rx: 0.05, ry: 0.04, weight: -2.6 }],
    noiseScale: 700,
    hillShare: 0.12,
    forestShare: 0.2,
    rivers: [
      { points: [[0.8, -0.02], [0.76, 0.3], [0.81, 0.62], [0.78, 1.02]], width: 5 },
      { points: [[-0.02, 0.72], [0.22, 0.76], [0.4, 0.88], [0.47, 1.02]], width: 4 },
    ],
    territoryCount: 175,
    claimedShare: 1,
    cityShare: 0.22,
    nations: [
      { nation: 'britain', anchor: [0.3, 0.3], share: 1.0, armies: { total: 168_000, count: 44, grand: 58_456 } },
      { nation: 'france', anchor: [0.4, 0.78], share: 1.15, armies: { total: 196_000, count: 50, grand: 39_900 } },
      { nation: 'prussia', anchor: [0.88, 0.32], share: 0.65, armies: { total: 120_000, count: 34, grand: 41_200 } },
    ],
    initialRelations: [{ a: 'britain', b: 'prussia', state: 'ALLIANCE' }],
  },
];

export function getMapDef(id: string): MapDef | undefined {
  return MAPS.find((m) => m.id === id);
}
