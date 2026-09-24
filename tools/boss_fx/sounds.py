"""보스 스킬 사운드 — 합성 .ogg + assets/oly/sounds.json

- 합성음(부딪힘·바람·불·석화 …) = 이 프로젝트 고유 파일 assets/oly/sounds/boss/*.ogg (Vorbis, 모노 → 위치 음향)
- 목소리(포효·짖음·쉿) = 바닐라 파일을 낮은 피치로 재사용 (경로는 1.21.11 sounds.json 으로 검증)
이벤트 이름: oly:boss.<id>.<name>  (Skript: playsound oly:boss.minotaur.stomp hostile ...)
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

SR = 44100
ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "resourcepack", "olympus_pack", "assets", "oly")
rng = np.random.default_rng(1234)


def t_(sec):
    return np.arange(int(SR * sec)) / SR


def noise(sec):
    return rng.standard_normal(int(SR * sec))


def filt(x, kind, f, order=4):
    sos = signal.butter(order, f, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def env_exp(sec, decay, attack=0.004):
    t = t_(sec)
    e = np.exp(-t / decay)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return e * a


def env_adsr(sec, a, r):
    t = t_(sec)
    e = np.ones_like(t)
    e *= np.clip(t / a, 0, 1)
    e *= np.clip((sec - t) / r, 0, 1)
    return e


def sweep(f0, f1, sec, kind="sin"):
    t = t_(sec)
    f = f0 * (f1 / f0) ** (t / sec)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if kind == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    return np.sin(ph)


def pad(x, sec):
    n = int(SR * sec)
    if len(x) >= n:
        return x[:n]
    return np.concatenate([x, np.zeros(n - len(x))])


def at(buf, x, sec):
    i = int(SR * sec)
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i]


def reverb(x, size=0.45, mix=0.22):
    n = int(SR * size * 2.2)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (SR * size))
    ir = filt(ir, "lowpass", 5000, 2)
    wet = signal.fftconvolve(x, ir)[: len(x) + n]
    wet = np.concatenate([wet, np.zeros(len(x) + n - len(wet))])
    wet /= np.max(np.abs(wet)) + 1e-9
    dry = np.concatenate([x, np.zeros(n)])
    dry /= np.max(np.abs(dry)) + 1e-9
    return dry * (1 - mix) + wet * mix


def finish(x, peak=0.89, rev=None):
    if rev:
        x = reverb(x, *rev)
    x = x - np.mean(x)
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    fade = int(SR * 0.02)
    x[-fade:] *= np.linspace(1, 0, fade)
    # 뒤쪽 무음 자르기
    thr = 0.002
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx):
        x = x[: idx[-1] + int(SR * 0.05)]
    return x


def thump(f0, f1, sec, decay):
    return sweep(f0, f1, sec) * env_exp(sec, decay)


def grains(sec, count, lo, hi, glen=0.012, curve=1.0):
    out = np.zeros(int(SR * sec))
    for k in range(count):
        p = (k / count) ** curve * sec * 0.95
        g = filt(noise(glen), "bandpass", [lo, hi], 2) * env_exp(glen, glen / 3, 0.001)
        at(out, g * rng.uniform(0.3, 1.0), p + rng.uniform(0, 0.01))
    return out


# ───────────────────────────────────── 합성음
def s_warn():                     # 청동 징 — 모든 예고의 시작
    sec = 2.0
    x = np.zeros(int(SR * sec))
    for r, a, d in ((1, 1, 1.1), (2.1, 0.6, 0.7), (2.98, 0.45, 0.5), (4.2, 0.3, 0.35), (5.43, 0.2, 0.25)):
        f = 170 * r
        x += a * np.sin(2 * np.pi * f * t_(sec) + 0.3 * np.sin(2 * np.pi * 3.1 * t_(sec))) * env_exp(sec, d, 0.002)
    x += filt(noise(sec), "bandpass", [800, 4000], 2) * env_exp(sec, 0.03) * 0.8
    return finish(x, rev=(0.6, 0.3))


def s_cast():                     # 기운이 모이는 상승음
    sec = 1.1
    n = filt(noise(sec), "bandpass", [400, 3000], 2)
    sw = sweep(180, 640, sec) * 0.5 * (1 + 0.3 * np.sin(2 * np.pi * 9 * t_(sec)))
    e = (t_(sec) / sec) ** 2
    return finish((n * 0.6 + sw) * e * env_adsr(sec, 0.05, 0.08), rev=(0.3, 0.2))


def s_stomp():                    # 지면 강타
    sec = 1.2
    x = thump(70, 32, sec, 0.35) * 1.2
    x += filt(noise(sec), "lowpass", 420) * env_exp(sec, 0.18) * 1.4
    x += grains(sec, 90, 1500, 5000, curve=1.6) * 0.35
    return finish(x, rev=(0.5, 0.25))


def s_whirl():                    # 도끼 난무 — 휘익 휘익
    sec = 2.6
    t = t_(sec)
    n = noise(sec)
    center = 700 + 500 * np.sin(2 * np.pi * 4.2 * t)
    out = np.zeros_like(n)
    blk = 512
    for i in range(0, len(n), blk):
        c = center[i]
        seg = filt(n[max(0, i - 2048):i + blk], "bandpass", [c * 0.6, c * 1.6], 2)[-min(blk, len(n) - i):]
        out[i:i + blk] = seg
    am = (0.5 + 0.5 * np.sin(2 * np.pi * 4.2 * t - np.pi / 2)) ** 2
    return finish(out * am * env_adsr(sec, 0.15, 0.3))


def s_wallhit():                  # 벽에 박힘 — 돌 무너짐 + 도끼 울림
    sec = 1.6
    x = thump(90, 40, sec, 0.25) * 1.3
    x += filt(noise(sec), "lowpass", 900) * env_exp(sec, 0.12)
    x += grains(sec, 140, 700, 3500, glen=0.02, curve=1.3) * 0.5
    for f, a in ((880, 0.25), (1323, 0.18), (2210, 0.12)):
        x += a * np.sin(2 * np.pi * f * t_(sec)) * env_exp(sec, 0.5)
    return finish(x, rev=(0.45, 0.2))


def s_claw():                     # 발톱 세 번
    sec = 0.6
    x = np.zeros(int(SR * sec))
    for k in range(3):
        d = 0.11
        n = noise(d)
        sw = np.zeros_like(n)
        for i in range(0, len(n), 256):
            c = 4200 - 2600 * i / len(n)
            sw[i:i + 256] = filt(n[max(0, i - 1024):i + 256], "bandpass", [c * 0.7, c * 1.4], 2)[-len(sw[i:i + 256]):]
        at(x, sw * env_adsr(d, 0.01, 0.06), k * 0.13)
    return finish(x)


def fire_core(sec, lp, crackles):
    t = t_(sec)
    x = filt(noise(sec), "lowpass", lp) * (0.8 + 0.2 * np.sin(2 * np.pi * 7 * t + np.sin(2 * np.pi * 1.3 * t)))
    for _ in range(crackles):
        p = rng.uniform(0, sec - 0.02)
        at(x, filt(noise(0.006), "highpass", 2500) * rng.uniform(0.5, 1.5), p)
    return x


def s_breath():                   # 키메라 화염 브레스
    sec = 1.8
    return finish(fire_core(sec, 1400, 70) * env_adsr(sec, 0.12, 0.5), rev=(0.3, 0.15))


def s_spit():                     # 독 덩어리 발사
    sec = 0.35
    x = thump(420, 140, sec, 0.08)
    x += filt(noise(sec), "bandpass", [500, 1400], 2) * env_exp(sec, 0.05) * 0.8
    return finish(x)


def s_splat():                    # 독 웅덩이 — 철퍽 + 치이익
    sec = 1.5
    x = filt(noise(sec), "bandpass", [700, 2400], 2) * env_exp(sec, 0.09) * 1.2
    x += filt(noise(sec), "highpass", 5000) * env_exp(sec, 0.6, 0.05) * 0.25
    for _ in range(10):
        at(x, thump(rng.uniform(300, 700), rng.uniform(900, 1400), 0.04, 0.015) * 0.3, rng.uniform(0.05, 1.0))
    return finish(x)


def s_quake():                    # 케르베로스 저승의 충격파
    sec = 2.2
    x = thump(55, 28, sec, 0.7) * 1.4
    x += filt(noise(sec), "lowpass", 220) * env_exp(sec, 0.6) * 1.2
    x += filt(noise(sec), "bandpass", [2000, 6000], 2) * env_exp(sec, 0.04) * 0.5
    return finish(x, rev=(0.8, 0.3))


def s_fire():                     # 케르베로스 지옥불 — 낮고 어두운 불 + 울음
    sec = 1.6
    t = t_(sec)
    x = fire_core(sec, 750, 40)
    x += 0.25 * np.sin(2 * np.pi * (210 + 8 * np.sin(2 * np.pi * 5 * t)) * t)
    return finish(x * env_adsr(sec, 0.1, 0.45), rev=(0.4, 0.2))


def s_gate():                     # 지옥문 — 6초 드론
    sec = 6.5
    t = t_(sec)
    x = np.zeros_like(t)
    for f in (55.0, 55.35, 82.4, 110.6):
        x += sweep(f, f * 0.98, sec, "saw") * 0.3
    x = filt(x, "lowpass", 520)
    wind = filt(noise(sec), "bandpass", [200, 900], 2) * (0.3 + 0.3 * np.sin(2 * np.pi * 0.35 * t) ** 2)
    x += wind * 0.8
    x *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.9 * t)
    return finish(x * env_adsr(sec, 1.0, 1.4), rev=(0.8, 0.3))


def s_regrow():                   # 히드라 목이 자라남 — 질척이는 소리
    sec = 1.4
    x = np.zeros(int(SR * sec))
    for k in range(9):
        blip = sweep(rng.uniform(150, 260), rng.uniform(500, 800), 0.09) * env_adsr(0.09, 0.01, 0.05)
        blip += filt(noise(0.09), "bandpass", [300, 1200], 2) * env_exp(0.09, 0.03) * 0.6
        at(x, blip * rng.uniform(0.6, 1), k * 0.14 + rng.uniform(0, 0.04))
    x += filt(noise(sec), "lowpass", 300) * env_adsr(sec, 0.3, 0.4) * 0.4
    return finish(x)


def s_sever():                    # 머리 절단
    sec = 0.9
    x = filt(noise(0.03), "highpass", 1500)
    x = pad(x * env_exp(0.03, 0.008), sec) * 1.4
    x += thump(140, 55, sec, 0.12) * 1.2
    x += filt(noise(sec), "bandpass", [600, 2000], 2) * env_exp(sec, 0.15, 0.03) * 0.6
    return finish(x, rev=(0.3, 0.15))


def s_sear():                     # 불로 지짐 — 치이익
    sec = 1.6
    x = filt(noise(sec), "highpass", 3500) * env_exp(sec, 0.55, 0.02)
    for _ in range(50):
        at(x, filt(noise(0.005), "highpass", 2000) * rng.uniform(0.5, 2), rng.uniform(0, 1.3))
    return finish(x)


def s_gaze():                     # 메두사의 시선 — 불협 반짝임
    sec = 1.8
    t = t_(sec)
    x = np.zeros_like(t)
    for f, a in ((660, 0.5), (698.5, 0.45), (990, 0.3), (1047, 0.25), (1480, 0.12)):
        x += a * np.sin(2 * np.pi * f * t + 0.4 * np.sin(2 * np.pi * 5.5 * t))
    x *= 0.6 + 0.4 * np.sin(2 * np.pi * 12 * t) ** 2
    x *= (t / sec) ** 1.5
    return finish(x * env_adsr(sec, 0.05, 0.12), rev=(0.6, 0.35))


def s_petrify():                  # 석화 — 돌이 굳으며 갈라짐
    sec = 1.3
    x = grains(sec, 160, 900, 3200, glen=0.015, curve=0.6)
    x += filt(noise(sec), "lowpass", 280) * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * t_(sec))) * env_adsr(sec, 0.1, 0.3) * 0.6
    x += thump(120, 60, sec, 0.2) * 0.5
    return finish(x, rev=(0.3, 0.15))


def s_reflect():                  # 방패 반사 — 청명한 금속음
    sec = 2.0
    t = t_(sec)
    x = np.zeros_like(t)
    for f, a, d in ((1200, 0.5, 0.9), (1812, 0.4, 0.7), (2703, 0.3, 0.5), (3610, 0.2, 0.35)):
        x += a * np.sin(2 * np.pi * f * t) * env_exp(sec, d, 0.001)
    x += filt(noise(sec), "highpass", 3000) * env_exp(sec, 0.02) * 0.7
    return finish(x, rev=(0.5, 0.3))


def s_zone():                     # 석화 지대 — 낮게 갈리는 소리
    sec = 1.4
    t = t_(sec)
    x = 0.5 * np.sin(2 * np.pi * 68 * t)
    x += filt(noise(sec), "lowpass", 260) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t))
    x += grains(sec, 40, 600, 2000) * 0.3
    return finish(x * env_adsr(sec, 0.2, 0.4))


def s_slam():                     # 스킬라 촉수 강타 — 젖은 내려찍기
    sec = 1.3
    x = thump(75, 35, sec, 0.3) * 1.3
    x += filt(noise(sec), "bandpass", [900, 4200], 2) * env_exp(sec, 0.28, 0.01) * 0.9
    for _ in range(14):
        at(x, sweep(rng.uniform(400, 900), rng.uniform(1200, 2200), 0.03) * env_exp(0.03, 0.01) * 0.25, rng.uniform(0.05, 0.8))
    return finish(x, rev=(0.4, 0.2))


def s_whirlw():                   # 소용돌이 — 물이 도는 소리
    sec = 3.0
    t = t_(sec)
    n = noise(sec)
    center = 650 + 420 * np.sin(2 * np.pi * 0.9 * t)
    out = np.zeros_like(n)
    for i in range(0, len(n), 512):
        c = center[i]
        seg = filt(n[max(0, i - 2048):i + 512], "bandpass", [c * 0.5, c * 1.8], 2)[-min(512, len(n) - i):]
        out[i:i + 512] = seg
    for _ in range(40):
        at(out, sweep(rng.uniform(300, 600), rng.uniform(900, 1500), 0.03) * env_exp(0.03, 0.01) * 0.6, rng.uniform(0, 2.8))
    return finish(out * env_adsr(sec, 0.4, 0.6))


def s_cage():                     # 촉수 울타리 — 솟아오르는 촉수
    sec = 1.5
    t = t_(sec)
    x = sweep(70, 150, sec) * 0.5 * env_adsr(sec, 0.3, 0.4)
    x += filt(noise(sec), "lowpass", 500) * (0.5 + 0.5 * np.sin(2 * np.pi * 17 * t)) * env_adsr(sec, 0.2, 0.5)
    for _ in range(8):
        at(x, sweep(rng.uniform(200, 300), rng.uniform(600, 900), 0.08) * env_adsr(0.08, 0.01, 0.05) * 0.4, rng.uniform(0.1, 1.2))
    return finish(x, rev=(0.4, 0.2))


SYNTH = {
    "warn": s_warn, "cast": s_cast,
    "minotaur_stomp": s_stomp, "minotaur_whirl": s_whirl, "minotaur_wallhit": s_wallhit,
    "nemean_lion_claw": s_claw,
    "chimera_breath": s_breath, "chimera_spit": s_spit, "chimera_splat": s_splat,
    "cerberus_quake": s_quake, "cerberus_fire": s_fire, "cerberus_gate": s_gate,
    "hydra_regrow": s_regrow, "hydra_sever": s_sever, "hydra_sear": s_sear,
    "medusa_gaze": s_gaze, "medusa_petrify": s_petrify, "medusa_reflect": s_reflect, "medusa_zone": s_zone,
    "scylla_slam": s_slam, "scylla_whirl": s_whirlw, "scylla_cage": s_cage,
}


def own(name, pitch=1.0, volume=1.0):
    d = {"name": f"oly:boss/{name}"}
    if pitch != 1.0:
        d["pitch"] = pitch
    if volume != 1.0:
        d["volume"] = volume
    return d


def van(path, pitch=1.0, volume=1.0):
    d = {"name": f"minecraft:{path}"}
    if pitch != 1.0:
        d["pitch"] = pitch
    if volume != 1.0:
        d["volume"] = volume
    return d


def vans(prefix, nums, pitch, volume=1.0, sep=""):
    return [van(f"{prefix}{sep}{i}", pitch, volume) for i in nums]


EVENTS = {
    "boss.warn": [own("warn")],
    "boss.cast": [own("cast")],
    "boss.stun": vans("mob/ravager/stun", (1, 2, 3), 0.8),
    "boss.minotaur.snort": vans("mob/hoglin/angry", (1, 2, 3, 4), 0.55),
    "boss.minotaur.stomp": [own("minotaur_stomp")],
    "boss.minotaur.whirl": [own("minotaur_whirl")],
    "boss.minotaur.wallhit": [own("minotaur_wallhit")],
    "boss.minotaur.rage": vans("mob/ravager/roar", (1, 2, 3, 4), 0.55),
    "boss.nemean_lion.growl": vans("mob/wolf/big/growl", (1, 2, 3), 0.45),
    "boss.nemean_lion.roar": vans("mob/ravager/roar", (1, 2, 3, 4), 0.8),
    "boss.nemean_lion.claw": [own("nemean_lion_claw")],
    "boss.nemean_lion.mark": [van(f"mob/warden/heartbeat_{i}", 0.9) for i in (1, 2, 3, 4)],
    "boss.chimera.breath": [own("chimera_breath")],
    "boss.chimera.hiss": vans("mob/cat/hiss", (1, 2, 3), 0.5),
    "boss.chimera.spit": [own("chimera_spit")],
    "boss.chimera.splat": [own("chimera_splat")],
    "boss.chimera.bleat": vans("mob/goat/screaming_pre_ram", (1, 2, 3, 4, 5), 0.6),
    "boss.chimera.spike": [van("mob/evocation_illager/fangs", 0.7)],
    "boss.cerberus.bark": vans("mob/wolf/big/bark", (1, 2, 3), 0.55),
    "boss.cerberus.quake": [own("cerberus_quake")],
    "boss.cerberus.fire": [own("cerberus_fire")],
    "boss.cerberus.gate": [own("cerberus_gate")],
    "boss.cerberus.fury": [van(f"mob/warden/roar_{i}", 0.75) for i in (1, 2, 3, 4, 5)],
    "boss.hydra.hiss": vans("mob/cat/hiss", (1, 2, 3), 0.35),
    "boss.hydra.spit": [own("chimera_spit", 0.7)],
    "boss.hydra.splat": [own("chimera_splat", 0.8)],
    "boss.hydra.regrow": [own("hydra_regrow")],
    "boss.hydra.sever": [own("hydra_sever")],
    "boss.hydra.sear": [own("hydra_sear")],
    "boss.medusa.gaze": [own("medusa_gaze")],
    "boss.medusa.petrify": [own("medusa_petrify")],
    "boss.medusa.reflect": [own("medusa_reflect")],
    "boss.medusa.hiss": vans("mob/cat/hiss", (1, 2, 3), 0.8),
    "boss.medusa.zone": [own("medusa_zone")],
    "boss.scylla.slam": [own("scylla_slam")],
    "boss.scylla.bark": vans("mob/wolf/big/bark", (1, 2, 3), 0.8),
    "boss.scylla.whirl": [own("scylla_whirl")],
    "boss.scylla.cage": [own("scylla_cage")],
}

SUBTITLE_KO = {}


def build(check_vanilla=None):
    out_dir = os.path.join(ROOT, "sounds", "boss")
    os.makedirs(out_dir, exist_ok=True)
    for name, fn in SYNTH.items():
        x = fn().astype(np.float32)
        sf.write(os.path.join(out_dir, name + ".ogg"), x, SR, format="OGG", subtype="VORBIS")
    sounds = {}
    for ev, lst in EVENTS.items():
        sounds[ev] = {"sounds": lst}
    with open(os.path.join(ROOT, "sounds.json"), "w", encoding="utf-8") as f:
        json.dump(sounds, f, ensure_ascii=False, indent=1)
        f.write("\n")
    # 검증: 모든 참조 파일이 존재하는가
    bad = []
    vanilla = set(json.load(open(check_vanilla))) if check_vanilla else None
    for ev, lst in EVENTS.items():
        for s in lst:
            ns, p = s["name"].split(":")
            if ns == "oly":
                if not os.path.exists(os.path.join(ROOT, "sounds", p + ".ogg")):
                    bad.append((ev, s["name"]))
            elif vanilla is not None and p not in vanilla:
                bad.append((ev, s["name"]))
    return bad


if __name__ == "__main__":
    print("missing:", build(sys.argv[1] if len(sys.argv) > 1 else None))
