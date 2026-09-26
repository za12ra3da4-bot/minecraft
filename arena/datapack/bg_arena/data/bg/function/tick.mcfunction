execute as @e[type=item_display,tag=bg_tg] run function bg:tele/tick
execute as @e[type=!player,tag=bg_spin_fast] at @s run tp @s ~ ~ ~ ~3 ~
execute as @e[type=!player,tag=bg_spin] at @s run tp @s ~ ~ ~ ~0.8 ~
execute if score #run bg_build matches 1 run function bg:map/build/step with storage bg:map origin
