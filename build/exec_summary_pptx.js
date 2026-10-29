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
  pres.title = 'NAV Bottleneck Report - Executive Summary';
  const C = pres.SchemeColor;

  pres.defineSlideMaster({ title: 'ONE_PAGER', background: { color: 'FFFFFF' },
    objects: [
      { placeholder: { options: { name: 'title', type: 'title', x: 0.5, y: 0.35, w: 12.33, h: 0.75, fontFace: 'Cambria', fontSize: 32, bold: true, color: C.text2, valign: 'top', align: 'left', margin: 0 }, text: '' } },
      { placeholder: { options: { name: 'body', type: 'body', x: 0.5, y: 1.1, w: 12.33, h: 0.5, fontSize: 16, color: C.accent6, valign: 'top', margin: 0 }, text: '' } },
    ] });

  pres.addSection({ title: 'Executive summary' });
  const s = pres.addSlide({ masterName: 'ONE_PAGER', sectionTitle: 'Executive summary' });
  s.addText('NAV Bottleneck Report: where our NAV time goes', { placeholder: 'title' });
  s.addText('A two-page Power BI report that shows which suppliers put funds at risk, where each fund’s day is lost, and whether the team had enough makers when work landed.', { placeholder: 'body' });

  const cards = [
    { tag: 'PAGE 1 · SUPPLIER RISK', head: 'Supplier risk', ic: fa.FaLink, col: C.accent5, hex: THEME.colors.accent5,
      q: 'Which pricing files put the most funds at risk, and is lateness coming from suppliers or from us?',
      pts: ['Funds and clients behind each pricing file', 'Hours pricing was late vs the breaches it caused', 'Breaches by possible cause, per client'],
      dec: 'Which suppliers to escalate, and which fixes are ours' },
    { tag: 'PAGE 2 · FUND LEVEL', head: 'Fund-by-fund timeline', ic: md.MdTimeline, col: C.accent2, hex: THEME.colors.accent2,
      q: 'On a given day, where did each fund’s time go?',
      pts: ['Wait, NAV work, control and delivery for every fund', 'Pricing, custody, broker and client cut-offs on one clock', 'Headroom left before the client cut-off'],
      dec: 'Which step to fix behind each breach' },
    { tag: 'PAGE 2 · TEAM LOAD', head: 'Team load by hour', ic: fa.FaUsers, col: C.accent1, hex: THEME.colors.accent1,
      q: 'Did we have enough makers when the work landed?',
      pts: ['Work in hand vs maker capacity, hour by hour', 'Load %: green, amber, red; purple after shift', 'Client cut-offs due in each hour'],
      dec: 'Shift times and staffing for the peak hours' },
  ];
  const cw = 3.91, gap = 0.3, cy = 1.8, ch = 3.95;
  for (let i = 0; i < cards.length; i++) {
    const c = cards[i]; const x = 0.5 + i * (cw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: cy, w: cw, h: ch, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: 'Card ' + (i + 1) });
    s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: cy + 0.25, w: 0.6, h: 0.6, fill: { color: C.background1 }, line: { color: c.col, width: 1.5 }, objectName: 'Icon circle ' + (i + 1) });
    s.addImage({ data: await icon(c.ic, c.hex), x: x + 0.39, y: cy + 0.39, w: 0.32, h: 0.32, altText: c.head + ' icon' });
    s.addText(c.tag, { x: x + 1.0, y: cy + 0.22, w: cw - 1.15, h: 0.28, fontSize: 11, bold: true, color: c.col, charSpacing: 1, margin: 0, isTextBox: true });
    s.addText(c.head, { x: x + 1.0, y: cy + 0.5, w: cw - 1.15, h: 0.4, fontFace: 'Cambria', fontSize: 18, bold: true, color: C.text2, margin: 0, isTextBox: true });
    s.addText(c.q, { x: x + 0.25, y: cy + 1.05, w: cw - 0.5, h: 0.75, fontSize: 14, italic: true, color: C.text1, margin: 0, valign: 'top', isTextBox: true });
    s.addText(c.pts.map((t, j) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: j < c.pts.length - 1, paraSpaceAfter: 4 } })),
      { x: x + 0.25, y: cy + 1.85, w: cw - 0.5, h: 1.3, fontSize: 14, color: C.text1, margin: 0, valign: 'top', isTextBox: true });
    s.addText([{ text: 'Decision: ', options: { bold: true, color: c.col } }, { text: c.dec, options: { color: C.text1 } }],
      { x: x + 0.25, y: cy + 3.25, w: cw - 0.5, h: 0.55, fontSize: 14, margin: 0, valign: 'top', isTextBox: true });
  }

  // Bottom band
  const by = 6.0, bh = 1.25;
  s.addText('HOW IT WORKS', { x: 0.5, y: by, w: 6, h: 0.28, fontSize: 11, bold: true, color: C.accent6, charSpacing: 1, margin: 0, isTextBox: true });
  const flow = ['Status log + pricing arrivals', 'Excel template v4.5\ncalculations and checks', 'Power BI\n70 measures, 2 pages'];
  const fw = 2.0, fg = 0.32;
  for (let i = 0; i < flow.length; i++) {
    const fx = 0.5 + i * (fw + fg);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: fx, y: by + 0.4, w: fw, h: 0.8, rectRadius: 0.08, fill: { color: i === 2 ? C.text2 : C.background2 }, line: { color: i === 2 ? C.text2 : C.background2 }, objectName: 'Flow step ' + (i + 1) });
    s.addText(flow[i], { x: fx + 0.08, y: by + 0.4, w: fw - 0.16, h: 0.8, fontSize: 12, bold: i === 2, color: i === 2 ? C.background1 : C.text1, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    if (i < flow.length - 1) s.addShape(pres.shapes.CHEVRON, { x: fx + fw + 0.09, y: by + 0.68, w: 0.15, h: 0.24, fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: 'Arrow ' + (i + 1) });
  }
  const rx = 7.65, rw = 5.18;
  s.addText('READ WITH CARE', { x: rx, y: by, w: rw, h: 0.28, fontSize: 11, bold: true, color: C.accent4, charSpacing: 1, margin: 0, isTextBox: true });
  s.addText([
    { text: 'Custody, TA and broker arrival times are not captured: the report shows exposure, not proof they were late.', options: { bullet: { indent: 12 }, breakLine: true, paraSpaceAfter: 3 } },
    { text: 'Wait split and capacity are rebuilt from status times and weightage budgets: read the direction, not exact minutes.', options: { bullet: { indent: 12 } } },
  ], { x: rx, y: by + 0.36, w: rw, h: 0.95, fontSize: 12, color: C.text1, margin: 0, valign: 'top', isTextBox: true });

  s.addNotes('Talk track (about 2 minutes).\n' +
    '1. Purpose: one report that answers three questions - supplier risk, where each fund\'s day goes, and whether we had the makers when the work landed.\n' +
    '2. Page 1 is the monthly view for supplier and process conversations: which pricing files carry the most funds, whether their lateness reached clients, and what sits behind each client\'s breaches. Only pricing lateness is measured; the other causes are exposures.\n' +
    '3. Page 2 is the single-day view: a timeline per fund with every cut-off, plus team load by hour (work in hand vs maker capacity at 50 minutes per maker-hour).\n' +
    '4. Everything is calculated from the Excel template v4.5; nothing is typed into Power BI by hand.\n' +
    '5. Caveats: custody, TA and broker arrivals are not captured, and the wait split and capacity are reconstructions from budgets.');

  const out = '/home/user/bottleneck/NAV_Report_Executive_Summary.pptx';
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log('ok');
})();
