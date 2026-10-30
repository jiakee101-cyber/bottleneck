// Dim_TOP: TOP_ID, TOP_Name, Pricing_Supplier from the sheet; fund counts and cut-offs from Dim_Fund.
// TOP_Days_Scored, TOP_Days_Late, Late_Hours_Total and Breached_Fund_Days_When_Late are DAX calculated columns (v5 script).
let
    fx = fxNAV,
    Raw = NAV_Inputs[TOP],
    Funds = Table.Buffer(Table.SelectColumns(Dim_Fund, {"TOP_ID", "Pricing_Cutoff_Hr", "Client_First_In_TOP"})),
    FundCount = Table.RowCount(Funds),
    ByTop = Table.Group(
        Table.AddColumn(Funds, "K", each fx.Key([TOP_ID]), type text),
        {"K"},
        {
            {"Funds", each Table.RowCount(_), Int64.Type},
            {"Earliest", each let p = List.Select([Pricing_Cutoff_Hr], (h) => h <> null and h > 0) in if List.IsEmpty(p) then 0 else List.Min(p), type number},
            {"Latest", each let p = List.Select([Pricing_Cutoff_Hr], (h) => h <> null and h > 0) in if List.IsEmpty(p) then 0 else List.Max(p), type number},
            {"Clients", each List.Sum([Client_First_In_TOP]), Int64.Type}
        }),
    Stats = fx.LookupOf(ByTop[K], Table.ToRecords(ByTop)),
    Rows = Table.AddColumn(Raw, "C", (r) =>
        let
            S = fx.Find(Stats, r[TOP_ID]),
            D = if S = null then 0 else S[Funds],
            E = if D = 0 then null else S[Earliest],
            F = if D = 0 then null else S[Latest]
        in
            [
                Funds_In_TOP = D,
                Earliest_Cutoff_Hr = E,
                Latest_Cutoff_Hr = F,
                Cutoff_Spread_Mins = if D = 0 then null else fx.R0((F - E) * 60),
                Binding_Cutoff_Hr = E,
                Blast_Radius_Flag = if D >= 4 then "HIGH — " & Text.From(D) & " funds share this feed"
                    else if D >= 2 then "Medium — " & Text.From(D) & " funds" else "Single fund",
                Clients_In_TOP = if S = null then 0 else S[Clients],
                Share_Of_Funds = if FundCount = 0 then null else D / FundCount
            ]),
    Expanded = Table.ExpandRecordColumn(Rows, "C", {"Funds_In_TOP", "Earliest_Cutoff_Hr", "Latest_Cutoff_Hr",
        "Cutoff_Spread_Mins", "Binding_Cutoff_Hr", "Blast_Radius_Flag", "Clients_In_TOP", "Share_Of_Funds"}),
    Cleaned = Table.TransformColumns(Expanded, {{"TOP_ID", fx.Txt}, {"TOP_Name", fx.Txt}, {"Pricing_Supplier", fx.Txt}}),
    Unique = Table.Distinct(Table.Buffer(Cleaned), {"TOP_ID"}),
    Typed = Table.TransformColumnTypes(Unique, {{"TOP_ID", type text}, {"TOP_Name", type text}, {"Pricing_Supplier", type text},
        {"Funds_In_TOP", Int64.Type}, {"Earliest_Cutoff_Hr", type number}, {"Latest_Cutoff_Hr", type number},
        {"Cutoff_Spread_Mins", type number}, {"Binding_Cutoff_Hr", type number}, {"Blast_Radius_Flag", type text},
        {"Clients_In_TOP", Int64.Type}, {"Share_Of_Funds", type number}})
in
    Typed
