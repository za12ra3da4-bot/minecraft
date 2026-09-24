# 자동 생성 (tools/boss_fx/datapack.py) — 보스 스킬 연출. Skript 10-bossfx.sk / 10-boss-<id>.sk 가 부른다.
# 파츠 전체 외곽선 발광. 사용: function oly:boss/nemean_lion/fx/glow {c:16711680}
$execute as @e[tag=olyb_nemean_lion_part] run data merge entity @s {Glowing:1b,glow_color_override:$(c)}
