const STEPS: [string, string, string][] = [
  ['🖱', '부대 고르기', '내 부대(금색 ▼)를 클릭하거나, 마우스로 네모를 그리듯 드래그하면 여러 부대가 한 번에 선택됩니다.'],
  ['➜', '이동 · 공격', '부대를 고른 뒤 지도를 클릭하면 그곳으로 행군합니다. 적 부대를 클릭하면 공격합니다.'],
  ['🗺', '지도 보기', '마우스 휠로 확대/축소, 오른쪽 버튼 드래그(또는 WASD)로 지도를 움직입니다. 오른쪽 아래 미니맵도 클릭할 수 있어요.'],
  ['⚑', '군대 만들기', '아래 [군대 만들기] 버튼을 누르면 수도가 열립니다. 병력 수를 고르고 [생산]을 누르세요.'],
  ['⚔', '점령', '적의 땅에 부대를 세워 두면 줄무늬가 차오르고 그 땅이 내 것이 됩니다. 붉은 선이 전선입니다.'],
  ['📱', '모바일', '한 손가락으로 지도 이동, 두 손가락으로 확대, [범위 선택] 버튼을 켜면 드래그로 여러 부대를 고릅니다.'],
];

/** First-run tutorial card (can be reopened with the help button). */
export function GameHelp({ onClose }: { onClose: () => void }) {
  return (
    <div className="overlay" onClick={onClose}>
      <div className="panel help-card" onClick={(e) => e.stopPropagation()}>
        <div className="panel-title">조작 방법</div>
        <h2>이렇게 하면 됩니다</h2>
        <div className="help-steps">
          {STEPS.map(([icon, title, text]) => (
            <div key={title} className="help-step">
              <span className="help-icon">{icon}</span>
              <div>
                <div className="help-title">{title}</div>
                <div className="help-text">{text}</div>
              </div>
            </div>
          ))}
        </div>
        <button className="btn primary big" onClick={onClose} data-testid="help-close">
          알겠어요, 시작!
        </button>
      </div>
    </div>
  );
}
