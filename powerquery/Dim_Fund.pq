// Dim_Fund: input columns A:Y from the sheet; every v4.5 formula column worked out here.
// Runs_Observed and NAV_Frequency_Observed need the fund-days, so they are DAX calculated columns (v5 script).
let
    fx = fxNAV,
    Cfg = NAV_Config,
    InputCols = {"Fund_ID", "Fund_Name", "Client_ID", "Client_Name", "Strategic_Client", "Team_ID", "Default_Analyst_Name",
        "Weightage", "ETD", "OTC_nonCFD", "OTC_CFD", "PFC", "EUC", "Has_Custody_Process", "Has_TA_Process",
        "Has_Broker_Process", "Custody_Cutoff", "TA_Cutoff", "Broker_ETA", "Pricing_Cutoff", "TOP_ID", "Client_Cutoff",
        "NAV_Deadline", "Signoff_Model", "Cutoff_Data_Quality"},
    Raw = NAV_Inputs[Fund],
    Indexed = Table.AddIndexColumn(Raw, "Sheet_Row", 1, 1, Int64.Type),
    // One row per Fund_ID (the first one, as VLOOKUP would find it).
    WithKey = Table.AddColumn(Indexed, "Fund_Key", each fx.Key([Fund_ID]), type text),
    Unique = Table.Distinct(Table.Buffer(WithKey), {"Fund_Key"}),
    Teams = Table.Buffer(Dim_Team),
    TeamStart = fx.LookupOf(Teams[Team_ID], Teams[Shift_Start_Hr]),
    Signoff = Table.Buffer(NAV_Inputs[Signoff]),
    SignoffTail = fx.LookupOf(Signoff[Signoff_Model], List.Transform(Signoff[Planned_Tail_Mins], fx.Num)),
    TopIds = List.Buffer(List.Transform(NAV_Inputs[TOP][TOP_ID], fx.Key)),
    // Step 1: per-row columns Z:AW plus the hours needed below.
    Step1 = Table.AddColumn(Unique, "C1", (r) =>
        let
            ReconPct = Cfg[Base_Recon_Pct] + fx.N(r[ETD]) * Cfg[ETD_Adj] + fx.N(r[OTC_nonCFD]) * Cfg[OTC_nonCFD_Adj]
                + fx.N(r[OTC_CFD]) * Cfg[OTC_CFD_Adj] + fx.N(r[PFC]) * Cfg[PFC_Adj] + fx.N(r[EUC]) * Cfg[EUC_Adj],
            NavPct = 100 - ReconPct,
            Required = fx.R(fx.N(r[Weightage]) * Cfg[Mins_Per_Weightage], 1),
            ReconM = fx.R(Required * ReconPct / 100, 1),
            NavM = fx.R(Required * NavPct / 100, 1),
            CustHr = fx.Hr(r[Custody_Cutoff]), TAHr = fx.Hr(r[TA_Cutoff]), BrokerHr = fx.Hr(r[Broker_ETA]),
            PriceHr = fx.Hr(r[Pricing_Cutoff]), ClientHr = fx.Hr(r[Client_Cutoff]), DeadlineHr = fx.Hr(r[NAV_Deadline]),
            ShiftHr = fx.Find(TeamStart, r[Team_ID]),
            Tail = fx.Find(SignoffTail, r[Signoff_Model]),
            NoCust = fx.IsNo(r[Has_Custody_Process]), NoTA = fx.IsNo(r[Has_TA_Process]), NoBroker = fx.IsNo(r[Has_Broker_Process]),
            SlackCust = if NoCust then null else fx.R0((PriceHr - CustHr) * 60),
            SlackTA = if NoTA then null else fx.R0((PriceHr - TAHr) * 60),
            SlackBroker = if NoBroker then null else fx.R0((PriceHr - BrokerHr) * 60),
            AvailRecon = if ShiftHr = null then null else fx.R0((PriceHr - ShiftHr) * 60),
            AvailNav = fx.R0((ClientHr - PriceHr) * 60),
            ReconOK = if AvailRecon = null then null else if AvailRecon >= ReconM then "Yes" else "No",
            NavOK = if Tail = null then null else if AvailNav >= NavM + Tail then "Yes" else "No",
            ThinCust = if NoCust then "n/a" else if SlackCust <= Cfg[Thin_Slack_Mins] then "Yes" else "No"
        in
            [
                Recon_Pct = ReconPct, NAV_Pct = NavPct, Required_Mins = Required, Recon_Mins = ReconM, NAV_Mins = NavM,
                Custody_Cutoff_Hr = CustHr, TA_Cutoff_Hr = TAHr, Broker_ETA_Hr = BrokerHr, Pricing_Cutoff_Hr = PriceHr,
                Client_Cutoff_Hr = ClientHr, NAV_Deadline_Hr = DeadlineHr, Shift_Start_Hr = ShiftHr, Planned_Tail_Mins = Tail,
                Slack_Custody_Mins = if NoCust then "n/a" else Text.From(SlackCust),
                Slack_TA_Mins = if NoTA then "n/a" else Text.From(SlackTA),
                Slack_Broker_Mins = if NoBroker then "n/a" else Text.From(SlackBroker),
                Avail_Recon_Mins = AvailRecon, Avail_NAV_Mins = AvailNav,
                Recon_Feasible = ReconOK, NAV_Feasible = NavOK,
                Feasibility_Flag = if ReconOK = null or NavOK = null then null
                    else if ReconOK = "Yes" and NavOK = "Yes" then "OK" else "REVIEW",
                Broker_Watchlist = if NoBroker then "Not applicable"
                    else if SlackBroker < Cfg[Broker_Watchlist_Mins] then "CAPTURE" else "Not needed",
                Slack_Broker_Value = SlackBroker,
                Client_Tier = if fx.IsYes(r[Strategic_Client]) then "Strategic" else "Non-strategic",
                Broker_Dependent = if fx.IsYes(r[Has_Broker_Process]) then "Yes" else "No",
                Thin_Custody_Slack = ThinCust,
                Thin_TA_Slack = if NoTA then "n/a" else if SlackTA <= Cfg[Thin_Slack_Mins] then "Yes" else "No",
                Thin_Broker_Slack = if NoBroker then "n/a" else if SlackBroker <= Cfg[Thin_Slack_Mins] then "Yes" else "No",
                Custody_Slack_Group = if NoCust then "No custody process"
                    else if ThinCust = "Yes" then "Thin custody slack" else "Ample custody slack",
                Slack_Custody_Num = SlackCust, Slack_TA_Num = SlackTA, Slack_Broker_Num = SlackBroker
            ]),
    C1Fields = {"Recon_Pct", "NAV_Pct", "Required_Mins", "Recon_Mins", "NAV_Mins", "Custody_Cutoff_Hr", "TA_Cutoff_Hr",
        "Broker_ETA_Hr", "Pricing_Cutoff_Hr", "Client_Cutoff_Hr", "NAV_Deadline_Hr", "Shift_Start_Hr", "Planned_Tail_Mins",
        "Slack_Custody_Mins", "Slack_TA_Mins", "Slack_Broker_Mins", "Avail_Recon_Mins", "Avail_NAV_Mins", "Recon_Feasible",
        "NAV_Feasible", "Feasibility_Flag", "Broker_Watchlist", "Slack_Broker_Value", "Client_Tier", "Broker_Dependent",
        "Thin_Custody_Slack", "Thin_TA_Slack", "Thin_Broker_Slack", "Custody_Slack_Group", "Slack_Custody_Num",
        "Slack_TA_Num", "Slack_Broker_Num"},
    Expanded1 = Table.ExpandRecordColumn(Step1, "C1", C1Fields),
    Buffered = Table.Buffer(Expanded1),
    // Step 2: columns that compare a fund with the other funds.
    BrokerSlacks = List.Buffer(List.Sort(List.RemoveNulls(Buffered[Slack_Broker_Value]))),
    TopKeys = List.Buffer(List.Transform(Buffered[TOP_ID], fx.Key)),
    PriceHrs = List.Buffer(Buffered[Pricing_Cutoff_Hr]),
    // Earliest pricing cut-off (> 0) among the funds of each TOP; 0 when none is above zero.
    TopEarliest = let
            Pairs = Table.FromColumns({TopKeys, PriceHrs}, {"K", "H"}),
            Grouped = Table.Group(Table.SelectRows(Pairs, each [K] <> null), {"K"},
                {{"E", each let p = List.Select([H], (h) => h > 0) in if List.IsEmpty(p) then 0 else List.Min(p), type number}})
        in
            Record.FromList(Grouped[E], Grouped[K]),
    // First row of each TOP + client pair, in sheet order.
    FirstPair = let
            Pairs = Table.AddColumn(Table.SelectColumns(Buffered, {"Sheet_Row", "TOP_ID", "Client_ID"}), "P",
                each if fx.Key([TOP_ID]) = null then null else fx.Key([TOP_ID]) & "|" & (if fx.Key([Client_ID]) = null then "" else fx.Key([Client_ID]))),
            Grouped = Table.Group(Table.SelectRows(Pairs, each [P] <> null), {"P"}, {{"First", each List.Min([Sheet_Row]), Int64.Type}})
        in
            fx.LookupOf(List.Transform(Grouped[First], Text.From), List.Repeat({true}, Table.RowCount(Grouped))),
    Step2 = Table.AddColumn(Buffered, "C2", (r) =>
        let
            TopKey = fx.Key(r[TOP_ID]),
            Binding = if TopKey = null or not List.Contains(TopIds, TopKey) then null else Record.FieldOrDefault(TopEarliest, TopKey, null),
            Vs = if Binding = null then null else fx.R0((r[Pricing_Cutoff_Hr] - Binding) * 60)
        in
            [
                Broker_Slack_Rank = if fx.IsNo(r[Has_Broker_Process]) then "n/a"
                    else Text.From(List.Count(List.Select(BrokerSlacks, each _ < r[Slack_Broker_Value])) + 1),
                TOP_Binding_Cutoff_Hr = Binding,
                Cutoff_Vs_TOP_Mins = Vs,
                TOP_Cutoff_Risk = if Vs = null then null else if Vs <= 0 then "Sets the deadline" else "Later than peers by " & Text.From(Vs) & " min",
                Client_First_In_TOP = if TopKey = null then 0 else if Record.HasFields(FirstPair, Text.From(r[Sheet_Row])) then 1 else 0
            ]),
    Expanded2 = Table.ExpandRecordColumn(Step2, "C2",
        {"Broker_Slack_Rank", "TOP_Binding_Cutoff_Hr", "Cutoff_Vs_TOP_Mins", "TOP_Cutoff_Risk", "Client_First_In_TOP"}),
    Cleaned = Table.TransformColumns(Expanded2, {
        {"Fund_ID", fx.Txt}, {"Fund_Name", fx.Txt}, {"Client_ID", fx.Txt}, {"Client_Name", fx.Txt},
        {"Strategic_Client", fx.Txt}, {"Team_ID", fx.Txt}, {"Default_Analyst_Name", fx.Txt}, {"Weightage", fx.Num},
        {"ETD", fx.Num}, {"OTC_nonCFD", fx.Num}, {"OTC_CFD", fx.Num}, {"PFC", fx.Num}, {"EUC", fx.Num},
        {"Has_Custody_Process", fx.Txt}, {"Has_TA_Process", fx.Txt}, {"Has_Broker_Process", fx.Txt},
        {"Custody_Cutoff", fx.ToTime}, {"TA_Cutoff", fx.ToTime}, {"Broker_ETA", fx.ToTime}, {"Pricing_Cutoff", fx.ToTime},
        {"TOP_ID", fx.Txt}, {"Client_Cutoff", fx.ToTime}, {"NAV_Deadline", fx.ToTime}, {"Signoff_Model", fx.Txt},
        {"Cutoff_Data_Quality", fx.Txt}}),
    Ordered = Table.SelectColumns(Cleaned, InputCols & {"Recon_Pct", "NAV_Pct", "Required_Mins", "Recon_Mins", "NAV_Mins",
        "Custody_Cutoff_Hr", "TA_Cutoff_Hr", "Broker_ETA_Hr", "Pricing_Cutoff_Hr", "Client_Cutoff_Hr", "NAV_Deadline_Hr",
        "Shift_Start_Hr", "Planned_Tail_Mins", "Slack_Custody_Mins", "Slack_TA_Mins", "Slack_Broker_Mins",
        "Avail_Recon_Mins", "Avail_NAV_Mins", "Recon_Feasible", "NAV_Feasible", "Feasibility_Flag", "Broker_Watchlist",
        "Broker_Slack_Rank", "Client_Tier", "TOP_Binding_Cutoff_Hr", "Cutoff_Vs_TOP_Mins", "TOP_Cutoff_Risk",
        "Client_First_In_TOP", "Broker_Dependent", "Thin_Custody_Slack", "Thin_TA_Slack", "Thin_Broker_Slack",
        "Custody_Slack_Group", "Slack_Custody_Num", "Slack_TA_Num", "Slack_Broker_Num"}),
    Typed = Table.TransformColumnTypes(Ordered, {
        {"Fund_ID", type text}, {"Fund_Name", type text}, {"Client_ID", type text}, {"Client_Name", type text},
        {"Strategic_Client", type text}, {"Team_ID", type text}, {"Default_Analyst_Name", type text},
        {"Weightage", type number}, {"ETD", type number}, {"OTC_nonCFD", type number}, {"OTC_CFD", type number},
        {"PFC", type number}, {"EUC", type number}, {"Has_Custody_Process", type text}, {"Has_TA_Process", type text},
        {"Has_Broker_Process", type text}, {"Custody_Cutoff", type time}, {"TA_Cutoff", type time},
        {"Broker_ETA", type time}, {"Pricing_Cutoff", type time}, {"TOP_ID", type text}, {"Client_Cutoff", type time},
        {"NAV_Deadline", type time}, {"Signoff_Model", type text}, {"Cutoff_Data_Quality", type text},
        {"Recon_Pct", type number}, {"NAV_Pct", type number}, {"Required_Mins", type number}, {"Recon_Mins", type number},
        {"NAV_Mins", type number}, {"Custody_Cutoff_Hr", type number}, {"TA_Cutoff_Hr", type number},
        {"Broker_ETA_Hr", type number}, {"Pricing_Cutoff_Hr", type number}, {"Client_Cutoff_Hr", type number},
        {"NAV_Deadline_Hr", type number}, {"Shift_Start_Hr", type number}, {"Planned_Tail_Mins", type number},
        {"Slack_Custody_Mins", type text}, {"Slack_TA_Mins", type text}, {"Slack_Broker_Mins", type text},
        {"Avail_Recon_Mins", type number}, {"Avail_NAV_Mins", type number}, {"Recon_Feasible", type text},
        {"NAV_Feasible", type text}, {"Feasibility_Flag", type text}, {"Broker_Watchlist", type text},
        {"Broker_Slack_Rank", type text}, {"Client_Tier", type text}, {"TOP_Binding_Cutoff_Hr", type number},
        {"Cutoff_Vs_TOP_Mins", type number}, {"TOP_Cutoff_Risk", type text}, {"Client_First_In_TOP", Int64.Type},
        {"Broker_Dependent", type text}, {"Thin_Custody_Slack", type text}, {"Thin_TA_Slack", type text},
        {"Thin_Broker_Slack", type text}, {"Custody_Slack_Group", type text}, {"Slack_Custody_Num", type number},
        {"Slack_TA_Num", type number}, {"Slack_Broker_Num", type number}})
in
    Typed
