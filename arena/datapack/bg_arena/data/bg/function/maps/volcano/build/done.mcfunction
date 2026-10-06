scoreboard players set #run bg_build 0
function bg:maps/volcano/border with storage bg:map origin
function bg:maps/volcano/decor
function bg:maps/volcano/build/unload with storage bg:map origin
tellraw @a [{"text":"[전장] ","color":"gold"},{"text":"맵 건설 완료! /전장 자동팀 → /전장 시작","color":"green"}]
