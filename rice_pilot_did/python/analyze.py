"""Reproduce with Python + numpy scipy pandas matplotlib. No statsmodels required.
Usage: python analyze.py --source /path/to/벼_재배면적.xls
"""
from pathlib import Path
import argparse, re, html, json, hashlib, itertools
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io

OUT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(); ap.add_argument('--source',required=True); args=ap.parse_args()
source=Path(args.source)
raw=source.read_bytes()
s=re.sub(r'<\?xml[^>]+\?>','',raw.decode('euc-kr').lstrip())
s=re.sub(r'(<Data\b[^>]*>)(.*?)(</Data>)',lambda m:m[1]+html.escape(html.unescape(m[2]),quote=False)+m[3],s,flags=re.S)
ns={'s':'urn:schemas-microsoft-com:office:spreadsheet'}; root=ET.fromstring(s)
rows=[]
for row in root.find('s:Worksheet',ns).find('s:Table',ns).findall('s:Row',ns):
    a=[]
    for c in row.findall('s:Cell',ns):
        idx=c.get('{'+ns['s']+'}Index')
        if idx: a+=['']*(int(idx)-1-len(a))
        v=c.find('s:Data',ns); a.append('' if v is None else ''.join(v.itertext()))
    rows.append(a)
headers=rows[1]; yearcol={int(re.search(r'\d{4}',h)[0]):i for i,h in enumerate(headers) if re.search(r'\d{4}',h)}
provs={'전라남도':'JN','경기도':'GG','강원도':'GW','충청북도':'CB','충청남도':'CN','전라북도':'JB','경상북도':'GB','경상남도':'GN'}
early={'GG':['평택시','이천시'],'GW':['철원군'],'CB':['청원군','진천군'],'CN':['당진군','서산시','논산시'],'JB':['김제시','부안군','익산시'],'JN':['나주시','영암군','해남군'],'GB':['구미시','상주시'],'GN':['김해시','밀양시'],'BS':['기장군'],'US':['울주군']}
late={'GG':['화성시'],'CN':['예산군','아산시'],'JB':['고창군','정읍시'],'JN':['영광군','고흥군'],'GB':['경주시','의성군'],'IC':['강화군']}
E={(p,n) for p,v in early.items() for n in v}; L={(p,n) for p,v in late.items() for n in v}
records=[]; province=None
for rownum,r in enumerate(rows):
    if len(r)<2 or r[1]!='재배면적': continue
    name=r[0]
    if name in provs: province=provs[name]; continue
    if name=='전국' or '광역시' in name or '특별' in name or name=='제주도': province=None; continue
    if province is None: continue
    for y in range(2000,2012):
        v=r[yearcol[y]] if yearcol[y]<len(r) else ''
        try: value=float(v.replace(',',''))
        except ValueError: value=np.nan
        records.append(dict(id=province+'_'+name,province=province,name=name,year=y,area=value,cohort=2009 if (province,name) in E else 2011 if (province,name) in L else 2012,source_row=rownum+1))
d=pd.DataFrame(records)
# Historical aliases with no data are retained in audit only, never imputed.
d.to_csv(OUT/'parsed_source_rows.csv',index=False)
nonempty=d.groupby('source_row').area.count()
d=d[d.source_row.isin(nonempty[nonempty>0].index)].copy()
assert not d.duplicated(['id','year']).any(), 'Duplicate regional labels must be resolved'
d['log_area']=np.log(d.area.where(d.area>0)); d['treated']=(d.cohort==2009).astype(int)
d.to_csv(OUT/'source_panel_2000_2011.csv',index=False)
merger={'창원시','마산시','진해시'}
bound=merger|{'논산시','계룡시','괴산군','증평군'}
audit=d.groupby(['id','province','name','cohort']).agg(n_positive=('log_area','count'),area2000=('area','first'),area2011=('area','last')).reset_index()
audit['boundary_exclusion_long']=audit.name.isin(bound)
audit.to_csv(OUT/'coverage_audit.csv',index=False)
def sample(start=2000,screen=True,short_bound=False):
    q=d[(d.year>=start)&(d.cohort!=2011)&~d.name.isin(merger if short_bound else bound)].copy()
    ids=q.groupby('id').log_area.count(); q=q[q.id.isin(ids[ids==2012-start].index)]
    pre=q[q.year<2009].groupby('id').area.mean()
    treated=q[q.treated==1].id.unique(); lo,hi=pre.loc[treated].min(),pre.loc[treated].max()
    if screen: q=q[q.id.isin(treated)|q.id.isin(pre[pre.between(lo,hi)].index)]
    return q.sort_values(['id','year']).reset_index(drop=True),(lo,hi)
main,limits=sample()
main.to_csv(OUT/'analysis_panel_main.csv',index=False)
# Balanced panels permit exact two-way demeaning, including province-year FE.
def within(a,q,provyear=False):
    a=np.asarray(a,float); one=a.ndim==1
    if one: a=a[:,None]
    z=a.copy()
    for group in [q.id, q.province+'_'+q.year.astype(str) if provyear else q.year]:
        codes,lev=pd.factorize(group)
        sums=np.zeros((len(lev),a.shape[1])); np.add.at(sums,codes,z)
        z-=sums[codes]/np.bincount(codes)[codes,None]
    return z[:,0] if one else z
def fit(q,X,provyear=False,cluster='id'):
    X=np.asarray(X,float)
    if X.ndim==1: X=X[:,None]
    xr=within(X,q,provyear); yr=within(q.log_area,q,provyear)
    inv=np.linalg.inv(xr.T@xr); b=inv@xr.T@yr; resid=yr-xr@b
    codes,levels=pd.factorize(q[cluster]); G=len(levels); N=len(q)
    K=q.id.nunique()+(q.province.nunique() if provyear else 1)*(q.year.nunique()-1)+X.shape[1]
    scores=np.zeros((G,X.shape[1])); np.add.at(scores,codes,xr*resid[:,None])
    V=G/(G-1)*(N-1)/(N-K)*inv@scores.T@scores@inv
    return b,V,G,K,resid,xr
def result(q,label,provyear=False,cluster='id'):
    x=q.treated.to_numpy()*(q.year.to_numpy()>=2009)
    b,V,G,K,_,_=fit(q,x,provyear,cluster); beta=b[0]; se=np.sqrt(V[0,0]); crit=stats.t.ppf(.975,G-1)
    low,high=beta-crit*se,beta+crit*se
    return dict(model=label,n=len(q),municipalities=q.id.nunique(),treated=q[q.treated==1].id.nunique(),controls=q[q.treated==0].id.nunique(),cluster=cluster,clusters=G,beta=beta,se=se,p=2*stats.t.sf(abs(beta/se),G-1),ci_low=low,ci_high=high,percent=100*np.expm1(beta),percent_low=100*np.expm1(low),percent_high=100*np.expm1(high),mde_log=(crit+stats.norm.ppf(.8))*se)
results=[result(main,'Main: pre-area screen, 2000-2011'),result(main,'Main, province clusters',cluster='province')]
full,_=sample(screen=False)
results.append(result(full,'All stable eligible controls'))
results.append(result(main,'Province-by-year FE',provyear=True))
results.append(result(main[main.year>=2006].copy(),'Same sample, 2006-2011'))
short,shortlimits=sample(2006,True,True)
short.to_csv(OUT/'analysis_panel_short.csv',index=False)
results.append(result(short,'2006-2011, include split municipalities'))
results.append(result(main[main.year!=2009].copy(),'Exclude 2009 transition year'))
pd.DataFrame(results).to_csv(OUT/'estimates.csv',index=False)
# Event study, normalized to 2008, with joint pre-period diagnostic.
years=[y for y in range(2000,2012) if y!=2008]
X=np.column_stack([main.treated*(main.year==y) for y in years]); b,V,G,K,_,_=fit(main,X)
crit=stats.t.ppf(.975,G-1)
ev=pd.DataFrame({'year':years,'beta':b,'se':np.sqrt(np.diag(V))}); ev['ci_low']=ev.beta-crit*ev.se; ev['ci_high']=ev.beta+crit*ev.se
ev.to_csv(OUT/'event_study.csv',index=False)
ix=np.array([i for i,y in enumerate(years) if y<2008]); w=float(b[ix]@np.linalg.inv(V[np.ix_(ix,ix)])@b[ix]); pre_p=float(stats.f.sf(w/len(ix),len(ix),G-1))
pre=main[main.year<2009].copy()
bt,vt,gt,*_=fit(pre,pre.treated*(pre.year-2008)); trendse=float(np.sqrt(vt[0,0])); trendp=float(2*stats.t.sf(abs(bt[0]/trendse),gt-1))
bp,vp,gp,*_=fit(pre,pre.treated*(pre.year>=2006)); placse=float(np.sqrt(vp[0,0])); placp=float(2*stats.t.sf(abs(bp[0]/placse),gp-1))
# Verify balanced 2x2 DiD coefficient independently using unit period means.
changes=main.assign(period=np.where(main.year<2009,'pre','post')).groupby(['id','treated','period']).log_area.mean().unstack()
delta=changes['post']-changes['pre']; collapse=float(delta.xs(1,level='treated').mean()-delta.xs(0,level='treated').mean())
assert np.isclose(collapse,results[0]['beta'],atol=1e-12)
# Validate residualization against explicit least squares FE design.
fe=pd.get_dummies(main[['id','year']].astype(str),drop_first=True,dtype=float)
xx=np.column_stack([np.ones(len(main)),fe.to_numpy(),main.treated*(main.year>=2009)])
explicit=np.linalg.lstsq(xx,main.log_area,rcond=None)[0][-1]
assert np.isclose(explicit,collapse,atol=1e-10)
loo=[]
for rid in main[main.treated==1].id.unique():
    rr=result(main[main.id!=rid].copy(),rid); loo.append(rr)
pd.DataFrame(loo).to_csv(OUT/'leave_one_treated_out.csv',index=False)
# Exhaustive null-imposed province wild cluster bootstrap (Rademacher), diagnostic only.
x=(main.treated*(main.year>=2009)).to_numpy(); xr=within(x,main); yr=within(main.log_area,main)
pc,pl=pd.factorize(main.province); signs=np.array(list(itertools.product([-1.,1.],repeat=len(pl)))).T
ys=within(yr[:,None]*signs[pc],main); bb=xr@ys/(xr@xr); uu=ys-xr[:,None]*bb
sc=np.zeros((len(pl),len(bb))); np.add.at(sc,pc,xr[:,None]*uu)
kk=main.id.nunique()+main.year.nunique()
vv=len(pl)/(len(pl)-1)*(len(main)-1)/(len(main)-kk)*(sc**2).sum(axis=0)/(xr@xr)**2
tb=bb/np.sqrt(vv); obs=results[1]['beta']/results[1]['se']; wildp=float(np.mean(np.abs(tb)>=abs(obs)-1e-12))
# Descriptives, trajectory, and source discontinuity flags.
desc=main.assign(group=np.where(main.treated==1,'2009 cohort','2012 cohort'),period=np.where(main.year<2009,'pre 2000-08','post 2009-11')).groupby(['group','period']).agg(mean_ha=('area','mean'),sd_ha=('area','std'),min_ha=('area','min'),max_ha=('area','max'),n=('area','size'),municipalities=('id','nunique'))
desc.to_csv(OUT/'descriptives.csv')
trajectory=main.groupby(['treated','year']).log_area.mean().unstack(0); index=np.exp(trajectory-trajectory.loc[2008])*100
index.to_csv(OUT/'indexed_trajectories.csv')
changes2=main.copy(); changes2['pct_change']=changes2.groupby('id').area.pct_change()*100
changes2[changes2['pct_change'].abs()>15].to_csv(OUT/'large_changes_to_verify.csv',index=False)
fig,axs=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
for t,label,c in [(1,'2009 pilot municipalities','#23679A'),(0,'2012 municipalities','#AC6337')]: axs[0].plot(index.index,index[t],label=label,color=c,marker='o',markersize=3)
axs[0].axvline(2008.5,color='gray',ls='--'); axs[0].set(ylabel='Geometric mean area index (2008 = 100)',title='Pre-policy trajectories and subsequent changes',xlabel='Year'); axs[0].legend(fontsize=8)
axs[1].errorbar(ev.year,ev.beta,yerr=crit*ev.se,fmt='o',color='#23679A',capsize=3); axs[1].plot(2008,0,'o',color='gray'); axs[1].axhline(0,color='gray',lw=1); axs[1].axvline(2008.5,color='gray',ls='--'); axs[1].set(title='Event study (2008 reference)',ylabel='Difference in log area; pointwise 95% CI',xlabel='Year')
for ax in axs: ax.spines[['top','right']].set_visible(False); ax.grid(axis='y',alpha=.2)
png_buffer=io.BytesIO(); fig.savefig(png_buffer,format='png',dpi=190)
(OUT/'rice_results.png').write_bytes(png_buffer.getvalue())
fig.savefig(OUT/'rice_results.pdf'); plt.close(fig)
summary=dict(source_sha256=hashlib.sha256(raw).hexdigest(),scale_screen_ha=limits,short_scale_screen_ha=shortlimits,main=results[0],pretrend_joint_F=w/len(ix),pretrend_joint_df=[len(ix),G-1],pretrend_joint_p=pre_p,pre_linear_slope=float(bt[0]),pre_linear_se=trendse,pre_linear_p=trendp,placebo_2006_beta=float(bp[0]),placebo_2006_se=placse,placebo_2006_p=placp,province_wild_p=wildp,province_wild_draws=len(bb),collapsed_did=collapse,explicit_fe_beta=float(explicit),loo_min=min(r['beta'] for r in loo),loo_max=max(r['beta'] for r in loo))
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(pd.DataFrame(results).to_string(index=False)); print(json.dumps(summary,ensure_ascii=False,indent=2)); print(desc.to_string())
