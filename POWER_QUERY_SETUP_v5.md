# NAV Bottleneck v5 — moving the calculations from Excel to Power Query

The v4.5 workbook did every calculation with Excel formulas. Fact_Work alone searched the whole status log about
40 times per row. At about 5,000 funds a day that is too much for Excel, and a month of status log (about 500,000
rows) is already half of Excel's row limit.

In v5 the workbook holds **inputs only**, and Power BI (Power Query) does the calculations once per refresh.
The tables loaded into the model keep the **same names and the same columns**. The 70 report measures, the
relationships and every visual stay as they are.

```
 Inputs workbook (no heavy formulas)         Status log exports (folder of .csv / .xlsx)
 Constants, Dim_Fund A:Y, Dim_TOP A:C,                       │
 Dim_Team, Dim_Analyst, Fact_Milestone A:C                   │
              │                                              │
              └──────────────► Power Query ◄─────────────────┘
                     builds Dim_Fund, Dim_TOP, Dim_Team, Dim_Analyst, Dim_Slot,
                     Fact_Milestone and Fact_Work (same columns as v4.5)
                                   │
                                   ▼
                     Power BI model: existing measures and visuals
```

## What you get

| File | What it is |
|---|---|
| `NAV_Bottleneck_Inputs_v5.xlsx` | The v4.5 template cut down to its input columns. No Fact_Work sheet, no Checks sheet, no staging sheets. ID columns are pre-formatted as Text. |
| `powerquery/*.pq` | 17 Power Query queries, one file each. The file name is the query name. |
| `NAV_Bottleneck_v5_Additions.csx` | Tabular Editor script: 18 calculated columns (the few v4.5 columns that summarise Fact_Work for a small table) and 29 data-check measures that replace the Checks sheet. |
| `NAV_Bottleneck_Measures_v4_5.csx` | Unchanged. Do not run it again unless you rebuild the model. |

## Before you start

1. **Save a copy of your .pbix.** You will replace the code of seven queries.
2. Have Tabular Editor ready (the same one you used for the v4.5 script).
3. In Power BI Desktop: **File → Options and settings → Options → Current file → Privacy** → choose
   **Ignore the Privacy levels and potentially improve performance**. Without this, Power BI may refuse to combine
   the status log folder with the workbook ("Formula.Firewall"), and refreshes run slower.

## Step 1 — Prepare the inputs

**Option A (recommended): start from `NAV_Bottleneck_Inputs_v5.xlsx`.** Paste your data over the sample rows, sheet
by sheet. Paste values only (Paste Special → Values) so the ID columns stay Text.

**Option B: strip your existing v4.5 workbook.** Power Query reads only the input columns, so it also works on your
current workbook. Excel stays slow until you remove the formulas, though:

| Sheet | Keep | Delete |
|---|---|---|
| Dim_Fund | A:Y | Z:BK |
| Dim_TOP | A:C | D:O |
| Fact_Milestone | A:C | D:M |
| Dim_Analyst | A:C | D:Q |
| Dim_Team | A:E | F:G (optional) |
| Status_Log | A:F | G:J |
| Dim_Slot | A | B:H |
| Fact_Work, Checks, Dim_Fund_Staging, Raw_Fund_Import, Mapping, PBI_Mapping | — | whole sheet |

Keep the header row and the sheet names exactly as they are. Power Query finds the columns by header name.

**Status log at full volume: use a folder.** Put the status log exports in one folder, one file per day or per month,
as `.csv` or `.xlsx`. Each file needs this header row (any column order; extra columns are ignored):

`Log_NAV_Date, Log_Process_Date, Log_Fund_ID, Log_Status, Log_Timestamp, Log_Person_Name`

- In a `.xlsx` file, the sheet named `Status_Log` is used, or the first sheet if there is none with that name.
- In a `.csv` file, write dates as `yyyy-mm-dd` and timestamps as `yyyy-mm-dd hh:mm:ss`. Other formats are read using
  your Windows regional settings, and day/month can swap.
- CSV refreshes noticeably faster than XLSX at this volume.

For a small test you can leave the log in the workbook's `Status_Log` sheet and leave the folder parameter empty.

You no longer type fund-days anywhere: **Fact_Work is built from the status log**, one row for every NAV date +
process date + fund that appears in it.

## Step 2 — Add the new queries

Open **Transform data**. For each query below: **Home → New Source → Blank Query**, then **Advanced Editor**,
select everything, paste the contents of the `.pq` file, click **Done**, and rename the query to the file name
(exactly, including capitals). For the "Load = No" queries, right-click the query and **untick Enable load**.

Create them in this order (each one uses the ones above it):

| # | Query (file) | Load | What it does |
|---|---|---|---|
| 1 | `NAV_InputWorkbook` | parameter | Full path of the inputs workbook. Edit the path in the text before you click Done. |
| 2 | `NAV_StatusLogFolder` | parameter | Folder with the status log exports. Leave `""` to read the Status_Log sheet instead. |
| 3 | `NAV_LoadFromDate` | parameter | First process date to load, `"yyyy-mm-dd"`. Leave `""` to load everything. |
| 4 | `fxNAV` | No | Shared helper functions. |
| 5 | `NAV_Config` | No | The Constants sheet. |
| 6 | `NAV_Inputs` | No | The input sheets. |
| 7 | `NAV_StatusLog` | No | The status log (folder or sheet). |
| 8 | `NAV_MilestoneRaw` | No | Pricing arrivals. |

Pasting a parameter's text into a Blank Query turns it into a parameter automatically. You can change its value
later in **Home → Manage Parameters**.

## Step 3 — Replace the code of the existing tables

For each of these existing queries: select it, open **Advanced Editor**, select everything, and paste the `.pq` file
of the same name. Replacing the code (rather than deleting the query) keeps the table, its measures and its
relationships.

Do them in this order: `Dim_Team`, `Dim_Fund`, `Dim_TOP`, `Dim_Analyst`, `Dim_Slot`.

Then create two more staging queries (Blank Query, untick Enable load): `NAV_FundDays`, then `NAV_TopDays`.

Then replace `Fact_Milestone`, then `Fact_Work`.

**Delete** the old queries that read sheets which no longer exist or are no longer needed: `Status_Log`, and if you
loaded them, `Checks`, `Dim_Fund_Staging`, `Raw_Fund_Import`, `Mapping`. Leave the small chart tables
(`Dim_Hour`, `Dim_Clock`, `Dim_SupplierType`, `Dim_WaitGroup`, `Dim_Cause`, `Dim_DetailRow`, `Dim_BufferStep`,
`Dim_Signoff`) as they are.

If you switched to the new inputs workbook, point those small tables at it too:
**Home → Data source settings → select the old workbook → Change Source**.

## Step 4 — Load

**Close & Apply.** The first refresh reads the whole status log. Expect a few minutes for a month at full volume.

If a query shows an error, the message names the sheet, the column or the Constants row it could not find.

## Step 5 — Run the v5 script

In Tabular Editor (connected to the open .pbix), open the C# Script tab, paste `NAV_Bottleneck_v5_Additions.csx`,
run it (F5), and save (Ctrl+S). Back in Power BI, refresh once more.

It adds:

- **Calculated columns** (display folder "Calculated (v5)"): `Dim_TOP` TOP_Days_Scored, TOP_Days_Late,
  Late_Hours_Total, Breached_Fund_Days_When_Late; `Dim_Fund` Runs_Observed, NAV_Frequency_Observed; `Dim_Analyst`
  workload per day (Planned/Actual maker minutes, utilisation, checks, Capacity_Flag); `Dim_Slot` Fund_Days_Due,
  averages and Peak_Flag. None of the report visuals use them; they keep the v4.5 columns available.
- **29 data checks** (measure folder "9 Data Checks", names starting `Chk`). Put them in a table visual on a hidden
  page: this replaces the Checks sheet. Unlike the sheet, they respond to the report's slicers.

If the script says a column was skipped because "a loaded column still has this name", refresh the model and run it
again.

## Step 6 — Check the numbers against v4.5

For one month you already have in v4.5, compare: Fund-Days, Breached Fund-Days, TOP Late Rate, Queue Share of Wait,
and the Team load chart for one date. They should match, apart from the intended differences below.

## Intended differences from v4.5

| Area | v4.5 (Excel) | v5 (Power Query) |
|---|---|---|
| Fund-days | Typed into the Fact_Work sheet | One row per NAV date + process date + fund found in the status log |
| Pricing arrival left empty | Read as 00:00 and scored as on time | Left unscored (no SLA result, no late minutes) |
| A formula error (#VALUE!, #N/A) | Shown as an error | Blank |
| IDs and status text | Matched ignoring case | Same, and surrounding spaces are ignored too |
| Duplicate Fund_ID in Dim_Fund | VLOOKUP used the first row | Same: only the first row is kept |
| Checks | Whole workbook | Respond to the report filters |

## Keeping refreshes fast

- Set `NAV_LoadFromDate` to the start of the period you analyse (for example the last three months). Every refresh
  re-reads every file it loads.
- Move months you no longer analyse out of the status log folder.
- Prefer CSV exports to XLSX.
- **File → Options → Global → Data Load**: raise *Maximum memory used per simultaneous evaluation* if your PC has
  the memory, and untick *Allow data preview to download in the background*.
- When the Arcturus feed is ready, `NAV_StatusLog` and `NAV_MilestoneRaw` are the only queries that need a new
  source. Everything downstream stays the same.

## How this was checked

`build/pq_reference.py` repeats the Power Query logic step for step in Python. `build/pq_verify.py` compares it with
the v4.5 formulas recalculated on a test workbook (40 funds, 4 days, 672 status rows, with recalculations, missing
statuses, client sign-off funds, an unknown fund, a mixed-case status and IDs such as `05035B`). All 13,900 compared
cells match. The `.pq` files pass the Power Query parser. The Power Query code itself could not be run here, because
Power Query only runs inside Power BI and Excel, so expect to fix the odd typo on first refresh. The error message
names the query and the step.
