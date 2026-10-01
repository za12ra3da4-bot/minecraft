import { app } from '../game/AppState';
import { MenuShell } from './MenuShell';

const SECTIONS: [string, string[]][] = [
  ['목표 · Goal', ['국가를 선택하고 군대를 지휘해 적의 영토와 수도를 점령하세요.', '승리 조건: Conquest(최후의 국가/동맹), Domination(영토 60%), Capitals(모든 수도 점령).']],
  ['지도 · Map', ['마우스 휠 / 핀치로 확대·축소, 드래그로 지도 이동.', '줌 아웃하면 가까운 군대가 [국기 ×N] 클러스터로 묶이고, 줌 인하면 개별 군대와 정확한 병력 수가 보입니다.', 'WASD / 방향키로도 이동할 수 있습니다.']],
  ['군대 · Armies', ['내 군대(금색 ▼ 표시)를 클릭해 선택 → 지도 클릭으로 이동. 순간이동하지 않고 도로·지형에 따라 행군합니다.', '적 군대를 클릭하면 공격 명령, 내 다른 군대를 우클릭하면 합류(JOIN) 명령.', 'Shift+드래그로 여러 군대 선택, Ctrl+A 전체 선택, H 정지, M 합병, J 합류, F 선택 위치로 이동.', '오른쪽 패널의 SPLIT 슬라이더로 군대를 분할할 수 있습니다.']],
  ['전투 · Battle', ['전쟁 중인 국가의 군대가 마주치면 전투가 벌어집니다. 병력·사기·지형(언덕, 숲, 도시)이 결과를 좌우합니다.', '사기가 무너진 군대는 후퇴합니다. 모든 결과는 서버에서 계산됩니다.']],
  ['영토 · Territory', ['적(또는 무주지) 영토에 군대가 머무르면 점령 게이지가 차오르고 소유권이 바뀝니다. 붉은 선은 전선입니다.', '수도를 잃으면 비축 자원과 사기가 크게 떨어집니다.']],
  ['경제 · Economy', ['영토와 도시가 MANPOWER·INDUSTRY·SUPPLIES를 생산합니다. 군대는 보급품을 소비합니다.', '도시(■) 또는 수도(★)를 클릭하면 CREATE ARMY로 새 군대를 생산할 수 있습니다. 생산에는 시간이 걸립니다.']],
  ['외교 · Diplomacy', ['상단의 DIPLOMACY에서 선전포고, 평화 제안, 동맹 제안을 할 수 있습니다.']],
  ['모바일 · Mobile', ['한 손가락 드래그로 이동, 두 손가락 핀치로 확대, 탭으로 선택/이동, 길게 눌러 정보 보기.']],
];

export function HowToPlay() {
  return (
    <MenuShell>
      <div className="dialog-wrap">
        <div className="panel dialog">
          <div>
            <div className="panel-title">Field manual</div>
            <h2>How to Play</h2>
          </div>
          {SECTIONS.map(([title, lines]) => (
            <div key={title} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div className="panel-title">{title}</div>
              {lines.map((l) => (
                <div key={l} style={{ fontFamily: 'var(--font-body)', fontSize: 15, lineHeight: 1.5, color: 'var(--text)' }}>
                  {l}
                </div>
              ))}
            </div>
          ))}
          <div className="dialog-actions">
            <button className="btn ghost" onClick={() => app.go('menu')}>
              ← Back
            </button>
          </div>
        </div>
      </div>
    </MenuShell>
  );
}
