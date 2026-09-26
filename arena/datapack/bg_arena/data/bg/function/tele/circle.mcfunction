# 원형 장판: {x,y,z,d(지름),t(틱),id}
$summon item_display $(x) $(y) $(z) {Tags:["bg","bg_tg","bgt_$(id)"],item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"bg:tele/circle_ring","minecraft:custom_data":{flash:'circle_flash'}}},item_display:"none",brightness:{sky:15,block:15},view_range:4f,shadow_radius:0f,teleport_duration:2,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0.03f,0f],scale:[$(d)f,1f,$(d)f]}}
$summon item_display $(x) $(y) $(z) {Tags:["bg","bg_tg","bgt_$(id)","bg_tg_grow"],item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"bg:tele/circle_fill","minecraft:custom_data":{kill:1b,gx:$(d),gz:$(d),ty:0.04,tz:0,t:$(t)}}},item_display:"none",brightness:{sky:15,block:15},view_range:4f,shadow_radius:0f,teleport_duration:2,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0.04f,0f],scale:[0.01f,1f,0.01f]}}
$summon item_display $(x) $(y) $(z) {Tags:["bg","bg_tg","bgt_$(id)","bg_tg_arc"],item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"bg:tele/circle_arc_0","minecraft:custom_data":{kill:1b,pre:'circle_arc'}}},item_display:"none",brightness:{sky:15,block:15},view_range:4f,shadow_radius:0f,teleport_duration:2,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0.05f,0f],scale:[$(d)f,1f,$(d)f]}}
$scoreboard players set @e[tag=bgt_$(id)] bg_life $(t)
$scoreboard players set @e[tag=bgt_$(id)] bg_age 0
$scoreboard players set @e[tag=bgt_$(id)] bg_frames 20
$scoreboard players set @e[tag=bgt_$(id)] bg_last -1
