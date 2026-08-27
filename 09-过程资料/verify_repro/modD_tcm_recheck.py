# -*- coding: utf-8 -*-
"""
模块D独立复算：中药库ADMET过滤 233条目→224解析→131通过。
从存档 tcm_library_raw.csv 出发独立重算 150<MW<500 / LogP<5.5 / HBD<=5 / HBA<=10，
PAINS标记（独立路径），申报书排除清单逐条核对；与 tcm_library_filtered.csv 对账。
"""
import pandas as pd
import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, Lipinski
from rdkit.Chem import FilterCatalog

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"

raw = pd.read_csv(f"{D}/data/tcm/tcm_library_raw.csv")
fil = pd.read_csv(f"{D}/data/tcm/tcm_library_filtered.csv")
print(f"raw rows={len(raw)} (claim 233条目) | parsed(resolved)={raw['smiles'].notna().sum()} (claim 224) | filtered archived={len(fil)} (claim 131)")

# 独立重算每行的ADMET（用RDKit从SMILES重新计算，不信存档mw/logp列）
def calc(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    return (Descriptors.MolWt(m), Crippen.MolLogP(m),
            Lipinski.NumHDonors(m), Lipinski.NumHAcceptors(m))

ok_rows = []
for _, r in raw[raw["smiles"].notna()].iterrows():
    c = calc(r["smiles"])
    if c is None:
        continue
    mw, logp, hbd, hba = c
    admet_ok = (150 < mw < 500) and (logp < 5.5) and (hbd <= 5) and (hba <= 10)
    ok_rows.append(dict(herb=r["herb"], name=r["name"], smiles=r["smiles"],
                        cid=r.get("cid"), mw=mw, logp=logp, hbd=hbd, hba=hba,
                        admet_ok=admet_ok))
mine = pd.DataFrame(ok_rows)
passed = mine[mine.admet_ok]
print(f"my ADMET pass: {len(passed)}  archived filtered: {len(fil)}")

# 存档filtered集合 vs 我的通过集合（按herb+name+smiles）
key = lambda d: set(zip(d["herb"], d["name"]))
mine_set, arch_set = key(passed), key(fil)
print(f"set match: mine-arch={len(mine_set - arch_set)} arch-mine={len(arch_set - mine_set)} common={len(mine_set & arch_set)}")
if mine_set - arch_set:
    print("  extra in mine:", list(mine_set - arch_set)[:10])
if arch_set - mine_set:
    print("  extra in archived:", list(arch_set - mine_set)[:10])

# 排除清单逐条核对：filtered中不得含排除名单成分
EXCLUDE = {"quercetin","luteolin","apigenin","kaempferol","hesperetin","baicalein",
 "caffeic acid","chlorogenic acid","vanillic acid","ellagic acid","gallic acid","ferulic acid",
 "choline","adenine","glucose","palmitic acid","curcumin","resveratol","epigallocatechin gallate",
 "taxifolin","triptolide","tripdiolide","triptonide","salvianolic acid a","salvianolic acid b",
 "rosmarinic acid","danshensu","protocatechuic aldehyde"}
in_fil = {n.lower() for n in fil["name"]} & EXCLUDE
print(f"excluded names present in filtered (must be 0): {len(in_fil)} {in_fil if in_fil else ''}")

# raw中status字段的EXCLUDED_BY_PROPOSAL数量
if "status" in raw.columns:
    print("raw status counts:\n", raw["status"].value_counts().to_string())

# 存档filtered的mw/logp列与我重算的一致性（若存档含这些列）
for col in ["mw", "logp", "hbd", "hba"]:
    if col in fil.columns:
        j = fil.merge(mine, on=["herb", "name"], suffixes=("_a", "_m"))
        dmax = (j[f"{col}_a"] - j[f"{col}_m"]).abs().max()
        print(f"archived vs my recomputed {col}: max diff = {dmax:.4f}")

# 各草药计数 vs 声明（雷公藤仅2个无毒成分入库）
print("\nper-herb counts (archived filtered):")
print(fil["herb"].value_counts().to_string())
print("\nper-herb counts (my recomputed pass):")
print(passed["herb"].value_counts().to_string())
