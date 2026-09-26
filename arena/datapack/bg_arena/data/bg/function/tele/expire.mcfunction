execute if data entity @s item.components."minecraft:custom_data".kill run return run kill @s
execute if entity @s[tag=bg_tg_dying] run return run kill @s
tag @s add bg_tg_dying
scoreboard players add @s bg_life 5
function bg:tele/flash with entity @s item.components."minecraft:custom_data"
