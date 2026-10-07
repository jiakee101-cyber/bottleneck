import pandas as pd, numpy as np, sys
f=sys.argv[1]
S=lambda s,k: (lambda d: d[d[k].notna() & (d[k].astype(str)!='')].reset_index(drop=True))(pd.read_excel(f,s,keep_default_na=False).replace('',np.nan))
fund=S('Dim_Fund','Fund_ID'); top=S('Dim_TOP','TOP_ID'); fm=S('Fact_Milestone','Process_Date'); fw=S('Fact_Work','NAV_Date')
thr=pd.read_excel(f,'Constants',header=None).iloc[16,1]
bad=[]
def chk(name, got, exp):
    g=pd.Series(got).replace('',np.nan).reset_index(drop=True); e=pd.Series(exp).replace('',np.nan).reset_index(drop=True)
    for i,(a,b) in enumerate(zip(g,e)):
        if (pd.isna(a) and pd.isna(b)): continue
        try:
            if abs(float(a)-float(b))<1e-6: continue
        except: 
            if a==b: continue
        if isinstance(a,pd.Timestamp) and isinstance(b,pd.Timestamp) and abs((a-b).total_seconds())<1: continue
        bad.append((name,i,a,b))
# Dim_Fund
seen=set(); first=[]
for _,r in fund.iterrows():
    k=(r.TOP_ID,r.Client_ID); first.append(0 if pd.isna(r.TOP_ID) else int(k not in seen)); seen.add(k)
chk('Client_First_In_TOP',fund.Client_First_In_TOP,first)
chk('Broker_Dependent',fund.Broker_Dependent,np.where(fund.Has_Broker_Process.str.upper()=='YES','Yes','No'))
for col,flag,sl in [('Thin_Custody_Slack','Has_Custody_Process','Slack_Custody_Mins'),('Thin_TA_Slack','Has_TA_Process','Slack_TA_Mins'),('Thin_Broker_Slack','Has_Broker_Process','Slack_Broker_Mins')]:
    exp=[ 'n/a' if r[flag]=='No' else ('Yes' if float(r[sl])<=thr else 'No') for _,r in fund.iterrows()]
    chk(col,fund[col],exp)
    chk(sl.replace('_Mins','_Num'),fund[sl.replace('_Mins','_Num')],[np.nan if r[flag]=='No' else r[sl] for _,r in fund.iterrows()])
chk('Custody_Slack_Group',fund.Custody_Slack_Group,['No custody process' if r.Has_Custody_Process=='No' else ('Thin custody slack' if r.Thin_Custody_Slack=='Yes' else 'Ample custody slack') for _,r in fund.iterrows()])
# Fact_Milestone
chk('Late_Mins',fm.Late_Mins,[np.nan if pd.isna(h) or h=='' else max(0,h) for h in fm.Delay_Mins])
chk('Breached_Fund_Days',fm.Breached_Fund_Days,[np.nan if pd.isna(r.Binding_Cutoff_Hr) or r.Binding_Cutoff_Hr=='' else ((fw.Process_Date==r.Process_Date)&(fw.TOP_ID==r.TOP_ID)&(fw.Breached=='Yes')).sum() for _,r in fm.iterrows()])
# Dim_TOP
chk('Clients_In_TOP',top.Clients_In_TOP,[fund[fund.TOP_ID==t].Client_ID.nunique() for t in top.TOP_ID])
chk('Share_Of_Funds',top.Share_Of_Funds,[(fund.TOP_ID==t).sum()/len(fund) for t in top.TOP_ID])
chk('TOP_Days_Scored',top.TOP_Days_Scored,[((fm.TOP_ID==t)&fm.SLA_Met.isin(['Yes','No'])).sum() for t in top.TOP_ID])
chk('TOP_Days_Late',top.TOP_Days_Late,[((fm.TOP_ID==t)&(fm.SLA_Met=='No')).sum() for t in top.TOP_ID])
chk('Late_Hours_Total',top.Late_Hours_Total,[round(pd.to_numeric(fm[fm.TOP_ID==t].Late_Mins,errors='coerce').sum()/60,2) for t in top.TOP_ID])
# Fact_Work
fwm=fw.merge(fund[['Fund_ID','Client_Name','Broker_Dependent','Custody_Slack_Group','Client_Cutoff_Hr']],on='Fund_ID',how='left',suffixes=('','_f'))
chk('Client_Name',fw.Client_Name,fwm.Client_Name_f)
sla=[]
for _,r in fw.iterrows():
    m=fm[(fm.Process_Date==r.Process_Date)&(fm.TOP_ID==r.TOP_ID)].SLA_Met
    sla.append('No' if (m=='No').any() else ('Yes' if (m=='Yes').any() else np.nan))
chk('TOP_SLA_Met',fw.TOP_SLA_Met,sla)
mff=[];q=[];idle=[];other=[]
W=pd.to_datetime(fw.NAV_Start_DT,errors='coerce'); U=pd.to_datetime(fw.Pricing_Arrival_DT,errors='coerce')
for i,r in fw.iterrows():
    prev=W[(fw.Maker_Name==r.Maker_Name)&(fw.Process_Date==r.Process_Date)&(W<W[i])]
    m=prev.max() if len(prev) else pd.NaT; mff.append(m)
    wait=pd.to_numeric(pd.Series([r.Wait_After_Pricing_Mins]),errors='coerce')[0]
    if pd.isna(wait): q.append(np.nan); idle.append(np.nan); other.append(np.nan); continue
    qq=0 if pd.isna(m) else max(0,min(wait,round((m-U[i]).total_seconds()/60)))
    rb=pd.to_numeric(pd.Series([r.Recon_Mins]),errors='coerce').fillna(0)[0]
    own=int(np.floor(min(wait-qq,rb)+0.5)); q.append(qq); idle.append(own); other.append(wait-qq-own)
chk('Maker_Free_From_DT',pd.to_datetime(fw.Maker_Free_From_DT,errors='coerce'),mff)
chk('Queue_Wait_Mins',fw.Queue_Wait_Mins,q); chk('Own_Recon_Mins',fw.Own_Recon_Mins,idle); chk('Other_Holdup_Mins',fw.Other_Holdup_Mins,other)
chk('Broker_Dependent_fw',fw.Broker_Dependent,fwm.Broker_Dependent_f); chk('Custody_Slack_Group_fw',fw.Custody_Slack_Group,fwm.Custody_Slack_Group_f)
cause=['Not breached' if r.Breached!='Yes' else 'Pricing late' if r.Pricing_Late_For_This_Fund=='Yes' else 'Thin custody slack' if r.Custody_Slack_Group=='Thin custody slack' else 'Broker-dependent' if r.Broker_Dependent=='Yes' else 'None of these' for _,r in fw.iterrows()]
chk('Possible_Cause',fw.Possible_Cause,cause)
chk('Client_Cutoff_Hr',fw.Client_Cutoff_Hr,fwm.Client_Cutoff_Hr_f)
chk('Fund_Label',fw.Fund_Label,[r.Fund_ID+('*' if r.Signoff_Model=='Client' else '') for _,r in fw.iterrows()])
X=pd.to_datetime(fw.NAV_End_DT,errors='coerce'); Y=pd.to_datetime(fw.Delivered_DT,errors='coerce')
chk('Controlled_To_Delivered_Mins',fw.Controlled_To_Delivered_Mins,((Y-X).dt.total_seconds()/60).round())
chk('Headroom',fw.Headroom_At_Delivery_Mins,-pd.to_numeric(fw.Breach_Mins,errors='coerce'))
# stack must end at delivery time of day
num=lambda c: pd.to_numeric(fw[c],errors='coerce')
end=num('Bar_Offset_Hr')+num('Bar_Wait_Hr')+num('Bar_NAV_Hr')+num('Bar_Control_Hr')+num('Bar_Tail_Hr')
dhr=(Y-Y.dt.normalize()).dt.total_seconds()/3600
diff=(end-dhr).abs()
print("bar stack vs delivery hr: max diff (hrs) =",round(diff.max(),4),"rows",len(diff))
print("MISMATCHES:",len(bad)); [print(b) for b in bad[:20]]
print(fw[['Fund_Label','Maker_Name','Wait_After_Pricing_Mins','Queue_Wait_Mins','Own_Recon_Mins','Other_Holdup_Mins','Recon_Mins','Possible_Cause','TOP_SLA_Met']].to_string())
print(top[['TOP_ID','Funds_In_TOP','Clients_In_TOP','Share_Of_Funds','TOP_Days_Scored','TOP_Days_Late','Late_Hours_Total','Breached_Fund_Days_When_Late']].to_string())
