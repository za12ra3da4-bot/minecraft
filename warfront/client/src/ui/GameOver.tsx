import { formatNumber, getNation } from '@warfront/shared';
import { Flag } from '../components/Flag';
import type { GameClient } from '../game/GameClient';

export function GameOver({ game, onLeave, onClose }: { game: GameClient; onLeave: () => void; onClose: () => void }) {
  const info = game.over!;
  const won = game.you !== null && info.winners.includes(game.you);
  return (
    <div className="overlay">
      <div className="panel">
        <div className="panel-title">{won ? 'Victory' : 'The war is over'}</div>
        <h2>{won ? 'Your nation is victorious' : info.winners.length ? `${info.winners.map((w) => getNation(w).name).join(' & ')} prevail` : 'No victor'}</h2>
        <div className="hint" style={{ fontSize: 15 }}>
          {info.reason}
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 15 }}>
          <thead>
            <tr className="label">
              <th style={{ textAlign: 'left' }}>Nation</th>
              <th>Territories</th>
              <th>Soldiers</th>
              <th>Inflicted</th>
              <th>Lost</th>
            </tr>
          </thead>
          <tbody>
            {info.stats.map((s) => (
              <tr key={s.nation} style={{ borderTop: '1px solid var(--line-soft)' }}>
                <td style={{ padding: '6px 0' }}>
                  <Flag nation={s.nation} height={14} /> {getNation(s.nation).name}
                </td>
                <td style={{ textAlign: 'center' }}>{s.territories}</td>
                <td style={{ textAlign: 'center' }}>{formatNumber(s.soldiers)}</td>
                <td style={{ textAlign: 'center' }}>{formatNumber(s.kills)}</td>
                <td style={{ textAlign: 'center' }}>{formatNumber(s.losses)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="dialog-actions">
          <button className="btn ghost" onClick={onClose}>
            View map
          </button>
          <button className="btn primary" onClick={onLeave}>
            Return to menu
          </button>
        </div>
      </div>
    </div>
  );
}
