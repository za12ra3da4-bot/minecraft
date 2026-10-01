import { settings, type ClientSettings } from '../data/settings';
import { app } from '../game/AppState';
import { useStore } from '../game/store';
import { MenuShell } from './MenuShell';

const TOGGLES: [keyof ClientSettings, string][] = [
  ['showPaths', 'Show movement paths of my armies'],
  ['showCityNames', 'Show town names'],
  ['battleEffects', 'Battle smoke and flashes'],
];

export function SettingsScreen() {
  useStore(settings);
  const v = settings.value;
  return (
    <MenuShell>
      <div className="dialog-wrap">
        <div className="panel dialog" style={{ width: 'min(560px, 100%)' }}>
          <div>
            <div className="panel-title">Preferences</div>
            <h2>Settings</h2>
          </div>
          <label className="field">
            <span className="label">Commander name</span>
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
            <span className="label">Keyboard pan speed · {v.panSpeed.toFixed(1)}x</span>
            <input type="range" min={0.5} max={2.5} step={0.1} value={v.panSpeed} onChange={(e) => settings.update({ panSpeed: Number(e.target.value) })} />
          </label>
          <div className="dialog-actions">
            <button className="btn ghost" onClick={() => app.go('menu')}>
              ← Back
            </button>
          </div>
        </div>
      </div>
    </MenuShell>
  );
}
