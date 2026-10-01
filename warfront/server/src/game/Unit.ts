import { ARMY_TYPE_STATS, UNIT, UNIT_STATUSES, type ArmyType, type NationId, type UnitNet, type UnitStatus } from '@warfront/shared';

let nextUnitId = 1;

/** Authoritative army state. Only the server mutates these. */
export class Unit {
  readonly id: number;
  nation: NationId;
  type: ArmyType;
  name: string;
  soldiers: number;
  maxSoldiers: number;
  x: number;
  y: number;
  status: UnitStatus = 'IDLE';
  morale = 100;
  attack: number;
  defense: number;
  speed: number;
  tx: number | null = null;
  ty: number | null = null;
  targetUnit: number | null = null;
  joinUnit: number | null = null;
  path: number[] = [];
  pathIndex = 0;
  pathRev = 0;
  battleId: number | null = null;
  /** Seconds until the attack/join target is re-pathed. */
  repathIn = 0;
  kills = 0;
  /** Replication bookkeeping. */
  sentX = NaN;
  sentY = NaN;
  sentCold = '';
  sentHot = '';
  sentPathRev = -1;

  constructor(nation: NationId, type: ArmyType, name: string, soldiers: number, x: number, y: number) {
    this.id = nextUnitId++;
    this.nation = nation;
    this.type = type;
    this.name = name;
    this.soldiers = soldiers;
    this.maxSoldiers = soldiers;
    this.x = x;
    this.y = y;
    const stats = ARMY_TYPE_STATS[type];
    this.attack = stats.attack;
    this.defense = stats.defense;
    this.speed = UNIT.BASE_SPEED * stats.speed;
  }

  get alive(): boolean {
    return this.status !== 'DESTROYED';
  }

  get inBattle(): boolean {
    return this.battleId !== null;
  }

  get hasPath(): boolean {
    return this.pathIndex < this.path.length / 2;
  }

  setPath(path: number[], tx: number, ty: number): void {
    this.path = path;
    this.pathIndex = 0;
    this.pathRev++;
    this.tx = tx;
    this.ty = ty;
  }

  clearOrders(): void {
    this.path = [];
    this.pathIndex = 0;
    this.pathRev++;
    this.tx = null;
    this.ty = null;
    this.targetUnit = null;
    this.joinUnit = null;
  }

  toNet(includePath: boolean): UnitNet {
    const net: UnitNet = {
      id: this.id,
      nation: this.nation,
      type: this.type,
      name: this.name,
      soldiers: Math.round(this.soldiers),
      maxSoldiers: Math.round(this.maxSoldiers),
      x: Math.round(this.x * 2) / 2,
      y: Math.round(this.y * 2) / 2,
      status: this.status,
      morale: this.netMorale(),
      attack: Math.round(this.attack * 100) / 100,
      defense: Math.round(this.defense * 100) / 100,
      speed: Math.round(this.speed * 10) / 10,
      tx: this.tx === null ? null : Math.round(this.tx),
      ty: this.ty === null ? null : Math.round(this.ty),
      targetUnit: this.targetUnit,
      joinUnit: this.joinUnit,
      pathRev: this.pathRev,
      pathIndex: this.pathIndex,
      battleId: this.battleId,
    };
    if (includePath) net.path = this.path.map((v) => Math.round(v));
    return net;
  }

  /** Morale is replicated in steps of 5 to avoid resending recovering units every tick. */
  private netMorale(): number {
    return Math.round(this.morale / 5) * 5;
  }

  /** Orders and identity: changes rarely, replicated as a full record. */
  coldKey(): string {
    return `${Math.round(this.maxSoldiers)}|${this.type}|${this.name}|${this.tx}|${this.ty}|${this.targetUnit}|${this.joinUnit}|${this.pathRev}|${this.battleId}|${this.attack.toFixed(2)}|${this.defense.toFixed(2)}|${this.speed.toFixed(1)}`;
  }

  /** Combat state: changes often, replicated as a compact tuple. */
  hotKey(): string {
    return `${Math.round(this.soldiers)}|${this.netMorale()}|${this.status}|${this.pathIndex}`;
  }

  hotTuple(): [number, number, number, number, number] {
    return [this.id, Math.round(this.soldiers), this.netMorale(), UNIT_STATUSES.indexOf(this.status), this.pathIndex];
  }
}
