// One row per fund-day (NAV date + process date + fund) found in the status log, with the status times,
// the fund attributes and the pricing arrival. Staging query shared by Fact_Work and Fact_Milestone: do not load.
// This replaces the COUNTIFS / MINIFS / MAXIFS that each Fact_Work row ran against the whole Status_Log.
let
    fx = fxNAV,
    sCalc = "changed to the status of calculated",
    sCtrl = "changed to the status of controlled",
    sFA = "changed to the status of fund accounting signed off",
    sSO = "changed to the status of signed off",
    Serial6 = (x as nullable datetime) as nullable number =>
        if x = null then null else Number.Round(Number.From(x), 6, RoundingMode.AwayFromZero),
    // Person on the first log row of this status at its latest time (the Excel INDEX/MATCH on Key_Time).
    PersonAt = (rows as table, ts as nullable datetime) as nullable text =>
        if ts = null then null
        else
            let
                Hit = Table.SelectRows(rows, each Serial6([Log_Timestamp]) = Serial6(ts))
            in
                if Table.IsEmpty(Hit) then null else Table.Min(Hit, "Log_Row")[Log_Person_Name],
    Summarise = (g as table) as record =>
        let
            Calc = Table.SelectRows(g, each [Status_Key] = sCalc),
            Ctrl = Table.SelectRows(g, each [Status_Key] = sCtrl),
            CalcTs = List.RemoveNulls(Calc[Log_Timestamp]),
            CalcMin = List.Min(CalcTs),
            CalcMax = List.Max(CalcTs),
            CtrlMax = List.Max(List.RemoveNulls(Ctrl[Log_Timestamp])),
            Recalcs = Table.RowCount(Calc)
        in
            [
                Fund_ID = Table.Min(g, "Log_Row")[Log_Fund_ID],
                Status_Calculated_DT = CalcMin,
                Status_Controlled_DT = CtrlMax,
                Status_FA_SignedOff_DT = List.Max(List.RemoveNulls(Table.SelectRows(g, each [Status_Key] = sFA)[Log_Timestamp])),
                Status_SignedOff_DT = List.Max(List.RemoveNulls(Table.SelectRows(g, each [Status_Key] = sSO)[Log_Timestamp])),
                Recalc_Count = Recalcs,
                Rework_Gap_Mins = if Recalcs <= 1 then 0 else fx[R0](fx[Mins](CalcMax, CalcMin)),
                Maker_Name = PersonAt(Calc, CalcMax),
                Checker_Found = PersonAt(Ctrl, CtrlMax)
            ],
    Grouped = Table.Group(NAV_StatusLog, {"Log_NAV_Date", "Log_Process_Date", "Fund_Key"}, {{"S", Summarise, type record}}),
    Expanded = Table.ExpandRecordColumn(Grouped, "S", {"Fund_ID", "Status_Calculated_DT", "Status_Controlled_DT",
        "Status_FA_SignedOff_DT", "Status_SignedOff_DT", "Recalc_Count", "Rework_Gap_Mins", "Maker_Name", "Checker_Found"}),
    Renamed = Table.RenameColumns(Expanded, {{"Log_NAV_Date", "NAV_Date"}, {"Log_Process_Date", "Process_Date"}}),
    Sorted = Table.Sort(Renamed, {{"Process_Date", Order.Ascending}, {"NAV_Date", Order.Ascending}, {"Fund_Key", Order.Ascending}}),
    Funds = fx[LookupOf](Dim_Fund[Fund_ID], Table.ToRecords(Dim_Fund)),
    // Latest pricing arrival per process date + TOP (MAXIFS on Fact_Milestone).
    Ms = Table.Group(
        Table.AddColumn(NAV_MilestoneRaw, "K", each Date.ToText([Process_Date], "yyyy-MM-dd") & "|" & (if fx[Key]([TOP_ID]) = null then "" else fx[Key]([TOP_ID])), type text),
        {"K"}, {{"Arrival", each List.Max(List.RemoveNulls([Actual_Arrival_DT])), type nullable datetime}}),
    Arrivals = Record.FromList(Ms[Arrival], Ms[K]),
    WithDims = Table.AddColumn(Sorted, "D", (r) =>
        let
            F = fx[Find](Funds, r[Fund_ID]),
            Get = (name as text) as any => if F = null then null else Record.Field(F, name),
            Top = Get("TOP_ID"),
            ClientHr = Get("Client_Cutoff_Hr"),
            PriceHr = Get("Pricing_Cutoff_Hr"),
            ArrKey = if fx[Key](Top) = null then null else Date.ToText(r[Process_Date], "yyyy-MM-dd") & "|" & fx[Key](Top),
            U = if ArrKey = null then null else Record.FieldOrDefault(Arrivals, ArrKey, null),
            V = if ClientHr <> null and ClientHr > 0 then fx[AtHr](r[Process_Date], ClientHr) else null,
            Y = r[Status_SignedOff_DT],
            AH = fx[R0](fx[Mins](Y, V))
        in
            [
                Signoff_Model = Get("Signoff_Model"),
                Default_Analyst_Name = Get("Default_Analyst_Name"),
                Required_Mins = Get("Required_Mins"),
                Recon_Mins = Get("Recon_Mins"),
                NAV_Mins = Get("NAV_Mins"),
                Planned_Tail_Mins = Get("Planned_Tail_Mins"),
                Pricing_Arrival_DT = U,
                Client_Cutoff_DT = V,
                Breach_Mins = AH,
                Breached = if AH = null then null else if AH > 0 then "Yes" else "No",
                TOP_ID = Top,
                Fund_Pricing_Cutoff_Hr = PriceHr,
                Pricing_Late_Hr = if PriceHr = null then 0 else PriceHr,
                Client_Name = Get("Client_Name"),
                Broker_Dependent = Get("Broker_Dependent"),
                Custody_Slack_Group = Get("Custody_Slack_Group"),
                Client_Cutoff_Hr = if ClientHr <> null and ClientHr > 0 then ClientHr else null
            ]),
    Result = Table.ExpandRecordColumn(WithDims, "D", {"Signoff_Model", "Default_Analyst_Name", "Required_Mins", "Recon_Mins",
        "NAV_Mins", "Planned_Tail_Mins", "Pricing_Arrival_DT", "Client_Cutoff_DT", "Breach_Mins", "Breached", "TOP_ID",
        "Fund_Pricing_Cutoff_Hr", "Pricing_Late_Hr", "Client_Name", "Broker_Dependent", "Custody_Slack_Group", "Client_Cutoff_Hr"})
in
    Result
