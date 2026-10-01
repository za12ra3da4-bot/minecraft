import { getMapDef, getNation } from '@warfront/shared';
import { useState } from 'react';
import { settings } from '../data/settings';
import { app } from '../game/AppState';
import { useStore } from '../game/store';
import { Flag } from './Flag';
import { MenuShell } from './MenuShell';
import { defaultSettings } from './options';
import { SettingsForm } from './SettingsForm';

export function Singleplayer() {
  useStore(app);
  const [value, setValue] = useState(() => ({ ...defaultSettings(), aiCount: 9, roomName: 'Solo campaign' }));
  const [nation, setNation] = useState('france');
  const def = getMapDef(value.mapId)!;
  const nations = def.nations.map((n) => n.nation);
  const chosen = nations.includes(nation) ? nation : nations[0];
  return (
    <MenuShell>
      <div className="dialog-wrap">
        <form
          className="panel dialog"
          onSubmit={(e) => {
            e.preventDefault();
            void app.createRoom({ playerName: settings.value.playerName, settings: value, singleplayer: true, nation: chosen });
          }}
        >
          <div>
            <div className="panel-title">Solo campaign</div>
            <h2>Singleplayer</h2>
          </div>
          <div className="field">
            <span className="label">Choose your nation</span>
            <div className="nation-grid">
              {nations.map((n) => (
                <button type="button" key={n} className={`nation-card${n === chosen ? ' mine' : ''}`} style={{ ['--nation' as string]: getNation(n).color }} onClick={() => setNation(n)}>
                  <Flag nation={n} height={20} />
                  <span className="nname">{getNation(n).name}</span>
                </button>
              ))}
            </div>
          </div>
          <SettingsForm value={value} onChange={(v) => setValue({ ...v, aiCount: Math.min(v.aiCount, getMapDef(v.mapId)!.nations.length - 1) })} singleplayer />
          {app.error && <div className="error-text">{app.error}</div>}
          <div className="dialog-actions">
            <button type="button" className="btn ghost" onClick={() => app.go('menu')}>
              ← Back
            </button>
            <button type="submit" className="btn primary" disabled={app.busy || !app.connected}>
              {app.busy ? 'Mobilising…' : 'Start Campaign'}
            </button>
          </div>
        </form>
      </div>
    </MenuShell>
  );
}
