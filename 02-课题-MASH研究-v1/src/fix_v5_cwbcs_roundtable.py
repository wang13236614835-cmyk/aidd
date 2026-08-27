# -*- coding: utf-8 -*-
"""
圆桌行动项 A1+A3（judge_verdict.md 第六节）：
A1  v5 终榜修正重跑：删 5 个无名/CAS 条目；千里光(PA肝毒)全药材除名并建黑名单；
    Obtain 改实证字段（07H239-A / Alisiaquinol 不可购置 0）；证据措辞更正；FINAL 原公式重算。
A3  CW-BCS 榜双修：经验贝叶斯收缩 score*n/(n+5) 重排；代表成分置信度硬约束。
输出新文件，不改原始文件（可溯源）。
"""
import pandas as pd

D = "D:/zcode-workspace/mash_research"

# ---------------- A1: v5 终榜修正 ----------------
df = pd.read_csv(f"{D}/results/v5/final_unified_scores.csv")

# 1) 除名：无名/CAS 指代条目 + 千里光（PA 吡咯里西啶生物碱肝毒药材）
drop_mask = (
    df["id"].str.contains("未名|CAS21637", na=False)
    | df["id"].str.contains("千里光", na=False)
)
removed = df[drop_mask][["id", "FINAL"]].copy()
df = df[~drop_mask].copy()

# 2) Obtain 实证修正：07H239-A（LL-07H239 菌株不在 ATCC/NRRL）、Alisiaquinol（未鉴定海绵）不可购
for key in ["07H239-A", "Alisiaquinol"]:
    df.loc[df["id"].str.contains(key, na=False), "Obtain"] = 0.0

# 3) 证据措辞更正：樟芝"RCT"→物种级临床证据（裁判共识 #10 / 行动项 B4）
df.loc[df["id"].str.contains("Antrocinnamomin|樟芝", na=False), "Evidence_note"] = (
    "樟芝物种级临床证据(28例菌丝体全粉,SteatoTest血清学终点,PMID32657670)+双异源计算交叉印证"
)

# 4) FINAL 按原公式重算（asiatic acid 无计算分，保持 FINAL 为空、以直接文献入列）
def final_row(r):
    if pd.isna(r["Act"]) and pd.isna(r["Dock"]):
        return float("nan")
    act = 0.0 if pd.isna(r["Act"]) else r["Act"]
    dock = 0.0 if pd.isna(r["Dock"]) else r["Dock"]
    ev = r["Evidence"]; nov = r["Novelty"]; obt = r["Obtain"]
    return round(0.35 * act + 0.25 * dock + 0.20 * ev + 0.10 * nov + 0.10 * obt, 3)

df["FINAL"] = df.apply(final_row, axis=1)

# 5) 敏感性：樟芝 Evidence 1.0→0.7（若按更严证据等级计）检验位次稳定性
zz = df[df["id"].str.contains("Antrocinnamomin|樟芝", na=False)].iloc[0]
alt = round(0.35 * zz["Act"] + 0.25 * zz["Dock"] + 0.20 * 0.7 + 0.10 * zz["Novelty"] + 0.10 * zz["Obtain"], 3)

df["rank_basis"] = ""
df.loc[df["id"].str.contains("asiatic acid", na=False), "rank_basis"] = "无计算分,以直接文献(PMID35963324)入列"
df = df.sort_values("FINAL", ascending=False, na_position="last").reset_index(drop=True)
df.insert(0, "rank", range(1, len(df) + 1))
df.to_csv(f"{D}/results/v5/final_unified_scores_fix.csv", index=False)

print("=== A1 修正后 v5 终榜 ===")
print(df[["rank", "id", "Act", "Dock", "Evidence", "Novelty", "Obtain", "FINAL"]].to_string(index=False))
print("\n除名条目:", removed.to_dict("records"))
print(f"樟芝 Evidence=0.7 敏感性 FINAL = {alt}（第二名 {df.iloc[1]['id']}={df.iloc[1]['FINAL']}）")

# ---------------- A3: CW-BCS 榜双修 ----------------
h = pd.read_csv(f"{D}/results/tables/herb_cwbcs_ranking.csv")
h["herb_score_shrunk"] = (h["herb_score"] * h["n_compounds"] / (h["n_compounds"] + 5)).round(4)
h = h.sort_values("herb_score_shrunk", ascending=False).reset_index(drop=True)
h.insert(0, "rank_shrunk", range(1, len(h) + 1))

# 代表成分置信硬约束：域内低置信成分不得单独作代表 → 从成分表找高置信代表
c = pd.read_csv(f"{D}/results/tables/compound_cwbcs_full.csv")
notes = []
for i, row in h.iterrows():
    herb = row["herb"]
    sub = c[c["herb"] == herb].copy()
    hi = sub[sub["tier"] == "in_domain_high_conf(域内高置信)"].sort_values("CW_BCS", ascending=False)
    if "低置信" in str(row["best_tier"]):
        if len(hi) > 0:
            notes.append(f"{herb}: 代表成分改为高置信 {hi.iloc[0]['name']}(CW_BCS={hi.iloc[0]['CW_BCS']:.3f})，原最佳 {row['best_compound']}(低置信)列为次代表")
            h.at[i, "rep_fix"] = f"{hi.iloc[0]['name']}({hi.iloc[0]['tier'][:18]})"
        else:
            notes.append(f"{herb}: 无高置信成分，保留 {row['best_compound']} 并强制标注[域内低置信，双代表待补]")
            h.at[i, "rep_fix"] = f"{row['best_compound']}[低置信警示]"
    elif "域外" in str(row["best_tier"]):
        if len(hi) > 0:
            notes.append(f"{herb}: 最佳成分为域外预警，并列高置信代表 {hi.iloc[0]['name']}(CW_BCS={hi.iloc[0]['CW_BCS']:.3f})，域外条目降为参考")
            h.at[i, "rep_fix"] = f"{hi.iloc[0]['name']}({hi.iloc[0]['tier'][:18]})+{row['best_compound']}[域外参考]"
        else:
            notes.append(f"{herb}: 全部成分域外预警，整药材标注[域外警示药材]")
            h.at[i, "rep_fix"] = f"{row['best_compound']}[域外警示药材]"
    else:
        h.at[i, "rep_fix"] = f"{row['best_compound']}({str(row['best_tier'])[:18]})"

h.to_csv(f"{D}/results/tables/herb_cwbcs_ranking_fix.csv", index=False)
print("\n=== A3 收缩+置信约束后中药榜 ===")
print(h[["rank_shrunk", "herb", "n_compounds", "herb_score", "herb_score_shrunk", "best_compound", "best_tier", "rep_fix"]].to_string(index=False))
print("\n代表成分修正记录:")
for n in notes:
    print("-", n)
