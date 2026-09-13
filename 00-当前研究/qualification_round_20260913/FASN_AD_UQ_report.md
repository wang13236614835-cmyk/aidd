# FASN AD / UQ 报告

**日期：2026-09-13｜训练域：canonical CHEMBL5731051（96 分子）｜方法均实际运行**

## 一、三种并行方法（均预注册后执行）

### 1. 指纹相似度 AD

- 训练集 LOO 最近邻 Tanimoto：中位 **0.885**（再次确认单一紧密系列）；
- AD 阈值 = 训练 LOO NN 5th 百分位 = **0.812**（同 FXR LanthaScreen 模型同款保守规则）；
- 判定规则：分子到训练集 max-Tanimoto ≥ 0.812 → in_domain；否则 out_of_domain。

### 2. 化学空间可视化（仅诊断，不参与判定）

PCA/UMAP 仅用于展示训练系列与天然产物之间的巨大间隙；不作为 AD 判定量化依据。

### 3. 预测不确定性

- **split-conformal**：训练集 5 折骨架分组 CV 残差 → q10=0.907、q20=0.702 pActivity（内部名义覆盖 0.90/0.80）；
- **RF ensemble 方差**（tree sd）：作为模型内不确定性探索读数；
- 外部验证证明 conformal 区间**不可跨 assay 外推**（外部实际覆盖 0.629 vs 名义 0.90）。

## 二、AD 判定结果

| 集合 | n | 到训练集 max-Tanimoto（min/中位/max） | in_domain | out_of_domain |
|---|---:|---|---:|---:|
| 外部验证集 | 105 | 0.182 / 0.357 / — | 14 | 91 |
| 54 天然产物库 | 54 | 0.078 / **0.136** / **0.171** | **0** | **54** |

## 三、结论

1. 相似度 AD 方法可正常工作：它能正确把外部 assay 分子（中位 0.357）与天然产物（中位 0.136）与训练域（LOO 中位 0.885、阈值 0.812）区分开；
2. **54 个天然产物全部域外且距离极远**（最高 0.171，不足阈值的 22%）——冻结 NP54 域间隙结论（详见 `NP54_FASN_domain_gap_report.md`）；
3. UQ 的诚实边界：内部 conformal 有效、外部失效——因此任何对外部分子或天然产物的预测区间都必须标注"未经外部校准，不可用于决策"；
4. AD/UQ 本身满足 GNN 门控第 5 条（AD/UQ 可以正常工作），但第 4 条（外部有一定泛化）与第 6 条（样本规模）不满足（见 `FASN_GNN_gate_decision.md`）。

产物：`derived/NP54_FASN_domain_gap.csv`、`derived/FASN_external_predictions_AD.csv`。
