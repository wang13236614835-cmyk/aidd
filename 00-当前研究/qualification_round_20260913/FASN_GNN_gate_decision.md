# FASN GNN 启用门控判定

**日期：2026-09-13｜判定：GNN 保持关闭（6/8 条件未满足或不可判定）**

| # | 门控条件 | 本轮证据 | 结果 |
|---|---|---|---|
| 1 | canonical 数据清洗稳定 | QC PASS：96 分子/39 骨架，0 重复/0 立体对/0 不可能值，重复记录按中位数合并留痕 | ✅ 满足 |
| 2 | baseline 显著优于 permutation | Y-scrambling 20 次：三个模型 perm R² max（−0.14/0.08/−0.02）全部低于真实值——0/20 exceeded（+1 校正 p=0.0476） | ✅ 满足 |
| 3 | scaffold split 稳定 | ECFP-Ridge 10 seed R² 中位 0.732，但 1/10 seed 为 −0.654，IQR 0.55–0.76；近重复审计（无泄漏）显示全部测试分子 NN Tanimoto≥0.60（chemical-series confinement，系列内插值） | ⚠️ 名义满足、实质受限 |
| 4 | document/time 或 external 有一定泛化 | 外部验证：champion R² 0.180，分 assay 全负（−0.16/−0.21/−1.35）；宽口径 time R² −0.06/−0.42；conformal 覆盖 0.63 vs 名义 0.90 | ❌ 不满足 |
| 5 | AD/UQ 正常工作 | 相似度 AD 可用（0/54 NP、91/105 外部正确判域外）；conformal 内部有效、外部失效（边界已写明） | ✅ 有条件满足 |
| 6 | 样本规模足够 | 96 分子/39 骨架/单一文献系列 | ❌ 不满足 |
| 7 | GNN 有明确可能改善的问题 | 当前瓶颈是**数据域问题**（系列偏差+assay 异质），不是表征能力问题；无证据表明 message-passing 能修复域间隙 | ❌ 不成立 |
| 8 | 泄漏检查（结构重复/scaffold 共享/复制跨集） | 均未发现；高 Tanimoto 定性为 chemical-series confinement 而非泄漏 | ✅ 通过（附局部插值限定） |

## 结论

**GNN 保持关闭。**本轮未训练任何 GNN（gating 记录：gnn_trained=false）。理由不是"模型复杂"，而是：在单一系列 96 分子上，正则化线性模型（ECFP-Ridge）已是最优且最稳定；外部失败的根因（assay 异质+域间隙）是数据问题，GNN 无法解决并可能放大过拟合。重新评估的前提：多 assay 数据融合 + 桥接数据 + 外部泛化先行通过（与最终战略轮八项门控一致）。
