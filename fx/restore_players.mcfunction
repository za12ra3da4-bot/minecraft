# 자동 생성 (tools/boss_fx/datapack.py) — 보스 스킬 연출. Skript 10-bossfx.sk / 10-boss-<id>.sk 가 부른다.
# 보스가 건 석화·속박 수정치를 모든 플레이어에게서 뗀다
execute as @a run attribute @s minecraft:movement_speed modifier remove oly:boss_petrify
execute as @a run attribute @s minecraft:movement_speed modifier remove oly:boss_snare
execute as @a run attribute @s minecraft:jump_strength modifier remove oly:boss_petrify
execute as @a run attribute @s minecraft:jump_strength modifier remove oly:boss_snare
