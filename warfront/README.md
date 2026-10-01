# WARFRONT — 나폴레옹 시대 실시간 전쟁 전략 웹게임

실제 유럽 지도(Natural Earth, 1812년 판도) 위에서 국기 군대와 병력 숫자로 싸우는 실시간 멀티플레이 전략 게임.

## 실행 (로컬)
```bash
cd warfront
npm install
npm run dev        # 서버 :3001 + 클라이언트 :5173 (http://localhost:5173)
```

## 배포 (친구와 인터넷으로 플레이)
가장 간단한 방법: **서버 하나가 클라이언트까지 서빙** (Render / Railway / Fly.io 등 WebSocket 지원 호스트)
```bash
npm install && npm run build   # client/dist + server/dist 생성
npm start                      # PORT 환경변수 사용, 같은 주소에서 게임 제공
```
- Render: New Web Service → Root `warfront`, Build `npm install && npm run build`, Start `npm start`.
- 프론트를 Vercel에 따로 올릴 경우: `client` 폴더를 배포하고 환경변수 `VITE_SERVER_URL=https://<서버주소>` 설정, 서버에는 `CLIENT_ORIGIN=https://<vercel주소>`.
- 환경변수 예시는 `.env.example` 참고.

## 구조
- `shared/` 공통 타입·상수·데이터(국가, 지도, 지리 데이터 `data/geo/europe.json`)
- `server/` 서버 권위 시뮬레이션(이동·전투·점령·경제·생산·외교·AI), Socket.IO 방/로비/채팅
- `client/` React + Canvas 렌더러(지형 타일, 영토/전선, 국기 군대, 클러스터링, 전투 효과, 미니맵)
- `scripts/geo/build-europe.mjs` Natural Earth 데이터로 유럽 지도 재생성

## 테스트
`npm test` — 두 클라이언트(프랑스/영국) 방 생성·참가·생산·이동·전투·치트 거부 통합 테스트.
