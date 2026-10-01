import { formatNumber, getNation } from '@warfront/shared';
import { Flag } from '../components/Flag';
import type { GameClient } from '../game/GameClient';

export function GameOver({ game, onLeave, onClose }: { game: GameClient; onLeave: () => void; onClose: () => void }) {
  const info = game.over!;
  const won = game.you !== null && info.winners.includes(game.you);
  return (
    <div className="overlay">
      <div className="panel">
        <div className="panel-title">{won ? '승리' : '전쟁 종료'}</div>
        <h2>{won ? '우리 나라의 승리입니다!' : info.winners.length ? `${info.winners.map((w) => getNation(w).name).join(' · ')} 승리` : '승자 없음'}</h2>
        <div className="hint" style={{ fontSize: 15 }}>
          {info.reason}
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 15 }}>
          <thead>
            <tr className="label">
              <th style={{ textAlign: 'left' }}>나라</th>
              <th>영토</th>
              <th>병력</th>
              <th>적 피해</th>
              <th>아군 손실</th>
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
            지도 보기
          </button>
          <button className="btn primary" onClick={onLeave}>
            메뉴로
          </button>
        </div>
      </div>
    </div>
  );
}
