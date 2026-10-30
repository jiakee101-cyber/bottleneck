"""Build NAV_Bottleneck_Inputs_v5.xlsx: the v4.5 template cut down to its input columns (no heavy formulas).

Usage: python3 -I build/build_inputs_v5.py <v4.5 template or filled workbook> <out.xlsx>
Power Query (powerquery/*.pq) does every calculation the removed columns used to do.
"""
import sys
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

src, out = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(src)

KEEP = {  # sheet -> number of input columns kept (A..)
    "Constants": 3, "Dim_Team": 5, "Dim_Signoff": 4, "Dim_Fund": 25, "Dim_TOP": 3, "Fact_Milestone": 3,
    "Dim_Analyst": 3, "Status_Log": 6, "Dim_Slot": 1, "Dim_Clock": 2, "Dim_Hour": 3, "Dim_BufferStep": 2,
    "Dim_SupplierType": 2, "Dim_WaitGroup": 2, "Dim_Cause": 2, "Dim_DetailRow": 2,
}
TEXT_COLS = {"Dim_Fund": ["A", "C", "F", "U"], "Dim_TOP": ["A"], "Fact_Milestone": ["B"], "Status_Log": ["C"],
             "Dim_Team": ["A"], "Dim_Analyst": ["B"]}

for name in list(wb.sheetnames):
    if name not in KEEP and name != "README":
        del wb[name]
for name, n in KEEP.items():
    ws = wb[name]
    if ws.max_column > n:
        ws.delete_cols(n + 1, ws.max_column - n)
    # drop pre-filled rows that hold nothing in the input columns
    last = 1
    for r in range(2, ws.max_row + 1):
        if any(ws.cell(r, c).value not in (None, "") for c in range(1, n + 1)):
            last = r
    if ws.max_row > last:
        ws.delete_rows(last + 1, ws.max_row - last)
    for col in TEXT_COLS.get(name, []):
        ws.column_dimensions[col].number_format = "@"
        for r in range(2, ws.max_row + 1):
            c = ws[col + str(r)]
            if c.value is not None and not isinstance(c.value, str):
                c.value = str(c.value)
            c.number_format = "@"

# Constants: the two rows Power BI now works out itself
cons = wb["Constants"]
for r in range(2, cons.max_row + 1):
    label = str(cons.cell(r, 1).value or "")
    if label.startswith("Minutes per weightage unit"):
        cons.cell(r, 2).value = "=B3/B2"
        cons.cell(r, 3).value = "Shown for reference. Power BI works this out from the two rows above."
    if label.startswith("Business days in Fact_Work"):
        cons.cell(r, 2).value = None
        cons.cell(r, 3).value = "Worked out in Power BI from the process dates loaded (no longer needed here)."

# README
rd = wb["README"]
rd.delete_rows(1, rd.max_row)
lines = [
    ("NAV BOTTLENECK — INPUTS WORKBOOK v5", True),
    ("This workbook holds inputs only. Power BI (Power Query) does every calculation the v4.5 formula columns used to do.", False),
    ("", False),
    ("WHAT TO MAINTAIN HERE", True),
    ("Constants — the planning constants (values only).", False),
    ("Dim_Fund — one row per fund, columns A:Y. Fund_ID, Client_ID, Team_ID and TOP_ID are Text: keep them Text so 05035 keeps its zero.", False),
    ("Dim_TOP, Dim_Team, Dim_Analyst, Dim_Signoff — reference lists.", False),
    ("Fact_Milestone — one row per pricing (TOP) delivery: Process_Date, TOP_ID, Actual_Arrival_DT.", False),
    ("Status_Log — only for small tests. With real volumes, put the status log exports (.csv or .xlsx) in a folder and set the", False),
    ("    NAV_StatusLogFolder parameter in Power BI. The Fact_Work sheet is gone: fund-days are built from the status log.", False),
    ("Dim_Slot, Dim_Clock, Dim_Hour and the small Dim_* lists — chart scaffolding, normally left as they are.", False),
    ("", False),
    ("Setup and migration steps: POWER_QUERY_SETUP_v5.md in the project folder.", False),
]
for i, (t, bold) in enumerate(lines, 1):
    c = rd.cell(i, 1, t)
    c.font = Font(bold=bold, size=13 if i == 1 else 11)
rd.column_dimensions["A"].width = 130
wb.active = wb.sheetnames.index("README")
wb.save(out)
print("saved", out, wb.sheetnames)
