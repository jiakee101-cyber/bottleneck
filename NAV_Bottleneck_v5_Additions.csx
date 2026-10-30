// NAV Bottleneck v5: calculated columns and data-check measures for the Power Query build.
// Run AFTER the v5 Power Query code is in place and the model has been refreshed once (the old Excel
// columns with these names must be gone first). Tabular Editor 2 or 3 connected to Power BI Desktop:
// paste into the C# Script tab, run (F5), then save (Ctrl+S). Safe to re-run.
// Keep NAV_Bottleneck_Measures_v4_5.csx as it is: the report measures do not change.

var log = new System.Text.StringBuilder();
int cols = 0, checks = 0;

Func<string, Table> T = (name) => Model.Tables.FirstOrDefault(t => t.Name == name);

// Columns that summarise Fact_Work for a small table. They use FILTER rather than CALCULATE so that
// tables without a relationship (Dim_Analyst, Dim_Slot) do not raise a circular dependency.
Action<string, string, string, string> CalcCol = (table, name, fmt, dax) => {
    var t = T(table);
    if (t == null) { log.AppendLine("SKIPPED column " + name + ": table " + table + " not in model"); return; }
    var c = t.Columns.FirstOrDefault(x => x.Name == name);
    if (c != null && !(c is CalculatedColumn)) {
        log.AppendLine("SKIPPED column " + table + "[" + name + "]: a loaded column still has this name. Refresh the model after replacing the Power Query code, then run this script again.");
        return;
    }
    var cc = c as CalculatedColumn;
    if (cc == null) cc = t.AddCalculatedColumn(name);
    cc.Expression = dax;
    cc.DisplayFolder = "Calculated (v5)";
    if (!string.IsNullOrEmpty(fmt)) cc.FormatString = fmt;
    cols++;
};

Action<string, string, string> Check = (name, fmt, dax) => {
    var t = T("Fact_Work");
    if (t == null) { log.AppendLine("SKIPPED check " + name + ": table Fact_Work not in model"); return; }
    var m = Model.AllMeasures.FirstOrDefault(x => x.Name == name);
    if (m != null && m.Table != t) { m.Delete(); m = null; }
    if (m == null) m = t.AddMeasure(name);
    m.Expression = dax;
    m.DisplayFolder = @"9 Data Checks";
    m.Description = "Data-quality check (replaces the Checks sheet). Responds to the report filters.";
    m.FormatString = string.IsNullOrEmpty(fmt) ? "#,0" : fmt;
    checks++;
};

string BD = @"VAR d0 = MIN ( Fact_Work[Process_Date] )
VAR d1 = MAX ( Fact_Work[Process_Date] )
VAR bd = IF ( ISBLANK ( d0 ), 1, NETWORKDAYS ( d0, d1 ) )
";

// ---- Dim_TOP: delivery record of each pricing group
CalcCol("Dim_TOP", "TOP_Days_Scored", "#,0", @"VAR t = Dim_TOP[TOP_ID]
RETURN COUNTROWS ( FILTER ( Fact_Milestone, Fact_Milestone[TOP_ID] = t && Fact_Milestone[SLA_Met] IN { ""Yes"", ""No"" } ) ) + 0");
CalcCol("Dim_TOP", "TOP_Days_Late", "#,0", @"VAR t = Dim_TOP[TOP_ID]
RETURN COUNTROWS ( FILTER ( Fact_Milestone, Fact_Milestone[TOP_ID] = t && Fact_Milestone[SLA_Met] = ""No"" ) ) + 0");
CalcCol("Dim_TOP", "Late_Hours_Total", "0.00", @"VAR t = Dim_TOP[TOP_ID]
RETURN ROUND ( SUMX ( FILTER ( Fact_Milestone, Fact_Milestone[TOP_ID] = t ), Fact_Milestone[Late_Mins] ) / 60, 2 ) + 0");
CalcCol("Dim_TOP", "Breached_Fund_Days_When_Late", "#,0", @"VAR t = Dim_TOP[TOP_ID]
RETURN COUNTROWS ( FILTER ( Fact_Work, Fact_Work[TOP_ID] = t && Fact_Work[Breached] = ""Yes"" && Fact_Work[TOP_SLA_Met] = ""No"" ) ) + 0");

// ---- Dim_Fund: how often each fund ran
CalcCol("Dim_Fund", "Runs_Observed", "#,0", @"VAR f = Dim_Fund[Fund_ID]
RETURN COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Fund_ID] = f ) ) + 0");
CalcCol("Dim_Fund", "NAV_Frequency_Observed", "", BD + @"VAR runs = Dim_Fund[Runs_Observed]
RETURN
    SWITCH ( TRUE (),
        runs = 0, ""Not seen"",
        runs >= bd * 0.6, ""Daily"",
        runs >= bd * 0.12, ""Weekly"",
        ""Monthly or ad hoc"" )");

// ---- Dim_Analyst: average daily workload over the business days loaded
CalcCol("Dim_Analyst", "Planned_Maker_Mins_PerDay", "#,0", BD + @"VAR a = Dim_Analyst[Analyst_Name]
RETURN ROUND ( SUMX ( FILTER ( Fact_Work, Fact_Work[Default_Analyst_Name] = a ), Fact_Work[Required_Mins] ) / bd, 0 ) + 0");
CalcCol("Dim_Analyst", "Actual_Maker_Mins_PerDay", "#,0", BD + @"VAR a = Dim_Analyst[Analyst_Name]
RETURN ROUND ( SUMX ( FILTER ( Fact_Work, Fact_Work[Maker_Name] = a ), Fact_Work[Required_Mins] ) / bd, 0 ) + 0");
CalcCol("Dim_Analyst", "Actual_Utilisation", "0%", @"DIVIDE ( Dim_Analyst[Actual_Maker_Mins_PerDay], Dim_Analyst[Capacity_Mins] )");
CalcCol("Dim_Analyst", "Funds_Checked_PerDay", "0.0", BD + @"VAR a = Dim_Analyst[Analyst_Name]
RETURN ROUND ( COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Checker_Name] = a ) ) / bd, 1 ) + 0");
CalcCol("Dim_Analyst", "Check_Mins_PerDay", "#,0", BD + @"VAR a = Dim_Analyst[Analyst_Name]
RETURN ROUND ( SUMX ( FILTER ( Fact_Work, Fact_Work[Checker_Name] = a ), Fact_Work[Var_Control_Mins] ) / bd, 0 ) + 0");
CalcCol("Dim_Analyst", "True_Load_Mins", "#,0", @"Dim_Analyst[Actual_Maker_Mins_PerDay] + Dim_Analyst[Check_Mins_PerDay]");
CalcCol("Dim_Analyst", "True_Utilisation", "0%", @"DIVIDE ( Dim_Analyst[True_Load_Mins], Dim_Analyst[Capacity_Mins] )");
CalcCol("Dim_Analyst", "Reassignments_In", "#,0", @"VAR a = Dim_Analyst[Analyst_Name]
RETURN COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Maker_Name] = a && Fact_Work[Reassigned] = ""Yes"" ) ) + 0");
CalcCol("Dim_Analyst", "Capacity_Flag", "", @"IF ( Dim_Analyst[Active] <> ""Yes"", ""n/a"", IF ( Dim_Analyst[True_Load_Mins] > Dim_Analyst[Capacity_Mins], ""OVER"", ""OK"" ) )");

// ---- Dim_Slot: how many fund-days fall due in each half-hour slot
CalcCol("Dim_Slot", "Fund_Days_Due", "#,0", @"VAR s = Dim_Slot[Slot_Start_Hr]
RETURN COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Due_Slot_Hr] = s ) ) + 0");
CalcCol("Dim_Slot", "Avg_Funds_Due_Per_Day", "0.00", BD + @"RETURN ROUND ( Dim_Slot[Fund_Days_Due] / bd, 2 )");
CalcCol("Dim_Slot", "Avg_Due_NonZero", "0.00", @"IF ( Dim_Slot[Avg_Funds_Due_Per_Day] > 0, Dim_Slot[Avg_Funds_Due_Per_Day] )");
CalcCol("Dim_Slot", "Peak_Flag", "", @"VAR busy = FILTER ( ALL ( Dim_Slot ), NOT ISBLANK ( Dim_Slot[Avg_Due_NonZero] ) )
VAR p = MAX ( Dim_Slot[Peak_Percentile] )
RETURN
    IF (
        Dim_Slot[Avg_Funds_Due_Per_Day] = 0 || ISEMPTY ( busy ), ""Off-peak"",
        IF ( Dim_Slot[Avg_Funds_Due_Per_Day] >= PERCENTILEX.INC ( busy, Dim_Slot[Avg_Due_NonZero], p ), ""Peak"", ""Off-peak"" )
    )");

// ---- Data checks (the Checks sheet). Put them in a table visual on a hidden page.
Check("Chk Funds loaded", "", @"COUNTROWS ( Dim_Fund )");
Check("Chk Funds missing a default analyst", "", @"COUNTROWS ( FILTER ( Dim_Fund, ISBLANK ( Dim_Fund[Default_Analyst_Name] ) ) ) + 0");
Check("Chk Funds flagged REVIEW", "", @"COUNTROWS ( FILTER ( Dim_Fund, Dim_Fund[Feasibility_Flag] = ""REVIEW"" ) ) + 0");
Check("Chk Broker watchlist (capture actuals)", "", @"COUNTROWS ( FILTER ( Dim_Fund, Dim_Fund[Broker_Watchlist] = ""CAPTURE"" ) ) + 0");
Check("Chk Funds with estimated cut-offs", "", @"COUNTROWS ( FILTER ( Dim_Fund, Dim_Fund[Cutoff_Data_Quality] = ""Estimated"" ) ) + 0");
Check("Chk Funds not assigned to a TOP", "", @"COUNTROWS ( FILTER ( Dim_Fund, ISBLANK ( Dim_Fund[TOP_ID] ) ) ) + 0");
Check("Chk Funds never seen in Fact_Work", "", @"COUNTROWS ( FILTER ( Dim_Fund, Dim_Fund[Runs_Observed] = 0 ) ) + 0");
Check("Chk Funds later than their TOP peers", "", @"COUNTROWS ( FILTER ( Dim_Fund, LEFT ( Dim_Fund[TOP_Cutoff_Risk], 5 ) = ""Later"" ) ) + 0");
Check("Chk Milestone rows", "", @"COUNTROWS ( Fact_Milestone ) + 0");
Check("Chk Missing arrival timestamp", "", @"COUNTROWS ( FILTER ( Fact_Milestone, ISBLANK ( Fact_Milestone[Actual_Arrival_DT] ) ) ) + 0");
Check("Chk Pricing SLA breaches", "", @"COUNTROWS ( FILTER ( Fact_Milestone, Fact_Milestone[SLA_Met] = ""No"" ) ) + 0");
Check("Chk TOP deliveries on days none of its funds ran", "", @"COUNTROWS ( FILTER ( Fact_Milestone, Fact_Milestone[Funds_In_TOP] = 0 ) ) + 0");
Check("Chk Fund-days built", "", @"COUNTROWS ( Fact_Work ) + 0");
Check("Chk Fund-days not in Dim_Fund", "", @"COUNTROWS ( FILTER ( Fact_Work, ISBLANK ( RELATED ( Dim_Fund[Fund_ID] ) ) ) ) + 0");
Check("Chk Rows flagged CHECK", "", @"COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Row_Quality] = ""CHECK"" ) ) + 0");
Check("Chk Breached fund-days", "", @"COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Breached] = ""Yes"" ) ) + 0");
Check("Chk Reassignment rate", "0.0%", @"DIVIDE ( COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Reassigned] = ""Yes"" ) ), COUNTROWS ( Fact_Work ) )");
Check("Chk Recalculated fund-days", "", @"COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Recalc_Count] > 1 ) ) + 0");
Check("Chk Four-eyes breaches", "", @"COUNTROWS ( FILTER ( Fact_Work, LEFT ( Fact_Work[Self_Checked], 3 ) = ""YES"" ) ) + 0");
Check("Chk Maker names not in Dim_Analyst", "", @"COUNTROWS (
    FILTER ( VALUES ( Fact_Work[Maker_Name] ),
        NOT ISBLANK ( Fact_Work[Maker_Name] ) && NOT ( Fact_Work[Maker_Name] IN VALUES ( Dim_Analyst[Analyst_Name] ) ) )
) + 0");
Check("Chk Analysts over capacity", "", @"COUNTROWS ( FILTER ( Dim_Analyst, Dim_Analyst[Capacity_Flag] = ""OVER"" ) ) + 0");
Check("Chk Fund-days with no client cut-off", "", @"COUNTROWS ( FILTER ( Fact_Work, ISBLANK ( Fact_Work[Client_Cutoff_DT] ) ) ) + 0");
Check("Chk Wait split does not add up", "", @"COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Other_Holdup_Mins] < 0 ) ) + 0");
Check("Chk Breached fund-days with a possible cause", "", @"COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Possible_Cause] <> ""Not breached"" ) ) + 0");
Check("Chk Fund-days left out of the control workload", "", @"COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Control_Window_Status] <> ""OK"" ) ) + 0");
Check("Chk Fund-days left out of the team load", "", @"COUNTROWS ( FILTER ( Fact_Work, ISBLANK ( Fact_Work[NAV_Done_Hr] ) ) ) + 0");
Check("Chk Client cut-offs outside the chart hours", "", @"VAR h0 = MIN ( Dim_Hour[Hour_Start] )
VAR h1 = MAX ( Dim_Hour[Hour_Start] ) + 1
RETURN COUNTROWS ( FILTER ( Fact_Work, NOT ISBLANK ( Fact_Work[Client_Cutoff_Hr] ) && ( Fact_Work[Client_Cutoff_Hr] < h0 || Fact_Work[Client_Cutoff_Hr] >= h1 ) ) ) + 0");
Check("Chk Bridge rows failing the 2-minute tolerance", "", @"COUNTROWS ( FILTER ( Fact_Work, Fact_Work[Bridge_OK] = ""No"" ) ) + 0");
Check("Chk Teams with two shifts", "", @"COUNTROWS ( FILTER ( Dim_Team, Dim_Team[Shifts_In_Team] > 1 ) ) + 0");

log.Insert(0, "NAV Bottleneck v5: " + cols + " calculated columns and " + checks + " data checks processed.\n");
Info(log.ToString());
