const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  for (const n of ['proposal', 'data_card']) {
    await p.goto('file://' + __dirname + '/' + n + '.html');
    await p.evaluate(() => document.fonts.ready);
    await p.pdf({ path: n + '.pdf', format: 'A4', preferCSSPageSize: true, printBackground: true });
  }
  await b.close();
})();
