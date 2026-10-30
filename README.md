# NAV Bottleneck

## v5 — calculations in Power Query (for full volume, about 5,000 funds a day)

- `POWER_QUERY_SETUP_v5.md` — what changes and the step-by-step setup in Power BI Desktop. Start here.
- `NAV_Bottleneck_Inputs_v5.xlsx` — inputs-only workbook (no heavy formulas).
- `powerquery/` — the 17 Power Query queries, one `.pq` file per query (file name = query name).
- `NAV_Bottleneck_v5_Additions.csx` — Tabular Editor script: calculated columns and the data-check measures that replace the Checks sheet.
- `build/pq_reference.py`, `build/pq_verify.py` — Python mirror of the Power Query logic and the comparison against the v4.5 formulas. `build/build_inputs_v5.py` rebuilds the inputs workbook from a v4.5 workbook.

## v4.5 — Excel template

- `NAV_Bottleneck_Data_Template_v4_5.xlsx` — v4.4 plus the columns the two Power BI pages need (see README sheet, "VERSION 4.5", and the `PBI_Mapping` sheet).
- `NAV_Bottleneck_Measures_v4_5.csx` — Tabular Editor C# script: relationships, sort orders and all DAX measures. Safe to re-run. Still used in v5.
- `build/` — the generator (`build.py` + `measures.py`, single source for columns, DAX and the mapping sheet) and `verify.py` (independent recompute of the new columns).

Rebuild: `python3 build/build.py NAV_Bottleneck_Data_Template_v4_4.xlsx NAV_Bottleneck_Data_Template_v4_5.xlsx NAV_Bottleneck_Measures_v4_5.csx`, then recalculate in Excel.
