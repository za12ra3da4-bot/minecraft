import type { CityType } from '../types/map';

export interface CityTypeStats {
  label: string;
  canProduce: boolean;
  defense: number;
  /** Multiplier for territory population and industry. */
  population: number;
  industry: number;
  /** Capture takes longer for important cities. */
  captureFactor: number;
}

export const CITY_TYPE_STATS: Record<CityType, CityTypeStats> = {
  CAPITAL: { label: '수도', canProduce: true, defense: 1.35, population: 4.5, industry: 3.2, captureFactor: 0.45 },
  CITY: { label: '도시', canProduce: true, defense: 1.2, population: 2.4, industry: 1.6, captureFactor: 0.7 },
  PORT: { label: '항구', canProduce: true, defense: 1.15, population: 2.0, industry: 1.4, captureFactor: 0.75 },
  INDUSTRIAL_CITY: { label: '공업 도시', canProduce: true, defense: 1.15, population: 2.0, industry: 3.0, captureFactor: 0.75 },
  VILLAGE: { label: '마을', canProduce: false, defense: 1.05, population: 1.0, industry: 1.0, captureFactor: 1 },
};
