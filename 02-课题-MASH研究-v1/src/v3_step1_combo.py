# -*- coding: utf-8 -*-
"""
V3 Step1: COMBINATION synergy design (next-phase direction).
Logic: orthogonal-axis coverage (nuclear-receptor axis vs lipogenesis axis vs
inflammation-indirect axis vs fibrosis axis) — complementary target sets across
disease modules => synergy rationale (multi-module coverage, low redundancy).
Inputs: existing verified assets (QSAR profiles, docking, literature annotations).
"""
import itertools
import numpy as np
import pandas as pd

D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v3"
import os; os.makedirs(RES, exist_ok=True)

# agent pool: literature-verified assets with annotated axis evidence
# axes: NR=nuclear receptor (FXR/THRb/PPARG/LXRa), LIPO=lipogenesis(ACC/FASN/DGAT2/SCD/HMGCR/FDFT1),
# INFL=inflammation-indirect(TLR4/NF-kB, literature), FIB=fibrosis(literature)
AGENTS = {
 "Antrocinnamomin F (樟芝)": dict(axes={"NR": 2.0, "LIPO": 1.5},
     basis="5-target QSAR(NR+LIPO)+FXR/ACC/THRb三对接全<-8; 来源有NASH临床",
     obtain="发酵+标样", synergy_note="代谢轴多靶点主力"),
 "Alternaramide (海洋Alternaria环肽)": dict(axes={"INFL": 2.0, "LIPO": 0.5},
     basis="TLR4-MyD88/NF-kB抗炎机制文献(PMID 26620692)+ACC对接-8.3",
     obtain="菌株发酵", synergy_note="炎症间接作用轴主力, 零肝病报道"),
 "Butyrolactone VI (土曲霉)": dict(axes={"LIPO": 1.8, "NR": 0.8},
     basis="5-target QSAR(DGAT2/ACC2/THRb)+FXR/ACC对接<-7.9",
     obtain="土曲霉极易发酵", synergy_note="脂合成轴+PKA间接代谢效应"),
 "Versicolamide B (A. versicolor)": dict(axes={"INFL": 1.0, "FIB": 1.0},
     basis="家族notoamide Q肝IRI保护先例(PMID 37560942); 细胞保护类间接作用",
     obtain="全合成可得(Nat Chem 2009)", synergy_note="肝细胞保护间接轴"),
 "Asiatic acid (积雪草)": dict(axes={"FIB": 2.0},
     basis="抗肝纤维化多通路文献(PMID 35963324)",
     obtain="商品化", synergy_note="纤维化终点轴(MASH关键预后)"),
 "Berberine (黄连, 阳性对照)": dict(axes={"NR": 1.0, "LIPO": 1.0, "INFL": 0.8},
     basis="AMPK/TLR4多机制临床文献", obtain="商品化", synergy_note="已知多机制参照药"),
 "Resmetirom (上市药, 组合锚)": dict(axes={"NR": 2.0},
     basis="THR-b激动剂获批药", obtain="购买", synergy_note="与天然组分的转化医学桥"),
}
AXES = ["NR", "LIPO", "INFL", "FIB"]
AXNAME = {"NR": "核受体轴(FXR/THRb/PPARG/LXRa)", "LIPO": "脂合成轴(ACC/DGAT2/SCD/HMGCR)",
          "INFL": "炎症间接轴(TLR4/NF-kB)", "FIB": "纤维化轴(胶原/ECM)"}

rows = []
names = list(AGENTS)
for a, b in itertools.combinations(names, 2):
    A, Bg = AGENTS[a], AGENTS[b]
    cov = {ax: max(A["axes"].get(ax, 0), Bg["axes"].get(ax, 0)) for ax in AXES}
    # redundancy: overlap of both-covered axes
    both = sum(1 for ax in AXES if ax in A["axes"] and ax in Bg["axes"])
    n_axes = sum(1 for ax in AXES if cov[ax] > 0)
    sum_cov = sum(cov.values())
    score = round(sum_cov * (1 + 0.3 * (n_axes - 1)) / (1 + 0.25 * both), 2)
    rows.append(dict(combo=f"{a} + {b}", n_axes_covered=n_axes,
                     axes_covered="+".join(AXNAME[ax].split("(")[0] for ax in AXES if cov[ax] > 0),
                     redundancy_axes=both, synergy_score=score,
                     basis=f'{A["basis"]} || {Bg["basis"]}',
                     obtain=f'{A["obtain"]} + {Bg["obtain"]}'))
comb = pd.DataFrame(rows).sort_values("synergy_score", ascending=False)
comb.to_csv(f"{RES}/combination_synergy_design.csv", index=False)
print("=== TOP 10 SYNERGY-ORIENTED COMBINATIONS ===")
print(comb.head(10)[["combo", "n_axes_covered", "axes_covered", "redundancy_axes",
                     "synergy_score"]].to_string(index=False))

# triple combo (best rational design: 3 orthogonal axes)
best3 = None
for tri in itertools.combinations(names, 3):
    cov = set()
    for n in tri:
        cov |= set(AGENTS[n]["axes"])
    if len(cov) >= 4:
        print("\n3-drug orthogonal-axis design:", " + ".join(tri), "| axes:", cov)
        break
