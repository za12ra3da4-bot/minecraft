import { DIPLOMACY, getNation, type DiploAction, type NationId } from '@warfront/shared';
import type { GameState } from '../GameState';

export type DiploResult = { ok: true } | { ok: false; error: string };

/** Validates and applies a diplomatic action. Used by players and the AI. */
export function applyDiplomacy(state: GameState, from: NationId, action: DiploAction, target: NationId, offerId?: number): DiploResult {
  if (from === target) return { ok: false, error: 'Cannot target your own nation' };
  if (!state.isActive(from)) return { ok: false, error: 'Your nation is not active' };
  if (!state.isActive(target)) return { ok: false, error: 'That nation is not in the game' };
  const rel = state.relation(from, target);
  const me = state.nations.get(from)!;
  const fromName = getNation(from).name;
  const targetName = getNation(target).name;

  switch (action) {
    case 'DECLARE_WAR': {
      if (rel === 'WAR') return { ok: false, error: 'Already at war' };
      if (rel === 'ALLIANCE') return { ok: false, error: 'Break the alliance first' };
      const truce = me.truces.get(target) ?? 0;
      if (truce > state.time) return { ok: false, error: `Truce in effect for ${Math.ceil(truce - state.time)}s` };
      state.setRelation(from, target, 'WAR');
      removeOffersBetween(state, from, target);
      state.emit('WAR_DECLARED', `⚔ ${fromName} declared war on ${targetName}!`, [from, target], { major: true });
      return { ok: true };
    }
    case 'OFFER_PEACE':
    case 'OFFER_ALLIANCE': {
      const kind = action === 'OFFER_PEACE' ? 'PEACE' : 'ALLIANCE';
      if (kind === 'PEACE' && rel !== 'WAR') return { ok: false, error: 'You are not at war' };
      if (kind === 'ALLIANCE' && rel !== 'PEACE') return { ok: false, error: 'Alliances require peace first' };
      if (state.offers.some((o) => o.from === from && o.to === target && o.kind === kind)) return { ok: false, error: 'Offer already pending' };
      if (state.offers.filter((o) => o.from === from).length >= DIPLOMACY.MAX_OFFERS_PER_NATION) return { ok: false, error: 'Too many pending offers' };
      state.offers.push({ id: state.offerId(), from, to: target, kind, expires: state.time + DIPLOMACY.OFFER_TTL_SECONDS });
      state.diplomacyVersion++;
      state.emit('OFFER', `${fromName} offers ${kind === 'PEACE' ? 'peace' : 'an alliance'} to ${targetName}`, [from, target]);
      return { ok: true };
    }
    case 'ACCEPT_OFFER':
    case 'REJECT_OFFER': {
      const offer = state.offers.find((o) => o.id === offerId && o.to === from && o.from === target);
      if (!offer) return { ok: false, error: 'Offer not found or expired' };
      state.offers = state.offers.filter((o) => o !== offer);
      state.diplomacyVersion++;
      if (action === 'REJECT_OFFER') {
        state.emit('OFFER_REJECTED', `${fromName} rejected the ${offer.kind === 'PEACE' ? 'peace' : 'alliance'} offer from ${targetName}`, [from, target]);
        return { ok: true };
      }
      if (offer.kind === 'PEACE') {
        if (state.relation(from, target) !== 'WAR') return { ok: false, error: 'No longer at war' };
        makePeace(state, from, target);
      } else {
        if (state.relation(from, target) !== 'PEACE') return { ok: false, error: 'Alliance no longer possible' };
        state.setRelation(from, target, 'ALLIANCE');
        state.emit('ALLIANCE_FORMED', `🤝 ${fromName} and ${targetName} formed an alliance`, [from, target], { major: true });
      }
      return { ok: true };
    }
    case 'BREAK_ALLIANCE': {
      if (rel !== 'ALLIANCE') return { ok: false, error: 'Not allied' };
      state.setRelation(from, target, 'PEACE');
      state.emit('ALLIANCE_BROKEN', `${fromName} broke the alliance with ${targetName}`, [from, target], { major: true });
      return { ok: true };
    }
  }
  return { ok: false, error: 'Unknown action' };
}

export function makePeace(state: GameState, a: NationId, b: NationId): void {
  state.setRelation(a, b, 'PEACE');
  const until = state.time + DIPLOMACY.TRUCE_SECONDS;
  state.nations.get(a)?.truces.set(b, until);
  state.nations.get(b)?.truces.set(a, until);
  removeOffersBetween(state, a, b);
  for (const [tid, cap] of state.captures) {
    const owner = state.owners[tid];
    if ((cap.nation === a && owner === b) || (cap.nation === b && owner === a)) state.captures.delete(tid);
  }
  for (const u of state.units.values()) {
    if (u.targetUnit === null) continue;
    const t = state.units.get(u.targetUnit);
    if (t && ((u.nation === a && t.nation === b) || (u.nation === b && t.nation === a))) {
      u.clearOrders();
      if (!u.inBattle) u.status = 'IDLE';
    }
  }
  state.emit('PEACE_SIGNED', `🕊 ${getNation(a).name} and ${getNation(b).name} signed a peace treaty`, [a, b], { major: true });
}

function removeOffersBetween(state: GameState, a: NationId, b: NationId): void {
  const before = state.offers.length;
  state.offers = state.offers.filter((o) => !((o.from === a && o.to === b) || (o.from === b && o.to === a)));
  if (state.offers.length !== before) state.diplomacyVersion++;
}

export function expireOffers(state: GameState): void {
  const before = state.offers.length;
  state.offers = state.offers.filter((o) => o.expires > state.time && state.isActive(o.from) && state.isActive(o.to));
  if (state.offers.length !== before) state.diplomacyVersion++;
}
