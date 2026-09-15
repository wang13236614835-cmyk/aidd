# FASN Gate T1 最终裁决

**日期：2026-09-15｜性质：复用冻结资产后的定向计算裁决，不重跑前四轮。**

## Decision: **FAIL**

这是本轮 T1 的唯一裁决。FAIL 指的是“FASN 跨 assay 定量迁移 / 天然产物扩展门未通过”，不是删除 FASN 原始数据，也不是否定 canonical assay 内的局部 SAR。

## 1. 数据资格

复用：

- `final_strategy_round_20260912/FASN_activity_master.csv`
- `advancement_round_20260913/FASN_assay_aware_master.csv`
- `qualification_round_20260913/FASN_canonical_clean.csv`
- `qualification_round_20260913/FASN_external_set.csv`

实际审计：

- 1,652 条记录、1,139 个分子、51 assays、34 documents；
- IC50 1,630、Ki 20、Kd 2；nM 1,637、`ug.mL-1` 15；relation=`=` 1,652；物种均为 Homo sapiens；
- protein layer：cell extract 1,140、full-length 302、unknown 184、TE domain 24、KR domain 2；
- valid SMILES 1,652/1,652；多片段 2 条；potential_duplicate 标记 439 条（保留原记录，不将标记直接等同于泄漏）；
- canonical assay CHEMBL5731051：97 条原始记录、96 分子、39 scaffold、单文献/单年份/人源全长/IC50/nM；1 个同 assay 重复分子按中位数合并；
- 结论：canonical assay 训练数据可用；全量 master 是 provenance 保留池，不可直接混合成同质训练集。

## 2. 泄漏审计

`FASN_T1_LEAKAGE_AUDIT.json` 实际输出：

| 指标 | 数值 | 解释 |
|---|---:|---|
| exact_duplicate_count | 0 | canonical clean identity 层无重复分子 |
| canonical_overlap_count | 0 | evaluable external 与 canonical clean 无 identity 重叠 |
| scaffold_overlap_rate | 0.0 | 资格轮 10 个 scaffold split 均无跨集 scaffold |
| stereoisomer_overlap_count | 0 | canonical clean 内无 connectivity 相同而 identity 不同的成对记录 |
| assay_mirror_overlap_count | 89 | CHEMBL5731051 与 CHEMBL5734379 已知镜像共享；因此排除，不当独立 T1 pair |
| external_overlap_count | 3 | 外部候选池中 3 个与训练重叠的记录，资格轮已排除；不计入 evaluable external |
| near_duplicate_count | 82/96 | canonical clean 分子最近邻 Tanimoto≥0.85；定性为 chemical-series confinement，不称 leakage |

泄漏结论：canonical/external evaluable 边界受控；镜像和重叠均有显式排除记录。不存在因为“高相似”就强行改写为 leakage 的情况。

## 3. assay shared matrix 与变换

51 个 assay 两两矩阵共 1,275 个 pair；共享分子数达到 15 的 pair 共 4 个：

1. CHEMBL5731051 ↔ CHEMBL5734379：89 个共享分子，但属于已知 mirror，排除；
2. CHEMBL3888977 ↔ CHEMBL5733207：325 个共享分子，均为 IC50/nM/`=`/Homo sapiens/cell_extract，进入有效 T1 变换；
3. CHEMBL2328957 ↔ CHEMBL3705868：17 个共享分子，但 unknown 与 cell_extract 层级不一致，排除；
4. CHEMBL4402021 ↔ CHEMBL4402023：17 个共享分子，但 full_length 与 unknown 层级不一致，排除。

唯一有效 pair 的变换结果：

- n=325；slope=1.000439；intercept=−0.002712；in-sample R²=0.99958；
- offset=0.000434；offset R²=0.99958；
- 10 seed holdout R² median=0.999999、范围 0.997842–0.999999；Spearman median=1.0、范围 0.995092–1.0；
- 结论：该 pair 的变换稳定，但它只是**一个 cell-extract assay family 内部 pair**，无法独立证明跨 assay/跨构建体的通用效价迁移。

## 4. Random / scaffold / external 对照（均复用前四轮结果）

| 评估层 | 模型 | R² | RMSE | MAE | Spearman | UQ coverage |
|---|---|---:|---:|---:|---:|---:|
| Random split（5 seed 中位） | ECFP-Ridge | 0.722 | 0.345 | 0.252 | 0.882 | — |
| Random split（5 seed 中位） | ECFP-XGBoost | 0.729 | 0.351 | 0.254 | 0.908 | — |
| Random split（5 seed 中位） | ECFP-RF | 0.394 | 0.510 | 0.407 | 0.765 | — |
| Scaffold split（10 seed 中位） | ECFP-Ridge | 0.732 | 0.322 | 0.264 | 0.820 | 内部 conformal 有效 |
| Scaffold split（10 seed 中位） | ECFP-XGBoost | 0.594 | 0.440 | 0.340 | 0.750 | 内部 conformal 有效 |
| Scaffold split（10 seed 中位） | ECFP-RF | 0.217 | 0.516 | 0.409 | 0.513 | 内部 conformal 有效 |
| External（105 分子/3 assay） | ECFP-Ridge | 0.180 | 0.954 | 0.789 | 0.482 | 0.629（名义 0.90） |
| External（105 分子/3 assay） | ECFP-XGBoost | 0.069 | 1.016 | 0.864 | 0.314 | 0.581 |
| External（105 分子/3 assay） | ECFP-RF | −0.043 | 1.075 | 0.896 | 0.488 | 0.619 |

来源：Random 指标来自 `final_strategy_round_20260912/derived/FASN_canonical_multiseed_metrics.csv`；Scaffold 10-seed 指标来自 `qualification_v1/derived/GNN_benchmark_summary.csv`；External 指标来自 `qualification_round_20260913/derived/FASN_external_validation_metrics.csv`。三者均为前四轮冻结资产，本轮未重训。

正确结论是：random/scaffold 内部存在可学习信号，但 external 只有有限排序且效价水平/coverage 失败；因此不能写“模型表现优秀”或“跨化学空间泛化通过”。

## 6. 为什么不能 PASS

预冻结 PASS 要求同时满足：

1. 至少 2 个有效可对齐 assay pair；
2. normalized dataset 可建立；
3. E1/E2 Spearman≥0.5；
4. pooled R²≥cal_mean+0.05；
5. 10 seeds 稳定且 external/AD/UQ 不失控。

本轮实际情况：

- 有效可比较 pair = **1**，未达到至少 2 个；
- `FASN_T1_NORMALIZED_DATASET.csv` **未生成**，因为不足以建立跨 assay normalized dataset；
- 因此 pooled normalized benchmark 没有被伪造或补跑；
- 既有 external 仍为 Ridge R²=0.180、3 个 assay 分层 R² 全负、conformal coverage=0.629；
- E1_ADin 的 rho=0.880 仅 n=14，且效价偏移−0.663，不足以翻转 T1。

## 7. 后果

- FASN 从“长期 AIDD 主轴 / CONDITIONAL GO”收窄为：**canonical assay 内局部 SAR + assay/provenance 方法学线**；
- 保留 FASN 原始数据、assay-aware master、canonical model、外部失败、校准和所有日志；
- 继续禁止：通用 FASN activity model、NP54 FASN 定量排名、OOD 绝对 pIC50、GNN 开放；
- 不再为 T1 失败继续增加模型复杂度或重复下载/训练；
- 第五轮主发现权转向 Moracin N–NRF2/ferroptosis 肝细胞验证；FXR 维持证据锚点/Secondary，THRβ 维持 Reserve reporter 线。

## 8. 复算边界

本轮实际新增计算只有：FASN assay shared matrix、可比性审计、一个有效 pair 的线性/offset 变换和 10-seed holdout 诊断。没有重跑前四轮 baseline/GNN、没有下载新数据、没有生成候选榜。