# -*- coding: utf-8 -*-
"""
模块F独立核验：分子对接。
1) 从存档输出PDBQT+晶体SDF独立重算4个重对接RMSD（声明: 33Y=1.22, T3=0.42, 6U3=0.76, S1A=0.33, 全<2Å）
2) 阳性对照表 vs FINAL_REPORT引用值
3) NP批量对接最优值（声明: ACC最强-11.61, THRβ最强-10.28）
4) FXR交叉对接 Spearman(GNN μ, Vina ΔG) = -0.394, 范围-8.5~-10.6
"""
import json
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolAlign
from meeko import PDBQTMolecule
from meeko.rdkit_mol_create import RDKitMolCreate

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"

rv = json.load(open(f"{D}/docking/redock_validation.json"))
print("=== [1] redock RMSD independent recompute (from saved outputs) ===")
for tag, info in rv.items():
    lig = info["ligand"]
    sdf = f"{D}/docking/receptors/{tag}_{lig}_crystal.sdf"
    outp = f"{D}/docking/outputs/{tag}_{lig}_redock_out.pdbqt"
    ref = Chem.SDMolSupplier(sdf, removeHs=False)[0]
    refH = Chem.AddHs(ref, addCoords=True)
    txt = open(outp).read()
    first = "MODEL" + txt.split("MODEL")[1].split("ENDMDL")[0] + "ENDMDL\n"
    pmol = PDBQTMolecule(first, skip_typing=True)
    mol = RDKitMolCreate.from_pdbqt_mol(pmol)[0]
    pose, refnoh = Chem.RemoveHs(mol), Chem.RemoveHs(refH)
    # ① 与原脚本同方法:GetBestRMS(对称感知)
    rms_sym = float(rdMolAlign.GetBestRMS(pose, refnoh))
    # ② 更朴素口径:不做对称、直接对齐最小二乘RMSD
    rms_align = float(rdMolAlign.AlignMol(pose, refnoh))
    # ③ 完全不对齐的坐标RMSD
    c1 = pose.GetConformer().GetPositions(); c2 = refnoh.GetConformer().GetPositions()
    rms_raw = float(np.sqrt(((c1 - c2) ** 2).sum(1).mean()))
    ok = abs(rms_sym - info["rmsd"]) < 1e-3
    print(f"{tag:12s} {lig:4s}: archived={info['rmsd']:.4f} mine(GetBestRMS)={rms_sym:.4f} "
          f"{'PASS' if ok else 'FAIL'} | align-only={rms_align:.3f} no-align={rms_raw:.3f} "
          f"| gate<2Å: {'PASS' if rms_sym < 2 else 'FAIL'}")

print("\n=== [2] positive controls vs FINAL_REPORT quotes ===")
pc = pd.read_csv(f"{D}/results/tables/positive_controls_docking.csv")
claims = {("FXR_3FLI", "GW4064"): -9.70, ("FXR_3FLI", "tanshinone IIA"): -9.73,
          ("FXR_3FLI", "chenodeoxycholic acid"): -8.70, ("FXR_3FLI", "obeticholic acid"): -6.77,
          ("THRB_3GWS", "resmetirom"): -10.11, ("THRB_3GWS", "liothyronine"): -9.52,
          ("ACC2_5KKN", "ND-646"): -10.52}
for (t, n), c in claims.items():
    a = float(pc[(pc.target == t) & (pc.control == n)].affinity.iloc[0])
    print(f"  {t} {n:28s}: table={a:.3f} report={c:.2f} {'PASS' if abs(a-c)<0.006 else 'FAIL'}")

print("\n=== [3] NP docking extremes ===")
nd = pd.read_csv(f"{D}/results/tables/np_docking_raw.csv")
for tgt, claim in [("ACC2_5KKN", -11.61), ("THRB_3GWS", -10.28)]:
    sub = nd[nd.target == tgt]
    mn = sub.loc[sub.affinity.idxmin()]
    print(f"  {tgt}: best={mn.affinity} ({mn['name']}) | claim {claim} "
          f"{'PASS' if abs(mn.affinity-claim)<0.01 else 'FAIL'}")

print("\n=== [4] FXR cross-docking Spearman ===")
cd = pd.read_csv(f"{D}/results/tables/fxr_crossdocking_top10.csv")
from scipy.stats import spearmanr
r1 = spearmanr(cd["fxr_mu"], cd["dG_FXR_3FLI"]).statistic
r2 = spearmanr(cd["fxr_mu"], cd["dG_FXR_1OSH"]).statistic
r_both_pool = spearmanr(np.tile(cd["fxr_mu"], 2),
                        pd.concat([cd["dG_FXR_3FLI"], cd["dG_FXR_1OSH"]])).statistic
print(f"  n={len(cd)} | Spearman(mu,dG_3FLI)={r1:.3f} | (mu,dG_1OSH)={r2:.3f} | pooled={r_both_pool:.3f}")
print(f"  claim -0.394; dG range {cd[['dG_FXR_3FLI','dG_FXR_1OSH']].min().min():.1f}~{cd[['dG_FXR_3FLI','dG_FXR_1OSH']].max().max():.1f} (claim -8.5~-10.6)")
# 也算平均dG口径
r_avg = spearmanr(cd["fxr_mu"], (cd["dG_FXR_3FLI"]+cd["dG_FXR_1OSH"])/2).statistic
print(f"  avg-dG口径: {r_avg:.3f}")
