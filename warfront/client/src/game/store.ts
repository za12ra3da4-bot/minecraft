import { useSyncExternalStore } from 'react';

/** Minimal observable used by the app and game stores. */
export class Store {
  private listeners = new Set<() => void>();
  version = 0;

  subscribe = (fn: () => void): (() => void) => {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  };

  getVersion = (): number => this.version;

  notify(): void {
    this.version++;
    for (const fn of this.listeners) fn();
  }
}

/** Re-renders the component whenever the store notifies. */
export function useStore(store: Store): number {
  return useSyncExternalStore(store.subscribe, store.getVersion);
}
