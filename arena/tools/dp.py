"""데이터팩 생성: bg_arena

 bg:load / bg:tick
 bg:tele/*    경고 장판 (매크로) — Skript 가 function bg:tele/circle {x:..,y:..,...} 로 호출
 bg:map/*     맵 건설 (여러 틱에 나눠 fill strict) · 장식 디스플레이 소환/정리
 bg:boss/*    보스 파츠 소환·위치 동기화·애니메이션 (bossgen 이 생성)
"""
import json
import math
import os

import numpy as np

import blocks as B
import decor

NS = "bg"
PACK_FMT = {"pack_format": 94, "min_format": 88, "max_format": 101}


def w(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(lines, (list, tuple)):
        lines = "\n".join(lines) + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(lines)


def item(model, extra=""):
    cd = f',"minecraft:custom_data":{{{extra}}}' if extra else ""
    return f'item:{{id:"minecraft:paper",count:1,components:{{"minecraft:item_model":"{model}"{cd}}}}}'


def tf(tx=0, ty=0, tz=0, sx=1, sy=1, sz=1, lrot=(0, 0, 0, 1)):
    return (f"transformation:{{left_rotation:[{lrot[0]}f,{lrot[1]}f,{lrot[2]}f,{lrot[3]}f],right_rotation:[0f,0f,0f,1f],"
            f"translation:[{tx}f,{ty}f,{tz}f],scale:[{sx}f,{sy}f,{sz}f]}}")


BASE = 'item_display:"none",brightness:{sky:15,block:15},view_range:4f,shadow_radius:0f,teleport_duration:2'


def _sm(extra_tags, model, cdata, t, rot=False, extra=""):
    """장판 소환 명령 한 줄 (매크로)"""
    tags = 'Tags:["bg","bg_tg","bgt_$(id)"' + extra_tags + ']'
    r = ",Rotation:[$(yaw)f,0f]" if rot else ""
    return "$summon item_display $(x) $(y) $(z) {" + tags + r + "," + item(model, cdata) + "," + BASE + extra + "," + t + "}"


def tele_functions(fdir):
    T = os.path.join(fdir, "tele")
    G = ',"bg_tg_grow"'
    A = ',"bg_tg_arc"'
    life = ["$scoreboard players set @e[tag=bgt_$(id)] bg_life $(t)", "$scoreboard players set @e[tag=bgt_$(id)] bg_age 0"]
    w(os.path.join(T, "circle.mcfunction"), [
        "# 원형 장판: {x,y,z,d(지름),t(틱),id}",
        _sm("", "bg:tele/circle_ring", "flash:'circle_flash'", tf(0, 0.03, 0, "$(d)", 1, "$(d)")),
        _sm(G, "bg:tele/circle_fill", "kill:1b,gx:$(d),gz:$(d),ty:0.04,tz:0,t:$(t)", tf(0, 0.04, 0, 0.01, 1, 0.01)),
        _sm(A, "bg:tele/circle_arc_0", "kill:1b,pre:'circle_arc'", tf(0, 0.05, 0, "$(d)", 1, "$(d)")),
        *life,
        "$scoreboard players set @e[tag=bgt_$(id)] bg_frames 20",
        "$scoreboard players set @e[tag=bgt_$(id)] bg_last -1",
    ])
    w(os.path.join(T, "rect.mcfunction"), [
        "# 직선 장판: {x,y,z,yaw,wd,l,hl(=l/2),hz(=l-wd/2),t,id}",
        _sm("", "bg:tele/rect_base", "flash:'rect_flash'", tf(0, 0.03, "$(hl)", "$(wd)", 1, "$(l)"), rot=True),
        _sm(G, "bg:tele/rect_fill", "kill:1b,gx:$(wd),gz:$(l),ty:0.04,tz:$(hl),t:$(t)", tf(0, 0.04, 0, "$(wd)", 1, 0.01), rot=True),
        _sm("", "bg:tele/rect_head", "kill:1b", tf(0, 0.05, "$(hz)", "$(wd)", 1, "$(wd)"), rot=True),
        *life,
    ])
    w(os.path.join(T, "cone.mcfunction"), [
        "# 부채꼴 장판 (꼭짓점=위치): {x,y,z,yaw,deg(60|90|120),d(반지름x2),t,id}",
        _sm("", "bg:tele/cone$(deg)_base", "flash:'cone$(deg)_flash'", tf(0, 0.03, 0, "$(d)", 1, "$(d)"), rot=True),
        _sm(G, "bg:tele/cone$(deg)_fill", "kill:1b,gx:$(d),gz:$(d),ty:0.04,tz:0,t:$(t)", tf(0, 0.04, 0, 0.01, 1, 0.01), rot=True),
        *life,
    ])
    w(os.path.join(T, "donut.mcfunction"), [
        "# 도넛 장판 (안쪽 안전): {x,y,z,d,t,id}",
        _sm("", "bg:tele/donut_base", "flash:'donut_flash'", tf(0, 0.03, 0, "$(d)", 1, "$(d)")),
        _sm(A, "bg:tele/donut_fill_0", "kill:1b,pre:'donut_fill'", tf(0, 0.04, 0, "$(d)", 1, "$(d)")),
        *life,
        "$scoreboard players set @e[tag=bgt_$(id)] bg_frames 12",
        "$scoreboard players set @e[tag=bgt_$(id)] bg_last -1",
    ])
    w(os.path.join(T, "decal.mcfunction"), [
        "# 바닥 데칼: {x,y,z,m,d,t,yaw,id}",
        _sm("", "bg:tele/$(m)", "kill:1b", tf(0, 0.06, 0, "$(d)", 1, "$(d)"), rot=True),
        *life,
    ])
    w(os.path.join(T, "rune.mcfunction"), [
        "# 회전하는 마법진: {x,y,z,m,d,t,id}",
        _sm(',"bg_spin_fast"', "bg:tele/$(m)", "kill:1b", tf(0, 0.035, 0, "$(d)", 1, "$(d)")),
        *life,
    ])
    w(os.path.join(T, "mark.mcfunction"), [
        "# 머리 위 ! 표식 (빌보드): {x,y,z,t,id}",
        _sm("", "bg:tele/mark_head", "kill:1b", tf(0, 0, 0, 1.3, 1.3, 1.3), extra=',billboard:"vertical"'),
        *life,
    ])
    w(os.path.join(T, "move.mcfunction"), ["# 장판 따라가기: {id,x,y,z}", "$tp @e[type=item_display,tag=bgt_$(id)] $(x) $(y) $(z)"])
    w(os.path.join(T, "clear.mcfunction"), ["$kill @e[type=item_display,tag=bgt_$(id)]"])
    w(os.path.join(T, "clear_all.mcfunction"), ["kill @e[type=item_display,tag=bg_tg]"])
    w(os.path.join(T, "tick.mcfunction"), [
        "scoreboard players add @s bg_age 1",
        'execute if entity @s[tag=bg_tg_grow] run function bg:tele/grow with entity @s item.components."minecraft:custom_data"',
        "execute if entity @s[tag=bg_tg_arc] run function bg:tele/arc",
        "execute if score @s bg_age >= @s bg_life run function bg:tele/expire",
    ])
    w(os.path.join(T, "grow.mcfunction"), [
        "tag @s remove bg_tg_grow",
        "$data merge entity @s {start_interpolation:0,interpolation_duration:$(t),transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,$(ty)f,$(tz)f],scale:[$(gx)f,1f,$(gz)f]}}",
    ])
    w(os.path.join(T, "arc.mcfunction"), [
        "scoreboard players operation #f bg_tmp = @s bg_age",
        "scoreboard players operation #f bg_tmp *= @s bg_frames",
        "scoreboard players operation #f bg_tmp /= @s bg_life",
        "scoreboard players operation #m bg_tmp = @s bg_frames",
        "scoreboard players remove #m bg_tmp 1",
        "execute if score #f bg_tmp > #m bg_tmp run scoreboard players operation #f bg_tmp = #m bg_tmp",
        "execute if score #f bg_tmp = @s bg_last run return 0",
        "scoreboard players operation @s bg_last = #f bg_tmp",
        "execute store result storage bg:tmp f int 1 run scoreboard players get #f bg_tmp",
        'data modify storage bg:tmp pre set from entity @s item.components."minecraft:custom_data".pre',
        "function bg:tele/arc_set with storage bg:tmp",
    ])
    w(os.path.join(T, "arc_set.mcfunction"), ['$data modify entity @s item.components."minecraft:item_model" set value "bg:tele/$(pre)_$(f)"'])
    w(os.path.join(T, "expire.mcfunction"), [
        'execute if data entity @s item.components."minecraft:custom_data".kill run return run kill @s',
        "execute if entity @s[tag=bg_tg_dying] run return run kill @s",
        "tag @s add bg_tg_dying",
        "scoreboard players add @s bg_life 5",
        'function bg:tele/flash with entity @s item.components."minecraft:custom_data"',
    ])
    w(os.path.join(T, "flash.mcfunction"), ['$data modify entity @s item.components."minecraft:item_model" set value "bg:tele/$(flash)"'])


def core_functions(dp_root):
    F = os.path.join(dp_root, "data", NS, "function")
    w(os.path.join(dp_root, "pack.mcmeta"), json.dumps({"pack": {"description": "신들의 전장 — 4팀 PvP + 미니보스", **PACK_FMT}}, ensure_ascii=False, indent=1))
    w(os.path.join(dp_root, "data", "minecraft", "tags", "function", "load.json"), json.dumps({"values": [f"{NS}:load"]}))
    w(os.path.join(dp_root, "data", "minecraft", "tags", "function", "tick.json"), json.dumps({"values": [f"{NS}:tick"]}))
    w(os.path.join(F, "load.mcfunction"), [
        "scoreboard objectives add bg_age dummy",
        "scoreboard objectives add bg_life dummy",
        "scoreboard objectives add bg_frames dummy",
        "scoreboard objectives add bg_last dummy",
        "scoreboard objectives add bg_tmp dummy",
        "scoreboard objectives add bg_build dummy",
        "execute unless data storage bg:map origin run data merge storage bg:map {origin:{x:-128,y:40,z:-128}}",
    ])
    w(os.path.join(F, "tick.mcfunction"), [
        "execute as @e[type=item_display,tag=bg_tg] run function bg:tele/tick",
        "execute as @e[type=!player,tag=bg_spin_fast] at @s run tp @s ~ ~ ~ ~3 ~",
        "execute as @e[type=!player,tag=bg_spin] at @s run tp @s ~ ~ ~ ~0.8 ~",
        # 상점 상인 클릭 (interaction) → 누른 사람에게 태그 → Skript 가 상점을 연다
        "execute as @e[type=interaction,tag=bg_shopnpc] if data entity @s interaction on target run tag @s add bg_wantshop",
        "execute as @e[type=interaction,tag=bg_shopnpc] if data entity @s attack on attacker run tag @s add bg_wantshop",
        "execute as @e[type=interaction,tag=bg_shopnpc] run data remove entity @s interaction",
        "execute as @e[type=interaction,tag=bg_shopnpc] run data remove entity @s attack",
        "execute if score #run bg_build matches 1 run function bg:map/build/step with storage bg:map origin",
    ])
    tele_functions(F)


# ─────────────────────────────────────────────────────────────────────────────
#  맵 건설
# ─────────────────────────────────────────────────────────────────────────────
def greedy_boxes(vox, max_vol=32768):
    """같은 블록끼리 3D 박스로 합치기 → [(pid, x0,y0,z0,x1,y1,z1)]"""
    X, Y, Z = vox.shape
    done = np.zeros(vox.shape, bool)
    out = []
    nz = np.argwhere(vox != 0)
    order = np.lexsort((nz[:, 0], nz[:, 2], nz[:, 1]))     # y, z, x 순
    for idx in order:
        x, y, z = nz[idx]
        if done[x, y, z]:
            continue
        p = vox[x, y, z]
        x1 = x
        while x1 + 1 < X and vox[x1 + 1, y, z] == p and not done[x1 + 1, y, z] and (x1 + 2 - x) <= 256:
            x1 += 1
        z1 = z
        while z1 + 1 < Z and (z1 + 2 - z) * (x1 - x + 1) <= max_vol:
            seg = vox[x:x1 + 1, y, z1 + 1]
            if np.all(seg == p) and not done[x:x1 + 1, y, z1 + 1].any():
                z1 += 1
            else:
                break
        y1 = y
        while y1 + 1 < Y and (y1 + 2 - y) * (x1 - x + 1) * (z1 - z + 1) <= max_vol:
            blk = vox[x:x1 + 1, y1 + 1, z:z1 + 1]
            if np.all(blk == p) and not done[x:x1 + 1, y1 + 1, z:z1 + 1].any():
                y1 += 1
            else:
                break
        done[x:x1 + 1, y:y1 + 1, z:z1 + 1] = True
        out.append((int(p), int(x), int(y), int(z), int(x1), int(y1), int(z1)))
    return out


def full_state(s):
    """블록 상태 문자열 → 명령용 (minecraft: 접두)"""
    return "minecraft:" + s


def map_functions(dp_root, world, per_part=350):
    F = os.path.join(dp_root, "data", NS, "function", "map")
    boxes = greedy_boxes(world.vox)
    SX, SY, SZ = world.size
    cmds = []
    # 1) 비우기 (위에서 아래로)
    step = 16
    for x0 in range(0, SX, 32):
        for z0 in range(0, SZ, 32):
            for y0 in range(SY - step, -1, -step):
                cmds.append(f"fill ~{x0} ~{y0} ~{z0} ~{x0 + 31} ~{y0 + step - 1} ~{z0 + 31} minecraft:air strict")
    # 2) 블록 (아래에서 위로, 부착물은 나중에)
    def late(pid):
        d = B.describe(world.pal[pid])
        return d.kind in (3,) or (d.kind == 1 and len(d.boxes) == 1 and d.boxes[0] != (0, 0, 0, 1, 1, 1) and d.boxes[0][4] - d.boxes[0][1] < 0.7)
    lates = {pid: late(pid) for pid in set(b[0] for b in boxes)}
    boxes.sort(key=lambda b: (lates[b[0]], b[2]))
    for pid, x0, y0, z0, x1, y1, z1 in boxes:
        st = full_state(world.pal[pid])
        if (x0, y0, z0) == (x1, y1, z1):
            cmds.append(f"setblock ~{x0} ~{y0} ~{z0} {st} strict")
        else:
            cmds.append(f"fill ~{x0} ~{y0} ~{z0} ~{x1} ~{y1} ~{z1} {st} strict")
    parts = [cmds[i:i + per_part] for i in range(0, len(cmds), per_part)]
    for i, p in enumerate(parts):
        w(os.path.join(F, "build", "p", f"{i}.mcfunction"), p)
    n = len(parts)
    # 강제 로드 (256 청크 제한 → 4등분)
    fl = []
    for qx in (0, SX // 2):
        for qz in (0, SZ // 2):
            fl.append(f"$forceload add ~{qx} ~{qz} ~{qx + SX // 2 - 1} ~{qz + SZ // 2 - 1}")
    w(os.path.join(F, "build", "start.mcfunction"), [
        "# 맵 건설 시작: 원점은 storage bg:map origin (기본 -128 40 -128)",
        "#   바꾸려면: data merge storage bg:map {origin:{x:0,y:40,z:0}}",
        "function bg:map/build/forceload with storage bg:map origin",
        "scoreboard players set #part bg_build 0",
        "scoreboard players set #run bg_build 1",
        f'tellraw @a [{{"text":"[전장] ","color":"gold"}},{{"text":"맵 건설 시작 ({n}단계, 약 {n // 20 + 1}초)","color":"yellow"}}]',
    ])
    w(os.path.join(F, "build", "forceload.mcfunction"), [l.replace("~", "$(x)", 1) if False else l for l in
                                                           [f"$execute positioned $(x) $(y) $(z) run forceload add ~{qx} ~{qz} ~{qx + SX // 2 - 1} ~{qz + SZ // 2 - 1}"
                                                            for qx in (0, SX // 2) for qz in (0, SZ // 2)]])
    w(os.path.join(F, "build", "unload.mcfunction"), [f"$execute positioned $(x) $(y) $(z) run forceload remove ~{qx} ~{qz} ~{qx + SX // 2 - 1} ~{qz + SZ // 2 - 1}"
                                                      for qx in (0, SX // 2) for qz in (0, SZ // 2)])
    w(os.path.join(F, "build", "step.mcfunction"), [
        "execute store result storage bg:map origin.part int 1 run scoreboard players get #part bg_build",
        "function bg:map/build/run with storage bg:map origin",
        "scoreboard players add #part bg_build 1",
        f"execute if score #part bg_build matches {n}.. run function bg:map/build/done",
    ])
    w(os.path.join(F, "build", "run.mcfunction"), ["$execute positioned $(x) $(y) $(z) run function bg:map/build/p/$(part)"])
    # 맵 경계: 보이지 않는 벽(barrier) — 네 면, 높이 전체 (fill 한 번에 32768 칸 이하로 나눔)
    bl = []
    for (x0, z0, x1, z1) in ((-1, -1, -1, 127), (-1, 128, -1, SZ), (SX, -1, SX, 127), (SX, 128, SX, SZ),
                             (0, -1, 127, -1), (128, -1, SX - 1, -1), (0, SZ, 127, SZ), (128, SZ, SX - 1, SZ)):
        bl.append(f"$execute positioned $(x) $(y) $(z) run fill ~{x0} ~0 ~{z0} ~{x1} ~{SY - 1} ~{z1} barrier replace air")
    w(os.path.join(F, "border.mcfunction"), bl)
    w(os.path.join(F, "build", "done.mcfunction"), [
        "scoreboard players set #run bg_build 0",
        "function bg:map/border with storage bg:map origin",
        "function bg:map/decor",
        "function bg:map/build/unload with storage bg:map origin",
        'tellraw @a [{"text":"[전장] ","color":"gold"},{"text":"맵 건설 완료! /전장 자동팀 → /전장 시작","color":"green"}]',
    ])
    return len(cmds), n


def quat_yaw_tilt(yaw, tilt=0.0, tilt_axis="x"):
    """left_rotation 쿼터니언: yaw(도, Y축) · tilt(도)"""
    def q(axis, deg):
        a = math.radians(deg) / 2
        s = math.sin(a)
        return {"x": (s, 0, 0, math.cos(a)), "y": (0, s, 0, math.cos(a)), "z": (0, 0, s, math.cos(a))}[axis]

    def mul(a, b):
        ax, ay, az, aw = a; bx, by, bz, bw = b
        return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)
    r = mul(q("y", -yaw), q(tilt_axis, tilt))
    return tuple(round(v, 5) for v in r)


def qrot(q, v):
    """쿼터니언 (x,y,z,w) 로 벡터 회전"""
    x, y, z, w = q
    u = np.array([x, y, z]); v = np.array(v, float)
    return tuple(2 * np.dot(u, v) * u + (w * w - np.dot(u, u)) * v + 2 * w * np.cross(u, v))


# ── 맵 장식 = 마인크래프트 기본 아이템 · 갑옷 거치대 (리소스팩 없이 보임)
TEAM_DYE = {"red": "red", "blue": "blue", "green": "lime", "yellow": "yellow"}
TEAM_PAT = {"red": [("cross", "yellow"), ("border", "yellow")], "blue": [("triangles_top", "white"), ("border", "yellow")],
            "green": [("flower", "yellow"), ("border", "yellow")], "yellow": [("rhombus", "red"), ("border", "black")]}


def _pats(lst):
    return "[" + ",".join(f'{{pattern:"minecraft:{p}",color:"{c}"}}' for p, c in lst) + "]"


def _banner(color, pats):
    return f'item:{{id:"minecraft:{color}_banner",count:1,components:{{"minecraft:banner_patterns":{_pats(pats)}}}}}'


def _shield(color, pats):
    return f'item:{{id:"minecraft:shield",count:1,components:{{"minecraft:base_color":"{color}","minecraft:banner_patterns":{_pats(pats)}}}}}'


def _it(i):
    return f'item:{{id:"minecraft:{i}",count:1}}'


ALTAR_ITEM = {"ares": "fire_charge", "athena": "heart_of_the_sea", "hermes": "feather", "demeter": "enchanted_golden_apple"}
SUMMON_GLASS = {"talos": "orange", "sphinx": "light_blue", "ladon": "lime", "cyclops": "brown"}
STATUE_GEAR = {
    "hoplite": ("iron_helmet", "iron_chestplate", "iron_leggings", "iron_boots", "iron_sword", "shield", 2.4),
    "hoplite_broken": ("chainmail_helmet", "chainmail_chestplate", None, None, "stone_sword", None, 2.0),
    "god_ares": ("netherite_helmet", "netherite_chestplate", "netherite_leggings", "netherite_boots", "netherite_sword", "shield", 2.6),
    "god_athena": ("diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots", "trident", "shield", 2.6),
    "god_hermes": ("chainmail_helmet", "chainmail_chestplate", "chainmail_leggings", "golden_boots", "bow", "feather", 2.4),
    "god_demeter": ("golden_helmet", "golden_chestplate", "golden_leggings", "golden_boots", "golden_hoe", "wheat", 2.6),
}


def _quat_yaw_roll(yaw, roll):
    def q(axis, deg):
        h = math.radians(deg) / 2
        s_, c_ = math.sin(h), math.cos(h)
        return {"y": (0, s_, 0, c_), "z": (0, 0, s_, c_)}[axis]

    def mul(a, b):
        ax, ay, az, aw = a; bx, by, bz, bw = b
        return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)
    return tuple(round(v, 5) for v in mul(q("y", -yaw), q("z", roll)))


def _solid(name):
    return name != "air" and not any(k in name for k in ("grass", "fern", "flower", "torch", "lantern", "carpet", "snow", "button",
                                                            "rail", "sapling", "vine", "water", "lava", "fence", "wall", "chain", "pane", "bars"))


def find_spot(world, c, rmin, rmax, avoid, dy=(0, -1, 1)):
    """c 주변에서 발 디딜 곳(아래 단단, 위 3칸 비어 있음, 옆 1칸도 비어 있음) 중 c 에서 rmin~rmax, 가장 가까운 곳"""
    import math as _m
    cx, cy, cz = c
    best = None
    for r2 in range(int(rmin * 2), int(rmax * 2) + 1):
        r = r2 / 2
        for i in range(48):
            a = i / 48 * 2 * _m.pi
            x = int(_m.floor(cx + _m.cos(a) * r)); z = int(_m.floor(cz + _m.sin(a) * r))
            if any((ax - (x + 0.5)) ** 2 + (az - (z + 0.5)) ** 2 < ar * ar for ax, az, ar in avoid):
                continue
            for d in dy:
                y = int(_m.floor(cy)) + d
                try:
                    if not _solid(world.pal[world.vox[x, y - 1, z]]):
                        continue
                    ok = True
                    for ox in (-1, 0, 1):
                        for oz in (-1, 0, 1):
                            for oy in (0, 1, 2):
                                if world.pal[world.vox[x + ox, y + oy, z + oz]] != "air":
                                    ok = False
                    if ok:
                        return (x + 0.5, y, z + 0.5)
                except IndexError:
                    pass
    return best


def npc_and_class_lines(world, bdkit, bdmodels):
    import math as _m
    at = "$execute positioned $(x) $(y) $(z) run summon"
    out = []
    mk = world.markers

    def P(name):
        return mk[name]["pos"] if name in mk else None

    def text(x, y, z, parts, scale=1.5):
        comp = "[" + ",".join('{text:"%s",color:"%s",bold:%s}' % (t, c, "true" if b else "false") for t, c, b in parts) + "]"
        return (f'{at} text_display ~{x - 0.5:.3f} ~{y:.3f} ~{z - 0.5:.3f} {{Tags:["bg","bg_deco"],text:{comp},billboard:"center",'
                f'shadow:1b,view_range:0.5f,brightness:{{sky:15,block:15}},transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],'
                f'translation:[0f,0f,0f],scale:[{scale}f,{scale}f,{scale}f]}}}}')

    def npc(pos, face_to):
        x, y, z = pos
        yaw = _m.degrees(_m.atan2(-(face_to[0] - x), face_to[2] - z))
        mdl = bdmodels.merchant()
        out.extend(bdkit.summon_lines(mdl, at, x - 0.5, y, z - 0.5, yaw, 1.0, ['"bg"', '"bg_deco"'], view=0.8))
        # 클릭 판정: 상인 + 좌판
        a = _m.radians(-yaw)
        sx, sz = 15 / 16, 0.5 / 16
        wx = x + _m.cos(a) * sx + _m.sin(a) * sz; wz = z - _m.sin(a) * sx + _m.cos(a) * sz
        for (ix, iz, wd) in ((x, z, 1.3), (wx, wz, 1.1)):
            out.append(f'{at} interaction ~{ix - 0.5:.3f} ~{y:.3f} ~{iz - 0.5:.3f} {{Tags:["bg","bg_deco","bg_shopnpc"],width:{wd}f,height:2.4f,response:1b}}')
        out.append(text(x, y + 2.55, z, [("상점", "gold", True)], 1.6))
        out.append(text(x, y + 2.25, z, [("우클릭해서 열기", "yellow", False)], 1.0))

    for t in ("red", "blue", "green", "yellow"):
        sp = P(f"base_{t}_spawn_0")
        if not sp:
            continue
        avoid = [(mk[n]["pos"][0], mk[n]["pos"][2], 2.2) for n in mk if n.startswith(f"base_{t}_class_") or n.startswith(f"base_{t}_spawn_")]
        if P(f"base_{t}_beacon"):
            b = P(f"base_{t}_beacon"); avoid.append((b[0], b[2], 3.0))
        # 병과 발판 줄 끝에 이어서: [상인] [전사][궁수][수호자]
        spot = None
        c0, c1 = P(f"base_{t}_class_0"), P(f"base_{t}_class_1")
        if c0 and c1:
            dx, dz = c0[0] - c1[0], c0[2] - c1[2]
            L = (dx * dx + dz * dz) ** 0.5 or 1
            want = (c0[0] + dx / L * 5.5, sp[1], c0[2] + dz / L * 5.5)
            spot = find_spot(world, want, 0, 3, [(a, b, 1.6) for a, b, _ in avoid])
            if spot is None:
                want = (c1[0] - dx / L * 17.5, sp[1], c1[2] - dz / L * 17.5)
                spot = find_spot(world, want, 0, 3, [(a, b, 1.6) for a, b, _ in avoid])
        if spot is None:
            spot = find_spot(world, sp, 4, 9, avoid)
        if spot:
            npc(spot, sp)
        else:
            print(f"[npc] {t} 본진 상인 자리를 못 찾음")
        # 병과 발판 표식
        names = [("전사", "쇠사슬 · 검 · 활"), ("궁수", "활 · 화살 24"), ("수호자", "철 흉갑 · 도끼")]
        for k in range(3):
            c = P(f"base_{t}_class_{k}")
            if not c:
                continue
            x, y, z = c
            ic = bdmodels.class_icon(k)
            out.extend(bdkit.summon_lines(ic, at, x - 0.5, y + 1.4, z - 0.5, 0.0, 1.0, ['"bg"', '"bg_deco"'], view=0.6))
            out.append(text(x, y + 2.75, z, [(names[k][0], "gold", True)], 1.4))
            out.append(text(x, y + 2.45, z, [(names[k][1], "gray", False)], 0.8))
    lb = P("lobby_spawn")
    if lb:
        avoid = [(mk[n]["pos"][0], mk[n]["pos"][2], 3.0) for n in mk if n.startswith("lobby_pad_")] + [(lb[0], lb[2], 2.5)]
        spot = find_spot(world, lb, 4, 10, avoid)
        if spot:
            npc(spot, lb)
    return out


def decor_functions(dp_root, world):
    """world.displays → 소환 함수 (원점 기준 상대 좌표)
       장식은 전부 블록 디스플레이 조립 (bdmodels) — 마법진만 리소스팩 판"""
    import bdkit
    import bdmodels
    F = os.path.join(dp_root, "data", NS, "function", "map")
    lines = ["kill @e[tag=bg_deco]"]
    nparts = 0
    for d in world.displays:
        x, y, z = d["pos"]
        # 원점 매크로 값이 정수라 execute positioned 가 x·z 를 +0.5 (블록 가운데) 로 옮긴다 → 미리 빼 둔다
        x -= 0.5
        z -= 0.5
        m = d["model"]
        sc = d.get("scale", 1.0)
        yaw = d.get("yaw", 0.0) or 0.0
        tags = ['"bg"', '"bg_deco"'] + ([f'"{d["tag"]}"'] if d.get("tag") else []) + (['"bg_spin"'] if d.get("spin") else [])
        tags = list(dict.fromkeys(tags))
        at = "$execute positioned $(x) $(y) $(z) run summon"
        if m.startswith("deco/cap_ring_") or m.startswith("deco/summon_circle_") or m.startswith("deco/rune_ring"):
            # 마법진만 리소스팩 픽셀아트 (바닥 · 공중에 눕힌 판)
            lr = quat_yaw_tilt(0, d.get("tilt", 0.0) or 0.0)
            lines.append(f'{at} item_display ~{x:.3f} ~{y:.3f} ~{z:.3f} {{Tags:[{",".join(tags)}],Rotation:[{yaw:.1f}f,0f],{item("bg:" + m)},'
                         f'item_display:"none",view_range:6f,shadow_radius:0f,teleport_duration:2,brightness:{{sky:15,block:15}},{tf(0, 0, 0, sc, 1, sc, lr)}}}')
            continue
        mdl = bdmodels.build(m, sc, d)
        if mdl is None:
            continue
        if d.get("tilt") and d.get("kind") != "statue":
            bdkit.rotate(mdl.parts, bdkit.rot(0, d["tilt"], 0), (0, 0, 0))
        out = bdkit.summon_lines(mdl, at, x, y, z, yaw, 1.0, tags)
        nparts += len(out)
        lines += out
    # ── 상점 상인 NPC (본진 4곳 + 대기실) · 병과 발판 표식
    extra = npc_and_class_lines(world, bdkit, bdmodels)
    lines += extra
    nparts += len(extra)
    print(f"[decor] 블록 디스플레이 {nparts}개")
    w(os.path.join(F, "decor_run.mcfunction"), lines)
    w(os.path.join(F, "decor.mcfunction"), ["function bg:map/decor_run with storage bg:map origin"])
    w(os.path.join(F, "decor_clear.mcfunction"), ["kill @e[tag=bg_deco]"])
    w(os.path.join(dp_root, "data", NS, "function", "diag.mcfunction"), ["scoreboard objectives add bg_diag dummy", "scoreboard players set #dp bg_diag 1"])
    # 보스 보상 상자 (팀별, 블록 디스플레이)  execute positioned <바닥> run function bg:reward/chest_<팀>
    R_ = os.path.join(dp_root, "data", NS, "function", "reward")
    for t in bdmodels.TEAM:
        out = bdkit.summon_lines(bdmodels.treasure_chest(t), "summon", 0, 0, 0, 0, 1.0, ['"bg"', '"bg_reward"'], spin_tag='"bg_spin_fast"', view=2.0)
        w(os.path.join(R_, f"chest_{t}.mcfunction"), out)
    return len(lines) - 1
