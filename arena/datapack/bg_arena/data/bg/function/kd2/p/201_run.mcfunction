$execute positioned $(x) $(y) $(z) run fill ~81 ~63 ~-103 ~81 ~67 ~-103 minecraft:iron_chain[axis=y,waterlogged=false]
$execute positioned $(x) $(y) $(z) run setblock ~81 ~68 ~-103 minecraft:redstone_lamp[lit=true]
$execute positioned $(x) $(y) $(z) run fill ~86 ~-16 ~-114 ~93 ~79 ~-73 minecraft:air strict
$execute positioned $(x) $(y) $(z) run fill ~86 ~-16 ~-72 ~93 ~79 ~-31 minecraft:air strict
$execute positioned $(x) $(y) $(z) positioned ~-114 ~-18 ~-114 run kill @e[type=item,dx=229,dy=100,dz=229]
