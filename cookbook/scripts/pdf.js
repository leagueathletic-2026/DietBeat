// Render output/book.html -> output/DietBeat-Cookbook.pdf with headless Chromium (Playwright).
// Usage: node scripts/pdf.js [--png N,M]   (--png also writes preview images of the given page numbers)
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const html = path.join(root, 'output', 'book.html');
  const out = path.join(root, 'output', 'DietBeat-Cookbook.pdf');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + html, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);

  // Fail loudly if any page's content overflows its A4 box (it would be clipped in print).
  const overflow = await page.evaluate(() =>
    [...document.querySelectorAll('.page')]
      .map((el, i) => ({ i: i + 1, id: el.id, over: el.scrollHeight - el.clientHeight }))
      .filter(x => x.over > 1));
  if (overflow.length) {
    console.error('Pages overflowing A4:', JSON.stringify(overflow));
    process.exitCode = 2;
  }

  await page.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true });
  console.log('PDF ->', path.relative(root, out), (fs.statSync(out).size / 1024).toFixed(0) + ' KB');

  const i = process.argv.indexOf('--png');
  if (i > -1) {
    const nums = process.argv[i + 1].split(',').map(Number);
    const els = await page.$$('.page');
    for (const n of nums) {
      const f = path.join(root, 'output', `preview-p${n}.png`);
      await els[n - 1].screenshot({ path: f });
      console.log('PNG ->', path.relative(root, f));
    }
  }
  await browser.close();
})();
