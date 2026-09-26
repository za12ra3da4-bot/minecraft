scoreboard players add @s bg_age 1
execute if entity @s[tag=bg_tg_grow] run function bg:tele/grow with entity @s item.components."minecraft:custom_data"
execute if entity @s[tag=bg_tg_arc] run function bg:tele/arc
execute if score @s bg_age >= @s bg_life run function bg:tele/expire
