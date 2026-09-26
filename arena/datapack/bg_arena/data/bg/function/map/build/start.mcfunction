# 맵 건설 시작: 원점은 storage bg:map origin (기본 -128 40 -128)
#   바꾸려면: data merge storage bg:map {origin:{x:0,y:40,z:0}}
function bg:map/build/forceload with storage bg:map origin
scoreboard players set #part bg_build 0
scoreboard players set #run bg_build 1
tellraw @a [{"text":"[전장] ","color":"gold"},{"text":"맵 건설 시작 (229단계, 약 12초)","color":"yellow"}]
