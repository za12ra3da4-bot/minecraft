$summon item_display $(x) $(y) $(z) {Tags:["bg","bgfx","bgx","bgx_new","bgx_crater"],item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"bg:impact/crater_$(k)"}},item_display:"none",brightness:{sky:15,block:15},view_range:4f,shadow_radius:0f,teleport_duration:2,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0.02f,0f],scale:[$(d)f,1f,$(d)f]}}
$scoreboard players set @e[tag=bgx_new] bg_life $(cl)
scoreboard players set @e[tag=bgx_new] bg_frames 0
scoreboard players set @e[tag=bgx_new] bg_age 0
tag @e[tag=bgx_new] remove bgx_new
