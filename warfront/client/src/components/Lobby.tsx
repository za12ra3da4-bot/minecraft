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
          <div className="panel-title">작전실</div>
          <div>
            <div className="label">방 코드 — 친구에게 알려주세요</div>
            <div className="room-code" data-testid="room-code">
              {room.code}
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <button className="btn small" onClick={copy}>
                {copied ? '복사됨!' : '초대 링크 복사'}
              </button>
            </div>
          </div>
          <div className="panel-title">플레이어 · {room.players.length}/{room.settings.maxPlayers}</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, overflowY: 'auto' }}>
            {room.players.map((p) => (
              <div className="player-row" key={p.id} style={{ opacity: p.connected ? 1 : 0.5 }}>
                <Flag nation={p.nation} height={20} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="pname">
                    {p.name}
                    {p.id === app.playerId && <span className="hint"> (나)</span>}
                  </div>
                  <div className="sub">{p.nation ? getNation(p.nation).name : '나라 고르는 중…'}</div>
                </div>
                {p.isHost && <span className="badge host">♛ 방장</span>}
                {!p.isHost && <span className={`badge${p.ready ? ' ready' : ''}`}>{p.ready ? '준비 완료' : '준비 중'}</span>}
              </div>
            ))}
          </div>
          <div className="panel-title">설정</div>
          {editing && isHost ? (
            <SettingsForm
              value={room.settings}
              onChange={(s) => {
                void request('lobby:settings', s).then((res) => setError(res.ok ? null : res.error));
              }}
            />
          ) : (
            <dl className="settings-summary">
              <dt>방</dt>
              <dd>{room.settings.roomName}</dd>
              <dt>지도</dt>
              <dd>{def?.name}</dd>
              <dt>속도</dt>
              <dd>{room.settings.speed}배</dd>
              <dt>승리 조건</dt>
              <dd>{VICTORY_LABELS[room.settings.victory].label}</dd>
              <dt>AI 나라</dt>
              <dd>{room.settings.aiCount}</dd>
              <dt>시작</dt>
              <dd>{room.settings.startAtWar ? '역사적 전쟁' : '평화'}</dd>
            </dl>
          )}
          {isHost && (
            <button className="btn small ghost" onClick={() => setEditing(!editing)}>
              {editing ? '설정 완료' : '설정 바꾸기'}
            </button>
          )}
        </section>

        <section className="panel" style={{ overflowY: 'auto' }}>
          <div className="panel-title">나라 고르기</div>
          <div className="nation-grid">
            {room.nations.map((n) => {
              const owner = taken.get(n);
              const mine = me?.nation === n;
              return (
                <button key={n} className={`nation-card${mine ? ' mine' : ''}`} style={{ ['--nation' as string]: getNation(n).color }} disabled={!!owner && !mine} onClick={() => void pick(n)} data-testid={`nation-${n}`}>
                  <Flag nation={n} height={24} />
                  <span style={{ display: 'flex', flexDirection: 'column' }}>
                    <span className="nname">{getNation(n).name}</span>
                    <span className="taken">{owner ? (mine ? '내 나라' : `${owner} 선택함`) : '선택 가능'}</span>
                  </span>
                </button>
              );
            })}
          </div>
          <p className="hint">아무도 고르지 않은 나라는 AI가 맡거나(AI 나라 수만큼), 정복할 수 있는 빈 땅이 됩니다.</p>
          {error && <div className="error-text">{error}</div>}
          <div className="dialog-actions" style={{ marginTop: 'auto' }}>
            <button className="btn ghost" onClick={() => app.leave()}>
              방 나가기
            </button>
            <div style={{ display: 'flex', gap: 10 }}>
              {!isHost && (
                <button className={`btn${me?.ready ? ' active' : ''}`} disabled={!me?.nation} onClick={() => getSocket().emit('lobby:ready', !me?.ready)} data-testid="ready">
                  {me?.ready ? '✓ 준비 완료' : '준비'}
                </button>
              )}
              {isHost && (
                <button className="btn primary" disabled={!canStart} onClick={() => void start()} data-testid="start">
                  게임 시작
                </button>
              )}
            </div>
          </div>
          {isHost && !canStart && <div className="hint">모두 나라를 고르고, 다른 플레이어가 [준비]를 눌러야 시작할 수 있습니다.</div>}
        </section>

        <section className="panel">
          <div className="panel-title">채팅</div>
          <ChatBox messages={app.lobbyChat} />
        </section>
      </div>
    </MenuShell>
  );
}
