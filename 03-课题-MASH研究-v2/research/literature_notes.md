# 全新文献调研记录（2026-08-23，独立于旧项目）

## 1. MASH药物格局（决定靶点选择的文献依据）

| 证据 | 内容 | 来源 |
|---|---|---|
| 获批药1 | resmetirom (Rezdiffra, THR-β选择性激动剂), 2024-03 FDA加速获批，首个MASH药（F2-F3非肝硬化） | [PMC12467964 Tiwari 2025综述](https://pmc.ncbi.nlm.nih.gov/articles/PMC12467964/); [Springer 2025](https://link.springer.com/article/10.1186/s43162-025-00468-z) |
| 获批药2 | semaglutide (GLP-1RA), 2025-08 成为第二个获批MASH疗法 | [Nature Sci Rep](https://www.nature.com/articles/s41598-026-37494-y) |
| DNL轴临床 | ION224 (DGAT2反义寡核苷酸), Lancet 2b期, 160例, 最高剂量60%肝健康改善且独立于减重 | [UCSD 2025-08-27](https://health.ucsd.edu/news/press-releases/2025-08-27-first-enzyme-targeting-drug-reverses-liver-damage-in-mash/) |
| FASN临床 | TVB-2640 (FASN抑制剂) MASH 2b期（领域共识） | 2025格局综述 [MDPI Gastroenterol Insights](https://www.mdpi.com/2673-8937/5/1/7) |
| 组合策略 | resmetirom+semaglutide组合、FGF21类似物(efruxifermin/pegozafermin)肝硬化逆转证据 | [Houston Methodist 2025](https://www.houstonmethodist.org/news); AASLD 2025 Highlights |

## 2. 靶点三角论证（本项目: THRβ激动 + FASN抑制 + SCD1抑制）

1. **THRβ**: 唯一获批小分子靶点（resmetirom）。ChEMBL(CHEMBL1947)人源IC50 644条(2026-08-23查询)。人源配体复合物结构丰富（2J4A/OEF=sobetirome共晶等40个≤3Å）。
2. **FASN**: TVB-2640临床验证DNL轴。ChEMBL(CHEMBL4158)人源IC50 1,864条。7MHD=人FASN-TE结构域+磺酰胺噻唑抑制剂(ZEP)共晶2.03Å。
3. **SCD1**: MK-8245等临床lineage；DNL限速酶。ChEMBL(CHEMBL1275210)人源IC50 485条。**人源结构仅底物复合物(4ZYO/ST9, 3.25Å)，无抑制剂共晶→按预案降级为仅QSAR**。
4. 备选排除记录: DGAT2无实验结构+288条（ION224为反义药非小分子，不入对接管线）；ACACA/ACACB数据量不足(49/8)；PPARα/δ(elafibranor 3期失败)。

## 3. 转录组数据集（全新选择，非旧项目GSE135251）

| 数据集 | 设计 | 平台 | 用途 |
|---|---|---|---|
| GSE48452 | 肝活检73例: Control 14 / SS 14 / NASH 18 / Healthy-obese 27，含NAS/纤维化分期 | GPL11532 (HuGene 1.1 ST) | 主队列 |
| GSE63067 | 肝组织18例: healthy 7 / SS 2 / NASH 9 | GPL570 (U133 Plus 2.0) | 复验队列(Stouffer meta) |

## 4. 中药清单（10味全新选择，与旧项目零重叠）

| 药材 | 证据等级* | 关键依据 |
|---|---|---|
| 茵陈 Artemisia capillaris | A | 茵陈蒿汤NAFLD系统综述RCT [Frontiers Pharmacol 2025综述 PMC12728050](https://pmc.ncbi.nlm.nih.gov/articles/PMC12728050/) |
| 虎杖 Polygonum cuspidatum | B | 茵陈蒿汤组分; 白藜芦醇类被pan-assay排除后取piceid等 |
| 垂盆草 Sedum sarmentosum | B | 临床降ALT经典保肝药 |
| 山楂 Crataegus pinnatifida | B | 脂代谢临床+临床前 [Frontiers 2024](https://www.frontiersin.org/journals/pharmacology/articles/10.3389/fphar.2024.1499602/full) |
| 泽泻 Alisma orientale | B | 脂肪肝临床前+经方 (六味地黄/泽泻汤) |
| 决明子 Cassia obtusifolia | B | 降脂小样本RCT |
| 葛根 Pueraria lobata | B | 代谢调节; puerarin临床应用广 |
| 绞股蓝 Gynostemma pentaphyllum | B- | NASH进展干预临床前 [PMC5884411](https://pmc.ncbi.nlm.nih.gov/articles/PMC5884411/) |
| 叶下珠 Phyllanthus niruri | C+ | 保肝临床(HBV); NAFLD临床前 |
| 桑叶 Morus alba | C+ | 代谢调节小样本临床 |

*A=系统综述级RCT证据; B=临床前充分/小样本临床; C+=有限证据。
排除规则(全新): 泛活性清单(quercetin/kaempferol/luteolin/apigenin/genistein/curcumin/resveratrol/EGCG/anthraquinones类/没食子酸类等) + 绞股蓝皂苷MW>700如实剔除(0化合物入组)。

## 5. 关键工具/数据版本

- ChEMBL REST (activity过滤参数式查询), 2026-08-23
- PubChem PUG-REST (name→CID/SMILES), 2026-08-23
- RCSB: 2J4A (THRβ+OEF, 2.2Å), 7MHD (FASN-TE+ZEP, 2.03Å), 4ZYO (SCD1+底物, 3.25Å, 未用于对接)
- KEGG REST (link/list pathway hsa), 2026-08-23
- Vina 1.2.5 / meeko 0.7.1 / RDKit 2026.03.3
