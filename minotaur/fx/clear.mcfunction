# 자동 생성 (tools/boss_fx/datapack.py) — 보스 스킬 연출. Skript 10-bossfx.sk / 10-boss-<id>.sk 가 부른다.
kill @e[tag=olyfx_minotaur]
execute as @e[tag=olyb_minotaur_part] run data merge entity @s {Glowing:0b}
stopsound @a hostile oly:boss.minotaur.whirl
stopsound @a hostile oly:boss.minotaur.rage
