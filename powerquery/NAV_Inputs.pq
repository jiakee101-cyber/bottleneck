// The input sheets of the inputs workbook, as a record of tables (input columns only). Do not load.
// Every workbook read happens here (and in NAV_Config / NAV_StatusLog / NAV_MilestoneRaw), so the calculation
// queries only reference other queries. That keeps Power BI's privacy firewall ("rebuild this data combination") happy.
let
    fx = fxNAV,
    Inputs = [
        Team = fx[Inputs]("Dim_Team", {"Team_ID", "Team_Name", "Shift_Start", "Shifts_In_Team", "Daily_Capacity_Mins"}),
        Signoff = fx[Inputs]("Dim_Signoff", {"Signoff_Model", "Planned_Tail_Mins"}),
        Fund = fx[Inputs]("Dim_Fund", {"Fund_ID", "Fund_Name", "Client_ID", "Client_Name", "Strategic_Client", "Team_ID",
            "Default_Analyst_Name", "Weightage", "ETD", "OTC_nonCFD", "OTC_CFD", "PFC", "EUC", "Has_Custody_Process",
            "Has_TA_Process", "Has_Broker_Process", "Custody_Cutoff", "TA_Cutoff", "Broker_ETA", "Pricing_Cutoff", "TOP_ID",
            "Client_Cutoff", "NAV_Deadline", "Signoff_Model", "Cutoff_Data_Quality"}),
        TOP = fx[Inputs]("Dim_TOP", {"TOP_ID", "TOP_Name", "Pricing_Supplier"}),
        Analyst = fx[Inputs]("Dim_Analyst", {"Analyst_Name", "Team_ID", "Active"}),
        Slot = fx[Inputs]("Dim_Slot", {"Slot_Start_Hr"})
    ]
in
    Inputs
