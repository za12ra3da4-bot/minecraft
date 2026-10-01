import { Store } from '../game/store';

export interface ClientSettings {
  playerName: string;
  showPaths: boolean;
  showCityNames: boolean;
  battleEffects: boolean;
  /** Edge scrolling and keyboard panning speed multiplier. */
  panSpeed: number;
}

const KEY = 'warfront.settings';

const DEFAULTS: ClientSettings = {
  playerName: '',
  showPaths: true,
  showCityNames: true,
  battleEffects: true,
  panSpeed: 1,
};

class SettingsStore extends Store {
  value: ClientSettings;

  constructor() {
    super();
    this.value = { ...DEFAULTS };
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) this.value = { ...DEFAULTS, ...(JSON.parse(raw) as Partial<ClientSettings>) };
    } catch {
      /* ignore */
    }
  }

  update(patch: Partial<ClientSettings>): void {
    this.value = { ...this.value, ...patch };
    try {
      localStorage.setItem(KEY, JSON.stringify(this.value));
    } catch {
      /* ignore */
    }
    this.notify();
  }
}

export const settings = new SettingsStore();
