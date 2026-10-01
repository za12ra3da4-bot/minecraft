/** Uniform grid spatial index rebuilt every tick. */
export class SpatialHash<T extends { x: number; y: number }> {
  private cells = new Map<number, T[]>();

  constructor(private cellSize: number) {}

  clear(): void {
    this.cells.clear();
  }

  private key(cx: number, cy: number): number {
    return (cx + 4096) * 8192 + (cy + 4096);
  }

  insert(item: T): void {
    const k = this.key(Math.floor(item.x / this.cellSize), Math.floor(item.y / this.cellSize));
    let bucket = this.cells.get(k);
    if (!bucket) {
      bucket = [];
      this.cells.set(k, bucket);
    }
    bucket.push(item);
  }

  /** Calls fn for every item within `radius` of (x, y). */
  query(x: number, y: number, radius: number, fn: (item: T) => void): void {
    const r2 = radius * radius;
    const x0 = Math.floor((x - radius) / this.cellSize);
    const x1 = Math.floor((x + radius) / this.cellSize);
    const y0 = Math.floor((y - radius) / this.cellSize);
    const y1 = Math.floor((y + radius) / this.cellSize);
    for (let cx = x0; cx <= x1; cx++) {
      for (let cy = y0; cy <= y1; cy++) {
        const bucket = this.cells.get(this.key(cx, cy));
        if (!bucket) continue;
        for (const item of bucket) {
          const dx = item.x - x;
          const dy = item.y - y;
          if (dx * dx + dy * dy <= r2) fn(item);
        }
      }
    }
  }
}
