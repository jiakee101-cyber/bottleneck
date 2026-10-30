// Dim_Slot: half-hour due slots. Fund_Days_Due, Avg_Funds_Due_Per_Day, Avg_Due_NonZero and Peak_Flag are
// DAX calculated columns (v5 script); Peak_Percentile carries Constants "Peak percentile" for them.
let
    fx = fxNAV,
    Cfg = NAV_Config,
    Raw = NAV_Inputs[Slot],
    Starts = Table.TransformColumns(Raw, {{"Slot_Start_Hr", fx[Num]}}),
    Indexed = Table.AddIndexColumn(Starts, "Slot_Order", 1, 1, Int64.Type),
    Label = (h as number) as text =>
        Text.PadStart(Text.From(Number.RoundDown(h)), 2, "0") & ":" & Text.PadStart(Text.From(fx[R0](Number.Mod(h, 1) * 60)), 2, "0"),
    WithEnd = Table.AddColumn(Indexed, "Slot_End_Hr", each [Slot_Start_Hr] + 0.5, type number),
    WithLabel = Table.AddColumn(WithEnd, "Slot_Label", each Label([Slot_Start_Hr]) & "–" & Label([Slot_End_Hr]), type text),
    WithPct = Table.AddColumn(WithLabel, "Peak_Percentile", each Cfg[Peak_Percentile], type number),
    Ordered = Table.SelectColumns(WithPct, {"Slot_Start_Hr", "Slot_End_Hr", "Slot_Label", "Slot_Order", "Peak_Percentile"}),
    Typed = Table.TransformColumnTypes(Ordered, {{"Slot_Start_Hr", type number}})
in
    Typed
