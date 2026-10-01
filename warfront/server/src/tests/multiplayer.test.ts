import { CITY_TYPE_STATS, type UnitNet } from '@warfront/shared';
import assert from 'node:assert/strict';
import type { AddressInfo } from 'node:net';
import { after, before, test } from 'node:test';
import { createGameServer, type GameServer } from '../app';
import { TestClient } from './TestClient';

let server: GameServer;
let url = '';

before(async () => {
  server = createGameServer({ clientOrigins: [], clientDistCandidates: [] });
  await new Promise<void>((r) => server.httpServer.listen(0, '127.0.0.1', () => r()));
  url = `http://127.0.0.1:${(server.httpServer.address() as AddressInfo).port}`;
});

after(async () => {
  await server.close();
});

test('France vs Britain: create, join, produce, move, battle, capture, stay in sync, reject cheats', { timeout: 150_000 }, async () => {
  const a = new TestClient(url);
  const b = new TestClient(url);
  try {
    // ---- lobby
    const created = await a.call('room:create', {
      playerName: 'Player1',
      settings: { roomName: 'Waterloo', mapId: 'continental', maxPlayers: 2, aiCount: 0, speed: 4, victory: 'CONQUEST', startAtWar: true },
    });
    assert.ok(created.ok, 'room created');
    assert.match(created.code, /^[A-Z2-9]{6}$/);

    const joined = await b.call('room:join', { code: created.code.toLowerCase(), playerName: 'Player2' });
    assert.ok(joined.ok, 'friend joined with room code');

    assert.deepEqual(await a.call('lobby:nation', 'france'), { ok: true });
    const stolen = await b.call('lobby:nation', 'france');
    assert.equal(stolen.ok, false, 'a nation cannot be taken twice');
    assert.deepEqual(await b.call('lobby:nation', 'britain'), { ok: true });

    const notReady = await a.call('lobby:start');
    assert.equal(notReady.ok, false, 'cannot start before everyone is ready');
    const notHost = await b.call('lobby:start');
    assert.equal(notHost.ok, false, 'only the host can start');

    b.socket.emit('lobby:ready', true);
    await a.waitFor(() => a.room?.players.find((p) => p.name === 'Player2')?.ready, 3000, 'ready flag');
    assert.deepEqual(await a.call('lobby:start'), { ok: true });

    await a.waitFor(() => a.initialised && b.initialised, 15_000, 'game:init on both clients');
    assert.equal(a.replica.you, 'france');
    assert.equal(b.replica.you, 'britain');
    assert.equal(a.replica.units.size, b.replica.units.size, 'same starting armies');
    assert.ok(a.replica.units.size > 30, 'many armies on the map');

    const map = a.replica.map;
    const cityFor = (nation: string, towards: { x: number; y: number }) =>
      map.cities
        .filter((c) => a.replica.owners[c.territoryId] === nation && CITY_TYPE_STATS[c.type].canProduce)
        .sort((p, q) => Math.hypot(p.x - towards.x, p.y - towards.y) - Math.hypot(q.x - towards.x, q.y - towards.y))[0];
    const capital = (nation: string) => map.cities[a.replica.nations.get(nation)!.capitalCity!];
    const frenchCity = cityFor('france', capital('britain'));
    const britishCity = cityFor('britain', capital('france'));
    assert.ok(frenchCity && britishCity, 'production cities exist');

    // ---- production (server deducts resources and validates)
    const before = a.privateState!.resources.manpower;
    assert.deepEqual(await a.call('game:command', { type: 'CREATE_ARMY', cityId: frenchCity.id, soldiers: 30_000, armyType: 'INFANTRY' }), { ok: true });
    assert.deepEqual(await b.call('game:command', { type: 'CREATE_ARMY', cityId: britishCity.id, soldiers: 25_000, armyType: 'INFANTRY' }), { ok: true });
    await a.waitFor(() => a.privateState!.resources.manpower < before - 20_000, 3000, 'manpower deducted');

    // ---- cheat attempts are rejected by the server
    const frenchUnit = [...b.replica.units.values()].find((u) => u.nation === 'france')!;
    const cheats: [string, unknown][] = [
      ['999999 troops', { type: 'CREATE_ARMY', cityId: britishCity.id, soldiers: 999_999, armyType: 'INFANTRY' }],
      ['enemy city', { type: 'CREATE_ARMY', cityId: frenchCity.id, soldiers: 5_000, armyType: 'INFANTRY' }],
      ['move enemy army', { type: 'MOVE_UNIT', unitIds: [frenchUnit.id], x: 100, y: 100 }],
      ['split enemy army', { type: 'SPLIT_UNIT', unitId: frenchUnit.id, soldiers: 500 }],
      ['speed as guest', { type: 'SET_SPEED', speed: 4 }],
      ['unknown command', { type: 'SET_SOLDIERS', unitId: frenchUnit.id, soldiers: 999_999 }],
      ['NaN coordinates', { type: 'MOVE_UNIT', unitIds: [1], x: 'NaN', y: null }],
    ];
    for (const [label, cmd] of cheats) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const res = await b.call('game:command', cmd as any);
      assert.equal(res.ok, false, `cheat rejected: ${label}`);
    }
    const ownBritish = [...b.replica.units.values()].find((u) => u.nation === 'britain')!;
    const oversplit = await b.call('game:command', { type: 'SPLIT_UNIT', unitId: ownBritish.id, soldiers: ownBritish.soldiers + 1 });
    assert.equal(oversplit.ok, false, 'cannot split more soldiers than the army has');

    // ---- wait for the new armies
    const findNew = (c: TestClient, nation: string, size: number) =>
      [...c.replica.units.values()].find((u) => u.nation === nation && u.maxSoldiers === size && u.name.includes('Infantry'));
    const fr = await a.waitFor(() => findNew(a, 'france', 30_000), 20_000, 'French 30,000 army');
    const gb = await b.waitFor(() => findNew(b, 'britain', 25_000), 20_000, 'British 25,000 army');
    assert.equal(fr.soldiers, 30_000);
    assert.equal(gb.soldiers, 25_000);

    // ---- both move towards each other (France attacks, Britain marches out)
    const midX = (fr.x + gb.x) / 2;
    const midY = (fr.y + gb.y) / 2;
    assert.deepEqual(await a.call('game:command', { type: 'ATTACK', unitIds: [fr.id], targetUnitId: gb.id }), { ok: true });
    assert.deepEqual(await b.call('game:command', { type: 'MOVE_UNIT', unitIds: [gb.id], x: midX, y: midY }), { ok: true });

    // Armies really travel (no teleport): positions change gradually.
    const p0 = { x: fr.x, y: fr.y };
    await a.waitFor(() => {
      const u = a.replica.units.get(fr.id);
      return u && Math.hypot(u.x - p0.x, u.y - p0.y) > 5;
    }, 5000, 'French army moving');
    const step = Math.hypot(a.replica.units.get(fr.id)!.x - p0.x, a.replica.units.get(fr.id)!.y - p0.y);
    assert.ok(step < 120, `moved gradually, not teleported (${step.toFixed(1)})`);

    // ---- battle
    const battle = await a.waitFor(
      () => a.replica.battles.find((bt) => bt.sides.some((s) => s.nation === 'france') && bt.sides.some((s) => s.nation === 'britain')),
      60_000,
      'battle between France and Britain',
    );
    console.log(`  battle: ${battle.name}`, battle.sides);
    await a.waitFor(() => {
      const f = a.replica.units.get(fr.id);
      const g = a.replica.units.get(gb.id);
      return (!f || f.soldiers < 30_000) && (!g || g.soldiers < 25_000) && (f || g);
    }, 60_000, 'casualties on both sides');

    // Battle resolves: one army destroyed or routed.
    await a.waitFor(() => {
      const f = a.replica.units.get(fr.id);
      const g = a.replica.units.get(gb.id);
      return !f || !g || f.status === 'RETREATING' || g.status === 'RETREATING';
    }, 90_000, 'battle resolution');
    const f = a.replica.units.get(fr.id);
    const g = a.replica.units.get(gb.id);
    console.log(`  after battle: France ${f ? `${f.soldiers} ${f.status}` : 'destroyed'} | Britain ${g ? `${g.soldiers} ${g.status}` : 'destroyed'}`);
    const winner: { client: TestClient; unit: UnitNet; loser: string } =
      f && f.status !== 'RETREATING' ? { client: a, unit: f, loser: 'britain' } : { client: b, unit: g!, loser: 'france' };

    // ---- winner captures enemy territory
    const owners = winner.client.replica.owners;
    const target = map.territories
      .filter((t) => owners[t.id] === winner.loser)
      .sort((p, q) => Math.hypot(p.cx - winner.unit.x, p.cy - winner.unit.y) - Math.hypot(q.cx - winner.unit.x, q.cy - winner.unit.y))[0];
    await a.waitFor(() => !a.replica.units.get(winner.unit.id)?.battleId, 30_000, 'winner out of battle');
    assert.deepEqual(
      await winner.client.call('game:command', { type: 'MOVE_UNIT', unitIds: [winner.unit.id], x: target.cx, y: target.cy }),
      { ok: true },
    );
    const capturer = winner.unit.nation;
    await a.waitFor(() => a.replica.owners.filter((o) => o === capturer).length > owners.filter((o) => o === capturer).length || a.replica.owners[target.id] === capturer, 90_000, 'territory captured');
    console.log(`  ${capturer} captured territory; events:`, a.events.filter((e) => e.kind === 'TERRITORY_CAPTURED').map((e) => e.text).slice(-3));

    // ---- both browsers see the same world
    await a.waitFor(() => a.replica.tick === b.replica.tick && a.replica.tick > 0, 5000, 'same tick');
    assert.deepEqual(a.replica.owners, b.replica.owners, 'territory owners identical');
    const strip = (u: UnitNet) => `${u.id}:${u.nation}:${u.soldiers}:${u.x}:${u.y}:${u.status}`;
    assert.deepEqual([...a.replica.units.values()].map(strip).sort(), [...b.replica.units.values()].map(strip).sort(), 'units identical');
    assert.ok(a.events.some((e) => e.kind === 'BATTLE_STARTED'), 'battle event broadcast');

    // ---- chat with spam protection
    assert.deepEqual(await a.call('chat:send', '공격 시작한다'), { ok: true });
    const dup = await a.call('chat:send', '공격 시작한다');
    assert.equal(dup.ok, false, 'duplicate message rejected');
    const long = await b.call('chat:send', 'x'.repeat(1000));
    assert.ok(long.ok);
    await b.waitFor(() => b.chat.some((m) => m.text === '공격 시작한다'), 2000, 'chat delivered');
    assert.ok(b.chat.every((m) => m.text.length <= 200), 'chat length limited');
  } finally {
    a.close();
    b.close();
  }
});
