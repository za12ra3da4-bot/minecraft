/*
 * FC온라인 스쿼드 코치 — shared spec.
 * Loaded by the page (<script src="coach-spec.js">, global `CoachSpec`) and by
 * server.mjs (require). Holds the coach prompt, the result JSON schema, result
 * normalization and the example squad shown before the first request.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.CoachSpec = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var SYSTEM_PROMPT = [
    'You are "FC온라인 스쿼드 코치", a veteran squad builder and tactics coach for Nexon\'s FC Online',
    "(EA SPORTS FC Online, formerly FIFA Online 4 / 피파온라인4). Korean players describe the squad they",
    "want in casual Korean. You build it in the game's own terms: a starting XI, a bench, team tactics,",
    "per-player instructions (개인 전술), set-piece takers, situational tactic tweaks, play tips,",
    "alternative players and caveats.",
    "",
    "Follow the request exactly",
    "- Hard constraints come first: must-include players, formation, BP budget, team color (팀컬러: club,",
    "  nation or other), season/card restrictions, enhancement (강화) level, salary cap (급여), playstyle,",
    "  and whether the squad is for 공식경기 (manual play) or 감독모드 (the AI plays).",
    "- If constraints conflict or cannot all be met, meet as many as possible and explain the trade-off",
    "  in caveats. If the request is vague, pick a strong, sensible default and say what you assumed in reply.",
    "- When a CURRENT SQUAD is given, the new message is an edit request: change only what the user asked",
    "  for, plus whatever that change forces (e.g. tactics that no longer fit), and keep the rest identical.",
    "- If an owned-player list is given, build from it as the request says (only those players, or those first).",
    "",
    "FC Online conventions",
    "- Use real players and real FC Online season/card classes you know exist (e.g. ICON, ICON TM, TOTY, TOTS,",
    "  UCL, BTB, LN, UT, NHD, HR, MOG, LIVE). Never invent a season. Write card as \"<season> +<강화>\",",
    "  e.g. \"24TOTY +5\".",
    "- ovr: the card's approximate in-game overall at its position, including enhancement; 0 if unknown.",
    "- salary: the card's 급여 as an integer; 0 if unknown. Keep the squad's total salary within the game's",
    "  salary cap as you know it.",
    "- price: approximate BP market price in Korean units, e.g. \"약 350억 BP\", \"약 1.2조 BP\".",
    "  total_cost: the starters plus bench, e.g. \"약 4,800억 BP\". Prices are your estimates and can be",
    "  out of date: say so once in caveats and never present them as live market data.",
    "- team_tactics: choice-type settings from FC Online's 팀 전술 screen with the game's Korean labels as you",
    "  know them (e.g. 수비 스타일, 빌드업 플레이). sliders: numeric settings on the game's actual scale",
    "  (e.g. 수비 폭, 수비 깊이, 공격 폭, 박스 안 선수 수, 코너킥, 프리킥). group is \"공격\", \"수비\" or \"세트피스\".",
    "- instructions: 1-3 short 개인 전술 options per starter in FC Online wording.",
    "- game_plans: 2-3 situational tweaks for the saved tactic slots (e.g. 선제골 후 잠그기, 지고 있을 때 총공격),",
    "  naming the settings and substitutions to change.",
    "- attack_tips / defense_tips: 3-5 concrete tips each. For 공식경기, explain how to play this setup by hand",
    "  (patterns, which player to target, moves that suit it). For 감독모드, focus on settings, since the AI plays.",
    "",
    "Pitch layout",
    "- Exactly 11 starters with exactly one GK. pos uses FC Online codes: GK, LB, LCB, CB, RCB, RB, LWB, RWB,",
    "  LDM, CDM, RDM, LCM, CM, RCM, LM, RM, LAM, CAM, RAM, LW, RW, LF, CF, RF, LS, ST, RS.",
    "- x: 0 = left touchline, 100 = right touchline. y: 0 = own goal line, 100 = opponent goal line (the team",
    "  attacks upward). GK at y 6; back line y 22-28; holding midfielders 38-46; central midfielders 48-56;",
    "  attacking midfielders 58-66; wingers 68-76; strikers 78-86. Left-sided positions have x below 50.",
    "  Keep every pair of players at least 10 units apart.",
    "- Order starters GK first, then defenders left to right, then midfielders, then attackers.",
    "",
    "Writing",
    "- Every text value in Korean. Player names in the Korean spelling FC Online and Korean media use",
    "  (손흥민, 해리 케인, 킬리안 음바페).",
    "- reply: 1-3 friendly sentences in 존댓말 about what you built or changed.",
    "- why: one short sentence. role: a short role name (e.g. 인사이드 포워드, 빌드업 센터백).",
    "- bench: 5-7 players. alternatives: 2-4 swaps (cheaper or stronger). caveats: 1-4 items."
  ].join("\n");

  // Plain-text description of the JSON shape, for callers that cannot pass a schema.
  var SHAPE_TEXT = [
    "Reply with only one JSON object in exactly this shape (no Markdown, no text before or after):",
    "{",
    '  "reply": string,',
    '  "squad_name": string,',
    '  "concept": string,',
    '  "formation": string,            // e.g. "4-2-3-1"',
    '  "team_color": string,           // e.g. "토트넘 (클럽 팀컬러)" or "없음"',
    '  "total_cost": string,',
    '  "starters": [ { "pos": string, "name": string, "card": string, "ovr": integer, "salary": integer,',
    '                  "price": string, "role": string, "x": integer, "y": integer,',
    '                  "instructions": [string], "why": string } ],   // exactly 11',
    '  "bench": [ { "pos": string, "name": string, "card": string, "ovr": integer, "salary": integer,',
    '               "price": string, "why": string } ],',
    '  "team_tactics": [ { "group": string, "label": string, "value": string, "why": string } ],',
    '  "sliders": [ { "group": string, "label": string, "value": integer, "min": integer, "max": integer, "why": string } ],',
    '  "set_pieces": [ { "duty": string, "player": string } ],   // 주장, 페널티킥, 프리킥, 왼쪽/오른쪽 코너킥',
    '  "game_plans": [ { "when": string, "change": string } ],',
    '  "attack_tips": [string],',
    '  "defense_tips": [string],',
    '  "alternatives": [ { "replace": string, "candidate": string, "price": string, "why": string } ],',
    '  "caveats": [string]',
    "}"
  ].join("\n");

  // JSON schema for structured outputs (server). Every object closed, every field required.
  function obj(props) {
    return { type: "object", properties: props, required: Object.keys(props), additionalProperties: false };
  }
  var STR = { type: "string" };
  var INT = { type: "integer" };
  var STRS = { type: "array", items: STR };
  var RESULT_SCHEMA = obj({
    reply: STR,
    squad_name: STR,
    concept: STR,
    formation: STR,
    team_color: STR,
    total_cost: STR,
    starters: {
      type: "array",
      items: obj({
        pos: STR, name: STR, card: STR, ovr: INT, salary: INT, price: STR, role: STR,
        x: INT, y: INT, instructions: STRS, why: STR
      })
    },
    bench: {
      type: "array",
      items: obj({ pos: STR, name: STR, card: STR, ovr: INT, salary: INT, price: STR, why: STR })
    },
    team_tactics: { type: "array", items: obj({ group: STR, label: STR, value: STR, why: STR }) },
    sliders: {
      type: "array",
      items: obj({ group: STR, label: STR, value: INT, min: INT, max: INT, why: STR })
    },
    set_pieces: { type: "array", items: obj({ duty: STR, player: STR }) },
    game_plans: { type: "array", items: obj({ when: STR, change: STR }) },
    attack_tips: STRS,
    defense_tips: STRS,
    alternatives: {
      type: "array",
      items: obj({ replace: STR, candidate: STR, price: STR, why: STR })
    },
    caveats: STRS
  });

  var MODES = { manual: "공식경기 (직접 조작)", coach: "감독모드 (AI가 경기 운영)" };

  function clip(v, max) {
    var s = typeof v === "string" ? v.trim() : "";
    return s.length > max ? s.slice(0, max) : s;
  }

  // Sanitizes whatever the page sends; used on both sides so the prompt is identical.
  function cleanPayload(p) {
    p = p && typeof p === "object" ? p : {};
    var current = null;
    if (p.current) {
      try { current = normalizeResult(p.current); } catch (e) { current = null; }
    }
    var history = Array.isArray(p.history) ? p.history : [];
    return {
      request: clip(p.request, 2000),
      mode: p.mode === "coach" ? "coach" : "manual",
      budget: clip(p.budget, 100),
      owned: clip(p.owned, 4000),
      current: current,
      history: current ? history.slice(-6).map(function (h) { return clip(h, 500); }).filter(Boolean) : []
    };
  }

  function buildUserMessage(payload) {
    var p = cleanPayload(payload);
    var parts = [];
    parts.push("## 경기 방식\n" + MODES[p.mode]);
    parts.push("## 예산\n" + (p.budget ? p.budget + " (BP)" : "따로 지정 안 함 (요청 문장에 있으면 그대로 따르세요)"));
    if (p.owned) parts.push("## 보유 선수 목록\n" + p.owned);
    if (p.current) {
      parts.push(
        "## CURRENT SQUAD — edit this; keep everything the user did not ask to change\n" +
          JSON.stringify(p.current)
      );
      if (p.history.length) {
        parts.push("## 지금까지의 요청\n" + p.history.map(function (h, i) { return i + 1 + ". " + h; }).join("\n"));
      }
      parts.push("## 새 수정 요청\n" + p.request);
    } else {
      parts.push("## 요청\n" + p.request);
    }
    return parts.join("\n\n");
  }

  // One self-contained prompt for runtimes without a system prompt or schema (the claude.ai artifact).
  function buildStandalonePrompt(payload) {
    return SYSTEM_PROMPT + "\n\n" + SHAPE_TEXT + "\n\n---\n\n" + buildUserMessage(payload);
  }

  // Fallback coordinates when a starter comes back without usable x/y.
  var POS_XY = {
    GK: [50, 6], LB: [14, 27], LCB: [37, 23], CB: [50, 22], RCB: [63, 23], RB: [86, 27],
    LWB: [12, 40], RWB: [88, 40], LDM: [38, 41], CDM: [50, 41], RDM: [62, 41],
    LCM: [34, 51], CM: [50, 51], RCM: [66, 51], LM: [14, 58], RM: [86, 58],
    LAM: [32, 63], CAM: [50, 63], RAM: [68, 63], LW: [16, 73], RW: [84, 73],
    LF: [34, 80], CF: [50, 80], RF: [66, 80], LS: [40, 85], ST: [50, 86], RS: [60, 85]
  };

  function str(v) {
    return typeof v === "string" ? v.trim() : v == null ? "" : String(v).trim();
  }
  function int(v) {
    var n = Math.round(Number(v));
    return isFinite(n) ? n : 0;
  }
  function list(v) {
    return Array.isArray(v) ? v.filter(function (x) { return x && typeof x === "object"; }) : [];
  }
  function strs(v) {
    return Array.isArray(v) ? v.map(str).filter(Boolean) : [];
  }
  function clamp(v, lo, hi) {
    return Math.min(hi, Math.max(lo, v));
  }

  // Pushes apart tokens that would overlap on the drawn pitch.
  function spread(players) {
    for (var pass = 0; pass < 4; pass++) {
      for (var i = 0; i < players.length; i++) {
        for (var j = i + 1; j < players.length; j++) {
          var a = players[i], b = players[j];
          var dx = b.x - a.x, dy = b.y - a.y;
          if (Math.abs(dx) < 12 && Math.abs(dy) < 7) {
            var push = (12 - Math.abs(dx)) / 2;
            var dir = dx === 0 ? (j % 2 ? 1 : -1) : dx > 0 ? 1 : -1;
            a.x = clamp(a.x - dir * push, 6, 94);
            b.x = clamp(b.x + dir * push, 6, 94);
          }
        }
      }
    }
    players.forEach(function (p) { p.x = Math.round(p.x); p.y = Math.round(p.y); });
  }

  function normalizeResult(raw) {
    var o = raw && typeof raw === "object" && !Array.isArray(raw) ? raw : {};
    var starters = list(o.starters).slice(0, 11).map(function (p) {
      var pos = str(p.pos).toUpperCase() || "?";
      var fb = POS_XY[pos] || [50, 50];
      var hasXY = p.x !== undefined && p.y !== undefined && isFinite(Number(p.x)) && isFinite(Number(p.y));
      return {
        pos: pos,
        name: str(p.name) || "미정",
        card: str(p.card),
        ovr: Math.max(0, int(p.ovr)),
        salary: Math.max(0, int(p.salary)),
        price: str(p.price),
        role: str(p.role),
        x: clamp(hasXY ? int(p.x) : fb[0], 5, 95),
        y: clamp(hasXY ? int(p.y) : fb[1], 4, 94),
        instructions: strs(p.instructions).slice(0, 4),
        why: str(p.why)
      };
    });
    if (!starters.length) throw new Error("선발 명단이 비어 있어요.");
    spread(starters);
    return {
      reply: str(o.reply),
      squad_name: str(o.squad_name) || "이름 없는 스쿼드",
      concept: str(o.concept),
      formation: str(o.formation),
      team_color: str(o.team_color),
      total_cost: str(o.total_cost),
      starters: starters,
      bench: list(o.bench).slice(0, 9).map(function (p) {
        return {
          pos: str(p.pos).toUpperCase(),
          name: str(p.name) || "미정",
          card: str(p.card),
          ovr: Math.max(0, int(p.ovr)),
          salary: Math.max(0, int(p.salary)),
          price: str(p.price),
          why: str(p.why)
        };
      }),
      team_tactics: list(o.team_tactics).map(function (t) {
        return { group: str(t.group), label: str(t.label), value: str(t.value), why: str(t.why) };
      }).filter(function (t) { return t.label && t.value; }),
      sliders: list(o.sliders).map(function (t) {
        var min = int(t.min), max = int(t.max);
        if (max <= min) { min = 1; max = 10; }
        return { group: str(t.group), label: str(t.label), value: clamp(int(t.value), min, max), min: min, max: max, why: str(t.why) };
      }).filter(function (t) { return t.label; }),
      set_pieces: list(o.set_pieces).map(function (t) {
        return { duty: str(t.duty), player: str(t.player) };
      }).filter(function (t) { return t.duty && t.player; }),
      game_plans: list(o.game_plans).map(function (t) {
        return { when: str(t.when), change: str(t.change) };
      }).filter(function (t) { return t.when && t.change; }),
      attack_tips: strs(o.attack_tips),
      defense_tips: strs(o.defense_tips),
      alternatives: list(o.alternatives).map(function (t) {
        return { replace: str(t.replace), candidate: str(t.candidate), price: str(t.price), why: str(t.why) };
      }).filter(function (t) { return t.candidate; }),
      caveats: strs(o.caveats)
    };
  }

  // Rough progress from the partially written JSON, for the status line.
  var PHASES = [
    ["caveats", "마무리하는 중"],
    ["alternatives", "대체 선수 찾는 중"],
    ["attack_tips", "플레이 팁 정리하는 중"],
    ["game_plans", "상황별 전술 짜는 중"],
    ["set_pieces", "세트피스 키커 정하는 중"],
    ["team_tactics", "팀 전술 설정하는 중"],
    ["bench", "벤치 구성하는 중"],
    ["starters", "선발 배치하는 중"]
  ];
  function progressFromText(text) {
    text = String(text || "");
    var placed = Math.min(11, (text.match(/"x"\s*:/g) || []).length);
    var phase = "스쿼드 콘셉트 잡는 중";
    for (var i = 0; i < PHASES.length; i++) {
      if (text.indexOf('"' + PHASES[i][0] + '"') !== -1) { phase = PHASES[i][1]; break; }
    }
    if (phase === "선발 배치하는 중") phase += " (" + placed + "/11)";
    return { chars: text.length, placed: placed, phase: phase };
  }

  function totalSalary(r) {
    var sum = 0;
    r.starters.concat(r.bench).forEach(function (p) { sum += p.salary || 0; });
    return sum;
  }

  function toPlainText(r) {
    var out = [];
    out.push("■ " + r.squad_name + (r.formation ? " (" + r.formation + ")" : ""));
    if (r.concept) out.push(r.concept);
    var meta = [];
    if (r.team_color) meta.push("팀컬러: " + r.team_color);
    if (r.total_cost) meta.push("예상 총액: " + r.total_cost);
    if (totalSalary(r)) meta.push("급여 합계: " + totalSalary(r));
    if (meta.length) out.push(meta.join(" / "));
    out.push("", "[선발]");
    r.starters.forEach(function (p) {
      var bits = [p.card, p.ovr ? "OVR " + p.ovr : "", p.price].filter(Boolean).join(", ");
      out.push(p.pos + " " + p.name + (bits ? " (" + bits + ")" : "") + (p.role ? " - " + p.role : ""));
      if (p.instructions.length) out.push("   개인 전술: " + p.instructions.join(" / "));
    });
    if (r.bench.length) {
      out.push("", "[벤치]");
      r.bench.forEach(function (p) { out.push(p.pos + " " + p.name + (p.card ? " (" + p.card + ")" : "")); });
    }
    if (r.team_tactics.length || r.sliders.length) {
      out.push("", "[팀 전술]");
      r.team_tactics.forEach(function (t) { out.push("- " + t.label + ": " + t.value); });
      r.sliders.forEach(function (t) { out.push("- " + t.label + ": " + t.value + " / " + t.max); });
    }
    if (r.set_pieces.length) {
      out.push("", "[세트피스]");
      r.set_pieces.forEach(function (t) { out.push("- " + t.duty + ": " + t.player); });
    }
    if (r.game_plans.length) {
      out.push("", "[상황별 전술]");
      r.game_plans.forEach(function (t) { out.push("- " + t.when + ": " + t.change); });
    }
    return out.join("\n");
  }

  // Shown before the first request. Card, price and salary are left blank on purpose.
  var EXAMPLE = normalizeResult({
    reply: "예시 스쿼드예요. 원하는 조건을 말해주시면 시즌·강화·BP 가격까지 맞춰서 새로 짜드릴게요.",
    squad_name: "태극전사 역습 4-2-3-1",
    concept: "대한민국 국가 팀컬러로 손흥민의 뒷공간 침투와 이강인의 킬패스를 살리는 빠른 역습형 스쿼드예요.",
    formation: "4-2-3-1",
    team_color: "대한민국 (국가 팀컬러)",
    total_cost: "",
    starters: [
      { pos: "GK", name: "조현우", role: "반응형 골키퍼", x: 50, y: 6, instructions: ["빌드업 시 짧게 연결"], why: "1:1 선방이 좋아 역습 뒤 실점 위기를 줄여줘요." },
      { pos: "LB", name: "이명재", role: "오버래핑 풀백", x: 14, y: 28, instructions: ["공격 가담 많이", "크로스 위주"], why: "손흥민이 안으로 좁힐 때 바깥 공간을 채워요." },
      { pos: "LCB", name: "김민재", role: "커버형 센터백", x: 37, y: 23, instructions: ["인터셉트 적극적"], why: "라인 뒷공간을 혼자 커버할 수 있는 속도와 힘이 있어요." },
      { pos: "RCB", name: "조유민", role: "빌드업 센터백", x: 63, y: 23, instructions: ["수비 위치 유지"], why: "김민재가 전진할 때 뒤를 지켜줘요." },
      { pos: "RB", name: "설영우", role: "밸런스 풀백", x: 86, y: 28, instructions: ["공격 가담 균형"], why: "이강인이 안쪽으로 들어올 때 측면 폭을 만들어요." },
      { pos: "LDM", name: "박용우", role: "홀딩 미드필더", x: 38, y: 42, instructions: ["공격 가담 적게", "중앙 커버"], why: "역습을 당할 때 첫 번째 저지선이에요." },
      { pos: "RDM", name: "황인범", role: "딥 라잉 플레이메이커", x: 62, y: 44, instructions: ["전진 패스 위주"], why: "볼을 뺏은 직후 전방으로 빠르게 연결해요." },
      { pos: "CAM", name: "이재성", role: "박스 투 박스 공미", x: 50, y: 62, instructions: ["박스 침투", "전방 압박"], why: "활동량으로 공수 간격을 좁혀줘요." },
      { pos: "LW", name: "손흥민", role: "인사이드 포워드", x: 17, y: 73, instructions: ["뒷공간 침투", "수비 가담 적게"], why: "역습의 마무리 담당이에요." },
      { pos: "RW", name: "이강인", role: "플레이메이커 윙어", x: 83, y: 71, instructions: ["안쪽으로 좁히기", "킬패스 위주"], why: "왼발 스루패스로 손흥민을 살려요." },
      { pos: "ST", name: "오현규", role: "타깃 스트라이커", x: 50, y: 85, instructions: ["등지고 연계", "박스 안 대기"], why: "센터백을 끌고 다니며 윙어에게 공간을 열어줘요." }
    ],
    bench: [
      { pos: "GK", name: "김승규", why: "빌드업이 필요한 경기용 골키퍼예요." },
      { pos: "CB", name: "김영권", why: "리드를 지킬 때 들어가는 수비 교체예요." },
      { pos: "CM", name: "백승호", why: "중거리 슈팅이 필요할 때 써요." },
      { pos: "CAM", name: "배준호", why: "밀집 수비를 드리블로 풀어요." },
      { pos: "RW", name: "황희찬", why: "후반 스피드 교체 카드예요." },
      { pos: "ST", name: "조규성", why: "크로스 위주로 바꿀 때 공중볼 타깃이에요." }
    ],
    team_tactics: [
      { group: "공격", label: "빌드업 플레이", value: "빠른 빌드업", why: "볼을 뺏자마자 윙어에게 연결하는 게 핵심이에요." },
      { group: "수비", label: "수비 스타일", value: "후퇴", why: "내려앉은 뒤 손흥민이 뛸 공간을 남겨둬요." }
    ],
    sliders: [
      { group: "수비", label: "수비 폭", value: 4, min: 1, max: 10, why: "중앙을 좁혀서 스루패스를 막아요." },
      { group: "수비", label: "수비 깊이", value: 4, min: 1, max: 10, why: "라인을 내려 뒷공간을 줄여요." },
      { group: "공격", label: "공격 폭", value: 6, min: 1, max: 10, why: "양쪽 윙어가 넓게 벌려 역습 루트를 만들어요." },
      { group: "공격", label: "박스 안 선수 수", value: 5, min: 1, max: 10, why: "역습 때 무리하게 올라가지 않도록 중간값이에요." }
    ],
    set_pieces: [
      { duty: "주장", player: "손흥민" },
      { duty: "페널티킥", player: "손흥민" },
      { duty: "프리킥", player: "이강인" },
      { duty: "코너킥", player: "이강인" }
    ],
    game_plans: [
      { when: "선제골 후 잠그기", change: "수비 깊이 3, 박스 안 선수 수 3으로 내리고 이재성 대신 백승호를 넣어요." },
      { when: "지고 있을 때", change: "박스 안 선수 수 7, 공격 폭 7로 올리고 황희찬·조규성을 동시에 투입해요." }
    ],
    attack_tips: [
      "공을 뺏으면 황인범에게 먼저 주고, 바로 손흥민 쪽 뒷공간으로 스루패스를 노리세요.",
      "이강인이 오른쪽에서 안으로 들어오면 설영우가 바깥으로 오버래핑해요. 둘 중 비는 쪽을 쓰세요.",
      "오현규에게 등지는 패스를 넣고, 2선에서 침투하는 이재성에게 원터치로 내주세요."
    ],
    defense_tips: [
      "상대 윙어를 쫓아가지 말고 두 수비형 미드필더로 중앙부터 막으세요.",
      "김민재로만 전진 압박하고 조유민은 뒤에 남겨두세요."
    ],
    alternatives: [
      { replace: "오현규", candidate: "조규성", price: "", why: "크로스와 공중볼 위주로 갈 때 더 잘 맞아요." },
      { replace: "이명재", candidate: "김진수", price: "", why: "왼발 크로스가 더 정교해요." }
    ],
    caveats: ["예시 스쿼드라 시즌·강화·가격·급여는 비워 뒀어요."]
  });

  return {
    SYSTEM_PROMPT: SYSTEM_PROMPT,
    SHAPE_TEXT: SHAPE_TEXT,
    RESULT_SCHEMA: RESULT_SCHEMA,
    MODES: MODES,
    cleanPayload: cleanPayload,
    buildUserMessage: buildUserMessage,
    buildStandalonePrompt: buildStandalonePrompt,
    normalizeResult: normalizeResult,
    progressFromText: progressFromText,
    totalSalary: totalSalary,
    toPlainText: toPlainText,
    EXAMPLE: EXAMPLE
  };
});
