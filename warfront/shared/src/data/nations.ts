import type { NationDef, NationId } from '../types/nation';

/**
 * Nation catalogue. Flags are stylised UI icons painted from these layer
 * descriptions – add a nation here and reference it from a map in maps.ts.
 */
export const NATIONS: NationDef[] = [
  {
    id: 'britain',
    name: 'Britain',
    adjective: 'British',
    code: 'GBR',
    color: '#c8463f',
    nameStyle: 'english',
    personality: { aggression: 0.55, caution: 0.55, diplomacy: 0.6 },
    flag: {
      field: '#1f2f6b',
      layers: [
        { kind: 'saltire', color: '#f4f1ea', width: 0.2 },
        { kind: 'saltire', color: '#c8302f', width: 0.07 },
        { kind: 'cross', color: '#f4f1ea', width: 0.32 },
        { kind: 'cross', color: '#c8302f', width: 0.19 },
      ],
    },
  },
  {
    id: 'france',
    name: 'France',
    adjective: 'French',
    code: 'FRA',
    color: '#3a6fd0',
    nameStyle: 'french',
    personality: { aggression: 0.8, caution: 0.35, diplomacy: 0.4 },
    flag: { field: '#f4f1ea', layers: [{ kind: 'stripes-v', colors: ['#1f3f9a', '#f4f1ea', '#c8302f'] }] },
  },
  {
    id: 'prussia',
    name: 'Prussia',
    adjective: 'Prussian',
    code: 'PRU',
    color: '#535a6b',
    nameStyle: 'german',
    personality: { aggression: 0.7, caution: 0.45, diplomacy: 0.5 },
    flag: {
      field: '#f2f0ea',
      layers: [
        { kind: 'stripes-h', colors: ['#1b1b1b', '#f2f0ea', '#1b1b1b'], weights: [1, 4, 1] },
        { kind: 'eagle', color: '#1b1b1b', x: 0.5, y: 0.5, size: 0.46 },
      ],
    },
  },
  {
    id: 'austria',
    name: 'Austria',
    adjective: 'Austrian',
    code: 'AUT',
    color: '#d6a92c',
    nameStyle: 'german',
    personality: { aggression: 0.45, caution: 0.6, diplomacy: 0.65 },
    flag: { field: '#f4f1ea', layers: [{ kind: 'stripes-h', colors: ['#c8302f', '#f4f1ea', '#c8302f'] }] },
  },
  {
    id: 'russia',
    name: 'Russia',
    adjective: 'Russian',
    code: 'RUS',
    color: '#3e8f55',
    nameStyle: 'slavic',
    personality: { aggression: 0.6, caution: 0.5, diplomacy: 0.45 },
    flag: { field: '#f4f1ea', layers: [{ kind: 'stripes-h', colors: ['#f4f1ea', '#2a4fa0', '#c8302f'] }] },
  },
  {
    id: 'spain',
    name: 'Spain',
    adjective: 'Spanish',
    code: 'ESP',
    color: '#9a52b8',
    nameStyle: 'spanish',
    personality: { aggression: 0.5, caution: 0.55, diplomacy: 0.5 },
    flag: {
      field: '#f1c232',
      layers: [{ kind: 'stripes-h', colors: ['#c8302f', '#f1c232', '#c8302f'], weights: [1, 2, 1] }],
    },
  },
  {
    id: 'netherlands',
    name: 'Netherlands',
    adjective: 'Dutch',
    code: 'NED',
    color: '#e8892d',
    nameStyle: 'dutch',
    personality: { aggression: 0.35, caution: 0.65, diplomacy: 0.75 },
    flag: { field: '#f4f1ea', layers: [{ kind: 'stripes-h', colors: ['#b5262c', '#f4f1ea', '#233f8a'] }] },
  },
  {
    id: 'sweden',
    name: 'Sweden',
    adjective: 'Swedish',
    code: 'SWE',
    color: '#3ea6d8',
    nameStyle: 'nordic',
    personality: { aggression: 0.45, caution: 0.55, diplomacy: 0.6 },
    flag: { field: '#1f5fa8', layers: [{ kind: 'cross', color: '#f1c232', width: 0.2, offsetX: -0.14 }] },
  },
  {
    id: 'ottoman',
    name: 'Ottoman Empire',
    adjective: 'Ottoman',
    code: 'OTT',
    color: '#25988a',
    nameStyle: 'turkish',
    personality: { aggression: 0.6, caution: 0.5, diplomacy: 0.4 },
    flag: {
      field: '#c42b2b',
      layers: [
        { kind: 'crescent', color: '#f4f1ea', x: 0.42, y: 0.5, r: 0.27 },
        { kind: 'star', color: '#f4f1ea', x: 0.63, y: 0.5, r: 0.11 },
      ],
    },
  },
  {
    id: 'poland',
    name: 'Poland',
    adjective: 'Polish',
    code: 'POL',
    color: '#b5476f',
    nameStyle: 'polish',
    personality: { aggression: 0.5, caution: 0.5, diplomacy: 0.6 },
    flag: { field: '#f4f1ea', layers: [{ kind: 'stripes-h', colors: ['#f4f1ea', '#c8302f'] }] },
  },
];

const NATION_INDEX = new Map(NATIONS.map((n) => [n.id, n]));

export function getNation(id: NationId): NationDef {
  const n = NATION_INDEX.get(id);
  if (!n) throw new Error(`Unknown nation ${id}`);
  return n;
}

export function isNationId(id: unknown): id is NationId {
  return typeof id === 'string' && NATION_INDEX.has(id);
}

/** Colour used for land nobody owns. */
export const NEUTRAL_COLOR = '#9a8f7a';
