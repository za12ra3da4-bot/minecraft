scoreboard players add @s bg_age 1
execute if entity @s[tag=bgx_shock] if score @s bg_age matches 2 run function bg:impact/expand with entity @s item.components."minecraft:custom_data"
execute if entity @s[tag=bgx_shock] if score @s bg_age matches 9.. run return run kill @s
execute if entity @s[tag=bgx_burst] if score @s bg_age matches 2 run function bg:impact/rise with entity @s item.components."minecraft:custom_data"
execute if entity @s[tag=bgx_burst] if score @s bg_age matches 7 run function bg:impact/thin with entity @s item.components."minecraft:custom_data"
execute if entity @s[tag=bgx_burst] if score @s bg_age matches 12.. run return run kill @s
execute if entity @s[tag=bgx_crater] if score @s bg_age = @s bg_life run data merge entity @s {start_interpolation:0,interpolation_duration:10,transformation:{scale:[0f,1f,0f]}}
execute if entity @s[tag=bgx_crater] if score @s bg_age >= @s bg_life run scoreboard players add @s bg_frames 1
execute if entity @s[tag=bgx_crater] if score @s bg_frames matches 11.. run return run kill @s
execute if entity @s[tag=bgx_num] if score @s bg_age matches 2 run data merge entity @s {start_interpolation:0,interpolation_duration:12,transformation:{translation:[0f,1.2f,0f]}}
execute if entity @s[tag=bgx_num] if score @s bg_age matches 15 run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[0f,1.5f,0f],scale:[0f,0f,0f]}}
execute if entity @s[tag=bgx_num] if score @s bg_age matches 21.. run return run kill @s
execute if entity @s[tag=bgx_dA,tag=bgx_c1] if score @s bg_age matches 2 run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[-0.16f,1.10f,0.72f],left_rotation:[0.872f,0f,0.349f,0.342f]}}
execute if entity @s[tag=bgx_dA,tag=bgx_c1] if score @s bg_age matches 7 run data merge entity @s {start_interpolation:0,interpolation_duration:6,transformation:{translation:[-0.16f,0.02f,1.30f],left_rotation:[0.533f,0f,0.213f,-0.819f]}}
execute if entity @s[tag=bgx_dB,tag=bgx_c1] if score @s bg_age matches 2 run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[-0.16f,1.38f,0.44f],left_rotation:[0.872f,0f,0.349f,0.342f]}}
execute if entity @s[tag=bgx_dB,tag=bgx_c1] if score @s bg_age matches 7 run data merge entity @s {start_interpolation:0,interpolation_duration:6,transformation:{translation:[-0.16f,0.02f,0.80f],left_rotation:[0.533f,0f,0.213f,-0.819f]}}
execute if entity @s[tag=bgx_dA,tag=bgx_c2] if score @s bg_age matches 2 run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[-0.24f,1.90f,1.32f],left_rotation:[0.872f,0f,0.349f,0.342f]}}
execute if entity @s[tag=bgx_dA,tag=bgx_c2] if score @s bg_age matches 7 run data merge entity @s {start_interpolation:0,interpolation_duration:6,transformation:{translation:[-0.24f,0.02f,2.40f],left_rotation:[0.533f,0f,0.213f,-0.819f]}}
execute if entity @s[tag=bgx_dB,tag=bgx_c2] if score @s bg_age matches 2 run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[-0.24f,2.38f,0.83f],left_rotation:[0.872f,0f,0.349f,0.342f]}}
execute if entity @s[tag=bgx_dB,tag=bgx_c2] if score @s bg_age matches 7 run data merge entity @s {start_interpolation:0,interpolation_duration:6,transformation:{translation:[-0.24f,0.02f,1.50f],left_rotation:[0.533f,0f,0.213f,-0.819f]}}
execute if entity @s[tag=bgx_dA,tag=bgx_c3] if score @s bg_age matches 2 run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[-0.31f,2.80f,2.09f],left_rotation:[0.872f,0f,0.349f,0.342f]}}
execute if entity @s[tag=bgx_dA,tag=bgx_c3] if score @s bg_age matches 7 run data merge entity @s {start_interpolation:0,interpolation_duration:6,transformation:{translation:[-0.31f,0.02f,3.80f],left_rotation:[0.533f,0f,0.213f,-0.819f]}}
execute if entity @s[tag=bgx_dB,tag=bgx_c3] if score @s bg_age matches 2 run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[-0.31f,3.50f,1.26f],left_rotation:[0.872f,0f,0.349f,0.342f]}}
execute if entity @s[tag=bgx_dB,tag=bgx_c3] if score @s bg_age matches 7 run data merge entity @s {start_interpolation:0,interpolation_duration:6,transformation:{translation:[-0.31f,0.02f,2.30f],left_rotation:[0.533f,0f,0.213f,-0.819f]}}
execute if entity @s[tag=bgx_deb] if score @s bg_age matches 26 run data merge entity @s {start_interpolation:0,interpolation_duration:8,transformation:{scale:[0f,0f,0f]}}
execute if entity @s[tag=bgx_deb] if score @s bg_age matches 35.. run return run kill @s
execute if score @s bg_age matches 400.. run kill @s
