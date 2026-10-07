"""Single source for the Power BI layer: measures, relationships, sort orders and the visual map."""

# TOP-days that at least one in-view fund-day depended on. Carries the date, client, fund and TOP
# filters (all on Fact_Work / Dim_Fund / Dim_TOP) across to Fact_Milestone without a date table.
TOP_DAYS = "TREATAS ( SUMMARIZE ( Fact_Work, Fact_Work[Process_Date], Fact_Work[TOP_ID] ), " \
           "Fact_Milestone[Process_Date], Fact_Milestone[TOP_ID] )"


def by_wait_group(e):
    return f"""
VAR g = SELECTEDVALUE ( Dim_WaitGroup[Wait_Group] )
RETURN
    SWITCH (
        g,
        "Broker-dependent", CALCULATE ( {e}, KEEPFILTERS ( Fact_Work[Broker_Dependent] = "Yes" ) ),
        "Not broker-dependent", CALCULATE ( {e}, KEEPFILTERS ( Fact_Work[Broker_Dependent] = "No" ) ),
        "Thin custody slack", CALCULATE ( {e}, KEEPFILTERS ( Fact_Work[Custody_Slack_Group] = "Thin custody slack" ) ),
        "Ample custody slack", CALCULATE ( {e}, KEEPFILTERS ( Fact_Work[Custody_Slack_Group] = "Ample custody slack" ) ),
        {e}
    )"""


def by_supplier(pricing, custody, ta, broker):
    return f"""
VAR s = SELECTEDVALUE ( Dim_SupplierType[Supplier_Type] )
RETURN
    SWITCH (
        s,
        "Pricing (TOP)", {pricing},
        "Custody", {custody},
        "TA", {ta},
        "Broker (dependent)", {broker}
    )"""


F0 = "0"
FP0 = "0%"
FP1 = "0.0%"
FN = "#,0"

MEASURES = [
    # ------------------------------------------------------------------ base
    dict(table="Fact_Work", name="Fund-Days", folder="0 Base", fmt=FN,
         desc="Fund-days in view (one Fact_Work row per fund per NAV date per process date).",
         dax="COUNTROWS ( Fact_Work )"),
    dict(table="Fact_Work", name="Breached Fund-Days", folder="0 Base", fmt=FN,
         desc="Fund-days delivered after the client cut-off.",
         dax='CALCULATE ( COUNTROWS ( Fact_Work ), KEEPFILTERS ( Fact_Work[Breached] = "Yes" ) )'),
    dict(table="Fact_Work", name="Breach Rate", folder="0 Base", fmt=FP1,
         desc="Breached fund-days / fund-days.",
         dax="DIVIDE ( [Breached Fund-Days], [Fund-Days] )"),
    dict(table="Dim_Fund", name="Funds", folder="0 Base", fmt=FN,
         desc="Funds assigned (design view: not limited by the date slicer).",
         dax="DISTINCTCOUNT ( Dim_Fund[Fund_ID] )"),
    dict(table="Dim_Fund", name="Clients", folder="0 Base", fmt=FN,
         desc="Distinct clients.",
         dax="DISTINCTCOUNT ( Dim_Fund[Client_ID] )"),
    dict(table="Fact_Work", name="Date Range Label", folder="0 Base",
         desc="Header text, e.g. 3–28 Aug 2026.",
         dax="""
VAR d0 = MIN ( Fact_Work[Process_Date] )
VAR d1 = MAX ( Fact_Work[Process_Date] )
RETURN
    IF (
        ISBLANK ( d0 ), "No data",
        IF (
            d0 = d1, FORMAT ( d0, "dd mmm yyyy" ),
            IF (
                YEAR ( d0 ) = YEAR ( d1 ) && MONTH ( d0 ) = MONTH ( d1 ),
                FORMAT ( d0, "d" ),
                FORMAT ( d0, "d mmm yyyy" )
            ) & "–" & FORMAT ( d1, "d mmm yyyy" )
        )
    )"""),
    dict(table="Dim_Fund", name="Client Label", folder="0 Base",
         desc="Header text: All (n), the client name, or n selected.",
         dax="""
VAR n = DISTINCTCOUNT ( Dim_Fund[Client_Name] )
RETURN
    IF (
        NOT ISFILTERED ( Dim_Fund[Client_Name] ), "All (" & n & ")",
        IF ( n = 1, SELECTEDVALUE ( Dim_Fund[Client_Name] ), n & " selected" )
    )"""),

    # ------------------------------------------------------------------ page 1 KPIs
    dict(table="Dim_TOP", name="Largest TOP", folder="1 Supplier Risk\\KPIs",
         desc="TOP with the most funds in view (ties: lowest TOP_ID).",
         dax="""
VAR t =
    TOPN ( 1, FILTER ( VALUES ( Dim_TOP[TOP_ID] ), [Funds] > 0 ), [Funds], DESC, Dim_TOP[TOP_ID], ASC )
RETURN
    MINX ( t, Dim_TOP[TOP_ID] )"""),
    dict(table="Dim_TOP", name="Largest TOP Funds", folder="1 Supplier Risk\\KPIs", fmt=FN,
         dax="""
VAR t = [Largest TOP]
RETURN CALCULATE ( [Funds], Dim_TOP[TOP_ID] = t )"""),
    dict(table="Dim_TOP", name="Largest TOP Clients", folder="1 Supplier Risk\\KPIs", fmt=FN,
         dax="""
VAR t = [Largest TOP]
RETURN CALCULATE ( [Clients], Dim_TOP[TOP_ID] = t )"""),
    dict(table="Dim_TOP", name="Largest TOP Share", folder="1 Supplier Risk\\KPIs", fmt=FP0,
         desc="Largest TOP's funds as a share of all funds in view.",
         dax="DIVIDE ( [Largest TOP Funds], [Funds] )"),
    dict(table="Dim_TOP", name="Largest TOP Subtitle", folder="1 Supplier Risk\\KPIs",
         desc="e.g. 21% of funds, 5 clients",
         dax='FORMAT ( [Largest TOP Share], "0%" ) & " of funds, " & [Largest TOP Clients] & " clients"'),
    dict(table="Fact_Milestone", name="TOP-Days Scored", folder="1 Supplier Risk\\KPIs", fmt=FN,
         desc="TOP deliveries scored against a binding cut-off, on TOP-days an in-view fund depended on.",
         dax=f'CALCULATE ( COUNTROWS ( Fact_Milestone ), KEEPFILTERS ( {TOP_DAYS} ), '
             f'KEEPFILTERS ( Fact_Milestone[SLA_Met] IN {{ "Yes", "No" }} ) )'),
    dict(table="Fact_Milestone", name="TOP-Days Late", folder="1 Supplier Risk\\KPIs", fmt=FN,
         dax=f'CALCULATE ( COUNTROWS ( Fact_Milestone ), KEEPFILTERS ( {TOP_DAYS} ), '
             f'KEEPFILTERS ( Fact_Milestone[SLA_Met] = "No" ) )'),
    dict(table="Fact_Milestone", name="TOP Late Rate", folder="1 Supplier Risk\\KPIs", fmt=FP0,
         desc="TOP-days arriving after the binding cut-off.",
         dax="DIVIDE ( [TOP-Days Late], [TOP-Days Scored] )"),
    dict(table="Fact_Work", name="Breached Fund-Days Subtitle", folder="1 Supplier Risk\\KPIs",
         desc="e.g. 9.7% of 1,800 fund-days",
         dax='FORMAT ( [Breach Rate], "0.0%" ) & " of " & FORMAT ( [Fund-Days], "#,0" ) & " fund-days"'),
    dict(table="Fact_Work", name="Breaches Pricing Late", folder="1 Supplier Risk\\KPIs", fmt=FN,
         desc="Breached fund-days where pricing arrived after the fund's own PSA cut-off.",
         dax='CALCULATE ( [Breached Fund-Days], KEEPFILTERS ( Fact_Work[Pricing_Late_For_This_Fund] = "Yes" ) )'),
    dict(table="Fact_Work", name="Breaches Pricing Late %", folder="1 Supplier Risk\\KPIs", fmt=FP0,
         dax="DIVIDE ( [Breaches Pricing Late], [Breached Fund-Days] )"),
    dict(table="Fact_Work", name="Queue Share of Wait", folder="1 Supplier Risk\\KPIs", fmt=FP0,
         desc="Share of the wait after pricing spent behind the maker's other funds (reconstructed). Capacity signal.",
         dax="DIVIDE ( SUM ( Fact_Work[Queue_Wait_Mins] ), SUM ( Fact_Work[Wait_After_Pricing_Mins] ) )"),
    dict(table="Fact_Work", name="Own Recon Share of Wait", folder="1 Supplier Risk\\KPIs", fmt=FP0,
         desc="Share of the wait the same maker spent reconciling this fund, up to its recon budget.",
         dax="DIVIDE ( SUM ( Fact_Work[Own_Recon_Mins] ), SUM ( Fact_Work[Wait_After_Pricing_Mins] ) )"),
    dict(table="Fact_Work", name="Other Holdup Share of Wait", folder="1 Supplier Risk\\KPIs", fmt=FP0,
         desc="Share of the wait not explained by other funds or the recon budget: data, breaks, recon over budget.",
         dax="DIVIDE ( SUM ( Fact_Work[Other_Holdup_Mins] ), SUM ( Fact_Work[Wait_After_Pricing_Mins] ) )"),

    # ------------------------------------------------------------------ page 1 exposure
    dict(table="Dim_Fund", name="Funds Label", folder="1 Supplier Risk\\Exposure",
         desc="Data label: 19 funds · 5 clients",
         dax='[Funds] & " funds · " & [Clients] & " clients"'),
    dict(table="Dim_TOP", name="Exposure Bar Color", folder="1 Supplier Risk\\Exposure",
         desc="Conditional formatting (field value) for the exposure bars: red for the largest TOP.",
         dax="""
VAR largest = CALCULATE ( [Largest TOP], ALLSELECTED ( Dim_TOP ) )
RETURN IF ( SELECTEDVALUE ( Dim_TOP[TOP_ID] ) = largest, "#C8423B", "#C9D1DB" )"""),

    # ------------------------------------------------------------------ page 1 supplier table
    dict(table="Dim_Fund", name="Supplier Funds", folder="1 Supplier Risk\\Dependency Table", fmt=FN,
         dax=by_supplier(
             'CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[TOP_ID] <> "" ) )',
             'CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Has_Custody_Process] = "Yes" ) )',
             'CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Has_TA_Process] = "Yes" ) )',
             'CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Broker_Dependent] = "Yes" ) )')),
    dict(table="Dim_Fund", name="Supplier Clients", folder="1 Supplier Risk\\Dependency Table", fmt=FN,
         dax=by_supplier(
             'CALCULATE ( [Clients], KEEPFILTERS ( Dim_Fund[TOP_ID] <> "" ) )',
             'CALCULATE ( [Clients], KEEPFILTERS ( Dim_Fund[Has_Custody_Process] = "Yes" ) )',
             'CALCULATE ( [Clients], KEEPFILTERS ( Dim_Fund[Has_TA_Process] = "Yes" ) )',
             'CALCULATE ( [Clients], KEEPFILTERS ( Dim_Fund[Broker_Dependent] = "Yes" ) )')),
    dict(table="Dim_Fund", name="Median Slack Mins", folder="1 Supplier Risk\\Dependency Table", fmt=F0,
         desc="Median minutes between the supplier's cut-off and the pricing gate. Pricing is 0 by definition.",
         dax=by_supplier(
             'IF ( [Supplier Funds] > 0, 0 )',
             'MEDIAN ( Dim_Fund[Slack_Custody_Num] )',
             'MEDIAN ( Dim_Fund[Slack_TA_Num] )',
             'MEDIAN ( Dim_Fund[Slack_Broker_Num] )')),
    dict(table="Dim_Fund", name="Median Slack Label", folder="1 Supplier Risk\\Dependency Table",
         desc="0 min / 5.1 h",
         dax="""
VAR m = [Median Slack Mins]
RETURN
    IF ( ISBLANK ( m ), BLANK (), IF ( ABS ( m ) < 60, FORMAT ( m, "0" ) & " min", FORMAT ( m / 60, "0.0" ) & " h" ) )"""),
    dict(table="Dim_Fund", name="Thin Slack Funds", folder="1 Supplier Risk\\Dependency Table", fmt=FN,
         desc="Funds whose slack is at or below Constants!B17 (0 = zero tolerance). Pricing: every fund.",
         dax=by_supplier(
             '[Supplier Funds]',
             'CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Thin_Custody_Slack] = "Yes" ) ) + 0',
             'CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Thin_TA_Slack] = "Yes" ) ) + 0',
             'CALCULATE ( [Funds], KEEPFILTERS ( Dim_Fund[Thin_Broker_Slack] = "Yes" ) ) + 0')),
    dict(table="Dim_Fund", name="Thin Slack Label", folder="1 Supplier Risk\\Dependency Table",
         desc="all funds / 23 funds",
         dax="""
IF (
    SELECTEDVALUE ( Dim_SupplierType[Supplier_Type] ) = "Pricing (TOP)", "all funds",
    IF ( ISBLANK ( [Thin Slack Funds] ), BLANK (), [Thin Slack Funds] & " funds" )
)"""),
    dict(table="Dim_Fund", name="Thin Slack Color", folder="1 Supplier Risk\\Dependency Table",
         desc="Font colour for Thin Slack Label and Median Slack Label: red for pricing, amber when any fund is thin.",
         dax="""
IF (
    SELECTEDVALUE ( Dim_SupplierType[Supplier_Type] ) = "Pricing (TOP)", "#C8423B",
    IF ( [Thin Slack Funds] > 0, "#E8A33D", "#1F2933" )
)"""),

    # ------------------------------------------------------------------ page 1 pricing delay
    dict(table="Fact_Milestone", name="Late Hours", folder="1 Supplier Risk\\Pricing Delay", fmt="0.0",
         desc="Hours the TOP file arrived after its binding cut-off, summed over the TOP-days in view ('created').",
         dax=f"DIVIDE ( CALCULATE ( SUM ( Fact_Milestone[Late_Mins] ), KEEPFILTERS ( {TOP_DAYS} ) ), 60 )"),
    dict(table="Fact_Milestone", name="Late Hours Label", folder="1 Supplier Risk\\Pricing Delay",
         dax='FORMAT ( [Late Hours] + 0, "0.0" ) & "h"'),
    dict(table="Fact_Work", name="Breached Fund-Days When Late", folder="1 Supplier Risk\\Pricing Delay", fmt=FN,
         desc="Breached fund-days on days the fund's TOP missed its binding cut-off ('reached the funds').",
         dax='CALCULATE ( [Breached Fund-Days], KEEPFILTERS ( Fact_Work[TOP_SLA_Met] = "No" ) ) + 0'),

    # ------------------------------------------------------------------ page 1 waiting
    dict(table="Fact_Work", name="Avg Queue Wait", folder="1 Supplier Risk\\Waiting", fmt=F0,
         desc="Avg minutes per fund-day behind the maker's other funds (purple). Group-aware via Dim_WaitGroup.",
         dax=by_wait_group("AVERAGE ( Fact_Work[Queue_Wait_Mins] )")),
    dict(table="Fact_Work", name="Avg Own Recon Wait", folder="1 Supplier Risk\\Waiting", fmt=F0,
         desc="Avg minutes per fund-day the same maker spent reconciling this fund, up to its recon budget (blue). Group-aware.",
         dax=by_wait_group("AVERAGE ( Fact_Work[Own_Recon_Mins] )")),
    dict(table="Fact_Work", name="Avg Other Holdup Wait", folder="1 Supplier Risk\\Waiting", fmt=F0,
         desc="Avg minutes per fund-day not explained by other funds or the recon budget (amber). Group-aware.",
         dax=by_wait_group("AVERAGE ( Fact_Work[Other_Holdup_Mins] )")),
    dict(table="Fact_Work", name="Wait Fund-Days", folder="1 Supplier Risk\\Waiting", fmt=FN,
         desc="Fund-days with a measured wait (pricing arrival logged). Group-aware.",
         dax=by_wait_group("COUNT ( Fact_Work[Wait_After_Pricing_Mins] )")),
    dict(table="Fact_Work", name="Wait n Label", folder="1 Supplier Risk\\Waiting",
         desc="n=640",
         dax='"n=" & FORMAT ( [Wait Fund-Days] + 0, "#,0" )'),

    # ------------------------------------------------------------------ page 2 KPIs
    dict(table="Fact_Work", name="Funds In View", folder="2 Fund Level\\KPIs", fmt=FN,
         dax="DISTINCTCOUNT ( Fact_Work[Fund_ID] )"),
    dict(table="Fact_Work", name="Breached Funds", folder="2 Fund Level\\KPIs", fmt=FN,
         dax='CALCULATE ( DISTINCTCOUNT ( Fact_Work[Fund_ID] ), KEEPFILTERS ( Fact_Work[Breached] = "Yes" ) ) + 0'),
    dict(table="Fact_Work", name="Client Sign-off Funds", folder="2 Fund Level\\KPIs", fmt=FN,
         dax='CALCULATE ( DISTINCTCOUNT ( Fact_Work[Fund_ID] ), KEEPFILTERS ( Fact_Work[Signoff_Model] = "Client" ) ) + 0'),
    dict(table="Fact_Work", name="Funds In View Subtitle", folder="2 Fund Level\\KPIs",
         desc="4 breached, 3 client sign-off",
         dax='[Breached Funds] & " breached, " & [Client Sign-off Funds] & " client sign-off"'),
    dict(table="Fact_Work", name="Fund Filter Label", folder="2 Fund Level\\KPIs",
         desc="Header text: All (n), the fund, or n selected.",
         dax="""
VAR n = DISTINCTCOUNT ( Fact_Work[Fund_ID] )
RETURN
    IF (
        ISFILTERED ( Fact_Work[Fund_ID] ) || ISFILTERED ( Dim_Fund[Fund_ID] ),
        IF ( n = 1, SELECTEDVALUE ( Fact_Work[Fund_ID] ), n & " selected" ),
        "All (" & n & ")"
    )"""),
    dict(table="Fact_Work", name="Avg Wait After Pricing", folder="2 Fund Level\\KPIs", fmt=F0,
         desc="Avg minutes from pricing arrived to NAV started.",
         dax="AVERAGE ( Fact_Work[Wait_After_Pricing_Mins] )"),
    dict(table="Fact_Work", name="Avg NAV To Controlled", folder="2 Fund Level\\KPIs", fmt=F0,
         desc="Avg minutes FA spent: NAV start to Controlled (to FA signed off for client sign-off funds).",
         dax="AVERAGE ( Fact_Work[NAV_Span_Mins] )"),
    dict(table="Fact_Work", name="Avg Controlled To Delivered", folder="2 Fund Level\\KPIs", fmt=F0,
         desc="Avg minutes after FA finished: NAV_End to Delivered.",
         dax="AVERAGE ( Fact_Work[Controlled_To_Delivered_Mins] )"),
    dict(table="Fact_Work", name="Avg Headroom", folder="2 Fund Level\\KPIs", fmt=F0,
         desc="Avg minutes delivered before the client cut-off (negative = after).",
         dax="AVERAGE ( Fact_Work[Headroom_At_Delivery_Mins] )"),

    # ------------------------------------------------------------------ page 2 timeline
    dict(table="Fact_Work", name="Bar Offset", folder="2 Fund Level\\Timeline", fmt="0.00",
         desc="Transparent first segment (hours of day). Set the X axis start to 9.",
         dax="MIN ( Fact_Work[Bar_Offset_Hr] )"),
    dict(table="Fact_Work", name="Bar Waiting After Pricing", folder="2 Fund Level\\Timeline", fmt="0.00",
         dax="SUM ( Fact_Work[Bar_Wait_Hr] )"),
    dict(table="Fact_Work", name="Bar NAV To Controlled", folder="2 Fund Level\\Timeline", fmt="0.00",
         dax="SUM ( Fact_Work[Bar_NAV_Hr] )"),
    dict(table="Fact_Work", name="Bar Controlled To FA Signed Off", folder="2 Fund Level\\Timeline", fmt="0.00",
         dax="SUM ( Fact_Work[Bar_Control_Hr] )"),
    dict(table="Fact_Work", name="Bar FA Signed Off To Delivered", folder="2 Fund Level\\Timeline", fmt="0.00",
         dax="SUM ( Fact_Work[Bar_Tail_Hr] )"),
    dict(table="Fact_Work", name="NAV Start Hr", folder="2 Fund Level\\Timeline", fmt="0.00",
         desc="Sort the timeline's Y axis by this, ascending.",
         dax="MIN ( Fact_Work[Start_Hr] )"),
    dict(table="Fact_Work", name="Pricing Cutoff Hr", folder="2 Fund Level\\Timeline", fmt="0.00",
         dax="MIN ( Fact_Work[Fund_Pricing_Cutoff_Hr] )"),
    dict(table="Fact_Work", name="Pricing Arrived Hr", folder="2 Fund Level\\Timeline", fmt="0.00",
         dax="MIN ( Fact_Work[Arrival_Hr] )"),
    dict(table="Fact_Work", name="Client Cutoff Hr", folder="2 Fund Level\\Timeline", fmt="0.00",
         dax="MIN ( Fact_Work[Client_Cutoff_Hr] )"),

    # ------------------------------------------------------------------ page 2 selected fund
    dict(table="Fact_Work", name="Selected Fund Title", folder="2 Fund Level\\Selected Fund",
         dax='"Selected fund — " & IF ( HASONEVALUE ( Fact_Work[Fund_ID] ), VALUES ( Fact_Work[Fund_ID] ), "select one" )'),
    dict(table="Fact_Work", name="Detail Value", folder="2 Fund Level\\Selected Fund",
         desc="Value column of the selected-fund table (rows from Dim_DetailRow).",
         dax="""
VAR r = SELECTEDVALUE ( Dim_DetailRow[Detail] )
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
VAR isClient = SELECTEDVALUE ( Fact_Work[Signoff_Model] ) = "Client"
RETURN
    IF (
        NOT HASONEVALUE ( Fact_Work[Fund_ID] ), BLANK (),
        SWITCH (
            r,
            "Pricing cut-off", IF ( ISBLANK ( pc ), "–", FORMAT ( pc / 24, "hh:mm" ) ),
            "Pricing arrived", IF ( ISBLANK ( pa ), "not logged",
                FORMAT ( pa, "hh:mm" ) & IF ( ISBLANK ( vp ), "", " (" & FORMAT ( vp, "+0;-0;0" ) & " min)" ) ),
            "NAV started", IF ( ISBLANK ( ns ), "–", FORMAT ( ns, "hh:mm" ) ),
            "Controlled", IF ( isClient, "n/a — client sign-off", IF ( ISBLANK ( ct ), "–", FORMAT ( ct, "hh:mm" ) ) ),
            "FA signed off", IF ( ISBLANK ( fa ), "–", FORMAT ( fa, "hh:mm" ) ),
            "Delivered", IF ( ISBLANK ( dl ), "–", FORMAT ( dl, "hh:mm" ) ),
            "Client cut-off", IF ( ISBLANK ( cc ), "–", FORMAT ( cc / 24, "hh:mm" ) ),
            "Headroom", IF ( ISBLANK ( hd ), "–", FORMAT ( hd, "0;-0;0" ) & " min" ),
            "Waited after pricing", IF ( ISBLANK ( wt ), "–", FORMAT ( wt, "0" ) & " min" ),
            "NAV to Controlled", IF ( ISBLANK ( nv ), "–", FORMAT ( nv, "0" ) & " min" )
        )
    )"""),
    dict(table="Fact_Work", name="Detail Font Color", folder="2 Fund Level\\Selected Fund",
         desc="Conditional font colour for the selected-fund table: red headroom when negative.",
         dax="""
IF (
    SELECTEDVALUE ( Dim_DetailRow[Detail] ) = "Headroom" && MIN ( Fact_Work[Headroom_At_Delivery_Mins] ) < 0,
    "#C8423B", "#1F2933"
)"""),
]

RELATIONSHIPS = [
    ("Fact_Work", "Fund_ID", "Dim_Fund", "Fund_ID", "Fund attributes and the client slicer filter the fund-days."),
    ("Dim_Fund", "TOP_ID", "Dim_TOP", "TOP_ID", "A TOP filters its funds, and through them their fund-days."),
    ("Fact_Milestone", "TOP_ID", "Dim_TOP", "TOP_ID", "TOP axis on the pricing-delay visual."),
    ("Fact_Work", "Possible_Cause", "Dim_Cause", "Possible_Cause", "Legend order on the cause chart."),
]

SORT_BY = [
    ("Dim_Cause", "Possible_Cause", "Cause_Order"),
    ("Dim_SupplierType", "Supplier_Type", "Type_Order"),
    ("Dim_WaitGroup", "Wait_Group", "Group_Order"),
    ("Dim_DetailRow", "Detail", "Detail_Order"),
]

P1, P2 = "1 Supplier Concentration Risk", "2 Fund Level"
VISUALS = [
    (P1, "Header: Date", "Card / text", "", "[Date Range Label]", "Slicer: Fact_Work[Process_Date] (between)", ""),
    (P1, "Header: Client", "Card / text", "", "[Client Label]", "Slicer: Dim_Fund[Client_Name]", ""),
    (P1, "KPI Largest TOP", "Card", "", "[Largest TOP]; subtitle [Largest TOP Subtitle]", "", ""),
    (P1, "KPI TOP late rate", "Card", "", "[TOP Late Rate]; subtitle text 'TOP-days arriving after the cut-off'", "",
     "Counts only TOP-days an in-view fund ran on. Date and client filters reach Fact_Milestone through TREATAS."),
    (P1, "KPI Breached fund-days", "Card", "", "[Breached Fund-Days]; subtitle [Breached Fund-Days Subtitle]", "", ""),
    (P1, "KPI Breaches, pricing late", "Card", "", "[Breaches Pricing Late %]; subtitle text", "",
     "Against each fund's own PSA cut-off (Pricing_Late_For_This_Fund)."),
    (P1, "KPI Share of wait behind other funds", "Card", "", "[Queue Share of Wait]; alternatives [Own Recon Share of Wait], [Other Holdup Share of Wait]", "",
     "Reconstructed, see README v4.5. The three shares add to 100%."),
    (P1, "Who is exposed — funds behind each TOP", "Clustered bar", "Y: Dim_TOP[TOP_ID]", "X: [Funds]",
     "Sort by [Funds] desc. Data label: [Funds Label] (custom label). Bar colour: fx field value [Exposure Bar Color]",
     "Design view: not limited by the date slicer."),
    (P1, "Dependency types — slack table", "Table", "Rows: Dim_SupplierType[Supplier_Type]",
     "[Supplier Funds], [Supplier Clients], [Median Slack Label], [Thin Slack Label]",
     "Sort by Type_Order. Font colour of Thin Slack Label: fx field value [Thin Slack Color]",
     "Thin = slack at or below Constants!B17 (0 = zero tolerance)."),
    (P1, "Pricing delay — created", "Clustered bar", "Y: Dim_TOP[TOP_ID]", "X: [Late Hours]",
     "Sort by [Late Hours] desc. Label [Late Hours Label]", "Place side by side with the next visual, same sort."),
    (P1, "Pricing delay — reached the funds", "Clustered bar", "Y: Dim_TOP[TOP_ID]", "X: [Breached Fund-Days When Late]",
     "Sort by [Late Hours] desc (add it to tooltips to sort)", ""),
    (P1, "Where funds waited after pricing", "Stacked bar", "Y: Dim_WaitGroup[Wait_Group]",
     "X: [Avg Queue Wait] (purple #7B5EA7) + [Avg Own Recon Wait] (blue #2F6FB0) + [Avg Other Holdup Wait] (amber #E8A33D)",
     "Sort by Group_Order. Label n: [Wait n Label] in tooltip or a side card",
     "Groups overlap: a fund-day is in one broker group and one custody group."),
    (P1, "Breached fund-days by possible cause", "Stacked column", "X: Dim_Fund[Client_Name]", "Y: [Breached Fund-Days]",
     "Legend: Dim_Cause[Possible_Cause]. Colours: Pricing late #C8423B, Thin custody slack #2F6FB0, Broker-dependent #7B5EA7, None of these #C9D1DB",
     "Only pricing is a measured cause."),
    (P2, "Header: Date / Client / Fund", "Cards / slicers", "", "[Date Range Label], [Client Label], [Fund Filter Label]",
     "Slicers: Fact_Work[Process_Date] (single date), Dim_Fund[Client_Name] (single), Fact_Work[Fund_ID]", ""),
    (P2, "KPI Funds in view", "Card", "", "[Funds In View]; subtitle [Funds In View Subtitle]", "", ""),
    (P2, "KPI Waiting after pricing", "Card", "", "[Avg Wait After Pricing] min", "", ""),
    (P2, "KPI NAV to Controlled", "Card", "", "[Avg NAV To Controlled] min", "", ""),
    (P2, "KPI Controlled to delivered", "Card", "", "[Avg Controlled To Delivered] min", "", ""),
    (P2, "KPI Headroom to cut-off", "Card", "", "[Avg Headroom] min", "", ""),
    (P2, "NAV timeline by fund", "Stacked bar", "Y: Fact_Work[Fund_Label]",
     "X: [Bar Offset] (no fill) + [Bar Waiting After Pricing] (purple) + [Bar NAV To Controlled] (green #2E9E5B) + "
     "[Bar Controlled To FA Signed Off] (blue #2F6FB0) + [Bar FA Signed Off To Delivered] (amber)",
     "X axis min 9, max 17. Sort by [NAV Start Hr] asc (put it in tooltips). Tooltips: [Pricing Cutoff Hr], "
     "[Pricing Arrived Hr], [Client Cutoff Hr]",
     "The native bar chart has no point markers. For the cut-off/arrival markers use error bars on the matching measure, "
     "or a Deneb visual."),
    (P2, "Selected fund table", "Table", "Rows: Dim_DetailRow[Detail]", "[Detail Value]",
     "Sort by Detail_Order. Font colour: fx field value [Detail Font Color]. Title: [Selected Fund Title]",
     "Shows values when one fund is selected (click a bar; set the timeline to cross-filter this table)."),
]

PQ_NOTE = ("Pre-filled formula rows with no data load as empty rows, and blank formula results (\"\") load as empty text. "
           "In each table's query: (1) filter out rows whose first column is null or empty; (2) replace \"\" with null in "
           "number and date columns, e.g. Table.ReplaceValue(prev, \"\", null, Replacer.ReplaceValue, {\"Queue_Wait_Mins\", ...}); "
           "(3) set *_Hr, *_Mins, *_Num and Bar_* to Decimal Number, *_DT to Date/Time, NAV_Date and Process_Date to Date. "
           "Slack_*_Mins and Check_Mins hold 'n/a' and stay text; do the maths on the *_Num and Bar_* columns.")

# Measures from the first v4.5 cut that the script removes when it finds them.
OBSOLETE = ["Idle Share of Wait", "Avg Idle Wait"]
