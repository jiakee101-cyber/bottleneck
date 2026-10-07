"""Generate Wait_Split_Explained.html (print to PDF with headless Chromium).

Usage: python3 -I build/explain_wait_split.py <out.html>
Times for the worked examples are the sample data in NAV_Bottleneck_Data_Template_v4_5.xlsx (31 Aug 2026).
"""
import sys

PUR, BLU, AMB, GRY, INK, MUT, RED = "#7B5EA7", "#2F6FB0", "#E8A33D", "#C9D1DB", "#1F2933", "#5B6573", "#C8423B"


def hm(s):
    h, m = s.split(":")[:2]
    sec = int(s.split(":")[2]) if s.count(":") == 2 else 0
    return int(h) * 60 + int(m) + sec / 60


def fmt(t):
    return f"{int(t // 60):02d}:{int(round(t % 60)):02d}" if round(t % 60) < 60 else f"{int(t // 60) + 1:02d}:00"


class Axis:
    def __init__(self, t0, t1, x0=150, x1=700):
        self.t0, self.t1, self.x0, self.x1 = t0, t1, x0, x1

    def x(self, t):
        return self.x0 + (t - self.t0) / (self.t1 - self.t0) * (self.x1 - self.x0)

    def ticks(self, y0, y1, step=60):
        out = []
        t = (self.t0 // step + 1) * step if self.t0 % step else self.t0
        while t <= self.t1:
            X = self.x(t)
            out.append(f'<line x1="{X:.1f}" x2="{X:.1f}" y1="{y0}" y2="{y1}" stroke="#EEF1F4"/>'
                       f'<text x="{X:.1f}" y="{y1 + 14}" text-anchor="middle" class="tick">{fmt(t)}</text>')
            t += step
        return "".join(out)


def diamond(X, y, filled=True, size=6):
    f = INK if filled else "white"
    return (f'<path d="M{X:.1f} {y - size} l{size} {size} l{-size} {size} l{-size} {-size} z" fill="{f}" '
            f'stroke="{INK}" stroke-width="1.3"/>')


def bar(X1, X2, y, h, color, op=1.0, stroke=None, dash=None, rx=2):
    s = f' stroke="{stroke}" stroke-width="1.3"' if stroke else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{X1:.1f}" y="{y - h / 2:.1f}" width="{max(X2 - X1, 0.8):.1f}" height="{h}" rx="{rx}" fill="{color}" fill-opacity="{op}"{s}{d}/>'


def text(x, y, s, cls="lbl", anchor="start", color=None, weight=None):
    c = f' fill="{color}"' if color else ""
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}"{c}{w}>{s}</text>'


def stacked(parts, total_w=550, x0=150, y=0, h=26, show_total=True, label=None):
    """parts: list of (minutes, color, caption)."""
    tot = sum(p[0] for p in parts)
    out, X = [], x0
    for mins, col, cap in parts:
        if mins <= 0:
            continue
        w = total_w * mins / tot if tot else 0
        out.append(bar(X, X + w, y, h, col, rx=0))
        if w > 34:
            out.append(text(X + w / 2, y + 4.5, f"{mins:g}", "seg", "middle", "white", 600))
        X += w
    if label:
        out.append(text(x0 - 10, y + 4, label, "lbl", "end", weight=600))
    if show_total:
        out.append(text(x0 + total_w + 8, y + 4, f"= {tot:g} min", "lbl", color=MUT))
    return "".join(out)


def svg(w, h, body, title):
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{title}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


# ------------------------------------------------------------------ figure 1: the whole idea
def fig_overview():
    b = []
    b.append(stacked([(36, PUR, ""), (21, BLU, ""), (147, AMB, "")], y=40, label="FD-1007 wait"))
    b.append(text(150, 76, "Queue 36", "cap", color=PUR, weight=600))
    b.append(text(250, 76, "Own recon 21", "cap", color=BLU, weight=600))
    b.append(text(430, 76, "Other hold-up 147", "cap", color="#B57A1D", weight=600))
    b.append(text(150, 18, "Pricing arrived 11:58", "cap", color=MUT))
    b.append(text(700, 18, "Calculated 15:22", "cap", "end", MUT))
    return svg(780, 90, "".join(b), "Total wait of 204 minutes split into 36 queue, 21 own recon, 147 other hold-up")


# ------------------------------------------------------------------ figure 2: the ingredients for one fund
def fig_ingredients():
    A = Axis(hm("11:30"), hm("15:40"))
    b = [A.ticks(30, 150)]
    pa, calc, rb = hm("11:58"), hm("15:22"), 20.8
    ws = calc - rb
    y = 75
    b.append(bar(A.x(pa), A.x(calc), y, 22, GRY, 0.55))
    b.append(text(A.x((pa + calc) / 2), y + 4, "wait after pricing = 204 min", "lbl", "middle"))
    b.append(diamond(A.x(pa), y))
    b.append(text(A.x(pa), y - 20, "1 · Pricing arrived 11:58", "cap", "middle", weight=600))
    b.append(f'<line x1="{A.x(calc):.1f}" x2="{A.x(calc):.1f}" y1="{y - 16}" y2="{y + 16}" stroke="{INK}" stroke-width="2"/>')
    b.append(text(A.x(calc), y - 20, "2 · Calculated 15:22", "cap", "middle", weight=600))
    y2 = 120
    b.append(bar(A.x(ws), A.x(calc), y2, 16, INK, 0.85))
    b.append(text(A.x(ws) - 6, y2 + 4, "3 · work window = Calculated − recon budget (20.8 min)", "cap", "end", weight=600))
    b.append(text(150, y + 4, "FD-1007", "lbl", "end", weight=600))
    return svg(780, 175, "".join(b), "One fund's ingredients: pricing arrival, Calculated time, and work window")


# ------------------------------------------------------------------ figure 3: Lim Wei Ming, 31 Aug
def fig_lim():
    A = Axis(hm("10:50"), hm("15:45"))
    rows = [
        ("FD-1001", "11:03", "13:49:30", "14:18"),
        ("FD-1007", "11:58", "15:01:12", "15:22"),
        ("FD-1005", "11:03", "15:14:06", "15:37"),
    ]
    b = [A.ticks(20, 300)]
    y = 45
    for name, pa, ws, cal in rows:
        focus = name == "FD-1007"
        b.append(bar(A.x(hm(pa)), A.x(hm(cal)), y, 18, GRY, 0.55 if focus else 0.3,
                     stroke=INK if focus else None))
        b.append(bar(A.x(hm(ws)), A.x(hm(cal)), y, 18, INK, 0.85))
        b.append(diamond(A.x(hm(pa)), y, size=5))
        b.append(text(140, y + 4, name, "lbl", "end", weight=700 if focus else 400))
        y += 36
    b.append(text(140, y + 4, "Lim's work", "lbl", "end", color=MUT))
    for _, _, ws, cal in rows:
        b.append(bar(A.x(hm(ws)), A.x(hm(cal)), y, 12, INK, 0.85))
    ywait = y + 50
    pa, cal = hm("11:58"), hm("15:22")
    b.append(text(140, ywait + 4, "FD-1007 wait", "lbl", "end", weight=700))
    b.append(bar(A.x(pa), A.x(cal), ywait, 22, GRY, 0.35, stroke=INK))
    for ws, ce, lab in [("13:49:30", "14:18", "28.5 min on FD-1001"), ("15:14:06", "15:22", "7.9 min on FD-1005")]:
        x1, x2 = A.x(hm(ws)), A.x(min(hm(ce), cal))
        b.append(bar(x1, x2, ywait, 22, PUR, 0.95, rx=0))
        b.append(f'<line x1="{x1:.1f}" x2="{x1:.1f}" y1="{y - 8}" y2="{ywait - 11}" stroke="{PUR}" stroke-dasharray="3 3"/>')
        b.append(f'<line x1="{x2:.1f}" x2="{x2:.1f}" y1="{y - 8}" y2="{ywait - 11}" stroke="{PUR}" stroke-dasharray="3 3"/>')
        b.append(text((x1 + x2) / 2, ywait + 28, lab, "cap", "middle", PUR, 600))
    b.append(text(A.x(pa), ywait - 16, "pricing 11:58", "cap", "middle", MUT))
    b.append(text(A.x(cal), ywait - 16, "Calculated 15:22", "cap", "middle", MUT))
    return svg(780, ywait + 50, "".join(b), "Lim Wei Ming's three funds on 31 August and where FD-1007's queue minutes come from")


# ------------------------------------------------------------------ scenario mini-figures
def fig_scenario(rows, focus, t0, t1, wait_window, overlaps, result, title):
    A = Axis(hm(t0), hm(t1), x0=120, x1=700)
    b = [A.ticks(14, 32 + 30 * len(rows))]
    y = 30
    for name, pa, ws, cal in rows:
        f = name == focus
        b.append(bar(A.x(hm(pa)), A.x(hm(cal)), y, 15, GRY, 0.55 if f else 0.3, stroke=INK if f else None))
        b.append(bar(A.x(hm(ws)), A.x(hm(cal)), y, 15, INK, 0.85))
        b.append(diamond(A.x(hm(pa)), y, size=4.5))
        b.append(text(110, y + 4, name, "lbl", "end", weight=700 if f else 400))
        for o1, o2 in overlaps if f else []:
            b.append(bar(A.x(hm(o1)), A.x(hm(o2)), y, 15, PUR, 0.95, rx=0))
        y += 30
    y += 26
    b.append(stacked(result, total_w=520, x0=120, y=y, h=20, label="split"))
    return svg(780, y + 22, "".join(b), title)


CSS = """
@page { size: A4; margin: 15mm 15mm 16mm 15mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; color: #1F2933; font-size: 10.5pt; line-height: 1.45; margin: 0; }
h1 { font-size: 21pt; margin: 0 0 4px; color: #123A5E; }
h2 { font-size: 14pt; margin: 18px 0 6px; color: #123A5E; border-bottom: 2px solid #123A5E; padding-bottom: 3px; }
h3 { font-size: 11.5pt; margin: 14px 0 4px; }
p { margin: 5px 0; }
.sub { color: #5B6573; font-size: 11pt; margin-bottom: 12px; }
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
svg { width: 100%; height: auto; display: block; margin: 8px 0; }
svg text { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }
.tick { font-size: 10px; fill: #5B6573; }
.lbl { font-size: 12px; fill: #1F2933; }
.cap { font-size: 11px; fill: #1F2933; }
.seg { font-size: 12px; }
.key { display: flex; gap: 16px; flex-wrap: wrap; margin: 6px 0 10px; font-size: 10pt; }
.key span { display: inline-flex; align-items: center; gap: 6px; }
.sw { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }
.cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 10px 0; }
.card { border: 1px solid #DDE3EA; border-radius: 8px; padding: 10px 12px; border-top: 5px solid; }
.card .t { display: block; font-size: 11pt; font-weight: 700; margin-bottom: 3px; }
.card .ask { color: #5B6573; font-size: 9.5pt; margin-top: 6px; }
table { width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 10pt; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #E3E8EE; vertical-align: top; }
th { background: #F3F6F9; font-weight: 600; }
td.n { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.box { background: #F6F8FA; border-left: 4px solid #123A5E; padding: 8px 12px; margin: 10px 0; border-radius: 0 6px 6px 0; }
.warn { background: #FDF3F2; border-left-color: #C8423B; }
.steps { counter-reset: s; margin: 8px 0; padding: 0; list-style: none; }
.steps li { counter-increment: s; margin: 6px 0 6px 30px; position: relative; }
.steps li::before { content: counter(s); position: absolute; left: -30px; top: 0; width: 20px; height: 20px; border-radius: 50%; background: #123A5E; color: white; font-size: 9pt; text-align: center; line-height: 20px; font-weight: 600; }
.small { font-size: 9pt; color: #5B6573; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
"""

KEY = (f'<div class="key"><span><i class="sw" style="background:{PUR}"></i>Queue: maker working on another fund</span>'
       f'<span><i class="sw" style="background:{BLU}"></i>Own recon: maker reconciling this fund</span>'
       f'<span><i class="sw" style="background:{AMB}"></i>Other hold-up: everything else</span></div>')

KEY_T = (f'<div class="key"><span><i class="sw" style="background:{INK};transform:rotate(45deg) scale(.75);border-radius:1px"></i> pricing arrived</span>'
         f'<span><i class="sw" style="background:{GRY}"></i>fund waiting (pricing arrived → Calculated)</span>'
         f'<span><i class="sw" style="background:{INK}"></i>work window (recon budget before Calculated)</span>'
         f'<span><i class="sw" style="background:{PUR}"></i>overlap = queue minutes</span></div>')


def page1():
    return f"""
<section class="page">
<h1>How the wait after pricing is split</h1>
<div class="sub">NAV Bottleneck report · Page 1 chart "Where funds waited after pricing arrived" · worked examples from the template's sample data, 31 Aug 2026</div>

<p><b>The wait after pricing</b> is the time from when the pricing file <b>arrived</b> to when the maker marked the fund <b>Calculated</b>.
The report cuts that one stretch of time into three parts. The three always add back to the total.</p>
{fig_overview()}
{KEY}

<div class="cards">
<div class="card" style="border-top-color:{PUR}"><span class="t">Queue</span>Minutes when the <b>same maker was working on a different fund</b>.
<div class="ask">Points to: capacity, workload, the order funds are picked up.</div></div>
<div class="card" style="border-top-color:{BLU}"><span class="t">Own recon</span>Minutes the maker spent <b>reconciling this fund</b>, up to its recon budget.
<div class="ask">Points to: expected work. Not a problem in itself.</div></div>
<div class="card" style="border-top-color:{AMB}"><span class="t">Other hold-up</span><b>Everything else</b>: the fund waited, but not for the maker's other work or its own recon.
<div class="ask">Points to: data not ready, recon breaks, recon over budget, work not in the status log.</div></div>
</div>

<h2>An everyday picture: a clinic</h2>
<table>
<tr><th style="width:24%">Report term</th><th>In a clinic</th><th style="width:30%">If this is large…</th></tr>
<tr><td>Fund · maker · pricing arrived</td><td>Patient · doctor · patient checks in</td><td></td></tr>
<tr><td><span class="sw" style="background:{PUR}"></span> Queue</td><td>The doctor is seeing <b>other patients</b></td><td>…you need more doctors, or a better order</td></tr>
<tr><td><span class="sw" style="background:{BLU}"></span> Own recon</td><td>The doctor is <b>reading your file</b> before calling you in</td><td>…that is normal preparation</td></tr>
<tr><td><span class="sw" style="background:{AMB}"></span> Other hold-up</td><td>The doctor is free, but you still wait, for example for <b>lab results</b></td><td>…fix the lab, not the doctor's diary</td></tr>
</table>

<div class="box"><b>Why not call it "idle"?</b> The same maker usually does both the reconciliation and the calculation.
Time spent reconciling the fund is work, so it gets its own colour. Only what is left after queue and own recon is called other hold-up.</div>
</section>"""


def page2():
    return f"""
<section class="page">
<h2>Step 1 · Three ingredients for every fund-day</h2>
<p>Everything comes from data the template already holds. Nothing extra is captured.</p>
{fig_ingredients()}
<ol class="steps">
<li><b>Pricing arrived</b>: when the TOP pricing file landed (Fact_Milestone, looked up into Fact_Work column U).</li>
<li><b>Calculated</b>: when the maker set the fund to "Calculated" in the status log (Fact_Work column W, the NAV start).</li>
<li><b>Work window</b>: no system records when someone <i>starts</i> a fund, so the template estimates it as
<b>Calculated minus the fund's recon budget</b> (Recon_Mins, from the weightage). For FD-1007 that is 15:22 − 20.8 min = 15:01. These are Fact_Work columns BS (start) and BT (end).</li>
</ol>

<h2>Step 2 · Fill three buckets, in this order</h2>
<table>
<tr><th style="width:6%">#</th><th style="width:20%">Bucket</th><th>Rule</th></tr>
<tr><td>1</td><td><span class="sw" style="background:{PUR}"></span> Queue</td><td>Look at the <b>same maker's other fund-days on the same processing date</b>. Add up every minute where their work window overlaps this fund's wait. Never more than the total wait.</td></tr>
<tr><td>2</td><td><span class="sw" style="background:{BLU}"></span> Own recon</td><td>From what is left, take up to <b>this fund's recon budget</b>.</td></tr>
<tr><td>3</td><td><span class="sw" style="background:{AMB}"></span> Other hold-up</td><td>Whatever is left: wait − queue − own recon.</td></tr>
</table>
<p>Because bucket 3 takes the remainder, the three parts always add up to the wait exactly. The Checks sheet line <i>"Wait split does not add up"</i> must read 0.</p>

<div class="box"><b>Why only overlaps, not "until the maker's previous fund finished"?</b>
If the fund ahead was itself stuck (say, waiting for data), the maker was not actually busy, and that stuck time should not be blamed on capacity.
Counting only the minutes inside other funds' work windows stops one fund's hold-up being passed down the line as "queue".</div>
</section>"""


def page3():
    return f"""
<section class="page">
<h2>Worked example · FD-1007, maker Lim Wei Ming, 31 Aug</h2>
<p>Lim calculated three funds that day. Each row shows the fund waiting (grey, from its pricing diamond to its Calculated time) and its work window (dark).
The bottom row is FD-1007's wait; the purple slices are the minutes Lim's work on the other two funds falls inside it.</p>
{KEY_T}
{fig_lim()}
<table>
<tr><th>Step</th><th>Working</th><th class="n">Minutes</th></tr>
<tr><td>Total wait</td><td>Pricing arrived 11:58 → Calculated 15:22</td><td class="n">204</td></tr>
<tr><td><span class="sw" style="background:{PUR}"></span> Queue</td><td>FD-1001 work window 13:49:30–14:18 lies fully inside the wait: 28.5 min.<br>FD-1005 work window 15:14:06–15:37 overlaps the wait until 15:22: 7.9 min.<br>28.5 + 7.9 = 36.4, rounded</td><td class="n">36</td></tr>
<tr><td><span class="sw" style="background:{BLU}"></span> Own recon</td><td>FD-1007 recon budget is 20.8 min. 204 − 36 = 168 min is left, so the full budget fits. Rounded</td><td class="n">21</td></tr>
<tr><td><span class="sw" style="background:{AMB}"></span> Other hold-up</td><td>204 − 36 − 21</td><td class="n">147</td></tr>
</table>
{stacked_page3()}
<div class="box"><b>How to read it.</b> For about 2½ hours of FD-1007's wait, Lim was not recorded working on another fund and the fund's own recon budget only explains 21 minutes.
That 147 minutes is what to investigate: was data late, was there a recon break, or does the recon really take far longer than its budget?</div>
<p class="small">The own-recon minutes are an amount, not a place on the clock: they are taken from whatever time is left after the queue. That is why the split bar is drawn separately from the timeline.</p>
</section>"""


def stacked_page3():
    return svg(780, 50, stacked([(36, PUR, ""), (21, BLU, ""), (147, AMB, "")], y=25, label="FD-1007 split"), "FD-1007 split")


def page4():
    s1 = fig_scenario([("FD-1001", "11:03", "13:49:30", "14:18"), ("FD-1007", "11:58", "15:01:12", "15:22"), ("FD-1005", "11:03", "15:14:06", "15:37")],
                      "FD-1001", "10:50", "15:45", [], [], [(0, PUR, ""), (29, BLU, ""), (166, AMB, "")], "Scenario A")
    s2 = fig_scenario([("FD-1003", "11:58", "11:42:30", "12:10"), ("FD-1004", "11:19", "14:41:12", "15:09")],
                      "FD-1003", "11:10", "15:20", [], [], [(0, PUR, ""), (12, BLU, ""), (0, AMB, "")], "Scenario B")
    s3 = fig_scenario([("Fund X", "11:00", "11:05", "11:45"), ("Fund Y", "11:00", "11:50", "12:30"), ("Fund Z", "11:00", "12:35", "13:15")],
                      "Fund Z", "10:50", "13:25", [], [("11:05", "11:45"), ("11:50", "12:30")],
                      [(80, PUR, ""), (40, BLU, ""), (15, AMB, "")], "Scenario C")
    return f"""
<section class="page">
<h2>Three more situations</h2>
{KEY_T}

<h3>A · First fund of the day, mostly other hold-up (FD-1001, Lim, 31 Aug)</h3>
{s1}
<p>Pricing arrived 11:03, Calculated 14:18: a 195-minute wait. Lim's other work windows that day (FD-1007, FD-1005) are all <b>after</b> 14:18, so nothing overlaps:
<b>queue 0</b>. Own recon takes its full budget of 28.5 → <b>29</b>. The remaining <b>166 minutes</b> are other hold-up, the strongest signal on the day that something other than workload held this fund.</p>

<h3>B · Short wait, recon capped (FD-1003, Chen Xiao, 31 Aug)</h3>
{s2}
<p>Pricing arrived 11:58 and Chen calculated at 12:10: only <b>12 minutes</b> of wait. The recon budget is 27.5 minutes, but only 12 minutes of wait exist,
so own recon is <b>capped at 12</b> and other hold-up is <b>0</b>. Much of the recon happened before pricing even arrived, which is the healthy pattern.</p>

<h3>C · A real capacity problem (made-up example, for illustration)</h3>
{s3}
<p>Pricing for three funds lands at 11:00 and one maker works them back to back. Fund Z waits 135 minutes (11:00 → 13:15).
Its wait overlaps Fund X's work window (40 min) and Fund Y's (40 min): <b>queue 80</b>. Own recon takes its 40-minute budget, and only <b>15</b> minutes are other hold-up.
Mostly purple means the fix is capacity or a better pick-up order, not the data.</p>
<p class="small">Your sample data has no day like C: across it, queue is about 5% of the wait, own recon 12% and other hold-up 83%.</p>
</section>"""


def page5():
    return f"""
<section class="page">
<h2>Reading the chart, and what to do</h2>
<table>
<tr><th style="width:22%">If the bar is mostly…</th><th>It means</th><th style="width:36%">Look at</th></tr>
<tr><td><span class="sw" style="background:{PUR}"></span> Purple (queue)</td><td>Funds waited while their maker was busy on other funds.</td><td>Workload per analyst, reassignment, the order funds are picked up, month-end peaks.</td></tr>
<tr><td><span class="sw" style="background:{BLU}"></span> Blue (own recon)</td><td>Funds were being reconciled after pricing arrived.</td><td>Whether more recon could be done before pricing lands.</td></tr>
<tr><td><span class="sw" style="background:{AMB}"></span> Amber (other hold-up)</td><td>Funds waited for something other than the maker's work.</td><td>Late data, recon breaks, recon budgets that are too low, work outside the status log.</td></tr>
</table>
<p>The chart groups fund-days four ways: broker-dependent or not, and thin or ample custody slack. A fund-day sits in one broker group <i>and</i> one custody group, so the groups overlap.
If one group carries much more amber than its partner, that dependency is the likely hold-up.</p>

<h2>Where each number lives in the workbook</h2>
<table>
<tr><th style="width:30%">Fact_Work column</th><th>What it holds</th></tr>
<tr><td>AC · Wait_After_Pricing_Mins</td><td>Calculated − pricing arrival, never below 0</td></tr>
<tr><td>BS · Work_Start_Num<br>BT · Work_End_Num</td><td>Each fund-day's work window: Calculated − recon budget, to Calculated</td></tr>
<tr><td>BD · Queue_Wait_Mins</td><td>Overlap of this fund's wait with the same maker's other work windows, same processing date, capped at the wait</td></tr>
<tr><td>BE · Own_Recon_Mins</td><td>The smaller of (wait − queue) and the recon budget</td></tr>
<tr><td>BR · Other_Holdup_Mins</td><td>Wait − queue − own recon</td></tr>
</table>
<p>In Power BI: <b>[Avg Queue Wait]</b>, <b>[Avg Own Recon Wait]</b>, <b>[Avg Other Holdup Wait]</b> on the chart; <b>[Queue Share of Wait]</b>, <b>[Own Recon Share of Wait]</b> and <b>[Other Holdup Share of Wait]</b> for cards. The three shares add to 100%.</p>

<div class="box warn"><b>What this can and cannot claim</b>
<ul style="margin:4px 0 0 18px;padding:0">
<li><b>Reconstructed, not observed.</b> Work windows are estimated from recon budgets, because no system records when work starts.</li>
<li>Recon that runs <b>over</b> its budget shows up as other hold-up. A fund that is always amber may simply have a budget that is too low.</li>
<li>Only work in the <b>status log</b> counts. Meetings, queries and non-NAV tasks are invisible and land in other hold-up.</li>
<li>Estimated work windows can overlap one another. Queue is counted first; own recon comes from what is left.</li>
</ul></div>

<div class="box"><b>One line for the textbox:</b> Waiting: purple is queueing behind other funds, blue is the maker reconciling this fund, amber is any other hold-up such as data or breaks.</div>
</section>"""


html = f"""<!doctype html><html><head><meta charset="utf-8"><title>How the wait after pricing is split</title><style>{CSS}</style></head>
<body>{page1()}{page2()}{page3()}{page4()}{page5()}</body></html>"""
open(sys.argv[1], "w", encoding="utf-8").write(html)
print("wrote", sys.argv[1])
