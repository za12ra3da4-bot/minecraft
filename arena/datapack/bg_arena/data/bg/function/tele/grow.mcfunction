tag @s remove bg_tg_grow
$data merge entity @s {start_interpolation:0,interpolation_duration:$(t),transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,$(ty)f,$(tz)f],scale:[$(gx)f,1f,$(gz)f]}}
