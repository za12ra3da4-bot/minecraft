/** Terrain codes stored per grid cell. */
export const Terrain = {
  WATER: 0,
  PLAINS: 1,
  FOREST: 2,
  HILLS: 3,
  MARSH: 4,
} as const;
export type Terrain = (typeof Terrain)[keyof typeof Terrain];

/** Bit flags stored per grid cell. */
export const CellFlag = {
  RIVER: 1,
  ROAD: 2,
  BRIDGE: 4,
  COAST: 8,
  TOWN: 16,
  /** Land outside the playable theatre (drawn, but impassable). */
  OUTSIDE: 32,
  /** Coastal water that armies can cross slowly (straits, channels). */
  SHALLOW: 64,
} as const;

export const CITY_TYPES = ['CAPITAL', 'CITY', 'PORT', 'INDUSTRIAL_CITY', 'VILLAGE'] as const;
export type CityType = (typeof CITY_TYPES)[number];

export const RESOURCE_KINDS = ['GRAIN', 'IRON', 'COAL', 'TIMBER', 'HORSES', 'WINE'] as const;
export type ResourceKind = (typeof RESOURCE_KINDS)[number];

export interface TerritoryDef {
  id: number;
  name: string;
  /** Label / rally point in world units (always inside the territory). */
  cx: number;
  cy: number;
  neighbors: number[];
  population: number;
  industry: number;
  resource: ResourceKind;
  cityId: number | null;
  /** Number of grid cells (area). */
  cells: number;
  coastal: boolean;
  /** Dominant terrain of the territory. */
  terrain: Terrain;
}

export interface CityDef {
  id: number;
  name: string;
  type: CityType;
  territoryId: number;
  x: number;
  y: number;
}

export interface RiverDef {
  /** Flat [x0, y0, x1, y1, ...] world coordinates. */
  points: number[];
  width: number;
}

export interface RoadDef {
  points: number[];
  major: boolean;
}

export interface BridgeDef {
  x: number;
  y: number;
  angle: number;
}

/**
 * Static map data. Generated on the server once per game and sent to every
 * client in the init packet. Grids are RLE+base64 encoded (see utils/codec).
 */
export interface MapData {
  id: string;
  name: string;
  seed: number;
  width: number;
  height: number;
  cellSize: number;
  cols: number;
  rows: number;
  /** Elevation at grid vertices ((cols+1)*(rows+1)), 0..255, sea level = SEA_LEVEL_BYTE. Plain base64 bytes. */
  heights: string;
  /** Terrain code per cell (cols*rows). */
  terrain: string;
  /** CellFlag bits per cell. */
  flags: string;
  /** Territory id per cell or -1 for water (cols*rows). */
  territoryGrid: string;
  rivers: RiverDef[];
  roads: RoadDef[];
  bridges: BridgeDef[];
  territories: TerritoryDef[];
  cities: CityDef[];
}

/** Decoded, ready to use grids. */
export interface MapGrids {
  heights: Uint8Array;
  terrain: Uint8Array;
  flags: Uint8Array;
  territoryGrid: Int16Array;
}

export const SEA_LEVEL_BYTE = 96;
