/** Rename the game here – every screen reads the title from this constant. */
export const GAME_TITLE = 'WARFRONT';
export const GAME_SUBTITLE = 'Real-time grand battle strategy';

/** Server simulation tick. */
export const SERVER_TICK_MS = 100;
/** Deltas are broadcast every N ticks (5 Hz). */
export const BROADCAST_EVERY_TICKS = 2;
/** Private state (resources/production) is sent every N ticks. */
export const PRIVATE_EVERY_TICKS = 5;

/** In-game clock. One simulated second equals this many in-game minutes. */
export const GAME_MINUTES_PER_SIM_SECOND = 10;
export const START_YEAR = 1815;
/** In-game clock starts at 06:00 on day 1. */
export const START_MINUTE_OF_DAY = 6 * 60;

export const ROOM = {
  CODE_LENGTH: 6,
  CODE_ALPHABET: 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789',
  MAX_PLAYERS: 10,
  MAX_ROOMS: 200,
  NAME_MAX: 24,
  PLAYER_NAME_MAX: 16,
  /** A disconnected player keeps their seat this long (ms). */
  RECONNECT_GRACE_MS: 3 * 60_000,
  /** Empty rooms are removed after this long (ms). */
  EMPTY_ROOM_TTL_MS: 60_000,
} as const;

export const UNIT = {
  MIN_SOLDIERS: 60,
  MIN_SPLIT: 100,
  MAX_SOLDIERS: 500_000,
  /** Enemy units closer than this engage in battle. */
  ENGAGE_RADIUS: 34,
  /** Friendly units must be this close to merge. */
  MERGE_RADIUS: 70,
  /** Base movement speed in world units per sim second. */
  BASE_SPEED: 30,
  /** Large armies move slower: speed *= 1 - min(MAX_SIZE_SLOWDOWN, soldiers / SIZE_SLOWDOWN_SOLDIERS). */
  SIZE_SLOWDOWN_SOLDIERS: 300_000,
  MAX_SIZE_SLOWDOWN: 0.3,
  MAX_UNITS_PER_NATION: 160,
  MAX_COMMAND_UNITS: 200,
} as const;

export const TERRAIN_SPEED = {
  PLAINS: 1,
  FOREST: 0.72,
  HILLS: 0.68,
  MARSH: 0.55,
  ROAD: 1.45,
  RIVER_CROSSING: 0.4,
} as const;

export const COMBAT = {
  /** Fraction of effective strength dealt as casualties per sim second. */
  BASE_DAMAGE: 0.016,
  /** Random factor applied per tick (+/-). */
  DAMAGE_JITTER: 0.18,
  ROUT_MORALE: 18,
  /** Morale lost per percent of soldiers lost. */
  MORALE_PER_LOSS_PCT: 1.6,
  /** Constant morale drain while fighting (per sim second). */
  MORALE_DRAIN: 0.35,
  MORALE_RECOVERY: 1.6,
  DEFENDER_BONUS: 1.12,
  HILLS_DEFENSE: 1.3,
  FOREST_DEFENSE: 1.2,
  TOWN_DEFENSE: 1.25,
  RIVER_ATTACK_PENALTY: 0.75,
  /** Units that disengage keep taking damage at this multiplier. */
  RETREAT_DAMAGE_TAKEN: 1.4,
} as const;

export const CAPTURE = {
  /** Base seconds to capture a territory with a 10k army. */
  BASE_SECONDS: 12,
  DECAY_PER_SECOND: 0.08,
  MOVING_FACTOR: 0.5,
  CAPITAL_FACTOR: 0.45,
  CITY_FACTOR: 0.7,
} as const;

export const ECONOMY = {
  /** Resource income per sim second per unit of territory value. */
  MANPOWER_PER_POP: 0.0004,
  INDUSTRY_PER_POINT: 0.08,
  SUPPLIES_PER_POINT: 0.22,
  SUPPLIES_PER_TERRITORY: 0.35,
  /** Supplies consumed per soldier per sim second. */
  UPKEEP_PER_SOLDIER: 0.00009,
  CAPITAL_BONUS: 1.25,
  /** Losing the capital costs this share of stockpiles. */
  CAPITAL_LOSS_SHARE: 0.3,
  CAPITAL_LOSS_MORALE: 22,
  OUT_OF_SUPPLY_MORALE_DRAIN: 0.8,
  OUT_OF_SUPPLY_ATTRITION: 0.0015,
  MAX_STOCK: { manpower: 5_000_000, industry: 200_000, supplies: 400_000 },
  STARTING: { manpower: 250_000, industry: 1_240, supplies: 8_500 },
} as const;

export const PRODUCTION = {
  MIN_SOLDIERS: 1_000,
  MAX_SOLDIERS: 100_000,
  BASE_SECONDS: 4,
  SOLDIERS_PER_SECOND: 2_400,
  /** Industry cost per soldier. */
  INDUSTRY_PER_SOLDIER: 0.02,
  /** Supplies cost per soldier. */
  SUPPLIES_PER_SOLDIER: 0.05,
  MAX_QUEUE_PER_CITY: 3,
} as const;

export const DIPLOMACY = {
  OFFER_TTL_SECONDS: 45,
  /** After peace is signed, war cannot be declared again for this long. */
  TRUCE_SECONDS: 60,
  MAX_OFFERS_PER_NATION: 6,
} as const;

export const VICTORY = {
  DOMINATION_SHARE: 0.6,
} as const;

export const CHAT = {
  MAX_LENGTH: 200,
  /** Burst of messages allowed in WINDOW_MS. */
  BURST: 5,
  WINDOW_MS: 10_000,
  HISTORY: 60,
} as const;

export const RATE_LIMIT = {
  COMMANDS_PER_SECOND: 20,
  COMMAND_BURST: 40,
  ROOM_ACTIONS_PER_MINUTE: 30,
} as const;
