execute as @e[type=item_display,tag=bg_tg] run function bg:tele/tick
execute as @e[type=!player,tag=bg_spin_fast] at @s run tp @s ~ ~ ~ ~3 ~
execute as @e[type=!player,tag=bg_spin] at @s run tp @s ~ ~ ~ ~0.8 ~
execute as @e[type=interaction,tag=bg_shopnpc] if data entity @s interaction on target run tag @s add bg_wantshop
execute as @e[type=interaction,tag=bg_shopnpc] if data entity @s attack on attacker run tag @s add bg_wantshop
execute as @e[type=interaction,tag=bg_shopnpc] run data remove entity @s interaction
execute as @e[type=interaction,tag=bg_shopnpc] run data remove entity @s attack
execute as @e[type=interaction,tag=bg_rewardhit] if data entity @s interaction on target run tag @s add bg_wantreward
execute as @e[type=interaction,tag=bg_corehit_red] if data entity @s attack on attacker run tag @s add bg_wantcore_red
execute as @e[type=interaction,tag=bg_corehit_blue] if data entity @s attack on attacker run tag @s add bg_wantcore_blue
execute as @e[type=interaction,tag=bg_corehit_green] if data entity @s attack on attacker run tag @s add bg_wantcore_green
execute as @e[type=interaction,tag=bg_corehit_yellow] if data entity @s attack on attacker run tag @s add bg_wantcore_yellow
execute as @e[type=interaction,tag=bg_corehit] run data remove entity @s attack
execute as @e[type=interaction,tag=bg_rewardhit] if data entity @s attack on attacker run tag @s add bg_wantreward
execute as @e[type=interaction,tag=bg_rewardhit] run data remove entity @s interaction
execute as @e[type=interaction,tag=bg_rewardhit] run data remove entity @s attack
execute if score #run bg_build matches 1 run function bg:map/build/step with storage bg:map origin
