"""Python mirror of the v5 Power Query queries (powerquery/*.pq), step for step.

Used only to verify the Power Query logic against the v4.5 Excel formulas: run it on a workbook's input
columns and compare with the same workbook recalculated by Excel/LibreOffice (see pq_verify.py).
Function and variable names follow the .pq files so the two can be read side by side.
"""
import datetime as dt
import math
from decimal import Decimal, ROUND_HALF_UP
import openpyxl

EPOCH = dt.datetime(1899, 12, 30)
S_CALC = "changed to the status of calculated"
S_CTRL = "changed to the status of controlled"
S_FA = "changed to the status of fund accounting signed off"
S_SO = "changed to the status of signed off"


# ---------------------------------------------------------------- fxNAV
def is_blank(v): return v is None or (isinstance(v, str) and v.strip() == "")
def txt(v): return None if is_blank(v) else str(v).strip()
def key(v): return None if is_blank(v) else str(v).strip().upper()
def same(a, b): return ("" if a is None else str(a).strip().upper()) == ("" if b is None else str(b).strip().upper())
def is_yes(v): return key(v) == "YES"
def is_no(v): return key(v) == "NO"
def num(v):
    if is_blank(v): return None
    if isinstance(v, bool): return None
    if isinstance(v, (int, float)): return v
    try: return float(v)
    except Exception: return None
def N(v): return v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0
def to_date(v):
    if is_blank(v): return None
    if isinstance(v, dt.datetime): return v.date()
    if isinstance(v, dt.date): return v
    return None
def to_datetime(v):
    if is_blank(v): return None
    if isinstance(v, dt.datetime): return v
    if isinstance(v, dt.date): return dt.datetime.combine(v, dt.time())
    if isinstance(v, (int, float)): return EPOCH + dt.timedelta(days=v)
    return None
def to_time(v):
    if is_blank(v): return None
    if isinstance(v, dt.time): return v
    if isinstance(v, dt.datetime): return v.time()
    if isinstance(v, dt.timedelta): return (dt.datetime(2000, 1, 1) + v).time()
    if isinstance(v, (int, float)): return (EPOCH + dt.timedelta(days=v % 1)).time()
    return None
def hr(v):
    t = to_time(v)
    return 0 if t is None else t.hour + t.minute / 60
def R(x, d):
    """ROUND(x, d) half away from zero on the decimal value, as Excel and Number.Round(..., AwayFromZero) give."""
    if x is None: return None
    return float(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))
def R0(x): return R(x, 0)
def floor_step(x, step): return None if x is None else math.floor(x / step) * step
def mins(a, b): return None if a is None or b is None else (a - b).total_seconds() / 60
def hrs_from(x, d): return None if x is None or d is None else (x - dt.datetime.combine(d, dt.time())).total_seconds() / 3600
def hr_of_day(x): return None if x is None else (x - dt.datetime.combine(x.date(), dt.time())).total_seconds() / 3600
def at_hr(d, h): return None if d is None or h is None else dt.datetime.combine(d, dt.time()) + dt.timedelta(seconds=h * 3600)
def add_mins(x, m): return None if x is None or m is None else x + dt.timedelta(seconds=m * 60)
def serial(x): return None if x is None else (x - EPOCH).total_seconds() / 86400
def lookup_of(keys, values):
    out = {}
    for k, v in zip(keys, values):
        k = key(k)
        if k is not None and k not in out: out[k] = v
    return out
def find(lk, k):
    k = key(k)
    return None if k is None else lk.get(k)


def sheet(wb, name, cols):
    ws = wb[name]
    hdr = [c.value for c in ws[1]]
    idx = [hdr.index(c) for c in cols]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        rec = {c: (r[i] if i < len(r) else None) for c, i in zip(cols, idx)}
        if not is_blank(rec[cols[0]]): rows.append(rec)
    return rows


def run(path):
    wb = openpyxl.load_workbook(path, data_only=False)
    # ------------------------------------------------------------ NAV_Config
    cons = {}
    for r in wb["Constants"].iter_rows(min_row=2, values_only=True):
        if not is_blank(r[0]): cons[str(r[0]).strip().lower()] = r[1]
    g = lambda lbl: num(cons[lbl.lower()])
    cfg = dict(FTE=g("FTE denominator"), Cap=g("Daily capacity (minutes)"), Base=g("Base reconciliation %"),
               ETD=g("ETD adjustment"), OTCn=g("OTC (non-CFD) adjustment"), OTCc=g("OTC (CFD) adjustment"),
               PFC=g("PFC adjustment"), EUC=g("EUC adjustment"), Watch=g("Broker slack watchlist threshold (mins)"),
               Peak=g("Peak percentile"), Thin=g("Thin slack threshold (mins)"), Shift=g("Shift length (hrs)"))
    cfg["MPW"] = cfg["Cap"] / cfg["FTE"]
    # ------------------------------------------------------------ Dim_Team
    teams = []
    for r in sheet(wb, "Dim_Team", ["Team_ID", "Team_Name", "Shift_Start", "Shifts_In_Team", "Daily_Capacity_Mins"]):
        s = hr(r["Shift_Start"])
        teams.append(dict(Team_ID=txt(r["Team_ID"]), Team_Name=txt(r["Team_Name"]), Shifts_In_Team=num(r["Shifts_In_Team"]),
                          Daily_Capacity_Mins=num(r["Daily_Capacity_Mins"]), Shift_Start_Hr=s, Shift_End_Hr=s + cfg["Shift"]))
    # ------------------------------------------------------------ Dim_Fund
    cols = ["Fund_ID", "Fund_Name", "Client_ID", "Client_Name", "Strategic_Client", "Team_ID", "Default_Analyst_Name",
            "Weightage", "ETD", "OTC_nonCFD", "OTC_CFD", "PFC", "EUC", "Has_Custody_Process", "Has_TA_Process",
            "Has_Broker_Process", "Custody_Cutoff", "TA_Cutoff", "Broker_ETA", "Pricing_Cutoff", "TOP_ID", "Client_Cutoff",
            "NAV_Deadline", "Signoff_Model", "Cutoff_Data_Quality"]
    raw = sheet(wb, "Dim_Fund", cols)
    seen = set(); funds = []
    for i, r in enumerate(raw, 1):
        k = key(r["Fund_ID"])
        if k in seen: continue
        seen.add(k); r = dict(r); r["Sheet_Row"] = i; funds.append(r)
    team_start = lookup_of([t["Team_ID"] for t in teams], [t["Shift_Start_Hr"] for t in teams])
    so = sheet(wb, "Dim_Signoff", ["Signoff_Model", "Planned_Tail_Mins"])
    so_tail = lookup_of([s["Signoff_Model"] for s in so], [num(s["Planned_Tail_Mins"]) for s in so])
    top_ids = [key(t["TOP_ID"]) for t in sheet(wb, "Dim_TOP", ["TOP_ID"])]
    for r in funds:
        rp = cfg["Base"] + N(r["ETD"]) * cfg["ETD"] + N(r["OTC_nonCFD"]) * cfg["OTCn"] + N(r["OTC_CFD"]) * cfg["OTCc"] \
             + N(r["PFC"]) * cfg["PFC"] + N(r["EUC"]) * cfg["EUC"]
        npct = 100 - rp
        req = R(N(r["Weightage"]) * cfg["MPW"], 1)
        rm = R(req * rp / 100, 1); nm = R(req * npct / 100, 1)
        ch, th, bh, ph, clh, dh = (hr(r[c]) for c in ["Custody_Cutoff", "TA_Cutoff", "Broker_ETA", "Pricing_Cutoff", "Client_Cutoff", "NAV_Deadline"])
        sh = find(team_start, r["Team_ID"]); tail = find(so_tail, r["Signoff_Model"])
        nc, nt, nb = is_no(r["Has_Custody_Process"]), is_no(r["Has_TA_Process"]), is_no(r["Has_Broker_Process"])
        sc = None if nc else R0((ph - ch) * 60); st = None if nt else R0((ph - th) * 60); sb = None if nb else R0((ph - bh) * 60)
        ar = None if sh is None else R0((ph - sh) * 60); an = R0((clh - ph) * 60)
        rok = None if ar is None else ("Yes" if ar >= rm else "No")
        nok = None if tail is None else ("Yes" if an >= nm + tail else "No")
        thin_c = "n/a" if nc else ("Yes" if sc <= cfg["Thin"] else "No")
        r.update(Recon_Pct=rp, NAV_Pct=npct, Required_Mins=req, Recon_Mins=rm, NAV_Mins=nm, Custody_Cutoff_Hr=ch, TA_Cutoff_Hr=th,
                 Broker_ETA_Hr=bh, Pricing_Cutoff_Hr=ph, Client_Cutoff_Hr=clh, NAV_Deadline_Hr=dh, Shift_Start_Hr=sh, Planned_Tail_Mins=tail,
                 Slack_Custody_Mins="n/a" if nc else str(int(sc)), Slack_TA_Mins="n/a" if nt else str(int(st)),
                 Slack_Broker_Mins="n/a" if nb else str(int(sb)), Avail_Recon_Mins=ar, Avail_NAV_Mins=an, Recon_Feasible=rok,
                 NAV_Feasible=nok, Feasibility_Flag=None if rok is None or nok is None else ("OK" if rok == "Yes" and nok == "Yes" else "REVIEW"),
                 Broker_Watchlist="Not applicable" if nb else ("CAPTURE" if sb < cfg["Watch"] else "Not needed"), Slack_Broker_Value=sb,
                 Client_Tier="Strategic" if is_yes(r["Strategic_Client"]) else "Non-strategic",
                 Broker_Dependent="Yes" if is_yes(r["Has_Broker_Process"]) else "No", Thin_Custody_Slack=thin_c,
                 Thin_TA_Slack="n/a" if nt else ("Yes" if st <= cfg["Thin"] else "No"),
                 Thin_Broker_Slack="n/a" if nb else ("Yes" if sb <= cfg["Thin"] else "No"),
                 Custody_Slack_Group="No custody process" if nc else ("Thin custody slack" if thin_c == "Yes" else "Ample custody slack"),
                 Slack_Custody_Num=sc, Slack_TA_Num=st, Slack_Broker_Num=sb)
    slacks = sorted(x["Slack_Broker_Value"] for x in funds if x["Slack_Broker_Value"] is not None)
    earliest = {}
    for x in funds:
        k = key(x["TOP_ID"])
        if k is None: continue
        earliest.setdefault(k, [])
        if x["Pricing_Cutoff_Hr"] > 0: earliest[k].append(x["Pricing_Cutoff_Hr"])
    earliest = {k: (min(v) if v else 0) for k, v in earliest.items()}
    first = {}
    for x in funds:
        if key(x["TOP_ID"]) is None: continue
        p = key(x["TOP_ID"]) + "|" + (key(x["Client_ID"]) or "")
        first.setdefault(p, x["Sheet_Row"])
    firsts = set(first.values())
    for x in funds:
        tk = key(x["TOP_ID"])
        b = None if tk is None or tk not in top_ids else earliest.get(tk)
        vs = None if b is None else R0((x["Pricing_Cutoff_Hr"] - b) * 60)
        x.update(Broker_Slack_Rank="n/a" if is_no(x["Has_Broker_Process"]) else str(sum(1 for s in slacks if s < x["Slack_Broker_Value"]) + 1),
                 TOP_Binding_Cutoff_Hr=b, Cutoff_Vs_TOP_Mins=vs,
                 TOP_Cutoff_Risk=None if vs is None else ("Sets the deadline" if vs <= 0 else "Later than peers by %d min" % vs),
                 Client_First_In_TOP=0 if tk is None else (1 if x["Sheet_Row"] in firsts else 0))
        for c in ["Fund_ID", "Fund_Name", "Client_ID", "Client_Name", "TOP_ID", "Signoff_Model", "Default_Analyst_Name", "Team_ID"]:
            x[c] = txt(x[c])
    # ------------------------------------------------------------ Dim_TOP
    tops = []
    for t in sheet(wb, "Dim_TOP", ["TOP_ID", "TOP_Name", "Pricing_Supplier"]):
        fs = [f for f in funds if key(f["TOP_ID"]) == key(t["TOP_ID"])]
        d = len(fs)
        p = [f["Pricing_Cutoff_Hr"] for f in fs if f["Pricing_Cutoff_Hr"] > 0]
        e = None if d == 0 else (min(p) if p else 0); ff = None if d == 0 else (max(p) if p else 0)
        tops.append(dict(TOP_ID=txt(t["TOP_ID"]), Funds_In_TOP=d, Earliest_Cutoff_Hr=e, Latest_Cutoff_Hr=ff,
                         Cutoff_Spread_Mins=None if d == 0 else R0((ff - e) * 60), Binding_Cutoff_Hr=e,
                         Blast_Radius_Flag=("HIGH — %d funds share this feed" % d) if d >= 4 else (("Medium — %d funds" % d) if d >= 2 else "Single fund"),
                         Clients_In_TOP=sum(f["Client_First_In_TOP"] for f in fs), Share_Of_Funds=d / len(funds) if funds else None))
    # ------------------------------------------------------------ Dim_Analyst
    team_rec = lookup_of([t["Team_ID"] for t in teams], teams)
    books = {}
    for f in funds:
        k = key(f["Default_Analyst_Name"])
        if k: books[k] = books.get(k, 0) + 1
    analysts_raw = sheet(wb, "Dim_Analyst", ["Analyst_Name", "Team_ID", "Active"])
    analysts = []
    for a in analysts_raw:
        t = find(team_rec, a["Team_ID"])
        analysts.append(dict(Analyst_Name=txt(a["Analyst_Name"]), Team_Name="external" if t is None else t["Team_Name"],
                             Shift_Start_Hr=None if t is None else t["Shift_Start_Hr"],
                             Capacity_Mins=0 if t is None else (t["Daily_Capacity_Mins"] or 0),
                             Funds_In_Default_Book=books.get(key(a["Analyst_Name"]), 0),
                             Shift_End_Hr=None if t is None else t["Shift_End_Hr"]))
    # ------------------------------------------------------------ NAV_StatusLog
    log = []
    for r in sheet(wb, "Status_Log", ["Log_NAV_Date", "Log_Process_Date", "Log_Fund_ID", "Log_Status", "Log_Timestamp", "Log_Person_Name"]):
        rec = dict(NAV=to_date(r["Log_NAV_Date"]), Proc=to_date(r["Log_Process_Date"]), Fund=txt(r["Log_Fund_ID"]),
                   Status=txt(r["Log_Status"]), TS=to_datetime(r["Log_Timestamp"]), Person=txt(r["Log_Person_Name"]))
        if rec["Status"] and rec["NAV"] and rec["Proc"] and rec["Fund"]: log.append(rec)
    for i, r in enumerate(log, 1):
        r["Row"] = i; r["SK"] = r["Status"].lower(); r["FK"] = r["Fund"].upper()
    # ------------------------------------------------------------ NAV_MilestoneRaw
    ms_raw = []
    for r in sheet(wb, "Fact_Milestone", ["Process_Date", "TOP_ID", "Actual_Arrival_DT"]):
        rec = dict(Process_Date=to_date(r["Process_Date"]), TOP_ID=txt(r["TOP_ID"]), Actual_Arrival_DT=to_datetime(r["Actual_Arrival_DT"]))
        if rec["Process_Date"]: ms_raw.append(rec)
    dkey = lambda d, t: None if key(t) is None else d.isoformat() + "|" + key(t)
    # ------------------------------------------------------------ NAV_FundDays
    def s6(x): return None if x is None else R(serial(x), 6)
    def person_at(rows, ts):
        if ts is None: return None
        hit = [r for r in rows if s6(r["TS"]) == s6(ts)]
        return min(hit, key=lambda r: r["Row"])["Person"] if hit else None
    groups = {}
    for r in log: groups.setdefault((r["NAV"], r["Proc"], r["FK"]), []).append(r)
    fund_rec = lookup_of([f["Fund_ID"] for f in funds], funds)
    arrivals = {}
    for m in ms_raw:
        k = m["Process_Date"].isoformat() + "|" + (key(m["TOP_ID"]) or "")
        arrivals.setdefault(k, [])
        if m["Actual_Arrival_DT"]: arrivals[k].append(m["Actual_Arrival_DT"])
    arrivals = {k: (max(v) if v else None) for k, v in arrivals.items()}
    fd = []
    for (nav, proc, fk), g in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2])):
        calc = [r for r in g if r["SK"] == S_CALC]; ctrl = [r for r in g if r["SK"] == S_CTRL]
        cts = [r["TS"] for r in calc if r["TS"]]
        cmin = min(cts) if cts else None; cmax = max(cts) if cts else None
        ctl = [r["TS"] for r in ctrl if r["TS"]]; ctlmax = max(ctl) if ctl else None
        fa = [r["TS"] for r in g if r["SK"] == S_FA and r["TS"]]; sso = [r["TS"] for r in g if r["SK"] == S_SO and r["TS"]]
        j = len(calc)
        row = dict(NAV_Date=nav, Process_Date=proc, Fund_ID=min(g, key=lambda r: r["Row"])["Fund"],
                   Status_Calculated_DT=cmin, Status_Controlled_DT=ctlmax, Status_FA_SignedOff_DT=max(fa) if fa else None,
                   Status_SignedOff_DT=max(sso) if sso else None, Recalc_Count=j,
                   Rework_Gap_Mins=0 if j <= 1 else R0(mins(cmax, cmin)), Maker_Name=person_at(calc, cmax), Checker_Found=person_at(ctrl, ctlmax))
        F = find(fund_rec, row["Fund_ID"])
        get = lambda n: None if F is None else F[n]
        top = get("TOP_ID"); clh = get("Client_Cutoff_Hr"); ph = get("Pricing_Cutoff_Hr")
        ak = dkey(proc, top)
        U = None if ak is None else arrivals.get(ak)
        V = at_hr(proc, clh) if clh is not None and clh > 0 else None
        AH = R0(mins(row["Status_SignedOff_DT"], V))
        row.update(Signoff_Model=get("Signoff_Model"), Default_Analyst_Name=get("Default_Analyst_Name"), Required_Mins=get("Required_Mins"),
                   Recon_Mins=get("Recon_Mins"), NAV_Mins=get("NAV_Mins"), Planned_Tail_Mins=get("Planned_Tail_Mins"),
                   Pricing_Arrival_DT=U, Client_Cutoff_DT=V, Breach_Mins=AH, Breached=None if AH is None else ("Yes" if AH > 0 else "No"),
                   TOP_ID=top, Fund_Pricing_Cutoff_Hr=ph, Pricing_Late_Hr=0 if ph is None else ph, Client_Name=get("Client_Name"),
                   Broker_Dependent=get("Broker_Dependent"), Custody_Slack_Group=get("Custody_Slack_Group"),
                   Client_Cutoff_Hr=clh if clh is not None and clh > 0 else None)
        fd.append(row)
    # ------------------------------------------------------------ NAV_TopDays
    topdays = {}
    for r in fd:
        k = dkey(r["Process_Date"], r["TOP_ID"])
        if k is None: continue
        t = topdays.setdefault(k, dict(Fund_Days=0, p=[], Breached_Fund_Days=0))
        t["Fund_Days"] += 1
        if r["Fund_Pricing_Cutoff_Hr"] is not None and r["Fund_Pricing_Cutoff_Hr"] > 0: t["p"].append(r["Fund_Pricing_Cutoff_Hr"])
        if r["Breached"] == "Yes": t["Breached_Fund_Days"] += 1
    for t in topdays.values(): t["Binding_Cutoff_Hr"] = min(t["p"]) if t["p"] else None
    # ------------------------------------------------------------ Fact_Milestone
    fm = []
    for m in ms_raw:
        k = dkey(m["Process_Date"], m["TOP_ID"]); day = None if k is None else topdays.get(k)
        E = 0 if day is None else day["Fund_Days"]; Fh = None if day is None else day["Binding_Cutoff_Hr"]
        G = at_hr(m["Process_Date"], Fh); H = R0(mins(m["Actual_Arrival_DT"], G))
        I = None if H is None else ("Yes" if H <= 0 else "No")
        fm.append(dict(m, Funds_In_TOP=E, Binding_Cutoff_Hr=Fh, Binding_Cutoff_DT=G, Delay_Mins=H, SLA_Met=I,
                       Fund_Days_Impacted=E if I == "No" else 0, Due_Slot_Hr=floor_step(Fh, 0.5),
                       Late_Mins=None if H is None else max(0, H), Breached_Fund_Days=None if Fh is None else day["Breached_Fund_Days"]))
    # ------------------------------------------------------------ Fact_Work
    an_set = lookup_of([a["Analyst_Name"] for a in analysts_raw], [True] * len(analysts_raw))
    top_e = lookup_of([t["TOP_ID"] for t in tops], [t["Earliest_Cutoff_Hr"] for t in tops])
    msg = {}
    for m in ms_raw:
        k = m["Process_Date"].isoformat() + "|" + (key(m["TOP_ID"]) or "")
        g = msg.setdefault(k, dict(arr=[], Rows=0)); g["Rows"] += 1
        if m["Actual_Arrival_DT"]: g["arr"].append(m["Actual_Arrival_DT"])
    for g in msg.values(): g["MaxArrival"] = max(g["arr"]) if g["arr"] else None
    fw = []
    for idx, r in enumerate(fd, 1):
        B = r["Process_Date"]; E = r["Signoff_Model"]; client = same(E, "Client")
        F, G, H, I = r["Status_Calculated_DT"], r["Status_Controlled_DT"], r["Status_FA_SignedOff_DT"], r["Status_SignedOff_DT"]
        K = r["Rework_Gap_Mins"]; L = r["Maker_Name"]; M = "n/a — no control step" if client else r["Checker_Found"]
        Nn = r["Default_Analyst_Name"]; Rr, S, T = r["Recon_Mins"], r["NAV_Mins"], r["Planned_Tail_Mins"]
        U, V = r["Pricing_Arrival_DT"], r["Client_Cutoff_DT"]
        W = F; X = H if client else G; Y = I
        Z = None if W is None or Rr is None else add_mins(W, -Rr)
        AA = None if U is None or V is None else R0(mins(V, U))
        AB = None if U is None else R0(mins(W, U))
        AC = None if AB is None else max(0, AB)
        AD = R0(mins(X, W))
        AEn = None if client else R0(mins(H, G))
        AE = "n/a" if client else (None if AEn is None else str(int(AEn)))
        AF = R0(mins(Y, H)); AG = R0(mins(H, F)); AH = r["Breach_Mins"]; AI = r["Breached"]; AL = r["TOP_ID"]; AN = r["Fund_Pricing_Cutoff_Hr"]
        AM = None if U is None else ("Yes" if U > at_hr(B, r["Pricing_Late_Hr"]) else "No")
        dk = dkey(B, AL); day = None if dk is None else topdays.get(dk); msd = None if dk is None else msg.get(dk)
        binding = None if day is None else day["Binding_Cutoff_Hr"]
        slot_base = binding if msd is not None and binding is not None else find(top_e, AL)
        AO = None if AL is None else floor_step(slot_base, 0.5)
        late = None if msd is None or binding is None or msd["MaxArrival"] is None else R0(mins(msd["MaxArrival"], at_hr(B, binding)))
        BB = None if AL is None or late is None else ("No" if late > 0 else "Yes")
        AP = None if U is None else R(hr_of_day(U), 4); AQ = None if W is None else R(hr_of_day(W), 4); AR = None if X is None else R(hr_of_day(X), 4)
        AS = None if AN is None or V is None or S is None or T is None else R0(mins(V, at_hr(B, AN)) - S - T)
        AT = None if AN is None or U is None else R0(mins(U, at_hr(B, AN)))
        AU = None if AD is None or S is None else R0(AD - S)
        AV = 0 if AEn is None else AEn
        AW = None if AF is None or T is None else AF - T
        AX = None if any(v is None for v in (AT, AB, AU, AW, AS, AH)) else R0(AT + AB + AU + AV + AW - AS - AH)
        BM = None if AQ is None else (AQ if AP is None else min(AP, AQ))
        done = None
        if W is not None and S is not None:
            bud = add_mins(W, S); done = bud if X is None else min(bud, max(X, W))
        row = dict(r)
        row.update(Row_ID=idx, Processing_Lag_Days=(B - r["NAV_Date"]).days, Checker_Name=M,
                   Reassigned="No" if same(L, Nn) else "Yes", Self_Checked="n/a" if client else ("YES — four-eyes breach" if same(L, M) else "No"),
                   NAV_Start_DT=W, NAV_End_DT=X, Delivered_DT=Y, Implied_Work_Start_DT=Z, Headroom_After_Pricing_Mins=AA,
                   Pricing_To_Calc_Mins=AB, Wait_After_Pricing_Mins=AC, NAV_Span_Mins=AD, Check_Mins=AE, External_Tail_Mins=AF,
                   FA_Total_Mins=AG,
                   Primary_Cause="On time" if AI != "Yes" else ("Wait for analyst" if N(AC) >= max(N(AF), N(K)) else ("External sign-off" if N(AF) >= N(K) else "Rework")),
                   Row_Quality="CHECK" if F is None or Y is None or find(an_set, L) is None else "OK",
                   Pricing_Late_For_This_Fund=AM, Due_Slot_Hr=AO, Arrival_Hr=AP, Start_Hr=AQ, End_Hr=AR, Planned_Buffer_Mins=AS,
                   Var_Pricing_Mins=AT, Var_NAV_Stretch_Mins=AU, Var_Control_Mins=AV, Var_Approval_Mins=AW, Bridge_Check=AX,
                   Bridge_OK="No" if AX is None else ("Yes" if abs(AX) <= 2 else "No"),
                   Breach_Class="n/a" if AI != "Yes" else ("Unknown" if AA is None or S is None or T is None else ("Lost on arrival" if AA < S + T else "Lost after arrival")),
                   TOP_SLA_Met=BB,
                   Possible_Cause="Not breached" if AI != "Yes" else ("Pricing late" if AM == "Yes" else ("Thin custody slack" if r["Custody_Slack_Group"] == "Thin custody slack" else ("Broker-dependent" if r["Broker_Dependent"] == "Yes" else "None of these"))),
                   Fund_Label=r["Fund_ID"] + ("*" if client else ""), Controlled_To_Delivered_Mins=R0(mins(Y, X)),
                   Headroom_At_Delivery_Mins=None if AH is None else -AH, Bar_Offset_Hr=BM,
                   Bar_Wait_Hr=None if BM is None else R(N(AC) / 60, 4), Bar_NAV_Hr=None if BM is None or AD is None else R(AD / 60, 4),
                   Bar_Control_Hr=None if BM is None else R(AV / 60, 4), Bar_Tail_Hr=None if BM is None or AF is None else R(AF / 60, 4),
                   Work_Start_Num=serial(Z) if Z is not None and W is not None else 0, Work_End_Num=serial(W) if W is not None else 0,
                   Control_Start_Hr=None if W is None else R(hrs_from(W, B), 4), Control_End_Hr=None if X is None else R(hrs_from(X, B), 4),
                   Control_Window_Status="Missing Calculated" if W is None else (("Missing FA signed off" if client else "Missing Controlled") if X is None else ("End before start" if X < W else "OK")),
                   InHand_Hr=None if Z is None else R(hrs_from(min(U, Z) if U is not None else Z, B), 4),
                   Work_Start_Hr=None if Z is None else R(hrs_from(Z, B), 4), NAV_Done_Hr=None if done is None else R(hrs_from(done, B), 4),
                   Maker_Key=key(L))
        fw.append(row)
    # queue pass
    grp = {}
    for r in fw: grp.setdefault((r["Maker_Key"], r["Process_Date"]), []).append(r)
    for g in grp.values():
        Ws = [serial(r["NAV_Start_DT"]) for r in g]
        for i, r in enumerate(g):
            AC = r["Wait_After_Pricing_Mins"]; Wi = Ws[i]; Ui = serial(r["Pricing_Arrival_DT"])
            total = 0
            if not (AC is None or AC == 0 or r["Maker_Key"] is None):
                for j, o in enumerate(g):
                    if j == i: continue
                    ov = min(Wi, o["Work_End_Num"]) - max(Ui, o["Work_Start_Num"])
                    total += ov if ov > 0 else 0
            r["Queue_Wait_Mins"] = None if AC is None else (0 if r["Maker_Key"] is None or AC == 0 else min(AC, R0(R(1440 * total, 4))))
            earlier = [] if r["Maker_Key"] is None or Wi is None else [Ws[j] for j in range(len(g)) if j != i and Ws[j] is not None and Ws[j] < Wi]
            r["Maker_Free_From_DT"] = None if not earlier else EPOCH + dt.timedelta(days=max(earlier))
    for r in fw:
        ac = r["Wait_After_Pricing_Mins"]
        r["Own_Recon_Mins"] = None if ac is None else R0(min(ac - r["Queue_Wait_Mins"], N(r["Recon_Mins"])))
        r["Other_Holdup_Mins"] = None if ac is None else ac - r["Queue_Wait_Mins"] - r["Own_Recon_Mins"]
    return dict(Dim_Fund=funds, Dim_TOP=tops, Dim_Team=teams, Dim_Analyst=analysts, Fact_Milestone=fm, Fact_Work=fw)
