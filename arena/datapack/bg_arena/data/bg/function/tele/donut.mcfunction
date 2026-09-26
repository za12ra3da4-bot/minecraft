# 도넛 장판 (안쪽 안전): {x,y,z,d,t,id}
$summon item_display $(x) $(y) $(z) {Tags:["bg","bg_tg","bgt_$(id)"],item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"bg:tele/donut_base","minecraft:custom_data":{flash:'donut_flash'}}},item_display:"none",brightness:{sky:15,block:15},view_range:4f,shadow_radius:0f,teleport_duration:2,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0.03f,0f],scale:[$(d)f,1f,$(d)f]}}
$summon item_display $(x) $(y) $(z) {Tags:["bg","bg_tg","bgt_$(id)","bg_tg_arc"],item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"bg:tele/donut_fill_0","minecraft:custom_data":{kill:1b,pre:'donut_fill'}}},item_display:"none",brightness:{sky:15,block:15},view_range:4f,shadow_radius:0f,teleport_duration:2,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0.04f,0f],scale:[$(d)f,1f,$(d)f]}}
$scoreboard players set @e[tag=bgt_$(id)] bg_life $(t)
$scoreboard players set @e[tag=bgt_$(id)] bg_age 0
$scoreboard players set @e[tag=bgt_$(id)] bg_frames 12
$scoreboard players set @e[tag=bgt_$(id)] bg_last -1
