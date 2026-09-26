scoreboard objectives add bg_age dummy
scoreboard objectives add bg_life dummy
scoreboard objectives add bg_frames dummy
scoreboard objectives add bg_last dummy
scoreboard objectives add bg_tmp dummy
scoreboard objectives add bg_build dummy
execute unless data storage bg:map origin run data merge storage bg:map {origin:{x:-128,y:40,z:-128}}
