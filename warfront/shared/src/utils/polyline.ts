/** Polyline helpers operating on flat [x0, y0, x1, y1, ...] arrays. */

/** Ramer–Douglas–Peucker simplification. Endpoints are always kept. */
export function simplifyPolyline(points: number[], epsilon: number): number[] {
  const n = points.length / 2;
  if (n <= 2) return points.slice();
  const keep = new Uint8Array(n);
  keep[0] = 1;
  keep[n - 1] = 1;
  const stack: [number, number][] = [[0, n - 1]];
  const eps2 = epsilon * epsilon;
  while (stack.length) {
    const [a, b] = stack.pop()!;
    const ax = points[a * 2];
    const ay = points[a * 2 + 1];
    const bx = points[b * 2];
    const by = points[b * 2 + 1];
    const dx = bx - ax;
    const dy = by - ay;
    const len2 = dx * dx + dy * dy;
    let maxD = -1;
    let idx = -1;
    for (let i = a + 1; i < b; i++) {
      const px = points[i * 2];
      const py = points[i * 2 + 1];
      let d2: number;
      if (len2 === 0) {
        d2 = (px - ax) ** 2 + (py - ay) ** 2;
      } else {
        const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / len2));
        d2 = (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2;
      }
      if (d2 > maxD) {
        maxD = d2;
        idx = i;
      }
    }
    if (idx >= 0 && maxD > eps2) {
      keep[idx] = 1;
      stack.push([a, idx], [idx, b]);
    }
  }
  const out: number[] = [];
  for (let i = 0; i < n; i++) if (keep[i]) out.push(points[i * 2], points[i * 2 + 1]);
  return out;
}

/** Chaikin corner cutting. Open polylines keep their endpoints. */
export function chaikin(points: number[], iterations: number, closed = false): number[] {
  let pts = points;
  for (let it = 0; it < iterations; it++) {
    const n = pts.length / 2;
    if (n < 3) return pts;
    const out: number[] = [];
    if (!closed) out.push(pts[0], pts[1]);
    const segs = closed ? n : n - 1;
    for (let i = 0; i < segs; i++) {
      const j = (i + 1) % n;
      const x0 = pts[i * 2];
      const y0 = pts[i * 2 + 1];
      const x1 = pts[j * 2];
      const y1 = pts[j * 2 + 1];
      if (!closed && i === 0) {
        out.push(0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1);
        if (segs === 1) break;
        continue;
      }
      out.push(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1);
      if (!closed && i === segs - 1) continue;
      out.push(0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1);
    }
    if (!closed) out.push(pts[(n - 1) * 2], pts[(n - 1) * 2 + 1]);
    pts = out;
  }
  return pts;
}

/** Catmull-Rom spline through control points, sampled every `step` world units. */
export function catmullRom(control: number[], step: number): number[] {
  const n = control.length / 2;
  if (n < 2) return control.slice();
  const get = (i: number): [number, number] => {
    const k = Math.max(0, Math.min(n - 1, i));
    return [control[k * 2], control[k * 2 + 1]];
  };
  const out: number[] = [];
  for (let i = 0; i < n - 1; i++) {
    const p0 = get(i - 1);
    const p1 = get(i);
    const p2 = get(i + 1);
    const p3 = get(i + 2);
    const segLen = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
    const samples = Math.max(2, Math.ceil(segLen / step));
    for (let s = 0; s < samples; s++) {
      const t = s / samples;
      const t2 = t * t;
      const t3 = t2 * t;
      const x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3);
      const y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3);
      out.push(x, y);
    }
  }
  const last = get(n - 1);
  out.push(last[0], last[1]);
  return out;
}

export function polylineLength(points: number[]): number {
  let len = 0;
  for (let i = 2; i < points.length; i += 2) len += Math.hypot(points[i] - points[i - 2], points[i + 1] - points[i - 1]);
  return len;
}

export function roundPoints(points: number[], decimals = 1): number[] {
  const f = 10 ** decimals;
  return points.map((v) => Math.round(v * f) / f);
}
