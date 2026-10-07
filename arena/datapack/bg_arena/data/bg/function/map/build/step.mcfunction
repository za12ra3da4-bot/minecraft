execute store result storage bg:map origin.part int 1 run scoreboard players get #part bg_build
function bg:map/build/run with storage bg:map origin
scoreboard players add #part bg_build 1
execute if score #part bg_build matches 240.. run function bg:map/build/done
