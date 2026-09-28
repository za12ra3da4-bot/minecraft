// 카메라 뷰 정의
//  pos: 카메라, tgt: 바라보는 점. y 가 '+2.62' 같은 문자열이면 그 지점 맨 위 블록 기준 높이
//    (맨 위 블록 y + 1 이 발바닥, 눈높이는 +1.62 → '+2.62' = 서 있는 플레이어 눈)
//  인게임(ig_): 바닐라 그래픽 + HUD.  renderDist = 렌더 거리(블록), fov = 70 (바닐라 기본)
const EYE = '+2.62';
const SIDEBAR = ['§7아르덴 왕국 RPG', ' ', '§f지역', '§e AREA', ' ', '§f레벨 §a27', '§f골드 §61,240', ' ', '§f진행 중인 퀘스트', '§b 별의 조각을 찾아서', ' ', '§7play.ardenm.kr'];
const ig = (o) => ({ fov: 70, detail: 256, far: 256, renderDist: 256, noLod: true, gui: 3, stand: !o.creative && !o.fixed, sidebarTitle: '⚔ 아르덴 ⚔', ...o, sidebar: o.area ? SIDEBAR.map(l => l.replace('AREA', o.area)) : undefined });

export const VIEWS = {
  // ── 인게임 1인칭
  ig_gate: ig({ pos: [3, EYE, 262], tgt: [0, 88, 214], area: '왕도 알더미어', actionbar: '— 왕도 알더미어 남문 —', slot: 0, sunDir: [-0.35, 0.55, 0.75] }),
  ig_street: ig({ pos: [1, EYE, 176], tgt: [0, 82, 60], area: '왕도 알더미어', slot: 3, sunDir: [-0.6, 0.6, 0.5] }),
  ig_square: ig({ pos: [-10, EYE, 57], tgt: [44, 92, 64], area: '대광장', actionbar: '— 대광장 —', slot: 7, sunDir: [-0.5, 0.65, -0.55] }),
  ig_castle: ig({ pos: [0, EYE, -18], tgt: [0, 110, -96], area: '알더미어 성', actionbar: '— 알더미어 성 —', slot: 0, sunDir: [0.4, 0.6, 0.7] }),
  ig_harbor: ig({ pos: [252, 70.62, 36], tgt: [228, 71, -8], fixed: true, area: '알더미어 항구', actionbar: '— 강변 항구 —', slot: 2, sunDir: [0.5, 0.55, 0.65] }),
  ig_millbrook: ig({ pos: [-448, EYE, 338], tgt: [-422, 88, 300], area: '밀브룩', actionbar: '— 밀브룩 —', slot: 3, sunDir: [0.3, 0.6, 0.75] }),
  ig_wizard: ig({ pos: [690, EYE, 684], tgt: [690, 104, 640], area: '별지기의 섬', actionbar: '— 별지기 마법사의 탑 —', slot: 7, sunDir: [-0.4, 0.55, 0.75] }),
  ig_dwarf: ig({ pos: [90, EYE, -662], tgt: [90, '+16', -690], area: '드워프 관문', actionbar: '— 드워프 왕국의 관문 —', slot: 1, sunDir: [0.3, 0.6, 0.75] }),
  ig_ruins: ig({ pos: [-760, EYE, 581], tgt: [-760, 84, 556], area: '그레이브 요새', actionbar: '— 무너진 그레이브 요새 —', slot: 0, sunDir: [0.4, 0.6, 0.7] }),
  ig_forest: ig({ pos: [-562, EYE, -92], tgt: [-622, 82, -113], area: '서쪽 숲', slot: 4, sunDir: [0.5, 0.65, 0.5] }),
  ig_cove: ig({ pos: [360, EYE, 498], tgt: [425, 64, 525], area: '갈매기 포구', actionbar: '— 갈매기 포구 —', slot: 8, sunDir: [-0.5, 0.55, -0.65] }),
  ig_fly: ig({ pos: [150, 150, 250], tgt: [0, 88, 10], creative: true, detail: 300, far: 420, renderDist: 420, area: '왕도 알더미어', slot: 5, sunDir: [-0.4, 0.6, 0.7] }),

  // ── 셰이더 느낌 공중 샷 (view.html)
  city: { pos: [300, 205, 340], tgt: [10, 76, 10], fov: 42, detail: 520, far: 1300, shadowR: 330 },
};
