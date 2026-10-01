import type { NationId } from '@warfront/shared';
import { MinHeap } from '../util/MinHeap';
import type { MapContext } from './MapContext';
import type { TerritoryDraft } from './territoryGen';

/**
 * Assigns a "home nation" to territories by growing contiguous regions from
 * each capital. The game later turns home nations into owners for the nations
 * that are actually in play.
 */
export function assignHomeNations(
  ctx: MapContext,
  drafts: TerritoryDraft[],
  capitalTerritories: number[],
): (NationId | null)[] {
  const { def, rng } = ctx;
  const home: (NationId | null)[] = new Array(drafts.length).fill(null);
  const totalShare = def.nations.reduce((s, n) => s + n.share, 0);
  const claim = Math.round(drafts.length * def.claimedShare);
  const targets = def.nations.map((n) => Math.max(1, Math.round((claim * n.share) / totalShare)));
  const counts = def.nations.map(() => 0);
  const heaps = def.nations.map(() => new MinHeap());

  def.nations.forEach((slot, i) => {
    const cap = capitalTerritories[i];
    home[cap] = slot.nation;
    counts[i] = 1;
    for (const n of drafts[cap].neighbors) heaps[i].push(n, 0);
  });

  const capX = capitalTerritories.map((t) => drafts[t].cx);
  const capY = capitalTerritories.map((t) => drafts[t].cy);
  for (;;) {
    let pick = -1;
    let bestRatio = Infinity;
    for (let i = 0; i < def.nations.length; i++) {
      if (counts[i] >= targets[i] || heaps[i].size === 0) continue;
      const ratio = counts[i] / targets[i];
      if (ratio < bestRatio) {
        bestRatio = ratio;
        pick = i;
      }
    }
    if (pick < 0) break;
    const heap = heaps[pick];
    let claimed = -1;
    while (heap.size) {
      const t = heap.pop();
      if (home[t] === null) {
        claimed = t;
        break;
      }
    }
    if (claimed < 0) continue;
    home[claimed] = def.nations[pick].nation;
    counts[pick]++;
    for (const n of drafts[claimed].neighbors) {
      if (home[n] !== null) continue;
      const d = Math.hypot(drafts[n].cx - capX[pick], drafts[n].cy - capY[pick]);
      heap.push(n, d * (1 + rng.next() * 0.35));
    }
  }

  // Fully claimed maps: hand leftovers to a neighbouring nation.
  if (def.claimedShare >= 0.999) {
    let changed = true;
    while (changed) {
      changed = false;
      for (const d of drafts) {
        if (home[d.id] !== null) continue;
        const n = d.neighbors.find((x) => home[x] !== null);
        if (n !== undefined) {
          home[d.id] = home[n];
          changed = true;
        }
      }
    }
  }
  return home;
}
