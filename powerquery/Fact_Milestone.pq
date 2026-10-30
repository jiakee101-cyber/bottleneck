// Fact_Milestone: one row per TOP delivery (Process_Date, TOP_ID, Actual_Arrival_DT from the sheet); the rest worked out here.
// A missing arrival time is left unscored (in Excel an empty arrival read as 00:00 and scored as on time).
let
    fx = fxNAV,
    TopNames = let t = NAV_Inputs[TOP] in fx[LookupOf](t[TOP_ID], List.Transform(t[TOP_Name], fx[Txt])),
    TopDays = NAV_TopDays,
    Days = Record.FromList(Table.ToRecords(TopDays), TopDays[K]),
    // Breached fund-days per process date + TOP.
    BreachedT = Table.Group(
        Table.AddColumn(Table.SelectRows(Table.SelectColumns(NAV_FundDays, {"Process_Date", "TOP_ID", "Breached"}), each [Breached] = "Yes"),
            "K", each if fx[Key]([TOP_ID]) = null then null else Date.ToText([Process_Date], "yyyy-MM-dd") & "|" & fx[Key]([TOP_ID]), type text),
        {"K"}, {{"N", each Table.RowCount(_), Int64.Type}}),
    Breaches = fx[LookupOf](BreachedT[K], BreachedT[N]),
    Rows = Table.AddColumn(NAV_MilestoneRaw, "C", (r) =>
        let
            K = if fx[Key](r[TOP_ID]) = null then null else Date.ToText(r[Process_Date], "yyyy-MM-dd") & "|" & fx[Key](r[TOP_ID]),
            Day = if K = null then null else Record.FieldOrDefault(Days, K, null),
            E = if Day = null then 0 else Day[Fund_Days],
            F = if Day = null then null else Day[Binding_Cutoff_Hr],
            G = fx[AtHr](r[Process_Date], F),
            H = fx[R0](fx[Mins](r[Actual_Arrival_DT], G)),
            I = if H = null then null else if H <= 0 then "Yes" else "No"
        in
            [
                TOP_Name = fx[Find](TopNames, r[TOP_ID]),
                Funds_In_TOP = E,
                Binding_Cutoff_Hr = F,
                Binding_Cutoff_DT = G,
                Delay_Mins = H,
                SLA_Met = I,
                Fund_Days_Impacted = if I = "No" then E else 0,
                Due_Slot_Hr = fx[Floor](F, 0.5),
                Late_Mins = if H = null then null else List.Max({0, H}),
                Breached_Fund_Days = if F = null then null else (let b = if K = null then null else Record.FieldOrDefault(Breaches, K, null) in if b = null then 0 else b)
            ]),
    Expanded = Table.ExpandRecordColumn(Rows, "C", {"TOP_Name", "Funds_In_TOP", "Binding_Cutoff_Hr", "Binding_Cutoff_DT",
        "Delay_Mins", "SLA_Met", "Fund_Days_Impacted", "Due_Slot_Hr", "Late_Mins", "Breached_Fund_Days"}),
    Ordered = Table.RemoveColumns(Expanded, {"Milestone_Row"}),
    Typed = Table.TransformColumnTypes(Ordered, {{"Process_Date", type date}, {"TOP_ID", type text},
        {"Actual_Arrival_DT", type datetime}, {"TOP_Name", type text}, {"Funds_In_TOP", Int64.Type},
        {"Binding_Cutoff_Hr", type number}, {"Binding_Cutoff_DT", type datetime}, {"Delay_Mins", type number},
        {"SLA_Met", type text}, {"Fund_Days_Impacted", Int64.Type}, {"Due_Slot_Hr", type number},
        {"Late_Mins", type number}, {"Breached_Fund_Days", Int64.Type}})
in
    Typed
