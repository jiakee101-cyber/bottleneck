// NAV Bottleneck — Power BI measures for template v4.5
// Tabular Editor 2 or 3: open the model (or connect to Power BI Desktop), paste into the C# Script tab, run (F5),
// then save (Ctrl+S). Safe to re-run: existing measures are updated in place, existing relationships kept.
// Assumes each workbook sheet was loaded as a table with the same name and column headers.

var log = new System.Text.StringBuilder();

Func<string, Table> T = (name) => Model.Tables.FirstOrDefault(t => t.Name == name);
Func<string, string, Column> C = (table, col) => { var t = T(table); return t == null ? null : t.Columns.FirstOrDefault(c => c.Name == col); };

Action<string, string, string, string, string, string> AddMeasure = (table, name, folder, fmt, desc, dax) => {
    var t = T(table);
    if (t == null) { log.AppendLine("SKIPPED measure " + name + ": table " + table + " not in model"); return; }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name);
    if (m != null && m.Table != t) { m.Delete(); m = null; }
    if (m == null) m = t.AddMeasure(name);
    m.Expression = dax;
    m.DisplayFolder = folder;
    m.Description = desc;
    if (!string.IsNullOrEmpty(fmt)) m.FormatString = fmt;
};

Action<string, string, string, string> Rel = (ft, fc, tt, tc) => {
    var from = C(ft, fc); var to = C(tt, tc);
    if (from == null || to == null) { log.AppendLine("SKIPPED relationship " + ft + "[" + fc + "] -> " + tt + "[" + tc + "]: column not in model"); return; }
    if (Model.Relationships.Any(r => r.FromColumn == from && r.ToColumn == to)) return;
    var rel = Model.AddRelationship();
    rel.FromColumn = from; rel.ToColumn = to;
    rel.FromCardinality = RelationshipEndCardinality.Many; rel.ToCardinality = RelationshipEndCardinality.One;
    rel.CrossFilteringBehavior = CrossFilteringBehavior.OneDirection;
    rel.IsActive = true;
};

Action<string, string, string> SortBy = (table, col, by) => {
    var c = C(table, col); var b = C(table, by);
    if (c == null || b == null) { log.AppendLine("SKIPPED sort " + table + "[" + col + "]"); return; }
    c.SortByColumn = b;
};

// ---- Relationships
Rel("Fact_Work", "Fund_ID", "Dim_Fund", "Fund_ID");  // Fund attributes and the client slicer filter the fund-days.
Rel("Dim_Fund", "TOP_ID", "Dim_TOP", "TOP_ID");  // A TOP filters its funds, and through them their fund-days.
Rel("Fact_Milestone", "TOP_ID", "Dim_TOP", "TOP_ID");  // TOP axis on the pricing-delay visual.
Rel("Fact_Work", "Possible_Cause", "Dim_Cause", "Possible_Cause");  // Legend order on the cause chart.

// ---- Sort orders
SortBy("Dim_Cause", "Possible_Cause", "Cause_Order");
SortBy("Dim_SupplierType", "Supplier_Type", "Type_Order");
SortBy("Dim_WaitGroup", "Wait_Group", "Group_Order");
SortBy("Dim_DetailRow", "Detail", "Detail_Order");

// ---- Measures
AddMeasure(@"Fact_Work", @"Fund-Days", @"0 Base", @"#,0", @"Fund-days in view (one Fact_Work row per fund per NAV date per process date).",
    @"COUNTROWS ( Fact_Work )");
AddMeasure(@"Fact_Work", @"Breached Fund-Days", @"0 Base", @"#,0", @"Fund-days delivered after the client cut-off.",
    @"CALCULATE ( COUNTROWS ( Fact_Work ), KEEPFILTERS ( Fact_Work[Breached] = ""Yes"" ) )");
AddMeasure(@"Fact_Work", @"Breach Rate", @"0 Base", @"0.0%", @"Breached fund-days / fund-days.",
    @"DIVIDE ( [Breached Fund-Days], [Fund-Days] )");
AddMeasure(@"Dim_Fund", @"Funds", @"0 Base", @"#,0", @"Funds assigned (design view: not limited by the date slicer).",
    @"DISTINCTCOUNT ( Dim_Fund[Fund_ID] )");
AddMeasure(@"Dim_Fund", @"Clients", @"0 Base", @"#,0", @"Distinct clients.",
    @"DISTINCTCOUNT ( Dim_Fund[Client_ID] )");
AddMeasure(@"Fact_Work", @"Date Range Label", @"0 Base", @"", @"Header text, e.g. 3–28 Aug 2026.",
    @"VAR d0 = MIN ( Fact_Work[Process_Date] )
VAR d1 = MAX ( Fact_Work[Process_Date] )
RETURN
    IF (
        ISBLANK ( d0 ), ""No data"",
        IF (
            d0 = d1, FORMAT ( d0, ""dd mmm yyyy"" ),
            IF (
                YEAR ( d0 ) = YEAR ( d1 ) && MONTH ( d0 ) = MONTH ( d1 ),
                FORMAT ( d0, ""d"" ),
                FORMAT ( d0, ""d mmm yyyy"" )
            ) & ""–"" & FORMAT ( d1, ""d mmm yyyy"" )
        )
    )");
AddMeasure(@"Dim_Fund", @"Client Label", @"0 Base", @"", @"Header text: All (n), the client name, or n selected.",
    @"VAR n = DISTINCTCOUNT ( Dim_Fund[Client_Name] )
RETURN
    IF (
        NOT ISFILTERED ( Dim_Fund[Client_Name] ), ""All ("" & n & "")"",
        IF ( n = 1, SELECTEDVALUE ( Dim_Fund[Client_Name] ), n & "" selected"" )
    )");
AddMeasure(@"Dim_TOP", @"Largest TOP", @"1 Supplier Risk\KPIs", @"", @"TOP with the most funds in view (ties: lowest TOP_ID).",
    @"VAR t =
    TOPN ( 1, FILTER ( VALUES ( Dim_TOP[TOP_ID] ), [Funds] > 0 ), [Funds], DESC, Dim_TOP[TOP_ID], ASC )
RETURN
    MINX ( t, Dim_TOP[TOP_ID] )");
AddMeasure(@"Dim_TOP", @"Largest TOP Funds", @"1 Supplier Risk\KPIs", @"#,0", @"",
    @"VAR t = [Largest TOP]
RETURN CALCULATE ( [Funds], Dim_TOP[TOP_ID] = t )");
AddMeasure(@"Dim_TOP", @"Largest TOP Clients", @"1 Supplier Risk\KPIs", @"#,0", @"",
    @"VAR t = [Largest TOP]
RETURN CALCULATE ( [Clients], Dim_TOP[TOP_ID] = t )");
AddMeasure(@"Dim_TOP", @"Largest TOP Share", @"1 Supplier Risk\KPIs", @"0%", @"Largest TOP's funds as a share of all funds in view.",
    @"DIVIDE ( [Largest TOP Funds], [Funds] )");
AddMeasure(@"Dim_TOP", @"Largest TOP Subtitle", @"1 Supplier Risk\KPIs", @"", @"e.g. 21% of funds, 5 clients",
    @"FORMAT ( [Largest TOP Share], ""0%"" ) & "" of funds, "" & [Largest TOP Clients] & "" clients""");
AddMeasure(@"Fact_Milestone", @"TOP-Days Scored", @"1 Supplier Risk\KPIs", @"#,0", @"TOP deliveries scored against a binding cut-off, on TOP-days an in-view fund depended on.",
    @"CALCULATE ( COUNTROWS ( Fact_Milestone ), KEEPFILTERS ( TREATAS ( SUMMARIZE ( Fact_Work, Fact_Work[Process_Date], Fact_Work[TOP_ID] ), Fact_Milestone[Process_Date], Fact_Milestone[TOP_ID] ) ), KEEPFILTERS ( Fact_Milestone[SLA_Met] IN { ""Yes"", ""No"" } ) )");
AddMeasure(@"Fact_Milestone", @"TOP-Days Late", @"1 Supplier Risk\KPIs", @"#,0", @"",
    @"CALCULATE ( COUNTROWS ( Fact_Milestone ), KEEPFILTERS ( TREATAS ( SUMMARIZE ( Fact_Work, Fact_Work[Process_Date], Fact_Work[TOP_ID] ), Fact_Milestone[Process_Date], Fact_Milestone[TOP_ID] ) ), KEEPFILTERS ( Fact_Milestone[SLA_Met] = ""No"" ) )");
AddMeasure(@"Fact_Milestone", @"TOP Late Rate", @"1 Supplier Risk\KPIs", @"0%", @"TOP-days arriving after the binding cut-off.",
    @"DIVIDE ( [TOP-Days Late], [TOP-Days Scored] )");
AddMeasure(@"Fact_Work", @"Breached Fund-Days Subtitle", @"1 Supplier Risk\KPIs", @"", @"e.g. 9.7% of 1,800 fund-days",
    @"FORMAT ( [Breach Rate], ""0.0%"" ) & "" of "" & FORMAT ( [Fund-Days], ""#,0"" ) & "" fund-days""");
AddMeasure(@"Fact_Work", @"Breaches Pricing Late", @"1 Supplier Risk\KPIs", @"#,0", @"Breached fund-days where pricing arrived after the fund's own PSA cut-off.",
    @"CALCULATE ( [Breached Fund-Days], KEEPFILTERS ( Fact_Work[Pricing_Late_For_This_Fund] = ""Yes"" ) )");
AddMeasure(@"Fact_Work", @"Breaches Pricing Late %", @"1 Supplier Risk\KPIs", @"0%", @"",
    @"DIVIDE ( [Breaches Pricing Late], [Breached Fund-Days] )");
AddMeasure(@"Fact_Work", @"Idle Share of Wait", @"1 Supplier Risk\KPIs", @"0%", @"Share of the wait after pricing while the maker was free (reconstructed).",
    @"VAR q = SUM ( Fact_Work[Queue_Wait_Mins] )
VAR i = SUM ( Fact_Work[Idle_Wait_Mins] )
RETURN DIVIDE ( i, q + i )");
AddMeasure(@"Dim_Fund", @"Funds Label", @"1 Supplier Risk\Exposure", @"", @"Data label: 19 funds · 5 clients",
    @"[Funds] & "" funds · "" & [Clients] & "" clients""");
AddMeasure(@"Dim_TOP", @"Exposure Bar Color", @"1 Supplier Risk\Exposure", @"", @"Conditional formatting (field value) for the exposure bars: red for the largest TOP.",
    @"VAR largest = CALCULATE ( [Largest TOP], ALLSELECTED ( Dim_TOP ) )
RETURN IF ( SELECTEDVALUE ( Dim_TOP[TOP_ID] ) = largest, ""#C8423B"", ""#C9D1DB"" )");
AddMeasure(@"Dim_Fund", @"Supplier Funds", @"1 Supplier Risk\Dependency Table", @"#,0", @"",
    @"VAR s = SELECTEDVALUE ( Dim_SupplierType[Supplier_Type] )
RETURN
    SWITCH (
        s,
        ""Pricing (TOP)"", CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[TOP_ID] <> """" ) ),
        ""Custody"", CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Has_Custody_Process] = ""Yes"" ) ),
        ""TA"", CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Has_TA_Process] = ""Yes"" ) ),
        ""Broker (dependent)"", CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Broker_Dependent] = ""Yes"" ) )
    )");
AddMeasure(@"Dim_Fund", @"Supplier Clients", @"1 Supplier Risk\Dependency Table", @"#,0", @"",
    @"VAR s = SELECTEDVALUE ( Dim_SupplierType[Supplier_Type] )
RETURN
    SWITCH (
        s,
        ""Pricing (TOP)"", CALCULATE ( [Clients], KEEPFILTERS ( Dim_Fund[TOP_ID] <> """" ) ),
        ""Custody"", CALCULATE ( [Clients], KEEPFILTERS ( Dim_Fund[Has_Custody_Process] = ""Yes"" ) ),
        ""TA"", CALCULATE ( [Clients], KEEPFILTERS ( Dim_Fund[Has_TA_Process] = ""Yes"" ) ),
        ""Broker (dependent)"", CALCULATE ( [Clients], KEEPFILTERS ( Dim_Fund[Broker_Dependent] = ""Yes"" ) )
    )");
AddMeasure(@"Dim_Fund", @"Median Slack Mins", @"1 Supplier Risk\Dependency Table", @"0", @"Median minutes between the supplier's cut-off and the pricing gate. Pricing is 0 by definition.",
    @"VAR s = SELECTEDVALUE ( Dim_SupplierType[Supplier_Type] )
RETURN
    SWITCH (
        s,
        ""Pricing (TOP)"", IF ( [Supplier Funds] > 0, 0 ),
        ""Custody"", MEDIAN ( Dim_Fund[Slack_Custody_Num] ),
        ""TA"", MEDIAN ( Dim_Fund[Slack_TA_Num] ),
        ""Broker (dependent)"", MEDIAN ( Dim_Fund[Slack_Broker_Num] )
    )");
AddMeasure(@"Dim_Fund", @"Median Slack Label", @"1 Supplier Risk\Dependency Table", @"", @"0 min / 5.1 h",
    @"VAR m = [Median Slack Mins]
RETURN
    IF ( ISBLANK ( m ), BLANK (), IF ( ABS ( m ) < 60, FORMAT ( m, ""0"" ) & "" min"", FORMAT ( m / 60, ""0.0"" ) & "" h"" ) )");
AddMeasure(@"Dim_Fund", @"Thin Slack Funds", @"1 Supplier Risk\Dependency Table", @"#,0", @"Funds whose slack is at or below Constants!B17 (0 = zero tolerance). Pricing: every fund.",
    @"VAR s = SELECTEDVALUE ( Dim_SupplierType[Supplier_Type] )
RETURN
    SWITCH (
        s,
        ""Pricing (TOP)"", [Supplier Funds],
        ""Custody"", CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Thin_Custody_Slack] = ""Yes"" ) ) + 0,
        ""TA"", CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Thin_TA_Slack] = ""Yes"" ) ) + 0,
        ""Broker (dependent)"", CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Thin_Broker_Slack] = ""Yes"" ) ) + 0
    )");
AddMeasure(@"Dim_Fund", @"Thin Slack Label", @"1 Supplier Risk\Dependency Table", @"", @"all funds / 23 funds",
    @"IF (
    SELECTEDVALUE ( Dim_SupplierType[Supplier_Type] ) = ""Pricing (TOP)"", ""all funds"",
    IF ( ISBLANK ( [Thin Slack Funds] ), BLANK (), [Thin Slack Funds] & "" funds"" )
)");
AddMeasure(@"Dim_Fund", @"Thin Slack Color", @"1 Supplier Risk\Dependency Table", @"", @"Font colour for Thin Slack Label and Median Slack Label: red for pricing, amber when any fund is thin.",
    @"IF (
    SELECTEDVALUE ( Dim_SupplierType[Supplier_Type] ) = ""Pricing (TOP)"", ""#C8423B"",
    IF ( [Thin Slack Funds] > 0, ""#E8A33D"", ""#1F2933"" )
)");
AddMeasure(@"Fact_Milestone", @"Late Hours", @"1 Supplier Risk\Pricing Delay", @"0.0", @"Hours the TOP file arrived after its binding cut-off, summed over the TOP-days in view ('created').",
    @"DIVIDE ( CALCULATE ( SUM ( Fact_Milestone[Late_Mins] ), KEEPFILTERS ( TREATAS ( SUMMARIZE ( Fact_Work, Fact_Work[Process_Date], Fact_Work[TOP_ID] ), Fact_Milestone[Process_Date], Fact_Milestone[TOP_ID] ) ) ), 60 )");
AddMeasure(@"Fact_Milestone", @"Late Hours Label", @"1 Supplier Risk\Pricing Delay", @"", @"",
    @"FORMAT ( [Late Hours] + 0, ""0.0"" ) & ""h""");
AddMeasure(@"Fact_Work", @"Breached Fund-Days When Late", @"1 Supplier Risk\Pricing Delay", @"#,0", @"Breached fund-days on days the fund's TOP missed its binding cut-off ('reached the funds').",
    @"CALCULATE ( [Breached Fund-Days], KEEPFILTERS ( Fact_Work[TOP_SLA_Met] = ""No"" ) ) + 0");
AddMeasure(@"Fact_Work", @"Avg Queue Wait", @"1 Supplier Risk\Waiting", @"0", @"Avg minutes per fund-day behind the maker's other funds (purple). Group-aware via Dim_WaitGroup.",
    @"VAR g = SELECTEDVALUE ( Dim_WaitGroup[Wait_Group] )
RETURN
    SWITCH (
        g,
        ""Broker-dependent"", CALCULATE ( AVERAGE ( Fact_Work[Queue_Wait_Mins] ), KEEPFILTERS ( Fact_Work[Broker_Dependent] = ""Yes"" ) ),
        ""Not broker-dependent"", CALCULATE ( AVERAGE ( Fact_Work[Queue_Wait_Mins] ), KEEPFILTERS ( Fact_Work[Broker_Dependent] = ""No"" ) ),
        ""Thin custody slack"", CALCULATE ( AVERAGE ( Fact_Work[Queue_Wait_Mins] ), KEEPFILTERS ( Fact_Work[Custody_Slack_Group] = ""Thin custody slack"" ) ),
        ""Ample custody slack"", CALCULATE ( AVERAGE ( Fact_Work[Queue_Wait_Mins] ), KEEPFILTERS ( Fact_Work[Custody_Slack_Group] = ""Ample custody slack"" ) ),
        AVERAGE ( Fact_Work[Queue_Wait_Mins] )
    )");
AddMeasure(@"Fact_Work", @"Avg Idle Wait", @"1 Supplier Risk\Waiting", @"0", @"Avg minutes per fund-day while the maker was free (amber). Group-aware via Dim_WaitGroup.",
    @"VAR g = SELECTEDVALUE ( Dim_WaitGroup[Wait_Group] )
RETURN
    SWITCH (
        g,
        ""Broker-dependent"", CALCULATE ( AVERAGE ( Fact_Work[Idle_Wait_Mins] ), KEEPFILTERS ( Fact_Work[Broker_Dependent] = ""Yes"" ) ),
        ""Not broker-dependent"", CALCULATE ( AVERAGE ( Fact_Work[Idle_Wait_Mins] ), KEEPFILTERS ( Fact_Work[Broker_Dependent] = ""No"" ) ),
        ""Thin custody slack"", CALCULATE ( AVERAGE ( Fact_Work[Idle_Wait_Mins] ), KEEPFILTERS ( Fact_Work[Custody_Slack_Group] = ""Thin custody slack"" ) ),
        ""Ample custody slack"", CALCULATE ( AVERAGE ( Fact_Work[Idle_Wait_Mins] ), KEEPFILTERS ( Fact_Work[Custody_Slack_Group] = ""Ample custody slack"" ) ),
        AVERAGE ( Fact_Work[Idle_Wait_Mins] )
    )");
AddMeasure(@"Fact_Work", @"Wait Fund-Days", @"1 Supplier Risk\Waiting", @"#,0", @"Fund-days with a measured wait (pricing arrival logged). Group-aware.",
    @"VAR g = SELECTEDVALUE ( Dim_WaitGroup[Wait_Group] )
RETURN
    SWITCH (
        g,
        ""Broker-dependent"", CALCULATE ( COUNT ( Fact_Work[Wait_After_Pricing_Mins] ), KEEPFILTERS ( Fact_Work[Broker_Dependent] = ""Yes"" ) ),
        ""Not broker-dependent"", CALCULATE ( COUNT ( Fact_Work[Wait_After_Pricing_Mins] ), KEEPFILTERS ( Fact_Work[Broker_Dependent] = ""No"" ) ),
        ""Thin custody slack"", CALCULATE ( COUNT ( Fact_Work[Wait_After_Pricing_Mins] ), KEEPFILTERS ( Fact_Work[Custody_Slack_Group] = ""Thin custody slack"" ) ),
        ""Ample custody slack"", CALCULATE ( COUNT ( Fact_Work[Wait_After_Pricing_Mins] ), KEEPFILTERS ( Fact_Work[Custody_Slack_Group] = ""Ample custody slack"" ) ),
        COUNT ( Fact_Work[Wait_After_Pricing_Mins] )
    )");
AddMeasure(@"Fact_Work", @"Wait n Label", @"1 Supplier Risk\Waiting", @"", @"n=640",
    @"""n="" & FORMAT ( [Wait Fund-Days] + 0, ""#,0"" )");
AddMeasure(@"Fact_Work", @"Funds In View", @"2 Fund Level\KPIs", @"#,0", @"",
    @"DISTINCTCOUNT ( Fact_Work[Fund_ID] )");
AddMeasure(@"Fact_Work", @"Breached Funds", @"2 Fund Level\KPIs", @"#,0", @"",
    @"CALCULATE ( DISTINCTCOUNT ( Fact_Work[Fund_ID] ), KEEPFILTERS ( Fact_Work[Breached] = ""Yes"" ) ) + 0");
AddMeasure(@"Fact_Work", @"Client Sign-off Funds", @"2 Fund Level\KPIs", @"#,0", @"",
    @"CALCULATE ( DISTINCTCOUNT ( Fact_Work[Fund_ID] ), KEEPFILTERS ( Fact_Work[Signoff_Model] = ""Client"" ) ) + 0");
AddMeasure(@"Fact_Work", @"Funds In View Subtitle", @"2 Fund Level\KPIs", @"", @"4 breached, 3 client sign-off",
    @"[Breached Funds] & "" breached, "" & [Client Sign-off Funds] & "" client sign-off""");
AddMeasure(@"Fact_Work", @"Fund Filter Label", @"2 Fund Level\KPIs", @"", @"Header text: All (n), the fund, or n selected.",
    @"VAR n = DISTINCTCOUNT ( Fact_Work[Fund_ID] )
RETURN
    IF (
        ISFILTERED ( Fact_Work[Fund_ID] ) || ISFILTERED ( Dim_Fund[Fund_ID] ),
        IF ( n = 1, SELECTEDVALUE ( Fact_Work[Fund_ID] ), n & "" selected"" ),
        ""All ("" & n & "")""
    )");
AddMeasure(@"Fact_Work", @"Avg Wait After Pricing", @"2 Fund Level\KPIs", @"0", @"Avg minutes from pricing arrived to NAV started.",
    @"AVERAGE ( Fact_Work[Wait_After_Pricing_Mins] )");
AddMeasure(@"Fact_Work", @"Avg NAV To Controlled", @"2 Fund Level\KPIs", @"0", @"Avg minutes FA spent: NAV start to Controlled (to FA signed off for client sign-off funds).",
    @"AVERAGE ( Fact_Work[NAV_Span_Mins] )");
AddMeasure(@"Fact_Work", @"Avg Controlled To Delivered", @"2 Fund Level\KPIs", @"0", @"Avg minutes after FA finished: NAV_End to Delivered.",
    @"AVERAGE ( Fact_Work[Controlled_To_Delivered_Mins] )");
AddMeasure(@"Fact_Work", @"Avg Headroom", @"2 Fund Level\KPIs", @"0", @"Avg minutes delivered before the client cut-off (negative = after).",
    @"AVERAGE ( Fact_Work[Headroom_At_Delivery_Mins] )");
AddMeasure(@"Fact_Work", @"Bar Offset", @"2 Fund Level\Timeline", @"0.00", @"Transparent first segment (hours of day). Set the X axis start to 9.",
    @"MIN ( Fact_Work[Bar_Offset_Hr] )");
AddMeasure(@"Fact_Work", @"Bar Waiting After Pricing", @"2 Fund Level\Timeline", @"0.00", @"",
    @"SUM ( Fact_Work[Bar_Wait_Hr] )");
AddMeasure(@"Fact_Work", @"Bar NAV To Controlled", @"2 Fund Level\Timeline", @"0.00", @"",
    @"SUM ( Fact_Work[Bar_NAV_Hr] )");
AddMeasure(@"Fact_Work", @"Bar Controlled To FA Signed Off", @"2 Fund Level\Timeline", @"0.00", @"",
    @"SUM ( Fact_Work[Bar_Control_Hr] )");
AddMeasure(@"Fact_Work", @"Bar FA Signed Off To Delivered", @"2 Fund Level\Timeline", @"0.00", @"",
    @"SUM ( Fact_Work[Bar_Tail_Hr] )");
AddMeasure(@"Fact_Work", @"NAV Start Hr", @"2 Fund Level\Timeline", @"0.00", @"Sort the timeline's Y axis by this, ascending.",
    @"MIN ( Fact_Work[Start_Hr] )");
AddMeasure(@"Fact_Work", @"Pricing Cutoff Hr", @"2 Fund Level\Timeline", @"0.00", @"",
    @"MIN ( Fact_Work[Fund_Pricing_Cutoff_Hr] )");
AddMeasure(@"Fact_Work", @"Pricing Arrived Hr", @"2 Fund Level\Timeline", @"0.00", @"",
    @"MIN ( Fact_Work[Arrival_Hr] )");
AddMeasure(@"Fact_Work", @"Client Cutoff Hr", @"2 Fund Level\Timeline", @"0.00", @"",
    @"MIN ( Fact_Work[Client_Cutoff_Hr] )");
AddMeasure(@"Fact_Work", @"Selected Fund Title", @"2 Fund Level\Selected Fund", @"", @"",
    @"""Selected fund — "" & IF ( HASONEVALUE ( Fact_Work[Fund_ID] ), VALUES ( Fact_Work[Fund_ID] ), ""select one"" )");
AddMeasure(@"Fact_Work", @"Detail Value", @"2 Fund Level\Selected Fund", @"", @"Value column of the selected-fund table (rows from Dim_DetailRow).",
    @"VAR r = SELECTEDVALUE ( Dim_DetailRow[Detail] )
VAR pc = MIN ( Fact_Work[Fund_Pricing_Cutoff_Hr] )
VAR pa = MIN ( Fact_Work[Pricing_Arrival_DT] )
VAR vp = MIN ( Fact_Work[Var_Pricing_Mins] )
VAR ns = MIN ( Fact_Work[NAV_Start_DT] )
VAR ct = MIN ( Fact_Work[Status_Controlled_DT] )
VAR fa = MIN ( Fact_Work[Status_FA_SignedOff_DT] )
VAR dl = MIN ( Fact_Work[Delivered_DT] )
VAR cc = MIN ( Fact_Work[Client_Cutoff_Hr] )
VAR hd = MIN ( Fact_Work[Headroom_At_Delivery_Mins] )
VAR wt = MIN ( Fact_Work[Wait_After_Pricing_Mins] )
VAR nv = MIN ( Fact_Work[NAV_Span_Mins] )
VAR isClient = SELECTEDVALUE ( Fact_Work[Signoff_Model] ) = ""Client""
RETURN
    IF (
        NOT HASONEVALUE ( Fact_Work[Fund_ID] ), BLANK (),
        SWITCH (
            r,
            ""Pricing cut-off"", IF ( ISBLANK ( pc ), ""–"", FORMAT ( pc / 24, ""hh:mm"" ) ),
            ""Pricing arrived"", IF ( ISBLANK ( pa ), ""not logged"",
                FORMAT ( pa, ""hh:mm"" ) & IF ( ISBLANK ( vp ), """", "" ("" & FORMAT ( vp, ""+0;-0;0"" ) & "" min)"" ) ),
            ""NAV started"", IF ( ISBLANK ( ns ), ""–"", FORMAT ( ns, ""hh:mm"" ) ),
            ""Controlled"", IF ( isClient, ""n/a — client sign-off"", IF ( ISBLANK ( ct ), ""–"", FORMAT ( ct, ""hh:mm"" ) ) ),
            ""FA signed off"", IF ( ISBLANK ( fa ), ""–"", FORMAT ( fa, ""hh:mm"" ) ),
            ""Delivered"", IF ( ISBLANK ( dl ), ""–"", FORMAT ( dl, ""hh:mm"" ) ),
            ""Client cut-off"", IF ( ISBLANK ( cc ), ""–"", FORMAT ( cc / 24, ""hh:mm"" ) ),
            ""Headroom"", IF ( ISBLANK ( hd ), ""–"", FORMAT ( hd, ""0;-0;0"" ) & "" min"" ),
            ""Waited after pricing"", IF ( ISBLANK ( wt ), ""–"", FORMAT ( wt, ""0"" ) & "" min"" ),
            ""NAV to Controlled"", IF ( ISBLANK ( nv ), ""–"", FORMAT ( nv, ""0"" ) & "" min"" )
        )
    )");
AddMeasure(@"Fact_Work", @"Detail Font Color", @"2 Fund Level\Selected Fund", @"", @"Conditional font colour for the selected-fund table: red headroom when negative.",
    @"IF (
    SELECTEDVALUE ( Dim_DetailRow[Detail] ) = ""Headroom"" && MIN ( Fact_Work[Headroom_At_Delivery_Mins] ) < 0,
    ""#C8423B"", ""#1F2933""
)");

log.Insert(0, "NAV Bottleneck v4.5: 56 measures processed.\n");
Info(log.ToString());
