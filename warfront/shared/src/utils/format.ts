import { GAME_MINUTES_PER_SIM_SECOND, START_DAY_OF_YEAR, START_MINUTE_OF_DAY, START_YEAR } from '../constants/game';

/** 58456 -> "58,456" (fast, allocation-light, used in the render loop). */
export function formatNumber(value: number): string {
  const n = Math.round(value);
  const neg = n < 0;
  let s = String(Math.abs(n));
  let out = '';
  while (s.length > 3) {
    out = ',' + s.slice(-3) + out;
    s = s.slice(0, -3);
  }
  return (neg ? '-' : '') + s + out;
}

/** 58456 -> "58K", 12500 -> "12.5K", 1250000 -> "1.25M". */
export function formatCompact(value: number): string {
  const n = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  if (n >= 1_000_000) return sign + trim(n / 1_000_000, n >= 10_000_000 ? 1 : 2) + 'M';
  if (n >= 10_000) return sign + Math.round(n / 1000) + 'K';
  if (n >= 1_000) return sign + trim(n / 1000, 1) + 'K';
  return sign + Math.round(n);
}

function trim(v: number, digits: number): string {
  return v.toFixed(digits).replace(/\.?0+$/, '');
}

export interface GameClock {
  year: number;
  /** Days since the campaign began (1-based). */
  day: number;
  /** Calendar date, e.g. "6월 24일". */
  date: string;
  hour: number;
  minute: number;
}

export function toGameClock(simSeconds: number): GameClock {
  const totalMinutes = START_MINUTE_OF_DAY + Math.floor(simSeconds * GAME_MINUTES_PER_SIM_SECOND);
  const dayIndex = Math.floor(totalMinutes / 1440);
  const minuteOfDay = totalMinutes % 1440;
  const doy = START_DAY_OF_YEAR + dayIndex;
  return {
    year: START_YEAR + Math.floor(doy / 365),
    day: dayIndex + 1,
    date: calendarDate(doy % 365),
    hour: Math.floor(minuteOfDay / 60),
    minute: minuteOfDay % 60,
  };
}

export function formatClock(simSeconds: number): string {
  const c = toGameClock(simSeconds);
  return `${String(c.hour).padStart(2, '0')}:${String(c.minute).padStart(2, '0')}`;
}

const MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

function calendarDate(dayOfYear: number): string {
  let d = dayOfYear;
  for (let m = 0; m < 12; m++) {
    if (d < MONTH_DAYS[m]) return `${m + 1}월 ${d + 1}일`;
    d -= MONTH_DAYS[m];
  }
  return '12월 31일';
}
