// Fact_Work: one row per fund-day, built from the status log (the Fact_Work sheet is no longer needed).
// Same 78 columns as the v4.5 sheet, so the measures and visuals keep working.
let
    fx = fxNAV,
    Base = NAV_FundDays,
    Analysts = let t = NAV_Inputs[Analyst] in fx[LookupOf](t[Analyst_Name], List.Repeat({true}, Table.RowCount(t))),
    TopEarliest = fx[LookupOf](Dim_TOP[TOP_ID], Dim_TOP[Earliest_Cutoff_Hr]),
    TopDaysT = NAV_TopDays,
    TopDays = Record.FromList(Table.ToRecords(TopDaysT), TopDaysT[K]),
    // Latest arrival per process date + TOP, and whether any arrival row exists (for TOP_SLA_Met and Due_Slot_Hr).
    MsGroups = Table.Group(
        Table.AddColumn(NAV_MilestoneRaw, "K", each Date.ToText([Process_Date], "yyyy-MM-dd") & "|" & (if fx[Key]([TOP_ID]) = null then "" else fx[Key]([TOP_ID])), type text),
        {"K"}, {{"MaxArrival", each List.Max(List.RemoveNulls([Actual_Arrival_DT])), type nullable datetime},
                {"Rows", each Table.RowCount(_), Int64.Type}}),
    Ms = Record.FromList(Table.ToRecords(MsGroups), MsGroups[K]),
    IsClient = (v as any) as logical => fx[Same](v, "Client"),
    // Step 1: every column that does not compare a fund-day with the maker's other fund-days.
    Step1 = Table.AddColumn(Base, "C1", (r) =>
        let
            B = r[Process_Date],
            E = r[Signoff_Model],
            Client = IsClient(E),
            F = r[Status_Calculated_DT], G = r[Status_Controlled_DT], H = r[Status_FA_SignedOff_DT], I = r[Status_SignedOff_DT],
            K = r[Rework_Gap_Mins],
            L = r[Maker_Name],
            M = if Client then "n/a — no control step" else r[Checker_Found],
            N = r[Default_Analyst_Name],
            R = r[Recon_Mins], S = r[NAV_Mins], T = r[Planned_Tail_Mins],
            U = r[Pricing_Arrival_DT], V = r[Client_Cutoff_DT],
            W = F,
            X = if Client then H else G,
            Y = I,
            Z = if W = null or R = null then null else fx[AddMins](W, -R),
            AA = if U = null or V = null then null else fx[R0](fx[Mins](V, U)),
            AB = if U = null then null else fx[R0](fx[Mins](W, U)),
            AC = if AB = null then null else List.Max({0, AB}),
            AD = fx[R0](fx[Mins](X, W)),
            AEnum = if Client then null else fx[R0](fx[Mins](H, G)),
            AE = if Client then "n/a" else if AEnum = null then null else Text.From(AEnum),
            AF = fx[R0](fx[Mins](Y, H)),
            AG = fx[R0](fx[Mins](H, F)),
            AH = r[Breach_Mins],
            AI = r[Breached],
            AL = r[TOP_ID],
            AN = r[Fund_Pricing_Cutoff_Hr],
            AM = if U = null then null else if U > fx[AtHr](B, r[Pricing_Late_Hr]) then "Yes" else "No",
            DayKey = if fx[Key](AL) = null then null else Date.ToText(B, "yyyy-MM-dd") & "|" & fx[Key](AL),
            Day = if DayKey = null then null else Record.FieldOrDefault(TopDays, DayKey, null),
            MsDay = if DayKey = null then null else Record.FieldOrDefault(Ms, DayKey, null),
            Binding = if Day = null then null else Day[Binding_Cutoff_Hr],
            SlotBase = if MsDay <> null and Binding <> null then Binding else fx[Find](TopEarliest, AL),
            AO = if AL = null then null else fx[Floor](SlotBase, 0.5),
            Late = if MsDay = null or Binding = null or MsDay[MaxArrival] = null then null
                else fx[R0](fx[Mins](MsDay[MaxArrival], fx[AtHr](B, Binding))),
            BB = if AL = null or Late = null then null else if Late > 0 then "No" else "Yes",
            AP = if U = null then null else fx[R](fx[HrOfDay](U), 4),
            AQ = if W = null then null else fx[R](fx[HrOfDay](W), 4),
            AR = if X = null then null else fx[R](fx[HrOfDay](X), 4),
            AS = if AN = null or V = null or S = null or T = null then null else fx[R0](fx[Mins](V, fx[AtHr](B, AN)) - S - T),
            AT = if AN = null or U = null then null else fx[R0](fx[Mins](U, fx[AtHr](B, AN))),
            AU = if AD = null or S = null then null else fx[R0](AD - S),
            AV = if AEnum = null then 0 else AEnum,
            AW = if AF = null or T = null then null else AF - T,
            AX = if List.Count(List.RemoveNulls({AT, AB, AU, AW, AS, AH})) < 6 then null else fx[R0](AT + AB + AU + AV + AW - AS - AH),
            BM = if AQ = null then null else if AP = null then AQ else List.Min({AP, AQ}),
            Done = if W = null or S = null then null
                else let Budget = fx[AddMins](W, S) in if X = null then Budget else List.Min({Budget, List.Max({X, W})})
        in
            [
                Processing_Lag_Days = Duration.Days(B - r[NAV_Date]),
                Checker_Name = M,
                Reassigned = if fx[Same](L, N) then "No" else "Yes",
                Self_Checked = if Client then "n/a" else if fx[Same](L, M) then "YES — four-eyes breach" else "No",
                NAV_Start_DT = W, NAV_End_DT = X, Delivered_DT = Y, Implied_Work_Start_DT = Z,
                Headroom_After_Pricing_Mins = AA, Pricing_To_Calc_Mins = AB, Wait_After_Pricing_Mins = AC,
                NAV_Span_Mins = AD, Check_Mins = AE, External_Tail_Mins = AF, FA_Total_Mins = AG,
                Primary_Cause = if AI <> "Yes" then "On time"
                    else if fx[N](AC) >= List.Max({fx[N](AF), fx[N](K)}) then "Wait for analyst"
                    else if fx[N](AF) >= fx[N](K) then "External sign-off" else "Rework",
                Row_Quality = if F = null or Y = null or fx[Find](Analysts, L) = null then "CHECK" else "OK",
                Pricing_Late_For_This_Fund = AM,
                Due_Slot_Hr = AO,
                Arrival_Hr = AP, Start_Hr = AQ, End_Hr = AR,
                Planned_Buffer_Mins = AS, Var_Pricing_Mins = AT, Var_NAV_Stretch_Mins = AU, Var_Control_Mins = AV,
                Var_Approval_Mins = AW, Bridge_Check = AX,
                Bridge_OK = if AX = null then "No" else if Number.Abs(AX) <= 2 then "Yes" else "No",
                Breach_Class = if AI <> "Yes" then "n/a"
                    else if AA = null or S = null or T = null then "Unknown"
                    else if AA < S + T then "Lost on arrival" else "Lost after arrival",
                TOP_SLA_Met = BB,
                Possible_Cause = if AI <> "Yes" then "Not breached"
                    else if AM = "Yes" then "Pricing late"
                    else if r[Custody_Slack_Group] = "Thin custody slack" then "Thin custody slack"
                    else if r[Broker_Dependent] = "Yes" then "Broker-dependent" else "None of these",
                Fund_Label = r[Fund_ID] & (if Client then "*" else ""),
                Controlled_To_Delivered_Mins = fx[R0](fx[Mins](Y, X)),
                Headroom_At_Delivery_Mins = if AH = null then null else -AH,
                Bar_Offset_Hr = BM,
                Bar_Wait_Hr = if BM = null then null else fx[R](fx[N](AC) / 60, 4),
                Bar_NAV_Hr = if BM = null or AD = null then null else fx[R](AD / 60, 4),
                Bar_Control_Hr = if BM = null then null else fx[R](AV / 60, 4),
                Bar_Tail_Hr = if BM = null or AF = null then null else fx[R](AF / 60, 4),
                Work_Start_Num = if Z <> null and W <> null then Number.From(Z) else 0,
                Work_End_Num = if W <> null then Number.From(W) else 0,
                Control_Start_Hr = if W = null then null else fx[R](fx[HrsFrom](W, B), 4),
                Control_End_Hr = if X = null then null else fx[R](fx[HrsFrom](X, B), 4),
                Control_Window_Status = if W = null then "Missing Calculated"
                    else if X = null then (if Client then "Missing FA signed off" else "Missing Controlled")
                    else if X < W then "End before start" else "OK",
                InHand_Hr = if Z = null then null else fx[R](fx[HrsFrom](if U <> null then List.Min({U, Z}) else Z, B), 4),
                Work_Start_Hr = if Z = null then null else fx[R](fx[HrsFrom](Z, B), 4),
                NAV_Done_Hr = if Done = null then null else fx[R](fx[HrsFrom](Done, B), 4)
            ]),
    C1Fields = {"Processing_Lag_Days", "Checker_Name", "Reassigned", "Self_Checked", "NAV_Start_DT", "NAV_End_DT",
        "Delivered_DT", "Implied_Work_Start_DT", "Headroom_After_Pricing_Mins", "Pricing_To_Calc_Mins",
        "Wait_After_Pricing_Mins", "NAV_Span_Mins", "Check_Mins", "External_Tail_Mins", "FA_Total_Mins", "Primary_Cause",
        "Row_Quality", "Pricing_Late_For_This_Fund", "Due_Slot_Hr", "Arrival_Hr", "Start_Hr", "End_Hr",
        "Planned_Buffer_Mins", "Var_Pricing_Mins", "Var_NAV_Stretch_Mins", "Var_Control_Mins", "Var_Approval_Mins",
        "Bridge_Check", "Bridge_OK", "Breach_Class", "TOP_SLA_Met", "Possible_Cause", "Fund_Label",
        "Controlled_To_Delivered_Mins", "Headroom_At_Delivery_Mins", "Bar_Offset_Hr", "Bar_Wait_Hr", "Bar_NAV_Hr",
        "Bar_Control_Hr", "Bar_Tail_Hr", "Work_Start_Num", "Work_End_Num", "Control_Start_Hr", "Control_End_Hr",
        "Control_Window_Status", "InHand_Hr", "Work_Start_Hr", "NAV_Done_Hr"},
    Expanded1 = Table.ExpandRecordColumn(Step1, "C1", C1Fields),
    Indexed = Table.AddIndexColumn(Expanded1, "Row_ID", 1, 1, Int64.Type),
    // Step 2: per maker and process date, the queue behind the maker's other fund-days (Queue_Wait_Mins) and
    // the latest earlier NAV start (Maker_Free_From_DT). Same overlap rule as the v4.5 SUMPRODUCT.
    WithMakerKey = Table.AddColumn(Indexed, "Maker_Key", each fx[Key]([Maker_Name]), type text),
    Queue = (g as table) as table =>
        let
            T = Table.Buffer(g),
            Ids = List.Buffer(T[Row_ID]),
            Ws = List.Buffer(List.Transform(T[NAV_Start_DT], each if _ = null then null else Number.From(_))),
            BT = List.Buffer(T[Work_End_Num]),
            BS = List.Buffer(T[Work_Start_Num]),
            Pos = List.Positions(Ids),
            Results = List.Transform(Pos, (i) =>
                let
                    Row = T{i},
                    AC = Row[Wait_After_Pricing_Mins],
                    Wi = Ws{i},
                    Ui = if Row[Pricing_Arrival_DT] = null then null else Number.From(Row[Pricing_Arrival_DT]),
                    Total = if AC = null or AC = 0 or Row[Maker_Key] = null then 0
                        else List.Sum(List.Transform(Pos, (j) =>
                            if j = i then 0
                            else
                                let Ov = List.Min({Wi, BT{j}}) - List.Max({Ui, BS{j}}) in if Ov > 0 then Ov else 0)),
                    QueueMins = if AC = null then null
                        else if Row[Maker_Key] = null or AC = 0 then 0
                        else List.Min({AC, fx[R0](fx[R](1440 * Total, 4))}),
                    Earlier = if Row[Maker_Key] = null or Wi = null then {}
                        else List.Select(List.Transform(Pos, (j) => if j <> i and Ws{j} <> null and Ws{j} < Wi then Ws{j} else null), each _ <> null),
                    FreeFrom = if List.IsEmpty(Earlier) then null else DateTime.From(List.Max(Earlier))
                in
                    [Queue_Wait_Mins = QueueMins, Maker_Free_From_DT = FreeFrom]),
            Added = Table.FromColumns(Table.ToColumns(T) & {List.Transform(Results, each [Queue_Wait_Mins]), List.Transform(Results, each [Maker_Free_From_DT])},
                Table.ColumnNames(T) & {"Queue_Wait_Mins", "Maker_Free_From_DT"})
        in
            Added,
    Grouped = Table.Group(WithMakerKey, {"Maker_Key", "Process_Date"}, {{"G", Queue, type table}}),
    Combined = Table.Sort(Table.Combine(Grouped[G]), {{"Row_ID", Order.Ascending}}),
    // Step 3: own recon and other hold-up, which need the queue minutes.
    WithOwn = Table.AddColumn(Combined, "Own_Recon_Mins", each
        if [Wait_After_Pricing_Mins] = null then null
        else fx[R0](List.Min({[Wait_After_Pricing_Mins] - [Queue_Wait_Mins], fx[N]([Recon_Mins])})), type nullable number),
    WithOther = Table.AddColumn(WithOwn, "Other_Holdup_Mins", each
        if [Wait_After_Pricing_Mins] = null then null
        else [Wait_After_Pricing_Mins] - [Queue_Wait_Mins] - [Own_Recon_Mins], type nullable number),
    Columns = {"NAV_Date", "Process_Date", "Fund_ID", "Processing_Lag_Days", "Signoff_Model", "Status_Calculated_DT",
        "Status_Controlled_DT", "Status_FA_SignedOff_DT", "Status_SignedOff_DT", "Recalc_Count", "Rework_Gap_Mins",
        "Maker_Name", "Checker_Name", "Default_Analyst_Name", "Reassigned", "Self_Checked", "Required_Mins", "Recon_Mins",
        "NAV_Mins", "Planned_Tail_Mins", "Pricing_Arrival_DT", "Client_Cutoff_DT", "NAV_Start_DT", "NAV_End_DT",
        "Delivered_DT", "Implied_Work_Start_DT", "Headroom_After_Pricing_Mins", "Pricing_To_Calc_Mins",
        "Wait_After_Pricing_Mins", "NAV_Span_Mins", "Check_Mins", "External_Tail_Mins", "FA_Total_Mins", "Breach_Mins",
        "Breached", "Primary_Cause", "Row_Quality", "TOP_ID", "Pricing_Late_For_This_Fund", "Fund_Pricing_Cutoff_Hr",
        "Due_Slot_Hr", "Arrival_Hr", "Start_Hr", "End_Hr", "Planned_Buffer_Mins", "Var_Pricing_Mins",
        "Var_NAV_Stretch_Mins", "Var_Control_Mins", "Var_Approval_Mins", "Bridge_Check", "Bridge_OK", "Breach_Class",
        "Client_Name", "TOP_SLA_Met", "Maker_Free_From_DT", "Queue_Wait_Mins", "Own_Recon_Mins", "Broker_Dependent",
        "Custody_Slack_Group", "Possible_Cause", "Client_Cutoff_Hr", "Fund_Label", "Controlled_To_Delivered_Mins",
        "Headroom_At_Delivery_Mins", "Bar_Offset_Hr", "Bar_Wait_Hr", "Bar_NAV_Hr", "Bar_Control_Hr", "Bar_Tail_Hr",
        "Other_Holdup_Mins", "Work_Start_Num", "Work_End_Num", "Control_Start_Hr", "Control_End_Hr",
        "Control_Window_Status", "InHand_Hr", "Work_Start_Hr", "NAV_Done_Hr"},
    Ordered = Table.SelectColumns(WithOther, Columns),
    TextCols = {"Fund_ID", "Signoff_Model", "Maker_Name", "Checker_Name", "Default_Analyst_Name", "Reassigned", "Self_Checked",
        "Check_Mins", "Breached", "Primary_Cause", "Row_Quality", "TOP_ID", "Pricing_Late_For_This_Fund", "Bridge_OK",
        "Breach_Class", "Client_Name", "TOP_SLA_Met", "Broker_Dependent", "Custody_Slack_Group", "Possible_Cause",
        "Fund_Label", "Control_Window_Status"},
    Dates = {"NAV_Date", "Process_Date"},
    DateTimes = {"Status_Calculated_DT", "Status_Controlled_DT", "Status_FA_SignedOff_DT", "Status_SignedOff_DT",
        "Pricing_Arrival_DT", "Client_Cutoff_DT", "NAV_Start_DT", "NAV_End_DT", "Delivered_DT", "Implied_Work_Start_DT",
        "Maker_Free_From_DT"},
    Whole = {"Recalc_Count"},
    Numbers = List.Difference(Columns, TextCols & Dates & DateTimes & Whole),
    Typed = Table.TransformColumnTypes(Ordered,
        List.Transform(TextCols, each {_, type text}) & List.Transform(Dates, each {_, type date})
        & List.Transform(DateTimes, each {_, type datetime}) & List.Transform(Whole, each {_, Int64.Type})
        & List.Transform(Numbers, each {_, type number}))
in
    Typed
