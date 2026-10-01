import type { NationDef, NationId } from '../types/nation';

/**
 * Powers of Napoleonic Europe (June 1812). Flags are stylised UI icons;
 * names are shown to players in Korean.
 */
export const NATIONS: NationDef[] = [
  {
    id: 'france',
    name: '프랑스 제국',
    adjective: '프랑스',
    code: 'FRA',
    color: '#3a6fd0',
    nameStyle: 'french',
    personality: { aggression: 0.85, caution: 0.35, diplomacy: 0.4 },
    military: { fieldArmy: '대육군', generals: ['나폴레옹', '다부', '네', '뮈라', '마세나', '술트', '란', '베르티에'] },
    flag: { field: '#1f3f9a', layers: [{ kind: 'stripes-v', colors: ['#1f3f9a', '#f4f1ea', '#c8302f'] }] },
  },
  {
    id: 'britain',
    name: '영국',
    adjective: '영국',
    code: 'GBR',
    color: '#c8463f',
    nameStyle: 'english',
    personality: { aggression: 0.5, caution: 0.55, diplomacy: 0.6 },
    military: { fieldArmy: '반도 원정군', generals: ['웰링턴', '힐', '픽턴', '억스브리지', '무어', '그레이엄'] },
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
    name: '프로이센',
    adjective: '프로이센',
    code: 'PRU',
    color: '#535a6b',
    nameStyle: 'german',
    personality: { aggression: 0.6, caution: 0.5, diplomacy: 0.5 },
    military: { fieldArmy: '슐레지엔군', generals: ['블뤼허', '그나이제나우', '요르크', '뷜로', '클라이스트', '샤른호르스트'] },
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
    name: '오스트리아',
    adjective: '오스트리아',
    code: 'AUT',
    color: '#d6a92c',
    nameStyle: 'german',
    personality: { aggression: 0.45, caution: 0.6, diplomacy: 0.6 },
    military: { fieldArmy: '주력군', generals: ['슈바르첸베르크', '카를 대공', '라데츠키', '벨가르드', '힐러'] },
    flag: { field: '#1b1b1b', layers: [{ kind: 'stripes-h', colors: ['#1b1b1b', '#f1c232'] }] },
  },
  {
    id: 'russia',
    name: '러시아 제국',
    adjective: '러시아',
    code: 'RUS',
    color: '#3e8f55',
    nameStyle: 'slavic',
    personality: { aggression: 0.6, caution: 0.5, diplomacy: 0.45 },
    military: { fieldArmy: '제1서부군', generals: ['쿠투조프', '바르클라이 드 톨리', '바그라티온', '비트겐슈타인', '토르마소프', '플라토프'] },
    flag: { field: '#f4f1ea', layers: [{ kind: 'stripes-h', colors: ['#f4f1ea', '#2a4fa0', '#c8302f'] }] },
  },
  {
    id: 'spain',
    name: '스페인',
    adjective: '스페인',
    code: 'ESP',
    color: '#e0862d',
    nameStyle: 'spanish',
    personality: { aggression: 0.45, caution: 0.6, diplomacy: 0.5 },
    military: { fieldArmy: '안달루시아군', generals: ['카스타뇨스', '팔라폭스', '블레이크', '쿠에스타', '라 로마나'] },
    flag: { field: '#c8302f', layers: [{ kind: 'stripes-h', colors: ['#c8302f', '#f1c232', '#c8302f'], weights: [1, 2, 1] }] },
  },
  {
    id: 'portugal',
    name: '포르투갈',
    adjective: '포르투갈',
    code: 'POR',
    color: '#2f8a6e',
    nameStyle: 'spanish',
    personality: { aggression: 0.35, caution: 0.65, diplomacy: 0.6 },
    military: { fieldArmy: '포르투갈군', generals: ['베레스퍼드', '실베이라', '트랜트'] },
    flag: { field: '#2a4fa0', layers: [{ kind: 'stripes-v', colors: ['#2a4fa0', '#f4f1ea'] }] },
  },
  {
    id: 'sweden',
    name: '스웨덴',
    adjective: '스웨덴',
    code: 'SWE',
    color: '#3ea6d8',
    nameStyle: 'nordic',
    personality: { aggression: 0.4, caution: 0.6, diplomacy: 0.6 },
    military: { fieldArmy: '북방군', generals: ['베르나도트', '스테딩크', '아들레르크로이츠'] },
    flag: { field: '#1f5fa8', layers: [{ kind: 'cross', color: '#f1c232', width: 0.2, offsetX: -0.14 }] },
  },
  {
    id: 'denmark',
    name: '덴마크-노르웨이',
    adjective: '덴마크',
    code: 'DEN',
    color: '#a83c4e',
    nameStyle: 'nordic',
    personality: { aggression: 0.35, caution: 0.6, diplomacy: 0.55 },
    military: { fieldArmy: '덴마크 원정군', generals: ['헤센 공 프레데리크', '에발트'] },
    flag: { field: '#c8302f', layers: [{ kind: 'cross', color: '#f4f1ea', width: 0.2, offsetX: -0.14 }] },
  },
  {
    id: 'ottoman',
    name: '오스만 제국',
    adjective: '오스만',
    code: 'OTT',
    color: '#25988a',
    nameStyle: 'turkish',
    personality: { aggression: 0.55, caution: 0.5, diplomacy: 0.4 },
    military: { fieldArmy: '도나우군', generals: ['아흐메트 파샤', '무스타파 바이락타르', '후르시드 파샤'] },
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
    name: '바르샤바 공국',
    adjective: '폴란드',
    code: 'WAR',
    color: '#b5476f',
    nameStyle: 'polish',
    personality: { aggression: 0.6, caution: 0.45, diplomacy: 0.5 },
    military: { fieldArmy: '폴란드 제5군단', generals: ['포니아토프스키', '동브로프스키', '자욘체크'] },
    flag: { field: '#f4f1ea', layers: [{ kind: 'stripes-h', colors: ['#f4f1ea', '#c8302f'] }] },
  },
  {
    id: 'rhine',
    name: '라인 동맹',
    adjective: '라인',
    code: 'RHN',
    color: '#7f9a3e',
    nameStyle: 'german',
    personality: { aggression: 0.45, caution: 0.55, diplomacy: 0.55 },
    military: { fieldArmy: '바이에른군', generals: ['브레데', '제롬', '레니에'] },
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
    name: '이탈리아 왕국',
    adjective: '이탈리아',
    code: 'ITA',
    color: '#6dbb4a',
    nameStyle: 'spanish',
    personality: { aggression: 0.5, caution: 0.5, diplomacy: 0.55 },
    military: { fieldArmy: '이탈리아군', generals: ['외젠', '피노', '폰타넬리'] },
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
    name: '나폴리 왕국',
    adjective: '나폴리',
    code: 'NAP',
    color: '#9a52b8',
    nameStyle: 'spanish',
    personality: { aggression: 0.45, caution: 0.55, diplomacy: 0.5 },
    military: { fieldArmy: '나폴리군', generals: ['뮈라', '카라스코사', '피냐텔리'] },
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
