"""Mock-up PDF comparing ways to show team capacity by hour (simulated data).

Usage: python3 -I build/mock_team_load.py <out.pdf>
"""
import sys
import random
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

NAVY, INK, MUT, GRID = "#123A5E", "#1F2933", "#5B6573", "#E6EAEF"
PUR, GRN, BLU, AMB, RED, GRY = "#7B5EA7", "#2E9E5B", "#2F6FB0", "#E8A33D", "#C8423B", "#9AA5B1"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": "#C9D1DB",
                     "axes.labelcolor": MUT, "xtick.color": MUT, "ytick.color": MUT})

# ------------------------------------------------------------------ simulate one busy day
rng = random.Random(7)
N_ANALYSTS, SHIFT = 6, (9, 18)
tops = [(10.75, 6), (11.25, 7), (11.67, 6), (12.17, 6), (13.0, 5)]          # pricing arrival, funds
funds = []
for arr, n in tops:
    for _ in range(n):
        f = dict(arr=arr + rng.uniform(0, 0.05),
                 recon=rng.uniform(18, 36) / 60, nav=rng.uniform(12, 30) / 60,
                 check=rng.uniform(5, 15) / 60, tail=rng.uniform(5, 35) / 60)
        f["cut"] = round((arr + rng.uniform(2.4, 4.2)) * 4) / 4
        funds.append(f)
funds.sort(key=lambda f: f["arr"])
free = [SHIFT[0]] * N_ANALYSTS
for i, f in enumerate(funds):
    a = min(range(N_ANALYSTS), key=lambda k: free[k])
    f["start"] = max(f["arr"], free[a])
    f["calc"] = f["start"] + f["recon"]                       # Calculated (NAV start)
    free[a] = f["calc"] + f["nav"]
    f["ctl"] = f["calc"] + f["nav"] + rng.uniform(0, 55) / 60  # Controlled (waits for a checker)
    f["fa"] = f["ctl"] + f["check"]
    f["dlv"] = f["fa"] + f["tail"]
    f["name"] = f"F-{1000 + i:04d}"

hours = np.arange(9, 19)
cut_due = [sum(h <= f["cut"] < h + 1 for f in funds) for h in hours]
awaiting = [sum(f["calc"] < h + 1 and f["ctl"] > h for f in funds) for h in hours]
rostered = [N_ANALYSTS if SHIFT[0] <= h < SHIFT[1] else 0 for h in hours]
seen = [min(N_ANALYSTS, sum(h <= t < h + 1 for f in funds for t in (f["calc"], f["ctl"], f["fa"])) // 2 + 1)
        if 11 <= h <= 17 else 0 for h in hours]


def work_left(f, t):
    """Budgeted hours of work still to do on fund f at time t (0 once controlled)."""
    if t < f["arr"] or t >= f["ctl"]:
        return 0.0
    if t < f["start"]:
        return f["recon"] + f["nav"] + f["check"]
    if t < f["calc"]:
        return (f["calc"] - t) + f["nav"] + f["check"]
    if t < f["calc"] + f["nav"]:
        return (f["calc"] + f["nav"] - t) + f["check"]
    return f["check"]


load = []
for h in hours:
    need = sum(max(work_left(f, h), work_left(f, h + 0.5)) for f in funds) * 60     # minutes in hand during the hour
    avail = rostered[list(hours).index(h)] * 60
    load.append(100 * need / avail if avail else 0)

at_risk = []
for h in hours:
    t = h + 0.5
    at_risk.append([f for f in funds if f["dlv"] > t and work_left(f, t) + f["tail"] > (f["cut"] - t)])

grid = np.linspace(9, 18.5, 400)
cum = {k: [sum(f[k] <= t for f in funds) for t in grid] for k in ("arr", "calc", "ctl", "cut")}


# ------------------------------------------------------------------ drawing helpers
def hhmm(h):
    return f"{int(h):02d}:{int(round((h % 1) * 60)):02d}"


def style(ax, title, sub=None):
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold", color=NAVY, pad=24 if sub else 8)
    if sub:
        ax.text(0, 1.015, sub, transform=ax.transAxes, fontsize=8, color=MUT, va="bottom")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def hour_axis(ax):
    ax.set_xticks(hours)
    ax.set_xticklabels([f"{h:02d}:00" for h in hours], fontsize=8)


def draw_current(ax, compact=False):
    w = 0.38
    ax.bar(hours - w / 2, cut_due, w, color=RED, label="Client cut-offs due")
    ax.bar(hours + w / 2, awaiting, w, color=BLU, label="Funds awaiting control")
    ax.plot(hours, rostered, "--", color=GRY, lw=2, label="Rostered analysts")
    ax.plot(hours, seen, "-o", color=INK, lw=1.5, ms=3, label="Analysts seen working")
    hour_axis(ax)
    ax.set_ylabel("count")
    ax.legend(fontsize=7, frameon=False, loc="upper left", ncol=2 if compact else 1)


def draw_load(ax, compact=False):
    cols = [RED if v > 100 else (AMB if v > 80 else GRN) for v in load]
    ax.bar(hours, load, 0.6, color=cols)
    ax.axhline(100, color=INK, lw=1.2, ls="--")
    ax.text(8.55, 106, "100% = all rostered time already needed", fontsize=7, color=INK, va="bottom")
    for h, v in zip(hours, load):
        if v > 0:
            ax.text(h, v + 4, f"{v:.0f}%", ha="center", fontsize=7, color=INK)
    hour_axis(ax)
    ax.set_ylabel("work needed ÷ time available")
    ax.set_xlim(8.4, 19.6 if not compact else 19.9)
    ax.set_ylim(0, max(load) * 1.18)


def draw_cfd(ax, compact=False):
    ax.plot(grid, cum["arr"], color=PUR, lw=2, label="Pricing arrived")
    ax.plot(grid, cum["calc"], color=GRN, lw=2, label="NAV started (Calculated)")
    ax.plot(grid, cum["ctl"], color=BLU, lw=2, label="Controlled")
    ax.plot(grid, cum["cut"], color=RED, lw=2, ls="--", label="Client cut-offs due")
    ax.fill_between(grid, cum["calc"], cum["arr"], color=PUR, alpha=0.12)
    late = np.array(cum["ctl"]) < np.array(cum["cut"])
    ax.fill_between(grid, cum["ctl"], cum["cut"], where=late, color=RED, alpha=0.18)
    if not compact:
        i = int(np.argmax(np.array(cum["arr"]) - np.array(cum["calc"])))
        ax.annotate(f"backlog: {cum['arr'][i] - cum['calc'][i]} funds\nwith pricing, not started",
                    xy=(grid[i], (cum["arr"][i] + cum["calc"][i]) / 2), xytext=(grid[i] + 1.4, 6),
                    fontsize=8, color=PUR, arrowprops=dict(arrowstyle="->", color=PUR))
        j = np.where(late)[0]
        nb = sum(f["dlv"] > f["cut"] for f in funds)
        if not len(j):
            gap = np.array(cum["ctl"]) - np.array(cum["cut"])
            ccut = np.array(cum["cut"])
            win = (ccut > 0) & (ccut < len(funds))
            k = int(np.argmin(np.where(win, gap, 99)))
            ax.annotate(f"closest point: {gap[k]} funds of margin,\nyet {nb} funds breached individually:\n"
                        "running totals can hide late funds",
                        xy=(grid[k], (cum["ctl"][k] + cum["cut"][k]) / 2), xytext=(15.9, 7),
                        fontsize=8, color=RED, arrowprops=dict(arrowstyle="->", color=RED))
        if len(j):
            k = j[len(j) // 2]
            ax.annotate("red area: fewer funds controlled\nthan cut-offs already passed",
                        xy=(grid[k], (cum["ctl"][k] + cum["cut"][k]) / 2), xytext=(grid[k] - 3.2, 26),
                        fontsize=8, color=RED, arrowprops=dict(arrowstyle="->", color=RED))
    hour_axis(ax)
    ax.set_xlim(9, 18.5)
    ax.set_ylabel("funds (running total)")
    ax.legend(fontsize=7, frameon=False, loc="upper left")


def draw_risk(ax, compact=False):
    n = [len(x) for x in at_risk]
    ax.bar(hours, n, 0.6, color=[RED if v else GRY for v in n])
    for h, v in zip(hours, n):
        if v:
            ax.text(h, v + 0.2, str(v), ha="center", fontsize=8, color=INK)
    hour_axis(ax)
    ax.set_ylabel("funds at risk (mid-hour)")
    ax.set_ylim(0, max(n) + 2)


def header(fig, title, page, sub="Date: 31 Aug 2026 · Whole team (6 analysts) · 30 fund-days"):
    fig.patches.append(Rectangle((0, 0.935), 1, 0.065, transform=fig.transFigure, color=NAVY, zorder=0))
    fig.text(0.02, 0.962, title, color="white", fontsize=15, fontweight="bold", va="center")
    fig.text(0.98, 0.962, f"Page {page} of 5", color="#C9D1DB", fontsize=9, va="center", ha="right")
    fig.text(0.02, 0.905, sub, fontsize=9, color=MUT)
    fig.text(0.98, 0.905, "MOCKUP — simulated data, not your results", fontsize=9, color=RED,
             fontweight="bold", ha="right")


def notes(fig, x, y, w, items, title="How to read it"):
    fig.text(x, y, title, fontsize=11, fontweight="bold", color=NAVY, va="top")
    yy = y - 0.045
    for head, body in items:
        fig.text(x, yy, head, fontsize=9, fontweight="bold", color=INK, va="top")
        txt = fig.text(x, yy - 0.028, body, fontsize=8.5, color=INK, va="top", wrap=True)
        txt._get_wrap_line_width = lambda w=w, f=fig: w * f.get_figwidth() * 72
        lines = max(1, int(len(body) / (w * 175)) + 1)
        yy -= 0.05 + 0.024 * lines


# ------------------------------------------------------------------ pages
def page_overview(pdf):
    fig = plt.figure(figsize=(16, 9))
    header(fig, "Team load by hour — four ways to show it", 1)
    specs = [(draw_current, "Current: counts by hour", "Cut-offs and funds vs head count. Mixes funds with people."),
             (draw_load, "Option 1 · Load %", "Minutes of work in hand ÷ minutes of analysts rostered."),
             (draw_cfd, "Option 2 · Cumulative flow", "Running totals: arrived, started, controlled vs cut-offs due."),
             (draw_risk, "Option 3 · Funds at risk", "Funds whose work left is more than the time left to cut-off.")]
    for i, (fn, t, s) in enumerate(specs):
        ax = fig.add_axes([0.05 + (i % 2) * 0.49, 0.50 - (i // 2) * 0.43, 0.42, 0.30])
        fn(ax, compact=True)
        style(ax, t, s)
    pdf.savefig(fig)
    plt.close(fig)


def page_single(pdf, page, title, fn, chart_title, sub, items, extra=None):
    fig = plt.figure(figsize=(16, 9))
    header(fig, title, page)
    ax = fig.add_axes([0.05, 0.12, 0.60, 0.68])
    fn(ax)
    style(ax, chart_title, sub)
    notes(fig, 0.70, 0.83, 0.27, items)
    if extra:
        extra(fig)
    pdf.savefig(fig)
    plt.close(fig)


def risk_table(fig):
    h = 15
    rows = sorted(at_risk[list(hours).index(h)], key=lambda f: f["cut"])[:7]
    fig.text(0.70, 0.33, f"At risk at {h}:30 (first {len(rows)})", fontsize=10, fontweight="bold", color=NAVY)
    y = 0.30
    for c, x in zip(("Fund", "Cut-off", "Work left", "Time left"), (0.70, 0.77, 0.83, 0.90)):
        fig.text(x, y, c, fontsize=8, fontweight="bold", color=MUT)
    for f in rows:
        y -= 0.028
        t = h + 0.5
        left = (work_left(f, t) + f["tail"]) * 60
        time_left = (f["cut"] - t) * 60
        for v, x, col in ((f["name"], 0.70, INK), (hhmm(f["cut"]), 0.77, INK),
                          (f"{left:.0f} min", 0.83, INK), (f"{time_left:.0f} min", 0.90, RED)):
            fig.text(x, y, v, fontsize=8, color=col)


def page_recommended(pdf):
    fig = plt.figure(figsize=(16, 9))
    header(fig, "Recommended: cumulative flow with load % underneath", 5)
    ax1 = fig.add_axes([0.05, 0.40, 0.60, 0.42])
    draw_cfd(ax1, compact=True)
    style(ax1, "Is work keeping pace with deadlines?", "Option 2 · running totals across the day")
    ax1.set_xticklabels([])
    ax2 = fig.add_axes([0.05, 0.10, 0.60, 0.22], sharex=ax1)
    cols = [RED if v > 100 else (AMB if v > 80 else GRN) for v in load]
    ax2.bar(hours, load, 0.6, color=cols)
    ax2.axhline(100, color=INK, lw=1.2, ls="--")
    for h, v in zip(hours, load):
        if v > 0:
            ax2.text(h, v + 4, f"{v:.0f}%", ha="center", fontsize=7, color=INK)
    ax2.set_ylim(0, max(load) * 1.25)
    ax2.set_ylabel("load %")
    hour_axis(ax2)
    style(ax2, "Do we have enough people at that hour?", "Option 1 · work in hand ÷ rostered time")
    notes(fig, 0.70, 0.83, 0.27, [
        ("Read top to bottom",
         "The top chart shows when the team fell behind; the bar underneath shows whether it was short of people at that hour."),
        ("Behind and over 100%",
         "Capacity problem: more work in hand than people could do. Fix staffing or the pick-up order."),
        ("Behind but under 100%",
         "Not a people problem: funds were held by data, breaks or approvals. Look at Page 1's other hold-up."),
        ("Tooltip",
         "Hovering an hour shows funds awaiting control and funds at risk, so the control workload you asked for stays visible."),
        ("Card beside it",
         "Option 3's 'funds at risk now' works as a single number card on the page."),
    ])
    pdf.savefig(fig)
    plt.close(fig)


with PdfPages(sys.argv[1]) as pdf:
    page_overview(pdf)
    page_single(pdf, 2, "Option 1 · Load % by hour", draw_load, "Do we have enough people at that hour?",
                "Budgeted minutes of work in hand during the hour ÷ rostered analysts × 60", [
                    ("What it shows", "For each hour, the work the team had in hand (funds with pricing, not yet controlled: "
                                      "their remaining recon, NAV and check budget) divided by the minutes of analysts on shift."),
                    ("Colours", "Green under 80%, amber 80–100%, red over 100%: more work in hand than people could do in that hour."),
                    ("Why it is better", "Both sides are minutes, so a 90-minute fund weighs more than a 20-minute one. "
                                         "It peaks before the cut-off cluster, where the pressure really is."),
                    ("Watch out", "Uses budgeted minutes from the weightage, so it is only as right as the budgets. "
                                  "Assumes everyone rostered is available (no leave data)."),
                ])
    page_single(pdf, 3, "Option 2 · Cumulative flow", draw_cfd, "Is work keeping pace with deadlines?",
                "Running count of funds through each step, against cut-offs due", [
                    ("What it shows", "Four running totals across the day. Each line climbs by one when a fund reaches that step."),
                    ("Purple shading", "Gap between 'pricing arrived' and 'NAV started': funds with pricing in hand that nobody has started."),
                    ("Red shading", "Where 'controlled' drops below 'cut-offs due': more cut-offs have passed than funds "
                                    "controlled, so breaches are forming. None appears on this day (see Watch out)."),
                    ("Why it is better", "Only real timestamps, no reconstruction. The template's Dim_Clock and Arrival_Hr / Start_Hr / "
                                         "End_Hr columns were built for this chart."),
                    ("Watch out", "Running totals can hide individual late funds: on this day 7 funds breached but the lines never "
                                  "cross. It also shows that the team fell behind, not why. Pair it with Option 1 (why) and "
                                  "Option 3 or the timeline (which funds)."),
                ])
    page_single(pdf, 4, "Option 3 · Funds at risk by hour", draw_risk, "Which hours start to lose funds?",
                "Funds not yet delivered whose remaining work + sign-off tail exceeds time left to cut-off", [
                    ("What it shows", "At the middle of each hour, the funds that cannot make their cut-off even if worked "
                                      "without a break from now. An early warning, hour by hour."),
                    ("Table", "Lists the funds behind one bar, so the team knows which ones to escalate."),
                    ("Why it is useful", "Very actionable: it names funds, not averages. Same logic as Breach_Class 'Lost on arrival'."),
                    ("Watch out", "A list of problems, not a picture of capacity. Best as a card or drill-down beside Option 1 or 2."),
                ], extra=risk_table)
    page_recommended(pdf)
print("wrote", sys.argv[1])
