import { useState } from 'react';
import { settings } from '../data/settings';
import { app } from '../game/AppState';
import { useStore } from '../game/store';
import { MenuShell } from './MenuShell';
import { defaultSettings } from './options';
import { SettingsForm } from './SettingsForm';

export function CreateGame() {
  useStore(app);
  const [value, setValue] = useState(defaultSettings);
  return (
    <MenuShell>
      <div className="dialog-wrap">
        <form
          className="panel dialog"
          onSubmit={(e) => {
            e.preventDefault();
            void app.createRoom({ playerName: settings.value.playerName, settings: value });
          }}
        >
          <div>
            <div className="panel-title">New campaign</div>
            <h2>Create Game</h2>
          </div>
          <SettingsForm value={value} onChange={setValue} />
          {app.error && <div className="error-text">{app.error}</div>}
          <div className="dialog-actions">
            <button type="button" className="btn ghost" onClick={() => app.go('menu')}>
              ← Back
            </button>
            <button type="submit" className="btn primary" disabled={app.busy || !app.connected}>
              {app.busy ? 'Creating…' : 'Create Game'}
            </button>
          </div>
        </form>
      </div>
    </MenuShell>
  );
}
