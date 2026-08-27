# -*- coding: utf-8 -*-
"""
V4: TCM-focused rescan of the 738k scored library.
Filter by Chinese materia medica species (pharmacopoeia + ethnic medicines +
understudied hepatoprotective herbs), output multi-target TCM hits.
"""
import re
import numpy as np
import pandas as pd

D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v4"
import os; os.makedirs(RES, exist_ok=True)

# TCM species/genera list (pharmacopoeia + ethnic + understudied liver herbs)
TCM = {
 # 冷门肝病中药（重点）
 "Sedum sarmentosum": "垂盆草", "Abrus": "鸡骨草", "Penthorum": "赶黄草",
 "Swertia": "当药/藏茵陈", "Hypericum": "地耳草/田基黄", "Phyllanthus": "叶下珠",
 "Picrorhiza": "胡黄连", "Isodon": "香茶菜/冬凌草", "Hedyotis": "白花蛇舌草",
 "Oldenlandia": "白花蛇舌草", "Lobelia": "半边莲", "Rabdosia": "香茶菜",
 # 常用药典药材（肝病相关）
 "Silybum": "水飞蓟", "Schisandra": "五味子", "Ligustrum": "女贞子",
 "Eclipta": "墨旱莲", "Bupleurum": "柴胡", "Salvia": "丹参", "Glycyrrhiza": "甘草",
 "Berberis": "三颗针", "Coptis": "黄连", "Scutellaria": "黄芩",
 "Gentiana": "龙胆/秦艽", "Artemisia": "茵陈/青蒿", "Gardenia": "栀子",
 "Alisma": "泽泻", "Cassia": "决明子", "Crataegus": "山楂", "Astragalus": "黄芪",
 "Polygonum": "虎杖/何首乌", "Paeonia": "白芍/赤芍", "Curcuma": "莪术/姜黄",
 "Panax": "人参/三七", "Taraxacum": "蒲公英", "Cynanchum": "白薇/徐长卿",
 "Eucommia": "杜仲", "Cistanche": "肉苁蓉", "Plantago": "车前草",
 "Desmodium": "广金钱草", "Lysimachia": "金钱草", "Pyrrosia": "石韦",
 "Terminalia": "诃子", "Phyllanthus emblica": "余甘子", "Hippophae": "沙棘",
 "Andrographis": "穿心莲", "Ampelopsis": "藤茶", "Ilex": "苦丁茶",
 "Siegesbeckia": "豨莶草", "Cirsium": "小蓟/大蓟", "Poria": "茯苓",
 "Atractylodes": "白术/苍术", "Magnolia": "厚朴", "Broussonetia": "构树",
 "Kochia": "地肤子", "Cyathula": "川牛膝", "Achyranthes": "牛膝",
 "Inula": "旋覆花/土木香", "Tussilago": "款冬花", "Farfugium": "大吴风草",
 "Ligularia": "橐吾", "Senecio": "千里光", "Vernonia": "斑鸠菊",
 "Elephantopus": "地胆草", "Ixeris": "苦碟子", "Sonchus": "苣荬菜",
 "Cichorium": "菊苣/毛菊苣", "Cynara": "菜蓟", "Silybum marianum": "水飞蓟",
 "Chelidonium": "白屈菜", "Macleaya": "博落回", "Stephania": "防己",
 "Menispermum": "北豆根", "Sophora": "苦参/槐", "Tripterygium": "雷公藤",
 "Tripterospermum": "双蝴蝶", "Gentianella": "假龙胆", "Comastoma": "喉毛花",
 "Halenia": "花锚", "Lomatogonium": "肋柱花", "Swerfia": "獐牙菜(变体)",
 "Sarcandra": "草珊瑚", "Chloranthus": "及己", "Houttuynia": "鱼腥草",
}
HOT_EXCLUDE = {"Curcuma longa": "姜黄(热门)", "Camellia sinensis": "茶叶"}

def tcm_match(org):
    if not isinstance(org, str) or not org.strip():
        return None
    for sp, cn in TCM.items():
        if sp.lower() in org.lower():
            return cn
    return None

L = pd.read_csv(f"{D}/results/v2/library_scored.csv", low_memory=False,
                usecols=lambda c: c in {"canonical_smiles", "name", "organism",
                                        "pathway", "top3_mean", "max_pAct"}
                or c.startswith("pAct_"))
L["tcm"] = L["organism"].map(tcm_match)
T = L[L.tcm.notna()].copy()
print("TCM-sourced compounds in scored library:", len(T), "| herbs:", T.tcm.nunique())

tcols = [c for c in T.columns if c.startswith("pAct_")]
THR = 6.5
T["n_active"] = T[tcols].ge(THR).sum(1)
T["MTS"] = T[tcols].where(T[tcols].ge(THR)).sum(1).round(2)
T = T[T.n_active >= 2]  # TCM: relax to >=2 active targets
T = T.sort_values("MTS", ascending=False)
T.head(300).to_csv(f"{RES}/tcm_multitarget_top300.csv", index=False)

# per-herb best
best = T.sort_values("MTS", ascending=False).drop_duplicates("tcm")
print("\n=== each TCM herb best multi-target component ===")
for _, r in best.head(30).iterrows():
    acts = {c[5:]: r[c] for c in tcols if r[c] >= THR}
    prof = ",".join(f"{k}{v:.1f}" for k, v in sorted(acts.items(), key=lambda x: -x[1])[:6])
    print(f'{r["tcm"]:12s} | {str(r["name"])[:34]:34s} | n={int(r["n_active"])} MTS={r["MTS"]:.1f} | {prof}')

# top-20 table
top20 = T.head(20)[["tcm", "name", "organism", "n_active", "MTS", "top3_mean", "pathway"]]
top20.to_csv(f"{RES}/tcm_top20.csv", index=False)
print("\nsaved results/v4/tcm_multitarget_top300.csv + tcm_top20.csv")
