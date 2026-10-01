import type { NationId, UnitNet } from '@warfront/shared';
import type { Camera } from './Camera';
import type { RenderUnit } from './GameClient';

export interface UnitEntry {
  unit: UnitNet;
  r: RenderUnit;
}

/** A drawable map marker: one army or a cluster of nearby armies of one nation. */
export interface MapItem {
  nation: NationId;
  members: UnitEntry[];
  soldiers: number;
  /** Screen position (CSS px). */
  sx: number;
  sy: number;
  inBattle: boolean;
}

/** Cluster radius in screen pixels for each zoom level. */
const RADIUS: Record<number, number> = { 1: 46, 2: 34, 3: 20, 4: 0, 5: 0 };

/**
 * Greedy screen-space clustering: the largest army of a nation absorbs its
 * neighbours within the radius. Selected armies are never hidden in clusters.
 */
export function clusterUnits(entries: UnitEntry[], camera: Camera, selected: Set<number>): MapItem[] {
  const radius = RADIUS[camera.level];
  const items: MapItem[] = [];
  const pos = entries.map((e) => [camera.worldToScreenX(e.r.x), camera.worldToScreenY(e.r.y)] as const);

  if (radius <= 0) {
    entries.forEach((e, i) => items.push(single(e, pos[i][0], pos[i][1])));
    return items;
  }

  const order = entries.map((_, i) => i).sort((a, b) => entries[b].unit.soldiers - entries[a].unit.soldiers);
  const cell = radius;
  const grid = new Map<number, number[]>();
  const key = (x: number, y: number): number => (Math.floor(x / cell) + 2048) * 4096 + Math.floor(y / cell) + 2048;
  entries.forEach((_, i) => {
    const k = key(pos[i][0], pos[i][1]);
    let list = grid.get(k);
    if (!list) grid.set(k, (list = []));
    list.push(i);
  });
  const taken = new Uint8Array(entries.length);
  const r2 = radius * radius;
  for (const i of order) {
    if (taken[i]) continue;
    taken[i] = 1;
    const e = entries[i];
    if (selected.has(e.unit.id)) {
      items.push(single(e, pos[i][0], pos[i][1]));
      continue;
    }
    const members = [e];
    const [x, y] = pos[i];
    const gx = Math.floor(x / cell);
    const gy = Math.floor(y / cell);
    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        const list = grid.get((gx + dx + 2048) * 4096 + gy + dy + 2048);
        if (!list) continue;
        for (const j of list) {
          if (taken[j]) continue;
          const o = entries[j];
          if (o.unit.nation !== e.unit.nation || selected.has(o.unit.id)) continue;
          const ddx = pos[j][0] - x;
          const ddy = pos[j][1] - y;
          if (ddx * ddx + ddy * ddy > r2) continue;
          taken[j] = 1;
          members.push(o);
        }
      }
    }
    if (members.length === 1) {
      items.push(single(e, x, y));
      continue;
    }
    let sx = 0;
    let sy = 0;
    let soldiers = 0;
    let inBattle = false;
    for (const m of members) {
      const w = Math.max(1, m.unit.soldiers);
      sx += camera.worldToScreenX(m.r.x) * w;
      sy += camera.worldToScreenY(m.r.y) * w;
      soldiers += m.unit.soldiers;
      inBattle ||= m.unit.battleId !== null;
    }
    const total = members.reduce((s, m) => s + Math.max(1, m.unit.soldiers), 0);
    items.push({ nation: e.unit.nation, members, soldiers, sx: sx / total, sy: sy / total, inBattle });
  }
  return items;
}

function single(e: UnitEntry, sx: number, sy: number): MapItem {
  return { nation: e.unit.nation, members: [e], soldiers: e.unit.soldiers, sx, sy, inBattle: e.unit.battleId !== null };
}
