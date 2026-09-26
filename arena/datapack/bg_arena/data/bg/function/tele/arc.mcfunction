scoreboard players operation #f bg_tmp = @s bg_age
scoreboard players operation #f bg_tmp *= @s bg_frames
scoreboard players operation #f bg_tmp /= @s bg_life
scoreboard players operation #m bg_tmp = @s bg_frames
scoreboard players remove #m bg_tmp 1
execute if score #f bg_tmp > #m bg_tmp run scoreboard players operation #f bg_tmp = #m bg_tmp
execute if score #f bg_tmp = @s bg_last run return 0
scoreboard players operation @s bg_last = #f bg_tmp
execute store result storage bg:tmp f int 1 run scoreboard players get #f bg_tmp
data modify storage bg:tmp pre set from entity @s item.components."minecraft:custom_data".pre
function bg:tele/arc_set with storage bg:tmp
