"""Skript 정적 검사 (서버 없이 할 수 있는 만큼)

- 함수 정의/호출 대조: 없는 oly* 함수 호출, 인자 개수 불일치
- 줄 단위 문자열: 따옴표("" 이스케이프 포함) 짝, 문자열 안 % 짝
- 들여쓰기: 탭 금지, 4의 배수
- 데이터팩 함수 참조: olyCmd("function oly:boss/...") 가 실제 파일로 존재하는지
- 리소스 참조: "oly:fx/..", "oly:icon/..", oly:boss.<sound> 가 리소스팩에 있는지
python3 sklint.py
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..")
SCRIPTS = os.path.join(REPO, "Skript", "scripts")
PACK = os.path.join(REPO, "resourcepack", "olympus_pack", "assets")

errors = []


def err(f, n, msg):
    errors.append(f"{os.path.basename(f)}:{n}: {msg}")


def split_args(s):
    depth = 0
    cur = ""
    out = []
    instr = False
    i = 0
    while i < len(s):
        c = s[i]
        if c == '"':
            if instr and i + 1 < len(s) and s[i + 1] == '"':
                cur += '""'
                i += 2
                continue
            instr = not instr
        if not instr:
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif c == "," and depth == 0:
                out.append(cur)
                cur = ""
                i += 1
                continue
        cur += c
        i += 1
    if cur.strip():
        out.append(cur)
    return out


def strings_in(line):
    """줄에서 문자열 리터럴 구간을 뽑는다 ("" 는 이스케이프). 짝이 안 맞으면 None"""
    res = []
    i = 0
    instr = False
    start = 0
    depth_pct = False
    while i < len(line):
        c = line[i]
        if instr:
            if c == "%":
                depth_pct = not depth_pct
            elif c == '"' and not depth_pct:
                if i + 1 < len(line) and line[i + 1] == '"':
                    i += 2
                    continue
                res.append(line[start:i])
                instr = False
        else:
            if c == "#" and (i == 0 or line[i - 1] in " \t"):
                break
            if c == '"':
                instr = True
                start = i + 1
                depth_pct = False
        i += 1
    if instr:
        return None
    return res


def main():
    files = sorted(glob.glob(os.path.join(SCRIPTS, "*.sk")))
    defs = {}
    for f in files:
        for n, line in enumerate(open(f, encoding="utf-8"), 1):
            m = re.match(r"function (\w+)\((.*?)\)", line)
            if m:
                params = [p for p in m.group(2).split(",") if p.strip()]
                if m.group(1) in defs:
                    err(f, n, f"함수 중복 정의 {m.group(1)}")
                defs[m.group(1)] = (len(params), f, n)
    for f in files:
        for n, raw in enumerate(open(f, encoding="utf-8"), 1):
            line = raw.rstrip("\n")
            if "\t" in line[: len(line) - len(line.lstrip())]:
                err(f, n, "탭 들여쓰기")
            ind = len(line) - len(line.lstrip(" "))
            if line.strip() and ind % 4:
                err(f, n, f"들여쓰기 {ind}")
            if line.lstrip().startswith("#"):
                continue
            ss = strings_in(line)
            if ss is None:
                err(f, n, "따옴표 짝이 안 맞음")
                continue
            for st in ss:
                t = st.replace("%%", "")
                if t.count("%") % 2:
                    err(f, n, f"문자열 안 % 짝이 안 맞음: {st[:60]}")
            # 함수 호출 검사 (정의 줄 제외)
            if line.lstrip().startswith("function "):
                continue
            for m in re.finditer(r"\b(oly\w+)\(", line):
                name = m.group(1)
                # 괄호 짝 찾기
                i = m.end()
                depth = 1
                instr = False
                j = i
                while j < len(line) and depth:
                    c = line[j]
                    if c == '"':
                        instr = not instr
                    elif not instr:
                        if c == "(":
                            depth += 1
                        elif c == ")":
                            depth -= 1
                    j += 1
                args = split_args(line[i:j - 1])
                # 문자열 안(명령 텍스트)의 가짜 호출은 건너뛴다
                before = line[:m.start()]
                if strings_in(before + '"') is None and before.count('"') % 2 == 1:
                    continue
                if name not in defs:
                    err(f, n, f"정의되지 않은 함수 {name}")
                    continue
                want = defs[name][0]
                if len(args) != want:
                    err(f, n, f"{name} 인자 {len(args)}개 (정의 {want}개)")
    # 데이터팩 함수 참조
    for f in files:
        txt = open(f, encoding="utf-8").read()
        for m in re.finditer(r"function oly:boss/([a-z_]+)/([a-z_0-9/]+)(.?)", txt):
            boss, path = m.group(1), m.group(2)
            if m.group(3) == "%":
                continue
            p = os.path.join(REPO, boss, path + ".mcfunction")
            if boss in ("fx",):
                p = os.path.join(REPO, "fx", path + ".mcfunction")
            if not os.path.exists(p) and not path.startswith(("spawn", "rot", "remove", "idle", "walk", "attack", "roar", "charge", "breath", "gaze", "grow_")):
                errors.append(f"{os.path.basename(f)}: 데이터팩 함수 없음 oly:boss/{boss}/{path}")
        for m in re.finditer(r'"oly:(fx|icon|minotaur|nemean_lion|chimera|cerberus|hydra|medusa|scylla)/([a-z_0-9]+)"', txt.replace('""', '"')):
            p = os.path.join(PACK, "oly", "items", m.group(1), m.group(2) + ".json")
            if not os.path.exists(p):
                errors.append(f"{os.path.basename(f)}: 아이템 모델 없음 oly:{m.group(1)}/{m.group(2)}")
    sounds = json.load(open(os.path.join(PACK, "oly", "sounds.json")))
    for f in files:
        txt = open(f, encoding="utf-8").read()
        for m in re.finditer(r'olySfx\("([a-z_.]+)"', txt):
            if "boss." + m.group(1) not in sounds:
                errors.append(f"{os.path.basename(f)}: 사운드 없음 oly:boss.{m.group(1)}")
        for m in re.finditer(r"oly:boss\.([a-z_.]+)", txt):
            if "boss." + m.group(1) not in sounds:
                errors.append(f"{os.path.basename(f)}: 사운드 없음 oly:boss.{m.group(1)}")
        for m in re.finditer(r'olySfx\("%\{_id\}%\.([a-z_]+)"', txt):
            for b in ("chimera", "hydra"):
                if f"boss.{b}.{m.group(1)}" not in sounds:
                    errors.append(f"{os.path.basename(f)}: 사운드 없음 oly:boss.{b}.{m.group(1)}")
        for m in re.finditer(r'olyFx\w*\([^)]*"(oly:[a-z_]+/[a-z_0-9]+)"', txt):
            pass
    # 아이콘 키
    icons = set(re.findall(r'if \{_k\} is "([a-z_]+)":', open(os.path.join(SCRIPTS, "10-bossfx.sk"), encoding="utf-8").read()))
    for f in files:
        txt = open(f, encoding="utf-8").read()
        for m in re.finditer(r'olySkBegin\("([a-z_]+)", "([a-z_]+)"\)', txt):
            if f"{m.group(1)}_{m.group(2)}" not in icons:
                errors.append(f"{os.path.basename(f)}: 아이콘/스킬명 없음 {m.group(1)}_{m.group(2)}")
        for m in re.finditer(r'"((?:minotaur|nemean_lion|chimera|cerberus|hydra|medusa|scylla|common)_[a-z]+)"', txt):
            if m.group(1) not in icons and not m.group(1).startswith("boss_"):
                errors.append(f"{os.path.basename(f)}: 아이콘 키 없음 {m.group(1)}")
    print("\n".join(errors) if errors else "sklint: 문제 없음")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
