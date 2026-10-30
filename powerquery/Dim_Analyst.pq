// Dim_Analyst: Analyst_Name, Team_ID, Active from the sheet; team lookups worked out here.
// The per-day workload columns (Planned_Maker_Mins_PerDay ... Capacity_Flag) are DAX calculated columns (v5 script).
let
    fx = fxNAV,
    Raw = NAV_Inputs[Analyst],
    Teams = Table.Buffer(Dim_Team),
    TeamRec = fx[LookupOf](Teams[Team_ID], Table.ToRecords(Teams)),
    Books = Table.Group(
        Table.AddColumn(Table.SelectColumns(Dim_Fund, {"Default_Analyst_Name"}), "K", each fx[Key]([Default_Analyst_Name]), type text),
        {"K"}, {{"N", each Table.RowCount(_), Int64.Type}}),
    BookRec = fx[LookupOf](Books[K], Books[N]),
    Rows = Table.AddColumn(Raw, "C", (r) =>
        let
            T = fx[Find](TeamRec, r[Team_ID]),
            Book = fx[Find](BookRec, r[Analyst_Name])
        in
            [
                Team_Name = if T = null then "external" else T[Team_Name],
                Shift_Start_Hr = if T = null then null else T[Shift_Start_Hr],
                Capacity_Mins = if T = null then 0 else (if T[Daily_Capacity_Mins] = null then 0 else T[Daily_Capacity_Mins]),
                Funds_In_Default_Book = if Book = null then 0 else Book,
                Shift_End_Hr = if T = null then null else T[Shift_End_Hr]
            ]),
    Expanded = Table.ExpandRecordColumn(Rows, "C", {"Team_Name", "Shift_Start_Hr", "Capacity_Mins", "Funds_In_Default_Book", "Shift_End_Hr"}),
    Cleaned = Table.TransformColumns(Expanded, {{"Analyst_Name", fx[Txt]}, {"Team_ID", fx[Txt]}, {"Active", fx[Txt]}}),
    Unique = Table.Distinct(Table.Buffer(Cleaned), {"Analyst_Name"}),
    Typed = Table.TransformColumnTypes(Unique, {{"Analyst_Name", type text}, {"Team_ID", type text}, {"Active", type text},
        {"Team_Name", type text}, {"Shift_Start_Hr", type number}, {"Capacity_Mins", type number},
        {"Funds_In_Default_Book", Int64.Type}, {"Shift_End_Hr", type number}})
in
    Typed
