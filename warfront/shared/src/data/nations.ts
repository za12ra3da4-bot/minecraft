import type { NationDef, NationId } from '../types/nation';

/**
 * Powers of Napoleonic Europe (June 1812). Flags are stylised UI icons.
 */
export const NATIONS: NationDef[] = [
  {
    id: 'france',
    name: 'French Empire',
    adjective: 'French',
    code: 'FRA',
    color: '#3a6fd0',
    nameStyle: 'french',
    personality: { aggression: 0.85, caution: 0.35, diplomacy: 0.4 },
    military: { fieldArmy: "Grande Armée", generals: ['Napoleon', 'Davout', 'Ney', 'Murat', 'Masséna', 'Soult', 'Lannes', 'Berthier'] },
    flag: { field: '#1f3f9a', layers: [{ kind: 'stripes-v', colors: ['#1f3f9a', '#f4f1ea', '#c8302f'] }] },
  },
  {
    id: 'britain',
    name: 'Britain',
    adjective: 'British',
    code: 'GBR',
    color: '#c8463f',
    nameStyle: 'english',
    personality: { aggression: 0.5, caution: 0.55, diplomacy: 0.6 },
    military: { fieldArmy: "Army of the Peninsula", generals: ['Wellington', 'Hill', 'Picton', 'Uxbridge', 'Moore', 'Graham'] },
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
    id: 'prussia',
    name: 'Prussia',
    adjective: 'Prussian',
    code: 'PRU',
    color: '#535a6b',
    nameStyle: 'german',
    personality: { aggression: 0.6, caution: 0.5, diplomacy: 0.5 },
    military: { fieldArmy: "Army of Silesia", generals: ['Blücher', 'Gneisenau', 'Yorck', 'Bülow', 'Kleist', 'Scharnhorst'] },
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
    personality: { aggression: 0.45, caution: 0.6, diplomacy: 0.6 },
    military: { fieldArmy: "Hauptarmee", generals: ['Schwarzenberg', 'Archduke Charles', 'Radetzky', 'Bellegarde', 'Hiller'] },
    flag: { field: '#1b1b1b', layers: [{ kind: 'stripes-h', colors: ['#1b1b1b', '#f1c232'] }] },
  },
  {
    id: 'russia',
    name: 'Russian Empire',
    adjective: 'Russian',
    code: 'RUS',
    color: '#3e8f55',
    nameStyle: 'slavic',
    personality: { aggression: 0.6, caution: 0.5, diplomacy: 0.45 },
    military: { fieldArmy: "1st Western Army", generals: ['Kutuzov', 'Barclay de Tolly', 'Bagration', 'Wittgenstein', 'Tormasov', 'Platov'] },
    flag: { field: '#f4f1ea', layers: [{ kind: 'stripes-h', colors: ['#f4f1ea', '#2a4fa0', '#c8302f'] }] },
  },
  {
    id: 'spain',
    name: 'Spain',
    adjective: 'Spanish',
    code: 'ESP',
    color: '#e0862d',
    nameStyle: 'spanish',
    personality: { aggression: 0.45, caution: 0.6, diplomacy: 0.5 },
    military: { fieldArmy: "Army of Andalusia", generals: ['Castaños', 'Palafox', 'Blake', 'Cuesta', 'La Romana'] },
    flag: { field: '#c8302f', layers: [{ kind: 'stripes-h', colors: ['#c8302f', '#f1c232', '#c8302f'], weights: [1, 2, 1] }] },
  },
  {
    id: 'portugal',
    name: 'Portugal',
    adjective: 'Portuguese',
    code: 'POR',
    color: '#2f8a6e',
    nameStyle: 'spanish',
    personality: { aggression: 0.35, caution: 0.65, diplomacy: 0.6 },
    military: { fieldArmy: "Portuguese Army", generals: ['Beresford', 'Silveira', 'Trant'] },
    flag: { field: '#2a4fa0', layers: [{ kind: 'stripes-v', colors: ['#2a4fa0', '#f4f1ea'] }] },
  },
  {
    id: 'sweden',
    name: 'Sweden',
    adjective: 'Swedish',
    code: 'SWE',
    color: '#3ea6d8',
    nameStyle: 'nordic',
    personality: { aggression: 0.4, caution: 0.6, diplomacy: 0.6 },
    military: { fieldArmy: "Army of the North", generals: ['Bernadotte', 'Stedingk', 'Adlercreutz'] },
    flag: { field: '#1f5fa8', layers: [{ kind: 'cross', color: '#f1c232', width: 0.2, offsetX: -0.14 }] },
  },
  {
    id: 'denmark',
    name: 'Denmark-Norway',
    adjective: 'Danish',
    code: 'DEN',
    color: '#a83c4e',
    nameStyle: 'nordic',
    personality: { aggression: 0.35, caution: 0.6, diplomacy: 0.55 },
    military: { fieldArmy: "Danish Auxiliary Corps", generals: ['Frederick of Hesse', 'Ewald'] },
    flag: { field: '#c8302f', layers: [{ kind: 'cross', color: '#f4f1ea', width: 0.2, offsetX: -0.14 }] },
  },
  {
    id: 'ottoman',
    name: 'Ottoman Empire',
    adjective: 'Ottoman',
    code: 'OTT',
    color: '#25988a',
    nameStyle: 'turkish',
    personality: { aggression: 0.55, caution: 0.5, diplomacy: 0.4 },
    military: { fieldArmy: "Army of the Danube", generals: ['Ahmed Pasha', 'Mustafa Bayrakdar', 'Hurshid Pasha'] },
    flag: {
      field: '#c42b2b',
      layers: [
        { kind: 'crescent', color: '#f4f1ea', x: 0.42, y: 0.5, r: 0.27 },
        { kind: 'star', color: '#f4f1ea', x: 0.63, y: 0.5, r: 0.11 },
      ],
    },
  },
  {
    id: 'warsaw',
    name: 'Duchy of Warsaw',
    adjective: 'Polish',
    code: 'WAR',
    color: '#b5476f',
    nameStyle: 'polish',
    personality: { aggression: 0.6, caution: 0.45, diplomacy: 0.5 },
    military: { fieldArmy: "Polish V Corps", generals: ['Poniatowski', 'Dąbrowski', 'Zajączek'] },
    flag: { field: '#f4f1ea', layers: [{ kind: 'stripes-h', colors: ['#f4f1ea', '#c8302f'] }] },
  },
  {
    id: 'rhine',
    name: 'Confederation of the Rhine',
    adjective: 'Rhenish',
    code: 'RHN',
    color: '#7f9a3e',
    nameStyle: 'german',
    personality: { aggression: 0.45, caution: 0.55, diplomacy: 0.55 },
    military: { fieldArmy: "Bavarian Army", generals: ['Wrede', 'Jérôme', 'Reynier'] },
    flag: {
      field: '#f4f1ea',
      layers: [
        { kind: 'stripes-v', colors: ['#3a6fb0', '#f4f1ea', '#3a6fb0', '#f4f1ea', '#3a6fb0', '#f4f1ea'] },
        { kind: 'disc', color: '#c8302f', x: 0.5, y: 0.5, r: 0.18 },
      ],
    },
  },
  {
    id: 'italy',
    name: 'Kingdom of Italy',
    adjective: 'Italian',
    code: 'ITA',
    color: '#6dbb4a',
    nameStyle: 'spanish',
    personality: { aggression: 0.5, caution: 0.5, diplomacy: 0.55 },
    military: { fieldArmy: "Army of Italy", generals: ['Eugène', 'Pino', 'Fontanelli'] },
    flag: {
      field: '#c8302f',
      layers: [
        { kind: 'canton', color: '#f4f1ea', w: 0.78, h: 0.78 },
        { kind: 'canton', color: '#2d8a3e', w: 0.5, h: 0.5 },
      ],
    },
  },
  {
    id: 'naples',
    name: 'Kingdom of Naples',
    adjective: 'Neapolitan',
    code: 'NAP',
    color: '#9a52b8',
    nameStyle: 'spanish',
    personality: { aggression: 0.45, caution: 0.55, diplomacy: 0.5 },
    military: { fieldArmy: "Neapolitan Army", generals: ['Murat', 'Carascosa', 'Pignatelli'] },
    flag: { field: '#2a4fa0', layers: [{ kind: 'border', color: '#c8302f', width: 0.22 }, { kind: 'disc', color: '#f1c232', x: 0.5, y: 0.5, r: 0.16 }] },
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
