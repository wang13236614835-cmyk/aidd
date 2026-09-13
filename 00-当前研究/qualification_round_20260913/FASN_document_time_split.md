# FASN document / time split 评估

**日期：2026-09-13**

## 一、canonical assay 内部：不可评估（not evaluable），原因如下

| 拆分 | 状态 | 原因 |
|---|---|---|
| document split（canonical 内） | **not evaluable** | 96 个分子 100% 来自单一 document CHEMBL5725564；按文献拆分即按分子随机拆分，无独立文献测试集可分 |
| temporal split（canonical 内） | **not evaluable** | canonical 记录全部为 2017 年单时间点；不存在"早期训练/晚期测试"边界，伪造年份边界被禁止 |

以上不是数据缺陷声明，而是单 assay 数据结构的客观属性；按预注册规则如实标注，不伪造拆分。

## 二、替代执行的两种跨文献/跨时间检验（均已实际运行）

### 1. 跨 document 检验 = 本轮外部验证

训练 = canonical CHEMBL5725564（96 分子）；测试 = 三个**不同文献**的全长 FASN assay（CHEMBL4123591 / CHEMBL5730715 / CHEMBL4402021，105 个非重叠分子）。这实质上就是 document split 的严格形式。结果（champion ECFP-Ridge）：

- 总体 R² 0.180、RMSE 0.954、Spearman 0.482；
- 分 assay R² 全为负（−0.163 / −0.206 / −1.352）。

**解读**：跨文献后定量性能崩塌，排名信号仅残存中等（ρ≈0.2–0.5）。详见 `FASN_external_validation.md`。

### 2. 跨时间敏感性（宽口径，继承最终战略轮已运行结果）

full-length-stated 宽口径按分子最早年份切分（2017 训练 133 分子 → 2018–2019 测试 75 分子）：

- ECFP-RF R² −0.061（Spearman 0.226）；
- ECFP-XGBoost R² −0.423（Spearman 0.251）；
- 均值基线 R² −0.231。

**解读**：时间外推与跨文献外推同向失败；且该宽口径本身混合 assay 家系，只作敏感性证据。

## 三、结论

1. canonical assay 内部 document/time split **不可评估**（单文献单年份）；
2. 可评估的跨文献（外部验证）与跨时间（宽口径敏感性）**均未支持定量泛化**；
3. 因此任何"时间稳定/文献稳定的 FASN 活性模型"主张当前不成立——成立范围仅限 canonical assay 系列内插值。
