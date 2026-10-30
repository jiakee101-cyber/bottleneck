// One row per process date + TOP that has fund-days: how many fund-days ran on that TOP's file and the binding
// (earliest) pricing cut-off among them. Built from the distinct fund-days of the status log. Do not load.
let
    fx = fxNAV,
    Keys = Table.Distinct(Table.SelectColumns(NAV_StatusLog, {"Log_NAV_Date", "Log_Process_Date", "Fund_Key"})),
    Funds = fx[LookupOf](Dim_Fund[Fund_ID], Table.ToRecords(Table.SelectColumns(Dim_Fund, {"TOP_ID", "Pricing_Cutoff_Hr"}))),
    WithFund = Table.AddColumn(Keys, "F", each fx[Find](Funds, [Fund_Key])),
    Keyed = Table.AddColumn(WithFund, "K", each
        if [F] = null or fx[Key]([F][TOP_ID]) = null then null
        else Date.ToText([Log_Process_Date], "yyyy-MM-dd") & "|" & fx[Key]([F][TOP_ID]), type text),
    Grouped = Table.Group(Table.SelectRows(Keyed, each [K] <> null), {"K"}, {
        {"Fund_Days", each Table.RowCount(_), Int64.Type},
        {"Binding_Cutoff_Hr", each
            let p = List.Select(List.Transform([F], (f) => f[Pricing_Cutoff_Hr]), (h) => h <> null and h > 0)
            in if List.IsEmpty(p) then null else List.Min(p), type nullable number}})
in
    Table.Buffer(Grouped)
