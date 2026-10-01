import { Terrain } from '@warfront/shared';
import { useEffect, useRef } from 'react';
import type { GameClient } from '../game/GameClient';
import type { Renderer } from '../rendering/Renderer';
import { hexToRgb, nationColor } from '../rendering/palette';

const WIDTH = 220;

/** Whole-theatre overview: territory colours, armies, battles and the camera frame. */
export function Minimap({ game, renderer }: { game: GameClient; renderer: Renderer | null }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const map = game.replica.map;
  const height = Math.round((WIDTH * map.height) / map.width);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !renderer) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = WIDTH * dpr;
    canvas.height = height * dpr;
    const ctx = canvas.getContext('2d')!;
    const base = document.createElement('canvas');
    base.width = map.cols;
    base.height = map.rows;
    const bctx = base.getContext('2d')!;
    let builtVersion = -1;
    let last = 0;

    const draw = (): void => {
      const now = performance.now();
      if (now - last < 120) return;
      last = now;
      const r = game.replica;
      if (builtVersion !== r.ownersVersion) {
        builtVersion = r.ownersVersion;
        const img = bctx.createImageData(map.cols, map.rows);
        const colors = new Map<string | null, [number, number, number]>();
        for (let c = 0; c < map.cols * map.rows; c++) {
          const t = game.grids.territoryGrid[c];
          const o = c * 4;
          if (t < 0 || game.grids.terrain[c] === Terrain.WATER) {
            img.data[o] = 64;
            img.data[o + 1] = 88;
            img.data[o + 2] = 98;
          } else {
            const owner = r.owners[t];
            let col = colors.get(owner);
            if (!col) {
              const [cr, cg, cb] = hexToRgb(nationColor(owner));
              col = owner ? [cr * 0.75 + 40, cg * 0.75 + 40, cb * 0.75 + 40] : [150, 140, 118];
              colors.set(owner, col);
            }
            img.data[o] = col[0];
            img.data[o + 1] = col[1];
            img.data[o + 2] = col[2];
          }
          img.data[o + 3] = 255;
        }
        bctx.putImageData(img, 0, 0);
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(base, 0, 0, WIDTH, height);
      const k = WIDTH / map.width;
      for (const u of r.units.values()) {
        ctx.fillStyle = u.nation === game.you ? '#ffe9a6' : '#15120d';
        const s = u.soldiers > 30_000 ? 3 : 2;
        ctx.fillRect(u.x * k - s / 2, u.y * k - s / 2, s, s);
      }
      for (const b of r.battles) {
        ctx.strokeStyle = '#ff5a3c';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(b.x * k, b.y * k, 4 + Math.sin(now / 150) * 1.5, 0, Math.PI * 2);
        ctx.stroke();
      }
      const v = renderer.camera.viewBounds();
      ctx.strokeStyle = '#ffe08a';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(v.x0 * k, v.y0 * k, (v.x1 - v.x0) * k, (v.y1 - v.y0) * k);
    };
    renderer.onFrame = draw;
    return () => {
      renderer.onFrame = null;
    };
  }, [game, renderer, map, height]);

  const jump = (e: React.PointerEvent<HTMLCanvasElement>): void => {
    if (!renderer || (e.type === 'pointermove' && e.buttons !== 1)) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * map.width;
    const y = ((e.clientY - rect.top) / rect.height) * map.height;
    renderer.camera.setView(x, y, renderer.camera.zoom);
  };

  return (
    <div className="hud panel minimap">
      <canvas ref={ref} style={{ width: WIDTH, height }} onPointerDown={jump} onPointerMove={jump} />
    </div>
  );
}
