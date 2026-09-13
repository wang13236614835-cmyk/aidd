# FASN 主轴资格判定

**日期：2026-09-13**

## 判定：**CONDITIONAL GO**

FASN 靶点与 canonical 数据体系值得继续作为长期 AIDD 主轴，但在两个明确问题解决前，模型主张范围被限定，且天然产物定量筛选资格不予发放。

## 一、支持继续的证据（全部本轮实跑）

1. **可学习信号真实**：canonical assay（CHEMBL5731051，96 分子/39 骨架）10 seed scaffold split，ECFP-Ridge R² 中位 **0.732**（IQR 0.55–0.76），Spearman 中位 0.820；均值基线中位 −0.017。
2. **非伪学习**：20 次 Y-scrambling，Ridge/RF/XGB 的 permutation R² 最大值（−0.141 / 0.078 / −0.019）全部低于真实测试 R²——**0/20 permutations exceeded observed performance**（+1 校正 p=0.0476），z≈2.4–2.5。
3. **数据质量合格**：canonical QC 零异常（0 重复分子、0 立体异构对、0 盐/混合物、0 不可能值；1 个重复记录分子按中位数合并留痕）。
4. **AD 可用**：相似度 AD 阈值 0.812 能正确隔离外部（91/105 OOD）与天然产物（54/54 OOD）。
5. **临床/疾病面未变**：denifanstat Phase 2b 组织学阳性（PMID 39396529）与数据规模（精确主表 1,652 条/1,139 分子）仍是长期主轴资格的底盘。

## 二、必须先解决的两个问题（"条件"的精确内容）

### 条件 1：外部/跨 assay 泛化未通过 → 模型身份限定

外部验证（105 分子、3 个独立文献 assay、排除镜像 assay 与重叠分子）：champion ECFP-Ridge 总体 R² 仅 **0.180**，分 assay R² 全负（−0.163 / −0.206 / −1.352），conformal 覆盖 0.629（名义 0.90）。宽口径 time split 同向失败（R² −0.06/−0.42）。

**限定**：当前模型只能称 **canonical assay model（CHEMBL5731051 系列内）**；不得称一般 FASN activity model。解决路径：多 assay 数据融合（assay-aware / per-format 校准）或锁定新的可对齐外部校准集——在此之前一切"FASN 抑制预测"表述必须带 assay 限定语。

### 条件 2：天然产物域间隙 → NP 筛选资格不发放

54/54 天然产物域外（max-Tanimoto 中位 0.136，阈值 0.812）。桥接数据审计（`FASN_natural_product_bridge_set.csv`）：有数值的直接生化证据仅 phloretin（动物 FASN）+ asiatic acid/quercetin/kaempferol（酶源物种未声明，弱活性）；其余为细胞脂生成或表达变化层。

**限定**：**当前模型不具备天然产物定量筛选资格**（此为有效研究结果，非失败遮羞）。域适应/迁移学习**不值得做**（bridge n≈5、物种/assay 不明）。解决路径：只有获得≥数十个同 assay、人源、直接的天然产物/类天然产物活性点后才重评。

## 三、化学系列集中（chemical-series confinement）与稳定性的诚实披露

- 10 seed 近重复审计：未发现结构重复、scaffold 共享或复制记录跨集（泄漏检查通过）；高相似事实——**206/206 测试分子 NN Tanimoto≥0.60，138 个≥0.85，max 0.90**；训练集 LOO NN 中位 0.885——定性为 **chemical-series confinement / local interpolation**（单一紧密系列的局部插值），不称 data leakage；
- ECFP-Ridge 10 seed 中 1 个 seed R²=−0.654（测试 n=16 小样本敏感）；
- 结论：内部信号真实但不可外推为跨系列能力——与外部验证结果互相印证。

## 四、Champion model 决定

**ECFP-Ridge 正式保留为当前 champion**（Ridge R² 中位 0.732 > XGB 0.594 > RF 0.217；train-test gap 0.207 < XGB 0.405 < RF 0.423；外部 R² 0.180 亦最高）。解释：96 个分子、2048-bit 稀疏指纹下，L2 正则线性模型方差最小；单系列 SAR 近似线性可分；RF 受高维稀疏+小样本抑制；XGB 过拟合（gap 0.41）。**禁止以"AI 味道"为由换掉 Ridge。**

## 五、若条件无法解决的下场

若 3 个月内多 assay 融合或外部校准仍无法通过（外部 R² 持续≤0.2 且覆盖崩塌），FASN 轴降级为"canonical assay 方法学研究"，触发 Plan B 靶点审查（THRβ ligand-based 线优先），不通过补模型/补 docking 延命。
