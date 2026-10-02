$summon text_display $(x) $(y) $(z) {Tags:["bg","bgfx","bgx","bgx_new","bgx_num"],billboard:"center",shadow:1b,see_through:0b,background:0,brightness:{sky:15,block:15},view_range:3f,text:{text:"$(txt)",color:"$(col)",bold:true},transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[$(s)f,$(s)f,$(s)f]}}
scoreboard players set @e[tag=bgx_new] bg_age 0
tag @e[tag=bgx_new] remove bgx_new
