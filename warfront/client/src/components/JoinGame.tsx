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
            <div className="panel-title">참전</div>
            <h2>방 참가</h2>
          </div>
          <label className="field">
            <span className="label">방 코드 (친구에게 받은 6글자)</span>
            <div className="code-input">
              <input className="input" autoFocus maxLength={6} placeholder="W7K4P2" value={code} onChange={(e) => setCode(e.target.value.replace(/[^a-z0-9]/gi, '').toUpperCase())} />
            </div>
          </label>
          <label className="field">
            <span className="label">사령관 이름</span>
            <input className="input" maxLength={16} value={name} onChange={(e) => setName(e.target.value)} placeholder="이름" />
          </label>
          {app.error && <div className="error-text">{app.error}</div>}
          <div className="dialog-actions">
            <button type="button" className="btn ghost" onClick={() => app.go('menu')}>
              ← 뒤로
            </button>
            <button type="submit" className="btn primary" disabled={!valid || app.busy || !app.connected}>
              {app.busy ? '참가하는 중…' : '참가하기'}
            </button>
          </div>
        </form>
      </div>
    </MenuShell>
  );
}
