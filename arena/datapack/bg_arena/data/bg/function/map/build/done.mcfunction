scoreboard players set #run bg_build 0
function bg:map/decor
function bg:map/build/unload with storage bg:map origin
tellraw @a [{"text":"[전장] ","color":"gold"},{"text":"맵 건설 완료! /전장 준비 로 게임을 시작하세요.","color":"green"}]
