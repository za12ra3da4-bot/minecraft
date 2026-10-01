import { useEffect, useState } from 'react';
import type { GameClient } from '../game/GameClient';

export function Toasts({ game }: { game: GameClient }) {
  const [, tick] = useState(0);
  useEffect(() => {
    const id = window.setInterval(() => tick((n) => n + 1), 500);
    return () => clearInterval(id);
  }, []);
  const now = Date.now();
  return (
    <div className="hud toasts">
      {game.toasts
        .filter((t) => t.until > now)
        .map((t) => (
          <div key={t.id} className={`panel toast ${t.kind}`}>
            {t.text}
          </div>
        ))}
    </div>
  );
}
