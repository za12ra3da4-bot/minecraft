# 머리 위 ! 표식 (빌보드): {x,y,z,t,id}
$summon item_display $(x) $(y) $(z) {Tags:["bg","bg_tg","bgt_$(id)"],item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"bg:tele/mark_head","minecraft:custom_data":{kill:1b}}},item_display:"none",brightness:{sky:15,block:15},view_range:4f,shadow_radius:0f,teleport_duration:2,billboard:"vertical",transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[1.3f,1.3f,1.3f]}}
$scoreboard players set @e[tag=bgt_$(id)] bg_life $(t)
$scoreboard players set @e[tag=bgt_$(id)] bg_age 0
