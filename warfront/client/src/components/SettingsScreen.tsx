import { settings, type ClientSettings } from '../data/settings';
import { app } from '../game/AppState';
import { useStore } from '../game/store';
import { MenuShell } from './MenuShell';

const TOGGLES: [keyof ClientSettings, string][] = [
  ['showPaths', '내 부대의 이동 경로 표시'],
  ['showCityNames', '도시 이름 표시'],
  ['battleEffects', '전투 연기와 섬광 효과'],
];

export function SettingsScreen() {
  useStore(settings);
  const v = settings.value;
  return (
    <MenuShell>
      <div className="dialog-wrap">
        <div className="panel dialog" style={{ width: 'min(560px, 100%)' }}>
          <div>
            <div className="panel-title">환경 설정</div>
            <h2>설정</h2>
          </div>
          <label className="field">
            <span className="label">사령관 이름</span>
            <input className="input" maxLength={16} value={v.playerName} onChange={(e) => settings.update({ playerName: e.target.value })} />
          </label>
          {TOGGLES.map(([key, label]) => (
            <label className="toggle" key={key}>
              <input type="checkbox" checked={Boolean(v[key])} onChange={(e) => settings.update({ [key]: e.target.checked })} />
              <span className="track" />
              <span>{label}</span>
            </label>
          ))}
          <label className="field">
            <span className="label">키보드 지도 이동 속도 · {v.panSpeed.toFixed(1)}배</span>
            <input type="range" min={0.5} max={2.5} step={0.1} value={v.panSpeed} onChange={(e) => settings.update({ panSpeed: Number(e.target.value) })} />
          </label>
          <div className="dialog-actions">
            <button className="btn ghost" onClick={() => app.go('menu')}>
              ← 뒤로
            </button>
          </div>
        </div>
      </div>
    </MenuShell>
  );
}
