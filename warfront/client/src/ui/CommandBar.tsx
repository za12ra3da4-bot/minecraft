import { UNIT, formatNumber } from '@warfront/shared';
import type { GameClient } from '../game/GameClient';

interface Props {
  game: GameClient;
  onFocus: () => void;
  onSelectAll: () => void;
  onCapital: () => void;
  onHelp: () => void;
}

function Big({ icon, label, onClick, disabled, tone, title, testId }: { icon: string; label: string; onClick: () => void; disabled?: boolean; tone?: 'primary' | 'danger'; title?: string; testId?: string }) {
  return (
    <button className={`btn cmd${tone ? ` ${tone}` : ''}`} onClick={onClick} disabled={disabled} title={title} data-testid={testId}>
      <span className="cmd-icon">{icon}</span>
      <span className="cmd-label">{label}</span>
    </button>
  );
}

/** Bottom command panel: big, self-explanatory buttons for the current selection. */
export function CommandBar({ game, onFocus, onSelectAll, onCapital, onHelp }: Props) {
  const units = game.selectedUnits();
  const rangeToggle = (
    <span className="mobile-only">
      <Big icon="▢" label={game.boxMode ? '범위 선택 ON' : '범위 선택'} tone={game.boxMode ? 'primary' : undefined} onClick={() => ((game.boxMode = !game.boxMode), game.notify())} />
    </span>
  );

  if (!units.length) {
    return (
      <div className="hud panel command-bar">
        <div className="cmd-hint">
          <b>드래그</b>로 부대 여러 개 선택 · <b>클릭</b>으로 부대 선택 · <b>오른쪽 드래그</b>/WASD로 지도 이동
        </div>
        <div className="cmd-row">
          <Big icon="👥" label="내 부대 전체 선택" onClick={onSelectAll} tone="primary" testId="select-all" />
          <Big icon="⚑" label="군대 만들기" onClick={onCapital} />
          <Big icon="❓" label="도움말" onClick={onHelp} />
          {rangeToggle}
        </div>
      </div>
    );
  }

  const ids = units.map((u) => u.id);
  const total = units.reduce((s, u) => s + u.soldiers, 0);
  const fighting = units.some((u) => u.battleId !== null);
  const largest = units.reduce((a, b) => (b.soldiers > a.soldiers ? b : a));
  const single = units.length === 1 ? units[0] : null;

  const merge = (): void => {
    const together = units.every((u) => Math.hypot(u.x - largest.x, u.y - largest.y) <= UNIT.MERGE_RADIUS);
    if (together) void game.command({ type: 'MERGE_UNIT', unitIds: ids });
    else {
      void game.command({ type: 'JOIN_UNIT', unitIds: ids.filter((id) => id !== largest.id), targetUnitId: largest.id });
      game.toast('부대들이 가장 큰 부대로 모여서 합쳐집니다', 'info');
    }
  };

  return (
    <div className="hud panel command-bar">
      <div className="cmd-hint">
        <b>
          부대 {units.length}개 · {formatNumber(total)}명
        </b>{' '}
        — {fighting ? '전투 중! 지도를 클릭하면 후퇴합니다' : '지도를 클릭하면 이동, 적을 클릭하면 공격'}
      </div>
      <div className="cmd-row">
        <Big icon="🤝" label="합치기" onClick={merge} disabled={units.length < 2 || fighting} title="선택한 부대를 하나로 합칩니다" testId="merge" />
        <Big
          icon="✂"
          label="반으로 나누기"
          onClick={() => single && void game.command({ type: 'SPLIT_UNIT', unitId: single.id, soldiers: Math.floor(single.soldiers / 2) })}
          disabled={!single || fighting || (single?.soldiers ?? 0) < UNIT.MIN_SPLIT * 2}
          title="부대 하나를 선택하면 반으로 나눕니다"
          testId="split-half"
        />
        <Big icon="✋" label="멈추기" onClick={() => void game.command({ type: 'HALT', unitIds: ids })} />
        <Big icon="🎯" label="찾아가기" onClick={onFocus} />
        <Big icon="✖" label="선택 해제" onClick={() => game.select({ kind: 'none' })} />
        {rangeToggle}
      </div>
    </div>
  );
}
