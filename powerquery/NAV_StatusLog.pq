// Status log, one row per status change. Staging query: do not load (it is large).
// Reads every .csv / .xlsx file in NAV_StatusLogFolder, or the Status_Log sheet when the folder parameter is empty.
// Each file needs these headers: Log_NAV_Date, Log_Process_Date, Log_Fund_ID, Log_Status, Log_Timestamp, Log_Person_Name.
let
    fx = fxNAV,
    Cols = {"Log_NAV_Date", "Log_Process_Date", "Log_Fund_ID", "Log_Status", "Log_Timestamp", "Log_Person_Name"},
    ReadFile = (content as binary, ext as text) as table =>
        let
            Raw = if ext = ".csv" or ext = ".txt"
                then Table.PromoteHeaders(
                    Csv.Document(content, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
                    [PromoteAllScalars = true])
                else
                    let
                        Book = Excel.Workbook(content, true, true),
                        Sheets = Table.SelectRows(Book, each [Kind] = "Sheet"),
                        Named = Table.SelectRows(Sheets, each [Item] = "Status_Log"),
                        Pick = if Table.RowCount(Named) > 0 then Named{0}[Data] else Sheets{0}[Data]
                    in
                        Pick
        in
            Table.SelectColumns(Raw, Cols, MissingField.Error),
    FromFolder = () =>
        let
            Files = Folder.Files(NAV_StatusLogFolder),
            Keep = Table.SelectRows(Files, each
                not Text.StartsWith([Name], "~$")
                and List.Contains({".csv", ".txt", ".xlsx", ".xlsm", ".xlsb"}, Text.Lower([Extension]))),
            Ordered = Table.Sort(Keep, {{"Folder Path", Order.Ascending}, {"Name", Order.Ascending}}),
            Tables = List.Transform(Table.ToRecords(Ordered), each ReadFile([Content], Text.Lower([Extension])))
        in
            Table.Combine(Tables),
    FromSheet = () => Table.SelectColumns(fx.Sheet("Status_Log"), Cols, MissingField.Error),
    Source = if fx.IsBlank(NAV_StatusLogFolder) then FromSheet() else FromFolder(),
    Typed = Table.TransformColumns(Source, {
        {"Log_NAV_Date", fx.ToDate, type nullable date},
        {"Log_Process_Date", fx.ToDate, type nullable date},
        {"Log_Fund_ID", fx.Txt, type nullable text},
        {"Log_Status", fx.Txt, type nullable text},
        {"Log_Timestamp", fx.ToDateTime, type nullable datetime},
        {"Log_Person_Name", fx.Txt, type nullable text}}),
    FromDate = if fx.IsBlank(NAV_LoadFromDate) then null else Date.FromText(Text.Trim(NAV_LoadFromDate), [Format = "yyyy-MM-dd"]),
    NonBlank = Table.SelectRows(Typed, each [Log_Status] <> null and [Log_NAV_Date] <> null
        and [Log_Process_Date] <> null and [Log_Fund_ID] <> null
        and (FromDate = null or [Log_Process_Date] >= FromDate)),
    Indexed = Table.AddIndexColumn(NonBlank, "Log_Row", 1, 1, Int64.Type),
    WithKey = Table.AddColumn(Indexed, "Status_Key", each Text.Lower([Log_Status]), type text),
    WithFund = Table.AddColumn(WithKey, "Fund_Key", each Text.Upper([Log_Fund_ID]), type text)
in
    WithFund
