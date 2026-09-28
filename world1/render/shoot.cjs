// 사용법: node render/shoot.cjs view1,view2 [출력폴더]
//   render 폴더를 http://127.0.0.1:8766 로 서비스 중이어야 함
//   PAGE=ingame.html (기본) | view.html,  W/H: 화면 크기, PR: 내부 배율
const { chromium } = require(process.env.PW || 'playwright');
const path = require('path');
(async () => {
  const views = (process.argv[2] || 'test').split(',');
  const out = process.argv[3] || path.join(__dirname, '..', 'renders');
  require('fs').mkdirSync(out, { recursive: true });
  const page = process.env.PAGE || 'ingame.html';
  const W = +(process.env.W || (page === 'ingame.html' ? 1920 : 2560)), H = +(process.env.H || (page === 'ingame.html' ? 1080 : 1440));
  const PR = process.env.PR || (page === 'ingame.html' ? 2 : 1.5);
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--js-flags=--max-old-space-size=8192'] });
  const p = await b.newPage({ viewport: { width: W, height: H } });
  p.on('console', m => { const t = m.text(); if (t.startsWith('[view]') || m.type() === 'error') console.log(t); });
  p.on('pageerror', e => console.log('pageerror:', e.message));
  for (const v of views) {
    const t = Date.now();
    await p.goto(`http://127.0.0.1:8766/${page}?view=${v}&w=${W}&h=${H}&pr=${PR}`);
    await p.waitForFunction(() => window.__done === true, null, { timeout: 1800000, polling: 1000 });
    const err = await p.evaluate(() => window.__err);
    if (err) { console.log('ERR', err); continue; }
    await p.screenshot({ path: path.join(out, `${v}.png`) });
    console.log('saved', v, (Date.now() - t) / 1000 + 's');
  }
  await b.close();
})();
