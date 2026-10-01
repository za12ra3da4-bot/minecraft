import { useEffect, useRef, type ReactNode } from 'react';
import { MenuBackdrop } from '../rendering/MenuBackdrop';

/** Full-screen menu background: the animated battlefield behind a shade. */
export function MenuShell({ children, shade = true }: { children: ReactNode; shade?: boolean }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const backdrop = new MenuBackdrop(ref.current!);
    return () => backdrop.destroy();
  }, []);
  return (
    <div className="screen">
      <canvas ref={ref} className="backdrop-canvas" />
      <div className="screen-shade" style={shade ? undefined : { opacity: 0.6 }} />
      {children}
    </div>
  );
}
