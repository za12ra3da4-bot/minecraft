"""보스 데이터팩 연출 함수 생성 — oly:boss/<id>/fx/*, oly:boss/fx/*

저장소 최상위 <id>/ 폴더 = world/datapacks/olympus_bosses/data/oly/function/boss/<id>/ 이므로
여기서도 같은 자리(<repo>/<id>/fx/, <repo>/fx/)에 쓴다. 기존 spawn/rot/remove/애니메이션 파일은 건드리지 않는다.

UUID 규칙 (spawn.mcfunction 과 동일): 6f6c7962-0000-000B-0000-0000000000PP
부위 번호는 spawn.mcfunction(미노타우로스·사자·스킬라)과 애니메이션 프레임 좌표(나머지)로 확인했다.
"""
import os

REPO = os.path.join(os.path.dirname(__file__), "..", "..")

BOSS_B = {"minotaur": 1, "nemean_lion": 2, "chimera": 3, "cerberus": 4, "hydra": 5, "medusa": 6, "scylla": 7}

# 길게 울리는 사운드 — 보스가 사라지면 끊는다
LONG_SOUNDS = {
    "minotaur": ["boss.minotaur.whirl", "boss.minotaur.rage"],
    "nemean_lion": ["boss.nemean_lion.mark", "boss.nemean_lion.roar"],
    "chimera": ["boss.chimera.breath"],
    "cerberus": ["boss.cerberus.gate", "boss.cerberus.fire", "boss.cerberus.fury"],
    "hydra": ["boss.hydra.regrow", "boss.hydra.sear"],
    "medusa": ["boss.medusa.gaze", "boss.medusa.zone"],
    "scylla": ["boss.scylla.whirl", "boss.scylla.cage"],
}

EYES = {"minotaur": [6], "nemean_lion": [11], "medusa": [15], "scylla": [35]}

GROUPS = {
    "cerberus": {"head_a": range(9, 13), "head_m": range(13, 17), "head_b": range(17, 21)},
    "chimera": {"head_lion": range(9, 14), "head_goat": range(14, 22), "head_snake": range(22, 29)},
    "hydra": {f"neck_{k}": range(14 + 7 * k, 21 + 7 * k) for k in range(7)},
    "scylla": dict([(f"dog_{k}", range(40 + 3 * k, 43 + 3 * k)) for k in range(6)]
                   + [(f"arm_{k}", range(1 + 4 * k, 5 + 4 * k)) for k in range(8)]),
}

HEADER = "# 자동 생성 (tools/boss_fx/datapack.py) — 보스 스킬 연출. Skript 10-bossfx.sk / 10-boss-<id>.sk 가 부른다.\n"


def uid(b, p):
    return f"6f6c7962-0000-000{b}-0000-{p:012x}"


def write(rel, lines):
    p = os.path.join(REPO, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(HEADER)
        f.write("\n".join(lines) + "\n")


def glow_lines(b, parts, macro=True):
    out = []
    for p in parts:
        if macro:
            out.append(f"$data merge entity {uid(b, p)} {{Glowing:1b,glow_color_override:$(c)}}")
        else:
            out.append(f"data merge entity {uid(b, p)} {{Glowing:0b}}")
    return out


def breath(rel, b, part, off, particle, extra, doc):
    """머리(파츠) 위치에서 보스가 보는 방향으로 불길 한 번 (Skript 가 몇 틱마다 부른다)."""
    x, y, z = off
    lines = [f"# {doc}",
             f"execute as {uid(b, part)} at @s rotated as @s positioned ^{x} ^{y} ^{z} run function oly:boss/{rel}_line"]
    write(f"{rel}.mcfunction", lines)
    line = []
    for k in range(1, 12):
        s = 0.12 + k * 0.09
        line.append(f"particle {particle} ^ ^{-0.05 * k:.2f} ^{k * 1.0:.1f} {s:.2f} {s * 0.7:.2f} {s:.2f} 0.02 {4 + k} force")
        if extra and k % 2 == 0:
            line.append(f"particle {extra} ^ ^{-0.05 * k:.2f} ^{k * 1.0:.1f} {s:.2f} {s:.2f} {s:.2f} 0.01 2 force")
    write(f"{rel}_line.mcfunction", line)


def build():
    for boss, b in BOSS_B.items():
        base = f"{boss}/fx"
        clear = [f"kill @e[tag=olyfx_{boss}]",
                 f"execute as @e[tag=olyb_{boss}_part] run data merge entity @s {{Glowing:0b}}"]
        clear += [f"stopsound @a hostile oly:{s}" for s in LONG_SOUNDS[boss]]
        if boss == "hydra":
            clear.append("kill @e[tag=olyb_hydra_add]")
        write(f"{base}/clear.mcfunction", clear)
        write(f"{base}/glow.mcfunction",
              [f"# 파츠 전체 외곽선 발광. 사용: function oly:boss/{boss}/fx/glow {{c:16711680}}",
               f"$execute as @e[tag=olyb_{boss}_part] run data merge entity @s {{Glowing:1b,glow_color_override:$(c)}}"])
        write(f"{base}/unglow.mcfunction",
              [f"execute as @e[tag=olyb_{boss}_part] run data merge entity @s {{Glowing:0b}}"])
        if boss in EYES:
            write(f"{base}/eyes.mcfunction", ["# 눈 파츠만 발광 {c:색}"] + glow_lines(b, EYES[boss]))
        for g, parts in GROUPS.get(boss, {}).items():
            write(f"{base}/{g}.mcfunction", [f"# {g} 파츠만 발광 {{c:색}}"] + glow_lines(b, list(parts)))

    # 케르베로스 — 머리 셋의 입에서 (프레임 0 의 턱 파츠 위치)
    breath("cerberus/fx/breath_a", 4, 12, (1.19, -0.46, 2.43), "minecraft:flame", "minecraft:lava",
           "화염의 머리(A) 입에서 지옥불")
    breath("cerberus/fx/breath_a_soul", 4, 12, (1.19, -0.46, 2.43), "minecraft:soul_fire_flame", "minecraft:large_smoke",
           "분노 상태의 화염 머리 — 영혼불")
    write("cerberus/fx/roar_m.mcfunction", [
        "# 가운데 머리 — 충격파 발사 지점",
        f"execute as {uid(4, 16)} at @s rotated as @s positioned ^0.10 ^-0.55 ^2.60 run particle minecraft:sonic_boom ~ ~ ~ 0 0 0 0 1 force",
        f"execute as {uid(4, 16)} at @s rotated as @s positioned ^0.10 ^-0.55 ^2.60 run particle minecraft:soul ~ ~ ~ 0.6 0.4 0.6 0.05 20 force",
    ])
    write("cerberus/fx/bite_b.mcfunction", [
        "# 추적의 머리 — 물기 순간",
        f"execute as {uid(4, 20)} at @s rotated as @s positioned ^-1.08 ^-0.39 ^2.45 run particle minecraft:crit ~ ~ ~ 0.4 0.3 0.4 0.3 25 force",
        f"execute as {uid(4, 20)} at @s rotated as @s positioned ^-1.08 ^-0.39 ^2.45 run particle minecraft:damage_indicator ~ ~ ~ 0.3 0.2 0.3 0.1 6 force",
    ])
    # 키메라 — 사자 입, 뱀 꼬리 머리, 염소 머리
    breath("chimera/fx/breath_lion", 3, 12, (0.0, -1.11, 2.50), "minecraft:flame", "minecraft:smoke",
           "사자 머리 입에서 화염")
    write("chimera/fx/spit_snake.mcfunction", [
        "# 뱀 꼬리 머리 — 독 발사 순간",
        f"execute as {uid(3, 28)} at @s rotated as @s positioned ^0 ^0.22 ^-4.12 run particle minecraft:item_slime ~ ~ ~ 0.3 0.3 0.3 0.1 20 force",
        f"execute as {uid(3, 28)} at @s rotated as @s positioned ^0 ^0.22 ^-4.12 run particle minecraft:dust{{color:[0.35,0.85,0.2],scale:1.4}} ~ ~ ~ 0.3 0.3 0.3 0 15 force",
    ])
    write("chimera/fx/bleat_goat.mcfunction", [
        "# 염소 머리 — 가시를 부르는 울음",
        f"execute as {uid(3, 15)} at @s rotated as @s positioned ^0 ^0.43 ^-0.68 run particle minecraft:witch ~ ~0.5 ~ 0.4 0.4 0.4 0.1 25 force",
        f"execute as {uid(3, 15)} at @s rotated as @s positioned ^0 ^0.43 ^-0.68 run particle minecraft:electric_spark ~ ~0.5 ~ 0.4 0.4 0.4 0.2 20 force",
    ])
    # 메두사 — 눈에서 시선
    write("medusa/fx/gaze_charge.mcfunction", [
        "# 시전 중 눈에 모이는 빛",
        f"execute as {uid(6, 15)} at @s rotated as @s positioned ^0.05 ^-1.01 ^0.3 run particle minecraft:end_rod ~ ~ ~ 0.25 0.15 0.25 0.02 6 force",
        f"execute as {uid(6, 15)} at @s rotated as @s positioned ^0.05 ^-1.01 ^0.3 run particle minecraft:dust{{color:[0.55,1.0,0.6],scale:1.2}} ~ ~ ~ 0.4 0.3 0.4 0 8 force",
    ])

    # 히드라 — 목 자르기 (grow_N 의 정확한 반대: 같은 7개 파츠를 숨긴다)
    for n in range(3, 7):
        lines = [f"# 목 {n} 번을 숨긴다 (grow_{n} 이 다시 펼친다). 애니메이션은 oly_hidden 파츠를 건너뛴다"]
        for p in range(14 + 7 * n, 21 + 7 * n):
            lines.append(f"tag {uid(5, p)} add oly_hidden")
            lines.append(f"data merge entity {uid(5, p)} {{Glowing:0b,start_interpolation:0,interpolation_duration:6,"
                         "transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[0f,0f,0f]}}")
        write(f"hydra/fx/cut_{n}.mcfunction", lines)

    # 공통
    mods = []
    for attr in ("movement_speed", "jump_strength"):
        for m in ("boss_petrify", "boss_snare"):
            mods.append(f"execute as @a run attribute @s minecraft:{attr} modifier remove oly:{m}")
    write("fx/restore_players.mcfunction", ["# 보스가 건 석화·속박 수정치를 모든 플레이어에게서 뗀다"] + mods)
    write("fx/clear_all.mcfunction",
          [f"function oly:boss/{b}/fx/clear" for b in BOSS_B] + ["kill @e[tag=olyfx]", "function oly:boss/fx/restore_players"])


if __name__ == "__main__":
    build()
    print("datapack fx ok")
