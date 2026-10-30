// Dim_Team: inputs from the sheet, shift hours worked out here.
let
    fx = fxNAV,
    Cfg = NAV_Config,
    Raw = NAV_Inputs[Team],
    Rows = List.Transform(Table.ToRecords(Raw), (r) =>
        let
            Start = fx[Hr](r[Shift_Start])
        in
            [
                Team_ID = fx[Txt](r[Team_ID]),
                Team_Name = fx[Txt](r[Team_Name]),
                Shift_Start = fx[ToTime](r[Shift_Start]),
                Shifts_In_Team = fx[Num](r[Shifts_In_Team]),
                Daily_Capacity_Mins = fx[Num](r[Daily_Capacity_Mins]),
                Shift_Start_Hr = Start,
                Shift_End_Hr = Start + Cfg[Shift_Length_Hrs]
            ]),
    Result = Table.FromRecords(Rows, type table [Team_ID = nullable text, Team_Name = nullable text,
        Shift_Start = nullable time, Shifts_In_Team = nullable number, Daily_Capacity_Mins = nullable number,
        Shift_Start_Hr = number, Shift_End_Hr = number])
in
    Result
