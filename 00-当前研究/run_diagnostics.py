"""Recompute numerical consequences from frozen historical inputs, never release candidates."""
from pathlib import Path
import argparse,csv,json,sys,datetime,hashlib,platform
import numpy as np
import pandas as pd
from rdkit import Chem,DataStructs,__version__ as rdkit_version
from rdkit.Chem import rdFingerprintGenerator
from rdkit.ML.Cluster import Butina
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error,r2_score
from scipy.stats import spearmanr
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from methods import butina_labels,split_groups,conformal_radius,welch_de,signed_stouffer,ora_all
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'03-课题-MASH研究-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--fit-baseline',action='store_true');a=ap.parse_args();out=Path(a.output).resolve()
 if out.exists() and any(out.iterdir()):ap.error('Use a new empty output directory to preserve prior evidence')
 out.mkdir(parents=True,exist_ok=True);fpg=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)
 report={'mode':'historical_input_diagnostic','scientific_validation':'not_granted','wetlab_ready':False,'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),'rdkit':rdkit_version,'targets':{},'input_hashes':{},'scope':'MASH v2 molecular tables, clustering, optional RF, stored transcriptome reanalysis; no new activity assay review or efficacy validation'}
 for target in ['THRB','FASN','SCD1']:
  file=OLD/'data/chembl'/f'{target}_clean.csv';report['input_hashes'][str(file.relative_to(ROOT))]=sha(file);df=pd.read_csv(file);mols=[Chem.MolFromSmiles(s) for s in df.std_smiles]
  if any(m is None for m in mols):raise ValueError(target+' invalid molecule')
  fps=[fpg.GetFingerprint(m) for m in mols];n=len(fps)
  wrong=[1-DataStructs.TanimotoSimilarity(fps[i],fps[j]) for i in range(n) for j in range(i+1,n)]
  old_clusters=Butina.ClusterData(wrong,n,0.4,isDistData=True)
  labels,clusters=butina_labels(fps);tr,va,te=split_groups(labels)
  def center_violations(cs):return sum(DataStructs.TanimotoSimilarity(fps[c[0]],fps[j])<0.6-1e-9 for c in cs for j in c[1:])
  assert center_violations(clusters)==0
  maxsim=[max(DataStructs.BulkTanimotoSimilarity(fps[i],[fps[j] for j in tr])) for i in te]
  info={'n':n,'canonical_unique':len({Chem.MolToSmiles(m) for m in mols}),'old_clusters':len(old_clusters),'correct_clusters':len(clusters),'old_members_outside_center_cutoff':center_violations(old_clusters),'correct_members_outside_center_cutoff':0,'correct_split_sizes':[len(tr),len(va),len(te)],'distance_cutoff':0.4,'equivalent_center_similarity':0.6,'test_to_train_max_similarity':max(maxsim),'test_near_neighbor_ge_0_8':sum(s>=0.8 for s in maxsim),'assay_provenance_present':all(c in df.columns for c in ['activity_id','assay_chembl_id','document_chembl_id'])}
  assignments=np.empty(n,dtype=object)
  for ids,name in [(tr,'train'),(va,'calibration'),(te,'test')]:assignments[ids]=name
  df.assign(row_id=np.arange(n),cluster=labels,split=assignments).to_csv(out/f'{target}_diagnostic_split.csv',index=False)
  if a.fit_baseline:
   X=np.array([np.array(fp) for fp in fps]);y=df.pIC50.to_numpy();model=RandomForestRegressor(n_estimators=300,random_state=42,n_jobs=4).fit(X[tr],y[tr]);pred=model.predict(X[te]);cal=model.predict(X[va]);q=conformal_radius(np.abs(y[va]-cal))
   info['corrected_RF_diagnostic']={'seed':42,'n_estimators':300,'RMSE':float(np.sqrt(mean_squared_error(y[te],pred))),'mean_baseline_RMSE':float(np.sqrt(np.mean((y[te]-y[tr].mean())**2))),'R2':float(r2_score(y[te],pred)),'Spearman':float(spearmanr(pred,y[te]).statistic),'calibration_radius':q if np.isfinite(q) else 'unbounded','empirical_test_coverage':float(np.mean(abs(y[te]-pred)<=q)),'interval_claim':'empirical only; cluster shift/extrapolation do not guarantee 95% coverage'}
   pd.DataFrame({'row_id':te,'y':y[te],'pred':pred,'maxTan_train':maxsim}).to_csv(out/f'{target}_RF_diagnostic_test.csv',index=False)
  report['targets'][target]=info
 lib=pd.read_csv(OLD/'data/tcm/np_library_filtered.csv');report['np_library']={'rows':len(lib),'columns':list(lib.columns),'valid_smiles':sum(Chem.MolFromSmiles(s) is not None for s in lib.smiles),'unique_isomeric_smiles':len({Chem.MolToSmiles(Chem.MolFromSmiles(s)) for s in lib.smiles})}
 target_table=pd.read_csv(OLD/'results/tables/target_validation_new.csv');focus=target_table[target_table.gene.isin(['THRB','FASN','SCD','DGAT2'])][['gene','p_meta','padj_meta']];report['historical_target_FDR']=focus.to_dict('records')
 report['clinical_target_confirmation_from_expression']='not established: all four historical FDR > 0.05; expression association is not intervention causality'
 # Independent descriptive Welch reanalysis using saved gene-expression inputs.
 comparisons=[]
 for cohort in ['GSE48452','GSE63067']:
  expr=OLD/'data/geo'/f'{cohort}_gene_expr.csv.gz';meta=OLD/'data/geo'/f'{cohort}_meta.csv'
  if not expr.exists():report.setdefault('missing_inputs',[]).append(str(expr.relative_to(ROOT)));continue
  report['input_hashes'][str(expr.relative_to(ROOT))]=sha(expr);report['input_hashes'][str(meta.relative_to(ROOT))]=sha(meta)
  mat=pd.read_csv(expr,index_col=0);md=pd.read_csv(meta,index_col=0)
  column,positive,negative=('group','Nash','Control') if cohort=='GSE48452' else ('disease status','non-alcoholic steatohepatitis','healthy')
  ai=md.index[md[column]==positive];bi=md.index[md[column]==negative];lfc,pv,qv=welch_de(mat[ai],mat[bi]);res=pd.DataFrame({'log2FC':lfc,'p':pv,'padj':qv},index=mat.index);res.to_csv(out/f'{cohort}_welch_diagnostic.csv');comparisons.append((res,len(ai),len(bi)))
 if len(comparisons)==2:
  r1,r2=[x[0] for x in comparisons];shared=r1.index.intersection(r2.index);z,pv,qv=signed_stouffer(np.array([r1.loc[shared,'p'],r2.loc[shared,'p']]),np.array([r1.loc[shared,'log2FC'],r2.loc[shared,'log2FC']]),[(x[1],x[2]) for x in comparisons]);res=pd.DataFrame({'z_meta':z,'p_meta':pv,'padj_meta':qv},index=shared);res.to_csv(out/'welch_meta_diagnostic.csv');report['welch_meta_focus']=res.loc[res.index.intersection(['THRB','FASN','SCD','DGAT2'])].reset_index().to_dict('records');report['transcriptome_limit']='Unadjusted diagnostic, not limma; covariates, annotation ambiguity, independent cohorts and normalization require review.'
 dump(out/'diagnostic_summary.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
