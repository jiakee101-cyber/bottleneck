# NAV Bottleneck — template v4.5

- `NAV_Bottleneck_Data_Template_v4_5.xlsx` — v4.4 plus the columns the two Power BI pages need (see README sheet, "VERSION 4.5", and the `PBI_Mapping` sheet).
- `NAV_Bottleneck_Measures_v4_5.csx` — Tabular Editor C# script: relationships, sort orders and all 56 DAX measures. Safe to re-run.
- `build/` — the generator (`build.py` + `measures.py`, single source for columns, DAX and the mapping sheet) and `verify.py` (independent recompute of the new columns).

Rebuild: `python3 build/build.py NAV_Bottleneck_Data_Template_v4_4.xlsx NAV_Bottleneck_Data_Template_v4_5.xlsx NAV_Bottleneck_Measures_v4_5.csx`, then recalculate in Excel.
