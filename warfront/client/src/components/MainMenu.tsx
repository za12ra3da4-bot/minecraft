import { GAME_SUBTITLE, GAME_TITLE } from '@warfront/shared';
import { settings } from '../data/settings';
import { app, type Screen } from '../game/AppState';
import { useStore } from '../game/store';
import { MenuShell } from './MenuShell';

const ITEMS: { screen: Screen; label: string; roman: string; desc: string; primary?: boolean }[] = [
  { screen: 'create', label: 'Create Game', roman: 'I', desc: 'Host a room for friends', primary: true },
  { screen: 'join', label: 'Join Game', roman: 'II', desc: 'Enter a room code' },
  { screen: 'singleplayer', label: 'Singleplayer', roman: 'III', desc: 'Fight the AI powers' },
  { screen: 'howto', label: 'How to Play', roman: 'IV', desc: '조작법 · Field manual' },
  { screen: 'settings', label: 'Settings', roman: 'V', desc: 'Name and display' },
];

export function MainMenu() {
  useStore(app);
  useStore(settings);
  const [first, ...rest] = GAME_TITLE.split('');
  return (
    <MenuShell>
      <div className="menu-column">
        <div>
          <h1 className="game-title">
            <span>{first}</span>
            {rest.join('')}
          </h1>
          <div className="game-subtitle">{GAME_SUBTITLE} — command a hundred thousand men.</div>
          <div className="title-rule" />
        </div>
        <div className="field">
          <span className="label">Commander name</span>
          <input
            className="input"
            maxLength={16}
            placeholder="Enter your name"
            value={settings.value.playerName}
            onChange={(e) => settings.update({ playerName: e.target.value })}
          />
        </div>
        <nav className="menu-list">
          {ITEMS.map((item, i) => (
            <button key={item.screen} className={`menu-item${item.primary ? ' primary' : ''}`} style={{ animationDelay: `${0.15 + i * 0.07}s` }} onClick={() => app.go(item.screen)}>
              <span className="roman">{item.roman}.</span>
              {item.label}
              <span className="desc">{item.desc}</span>
            </button>
          ))}
        </nav>
        {app.error && <div className="error-text">{app.error}</div>}
        <span className={`status-dot${app.connected ? ' on' : ''}`}>{app.connected ? 'Connected to war office' : app.everConnected ? 'Reconnecting…' : 'Connecting to server…'}</span>
      </div>
    </MenuShell>
  );
}
