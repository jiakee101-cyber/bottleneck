"""Compare the Power Query mirror (pq_reference.py) with the v4.5 formulas.

Usage: python3 -I build/pq_verify.py <inputs.xlsx> <same workbook recalculated by Excel/LibreOffice>
"""
import sys, os, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import openpyxl
import pq_reference as ref

inp, calc = sys.argv[1], sys.argv[2]
got = ref.run(inp)
wb = openpyxl.load_workbook(calc, data_only=True)

def rows(name, keycols):
    ws = wb[name]; hdr = [c.value for c in ws[1]]; out = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        rec = dict(zip(hdr, r))
        k = tuple(rec[c] for c in keycols)
        if any(v in (None, "") for v in k): continue
        out[norm_key(k)] = rec
    return hdr, out

def norm_key(k):
    return tuple((v.date() if isinstance(v, dt.datetime) and v.time() == dt.time() else v) if not isinstance(v, str) else v.strip().upper() for v in k)

def eq(a, b):
    a = None if a == "" else a; b = None if b == "" else b
    if isinstance(b, str) and b.startswith("#"):
        errors.append(b); return True, "excel-error"
    if a is None and b is None: return True, ""
    if isinstance(b, dt.datetime) and b.time() == dt.time() and type(a) is dt.date: return a == b.date(), ""
    if isinstance(b, dt.datetime) and isinstance(a, (int, float)) and not isinstance(a, bool):
        a = ref.EPOCH + dt.timedelta(days=a)
    if isinstance(a, dt.datetime) or isinstance(b, dt.datetime):
        if isinstance(b, (int, float)) and not isinstance(b, bool): b = ref.EPOCH + dt.timedelta(days=b)
        if isinstance(a, dt.datetime) and isinstance(b, dt.datetime): return abs((a - b).total_seconds()) < 1, ""
        return False, ""
    if isinstance(a, dt.date) and isinstance(b, dt.date): return a == b, ""
    try:
        fa, fb = float(a), float(b)
        return abs(fa - fb) < 1e-6 * max(1, abs(fb)), ""
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip(), ""

total = bad = 0; issues = {}; errors = []
def compare(table, keycols, gotrows, skip=()):
    global total, bad
    hdr, exp = rows(table, keycols)
    seen = set()
    for g in gotrows:
        k = norm_key(tuple(g[c] for c in keycols)); seen.add(k)
        e = exp.get(k)
        if e is None: issues.setdefault((table, "row missing in Excel"), []).append(k); continue
        for c in hdr:
            if c is None or c in skip or c not in g: continue
            total += 1
            ok, why = eq(g[c], e[c])
            if not ok:
                bad += 1; issues.setdefault((table, c), []).append((k, g[c], e[c]))
    for k in exp:
        if k not in seen: issues.setdefault((table, "row missing in PQ"), []).append(k)

compare("Dim_Fund", ["Fund_ID"], got["Dim_Fund"], skip={"Runs_Observed", "NAV_Frequency_Observed"})
compare("Dim_TOP", ["TOP_ID"], got["Dim_TOP"], skip={"TOP_Days_Scored", "TOP_Days_Late", "Late_Hours_Total", "Breached_Fund_Days_When_Late"})
compare("Dim_Team", ["Team_ID"], got["Dim_Team"])
compare("Dim_Analyst", ["Analyst_Name"], got["Dim_Analyst"])
compare("Fact_Milestone", ["Process_Date", "TOP_ID"], got["Fact_Milestone"])
compare("Fact_Work", ["NAV_Date", "Process_Date", "Fund_ID"], got["Fact_Work"])
print("cells compared:", total, " mismatches:", bad, " Excel error cells skipped:", len(errors))
for (t, c), lst in sorted(issues.items()):
    print("%-15s %-30s %4d  e.g. %s" % (t, c, len(lst), lst[:3]))
