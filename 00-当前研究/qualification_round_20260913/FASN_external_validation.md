# FASN 外部验证报告

**日期：2026-09-13｜训练集：canonical CHEMBL5731051（96 分子，模型在见到外部数据前冻结）｜外部集：105 分子**

## 一、外部集构建规则

1. 来源：`FASN_activity_master.csv` 中 construct=full-length 人 FASN、IC50、nM、relation=`=` 的记录；
2. **排除 canonical assay（CHEMBL5731051）与镜像 assay（CHEMBL5734379，89 共享分子、数值镜像）**；
3. 排除与训练集重叠分子（3 个，理由记录于 `FASN_external_set.csv` 的 exclusion 列）；
4. 池 108 → 评估 105 个分子，跨 3 个独立文献 assay：

| assay | n | 年份 | 检测体系 | mean pActivity |
|---|---:|---|---|---:|
| CHEMBL4123591 | 45(42 无重叠) | 2018 | ³H-acetyl-CoA SPA（与 canonical 同族） | 6.74 |
| CHEMBL4402021 | 26 | 2019 | acetyl/malonyl-CoA + NADPH（90 min） | 6.68 |
| CHEMBL5730715 | 37 | 2017 | 重组全长 FASN NADPH 双时点荧光 | 5.31 |

外部集从不进入训练或调参。

## 二、总体结果（105 分子）

| 模型 | R² | RMSE | MAE | Spearman | bias(pred−true) | 覆盖率@q10（名义 0.90） |
|---|---:|---:|---:|---:|---:|---:|
| 均值 | −0.198 | 1.153 | 0.956 | — | +0.468 | 0.476 |
| 描述符-Ridge | −0.345 | 1.221 | 1.007 | 0.046 | −0.206 | 0.524 |
| **ECFP-Ridge（champion）** | **0.180** | **0.954** | **0.789** | **0.482** | +0.120 | **0.629** |
| ECFP-RF | −0.043 | 1.075 | 0.896 | 0.488 | +0.427 | 0.619 |
| ECFP-XGBoost | 0.069 | 1.016 | 0.864 | 0.314 | +0.112 | 0.581 |

内部 conformal 分位数（训练 5 折骨架分组 CV 残差）：q10=0.907、q20=0.702 pActivity。

## 三、champion（ECFP-Ridge）分 assay 表现

| assay | n | R² | Spearman | MAE | 到训练集 max-Tanimoto 中位 |
|---|---:|---:|---:|---:|---:|
| CHEMBL4123591 | 42 | −0.163 | 0.305 | 0.712 | 0.764 |
| CHEMBL4402021 | 26 | −0.206 | 0.194 | 1.013 | 0.306 |
| CHEMBL5730715 | 37 | −1.352 | 0.248 | 0.718 | 0.253 |

三个 assay 的 R² 全为负；即便与 canonical 同为 SPA 族的 CHEMBL4123591（化学距离最近，中位 Tanimoto 0.764）也只有 ρ=0.305。CHEMBL5730715（NADPH 荧光，均值 pActivity 5.31 vs 训练 6.68）呈系统性偏移（R² −1.352），提示 assay 间效价标尺不可直接对齐。

## 四、AD 状态

- 外部 105 分子中仅 14 个落在训练域内（AD 阈值=训练 LOO NN 5th 百分位 0.812），91 个域外；
- 外部分子到训练集 max-Tanimoto 中位仅 0.357；
- conformal 区间在外部覆盖率 0.629（名义 0.90）→ **内部校准的区间不能外推**。

## 五、判定性解读

1. **真实信号存在但属系列内插值**：canonical 内 10 seed scaffold split R² 中位 0.732 + Y-scrambling 0/20 exceeded（见对应文件）证明可学习信号真实；近重复审计未发现泄漏，高相似（NN Tanimoto 中位 0.85）定性为 chemical-series confinement，属单一紧密系列。
2. **外部定量泛化失败**：总体 R² 0.18、分 assay 全负、覆盖率崩塌。按预注册标准，"canonical 内很好但外部崩溃"成立。
3. 因此本项目模型**只能称 canonical assay model（CHEMBL5731051 系列内）**，不得称一般 FASN activity model。
4. 该失败是有效研究结果：它证明 FASN 公开数据的主要障碍不是数量而是 assay/format 异质性与单系列偏差，为 CONDITIONAL GO 的"条件"提供了精确内容（见 `FASN_GO_NOGO.md`）。
