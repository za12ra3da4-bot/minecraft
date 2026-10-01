import { GAME_SUBTITLE, GAME_TITLE } from '@warfront/shared';
import { settings } from '../data/settings';
import { app, type Screen } from '../game/AppState';
import { useStore } from '../game/store';
import { MenuShell } from './MenuShell';

const ITEMS: { screen: Screen; label: string; roman: string; desc: string; primary?: boolean }[] = [
  { screen: 'create', label: '방 만들기', roman: 'I', desc: '친구들과 함께 플레이', primary: true },
  { screen: 'join', label: '방 참가', roman: 'II', desc: '방 코드 입력' },
  { screen: 'singleplayer', label: '혼자 하기', roman: 'III', desc: 'AI 국가들과 전쟁' },
  { screen: 'howto', label: '게임 방법', roman: 'IV', desc: '조작법 안내' },
  { screen: 'settings', label: '설정', roman: 'V', desc: '이름과 화면' },
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
          <div className="game-subtitle">{GAME_SUBTITLE} — 수십만 대군을 지휘하라.</div>
          <div className="title-rule" />
        </div>
        <div className="field">
          <span className="label">사령관 이름</span>
          <input
            className="input"
            maxLength={16}
            placeholder="이름을 입력하세요"
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
        <span className={`status-dot${app.connected ? ' on' : ''}`}>{app.connected ? '서버에 연결됨' : app.everConnected ? '다시 연결하는 중…' : '서버에 연결하는 중…'}</span>
      </div>
    </MenuShell>
  );
}
