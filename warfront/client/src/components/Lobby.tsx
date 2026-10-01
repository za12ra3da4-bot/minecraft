import { getMapDef, getNation } from '@warfront/shared';
import { useState } from 'react';
import { getSocket, request } from '../network/connection';
import { app } from '../game/AppState';
import { useStore } from '../game/store';
import { ChatBox } from './ChatBox';
import { Flag } from './Flag';
import { MenuShell } from './MenuShell';
import { VICTORY_LABELS } from './options';
import { SettingsForm } from './SettingsForm';

export function Lobby() {
  useStore(app);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [editing, setEditing] = useState(false);
  const room = app.room;
  if (!room) return null;
  const me = room.players.find((p) => p.id === app.playerId);
  const isHost = app.isHost;
  const def = getMapDef(room.settings.mapId);
  const taken = new Map(room.players.filter((p) => p.nation).map((p) => [p.nation!, p.name]));
  const invite = `${location.origin}${location.pathname}?room=${room.code}`;
  const others = room.players.filter((p) => !p.isHost);
  const canStart = room.players.every((p) => p.nation) && others.every((p) => p.ready);

  const pick = async (nation: string) => {
    const res = await request('lobby:nation', me?.nation === nation ? null : nation);
    setError(res.ok ? null : res.error);
  };
  const start = async () => {
    const res = await request('lobby:start');
    setError(res.ok ? null : res.error);
  };
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(invite);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  return (
    <MenuShell shade={false}>
      <div className="lobby">
        <section className="panel">
          <div className="panel-title">War room</div>
          <div>
            <div className="label">Room code — share with friends</div>
            <div className="room-code" data-testid="room-code">
              {room.code}
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <button className="btn small" onClick={copy}>
                {copied ? 'Copied!' : 'Copy invite link'}
              </button>
            </div>
          </div>
          <div className="panel-title">Commanders · {room.players.length}/{room.settings.maxPlayers}</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, overflowY: 'auto' }}>
            {room.players.map((p) => (
              <div className="player-row" key={p.id} style={{ opacity: p.connected ? 1 : 0.5 }}>
                <Flag nation={p.nation} height={20} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="pname">
                    {p.name}
                    {p.id === app.playerId && <span className="hint"> (you)</span>}
                  </div>
                  <div className="sub">{p.nation ? getNation(p.nation).name : 'Choosing nation…'}</div>
                </div>
                {p.isHost && <span className="badge host">♛ Host</span>}
                {!p.isHost && <span className={`badge${p.ready ? ' ready' : ''}`}>{p.ready ? 'Ready' : 'Not ready'}</span>}
              </div>
            ))}
          </div>
          <div className="panel-title">Settings</div>
          {editing && isHost ? (
            <SettingsForm
              value={room.settings}
              onChange={(s) => {
                void request('lobby:settings', s).then((res) => setError(res.ok ? null : res.error));
              }}
            />
          ) : (
            <dl className="settings-summary">
              <dt>Room</dt>
              <dd>{room.settings.roomName}</dd>
              <dt>Map</dt>
              <dd>{def?.name}</dd>
              <dt>Speed</dt>
              <dd>{room.settings.speed}x</dd>
              <dt>Victory</dt>
              <dd>{VICTORY_LABELS[room.settings.victory].label}</dd>
              <dt>AI nations</dt>
              <dd>{room.settings.aiCount}</dd>
              <dt>Start</dt>
              <dd>{room.settings.startAtWar ? 'At war' : 'At peace'}</dd>
            </dl>
          )}
          {isHost && (
            <button className="btn small ghost" onClick={() => setEditing(!editing)}>
              {editing ? 'Done editing' : 'Edit settings'}
            </button>
          )}
        </section>

        <section className="panel" style={{ overflowY: 'auto' }}>
          <div className="panel-title">Choose your nation</div>
          <div className="nation-grid">
            {room.nations.map((n) => {
              const owner = taken.get(n);
              const mine = me?.nation === n;
              return (
                <button key={n} className={`nation-card${mine ? ' mine' : ''}`} style={{ ['--nation' as string]: getNation(n).color }} disabled={!!owner && !mine} onClick={() => void pick(n)} data-testid={`nation-${n}`}>
                  <Flag nation={n} height={24} />
                  <span style={{ display: 'flex', flexDirection: 'column' }}>
                    <span className="nname">{getNation(n).name}</span>
                    <span className="taken">{owner ? (mine ? 'Your nation' : `Taken by ${owner}`) : 'Available'}</span>
                  </span>
                </button>
              );
            })}
          </div>
          <p className="hint">Nations nobody picks are played by the AI (up to the AI count) or left as unclaimed land you can conquer.</p>
          {error && <div className="error-text">{error}</div>}
          <div className="dialog-actions" style={{ marginTop: 'auto' }}>
            <button className="btn ghost" onClick={() => app.leave()}>
              Leave room
            </button>
            <div style={{ display: 'flex', gap: 10 }}>
              {!isHost && (
                <button className={`btn${me?.ready ? ' active' : ''}`} disabled={!me?.nation} onClick={() => getSocket().emit('lobby:ready', !me?.ready)} data-testid="ready">
                  {me?.ready ? '✓ Ready' : 'Ready'}
                </button>
              )}
              {isHost && (
                <button className="btn primary" disabled={!canStart} onClick={() => void start()} data-testid="start">
                  Start Game
                </button>
              )}
            </div>
          </div>
          {isHost && !canStart && <div className="hint">Everyone must pick a nation and other players must be READY.</div>}
        </section>

        <section className="panel">
          <div className="panel-title">Dispatches</div>
          <ChatBox messages={app.lobbyChat} />
        </section>
      </div>
    </MenuShell>
  );
}
