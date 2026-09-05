# -*- coding: utf-8 -*-
"""
S6: TOPSIS多准则优先级排序（全新评分设计，非旧CW-BCS）。
准则(越大越优, docking已取负):
  C1 THRB_pIC50(QSAR) 0.25 | C2 FASN_pIC50 0.15 | C3 SCD1_pIC50 0.10
  C4 -dG_THRB(对接) 0.20    | C5 -dG_FASN 0.10
  C6 域适用度(三靶点maxTan均值) 0.15 | C7 药材证据等级(A=1,B=0.66,C+=0.33) 0.05
输出: 化合物TOPSIS贴近度+置信分层(域内/边缘/域外) + 药材级汇总 + 前20优先清单。
"""

# Historical pipeline: its outputs are invalidated; corrected code lives in 00-当前研究.
raise RuntimeError("此历史入口已停用以保留原数据与结果；请使用仓库00-当前研究中的诊断/修订流程。")
import json
import numpy as np
import pandas as pd

D = "D:/zcode-workspace/mash_v2_new"
pred = pd.read_csv(f"{D}/results/tables/np_predictions_new.csv")
dock = pd.read_csv(f"{D}/results/tables/np_docking_raw_new.csv")

dth = dock[dock.target == "THRB"][["herb", "name", "affinity"]].rename(columns={"affinity": "dG_THRB"})
dfa = dock[dock.target == "FASN"][["herb", "name", "affinity"]].rename(columns={"affinity": "dG_FASN"})
df = pred.merge(dth, on=["herb", "name"], how="left").merge(dfa, on=["herb", "name"], how="left")

EV = {"Artemisia capillaris(茵陈)": 1.0, "Polygonum cuspidatum(虎杖)": 0.66,
      "Sedum sarmentosum(垂盆草)": 0.66, "Crataegus pinnatifida(山楂)": 0.66,
      "Alisma orientale(泽泻)": 0.66, "Cassia obtusifolia(决明子)": 0.66,
      "Pueraria lobata(葛根)": 0.66, "Gynostemma pentaphyllum(绞股蓝)": 0.66,
      "Phyllanthus niruri(叶下珠)": 0.33, "Morus alba(桑叶)": 0.33}
df["evidence"] = df["herb"].map(EV).fillna(0.33)
df["negdG_THRB"] = -df["dG_THRB"]
df["negdG_FASN"] = -df["dG_FASN"]
df["ad_score"] = df[["THRB_maxTan_train", "FASN_maxTan_train", "SCD1_maxTan_train"]].mean(1)

CRIT = [("THRB_pIC50", 0.25), ("FASN_pIC50", 0.15), ("SCD1_pIC50", 0.10),
        ("negdG_THRB", 0.20), ("negdG_FASN", 0.10), ("ad_score", 0.15),
        ("evidence", 0.05)]
X = df[[c for c, _ in CRIT]].astype(float)
Xn = (X - X.min()) / (X.max() - X.min() + 1e-12)
w = np.array([wt for _, wt in CRIT]); w = w / w.sum()
V = Xn.values * w
best, worst = V.max(0), V.min(0)
db = np.sqrt(((V - best) ** 2).sum(1)); dw = np.sqrt(((V - worst) ** 2).sum(1))
df["topsis"] = np.round(dw / (db + dw + 1e-12), 4)

# 置信分层: 域适用度阈值(训练集maxTan) — 0.30/0.18两档(经验阈值,报告披露)
def tier(ad):
    if ad >= 0.30:
        return "T1_domain(域内参考)"
    if ad >= 0.18:
        return "T2_borderline(边缘)"
    return "T3_extrapolated(域外,仅供假设)"
df["confidence_tier"] = df["ad_score"].apply(tier)

df = df.sort_values("topsis", ascending=False).reset_index(drop=True)
df.to_csv(f"{D}/results/tables/np_topsis_full.csv", index=False)
top20 = df.head(20)[["herb", "name", "topsis", "confidence_tier", "THRB_pIC50",
                     "FASN_pIC50", "SCD1_pIC50", "dG_THRB", "dG_FASN", "ad_score"]]
top20.to_csv(f"{D}/results/tables/top20_priority.csv", index=False)
print("===== TOP-20 (TOPSIS) =====")
print(top20.to_string(index=False))

# 药材级汇总: top-20占据数(每味药进入前20的化合物数, 上限5) + 证据 + 库内化合物数
herb_rows = []
for herb, g in df.groupby("herb"):
    n_top = min((g.head(20).index < 20).sum(), 5)  # df已排序, 前20行
    n_top = int((g.index < 20).sum())
    herb_rows.append(dict(herb=herb, n_library=len(g), n_in_top20=n_top,
                          median_topsis=round(g.topsis.median(), 3),
                          best_compound=g.iloc[0]["name"],
                          best_topsis=g.iloc[0]["topsis"],
                          evidence=EV.get(herb, 0.33)))
hr = pd.DataFrame(herb_rows)
hr["priority_score"] = (0.6 * hr.n_in_top20.clip(0, 5) / 5 + 0.4 * hr.evidence).round(3)
hr = hr.sort_values("priority_score", ascending=False).reset_index(drop=True)
hr.to_csv(f"{D}/results/tables/herb_priority_new.csv", index=False)
print("\n===== 药材级优先级 =====")
print(hr.to_string(index=False))

print("\n===== 置信分层分布 =====")
print(df.confidence_tier.value_counts().to_string())
json.dump(dict(weights={c: float(x) for (c, x) in CRIT},
               tiers=df.confidence_tier.value_counts().to_dict()),
          open(f"{D}/results/tables/s6_summary.json", "w"), indent=1, ensure_ascii=False)
print("\nS6 complete.")
