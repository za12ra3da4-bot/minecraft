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

export interface MapNationSlot {
  nation: NationId;
  /** Capital location in normalised coordinates. */
  anchor: [number, number];
  /** Relative share of claimed land. */
  share: number;
  armies: StartingArmyPlan;
}

export interface MapDef {
  id: string;
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
}

export const MAPS: MapDef[] = [
  {
    id: 'continental',
    name: 'Continental',
    description: 'A vast continent split between ten great powers. Long fronts, rivers and coastlines.',
    width: 4800,
    height: 3200,
    cellSize: 16,
    seed: 1815,
    baseLand: -0.05,
    edgeFalloff: 1.15,
    landShapes: [
      { x: 0.5, y: 0.5, rx: 0.47, ry: 0.43, weight: 0.95 },
      { x: 0.16, y: 0.24, rx: 0.13, ry: 0.15, weight: 0.65 },
      { x: 0.56, y: 0.13, rx: 0.16, ry: 0.12, weight: 0.6 },
      { x: 0.87, y: 0.35, rx: 0.13, ry: 0.25, weight: 0.65 },
      { x: 0.15, y: 0.78, rx: 0.14, ry: 0.15, weight: 0.65 },
      { x: 0.8, y: 0.77, rx: 0.15, ry: 0.15, weight: 0.6 },
      { x: 0.5, y: 0.9, rx: 0.15, ry: 0.09, weight: -1.25 },
      { x: 0.37, y: 0.06, rx: 0.08, ry: 0.07, weight: -1.0 },
      { x: 0.04, y: 0.5, rx: 0.07, ry: 0.12, weight: -0.7 },
      { x: 0.66, y: 0.96, rx: 0.06, ry: 0.06, weight: -0.8 },
    ],
    noiseScale: 900,
    hillShare: 0.14,
    forestShare: 0.22,
    rivers: [
      { points: [[0.44, 0.6], [0.43, 0.47], [0.39, 0.33], [0.37, 0.2], [0.36, 0.06]], width: 7 },
      { points: [[0.47, 0.55], [0.58, 0.59], [0.7, 0.62], [0.83, 0.63], [0.98, 0.67]], width: 8 },
      { points: [[0.31, 0.44], [0.22, 0.5], [0.12, 0.52], [0.02, 0.51]], width: 6 },
      { points: [[0.68, 0.47], [0.66, 0.35], [0.65, 0.21], [0.66, 0.02]], width: 6 },
      { points: [[0.26, 0.63], [0.3, 0.76], [0.37, 0.86], [0.43, 0.9]], width: 5 },
      { points: [[0.85, 0.15], [0.8, 0.3], [0.79, 0.45], [0.83, 0.62]], width: 5 },
    ],
    territoryCount: 230,
    claimedShare: 0.86,
    cityShare: 0.3,
    nations: [
      { nation: 'britain', anchor: [0.15, 0.22], share: 1.0, armies: { total: 190_000, count: 20, grand: 58_456 } },
      { nation: 'france', anchor: [0.24, 0.5], share: 1.25, armies: { total: 230_000, count: 22, grand: 72_300 } },
      { nation: 'prussia', anchor: [0.5, 0.3], share: 1.0, armies: { total: 180_000, count: 20, grand: 41_200 } },
      { nation: 'austria', anchor: [0.56, 0.58], share: 1.1, armies: { total: 185_000, count: 20, grand: 45_000 } },
      { nation: 'russia', anchor: [0.86, 0.3], share: 1.35, armies: { total: 220_000, count: 22, grand: 64_000 } },
      { nation: 'spain', anchor: [0.14, 0.8], share: 0.9, armies: { total: 140_000, count: 16, grand: 36_000 } },
      { nation: 'netherlands', anchor: [0.33, 0.25], share: 0.6, armies: { total: 100_000, count: 14, grand: 25_000 } },
      { nation: 'sweden', anchor: [0.57, 0.1], share: 0.75, armies: { total: 110_000, count: 14, grand: 30_000 } },
      { nation: 'ottoman', anchor: [0.82, 0.78], share: 1.15, armies: { total: 180_000, count: 20, grand: 48_000 } },
      { nation: 'poland', anchor: [0.68, 0.36], share: 0.7, armies: { total: 110_000, count: 14, grand: 28_000 } },
    ],
    initialRelations: [],
  },
  {
    id: 'valois',
    name: 'Valois Ridge',
    description: 'A dense battlefield of farms, woods and ridges. Britain and Prussia stand together against France.',
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
