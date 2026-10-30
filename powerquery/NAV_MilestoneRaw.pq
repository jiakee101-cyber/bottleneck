// Pricing (TOP) arrivals as typed in the Fact_Milestone sheet: Process_Date, TOP_ID, Actual_Arrival_DT. Do not load.
let
    fx = fxNAV,
    Raw = fx[Inputs]("Fact_Milestone", {"Process_Date", "TOP_ID", "Actual_Arrival_DT"}),
    Typed = Table.FromRecords(
        List.Transform(Table.ToRecords(Raw), each [
            Process_Date = fx[ToDate]([Process_Date]),
            TOP_ID = fx[Txt]([TOP_ID]),
            Actual_Arrival_DT = fx[ToDateTime]([Actual_Arrival_DT])
        ]),
        type table [Process_Date = nullable date, TOP_ID = nullable text, Actual_Arrival_DT = nullable datetime]),
    FromDate = if fx[IsBlank](NAV_LoadFromDate) then null else Date.FromText(Text.Trim(NAV_LoadFromDate), [Format = "yyyy-MM-dd"]),
    Kept = Table.SelectRows(Typed, each [Process_Date] <> null and (FromDate = null or [Process_Date] >= FromDate)),
    Indexed = Table.AddIndexColumn(Kept, "Milestone_Row", 1, 1, Int64.Type)
in
    Indexed
