/** Binary min-heap of integer items keyed by float priorities. */
export class MinHeap {
  private items: number[] = [];
  private prios: number[] = [];

  get size(): number {
    return this.items.length;
  }

  clear(): void {
    this.items.length = 0;
    this.prios.length = 0;
  }

  push(item: number, priority: number): void {
    const items = this.items;
    const prios = this.prios;
    let i = items.length;
    items.push(item);
    prios.push(priority);
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (prios[parent] <= priority) break;
      items[i] = items[parent];
      prios[i] = prios[parent];
      i = parent;
    }
    items[i] = item;
    prios[i] = priority;
  }

  /** Priority of the top element (call before pop). */
  peekPriority(): number {
    return this.prios[0];
  }

  pop(): number {
    const items = this.items;
    const prios = this.prios;
    const top = items[0];
    const lastItem = items.pop()!;
    const lastPrio = prios.pop()!;
    const n = items.length;
    if (n > 0) {
      let i = 0;
      for (;;) {
        const l = i * 2 + 1;
        if (l >= n) break;
        const r = l + 1;
        const c = r < n && prios[r] < prios[l] ? r : l;
        if (prios[c] >= lastPrio) break;
        items[i] = items[c];
        prios[i] = prios[c];
        i = c;
      }
      items[i] = lastItem;
      prios[i] = lastPrio;
    }
    return top;
  }
}
