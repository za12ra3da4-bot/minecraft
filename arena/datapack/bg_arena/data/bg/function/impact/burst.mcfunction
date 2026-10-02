$summon item_display $(x) $(y) $(z) {Tags:["bg","bgfx","bgx","bgx_new","bgx_burst"],item:{id:"minecraft:paper",count:1,components:{"minecraft:item_model":"bg:impact/burst_$(k)","minecraft:custom_data":{bw:$(bw),bh:$(bh)}}},item_display:"none",brightness:{sky:15,block:15},view_range:4f,shadow_radius:0f,teleport_duration:2,billboard:"vertical",transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,$(bh0)f,0f],scale:[$(bw0)f,$(bh0)f,$(bw0)f]}}
scoreboard players set @e[tag=bgx_new] bg_age 0
tag @e[tag=bgx_new] remove bgx_new
