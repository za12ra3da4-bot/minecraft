# 자동 생성 (tools/boss_fx/datapack.py) — 보스 스킬 연출. Skript 10-bossfx.sk / 10-boss-<id>.sk 가 부른다.
function oly:boss/minotaur/fx/clear
function oly:boss/nemean_lion/fx/clear
function oly:boss/chimera/fx/clear
function oly:boss/cerberus/fx/clear
function oly:boss/hydra/fx/clear
function oly:boss/medusa/fx/clear
function oly:boss/scylla/fx/clear
kill @e[tag=olyfx]
function oly:boss/fx/restore_players
