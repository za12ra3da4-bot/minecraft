import { DIPLOMACY, getNation, type DiploAction, type NationId } from '@warfront/shared';
import type { GameState } from '../GameState';

export type DiploResult = { ok: true } | { ok: false; error: string };

/** Validates and applies a diplomatic action. Used by players and the AI. */
export function applyDiplomacy(state: GameState, from: NationId, action: DiploAction, target: NationId, offerId?: number): DiploResult {
  if (from === target) return { ok: false, error: '자기 나라는 선택할 수 없습니다' };
  if (!state.isActive(from)) return { ok: false, error: '우리 나라가 활동 중이 아닙니다' };
  if (!state.isActive(target)) return { ok: false, error: '게임에 없는 나라입니다' };
  const rel = state.relation(from, target);
  const me = state.nations.get(from)!;
  const fromName = getNation(from).name;
  const targetName = getNation(target).name;

  switch (action) {
    case 'DECLARE_WAR': {
      if (rel === 'WAR') return { ok: false, error: '이미 전쟁 중입니다' };
      if (rel === 'ALLIANCE') return { ok: false, error: '먼저 동맹을 파기하세요' };
      const truce = me.truces.get(target) ?? 0;
      if (truce > state.time) return { ok: false, error: `휴전 중입니다 (${Math.ceil(truce - state.time)}초 남음)` };
      state.setRelation(from, target, 'WAR');
      removeOffersBetween(state, from, target);
      state.emit('WAR_DECLARED', `⚔ 선전포고! ${fromName} → ${targetName}`, [from, target], { major: true });
      return { ok: true };
    }
    case 'OFFER_PEACE':
    case 'OFFER_ALLIANCE': {
      const kind = action === 'OFFER_PEACE' ? 'PEACE' : 'ALLIANCE';
      if (kind === 'PEACE' && rel !== 'WAR') return { ok: false, error: '전쟁 중이 아닙니다' };
      if (kind === 'ALLIANCE' && rel !== 'PEACE') return { ok: false, error: '동맹은 평화 상태에서만 가능합니다' };
      if (state.offers.some((o) => o.from === from && o.to === target && o.kind === kind)) return { ok: false, error: '이미 제안을 보냈습니다' };
      if (state.offers.filter((o) => o.from === from).length >= DIPLOMACY.MAX_OFFERS_PER_NATION) return { ok: false, error: '보낸 제안이 너무 많습니다' };
      state.offers.push({ id: state.offerId(), from, to: target, kind, expires: state.time + DIPLOMACY.OFFER_TTL_SECONDS });
      state.diplomacyVersion++;
      // AI-to-AI haggling stays private; offers involving a player are announced.
      if (involvesPlayer(state, from, target)) state.emit('OFFER', `${kind === 'PEACE' ? '평화' : '동맹'} 제안: ${fromName} → ${targetName}`, [from, target]);
      return { ok: true };
    }
    case 'ACCEPT_OFFER':
    case 'REJECT_OFFER': {
      const offer = state.offers.find((o) => o.id === offerId && o.to === from && o.from === target);
      if (!offer) return { ok: false, error: '제안이 없거나 만료되었습니다' };
      state.offers = state.offers.filter((o) => o !== offer);
      state.diplomacyVersion++;
      if (action === 'REJECT_OFFER') {
        if (involvesPlayer(state, from, target)) state.emit('OFFER_REJECTED', `${offer.kind === 'PEACE' ? '평화' : '동맹'} 제안 거절: ${fromName} ✕ ${targetName}`, [from, target]);
        return { ok: true };
      }
      if (offer.kind === 'PEACE') {
        if (state.relation(from, target) !== 'WAR') return { ok: false, error: '더 이상 전쟁 중이 아닙니다' };
        makePeace(state, from, target);
      } else {
        if (state.relation(from, target) !== 'PEACE') return { ok: false, error: '동맹을 맺을 수 없습니다' };
        state.setRelation(from, target, 'ALLIANCE');
        state.emit('ALLIANCE_FORMED', `🤝 동맹 체결: ${fromName} · ${targetName}`, [from, target], { major: true });
      }
      return { ok: true };
    }
    case 'BREAK_ALLIANCE': {
      if (rel !== 'ALLIANCE') return { ok: false, error: '동맹이 아닙니다' };
      state.setRelation(from, target, 'PEACE');
      state.emit('ALLIANCE_BROKEN', `동맹 파기: ${fromName} ✕ ${targetName}`, [from, target], { major: true });
      return { ok: true };
    }
  }
  return { ok: false, error: '알 수 없는 명령' };
}

function involvesPlayer(state: GameState, a: NationId, b: NationId): boolean {
  return state.nations.get(a)?.controller === 'PLAYER' || state.nations.get(b)?.controller === 'PLAYER';
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
  state.emit('PEACE_SIGNED', `🕊 평화 조약: ${getNation(a).name} · ${getNation(b).name}`, [a, b], { major: true });
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
