# 基于贝叶斯图神经网络的抗MASH天然药物筛选 —— 独立复现与改进研究

本研究以《基于贝叶斯图神经网络的抗MASH天然药物筛选》大创项目方案为蓝本，
独立完成了从数据获取到最终排名的全流程计算研究。**所有数据均来自真实公共数据库
（GEO / ChEMBL / PubChem / RCSB PDB / KEGG），所有中间结果均可通过本仓库代码复现。**

## 目录结构

```
mash_research/
├── src/                          # 全流程代码（按阶段编号）
│   ├── step0_geo_deg.py          # 阶段1: GEO GSE135251 DEG分析+靶点验证+KEGG ORA
│   ├── step1_fetch_chembl.py     # 阶段2a: ChEMBL REST获取FXR(CHEMBL2047) IC50数据
│   ├── step2_clean_chembl.py     # 阶段2b: 标准化/PAINS/去重/杠杆AD过滤
│   ├── step3b_bayesian_gnn_v2.py # 阶段3: 贝叶斯GIN(异方差NLL+MC Dropout)双划分评估
│   ├── step5_production_inference.py # 阶段5a: 全数据生产模型+NP库批量推理+三级标注
│   ├── step5b_explain.py         # 阶段5b: GNNExplainer可解释性+校准图
│   ├── step4_tcm_library.py      # 阶段4: 10味中药成分PubChem检索+ADMET过滤
│   ├── step6a_prep_receptors.py  # 阶段6a: 受体清洗+meeko制备+对接盒
│   ├── step6b_dock.py            # 阶段6b: 重对接验证+阳性对照+NP批量对接
│   └── step7_cwbcs.py            # 阶段7: CW-BCS评分+中药排名
├── data/                         # 真实数据（geo/chembl/tcm/pdb）
├── docking/                      # 受体pdbqt/配体pdbqt/对接输出/盒子定义
├── models/                       # 训练好的模型权重
├── results/                      # 表格+图（tables/ figures/）
└── research/                     # 4份调研报告（GEO数据集/中药成分/PDB结构/ChEMBL靶点）
```

## 数据来源（全部真实、可溯源）

| 数据 | 来源 | 获取日期 | 规模 |
|---|---|---|---|
| MASH肝转录组 | GEO GSE135251 (RNA-seq, 216例) | 2026-08-17 | Normal 10 / NAFL 51 / NASH 141 |
| FXR活性数据 | ChEMBL CHEMBL2047 (人源, assay_type=B, IC50) | 2026-08-17 | 548条原始→354化合物 |
| 中药成分 | PubChem PUG-REST (名称→CID+SMILES) | 2026-08-17 | 233条目→224解析→131通过ADMET |
| 靶点结构 | RCSB PDB: 3FLI/1OSH(FXR), 3GWS(THRβ), 5KKN/3GID(ACC2) | 2026-08-17 | 5受体+4配体重对接验证 |
| 通路注释 | KEGG REST (hsa) | 2026-08-17 | 全部hsa通路 |

## 方法学改进（相对原方案）

1. **双划分评估协议**：严格Bemis-Murcko骨架划分 + 申报书式随机划分并列报告，
   定量揭示了"天然产物过度外推"痛点（R² 0.79→-0.61）。
2. **异方差NLL损失 + MC Dropout 双层不确定性**：偶然(aleatoric)+认知(epistemic)
   不确定性分解，σ总=√(σ²_alea+var_epist)。
3. **五种子深度集成**：MC Dropout(单模型) → 种子集成+MC，σ更稳定。
4. **重对接验证门控**：4受体共晶配体重对接RMSD全部<2Å(0.33-1.22Å)后才开展虚拟筛选。
5. **CW-BCS显式归一化**：三靶点分数min-max归一化后取加权几何均值，
   结构冗余惩罚用Morgan指纹Tanimoto定量。
6. **绝对活性标志层**：在归一化排名之外增加FXR pIC50≥6.5 / ΔG≤-7 kcal/mol的
   可解释覆盖标志，区分"排名高"与"绝对活性达标"。

## 复现方式

```bash
python src/step1_fetch_chembl.py    # ~1 min (网络)
python src/step2_clean_chembl.py    # ~1 min
python src/step3b_bayesian_gnn_v2.py # ~10 min (CPU)
python src/step4_tcm_library.py     # ~6 min (网络)
python src/step5_production_inference.py # ~10 min (CPU)
python src/step6a_prep_receptors.py # ~2 min
python src/step6b_dock.py           # 验证+对照 ~10 min; 批量对接 `nps` ~1.5h
python src/step7_cwbcs.py           # 秒级
python src/step0_geo_deg.py         # ~10 min (含下载)
```

## 依赖

torch 2.2 / torch_geometric 2.5.3 / rdkit 2026.03 / sklearn / xgboost / statsmodels /
meeko 0.7.1 + prody / AutoDock Vina 1.2.5 (官方Windows可执行文件)
