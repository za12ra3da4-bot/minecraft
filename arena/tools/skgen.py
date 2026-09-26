"""Skript 데이터 파일 생성 (메모리 전용 변수 {-bg::...} 로 on load 에 채운다)"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "rp"))
import hud as H
from bossdata import BOSSES

HEAD = "# 자동 생성 파일 — 직접 고치지 말 것 (arena/tools/build.py 가 다시 만든다)\n"


def write_blocks(path, head, body, n=120):
    """'on load:' 한 덩어리를 작게 나눠 씀 (파일 붙여넣기/편집기 한도 · 큰 트리거 문제 방지)"""
    out = list(head)
    for i in range(0, len(body), n):
        out.append("on load:")
        out += body[i:i + n]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def q(s):
    """Skript 문자열 리터럴 (따옴표 두 번)"""
    return '"' + s.replace('"', '""').replace("%", "%%") + '"'


HUD_FUNCS = """
# ── 공백 글자 조합: n 픽셀만큼 커서 이동 (±1..±256 글자 18개를 조합)
function bgSpBuild(n: number) :: text:
    set {_s} to ""
    set {_r} to abs({_n})
    set {_g} to 1
    if {_n} < 0:
        set {_g} to -1
    loop 9 times:
        set {_v} to 2 ^ (9 - loop-number)
        while {_r} >= {_v}:
            set {_k} to {_v} * {_g}
            set {_s} to "%{_s}%%{-bg::spc::%{_k}%}%"
            remove {_v} from {_r}
    return {_s}

# ── 글리프 하나를 x 에 찍고 커서를 되돌림
function bgPlaceG(key: text, dx: number) :: text:
    set {_x} to round({-bg::fg::%{_key}%::x} + {_dx})
    set {_b} to -1 * ({_x} + {-bg::fg::%{_key}%::adv})
    return "%{-bg::sp::%{_x}%}%%{-bg::fg::%{_key}%::c}%%{-bg::sp::%{_b}%}%"

# ── 체력/시전 게이지 채움 (타일 반복 + 끝 조각)
function bgFillBuild(kind: text, px: number, tile: number, x0: number) :: text:
    set {_s} to ""
    set {_full} to floor({_px} / {_tile})
    set {_part} to {_px} - {_full} * {_tile}
    loop {_full} times:
        set {_d} to bgPlaceG("%{_kind}%_%{_tile}%", {_x0} + (loop-number - 1) * {_tile})
        set {_s} to "%{_s}%%{_d}%"
    if {_part} > 0:
        set {_d} to bgPlaceG("%{_kind}%_%{_part}%", {_x0} + {_full} * {_tile})
        set {_s} to "%{_s}%%{_d}%"
    return {_s}

function bgHudBuild(fw: number, tile: number, x0: number, cw: number, ctile: number, cx0: number):
    loop 1281 times:
        set {_n} to loop-number - 641
        set {-bg::sp::%{_n}%} to bgSpBuild({_n})
    loop {_fw} + 1 times:
        set {_n} to loop-number - 1
        set {-bg::hud::hp::%{_n}%} to bgFillBuild("hp", {_n}, {_tile}, {_x0})
        set {-bg::hud::trail::%{_n}%} to bgFillBuild("trail", {_n}, {_tile}, {_x0})
    loop {_cw} + 1 times:
        set {_n} to loop-number - 1
        set {-bg::hud::cast::%{_n}%} to bgFillBuild("cast", {_n}, {_ctile}, {_cx0})
"""


def write_hud(path, font):
    B = []
    for v, ch in H.SP_CH.items():
        B.append(f"    set {{-bg::spc::{v}}} to {q(ch)}")
    g = font.glyphs

    def placed(key, extra=0):
        return H.place(font, key, extra_x=extra)
    # 게이지 조각 글리프 (문자 · 폭 · 기준 x)
    for kind, tile in (("hp", H.TILE), ("trail", H.TILE), ("cast", H.CAST_TILE)):
        for w in range(1, tile + 1):
            k = f"boss/{kind}_{w}"
            if k not in g:
                continue
            gl = g[k]
            base = H.BOSS_X if gl["widget"] == "boss" else 0
            B.append(f"    set {{-bg::fg::{kind}_{w}::c}} to {q(gl['char'])}")
            B.append(f"    set {{-bg::fg::{kind}_{w}::adv}} to {gl['adv']}")
            B.append(f"    set {{-bg::fg::{kind}_{w}::x}} to {gl['x'] + base}")
    # 보스 위젯 정적 조각
    B.append(f"    set {{-bg::hud::boss_back}} to {q(placed('boss/back0') + placed('boss/back1'))}")
    B.append(f"    set {{-bg::hud::boss_front}} to {q(placed('boss/front0') + placed('boss/front1'))}")
    for st in ("normal", "rage"):
        B.append(f"    set {{-bg::hud::banner::{st}}} to {q(placed('boss/banner_' + st))}")
    for st in ("normal", "rage", "stun"):
        B.append(f"    set {{-bg::hud::status::{st}}} to {q(placed('boss/status_' + st))}")
    for st in ("idle", "lit"):
        B.append(f"    set {{-bg::hud::diamond::{st}}} to {q(placed('boss/diamond_' + st))}")
    for bid in BOSSES:
        B.append(f"    set {{-bg::hud::name::{bid}}} to {q(placed('boss/name_' + bid))}")
        B.append(f"    set {{-bg::hud::portrait::{bid}}} to {q(placed('boss/portrait_' + bid))}")
    for t in H.TEAM_COL:
        B.append(f"    set {{-bg::hud::plate::{t}}} to {q(placed('hud/plate_' + t))}")
        B.append(f"    set {{-bg::hud::plate::{t}_me}} to {q(placed('hud/plate_' + t + '_me'))}")
        B.append(f"    set {{-bg::hud::platecx::{t}}} to {H.PLATE_X[t] + 17 + (H.PLATE_W - 17) / 2}")
    B.append(f"    set {{-bg::hud::timer}} to {q(placed('hud/timer'))}")
    for pre, key in (("boss/d", "bd"), ("hud/d", "hd"), ("hud/t", "td")):
        for ch in "0123456789":
            B.append(f"    set {{-bg::hud::{key}::{ch}}} to {q(g[pre + '_' + ch]['char'])}")
        B.append(f"    set {{-bg::hud::{key}::s}} to {q(g[pre + '_slash']['char'])}")
        B.append(f"    set {{-bg::hud::{key}::c}} to {q(g[pre + '_colon']['char'])}")
    B.append(f"    set {{-bg::gui::shop}} to {q(g['gui/shop']['char'])}")
    B.append(f"    set {{-bg::hud::total_w}} to {H.TOTAL_W}")
    B.append(f"    set {{-bg::hud::boss_x}} to {H.BOSS_X}")
    B.append(f"    set {{-bg::hud::fill_w}} to {H.FILL_W}")
    B.append(f"    set {{-bg::hud::cast_w}} to {H.CAST_FILL[2] - H.CAST_FILL[0]}")
    tail = [f"    bgHudBuild({H.FILL_W}, {H.TILE}, {H.FILL[0]}, {H.CAST_FILL[2] - H.CAST_FILL[0]}, {H.CAST_TILE}, {H.CAST_FILL[0]})",
            "    set {-bg::hud::ready} to true"]
    write_blocks(path, [HEAD, HUD_FUNCS], B + tail)


def write_map(path, world):
    L = []
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
    write_blocks(path, [HEAD, "# 맵 좌표 (맵 로컬, 원점 = 설정 {bg::cfg::ox/oy/oz})"], L)


def write_boss(path, meta):
    L = []
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
    write_blocks(path, [HEAD], L)
