import type { NationId } from '@warfront/shared';
import { getNation } from '@warfront/shared';
import { flagDataUrl } from '../rendering/FlagPainter';

export function Flag({ nation, height = 18 }: { nation: NationId | null; height?: number }) {
  if (!nation) return <span className="flag-img" style={{ width: height * 1.5, height, background: '#3a362e' }} />;
  return <img className="flag-img" src={flagDataUrl(nation, Math.ceil(height))} width={height * 1.5} height={height} alt={getNation(nation).name} />;
}
