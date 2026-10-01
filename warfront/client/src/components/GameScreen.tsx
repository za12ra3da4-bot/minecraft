import { useEffect, useRef, useState } from 'react';
import { app } from '../game/AppState';
import type { GameClient } from '../game/GameClient';
import { useStore } from '../game/store';
import { Renderer } from '../rendering/Renderer';
import { CommandBar } from '../ui/CommandBar';
import { DiplomacyPanel } from '../ui/DiplomacyPanel';
import { EventLog } from '../ui/EventLog';
import { GameHelp } from '../ui/GameHelp';
import { GameOver } from '../ui/GameOver';
import { Minimap } from '../ui/Minimap';
import { NationPanel } from '../ui/NationPanel';
import { SelectionPanel } from '../ui/SelectionPanel';
import { Toasts } from '../ui/Toasts';
import { TopBar } from '../ui/TopBar';
import { ChatBox } from './ChatBox';

type Drawer = 'nation' | 'events' | 'chat' | null;

const HELP_KEY = 'warfront.helpSeen';

export function GameScreen({ game }: { game: GameClient }) {
  useStore(game);
  useStore(app);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [renderer, setRenderer] = useState<Renderer | null>(null);
  const [diplomacy, setDiplomacy] = useState(false);
  const [drawer, setDrawer] = useState<Drawer>(null);
  const [hideOver, setHideOver] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const [help, setHelp] = useState(() => {
    try {
      return localStorage.getItem(HELP_KEY) !== '1';
    } catch {
      return true;
    }
  });
  const closeHelp = (): void => {
    setHelp(false);
    try {
      localStorage.setItem(HELP_KEY, '1');
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    const r = new Renderer(canvasRef.current!, game);
    setRenderer(r);
    (window as unknown as { __warfront?: unknown }).__warfront = { game, renderer: r };
    return () => r.destroy();
  }, [game]);

  const toggle = (d: Exclude<Drawer, null>) => setDrawer(drawer === d ? null : d);

  return (
    <div className="game-root">
      <canvas ref={canvasRef} className="game-canvas" data-testid="game-canvas" />
      <TopBar
        game={game}
        onDiplomacy={() => setDiplomacy(true)}
        onHelp={() => setHelp(true)}
        onMenu={() => {
          if (confirm('전투를 떠나 메인 메뉴로 돌아갈까요?')) app.leave();
        }}
        onToggle={toggle}
      />
      <NationPanel game={game} open={drawer === 'nation'} />
      <SelectionPanel game={game} />
      <EventLog game={game} open={drawer === 'events'} />
      <div className={`hud panel chat-panel${drawer === 'chat' ? ' open' : ''}`}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="panel-title" style={{ flex: 1 }}>
            채팅
          </div>
          <button className="btn small ghost desktop-only" onClick={() => setChatOpen(!chatOpen)}>
            {chatOpen ? '–' : '+'}
          </button>
        </div>
        {(chatOpen || drawer === 'chat') && <ChatBox messages={game.chat} compact />}
      </div>
      <Minimap game={game} renderer={renderer} />
      <CommandBar game={game} onFocus={() => renderer?.focusSelection()} onSelectAll={() => renderer?.selectAll()} onCapital={() => renderer?.openCapital()} onHelp={() => setHelp(true)} />
      <Toasts game={game} />
      {diplomacy && <DiplomacyPanel game={game} onClose={() => setDiplomacy(false)} />}
      {help && <GameHelp onClose={closeHelp} />}
      {game.over && !hideOver && <GameOver game={game} onLeave={() => app.leave()} onClose={() => setHideOver(true)} />}
      {!app.connected && (
        <div className="overlay" style={{ background: 'rgba(5,6,8,0.35)' }}>
          <div className="panel" style={{ width: 'auto' }}>
            <div className="panel-title">서버 연결이 끊겼습니다 — 다시 연결하는 중…</div>
          </div>
        </div>
      )}
    </div>
  );
}
