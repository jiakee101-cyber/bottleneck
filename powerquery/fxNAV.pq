// Helper functions shared by the NAV queries. Do not load.
// They reproduce the Excel behaviour the v4.5 formulas relied on:
// ROUND is half away from zero, text comparisons ignore case, an empty cut-off reads as 00:00.
let
    IsBlank = (v as any) as logical => v = null or (v is text and Text.Trim(v) = ""),
    Txt = (v as any) as nullable text => if IsBlank(v) then null else Text.Trim(Text.From(v)),
    Key = (v as any) as nullable text => if IsBlank(v) then null else Text.Upper(Text.Trim(Text.From(v))),
    Same = (a as any, b as any) as logical =>
        (if a = null then "" else Text.Upper(Text.Trim(Text.From(a)))) = (if b = null then "" else Text.Upper(Text.Trim(Text.From(b)))),
    IsYes = (v as any) as logical => Key(v) = "YES",
    IsNo = (v as any) as logical => Key(v) = "NO",
    Num = (v as any) as nullable number =>
        if IsBlank(v) then null else if v is number then v else try Number.From(v) otherwise null,
    N = (v as any) as number => let x = if v is number then v else null in if x = null then 0 else x,
    ToDate = (v as any) as nullable date =>
        if IsBlank(v) then null
        else if v is date then v
        else if v is datetime then DateTime.Date(v)
        else if v is number then Date.From(v)
        else try Date.From(v) otherwise try DateTime.Date(DateTime.From(v)) otherwise null,
    ToDateTime = (v as any) as nullable datetime =>
        if IsBlank(v) then null
        else if v is datetime then v
        else if v is date then DateTime.From(v)
        else if v is number then DateTime.From(v)
        else try DateTime.From(v) otherwise null,
    ToTime = (v as any) as nullable time =>
        if IsBlank(v) then null
        else if v is time then v
        else if v is datetime then DateTime.Time(v)
        else if v is duration then #time(0, 0, 0) + v
        else if v is number then Time.From(Number.Mod(v, 1))
        else try Time.From(v) otherwise null,
    // HOUR(x) + MINUTE(x)/60; an empty cell counts as 00:00, as in Excel.
    Hr = (v as any) as number => let t = ToTime(v) in if t = null then 0 else Time.Hour(t) + Time.Minute(t) / 60,
    R = (x as nullable number, digits as number) as nullable number =>
        if x = null then null else Number.Round(x, digits, RoundingMode.AwayFromZero),
    R0 = (x as nullable number) as nullable number => if x = null then null else Number.Round(x, 0, RoundingMode.AwayFromZero),
    Floor = (x as nullable number, step as number) as nullable number => if x = null then null else Number.RoundDown(x / step) * step,
    Mins = (a as nullable datetime, b as nullable datetime) as nullable number =>
        if a = null or b = null then null else Duration.TotalMinutes(a - b),
    // Hours from midnight of day d to datetime x (can exceed 24 or be negative).
    HrsFrom = (x as nullable datetime, d as nullable date) as nullable number =>
        if x = null or d = null then null else Duration.TotalHours(x - DateTime.From(d)),
    // Hour of day of a datetime, (x - INT(x)) * 24 in Excel.
    HrOfDay = (x as nullable datetime) as nullable number =>
        if x = null then null else Duration.TotalHours(x - DateTime.From(DateTime.Date(x))),
    AtHr = (d as nullable date, hr as nullable number) as nullable datetime =>
        if d = null or hr = null then null else DateTime.From(d) + #duration(0, 0, 0, hr * 3600),
    AddMins = (x as nullable datetime, m as nullable number) as nullable datetime =>
        if x = null or m = null then null else x + #duration(0, 0, 0, m * 60),
    // Record keyed by upper-cased text: first value wins, empty keys are skipped (VLOOKUP behaviour).
    LookupOf = (keys as list, values as list) as record =>
        let
            Pairs = Table.FromColumns({List.Transform(keys, Key), values}, {"K", "V"}),
            Kept = Table.Distinct(Table.Buffer(Table.SelectRows(Pairs, each [K] <> null)), {"K"})
        in
            Record.FromList(Kept[V], Kept[K]),
    Find = (lookup as record, key as any) as any =>
        let k = Key(key) in if k = null then null else Record.FieldOrDefault(lookup, k, null),
    // Read one worksheet of the inputs workbook, first row as headers.
    Sheet = (name as text) as table =>
        let
            Book = Excel.Workbook(File.Contents(NAV_InputWorkbook), true, true),
            Found = Table.SelectRows(Book, each [Kind] = "Sheet" and [Item] = name),
            Data = if Table.RowCount(Found) = 0
                then error Error.Record("NAV inputs", "Sheet '" & name & "' was not found in " & NAV_InputWorkbook)
                else Found{0}[Data]
        in
            Data,
    // Keep the named input columns and drop rows whose first key column is empty.
    Inputs = (name as text, columns as list) as table =>
        let
            Selected = Table.SelectColumns(Sheet(name), columns, MissingField.Error),
            First = columns{0},
            NonBlank = Table.SelectRows(Selected, each not IsBlank(Record.Field(_, First)))
        in
            NonBlank
in
    [
        IsBlank = IsBlank, Txt = Txt, Key = Key, Same = Same, IsYes = IsYes, IsNo = IsNo,
        Num = Num, N = N, ToDate = ToDate, ToDateTime = ToDateTime, ToTime = ToTime, Hr = Hr,
        R = R, R0 = R0, Floor = Floor, Mins = Mins, HrsFrom = HrsFrom, HrOfDay = HrOfDay,
        AtHr = AtHr, AddMins = AddMins, LookupOf = LookupOf, Find = Find, Sheet = Sheet, Inputs = Inputs
    ]
