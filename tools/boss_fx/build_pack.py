"""resourcepack/olympus_pack/ → resourcepack/olympus_pack.zip (서버에 올리는 파일)

- 원래 zip 처럼 모든 항목 날짜를 2026-01-01 00:00 으로 고정 (같은 내용이면 같은 zip)
- 넣기 전에 검사: JSON 문법, 모델 → 텍스처, 아이템 정의 → 모델, 폰트 → 텍스처, sounds.json → .ogg
python3 build_pack.py
"""
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "resourcepack", "olympus_pack")
OUT = os.path.join(HERE, "..", "..", "resourcepack", "olympus_pack.zip")
DATE = (2026, 1, 1, 0, 0, 0)


def rel(p):
    return os.path.relpath(p, SRC).replace(os.sep, "/")


def res(ns_path, kind, ext):
    ns, p = ns_path.split(":", 1) if ":" in ns_path else ("minecraft", ns_path)
    return os.path.join(SRC, "assets", ns, kind, p + ext)


def model_refs(node, out):
    if isinstance(node, dict):
        if node.get("type") in ("minecraft:model", "model") and "model" in node:
            out.append(node["model"])
        for v in node.values():
            model_refs(v, out)
    elif isinstance(node, list):
        for v in node:
            model_refs(v, out)


def check():
    bad = []
    files = []
    for root, _, fs in os.walk(SRC):
        for f in fs:
            files.append(os.path.join(root, f))
    for p in files:
        if p.endswith((".json", ".mcmeta")):
            try:
                d = json.load(open(p, encoding="utf-8"))
            except Exception as e:  # noqa
                bad.append(f"JSON 오류 {rel(p)}: {e}")
                continue
            r = rel(p)
            if "/models/" in r:
                for k, t in d.get("textures", {}).items():
                    if t.startswith("#"):
                        continue
                    if not os.path.exists(res(t, "textures", ".png")) and not t.startswith("minecraft:"):
                        bad.append(f"텍스처 없음 {r} → {t}")
                par = d.get("parent")
                if par and not par.startswith(("minecraft:", "builtin/")) and not os.path.exists(res(par, "models", ".json")):
                    bad.append(f"부모 모델 없음 {r} → {par}")
                for el in d.get("elements", []):
                    for v in el["from"] + el["to"]:
                        if v < -16 or v > 32:
                            bad.append(f"요소 범위 밖 {r}: {v}")
                    rot = el.get("rotation")
                    if rot and rot.get("angle") not in (-45, -22.5, 0, 22.5, 45):
                        bad.append(f"회전 각도 {r}: {rot}")
            if "/items/" in r:
                refs = []
                model_refs(d, refs)
                for m in refs:
                    if m.startswith("minecraft:"):
                        continue
                    if not os.path.exists(res(m, "models", ".json")):
                        bad.append(f"모델 없음 {r} → {m}")
            if "/font/" in r:
                for pr in d.get("providers", []):
                    if pr.get("type") == "minecraft:bitmap":
                        f = pr["file"]
                        ns, fp = f.split(":", 1)
                        if not os.path.exists(os.path.join(SRC, "assets", ns, "textures", fp)):
                            bad.append(f"폰트 텍스처 없음 {r} → {f}")
            if r.endswith("sounds.json"):
                ns = r.split("/")[1]
                for ev, e in d.items():
                    for s in e["sounds"]:
                        n = s if isinstance(s, str) else s["name"]
                        sns, sp = n.split(":", 1) if ":" in n else (ns, n)
                        if sns != "minecraft" and not os.path.exists(os.path.join(SRC, "assets", sns, "sounds", sp + ".ogg")):
                            bad.append(f"사운드 파일 없음 {ev} → {n}")
    return bad, files


def build():
    bad, files = check()
    if bad:
        print("\n".join(bad))
        sys.exit(1)
    files.sort(key=rel)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            zi = zipfile.ZipInfo(rel(p), DATE)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o600 << 16
            with open(p, "rb") as fh:
                z.writestr(zi, fh.read())
    print(f"olympus_pack.zip: {len(files)} files, {os.path.getsize(OUT) // 1024} KB")


if __name__ == "__main__":
    build()
