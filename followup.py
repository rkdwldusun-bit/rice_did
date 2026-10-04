from pathlib import Path
import numpy as np,pandas as pd,json,shutil
from scipy import stats
P=Path(__file__).resolve().parent
OLD=P.parent/'rice_analysis_20261004'
if not (P/'source_panel.csv').exists(): shutil.copyfile(OLD/'source_panel_2000_2011.csv',P/'source_panel.csv')
if not (P/'main_panel.csv').exists(): shutil.copyfile(OLD/'analysis_panel_main.csv',P/'main_panel.csv')
d=pd.read_csv(P/'source_panel.csv');main=pd.read_csv(P/'main_panel.csv')
ex=['논산시','계룡시','괴산군','증평군','창원시','마산시','진해시']
d=d[~d.name.isin(ex)].copy(); n=d.groupby('id').log_area.count();d=d[d.id.isin(n[n==12].index)].copy()
d['uid']=pd.factorize(d.id)[0]+1;d.to_csv(P/'cs_input.csv',index=False)
assert d.groupby('cohort').id.nunique().to_dict()=={2009:17,2011:9,2012:119}
def regress(q,extra,by='year'):
 q=q.reset_index(drop=True);extra=np.asarray(extra,float)
 if extra.ndim==1:extra=extra[:,None]
 fe=pd.get_dummies(q[['id',by]].astype(str),drop_first=True,dtype=float)
 X=np.column_stack([np.ones(len(q)),fe,extra]);y=q.log_area.to_numpy();rank=np.linalg.matrix_rank(X)
 inv=np.linalg.pinv(X.T@X);b=np.linalg.lstsq(X,y,rcond=None)[0];u=y-X@b
 ids,lev=pd.factorize(q.id);G=len(lev);S=np.zeros((G,X.shape[1]));np.add.at(S,ids,X*u[:,None]);V=G/(G-1)*(len(q)-1)/(len(q)-rank)*inv@S.T@S@inv
 k=extra.shape[1];return b[-k:],V[-k:,-k:],G
def rec(name,q,extra,by='year'):
 b,V,G=regress(q,extra,by);se=np.sqrt(V[0,0]);c=stats.t.ppf(.975,G-1)
 return dict(model=name,beta=b[0],se=se,p=2*stats.t.sf(abs(b[0]/se),G-1),low=b[0]-c*se,high=b[0]+c*se,effect_pct=100*np.expm1(b[0]),n=len(q),clusters=G)
out=[]; pair=d[d.cohort.isin([2009,2011])&(d.year<=2010)].copy();pair['treated']=(pair.cohort==2009).astype(int)
out.append(rec('2011 cohort only; long pre TWFE',pair,pair.treated*(pair.year>=2009)))
out.append(rec('Main plus treated linear trend',main,np.column_stack([main.treated*(main.year>=2009),main.treated*(main.year-2008)])))
q=d[d.cohort!=2011].copy();q['treated']=(q.cohort==2009).astype(int)
size=q[q.year<2009].groupby('id').area.mean();bins,edges=pd.qcut(size,4,labels=False,retbins=True)
q['quartile']=q.id.map(bins).astype(int)+1;q['quartile_year']=q.quartile.astype(str)+'_'+q.year.astype(str)
out.append(rec('Pre-area quartile by year FE',q,q.treated*(q.year>=2009),'quartile_year'))
balance=q[q.year==2008].groupby(['quartile','treated']).size().unstack(fill_value=0)
balance.to_csv(P/'quartile_balance.csv');q.to_csv(P/'quartile_panel.csv',index=False)
out.append(rec('Gumi excluded influence only',main[main.id!='GB_구미시'],main.loc[main.id!='GB_구미시','treated']*(main.loc[main.id!='GB_구미시','year']>=2009)))
pd.DataFrame(out).to_csv(P/'alternative_estimates.csv',index=False)
# Unconditional group-time estimands. Each unit contributes its outcome difference.
wide=d.pivot(index='id',columns='year',values='log_area');coh=d.groupby('id').cohort.first().reindex(wide.index).to_numpy();N=len(wide)
def cell(g,t,only2011=False):
 base=g-1;delta=(wide[t]-wide[base]).to_numpy();a=coh==g;c=(coh==2011) if only2011 else coh>max(t,base)
 att=delta[a].mean()-delta[c].mean();IF=np.zeros(N);IF[a]=(delta[a]-delta[a].mean())/a.mean();IF[c]=-(delta[c]-delta[c].mean())/c.mean()
 return att,IF,a.sum(),c.sum()
cells=[(2009,2009),(2009,2010),(2009,2011),(2011,2011)]; vals=[cell(*c) for c in cells];b=np.array([z[0] for z in vals]);IF=np.column_stack([z[1] for z in vals]);V=IF.T@IF/N**2;se=np.sqrt(np.diag(V))
rng=np.random.default_rng(20261004);draw=rng.choice([-1.,1.],size=(9999,N))@IF/N;ts=draw/se;critical=np.quantile(np.max(abs(ts),axis=1),.95)
cs=pd.DataFrame([dict(g=g,t=t,beta=b[i],se=se[i],p_normal=2*stats.norm.sf(abs(b[i]/se[i])),p_multiplier=(1+(abs(ts[:,i])>=abs(b[i]/se[i])).sum())/10000,ci_low=b[i]-1.96*se[i],ci_high=b[i]+1.96*se[i],sim_low=b[i]-critical*se[i],sim_high=b[i]+critical*se[i],treated=vals[i][2],controls=vals[i][3]) for i,(g,t) in enumerate(cells)])
cs.to_csv(P/'group_time_att.csv',index=False);pd.DataFrame(V).to_csv(P/'group_time_covariance.csv',index=False)
z1=cell(2009,2009,True);z2=cell(2009,2010,True);pb=(z1[0]+z2[0])/2;pif=(z1[1]+z2[1])/2;pse=np.linalg.norm(pif)/N
pairsummary=dict(beta=pb,se=pse,p_normal=2*stats.norm.sf(abs(pb/pse)),low=pb-1.96*pse,high=pb+1.96*pse)
# Export baseline event covariance for official HonestDiD; full ordered coefficients.
years=[y for y in range(2000,2012) if y!=2008];X=np.column_stack([main.treated*(main.year==y) for y in years]);eb,EV,G=regress(main,X)
pd.DataFrame({'year':years,'beta':eb}).to_csv(P/'honest_beta.csv',index=False)
pd.DataFrame(EV,columns=[str(y) for y in years],index=years).to_csv(P/'honest_covariance.csv')
assert np.allclose(eb,pd.read_csv(OLD/'event_study.csv').beta) if OLD.exists() else True
assert np.linalg.eigvalsh(EV).min()>-1e-10
# Conservative separate Bonferroni projection, not HonestDiD package C-LF/FLCI.
A=np.zeros((8,11))
for i in range(7):A[i,i+1]=1;A[i,i]=-1
A[7,7]=-1
slopes=A@eb;slopese=np.sqrt(np.diag(A@EV@A.T));upper=np.max(np.abs(slopes)+stats.norm.ppf(1-.025/16)*slopese)
l=np.r_[np.zeros(8),np.repeat(1/3,3)];avg=l@eb;avgse=np.sqrt(l@EV@l);c=stats.norm.ppf(1-.025/2)
sens=pd.DataFrame([dict(Mbar=m,estimate=avg,se=avgse,slope_upper=upper,bias_bound=2*m*upper,low=avg-c*avgse-2*m*upper,high=avg+c*avgse+2*m*upper,method='Conservative Bonferroni RM bound; NOT official HonestDiD') for m in [0,.5,1,1.5,2]])
sens.to_csv(P/'conservative_sensitivity_NOT_HonestDiD.csv',index=False)
summary=dict(quartile_edges=edges.tolist(),pair2008base=pairsummary,event_average=float(avg),event_average_se=float(avgse),event_average_normal_low=float(avg-1.96*avgse),event_average_normal_high=float(avg+1.96*avgse),simultaneous_multiplier_critical=float(critical),R_did_executed=False,R_HonestDiD_executed=False)
(P/'summary.json').write_text(json.dumps(summary,indent=2))
print(pd.DataFrame(out).to_string(index=False));print(cs.to_string(index=False));print(balance.to_string());print(sens.to_string(index=False));print(json.dumps(summary,indent=2))
