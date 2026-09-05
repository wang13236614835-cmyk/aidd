# -*- coding: utf-8 -*-
"""
S2: ChEMBL数据获取+清洗（全新实现）。
三靶点: THRB(CHEMBL1947, 激动方向用IC50记录), FASN(CHEMBL4158), SCD1(CHEMBL1275210)。
拉取: target_chembl_id + standard_type=IC50 + assay_type=B + Homo sapiens + relation '=' + nM。
清洗: 盐剥离→最大片段→混合物剔除→MW>=150→pIC50→规范SMILES去重(均值)→PAINS A/B/C。
"""

# Historical pipeline: its outputs are invalidated; corrected code lives in 00-当前研究.
raise RuntimeError("此历史入口已停用以保留原数据与结果；请使用仓库00-当前研究中的诊断/修订流程。")
import json, time, urllib.parse, urllib.request
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors
from rdkit.Chem import FilterCatalog
from rdkit.Chem.SaltRemover import SaltRemover

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_v2_new"
OUT = f"{D}/data/chembl"
TARGETS = {"THRB": "CHEMBL1947", "FASN": "CHEMBL4158", "SCD1": "CHEMBL1275210"}
UA = {"User-Agent": "academic-drug-research/2.0"}

def fetch_all(target, standard_type="IC50"):
    """activity.json过滤参数式分页拉取"""
    base = "https://www.ebi.ac.uk/chembl/api/data/activity.json"
    rows, offset = [], 0
    while True:
        params = urllib.parse.urlencode({
            "target_chembl_id": target, "standard_type": standard_type,
            "assay_type": "B", "organism": "Homo sapiens",
            "standard_relation": "=", "standard_units": "nM",
            "limit": 100, "offset": offset, "format": "json"})
        req = urllib.request.Request(f"{base}?{params}", headers=UA)
        js = json.loads(urllib.request.urlopen(req, timeout=120).read())
        acts = js.get("activities", [])
        rows += acts
        total = js["page_meta"]["total_count"]
        offset += 100
        if offset >= total or not acts:
            break
        time.sleep(0.35)
    print(f"  {target} {standard_type}: fetched {len(rows)}/{total}")
    return rows

remover = SaltRemover()
def standardize(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None, None
    m = remover.StripMol(m, dontRemoveEverything=True)
    frags = Chem.GetMolFrags(m, asMols=True, sanitizeFrags=True)
    if len(frags) == 0:
        return None, None
    if len(frags) > 1:
        return "MIXTURE", None
    try:
        Chem.SanitizeMol(frags[0])
        return Chem.MolToSmiles(frags[0]), Descriptors.MolWt(frags[0])
    except Exception:
        return None, None

pc = FilterCatalog.FilterCatalogParams()
for c in [pc.FilterCatalogs.PAINS_A, pc.FilterCatalogs.PAINS_B, pc.FilterCatalogs.PAINS_C]:
    pc.AddCatalog(c)
fcat = FilterCatalog.FilterCatalog(pc)
def is_pains(smi):
    m = Chem.MolFromSmiles(smi)
    return m is not None and len(list(fcat.GetMatches(m))) > 0

summary = {}
for name, tid in TARGETS.items():
    print(f"\n===== {name} ({tid}) =====")
    rows = fetch_all(tid)
    df = pd.DataFrame([{
        "smiles": r.get("canonical_smiles"),
        "value": float(r["standard_value"]),
        "doc": r.get("document_chembl_id"),
        "assay": r.get("assay_chembl_id"),
        "mol": r.get("molecule_chembl_id"),
    } for r in rows if r.get("canonical_smiles") and r.get("standard_value")])
    df = df[df.value > 0]
    print(f"  exact-relation nM records: {len(df)}")
    std = df["smiles"].apply(standardize)
    df["std_smiles"] = [s[0] for s in std]
    df["mw"] = [s[1] for s in std]
    df = df[df.std_smiles.notna() & (df.std_smiles != "MIXTURE") & (df.mw >= 150)]
    print(f"  after salt/mix/MW: {len(df)}")
    df["pIC50"] = 9.0 - np.log10(df.value)
    g = df.groupby("std_smiles").agg(pIC50=("pIC50", "mean"), n_rep=("pIC50", "size")).reset_index()
    print(f"  unique: {len(g)} (max rep {g.n_rep.max()})")
    g["pains"] = g.std_smiles.apply(is_pains)
    g = g[~g.pains].drop(columns="pains").reset_index(drop=True)
    print(f"  after PAINS: {len(g)} | pIC50 {g.pIC50.min():.2f}-{g.pIC50.max():.2f}")
    g.to_csv(f"{OUT}/{name}_clean.csv", index=False)
    summary[name] = dict(target=tid, raw=len(rows), exact_nm=len(df), unique=int(g.n_rep.count() and len(g)),
                         final=len(g), pic50_range=[round(g.pIC50.min(), 2), round(g.pIC50.max(), 2)],
                         median_rep=float(g.n_rep.median()))
json.dump(summary, open(f"{OUT}/chembl_summary.json", "w"), indent=1)
print("\nsummary:", json.dumps(summary, indent=1))
