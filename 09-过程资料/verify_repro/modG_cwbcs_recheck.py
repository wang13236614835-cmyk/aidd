# -*- coding: utf-8 -*-
"""
模块G独立复算：CW-BCS评分与中药排名（含圆桌修正版）。
独立实现公式（与step7不同的代码路径）：
  CW-BCS = [clip(w*s_FXR,eps) * clip(s_THRB,eps) * clip(s_ACC,eps)]^(1/3), w=1/(1+sigma)
  herb_score = top3几何均值 * (1 - 冗余惩罚), 冗余=max(0,(meanTan-0.6)/0.4) cap 0.5
对账声明: 黄连0.718 苦参0.585 甘草0.566 雷公藤0.565 丹参0.545
修正版(收缩 score*n/(n+5)): 0.529/0.458/0.443/丹参0.427/青蒿0.375
"""
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"

pred = pd.read_csv(f"{D}/results/tables/np_fxr_predictions.csv")
dock = pd.read_csv(f"{D}/results/tables/np_docking_raw.csv")
print(f"docking rows={len(dock)} (claim 262 = 131x2) | targets={dock['target'].value_counts().to_dict()}")

thrb = dock[dock.target == "THRB_3GWS"][["herb", "name", "affinity"]].rename(columns={"affinity": "dG_THRB"})
acc = dock[dock.target == "ACC2_5KKN"][["herb", "name", "affinity"]].rename(columns={"affinity": "dG_ACC"})
df = pred.merge(thrb, on=["herb", "name"], how="outer").merge(acc, on=["herb", "name"], how="outer")

# min-max（独立写法）
def mm(s):
    s = s.astype(float)
    lo, hi = np.nanmin(s.values), np.nanmax(s.values)
    return pd.Series((s.values - lo) / (hi - lo), index=s.index)

sF = mm(df["fxr_mu_pIC50"]); sT = mm(-df["dG_THRB"]); sA = mm(-df["dG_ACC"])
w = 1.0 / (1.0 + df["fxr_sigma"].fillna(3.0))
EPS = 1e-3
cw = ((np.clip(w * sF, EPS, None) * np.clip(sT, EPS, None) * np.clip(sA, EPS, None)) ** (1 / 3)).round(4)
df["CW_mine"] = cw.values

# 与存档compound_cwbcs_full.csv对账
arch = pd.read_csv(f"{D}/results/tables/compound_cwbcs_full.csv")
j = df.merge(arch, on=["herb", "name"], suffixes=("_m", "_a"))
dcw = (j["CW_mine"] - j["CW_BCS"]).abs()
print(f"compound-level CW-BCS: n={len(j)} max|d|={dcw.max()} mean|d|={dcw.mean():.5f} n_exact={(dcw<1e-6).sum()}")

# herb排名独立重算
mfg = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
rows = []
for herb, g in df.groupby("herb"):
    top = g.sort_values("CW_mine", ascending=False).head(3)
    fps = [mfg.GetFingerprint(Chem.MolFromSmiles(s)) for s in top["smiles"]]
    sims = [DataStructs.TanimotoSimilarity(fps[i], fps[j])
            for i in range(len(fps)) for j in range(i + 1, len(fps)) if fps[i] and fps[j]]
    msim = float(np.mean(sims)) if sims else 0.0
    pen = min(max((msim - 0.6) / 0.4, 0.0), 0.5)
    geo = float(np.exp(np.log(top["CW_mine"].clip(lower=1e-4)).mean()))
    rows.append(dict(herb=herb, n=len(g), geo=round(geo, 4), tan=round(msim, 3),
                     pen=round(pen, 3), score=round(geo * (1 - pen), 4)))
rank_mine = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
print("\nMY herb ranking:")
print(rank_mine.to_string(index=False))

rank_arch = pd.read_csv(f"{D}/results/tables/herb_cwbcs_ranking.csv")
print("\nARCHIVED herb ranking (top 6):")
print(rank_arch.head(6).to_string(index=False))
jj = rank_mine.merge(rank_arch, on="herb", suffixes=("_m", "_a"))
print(f"\nherb_score mine vs archived: max|d|={(jj['score_m']-jj['herb_score']).abs().max()}, "
      f"rank agreement: {(jj['score_m'].rank(ascending=False).astype(int) == jj['rank_a']).all()}")

# 圆桌修正版（经验贝叶斯收缩 score*n/(n+5)）+ 代表成分硬约束
fix_arch = pd.read_csv(f"{D}/results/tables/herb_cwbcs_ranking_fix.csv")
print("\nARCHIVED fixed ranking (shrinkage):")
print(fix_arch.head(8).to_string(index=False))
jjj = jj.copy()
jjj["shrunk_mine"] = (jjj["score_m"] * jjj["n_m"] / (jjj["n_m"] + 5)).round(4)
jf = jjj.merge(fix_arch, on="herb")
cols = [c for c in jf.columns if "shrink" in c.lower() or "shrunk" in c.lower() or c == "herb"]
print("\nmy shrunk vs archived fix:")
cmp_col = [c for c in fix_arch.columns if "shrink" in c.lower() or "score" in c.lower()]
print(jf[["herb", "shrunk_mine"] + cmp_col[:2]].to_string(index=False))
