"""Reviewed numerical primitives; scientific dataset review remains separate."""
import numpy as np
from rdkit import DataStructs
from rdkit.ML.Cluster import Butina
from scipy import stats
from statsmodels.stats.multitest import multipletests

def butina_labels(fps, distance_cutoff=0.4):
    # RDKit expects lower-triangle row-major distances, NOT scipy condensed order.
    distances=[]
    for i in range(1,len(fps)):
        distances.extend(1-np.array(DataStructs.BulkTanimotoSimilarity(fps[i],fps[:i])))
    clusters=Butina.ClusterData(distances,len(fps),distance_cutoff,isDistData=True)
    labels=np.empty(len(fps),dtype=int)
    for label,cluster in enumerate(clusters):labels[list(cluster)]=label
    return labels,clusters

def split_groups(labels,seed=42):
    # Random tie-breaking within size order; no sample-level cluster splitting.
    rng=np.random.default_rng(seed);groups=np.unique(labels);rng.shuffle(groups)
    groups=sorted(groups,key=lambda g:-sum(labels==g));parts=[[],[],[]];n=len(labels)
    for g in groups:
        k=0 if len(parts[0])<0.8*n else 1 if len(parts[1])<0.1*n else 2
        parts[k].extend(np.flatnonzero(labels==g).tolist())
    if any(len(part)<2 for part in parts):raise ValueError('Clusters cannot support a three-way split; change design explicitly, do not split clusters silently.')
    return tuple(np.array(part,dtype=int) for part in parts)

def conformal_radius(residuals,alpha=0.05):
    if not 0<alpha<1:raise ValueError('alpha must lie strictly between zero and one')
    r=np.asarray(residuals,dtype=float)
    if r.ndim!=1 or len(r)==0 or not np.isfinite(r).all() or (r<0).any():raise ValueError('Invalid calibration residuals')
    k=int(np.ceil((len(r)+1)*(1-alpha)))
    # Insufficient finite-sample calibration yields an unbounded interval.
    return float('inf') if k>len(r) else float(np.sort(r)[k-1])

def welch_de(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if a.shape[0]!=b.shape[0] or min(a.shape[1],b.shape[1])<2:raise ValueError('Invalid expression groups')
    statistic,p=stats.ttest_ind(a,b,axis=1,equal_var=False,nan_policy='omit')
    finite=np.isfinite(p);adjusted=np.full(len(p),np.nan);adjusted[finite]=multipletests(p[finite],method='fdr_bh')[1]
    return np.nanmean(a,axis=1)-np.nanmean(b,axis=1),p,adjusted

def signed_stouffer(p_values,effects,group_sizes):
    p=np.asarray(p_values,float);effects=np.asarray(effects,float)
    if p.shape!=effects.shape or p.shape[0]!=len(group_sizes):raise ValueError('Cohort shapes differ')
    # Effective sample sizes for independent two-group comparisons, sqrt(n_a*n_b/(n_a+n_b)).
    weights=np.array([np.sqrt(a*b/(a+b)) for a,b in group_sizes])
    z=stats.norm.isf(np.clip(p,np.finfo(float).tiny,1)/2)*np.sign(effects)
    combined=np.sum(weights[:,None]*z,axis=0)/np.sqrt(np.sum(weights**2))
    result=2*stats.norm.sf(np.abs(combined));valid=np.isfinite(result);q=np.full(len(result),np.nan)
    q[valid]=multipletests(result[valid],method='fdr_bh')[1]
    return combined,result,q

def ora_all(pathways,universe,selected):
    universe=set(universe);selected=set(selected)&universe;rows=[]
    for name,genes in pathways.items():
        genes=set(genes)&universe
        if not genes:continue
        overlap=len(genes&selected)
        rows.append({'pathway':name,'overlap':overlap,'size':len(genes),'p':float(stats.hypergeom.sf(overlap-1,len(universe),len(genes),len(selected)))})
    if rows:
        q=multipletests([r['p'] for r in rows],method='fdr_bh')[1]
        for r,v in zip(rows,q):r['padj']=float(v)
    return sorted(rows,key=lambda r:r['p'])
