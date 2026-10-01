import { app } from '../game/AppState';
import { MenuShell } from './MenuShell';

const SECTIONS: [string, string[]][] = [
  ['🎯 목표', ['1812년 유럽에서 나라 하나를 골라 군대를 지휘하고, 적의 영토와 수도를 점령하세요.', '승리 조건은 정복(마지막 생존), 지배(영토 60%), 수도(모든 수도 점령) 중에서 고릅니다.']],
  ['🖱 부대 고르기', ['내 부대(국기 위 금색 ▼)를 클릭하면 선택됩니다.', '마우스로 네모를 그리듯 드래그하면 여러 부대가 한 번에 선택됩니다.', '아래 [내 부대 전체 선택] 버튼으로 모든 부대를 고를 수 있습니다.']],
  ['➜ 이동과 공격', ['부대를 고른 뒤 지도를 클릭하면 그곳으로 행군합니다. 길과 지형에 따라 속도가 달라집니다.', '적 부대를 클릭하면 공격합니다. 영국 해협 같은 좁은 바다는 배로 건널 수 있습니다.']],
  ['🤝 합치기 · ✂ 나누기', ['여러 부대를 고르고 [합치기]를 누르면 가장 큰 부대로 모여 하나가 됩니다.', '부대 하나를 고르고 [반으로 나누기]를 누르면 둘로 나뉩니다. 오른쪽 패널에서 원하는 숫자만큼 나눌 수도 있습니다.']],
  ['🗺 지도 보기', ['마우스 휠로 확대/축소, 오른쪽 버튼을 누른 채 드래그하거나 W A S D 키로 지도를 움직입니다.', '멀리서 보면 가까운 부대가 [국기 ×N] 묶음으로 보이고, 가까이 보면 정확한 병력 숫자가 보입니다.']],
  ['⚔ 전투와 점령', ['적 부대와 마주치면 전투가 벌어지고 병력 숫자가 줄어듭니다. 언덕·숲·도시는 방어에 유리합니다.', '적의 땅에 부대를 세워 두면 줄무늬가 차오르고 그 땅이 내 것이 됩니다. 붉은 선이 전선입니다.']],
  ['⚑ 군대 만들기', ['아래 [군대 만들기] 버튼을 누르면 수도가 열립니다. 병력 수를 고르고 [생산]을 누르세요.', '인력·산업·보급이 필요하고, 땅을 많이 가질수록 더 빨리 쌓입니다.']],
  ['🕊 외교', ['위쪽 [외교] 버튼에서 선전포고, 평화 제안, 동맹 제안을 할 수 있습니다.']],
  ['📱 모바일', ['한 손가락으로 지도 이동, 두 손가락으로 확대, 탭으로 선택과 이동을 합니다.', '[범위 선택] 버튼을 켜면 손가락 드래그로 여러 부대를 고를 수 있습니다. 길게 누르면 정보를 봅니다.']],
];

export function HowToPlay() {
  return (
    <MenuShell>
      <div className="dialog-wrap">
        <div className="panel dialog">
          <div>
            <div className="panel-title">교본</div>
            <h2>게임 방법</h2>
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
              ← 뒤로
            </button>
          </div>
        </div>
      </div>
    </MenuShell>
  );
}
