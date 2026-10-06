execute store result storage bg:map origin.part int 1 run scoreboard players get #part bg_build
function bg:maps/volcano/build/run with storage bg:map origin
scoreboard players add #part bg_build 1
execute if score #part bg_build matches 258.. run function bg:maps/volcano/build/done
