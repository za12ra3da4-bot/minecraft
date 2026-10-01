import { formatCompact, formatNumber } from '@warfront/shared';
import type { GameClient } from '../game/GameClient';

function Resource({ icon, label, value, rate }: { icon: string; label: string; value: number; rate: number }) {
  return (
    <div className="resource">
      <span className="icon">{icon}</span>
      <span className="k">{label}</span>
      <span className="v">{formatNumber(value)}</span>
      <span className={`d${rate < 0 ? ' neg' : ''}`}>
        {rate >= 0 ? '+' : ''}
        {formatNumber(rate)} / min
      </span>
    </div>
  );
}

/** Left panel: the player's nation at a glance. */
export function NationPanel({ game, open }: { game: GameClient; open: boolean }) {
  const p = game.privateState;
  const you = game.you;
  const state = you ? game.replica.nations.get(you) : null;
  const total = game.replica.owners.length;
  return (
    <div className={`hud panel left-panel${open ? '' : ' desktop-only'}`}>
      <div className="panel-title">Treasury &amp; War Office</div>
      {p ? (
        <div>
          <Resource icon="⚑" label="Manpower" value={p.resources.manpower} rate={p.income.manpower} />
          <Resource icon="⚒" label="Industry" value={p.resources.industry} rate={p.income.industry} />
          <Resource icon="❖" label="Supplies" value={p.resources.supplies} rate={p.income.supplies} />
        </div>
      ) : (
        <div className="hint">Observing.</div>
      )}
      {state && (
        <div className="stat-grid">
          <div className="stat">
            <div className="v">{formatCompact(state.soldiers)}</div>
            <div className="k">Soldiers</div>
          </div>
          <div className="stat">
            <div className="v">{state.armies}</div>
            <div className="k">Armies</div>
          </div>
          <div className="stat">
            <div className="v">{state.territories}</div>
            <div className="k">Territories</div>
          </div>
          <div className="stat">
            <div className="v">{Math.round((state.territories / Math.max(1, total)) * 100)}%</div>
            <div className="k">Of the map</div>
          </div>
        </div>
      )}
      {p && p.production.length > 0 && (
        <>
          <div className="panel-title">Mobilisation</div>
          {p.production.map((o) => {
            const city = game.replica.map.cities[o.cityId];
            return (
              <div key={o.id} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                  <span>
                    {formatNumber(o.soldiers)} {o.type.toLowerCase()} · {city?.name}
                  </span>
                  <span className="num">{Math.max(0, Math.ceil(o.total - o.progress))}s</span>
                </div>
                <div className="bar">
                  <div style={{ width: `${Math.min(100, (o.progress / o.total) * 100)}%` }} />
                </div>
              </div>
            );
          })}
        </>
      )}
      <div className="hint" style={{ fontSize: 12 }}>
        Click a town (★ ■) you own to raise armies. Upkeep: {formatNumber(p?.upkeep ?? 0)} supplies/min.
      </div>
    </div>
  );
}
