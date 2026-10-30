// The Constants sheet as a record, looked up by label. Do not load.
// "Minutes per weightage unit" is worked out here (capacity / FTE denominator) rather than read from the sheet.
let
    fx = fxNAV,
    Raw = fx[Sheet]("Constants"),
    Rows = Table.SelectRows(Raw, each not fx[IsBlank]([CONSTANT])),
    Get = (label as text) as number =>
        let
            Hit = Table.SelectRows(Rows, each Text.Lower(Text.Trim(Text.From([CONSTANT]))) = Text.Lower(label)),
            Value = if Table.RowCount(Hit) = 0
                then error Error.Record("NAV inputs", "Constants row '" & label & "' was not found")
                else fx[Num](Hit{0}[VALUE])
        in
            if Value = null then error Error.Record("NAV inputs", "Constants row '" & label & "' has no number") else Value,
    FTE = Get("FTE denominator"),
    Capacity = Get("Daily capacity (minutes)"),
    Config = [
        FTE_Denominator = FTE,
        Daily_Capacity_Mins = Capacity,
        Mins_Per_Weightage = Capacity / FTE,
        Base_Recon_Pct = Get("Base reconciliation %"),
        ETD_Adj = Get("ETD adjustment"),
        OTC_nonCFD_Adj = Get("OTC (non-CFD) adjustment"),
        OTC_CFD_Adj = Get("OTC (CFD) adjustment"),
        PFC_Adj = Get("PFC adjustment"),
        EUC_Adj = Get("EUC adjustment"),
        Broker_Watchlist_Mins = Get("Broker slack watchlist threshold (mins)"),
        Peak_Percentile = Get("Peak percentile"),
        Thin_Slack_Mins = Get("Thin slack threshold (mins)"),
        Shift_Length_Hrs = Get("Shift length (hrs)")
    ]
in
    Config
