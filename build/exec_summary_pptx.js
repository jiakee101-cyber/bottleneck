const pptxgen = require('pptxgenjs');
const React = require('react'); const RDS = require('react-dom/server'); const sharp = require('sharp');
const fa = require('react-icons/fa'); const md = require('react-icons/md');
const { applyTheme } = require('/root/.claude/skills/synced/4b0c1558-33fe-4b40-95b6-16f8f42a4c69_c6e77605-ba63-43bd-a3e9-048ac09c1e50/pptx/scripts/apply_theme.js');

const THEME = { name: 'NAV Bottleneck', headFontFace: 'Cambria', bodyFontFace: 'Calibri',
  colors: { dk1: '1F2933', lt1: 'FFFFFF', dk2: '1E2761', lt2: 'EEF1F6',
    accent1: '7B5EA7', accent2: '2E9E5B', accent3: '2F6FB0', accent4: 'E8A33D', accent5: 'C8423B', accent6: '5B6573',
    hlink: '2F6FB0', folHlink: '7B5EA7' } };

async function icon(Comp, hex) {
  const svg = RDS.renderToStaticMarkup(React.createElement(Comp, { color: '#' + hex, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).resize(256, 256).png().toBuffer();
  return 'image/png;base64,' + buf.toString('base64');
}

(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE';
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = 'NAV Bottleneck Dashboard - Executive Summary';
  const C = pres.SchemeColor, T = THEME.colors;

  pres.defineSlideMaster({ title: 'ONE_PAGER', background: { color: 'FFFFFF' },
    objects: [
      { placeholder: { options: { name: 'title', type: 'title', x: 0.5, y: 0.3, w: 12.33, h: 0.65, fontFace: 'Cambria', fontSize: 30, bold: true, color: C.text2, valign: 'top', align: 'left', margin: 0 }, text: '' } },
    ] });

  pres.addSection({ title: 'Executive summary' });
  const s = pres.addSlide({ masterName: 'ONE_PAGER', sectionTitle: 'Executive summary' });
  s.addText('NAV Bottleneck Dashboard: executive summary', { placeholder: 'title' });

  const label = (n, txt, x, y, w) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: 0.32, h: 0.32, fill: { color: C.text2 }, line: { color: C.text2 }, objectName: 'Section ' + n + ' marker' });
    s.addText(String(n), { x, y, w: 0.32, h: 0.32, fontSize: 12, bold: true, color: C.background1, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    s.addText(txt, { x: x + 0.45, y, w, h: 0.32, fontSize: 13, bold: true, color: C.text2, charSpacing: 1, valign: 'middle', margin: 0, isTextBox: true });
  };

  // ---------- Section 1: objective + advantages
  const y1 = 1.1;
  label(1, 'OBJECTIVE', 0.5, y1, 4);
  s.addText([
    { text: 'Identify where NAV production is held up, so we can optimise how tasks are scheduled and staffed.', options: { bold: true, color: C.text1, breakLine: true } },
    { text: 'The dashboard replaces our Excel-based tracking with one interactive view of suppliers, funds and team workload.', options: { color: C.accent6 } },
  ], { x: 0.5, y: y1 + 0.45, w: 6.4, h: 1.05, fontSize: 15, valign: 'top', margin: 0, paraSpaceAfter: 4, isTextBox: true });

  const adv = [
    { ic: fa.FaExpandArrowsAlt, head: 'Scalable', body: 'Adds funds, teams and months of history without heavier spreadsheets' },
    { ic: fa.FaChartBar, head: 'Clearer to read', body: 'Interactive charts with date, client and fund filters, instead of static tables' },
  ];
  for (let i = 0; i < 2; i++) {
    const x = 7.2 + i * 2.89, w = 2.74, y = y1 + 0.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.5, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: 'Advantage ' + (i + 1) });
    s.addImage({ data: await icon(adv[i].ic, T.dk2), x: x + 0.2, y: y + 0.2, w: 0.3, h: 0.3, altText: adv[i].head + ' icon' });
    s.addText(adv[i].head, { x: x + 0.6, y: y + 0.17, w: w - 0.75, h: 0.36, fontSize: 15, bold: true, color: C.text2, margin: 0, valign: 'middle', isTextBox: true });
    s.addText(adv[i].body, { x: x + 0.2, y: y + 0.62, w: w - 0.4, h: 0.8, fontSize: 13, color: C.text1, margin: 0, valign: 'top', isTextBox: true });
  }

  // ---------- Section 2: what it answers
  const y2 = 2.75;
  label(2, 'WHAT THE DASHBOARD ANSWERS', 0.5, y2, 6);
  const cards = [
    { head: 'Supplier risk', ic: fa.FaLink, col: C.accent5, hex: T.accent5,
      q: 'Which suppliers put the most funds at risk?',
      pts: ['Funds and clients behind each pricing file', 'How late each file was, and how many breaches followed', 'Breaches by likely cause, per client'] },
    { head: 'Fund-by-fund timeline', ic: md.MdTimeline, col: C.accent2, hex: T.accent2,
      q: 'Where did each fund’s time go on a given day?',
      pts: ['Waiting, NAV calculation, control and delivery per fund', 'All supplier and client cut-offs on one clock', 'Headroom left before the client cut-off'] },
    { head: 'Team workload', ic: fa.FaUsers, col: C.accent1, hex: T.accent1,
      q: 'Do we have enough makers at peak hours?',
      pts: ['Work in hand vs maker capacity, hour by hour', 'Peak hours flagged green, amber or red', 'Client cut-offs falling due in each hour'] },
  ];
  const cw = 3.91, gap = 0.3, cy = y2 + 0.45, ch = 2.3;
  for (let i = 0; i < 3; i++) {
    const c = cards[i], x = 0.5 + i * (cw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: cy, w: cw, h: ch, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: 'Card ' + (i + 1) });
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: cy + 0.18, w: 0.5, h: 0.5, fill: { color: C.background1 }, line: { color: c.col, width: 1.5 }, objectName: 'Card icon circle ' + (i + 1) });
    s.addImage({ data: await icon(c.ic, c.hex), x: x + 0.32, y: cy + 0.3, w: 0.26, h: 0.26, altText: c.head + ' icon' });
    s.addText(c.head, { x: x + 0.85, y: cy + 0.18, w: cw - 1.0, h: 0.5, fontFace: 'Cambria', fontSize: 17, bold: true, color: C.text2, margin: 0, valign: 'middle', isTextBox: true });
    s.addText(c.q, { x: x + 0.2, y: cy + 0.8, w: cw - 0.4, h: 0.3, fontSize: 13, italic: true, color: c.col, bold: true, margin: 0, valign: 'top', isTextBox: true });
    s.addText(c.pts.map((t, j) => ({ text: t, options: { bullet: { indent: 12 }, breakLine: j < c.pts.length - 1, paraSpaceAfter: 2 } })),
      { x: x + 0.2, y: cy + 1.15, w: cw - 0.4, h: 1.1, fontSize: 13, color: C.text1, margin: 0, valign: 'top', isTextBox: true });
  }

  // ---------- Section 3: challenges and next steps
  const y3 = 5.7;
  label(3, 'CHALLENGES AND NEXT STEPS', 0.5, y3, 6);
  const ch3 = [
    'Actual arrival times for custody, TA and broker data are not captured',
    'No system indicator shows when reconciliation actually starts',
    'Data comes from 18 team databases: costly to maintain, with accuracy and quality gaps',
  ];
  s.addText(ch3.map((t, j) => ({ text: t, options: { bullet: { indent: 12 }, breakLine: j < ch3.length - 1, paraSpaceAfter: 3 } })),
    { x: 0.5, y: y3 + 0.45, w: 6.6, h: 1.0, fontSize: 13, color: C.text1, margin: 0, valign: 'top', isTextBox: true });

  const steps = [
    { head: 'Today', body: '18 team databases', fill: C.background2, txt: C.text1 },
    { head: 'Next', body: 'Arcturus team supplies arrival and recon-start data', fill: C.background2, txt: C.text1 },
    { head: 'Target', body: 'Power BI linked to Arcturus through its API', fill: C.text2, txt: C.background1 },
  ];
  const sx = 7.25, sw = 1.62, sg = 0.31, sy = y3 + 0.4, sh = 1.0;
  for (let i = 0; i < 3; i++) {
    const x = sx + i * (sw + sg), st = steps[i];
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: sy, w: sw, h: sh, rectRadius: 0.08, fill: { color: st.fill }, line: { color: st.fill }, objectName: 'Roadmap step ' + (i + 1) });
    s.addText([{ text: st.head.toUpperCase(), options: { bold: true, fontSize: 11, charSpacing: 1, breakLine: true } }, { text: st.body, options: { fontSize: 12 } }],
      { x: x + 0.12, y: sy + 0.1, w: sw - 0.24, h: sh - 0.2, color: st.txt, valign: 'top', margin: 0, paraSpaceAfter: 3, isTextBox: true });
    if (i < 2) s.addShape(pres.shapes.CHEVRON, { x: x + sw + 0.09, y: sy + sh / 2 - 0.12, w: 0.14, h: 0.24, fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: 'Roadmap arrow ' + (i + 1) });
  }

  const out = '/home/user/bottleneck/NAV_Report_Executive_Summary.pptx';
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log('ok');
})();
