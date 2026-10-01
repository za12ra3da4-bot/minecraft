import { getNation, getRelation, type DiploAction, type NationId } from '@warfront/shared';
import { Flag } from '../components/Flag';
import type { GameClient } from '../game/GameClient';
import { RELATION_KO } from './labels';

export function DiplomacyPanel({ game, onClose }: { game: GameClient; onClose: () => void }) {
  const r = game.replica;
  const you = game.you;
  const offers = game.privateState?.offers ?? [];
  const act = (action: DiploAction, target: NationId, offerId?: number) => void game.command({ type: 'DIPLOMACY', action, target, offerId });
  const others = r.nationIds.filter((n) => n !== you && r.nations.get(n)?.controller !== 'NONE');
  return (
    <div className="overlay" onClick={onClose}>
      <div className="panel" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <div className="panel-title">외무부</div>
            <h2>외교</h2>
          </div>
          <button className="btn small ghost" onClick={onClose}>
            ✕
          </button>
        </div>
        {you &&
          offers
            .filter((o) => o.to === you)
            .map((o) => (
              <div key={o.id} className="offer">
                <Flag nation={o.from} height={20} />
                <span style={{ flex: 1 }}>
                  <b>{getNation(o.from).name}</b>이(가) {o.kind === 'PEACE' ? '평화' : '동맹'}를 제안합니다
                </span>
                <button className="btn small primary" onClick={() => act('ACCEPT_OFFER', o.from, o.id)}>
                  수락
                </button>
                <button className="btn small" onClick={() => act('REJECT_OFFER', o.from, o.id)}>
                  거절
                </button>
              </div>
            ))}
        {others.map((n) => {
          const state = r.nations.get(n)!;
          const rel = you ? getRelation(r.diplomacy.relations, you, n) : 'PEACE';
          const pending = offers.find((o) => o.from === you && o.to === n);
          return (
            <div key={n} className="diplo-row" style={{ ['--nation' as string]: getNation(n).color, opacity: state.eliminated ? 0.45 : 1 }}>
              <Flag nation={n} height={22} />
              <div>
                <div style={{ fontSize: 17, fontWeight: 700 }}>{getNation(n).name}</div>
                <div className="hint">
                  {state.eliminated ? '멸망' : `${state.controller === 'AI' ? 'AI' : (state.playerName ?? '플레이어')} · 영토 ${state.territories} · 병력 ${Math.round(state.soldiers / 1000)}천`}
                </div>
              </div>
              <span className={`badge ${rel.toLowerCase()}`}>{RELATION_KO[rel]}</span>
              <div className="actions">
                {!state.eliminated && you && (
                  <>
                    {rel !== 'WAR' && rel !== 'ALLIANCE' && (
                      <button className="btn small danger" onClick={() => act('DECLARE_WAR', n)}>
                        ⚔ 선전포고
                      </button>
                    )}
                    {rel === 'WAR' && (
                      <button className="btn small" disabled={!!pending} onClick={() => act('OFFER_PEACE', n)}>
                        {pending ? '제안 보냄' : '🕊 평화 제안'}
                      </button>
                    )}
                    {rel === 'PEACE' && (
                      <button className="btn small" disabled={!!pending} onClick={() => act('OFFER_ALLIANCE', n)}>
                        {pending ? '제안 보냄' : '🤝 동맹 제안'}
                      </button>
                    )}
                    {rel === 'ALLIANCE' && (
                      <button className="btn small" onClick={() => act('BREAK_ALLIANCE', n)}>
                        동맹 파기
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
