import { getNation, getRelation, type DiploAction, type NationId } from '@warfront/shared';
import { Flag } from '../components/Flag';
import type { GameClient } from '../game/GameClient';

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
            <div className="panel-title">Foreign office</div>
            <h2>Diplomacy</h2>
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
                  <b>{getNation(o.from).name}</b> offers {o.kind === 'PEACE' ? 'peace' : 'an alliance'}
                </span>
                <button className="btn small primary" onClick={() => act('ACCEPT_OFFER', o.from, o.id)}>
                  Accept
                </button>
                <button className="btn small" onClick={() => act('REJECT_OFFER', o.from, o.id)}>
                  Reject
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
                  {state.eliminated ? 'Eliminated' : `${state.controller === 'AI' ? 'AI' : (state.playerName ?? 'Player')} · ${state.territories} territories · ${Math.round(state.soldiers / 1000)}K soldiers`}
                </div>
              </div>
              <span className={`badge ${rel.toLowerCase()}`}>{rel}</span>
              <div className="actions">
                {!state.eliminated && you && (
                  <>
                    {rel !== 'WAR' && rel !== 'ALLIANCE' && (
                      <button className="btn small danger" onClick={() => act('DECLARE_WAR', n)}>
                        Declare war
                      </button>
                    )}
                    {rel === 'WAR' && (
                      <button className="btn small" disabled={!!pending} onClick={() => act('OFFER_PEACE', n)}>
                        {pending ? 'Offer sent' : 'Offer peace'}
                      </button>
                    )}
                    {rel === 'PEACE' && (
                      <button className="btn small" disabled={!!pending} onClick={() => act('OFFER_ALLIANCE', n)}>
                        {pending ? 'Offer sent' : 'Offer alliance'}
                      </button>
                    )}
                    {rel === 'ALLIANCE' && (
                      <button className="btn small" onClick={() => act('BREAK_ALLIANCE', n)}>
                        Break alliance
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
