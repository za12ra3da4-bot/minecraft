import { useState } from 'react';
import { settings } from '../data/settings';
import { app } from '../game/AppState';
import { useStore } from '../game/store';
import { MenuShell } from './MenuShell';

export function JoinGame() {
  useStore(app);
  const [code, setCode] = useState(app.inviteCode ?? '');
  const [name, setName] = useState(settings.value.playerName);
  const valid = code.trim().length === 6;
  return (
    <MenuShell>
      <div className="dialog-wrap">
        <form
          className="panel dialog"
          style={{ width: 'min(520px, 100%)' }}
          onSubmit={(e) => {
            e.preventDefault();
            settings.update({ playerName: name });
            void app.joinRoom(code.trim().toUpperCase(), name);
          }}
        >
          <div>
            <div className="panel-title">Report for duty</div>
            <h2>Join Game</h2>
          </div>
          <label className="field">
            <span className="label">Room code</span>
            <div className="code-input">
              <input className="input" autoFocus maxLength={6} placeholder="W7K4P2" value={code} onChange={(e) => setCode(e.target.value.replace(/[^a-z0-9]/gi, '').toUpperCase())} />
            </div>
          </label>
          <label className="field">
            <span className="label">Commander name</span>
            <input className="input" maxLength={16} value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
          </label>
          {app.error && <div className="error-text">{app.error}</div>}
          <div className="dialog-actions">
            <button type="button" className="btn ghost" onClick={() => app.go('menu')}>
              ← Back
            </button>
            <button type="submit" className="btn primary" disabled={!valid || app.busy || !app.connected}>
              {app.busy ? 'Joining…' : 'Join Game'}
            </button>
          </div>
        </form>
      </div>
    </MenuShell>
  );
}
