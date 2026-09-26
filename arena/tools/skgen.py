"""Skript 데이터 파일 생성 (메모리 전용 변수 {-bg::...} 로 on load 에 채운다)"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "rp"))
import hud as H
from bossdata import BOSSES

HEAD = "# 자동 생성 파일 — 직접 고치지 말 것 (arena/tools/build.py 가 다시 만든다)\n"


def q(s):
    """Skript 문자열 리터럴 (따옴표 두 번)"""
    return '"' + s.replace('"', '""').replace("%", "%%") + '"'


def write_hud(path, font):
    L = [HEAD, "on load:"]
    for n in range(-640, 641):
        L.append(f"    set {{-bg::sp::{n}}} to {q(H.sp(n))}")
    g = font.glyphs

    def placed(key, extra=0):
        return H.place(font, key, extra_x=extra)
    # 보스 위젯 정적 조각
    L.append(f"    set {{-bg::hud::boss_back}} to {q(placed('boss/back0') + placed('boss/back1'))}")
    L.append(f"    set {{-bg::hud::boss_front}} to {q(placed('boss/front0') + placed('boss/front1'))}")
    for st in ("normal", "rage"):
        L.append(f"    set {{-bg::hud::banner::{st}}} to {q(placed('boss/banner_' + st))}")
    for st in ("normal", "rage", "stun"):
        L.append(f"    set {{-bg::hud::status::{st}}} to {q(placed('boss/status_' + st))}")
    for st in ("idle", "lit"):
        L.append(f"    set {{-bg::hud::diamond::{st}}} to {q(placed('boss/diamond_' + st))}")
    for bid in BOSSES:
        L.append(f"    set {{-bg::hud::name::{bid}}} to {q(placed('boss/name_' + bid))}")
        L.append(f"    set {{-bg::hud::portrait::{bid}}} to {q(placed('boss/portrait_' + bid))}")
    # 채움 (0..최대)
    import hud_build as HB
    for kind, tile, x0, maxw in (("hp", H.TILE, H.FILL[0], H.FILL_W), ("trail", H.TILE, H.FILL[0], H.FILL_W),
                                 ("cast", H.CAST_TILE, H.CAST_FILL[0], H.CAST_FILL[2] - H.CAST_FILL[0])):
        for n in range(0, maxw + 1):
            L.append(f"    set {{-bg::hud::{kind}::{n}}} to {q(HB.fill_str(font, kind, n, tile, x0))}")
    # 팀 판 · 타이머
    for t in H.TEAM_COL:
        L.append(f"    set {{-bg::hud::plate::{t}}} to {q(placed('hud/plate_' + t))}")
        L.append(f"    set {{-bg::hud::plate::{t}_me}} to {q(placed('hud/plate_' + t + '_me'))}")
        L.append(f"    set {{-bg::hud::platecx::{t}}} to {H.PLATE_X[t] + 17 + (H.PLATE_W - 17) / 2}")
    L.append(f"    set {{-bg::hud::timer}} to {q(placed('hud/timer'))}")
    # 숫자 글자
    for pre, key in (("boss/d", "bd"), ("hud/d", "hd"), ("hud/t", "td")):
        for ch in "0123456789":
            L.append(f"    set {{-bg::hud::{key}::{ch}}} to {q(g[pre + '_' + ch]['char'])}")
        L.append(f"    set {{-bg::hud::{key}::s}} to {q(g[pre + '_slash']['char'])}")
        L.append(f"    set {{-bg::hud::{key}::c}} to {q(g[pre + '_colon']['char'])}")
    L.append(f"    set {{-bg::hud::total_w}} to {H.TOTAL_W}")
    L.append(f"    set {{-bg::hud::boss_x}} to {H.BOSS_X}")
    L.append(f"    set {{-bg::hud::fill_w}} to {H.FILL_W}")
    L.append(f"    set {{-bg::hud::cast_w}} to {H.CAST_FILL[2] - H.CAST_FILL[0]}")
    L.append(f"    set {{-bg::hud::ready}} to true")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def write_map(path, world):
    L = [HEAD, "# 맵 좌표 (맵 로컬, 원점 = 설정 {bg::cfg::origin::*}) ", "on load:"]
    for name, m in sorted(world.markers.items()):
        x, y, z = m["pos"]
        L.append(f"    set {{-bg::mk::{name}::x}} to {x}")
        L.append(f"    set {{-bg::mk::{name}::y}} to {y}")
        L.append(f"    set {{-bg::mk::{name}::z}} to {z}")
        for k in ("radius", "yaw"):
            if k in m:
                L.append(f"    set {{-bg::mk::{name}::{k}}} to {round(float(m[k]), 2)}")
        if "boss" in m:
            L.append(f"    set {{-bg::mk::{name}::boss}} to {q(m['boss'])}")
    L.append(f"    set {{-bg::mk::size}} to {world.size[0]}")
    L.append(f"    set {{-bg::mk::ready}} to true")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def write_boss(path, meta):
    L = [HEAD, "on load:"]
    for bid, m in meta.items():
        b = BOSSES[bid]
        L.append(f"    set {{-bg::bd::{bid}::name}} to {q(b['name'])}")
        L.append(f"    set {{-bg::bd::{bid}::short}} to {q(b['short'])}")
        L.append(f"    set {{-bg::bd::{bid}::lair}} to {q(b['lair'])}")
        L.append(f"    set {{-bg::bd::{bid}::hp}} to {b['hp']}")
        L.append(f"    set {{-bg::bd::{bid}::hitbox}} to {q(m['info'].get('hitbox', 'husk'))}")
        L.append(f"    set {{-bg::bd::{bid}::hitscale}} to {m['info'].get('hit_scale', 2)}")
        for sk, nm in b["skills"].items():
            L.append(f"    set {{-bg::bd::{bid}::skill::{sk}}} to {q(nm)}")
        for an, a in m["anims"].items():
            L.append(f"    set {{-bg::anim::{bid}::{an}::n}} to {len(a['ticks'])}")
            L.append(f"    set {{-bg::anim::{bid}::{an}::loop}} to {'true' if a['loop'] else 'false'}")
            for k, t in enumerate(a["ticks"]):
                L.append(f"    set {{-bg::anim::{bid}::{an}::t::{k}}} to {t}")
    ids = [q(b) for b in meta]
    L.append(f"    set {{-bg::bd::list::*}} to {', '.join(ids[:-1])} and {ids[-1]}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
