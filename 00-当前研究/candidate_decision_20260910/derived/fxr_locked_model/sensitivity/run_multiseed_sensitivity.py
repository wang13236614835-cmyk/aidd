from pathlib import Path
import pandas as pd, numpy as np, json, hashlib, warnings
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem, Descriptors, Lipinski, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, roc_auc_score, average_precision_score
from scipy.stats import spearmanr
warnings.filterwarnings('ignore')
ROOT=Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
DATA=ROOT/'derived'/'chembl_numeric_nM_exact_candidates.csv'
OUT=ROOT/'derived'/'fxr_locked_model'/'sensitivity'; OUT.mkdir(parents=True,exist_ok=True)
ASSAY='CHEMBL5735838'; SEEDS=[20260910,42,123,7,20260911,31415,271828,20260912,20260913,20260914]; N_BITS=2048

def mol(s): return Chem.MolFromSmiles(str(s))
def fp(m): return np.asarray(AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=N_BITS),dtype=np.uint8)
def desc(m): return np.array([Descriptors.MolWt(m),Descriptors.MolLogP(m),rdMolDescriptors.CalcTPSA(m),Lipinski.NumHDonors(m),Lipinski.NumHAcceptors(m),Lipinski.NumRotatableBonds(m),rdMolDescriptors.CalcNumAromaticRings(m)],float)
def scaf(s):
 m=mol(s); z=MurckoScaffold.MurckoScaffoldSmiles(mol=m); return z or '[NO_SCAFFOLD]'
def aucs(y,p):
 if len(set(y))<2:return {'roc_auc':None,'pr_auc':None}
 return {'roc_auc':float(roc_auc_score(y,p)),'pr_auc':float(average_precision_score(y,p))}
df=pd.read_csv(DATA,low_memory=False)
x=df[(df.target_label=='fxr')&(df.standard_type=='EC50')&(df.bao_label=='single protein format')&(df.assay_chembl_id==ASSAY)&(df.standard_flag==1)&(df.standard_relation=='=')&(df.potential_duplicate==0)].dropna(subset=['canonical_smiles','pActivity_nM']).drop_duplicates('molecule_chembl_id').reset_index(drop=True)
x['scaffold']=x.canonical_smiles.map(scaf); x['label']=(x.pActivity_nM>=8.0).astype(int)
X=np.stack([fp(mol(s)) for s in x.canonical_smiles]); D=np.stack([desc(mol(s)) for s in x.canonical_smiles]); y=x.pActivity_nM.to_numpy(float); yc=x.label.to_numpy(int); groups=x.scaffold.to_numpy(str)
params={'n_estimators':300,'random_state':0,'n_jobs':8,'min_samples_leaf':2,'max_features':'sqrt'}
res=[]; split_info=[]
for seed in SEEDS:
 outer=GroupShuffleSplit(n_splits=1,test_size=.2,random_state=seed); trdev,te=next(outer.split(X,y,groups))
 inner=GroupShuffleSplit(n_splits=1,test_size=.25,random_state=seed+1); tri,devi=next(inner.split(X[trdev],y[trdev],groups[trdev])); tr=trdev[tri]; dev=trdev[devi]
 r=RandomForestRegressor(**{**params,'random_state':seed}).fit(X[tr],y[tr]); p=r.predict(X[te]); rd=RandomForestRegressor(**{**params,'random_state':seed}).fit(D[tr],y[tr]); pd_=rd.predict(D[te])
 c=RandomForestClassifier(**{**params,'random_state':seed,'class_weight':'balanced_subsample'}).fit(X[tr],yc[tr]); prob=c.predict_proba(X[te])[:,1] if len(c.classes_)==2 else np.zeros(len(te))
 top=min(10,len(te)); order=np.argsort(-prob)[:top]; pos=float(yc[te].mean()); ef=float(yc[te][order].sum()/(top*pos)) if pos>0 else None
 rm={'seed':seed,'train_n':len(tr),'dev_n':len(dev),'test_n':len(te),'train_scaffolds':len(set(groups[tr])),'dev_scaffolds':len(set(groups[dev])),'test_scaffolds':len(set(groups[te])),'test_positive_rate':pos,'reg_MAE':float(mean_absolute_error(y[te],p)),'reg_RMSE':float(mean_squared_error(y[te],p)**.5),'reg_Spearman':float(spearmanr(y[te],p).statistic) if len(set(y[te]))>1 else None,'desc_MAE':float(mean_absolute_error(y[te],pd_)),'desc_RMSE':float(mean_squared_error(y[te],pd_)**.5),'desc_Spearman':float(spearmanr(y[te],pd_).statistic) if len(set(y[te]))>1 else None,'classification':aucs(yc[te],prob),'top10_hits':int(yc[te][order].sum()),'top10_EF':ef,'test_classes':sorted(set(yc[te].tolist()))}
 res.append(rm); split_info.append({'seed':seed,'train_indices':tr.tolist(),'dev_indices':dev.tolist(),'test_indices':te.tolist()})
# Summary across seeds; no seed chosen by performance.
mdf=pd.DataFrame([{**r,'roc_auc':r['classification']['roc_auc'],'pr_auc':r['classification']['pr_auc']} for r in res])
mdf.to_csv(OUT/'multiseed_locked_metrics.csv',index=False,encoding='utf-8-sig')
summary={'generated_at':'2026-09-10','model_id':'FXR_LanthaScreen_EC50_ECFP_RF_v1_sensitivity','assay':ASSAY,'records':len(x),'scaffolds':int(x.scaffold.nunique()),'predeclared_seeds':SEEDS,'metrics_summary':{},'per_seed':res,'split_indices':split_info,'selection_rule':'no seed selected by best score; all predeclared seeds reported','status':'sensitivity_analysis_not_external_validation'}
for c in ['reg_MAE','reg_RMSE','reg_Spearman','desc_MAE','desc_RMSE','desc_Spearman','top10_EF','roc_auc','pr_auc']:
 vals=pd.to_numeric(mdf[c],errors='coerce').dropna(); summary['metrics_summary'][c]={'n':int(len(vals)),'mean':float(vals.mean()) if len(vals) else None,'sd':float(vals.std(ddof=1)) if len(vals)>1 else None,'min':float(vals.min()) if len(vals) else None,'max':float(vals.max()) if len(vals) else None}
(OUT/'multiseed_locked_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(mdf.to_string(index=False)); print('\nSUMMARY',json.dumps(summary['metrics_summary'],ensure_ascii=False,indent=2))
