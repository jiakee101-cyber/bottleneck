// Editable PowerPoint version of docs/chart_guide_fd1001_work_in_hand.png (all native shapes and text boxes).
const pptxgen = require('pptxgenjs');
const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.theme = { headFontFace: 'Calibri', bodyFontFace: 'Calibri' };
pres.title = 'FD-1001 work in hand';
const s = pres.addSlide();
s.background = { color: 'FFFFFF' };

const INK = '1F2933', MUTED = '5B6573', GRID = 'D5D9DE', WAIT_F = 'ECECEA', WAIT_L = 'BDBDB6', BLUE = '4A90E2', ORANGE = 'F0845A';
const X0 = 3.0, PER_HR = 2.05;                       // 11:00 sits at x = 3.0"; 2.05" per hour
const X = (h) => X0 + (h - 11) * PER_HR;
const T = (hh, mm) => hh + mm / 60;
const tArr = T(11, 3), tRecon = T(13, 49), tCalc = T(14, 18), tDone = T(14, 32);
const txt = (text, o) => s.addText(text, Object.assign({ fontFace: 'Calibri', color: INK, margin: 0, isTextBox: true }, o));

txt('FD-1001 carries its full 43 minutes while it waits', { x: 0.6, y: 0.4, w: 12, h: 0.55, fontSize: 26, bold: true, objectName: 'Title' });
txt('31 Aug. The work only shrinks once the maker starts; the chart takes a snapshot each hour (dots).',
    { x: 0.6, y: 0.98, w: 12, h: 0.4, fontSize: 15, color: MUTED, objectName: 'Subtitle' });

// hour gridlines (dashed) across both rows
const gTop = 1.75, gBot = 5.75;
[11, 12, 13, 14, 15].forEach(h => s.addShape(pres.shapes.LINE, { x: X(h), y: gTop, w: 0, h: gBot - gTop,
  line: { color: GRID, width: 1, dashType: 'dash' }, objectName: 'Gridline ' + h + ':00' }));

// ---- top row: the fund-day bar
const barY = 2.75, barH = 0.62;
txt('FD-1001', { x: 0.6, y: barY, w: 2, h: barH, fontSize: 17, bold: true, valign: 'middle', objectName: 'Row label FD-1001' });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: X(tArr), y: barY, w: X(tRecon) - X(tArr), h: barH, rectRadius: 0.06,
  fill: { color: WAIT_F }, line: { color: WAIT_L, width: 1 }, objectName: 'Bar waiting on the desk' });
s.addShape(pres.shapes.RECTANGLE, { x: X(tRecon), y: barY, w: X(tCalc) - X(tRecon), h: barH, fill: { color: BLUE }, line: { color: BLUE, width: 0 }, objectName: 'Bar reconciliation' });
s.addShape(pres.shapes.RECTANGLE, { x: X(tCalc), y: barY, w: X(tDone) - X(tCalc), h: barH, fill: { color: ORANGE }, line: { color: ORANGE, width: 0 }, objectName: 'Bar NAV calculation' });

// event labels above the bar, right-aligned to their tick when they would run off the right edge
const above = (label, time, x, align, name) => {
  const w = 3.2, bx = align === 'right' ? x - w : x - (align === 'center' ? w / 2 : 0);
  txt([{ text: label, options: { fontSize: 15, breakLine: true } }, { text: time, options: { fontSize: 13, color: MUTED } }],
      { x: bx, y: 1.85, w, h: 0.7, align, valign: 'bottom', objectName: name });
  s.addShape(pres.shapes.LINE, { x, y: 2.58, w: 0, h: barY - 2.58, line: { color: WAIT_L, width: 1 }, objectName: name + ' tick' });
};
above('Pricing arrives', '11:03', X(tArr), 'center', 'Label pricing arrives');
above('Recon starts (estimated)', '13:49', X(tRecon), 'right', 'Label recon starts');
above('Finished (Controlled)', '14:32', X(tDone), 'left', 'Label finished');
// NAV start label below the bar
s.addShape(pres.shapes.LINE, { x: X(tCalc), y: barY + barH, w: 0, h: 0.28, line: { color: WAIT_L, width: 1 }, objectName: 'Label NAV starts tick' });
txt([{ text: 'NAV starts (Calculated)', options: { fontSize: 15, breakLine: true } }, { text: '14:18', options: { fontSize: 13, color: MUTED } }],
    { x: X(tCalc) - 3.2, y: barY + barH + 0.3, w: 3.2, h: 0.65, align: 'right', valign: 'top', objectName: 'Label NAV starts' });

// ---- bottom row: work left (area)
const yTop = 4.45, yZero = 5.45, MAXW = 43;
const Y = (m) => yZero - (m / MAXW) * (yZero - yTop);
txt('Work left', { x: 0.6, y: 4.6, w: 2, h: 0.5, fontSize: 17, bold: true, valign: 'middle', objectName: 'Row label work left' });
txt('43 min', { x: 1.6, y: Y(43) - 0.2, w: 1.15, h: 0.4, fontSize: 14, color: MUTED, align: 'right', valign: 'middle', objectName: 'Axis label 43 min' });
txt('0', { x: 1.6, y: yZero - 0.2, w: 1.15, h: 0.4, fontSize: 14, color: MUTED, align: 'right', valign: 'middle', objectName: 'Axis label 0' });
// shaded area: flat at 43 from arrival to recon start, falls to 0 at finish
const ax = X(tArr), aw = X(tDone) - ax, ah = yZero - yTop;
s.addShape(pres.shapes.CUSTOM_GEOMETRY, { x: ax, y: yTop, w: aw, h: ah, fill: { color: WAIT_F }, line: { type: 'none' },
  points: [{ x: 0, y: 0 }, { x: X(tRecon) - ax, y: 0 }, { x: aw, y: ah }, { x: 0, y: ah }, { close: true }],
  objectName: 'Work left area' });
s.addShape(pres.shapes.LINE, { x: X(11) - 0.05, y: yTop, w: X(tRecon) - X(11) + 0.05, h: 0, line: { color: INK, width: 2 }, objectName: 'Work left line flat' });
s.addShape(pres.shapes.LINE, { x: X(tRecon), y: yTop, w: X(tDone) - X(tRecon), h: ah, line: { color: INK, width: 2 }, objectName: 'Work left line falling' });
s.addShape(pres.shapes.LINE, { x: 2.85, y: yZero, w: X(15.5) - 2.85, h: 0, line: { color: WAIT_L, width: 1.25 }, objectName: 'Baseline' });
// hourly snapshots
[[11, 43], [12, 43], [13, 43], [14, 32], [15, 0]].forEach(([h, m]) => s.addShape(pres.shapes.OVAL,
  { x: X(h) - 0.075, y: Y(m) - 0.075, w: 0.15, h: 0.15, fill: { color: INK }, line: { color: INK, width: 0 }, objectName: 'Snapshot ' + h + ':00 ' + m + ' min' }));
[11, 12, 13, 14, 15].forEach(h => txt(h + ':00', { x: X(h) - 0.5, y: 5.62, w: 1, h: 0.35, fontSize: 14, color: MUTED, align: 'center', objectName: 'Axis ' + h + ':00' }));

// ---- legend
const legend = [['Waiting on the desk', WAIT_F, WAIT_L, 2.35], ['Reconciliation (28.5 min budget)', BLUE, BLUE, 3.35], ['NAV calculation (14 min)', ORANGE, ORANGE, 2.75]];
let lx = 3.5;
legend.forEach(([label, fill, line, w]) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: lx, y: 6.42, w: 0.22, h: 0.22, rectRadius: 0.03, fill: { color: fill }, line: { color: line, width: 1 }, objectName: 'Legend swatch ' + label });
  txt(label, { x: lx + 0.32, y: 6.35, w: w - 0.35, h: 0.36, fontSize: 14, valign: 'middle', objectName: 'Legend ' + label });
  lx += w + 0.2;
});

pres.writeFile({ fileName: process.argv[2] }).then(() => console.log('ok'));
