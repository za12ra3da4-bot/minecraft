import { CHAT, getNation, type ChatMessage } from '@warfront/shared';
import { useEffect, useRef, useState } from 'react';
import { request } from '../network/connection';

/** Chat log + input used in the lobby and in game. */
export function ChatBox({ messages, compact }: { messages: ChatMessage[]; compact?: boolean }) {
  const [text, setText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length]);
  const send = async () => {
    const t = text.trim();
    if (!t) return;
    const res = await request('chat:send', t);
    if (res.ok) {
      setText('');
      setError(null);
    } else setError(res.error);
  };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minHeight: 0, flex: 1 }}>
      <div className="chat-log" ref={logRef} style={compact ? { maxHeight: 160 } : undefined}>
        {messages.map((m) => (
          <div key={m.id} className={`chat-line${m.system ? ' system' : ''}`}>
            {!m.system && (
              <span className="who" style={{ color: m.nation ? getNation(m.nation).color : 'var(--brass)' }}>
                [{m.from}]
              </span>
            )}
            {m.text}
          </div>
        ))}
        {!messages.length && <div className="hint">아직 메시지가 없습니다.</div>}
      </div>
      <form
        style={{ display: 'flex', gap: 6 }}
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <input className="input" style={{ minHeight: 32, fontSize: 14 }} maxLength={CHAT.MAX_LENGTH} placeholder="메시지 입력…" value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.stopPropagation()} />
        <button className="btn small" type="submit">
          보내기
        </button>
      </form>
      {error && <div className="error-text" style={{ fontSize: 12 }}>{error}</div>}
    </div>
  );
}
