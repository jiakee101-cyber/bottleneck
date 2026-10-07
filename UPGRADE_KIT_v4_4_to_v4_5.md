# Upgrade kit — add v4.5 to a template you have already filled

Every formula below is the **row 2** formula. Click the cell in row 2 of your own file, paste the formula into the formula bar, press Enter, then fill it down to your last data row (double-click the fill handle). Type each header into row 1.

Do **not** insert or move columns: the new columns must sit at exactly these letters, because some formulas look them up by position.


## Constants — row 17

- **A17** `Thin slack threshold (mins)`
- **B17** `0` (typed number, blue: the thin-slack threshold in minutes)
- **C17** INPUT — v4.5. A custody, TA or broker feed is THIN when its slack to the pricing cut-off is at or below this. 0 = zero tolerance: thin only when the feed's cut-off is at or after the pricing cut-off, so any lateness reaches NAV directly. Separate from the broker watchlist threshold in B14.


## Dim_Fund — columns BC to BK

**BC1** `Client_First_In_TOP`

**BC2**
```
=IF($A2="","",IF($U2="",0,IF(COUNTIFS($U$2:$U2,$U2,$C$2:$C2,$C2)=1,1,0)))
```

**BD1** `Broker_Dependent`

**BD2**
```
=IF($A2="","",IF(UPPER($P2)="YES","Yes","No"))
```

**BE1** `Thin_Custody_Slack`

**BE2**
```
=IF($A2="","",IF($N2="No","n/a",IF(AM2<=Constants!$B$17,"Yes","No")))
```

**BF1** `Thin_TA_Slack`

**BF2**
```
=IF($A2="","",IF($O2="No","n/a",IF(AN2<=Constants!$B$17,"Yes","No")))
```

**BG1** `Thin_Broker_Slack`

**BG2**
```
=IF($A2="","",IF($P2="No","n/a",IF(AO2<=Constants!$B$17,"Yes","No")))
```

**BH1** `Custody_Slack_Group`

**BH2**
```
=IF($A2="","",IF($N2="No","No custody process",IF(BE2="Yes","Thin custody slack","Ample custody slack")))
```

**BI1** `Slack_Custody_Num`

**BI2**
```
=IF($A2="","",IF($N2="No","",AM2))
```

**BJ1** `Slack_TA_Num`

**BJ2**
```
=IF($A2="","",IF($O2="No","",AN2))
```

**BK1** `Slack_Broker_Num`

**BK2**
```
=IF($A2="","",IF($P2="No","",AO2))
```


## Dim_TOP — columns J to O

**J1** `Clients_In_TOP`

**J2**
```
=IF($A2="","",COUNTIFS(Dim_Fund!$U:$U,$A2,Dim_Fund!$BC:$BC,1))
```

**K1** `Share_Of_Funds`

**K2**
```
=IF($A2="","",IF(COUNTA(Dim_Fund!$A:$A)<=1,"",$D2/(COUNTA(Dim_Fund!$A:$A)-1)))
```

**L1** `TOP_Days_Scored`

**L2**
```
=IF($A2="","",COUNTIFS(Fact_Milestone!$B:$B,$A2,Fact_Milestone!$I:$I,"?*"))
```

**M1** `TOP_Days_Late`

**M2**
```
=IF($A2="","",COUNTIFS(Fact_Milestone!$B:$B,$A2,Fact_Milestone!$I:$I,"No"))
```

**N1** `Late_Hours_Total`

**N2**
```
=IF($A2="","",ROUND(SUMIFS(Fact_Milestone!$L:$L,Fact_Milestone!$B:$B,$A2)/60,2))
```

**O1** `Breached_Fund_Days_When_Late`

**O2**
```
=IF($A2="","",COUNTIFS(Fact_Work!$AL:$AL,$A2,Fact_Work!$AI:$AI,"Yes",Fact_Work!$BB:$BB,"No"))
```


## Fact_Milestone — columns L to M

**L1** `Late_Mins`

**L2**
```
=IF($A2="","",IF($H2="","",MAX(0,$H2)))
```

**M1** `Breached_Fund_Days`

**M2**
```
=IF($A2="","",IF($F2="","",COUNTIFS(Fact_Work!$B:$B,$A2,Fact_Work!$AL:$AL,$B2,Fact_Work!$AI:$AI,"Yes")))
```


## Fact_Work — columns BA to BT

**BA1** `Client_Name`

**BA2**
```
=IF($A2="","",IFERROR(VLOOKUP($C2,Dim_Fund!$A:$D,4,0),""))
```

**BB1** `TOP_SLA_Met`

**BB2**
```
=IF($A2="","",IF($AL2="","",IF(COUNTIFS(Fact_Milestone!$A:$A,$B2,Fact_Milestone!$B:$B,$AL2,Fact_Milestone!$I:$I,"No")>0,"No",IF(COUNTIFS(Fact_Milestone!$A:$A,$B2,Fact_Milestone!$B:$B,$AL2,Fact_Milestone!$I:$I,"Yes")>0,"Yes",""))))
```

**BC1** `Maker_Free_From_DT`

**BC2**
```
=IF($A2="","",IF(OR($L2="",$W2=""),"",IF(COUNTIFS($L:$L,$L2,$B:$B,$B2,$W:$W,"<"&$W2)=0,"",MAXIFS($W:$W,$L:$L,$L2,$B:$B,$B2,$W:$W,"<"&$W2))))
```

**BD1** `Queue_Wait_Mins`

**BD2**
```
=IF($A2="","",IF($AC2="","",IF(OR($L2="",$AC2=0),0,MIN($AC2,ROUND(ROUND(1440*SUMPRODUCT(($L$2:INDEX($L:$L,COUNTA($C:$C))=$L2)*($B$2:INDEX($B:$B,COUNTA($C:$C))=$B2)*(ROW($L$2:INDEX($L:$L,COUNTA($C:$C)))<>ROW())*((((($W2+$BT$2:INDEX($BT:$BT,COUNTA($C:$C))-ABS($W2-$BT$2:INDEX($BT:$BT,COUNTA($C:$C))))/2)-(($U2+$BS$2:INDEX($BS:$BS,COUNTA($C:$C))+ABS($U2-$BS$2:INDEX($BS:$BS,COUNTA($C:$C))))/2))+ABS(((($W2+$BT$2:INDEX($BT:$BT,COUNTA($C:$C))-ABS($W2-$BT$2:INDEX($BT:$BT,COUNTA($C:$C))))/2)-(($U2+$BS$2:INDEX($BS:$BS,COUNTA($C:$C))+ABS($U2-$BS$2:INDEX($BS:$BS,COUNTA($C:$C))))/2))))/2)),4),0)))))
```

**BE1** `Own_Recon_Mins`

**BE2**
```
=IF($A2="","",IF($AC2="","",ROUND(MIN($AC2-$BD2,N($R2)),0)))
```

**BF1** `Broker_Dependent`

**BF2**
```
=IF($A2="","",IFERROR(VLOOKUP($C2,Dim_Fund!$A:$BD,56,0),""))
```

**BG1** `Custody_Slack_Group`

**BG2**
```
=IF($A2="","",IFERROR(VLOOKUP($C2,Dim_Fund!$A:$BH,60,0),""))
```

**BH1** `Possible_Cause`

**BH2**
```
=IF($A2="","",IF($AI2<>"Yes","Not breached",IF($AM2="Yes","Pricing late",IF($BG2="Thin custody slack","Thin custody slack",IF($BF2="Yes","Broker-dependent","None of these")))))
```

**BI1** `Client_Cutoff_Hr`

**BI2**
```
=IF($A2="","",IFERROR(IF(VLOOKUP($C2,Dim_Fund!$A:$AI,35,0)>0,VLOOKUP($C2,Dim_Fund!$A:$AI,35,0),""),""))
```

**BJ1** `Fund_Label`

**BJ2**
```
=IF($A2="","",$C2&IF($E2="Client","*",""))
```

**BK1** `Controlled_To_Delivered_Mins`

**BK2**
```
=IF($A2="","",IFERROR(ROUND(($Y2-$X2)*1440,0),""))
```

**BL1** `Headroom_At_Delivery_Mins`

**BL2**
```
=IF($A2="","",IF($AH2="","",-$AH2))
```

**BM1** `Bar_Offset_Hr`

**BM2**
```
=IF($A2="","",IF($AQ2="","",IF($AP2="",$AQ2,MIN($AP2,$AQ2))))
```

**BN1** `Bar_Wait_Hr`

**BN2**
```
=IF($A2="","",IF($BM2="","",ROUND(N($AC2)/60,4)))
```

**BO1** `Bar_NAV_Hr`

**BO2**
```
=IF($A2="","",IF(OR($BM2="",$AD2=""),"",ROUND($AD2/60,4)))
```

**BP1** `Bar_Control_Hr`

**BP2**
```
=IF($A2="","",IF($BM2="","",ROUND(N($AE2)/60,4)))
```

**BQ1** `Bar_Tail_Hr`

**BQ2**
```
=IF($A2="","",IF(OR($BM2="",$AF2=""),"",ROUND($AF2/60,4)))
```

**BR1** `Other_Holdup_Mins`

**BR2**
```
=IF($A2="","",IF($AC2="","",$AC2-$BD2-$BE2))
```

**BS1** `Work_Start_Num`

**BS2**
```
=IF($A2="","",IF(AND(ISNUMBER($Z2),ISNUMBER($W2)),$Z2,0))
```

**BT1** `Work_End_Num`

**BT2**
```
=IF($A2="","",IF(ISNUMBER($W2),$W2,0))
```


## Fact_Work — two existing formulas to REPLACE (agreed fixes)

Replace row 2, then fill down over your existing rows.

**V2** (`Client_Cutoff_DT`)
```
=IF($A2="","",IFERROR(IF(VLOOKUP($C2,Dim_Fund!$A:$AI,35,0)>0,$B2+VLOOKUP($C2,Dim_Fund!$A:$AI,35,0)/24,""),""))
```

**AA2** (`Headroom_After_Pricing_Mins`)
```
=IF($A2="","",IF(OR(U2="",V2=""),"",ROUND((V2-U2)*1440,0)))
```


## Checks — rows 56 to 66 (new block)

| Cell A | Cell B (formula) | Cell C |
| --- | --- | --- |
| POWER BI COLUMNS (v4.5) | `` |  |
| Fact_Work rows without v4.5 formulas | `=COUNT(Fact_Work!$A:$A)-(COUNTIF(Fact_Work!$BJ:$BJ,"?*")-1)` | Target 0. Fill Fact_Work BA to BT down to the last data row, together with D to AZ. |
| Fund-days with no client cut-off | `=COUNTIFS(Fact_Work!$A:$A,"<>",Fact_Work!$V:$V,"")` | Target 0. The fund's client cut-off is missing (0) in Dim_Fund, so breach is not scored. Exclude, do not guess. |
| Wait split does not add up | `=COUNTIF(Fact_Work!$BR:$BR,"<0")` | Target 0. Other hold-up below zero means the three-way wait split is broken for that row. |
| Share of wait behind other funds | `=IFERROR(SUM(Fact_Work!$BD:$BD)/SUM(Fact_Work!$AC:$AC),"")` | Same maker working on another fund (inside its reconstructed work window). Capacity signal. |
| Share of wait on own recon | `=IFERROR(SUM(Fact_Work!$BE:$BE)/SUM(Fact_Work!$AC:$AC),"")` | Same maker reconciling this fund, up to its recon budget. Work, not idle. |
| Share of wait other hold-up | `=IFERROR(SUM(Fact_Work!$BR:$BR)/SUM(Fact_Work!$AC:$AC),"")` | Not explained by queue or recon budget: data not ready, breaks, recon over budget, unlogged work. |
| Funds with thin custody slack | `=COUNTIF(Dim_Fund!$BE:$BE,"Yes")` | Slack at or below Constants!B17. With 0 tolerance, only funds whose custody cut-off is at or after pricing. |
| Funds with thin TA slack | `=COUNTIF(Dim_Fund!$BF:$BF,"Yes")` | As above for TA. |
| Broker-dependent funds | `=COUNTIF(Dim_Fund!$BD:$BD,"Yes")` | Has_Broker_Process = Yes. |
| Breached fund-days with a possible cause | `=COUNTIFS(Fact_Work!$BH:$BH,"?*",Fact_Work!$BH:$BH,"<>Not breached")-COUNTIF(Fact_Work!$BH:$BH,"Possible_Cause")` | Must equal 'Breached cycles' above. |

Format B60:B62 as percentage.


## New sheets — 4 small lookup tables

Create each sheet with exactly this name, headers in row 1, values from row 2. Type them (they are short), do not copy from my file.


**Dim_SupplierType**

| Supplier_Type | Type_Order |
| --- | --- |
| Pricing (TOP) | 1 |
| Custody | 2 |
| TA | 3 |
| Broker (dependent) | 4 |

**Dim_WaitGroup**

| Wait_Group | Group_Order |
| --- | --- |
| Broker-dependent | 1 |
| Not broker-dependent | 2 |
| Thin custody slack | 3 |
| Ample custody slack | 4 |

**Dim_Cause**

| Possible_Cause | Cause_Order |
| --- | --- |
| Pricing late | 1 |
| Thin custody slack | 2 |
| Broker-dependent | 3 |
| None of these | 4 |
| Not breached | 5 |

**Dim_DetailRow**

| Detail | Detail_Order |
| --- | --- |
| Pricing cut-off | 1 |
| Pricing arrived | 2 |
| NAV started | 3 |
| Controlled | 4 |
| FA signed off | 5 |
| Delivered | 6 |
| Client cut-off | 7 |
| Headroom | 8 |
| Waited after pricing | 9 |
| NAV to Controlled | 10 |

## Optional tidy-ups (no effect on numbers)

- **Checks C8**: change `Constants!B13` to `Constants!B14` in the text.
- **Dim_Signoff A6:A7**: delete the two note rows (they load into Power BI as fake sign-off models).
- **PBI_Mapping** sheet and the README v4.5 notes: documentation only. Copy them across if you want them, but do not load PBI_Mapping into Power BI.
