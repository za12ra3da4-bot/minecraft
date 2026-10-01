import {
  ARMY_TYPE_STATS,
  ARMY_TYPES,
  CITY_TYPE_STATS,
  PRODUCTION,
  UNIT,
  armyCost,
  formatNumber,
  getNation,
  getRelation,
  type ArmyType,
  type UnitNet,
} from '@warfront/shared';
import { useState } from 'react';
import { Flag } from '../components/Flag';
import type { GameClient } from '../game/GameClient';

function territoryName(game: GameClient, x: number, y: number): string {
  const m = game.replica.map;
  const cx = Math.floor(x / m.cellSize);
  const cy = Math.floor(y / m.cellSize);
  const t = cx >= 0 && cy >= 0 && cx < m.cols && cy < m.rows ? game.grids.territoryGrid[cy * m.cols + cx] : -1;
  return t >= 0 ? m.territories[t].name : 'open water';
}

function UnitDetails({ game, unit, own }: { game: GameClient; unit: UnitNet; own: boolean }) {
  const nation = getNation(unit.nation);
  const r = game.render.get(unit.id);
  const [split, setSplit] = useState(Math.floor(unit.soldiers / 2));
  const maxSplit = unit.soldiers - UNIT.MIN_SPLIT;
  const splitValue = Math.max(UNIT.MIN_SPLIT, Math.min(maxSplit, split));
  const destination = unit.tx !== null && unit.ty !== null ? territoryName(game, unit.tx, unit.ty) : null;
  const target = unit.targetUnit !== null ? game.replica.units.get(unit.targetUnit) : null;
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <Flag nation={unit.nation} height={28} />
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 19, fontWeight: 700, letterSpacing: '0.04em' }}>{unit.name}</div>
          <div className="hint" style={{ color: nation.color }}>
            {nation.adjective} · {ARMY_TYPE_STATS[unit.type].label}
          </div>
        </div>
      </div>
      <div>
        <div className="big-number" data-testid="selected-soldiers">
          {formatNumber(r?.shown ?? unit.soldiers)}
        </div>
        <div className="label">soldiers of {formatNumber(unit.maxSoldiers)}</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className={`status-pill ${unit.status}`}>{unit.status}</span>
        <span className="hint">near {territoryName(game, unit.x, unit.y)}</span>
      </div>
      <dl className="kv">
        <dt>Morale</dt>
        <dd>
          <div className="bar" style={{ marginTop: 4 }}>
            <div style={{ width: `${unit.morale}%`, background: unit.morale > 60 ? '#7fbf5a' : unit.morale > 30 ? '#e2b33c' : '#d6493a' }} />
          </div>
        </dd>
        <dt>Attack</dt>
        <dd>{unit.attack.toFixed(2)}</dd>
        <dt>Defence</dt>
        <dd>{unit.defense.toFixed(2)}</dd>
        <dt>Speed</dt>
        <dd>{unit.speed.toFixed(0)}</dd>
        <dt>Heading to</dt>
        <dd>{target ? `⚔ ${getNation(target.nation).adjective} ${target.name}` : (destination ?? '—')}</dd>
      </dl>
      {own && unit.battleId === null && maxSplit >= UNIT.MIN_SPLIT && (
        <div className="field">
          <span className="label">
            Split · {formatNumber(splitValue)} / {formatNumber(unit.soldiers)}
          </span>
          <input type="range" min={UNIT.MIN_SPLIT} max={maxSplit} step={100} value={splitValue} onChange={(e) => setSplit(Number(e.target.value))} data-testid="split-slider" />
          <button className="btn small" onClick={() => void game.command({ type: 'SPLIT_UNIT', unitId: unit.id, soldiers: splitValue })} data-testid="split">
            Split army
          </button>
        </div>
      )}
    </>
  );
}

function ProductionPanel({ game, cityId }: { game: GameClient; cityId: number }) {
  const [soldiers, setSoldiers] = useState(10_000);
  const [type, setType] = useState<ArmyType>('INFANTRY');
  const p = game.privateState;
  if (!p) return null;
  const cost = armyCost(soldiers, type);
  const affordable = p.resources.manpower >= cost.manpower && p.resources.industry >= cost.industry && p.resources.supplies >= cost.supplies;
  const queue = p.production.filter((o) => o.cityId === cityId);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div className="panel-title">Create army</div>
      <div className="field">
        <span className="label">Soldiers · {formatNumber(soldiers)}</span>
        <input type="range" min={PRODUCTION.MIN_SOLDIERS} max={PRODUCTION.MAX_SOLDIERS} step={500} value={soldiers} onChange={(e) => setSoldiers(Number(e.target.value))} data-testid="create-slider" />
      </div>
      <div className="segmented">
        {ARMY_TYPES.map((t) => (
          <button key={t} className={type === t ? 'on' : ''} title={ARMY_TYPE_STATS[t].description} onClick={() => setType(t)} style={{ fontSize: 11 }}>
            {ARMY_TYPE_STATS[t].label}
          </button>
        ))}
      </div>
      <dl className="kv">
        <dt>Manpower</dt>
        <dd style={{ color: p.resources.manpower < cost.manpower ? 'var(--red)' : undefined }}>{formatNumber(cost.manpower)}</dd>
        <dt>Industry</dt>
        <dd style={{ color: p.resources.industry < cost.industry ? 'var(--red)' : undefined }}>{formatNumber(cost.industry)}</dd>
        <dt>Supplies</dt>
        <dd style={{ color: p.resources.supplies < cost.supplies ? 'var(--red)' : undefined }}>{formatNumber(cost.supplies)}</dd>
        <dt>Time</dt>
        <dd>{Math.ceil(cost.seconds)}s</dd>
      </dl>
      <button className="btn primary" disabled={!affordable} onClick={() => void game.command({ type: 'CREATE_ARMY', cityId, soldiers, armyType: type })} data-testid="create-army">
        Create · {formatNumber(soldiers)}
      </button>
      {queue.map((o) => (
        <div key={o.id} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 14 }}>
            <span>
              {formatNumber(o.soldiers)} {ARMY_TYPE_STATS[o.type].label}
            </span>
            <button className="btn small ghost" onClick={() => void game.command({ type: 'CANCEL_PRODUCTION', orderId: o.id })}>
              Cancel
            </button>
          </div>
          <div className="bar">
            <div style={{ width: `${Math.min(100, (o.progress / o.total) * 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function TerritoryDetails({ game, id }: { game: GameClient; id: number }) {
  const r = game.replica;
  const t = r.map.territories[id];
  const owner = r.owners[id];
  const city = t.cityId !== null ? r.map.cities[t.cityId] : null;
  const isCapital = owner !== null && city !== null && r.nations.get(owner)?.capitalCity === city.id;
  const capture = r.captures.find((c) => c.territoryId === id);
  const garrison = new Map<string, number>();
  for (const u of r.units.values()) {
    const m = r.map;
    const cx = Math.floor(u.x / m.cellSize);
    const cy = Math.floor(u.y / m.cellSize);
    if (game.grids.territoryGrid[cy * m.cols + cx] === id) garrison.set(u.nation, (garrison.get(u.nation) ?? 0) + u.soldiers);
  }
  const canProduce = owner === game.you && city !== null && CITY_TYPE_STATS[city.type].canProduce;
  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <Flag nation={owner} height={28} />
        <div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 26, lineHeight: 1, color: 'var(--parchment)' }}>{t.name}</div>
          <div className="hint">
            {owner ? getNation(owner).name : 'Unclaimed land'}
            {city ? ` · ${isCapital ? 'Capital' : CITY_TYPE_STATS[city.type].label}` : ''}
          </div>
        </div>
      </div>
      <dl className="kv">
        <dt>Population</dt>
        <dd>{formatNumber(t.population)}</dd>
        <dt>Industry</dt>
        <dd>{t.industry}</dd>
        <dt>Resource</dt>
        <dd>{t.resource.toLowerCase()}</dd>
        <dt>Coastal</dt>
        <dd>{t.coastal ? 'yes' : 'no'}</dd>
      </dl>
      {capture && (
        <div className="field">
          <span className="label">
            Being captured by {getNation(capture.nation).name} · {Math.round(capture.progress * 100)}%
          </span>
          <div className="bar">
            <div style={{ width: `${capture.progress * 100}%`, background: getNation(capture.nation).color }} />
          </div>
        </div>
      )}
      <div className="panel-title">Garrison</div>
      {garrison.size ? (
        [...garrison.entries()].map(([n, s]) => (
          <div key={n} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Flag nation={n} height={14} />
            <span>{getNation(n).name}</span>
            <span className="num" style={{ marginLeft: 'auto' }}>
              {formatNumber(s)}
            </span>
          </div>
        ))
      ) : (
        <div className="hint">No armies stationed.</div>
      )}
      {canProduce && city && <ProductionPanel game={game} cityId={city.id} />}
      {owner === game.you && city && !canProduce && <div className="hint">Villages cannot raise armies — use a city or your capital.</div>}
    </>
  );
}

/** Right panel: details of whatever is selected. */
export function SelectionPanel({ game }: { game: GameClient }) {
  const sel = game.selection;
  if (sel.kind === 'none') return null;
  let body: React.ReactNode = null;
  if (sel.kind === 'units') {
    const units = game.selectedUnits();
    if (!units.length) return null;
    if (units.length === 1) body = <UnitDetails key={units[0].id} game={game} unit={units[0]} own />;
    else {
      const total = units.reduce((s, u) => s + u.soldiers, 0);
      body = (
        <>
          <div className="panel-title">{units.length} armies selected</div>
          <div className="big-number">{formatNumber(total)}</div>
          <div className="label">total soldiers</div>
          <div className="unit-list">
            {units
              .slice()
              .sort((a, b) => b.soldiers - a.soldiers)
              .map((u) => (
                <div key={u.id} className="unit-row" onClick={() => game.select({ kind: 'units', ids: [u.id] })}>
                  <Flag nation={u.nation} height={12} />
                  <span>{u.name}</span>
                  <span className={`status-pill ${u.status}`} style={{ fontSize: 10, padding: '0 4px' }}>
                    {u.status}
                  </span>
                  <span className="n">{formatNumber(u.soldiers)}</span>
                </div>
              ))}
          </div>
        </>
      );
    }
  } else if (sel.kind === 'enemy') {
    const u = game.replica.units.get(sel.id);
    if (!u) return null;
    const you = game.you;
    const rel = you ? getRelation(game.replica.diplomacy.relations, you, u.nation) : 'PEACE';
    body = (
      <>
        <UnitDetails game={game} unit={u} own={false} />
        {you && u.nation !== you && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className={`badge ${rel.toLowerCase()}`}>{rel}</span>
            {rel === 'PEACE' && (
              <button className="btn small danger" onClick={() => void game.command({ type: 'DIPLOMACY', action: 'DECLARE_WAR', target: u.nation })}>
                Declare war
              </button>
            )}
            {rel === 'WAR' && <span className="hint">Select your armies, then click this army to attack.</span>}
          </div>
        )}
      </>
    );
  } else if (sel.kind === 'territory') {
    body = <TerritoryDetails game={game} id={sel.id} />;
  }
  return (
    <div className="hud panel right-panel" data-testid="selection-panel">
      <button className="btn small ghost" style={{ position: 'absolute', top: 8, right: 8, minHeight: 22, padding: '0 7px' }} onClick={() => game.select({ kind: 'none' })} aria-label="Close">
        ✕
      </button>
      {body}
    </div>
  );
}
