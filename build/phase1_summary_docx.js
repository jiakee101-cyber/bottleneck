const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  AlignmentType, LevelFormat, HeadingLevel, Footer, PageNumber, TableLayoutType } = require('docx');

const NAVY = '1E2761', MUTED = '5B6573', LIGHT = 'EEF1F6', LINE = 'C9D1DB';
const W = 9026; // A4 width minus 1" margins, in DXA

const p = (text, o = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, ...o,
  children: (Array.isArray(text) ? text : [text]).map(t => typeof t === 'string' ? new TextRun(t) : t) });
const b = (t) => new TextRun({ text: t, bold: true });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (parts, level = 0) => new Paragraph({ numbering: { reference: 'bullets', level }, spacing: { after: 80, line: 276 },
  children: (Array.isArray(parts) ? parts : [parts]).map(t => typeof t === 'string' ? new TextRun(t) : t) });
const num = (parts) => new Paragraph({ numbering: { reference: 'steps', level: 0 }, spacing: { after: 80, line: 276 },
  children: (Array.isArray(parts) ? parts : [parts]).map(t => typeof t === 'string' ? new TextRun(t) : t) });

const border = { style: BorderStyle.SINGLE, size: 4, color: LINE };
const borders = { top: border, bottom: border, left: border, right: border };
function table(widths, rows, headerFill = NAVY) {
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED,
    rows: rows.map((r, ri) => new TableRow({ tableHeader: ri === 0, cantSplit: true,
      children: r.map((c, ci) => new TableCell({
        width: { size: widths[ci], type: WidthType.DXA }, borders,
        shading: ri === 0 ? { type: ShadingType.CLEAR, color: 'auto', fill: headerFill } : (ri % 2 === 0 ? { type: ShadingType.CLEAR, color: 'auto', fill: 'F7F8FA' } : undefined),
        margins: { top: 80, bottom: 80, left: 110, right: 110 },
        children: (Array.isArray(c) ? c : [c]).map(t => new Paragraph({ spacing: { after: 40 },
          children: [new TextRun({ text: t, bold: ri === 0 || (ci === 0 && r.length > 1 && ri > 0 && widths[0] < 3000), color: ri === 0 ? 'FFFFFF' : undefined, size: 19 })] }))
      })) }))
  });
}
const gap = () => new Paragraph({ spacing: { after: 60 }, children: [] });

const children = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun('NAV Bottleneck Analysis')] }),
  new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: 'Phase 1 summary and Phase 2 proposal', size: 30, color: NAVY })] }),
  new Paragraph({ spacing: { after: 280 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: LINE, space: 8 } },
    children: [new TextRun({ text: 'Prepared for SMT  ·  6 November 2026', color: MUTED })] }),

  h1('1. Executive summary'),
  p('Phase 1 set out to find where NAV production is held up so that tasks can be scheduled and staffed better. It has delivered a Power BI dashboard, built on one consolidated dataset, that shows for every fund on every day when pricing arrived, how long the fund waited, how long our own processing took, and whether the client cut-off was met.'),
  bullet([b('Supplier risk is now visible. '), 'We can see which pricing files (TOPs) carry the most funds and clients, how often they arrive late, and how many client breaches followed.']),
  bullet([b('Waiting time is broken down. '), 'Time between pricing arrival and NAV start is split into queueing behind other funds, the maker reconciling the fund, and other hold-ups such as data or breaks.']),
  bullet([b('Team capacity is measured by the hour. '), 'For any day we can compare the work on the desk with the makers on shift, and see the hours where the team was over capacity.']),
  bullet([b('It runs at full volume. '), 'The calculations were moved out of Excel into Power BI so the report handles around 5,000 funds a day.']),
  p('Phase 1 also showed what we cannot yet measure. Phase 2 proposes a bottleneck framework: agreed standards for the processing window from pricing arrival to client cut-off, a review of supplier cut-offs that are missing or off track, and a consistent way to classify each bottleneck.'),

  h1('2. Phase 1: what was delivered'),
  h2('2.1 One dataset for the whole NAV day'),
  p('The dashboard brings together four sources that were previously looked at separately:'),
  table([2600, 6426], [
    ['Source', 'What it provides'],
    ['NAV status log', 'Time each fund was calculated, controlled, signed off by fund accounting and signed off, and who did each step'],
    ['Pricing (TOP) arrivals', 'When each pricing file arrived, per pricing group and day'],
    ['Fund reference', 'Each fund\'s client, team, pricing group, product mix and cut-offs for custody, TA, broker, pricing and the client'],
    ['Team and analyst roster', 'Teams, shift start times, makers and their daily capacity'],
  ]),
  gap(),
  p('From these, every fund-day gets a full timeline, the minutes spent in each stage, its headroom to the client cut-off, and a breach flag.'),

  h2('2.2 Questions the dashboard answers'),
  table([2400, 3500, 3126], [
    ['View', 'Question', 'What it shows'],
    ['Supplier risk', 'Which pricing files put the most funds at risk, and is lateness coming from suppliers or from us?', 'Funds and clients behind each pricing file; buffer between each supplier\'s cut-off and pricing; late hours per file against the breaches that followed; breaches by likely cause per client'],
    ['Waiting after pricing', 'Once pricing arrived, why did funds still wait to start?', 'Wait split into queue behind the maker\'s other funds, the maker\'s own reconciliation, and other hold-ups'],
    ['Fund-by-fund timeline', 'Where did each fund\'s time go on a given day?', 'Waiting, NAV calculation, control and delivery per fund, with every cut-off on one clock and the headroom left'],
    ['Team workload', 'Did we have enough makers when the work arrived?', 'Work in hand against maker capacity hour by hour, flagged green, amber or red, with the client cut-offs due in each hour'],
  ]),
  gap(),

  h2('2.3 How it points to a bottleneck'),
  p('For any late or tight fund-day, the dashboard shows which of four areas the time was lost in:'),
  table([2400, 6626], [
    ['Area', 'Signal in the dashboard'],
    ['Supplier', 'Pricing arrived after the fund\'s own pricing cut-off; the pricing group missed its binding cut-off'],
    ['Capacity', 'High share of waiting spent behind the maker\'s other funds; team load above 100% in the hours before the cut-off'],
    ['Data and process', 'Long waiting not explained by queue or reconciliation; long NAV calculation or sign-off stages; recalculations'],
    ['Schedule design', 'Supplier cut-offs at or after the pricing cut-off (no buffer), or a client cut-off that leaves less time than the work needs'],
  ]),
  gap(),
  p('Each breached fund-day is given one likely cause: pricing late, thin custody buffer, broker-dependent, or none of these. Only late pricing is measured directly; the others are exposures, for the reasons in section 3.'),

  h2('2.4 Built to scale and to be trusted'),
  bullet('All calculations now run in Power BI rather than Excel formulas, so the report handles full daily volume and keeps months of history.'),
  bullet('The status log is read from a folder of system exports, so no manual copying into spreadsheets is needed.'),
  bullet('Built-in data-quality checks flag missing cut-offs, unknown funds, missing timestamps and four-eyes breaches.'),
  bullet('The new calculations were checked against the original spreadsheet logic on a test dataset, and the results matched.'),
  bullet('A chart guide and a one-page summary explain each view for users.'),

  h1('3. What Phase 1 cannot yet tell us'),
  table([3000, 6026], [
    ['Gap', 'Effect'],
    ['Actual arrival times for custody, TA and broker data are not captured', 'We can show that a fund is exposed to these suppliers, but not prove that they were late'],
    ['No system indicator of when reconciliation starts', 'Reconciliation time is estimated from each fund\'s budget, so the waiting split shows direction rather than exact minutes'],
    ['Data comes from 18 team databases', 'High maintenance cost, and gaps in accuracy and consistency between teams'],
    ['No agreed standard for the processing window', 'We can see how much buffer each fund had, but not whether it was enough'],
    ['Supplier cut-offs are not reviewed systematically', 'Some funds have missing or estimated cut-offs, or cut-offs that no longer match how the supplier actually delivers'],
  ]),
  gap(),

  h1('4. Phase 2 proposal: a bottleneck framework'),
  p([b('Objective: '), 'agree the standards each fund-day is judged against, so that bottlenecks are identified the same way across teams and regions, and action can be targeted.']),

  h2('4.1 Processing window standard'),
  p('Define the reasonable processing window from pricing (TOP) arrival to client cut-off.'),
  bullet('Measure the actual window and the time each stage takes today, from the Phase 1 data, by fund type (product mix, sign-off model and complexity).'),
  bullet('Agree a required window for each fund type: the working time needed plus a safety buffer.'),
  bullet('Flag every fund whose schedule gives less than the required window, before it breaches.'),

  h2('4.2 Supplier cut-off review'),
  p('Find supplier cut-offs that are missing or off track.'),
  bullet('List funds with missing or estimated custody, TA, broker or pricing cut-offs.'),
  bullet('Flag cut-offs that leave no buffer: a supplier due at or after the pricing cut-off.'),
  bullet('Flag funds whose pricing cut-off is out of line with other funds on the same pricing file.'),
  bullet('Compare agreed cut-offs with actual arrival times where we have them, and agree updates with suppliers and client service.'),

  h2('4.3 Bottleneck classification'),
  bullet('Set clear thresholds that place each late or tight fund-day in one category: supplier, capacity, data and process, or schedule design.'),
  bullet('Report the categories by team, client and supplier, so that each issue has a clear owner.'),

  h2('4.4 Team buffer and rebalancing'),
  bullet('Add a view comparing teams within the same region: does each team keep enough buffer to its cut-offs?'),
  bullet('Propose which funds could move to another team in the region without reducing that team\'s buffer, taking shift times and spare capacity into account.'),

  h2('4.5 Data capture and integration'),
  bullet('Work with the Arcturus team to capture custody, TA and broker arrival times and the start of reconciliation.'),
  bullet('Connect Power BI to Arcturus through its API, replacing the 18 team databases as the source.'),

  h2('4.6 Proposed sequence'),
  num([b('Baseline: '), 'measure current processing windows and supplier buffers from Phase 1 data.']),
  num([b('Agree standards: '), 'required windows and thresholds with team leads in one pilot region.']),
  num([b('Build: '), 'framework views and the cut-off review list in the dashboard; pilot with the region.']),
  num([b('Extend: '), 'roll out to other regions and switch the data source to Arcturus as it becomes available.']),

  h1('5. Support requested from SMT'),
  bullet('Endorse the Phase 2 scope.'),
  bullet('Nominate a pilot region and a team-lead owner in each team to agree the processing window standards.'),
  bullet('Sponsor the data request to the Arcturus team for supplier arrival times and reconciliation start.'),
  bullet('Support the supplier cut-off review with client service and supplier relationship owners.'),
];

const doc = new Document({
  creator: 'NAV Bottleneck project', title: 'NAV Bottleneck Analysis - Phase 1 summary and Phase 2 proposal',
  styles: {
    default: { document: { run: { font: 'Arial', size: 21 } } },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal', run: { font: 'Arial', size: 44, bold: true, color: NAVY }, paragraph: { spacing: { before: 0, after: 60 }, keepNext: true } },
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: 'Arial', size: 30, bold: true, color: NAVY }, paragraph: { spacing: { before: 300, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: 'Arial', size: 24, bold: true, color: '1F2933' }, paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: 'steps', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
  ] },
  sections: [{
    properties: { page: { margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: 'NAV Bottleneck Analysis  ·  Page ', color: MUTED, size: 16 }), new TextRun({ children: [PageNumber.CURRENT], color: MUTED, size: 16 })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[2], buf); console.log('ok'); });
