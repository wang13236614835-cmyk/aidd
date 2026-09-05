from pathlib import Path
import json,sys,datetime
import numpy as np
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.ML.Cluster import Butina
from scipy import stats
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from methods import butina_labels,split_groups,conformal_radius,welch_de,signed_stouffer,ora_all
HERE=Path(__file__).resolve().parent
def main():
 results=[]
 def check(name,fn):
  try:detail=fn();results.append({'name':name,'passed':True,'detail':detail})
  except Exception as e:results.append({'name':name,'passed':False,'detail':str(e)})
 def cluster_test():
  smi=['CCO','CCCO','c1ccccc1','Cc1ccccc1','CCN','CCCCN','c1ccncc1'];gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048);fps=[gen.GetFingerprint(Chem.MolFromSmiles(s)) for s in smi];matrix=np.array([[1-DataStructs.TanimotoSimilarity(x,y) for y in fps] for x in fps]);labels,clusters=butina_labels(fps)
  full=Butina.ClusterData(matrix,len(fps),0.4,isDistData=True)
  assert {frozenset(c) for c in clusters}=={frozenset(c) for c in full}
  return 'Lower-triangle implementation agrees with independent full-matrix clustering.'
 def conformal_test():
  assert conformal_radius(np.arange(1,20))==19
  assert np.isinf(conformal_radius(np.arange(1,19)))
  assert conformal_radius(np.arange(1,41),alpha=.1)==37
  return 'Exact order statistic and insufficient-calibration infinite radius verified.'
 def welch_test():
  a=np.array([[1,2,3,4],[2,6,9,11]],float);b=np.array([[4,5,5],[1,1,2]],float);lfc,p,q=welch_de(a,b)
  independent=[]
  for x,y in zip(a,b):
   va=x.var(ddof=1)/len(x);vb=y.var(ddof=1)/len(y);df=(va+vb)**2/(va**2/(len(x)-1)+vb**2/(len(y)-1));t=(x.mean()-y.mean())/np.sqrt(va+vb);independent.append(2*stats.t.sf(abs(t),df))
  assert np.allclose(p,independent);assert np.all(q>=p)
  return 'Welch statistic uses unequal-variance degrees of freedom; BH includes all valid tests.'
 def meta_test():
  z,p,q=signed_stouffer(np.array([[.05,.05],[.05,.05]]),np.array([[1,1],[1,-1]]),[(18,14),(9,7)])
  z0=stats.norm.isf(.025);w=np.sqrt([18*14/32,9*7/16]);assert np.allclose(z,[z0*w.sum()/np.linalg.norm(w),z0*(w[0]-w[1])/np.linalg.norm(w)])
  return 'Signed effects and effective-sample weights independently checked.'
 def ora_test():
  rows=ora_all({'hit':{1,2},'zero':{8,9}},range(10),{1,2});assert len(rows)==2
  assert next(x for x in rows if x['pathway']=='zero')['p']==1
  return 'Zero-overlap tested pathways retained in BH family.'
 for name,fn in [('Butina_distance_order',cluster_test),('finite_sample_conformal',conformal_test),('Welch_formula',welch_test),('signed_meta_weights',meta_test),('ORA_test_family',ora_test)]:check(name,fn)
 result={'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'software_passed':all(r['passed'] for r in results),'scientific_validation':'not_granted','checks':results}
 out=HERE/'validation/software_checks.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['software_passed'] else 1
if __name__=='__main__':sys.exit(main())
