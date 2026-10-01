import { getMapDef, type GameSettings } from '@warfront/shared';
import { MAP_OPTIONS, SPEED_OPTIONS, VICTORY_LABELS, VICTORY_OPTIONS } from './options';

interface Props {
  value: GameSettings;
  onChange: (next: GameSettings) => void;
  /** Hide room-only fields (singleplayer). */
  singleplayer?: boolean;
  disabled?: boolean;
}

/** Shared editor for room settings (create game, lobby, singleplayer). */
export function SettingsForm({ value, onChange, singleplayer, disabled }: Props) {
  const nations = getMapDef(value.mapId)?.nations.length ?? 2;
  const set = (patch: Partial<GameSettings>) => {
    const next = { ...value, ...patch };
    const n = getMapDef(next.mapId)?.nations.length ?? 2;
    next.maxPlayers = Math.min(next.maxPlayers, n);
    next.aiCount = Math.min(next.aiCount, n - 1);
    onChange(next);
  };
  return (
    <fieldset disabled={disabled} style={{ border: 0, padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 18 }}>
      {!singleplayer && (
        <div className="grid-2">
          <label className="field">
            <span className="label">방 이름</span>
            <input className="input" maxLength={24} value={value.roomName} onChange={(e) => set({ roomName: e.target.value })} />
          </label>
          <label className="field">
            <span className="label">최대 인원 · {value.maxPlayers}명</span>
            <input type="range" min={2} max={Math.min(10, nations)} value={value.maxPlayers} onChange={(e) => set({ maxPlayers: Number(e.target.value) })} />
          </label>
        </div>
      )}
      <div className="field">
        <span className="label">지도</span>
        <div className="map-cards">
          {MAP_OPTIONS.map((m) => (
            <button type="button" key={m.id} className={`map-card${value.mapId === m.id ? ' on' : ''}`} onClick={() => set({ mapId: m.id })}>
              <div className="name">{m.name}</div>
              <div className="meta">
                {m.nations.length}개국 · {m.geo ? '실제 유럽' : '가상 전장'}
              </div>
              <div className="about">{m.description}</div>
            </button>
          ))}
        </div>
      </div>
      <div className="grid-2">
        <div className="field">
          <span className="label">게임 속도</span>
          <div className="segmented">
            {SPEED_OPTIONS.map((s) => (
              <button type="button" key={s} className={value.speed === s ? 'on' : ''} onClick={() => set({ speed: s })}>
                {s}배
              </button>
            ))}
          </div>
        </div>
        <label className="field">
          <span className="label">AI 나라 수 · {value.aiCount}</span>
          <input type="range" min={0} max={nations - 1} value={value.aiCount} onChange={(e) => set({ aiCount: Number(e.target.value) })} />
        </label>
      </div>
      <div className="field">
        <span className="label">승리 조건 — {VICTORY_LABELS[value.victory].about}</span>
        <div className="segmented">
          {VICTORY_OPTIONS.map((v) => (
            <button type="button" key={v} className={value.victory === v ? 'on' : ''} onClick={() => set({ victory: v })}>
              {VICTORY_LABELS[v].label}
            </button>
          ))}
        </div>
      </div>
      <label className="toggle">
        <input type="checkbox" checked={value.startAtWar} onChange={(e) => set({ startAtWar: e.target.checked })} />
        <span className="track" />
        <span>역사적 전쟁 상태로 시작 (끄면 모두 평화 상태에서 시작)</span>
      </label>
    </fieldset>
  );
}
