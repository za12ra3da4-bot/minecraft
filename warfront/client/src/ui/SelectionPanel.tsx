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
import { RELATION_KO, RESOURCE_KO, STATUS_KO } from './labels';

function territoryName(game: GameClient, x: number, y: number): string {
  const m = game.replica.map;
  const cx = Math.floor(x / m.cellSize);
  const cy = Math.floor(y / m.cellSize);
  const t = cx >= 0 && cy >= 0 && cx < m.cols && cy < m.rows ? game.grids.territoryGrid[cy * m.cols + cx] : -1;
  return t >= 0 ? m.territories[t].name : '바다';
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
        <div className="label">명 (최대 {formatNumber(unit.maxSoldiers)}명)</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className={`status-pill ${unit.status}`}>{STATUS_KO[unit.status]}</span>
        <span className="hint">위치: {territoryName(game, unit.x, unit.y)}</span>
      </div>
      <dl className="kv">
        <dt>사기</dt>
        <dd>
          <div className="bar" style={{ marginTop: 4 }}>
            <div style={{ width: `${unit.morale}%`, background: unit.morale > 60 ? '#7fbf5a' : unit.morale > 30 ? '#e2b33c' : '#d6493a' }} />
          </div>
        </dd>
        <dt>공격력</dt>
        <dd>{unit.attack.toFixed(2)}</dd>
        <dt>방어력</dt>
        <dd>{unit.defense.toFixed(2)}</dd>
        <dt>속도</dt>
        <dd>{unit.speed.toFixed(0)}</dd>
        <dt>목적지</dt>
        <dd>{target ? `⚔ ${getNation(target.nation).adjective} ${target.name}` : (destination ?? '—')}</dd>
      </dl>
      {own && unit.battleId === null && maxSplit >= UNIT.MIN_SPLIT && (
        <div className="field">
          <span className="label">
            원하는 만큼 나누기 · {formatNumber(splitValue)} / {formatNumber(unit.soldiers)}명
          </span>
          <input type="range" min={UNIT.MIN_SPLIT} max={maxSplit} step={100} value={splitValue} onChange={(e) => setSplit(Number(e.target.value))} data-testid="split-slider" />
          <button className="btn small" onClick={() => void game.command({ type: 'SPLIT_UNIT', unitId: unit.id, soldiers: splitValue })} data-testid="split">
            ✂ 이만큼 떼어내기
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
      <div className="panel-title">⚑ 군대 만들기</div>
      <div className="quick-sizes">
        {[5_000, 10_000, 20_000, 30_000].map((n) => (
          <button key={n} className={`btn small${soldiers === n ? ' active' : ''}`} onClick={() => setSoldiers(n)}>
            {n / 10_000 >= 1 ? `${n / 10_000}만` : `${n / 1_000}천`}명
          </button>
        ))}
      </div>
      <div className="field">
        <span className="label">병력 · {formatNumber(soldiers)}명</span>
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
        <dt>인력</dt>
        <dd style={{ color: p.resources.manpower < cost.manpower ? 'var(--red)' : undefined }}>{formatNumber(cost.manpower)}</dd>
        <dt>산업</dt>
        <dd style={{ color: p.resources.industry < cost.industry ? 'var(--red)' : undefined }}>{formatNumber(cost.industry)}</dd>
        <dt>보급</dt>
        <dd style={{ color: p.resources.supplies < cost.supplies ? 'var(--red)' : undefined }}>{formatNumber(cost.supplies)}</dd>
        <dt>걸리는 시간</dt>
        <dd>{Math.ceil(cost.seconds)}초</dd>
      </dl>
      <button className="btn primary" disabled={!affordable} onClick={() => void game.command({ type: 'CREATE_ARMY', cityId, soldiers, armyType: type })} data-testid="create-army">
        {affordable ? `생산 · ${formatNumber(soldiers)}명` : '자원이 부족합니다'}
      </button>
      {queue.map((o) => (
        <div key={o.id} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 14 }}>
            <span>
              {formatNumber(o.soldiers)}명 {ARMY_TYPE_STATS[o.type].label}
            </span>
            <button className="btn small ghost" onClick={() => void game.command({ type: 'CANCEL_PRODUCTION', orderId: o.id })}>
              취소
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
            {owner ? getNation(owner).name : '주인 없는 땅'}
            {city ? ` · ${isCapital ? '수도' : CITY_TYPE_STATS[city.type].label}` : ''}
          </div>
        </div>
      </div>
      <dl className="kv">
        <dt>인구</dt>
        <dd>{formatNumber(t.population)}</dd>
        <dt>산업</dt>
        <dd>{t.industry}</dd>
        <dt>자원</dt>
        <dd>{RESOURCE_KO[t.resource]}</dd>
        <dt>해안</dt>
        <dd>{t.coastal ? '예' : '아니오'}</dd>
      </dl>
      {capture && (
        <div className="field">
          <span className="label">
            {getNation(capture.nation).name}이(가) 점령 중 · {Math.round(capture.progress * 100)}%
          </span>
          <div className="bar">
            <div style={{ width: `${capture.progress * 100}%`, background: getNation(capture.nation).color }} />
          </div>
        </div>
      )}
      <div className="panel-title">주둔 병력</div>
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
        <div className="hint">주둔한 부대가 없습니다.</div>
      )}
      {canProduce && city && <ProductionPanel game={game} cityId={city.id} />}
      {owner === game.you && city && !canProduce && <div className="hint">마을에서는 군대를 만들 수 없습니다 — 도시(■)나 수도(★)를 누르세요.</div>}
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
          <div className="panel-title">부대 {units.length}개 선택됨</div>
          <div className="big-number">{formatNumber(total)}</div>
          <div className="label">명 (총 병력)</div>
          <div className="unit-list">
            {units
              .slice()
              .sort((a, b) => b.soldiers - a.soldiers)
              .map((u) => (
                <div key={u.id} className="unit-row" onClick={() => game.select({ kind: 'units', ids: [u.id] })}>
                  <Flag nation={u.nation} height={12} />
                  <span>{u.name}</span>
                  <span className={`status-pill ${u.status}`} style={{ fontSize: 10, padding: '0 4px' }}>
                    {STATUS_KO[u.status]}
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
            <span className={`badge ${rel.toLowerCase()}`}>{RELATION_KO[rel]}</span>
            {rel === 'PEACE' && (
              <button className="btn small danger" onClick={() => void game.command({ type: 'DIPLOMACY', action: 'DECLARE_WAR', target: u.nation })}>
                ⚔ 선전포고
              </button>
            )}
            {rel === 'WAR' && <span className="hint">내 부대를 고른 뒤 이 부대를 클릭하면 공격합니다.</span>}
          </div>
        )}
      </>
    );
  } else if (sel.kind === 'territory') {
    body = <TerritoryDetails game={game} id={sel.id} />;
  }
  return (
    <div className="hud panel right-panel" data-testid="selection-panel">
      <button className="btn small ghost" style={{ position: 'absolute', top: 8, right: 8, minHeight: 22, padding: '0 7px' }} onClick={() => game.select({ kind: 'none' })} aria-label="닫기">
        ✕
      </button>
      {body}
    </div>
  );
}
