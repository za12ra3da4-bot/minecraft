import { UNIT } from '@warfront/shared';
import type { GameClient } from '../game/GameClient';

/** Bottom command panel: orders for the current selection. */
export function CommandBar({ game, onFocus }: { game: GameClient; onFocus: () => void }) {
  const units = game.selectedUnits();
  if (!units.length) {
    return (
      <div className="hud panel command-bar">
        <span className="hint-text">Click your army (▼) to command it · Click a town to raise armies · Wheel to zoom · Drag to pan</span>
      </div>
    );
  }
  const ids = units.map((u) => u.id);
  const fighting = units.some((u) => u.battleId !== null);
  const canMerge = units.length > 1 && !fighting;
  const largest = units.reduce((a, b) => (b.soldiers > a.soldiers ? b : a));
  const mergeable = canMerge && units.every((u) => Math.hypot(u.x - largest.x, u.y - largest.y) <= UNIT.MERGE_RADIUS);
  return (
    <div className="hud panel command-bar">
      <span className="hint-text">{game.joinMode ? 'Tap the army to join…' : fighting ? 'In battle — a move order retreats' : 'Click map: MOVE · Click enemy: ATTACK'}</span>
      <button className="btn" onClick={() => game.toast('Click on the map to move. Click an enemy army to attack.', 'info')}>
        Move
      </button>
      <button className="btn danger" onClick={() => game.toast('Click an enemy army to attack it.', 'info')}>
        Attack
      </button>
      <button className={`btn${game.joinMode ? ' active' : ''}`} onClick={() => ((game.joinMode = !game.joinMode), game.notify())} title="Join another army (J)">
        Join
      </button>
      <button
        className="btn"
        disabled={!canMerge}
        title={mergeable ? 'Merge selected armies (M)' : 'Armies must stand together to merge'}
        onClick={() => void game.command({ type: 'MERGE_UNIT', unitIds: ids })}
        data-testid="merge"
      >
        Merge
      </button>
      <button className="btn" onClick={() => void game.command({ type: 'HALT', unitIds: ids })} title="Halt (H)">
        Halt
      </button>
      <button className="btn ghost" onClick={onFocus} title="Focus (F)">
        ◎
      </button>
    </div>
  );
}
