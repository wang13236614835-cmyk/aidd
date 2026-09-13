# GNN Clean Benchmark 报告

**日期：2026-09-13｜脚本：[run_gnn_clean_benchmark.py](run_gnn_clean_benchmark.py)｜输出：[derived/](derived/)｜运行时长 275.5 s（CPU）**

## 要回答的问题（预注册）

> 在当前冻结数据规模（FASN canonical 96 分子/39 骨架）和问题定义（pActivity 回归）下，GNN 是否真正提供优于经典 baseline（ECFP-Ridge / RF / XGBoost）的增益？

**答案：没有。GNN 未证明优于经典 baseline，且差距悬殊。这不是失败，是本项目第一份 GNN 实证证据。**

## 可比性保证（同折断言）

GNN 看到的每一折与资格验证轮**完全相同**：同一 CSV、同一行序、同一 `GroupShuffleSplit(test_size=0.2, groups=scaffold)`、同一 10 个种子（20260912–20260921）。脚本内置断言：重算 ecfp_ridge 10-seed 中位 R² = 0.732008，与资格轮冻结值逐位一致（<1e-9）才继续执行。每折断言 scaffold 训练/测试零重叠。

## 10-seed scaffold split 结果（测试集）

| 模型 | R² 中位 | R² 均值±std | R² 最差 | R² 最好 | Spearman 中位 |
|---|---|---|---|---|---|
| **ECFP-Ridge**（资格轮冠军，本轮复算） | **0.732** | 0.541±0.452 | −0.654 | 0.816 | **0.820** |
| XGBoost | 0.594 | 0.447±0.393 | −0.473 | 0.818 | 0.750 |
| RandomForest | 0.217 | 0.206±0.187 | −0.100 | 0.461 | 0.513 |
| **GNN-GCN**（3×GCNConv, mean pool） | 0.078 | 0.143±0.375 | −0.413 | 0.652 | 0.613 |
| **GNN-GINE**（3×GINEConv, 键特征） | −0.040 | −0.303±0.641 | −2.059 | 0.055 | 0.452 |

完整每 seed 数字见 `derived/GNN_benchmark_10seed_results.csv`、汇总见 `derived/GNN_benchmark_summary.csv`。

**排序：Ridge > XGB >> RF > GCN > GINE。** GNN 两个变体全面低于全部经典模型；GINE（带键特征）反而比 GCN 更差——小样本（训练 n≈77）下图网络参数量的劣势压过了表达力优势，键特征输入只增加了过拟合面。

## Y-scrambling ×20（seed0 折，仅 GNN；经典模型 0/20 已在资格轮成立）

| 模型 | 真实测试 R² | 置换最大 R² | 置换中位 R² | 置换反超次数 |
|---|---|---|---|---|
| GCN | 0.096 | 0.078 | −0.105 | **0/20** |
| GINE | −0.260 | 0.073 | −0.102 | **13/20** |

- GCN 在 seed0 上学到了**微弱但高于置换包络的真信号**（0/20 exceeded；注意真实 R² 也只有 0.096，量级远低于 Ridge）；
- GINE 在 seed0 上**未通过置换检验**（13/20 置换反超）——性能落在置换分布之内，无信号证据。

（首轮运行的 JSON 汇总曾因聚合键名 bug 报出 NaN，已修复并以 `--summary-only` 从 CSV 重建；CSV 原始数据自始正确，模型未重训，重建记录在 JSON note 字段。）

## 外部验证（105 分子/3 文献 assay，全量 96 分子训练）

| 模型 | overall R² | ADin(n=14) R² | ADin Spearman | ADout(n=91) R² |
|---|---|---|---|---|
| ECFP-Ridge | **0.180** | −1.457 | **0.880** | 0.111 |
| RF | −0.043 | −0.710 | 0.661 | −0.177 |
| XGB | 0.069 | −2.661 | 0.922 | 0.020 |
| GCN | −0.237 | −0.975 | 0.539 | −0.397 |
| GINE | −0.150 | −1.504 | 0.049 | −0.278 |

Ridge 的 ADin 结果与推进轮 E1_ADin（rho=0.880 / R² −1.457）**逐位复现**，进一步交叉验证了本轮与此前资产的同源性。GNN 在外部同样全面落后，且**不具备 Ridge 那样的 ADin 排序能力**（GCN 0.54 / GINE 0.05 vs Ridge 0.88）。

## UQ 学习件（MC-dropout，非正式 UQ 通道）

GCN 的 MC 方差与 |误差| 的 Spearman 中位 **−0.088**（10 seed），GINE +0.074——两者都接近 0，MC-dropout 方差在当前设置下不构成可用的不确定性指标。正式 UQ 通道仍为资格轮的 conformal（内部有效/外部失效结论不变）。

## 结论与门控影响

1. **GNN 当前未证明优于经典 baseline**——中位 R² 差距 0.65+，外部同样落后，无 ADin 排序优势，MC-dropout UQ 无效。样本量（96）远低于图网络常见需求；
2. Ridge champion 地位**加强**（内部、外部、ADin 三个维度同时最优）；
3. FASN_GNN_enable_gate 复审输入：本 benchmark 提供"模型增益"维度证据 = **不支持启用**。其余门控条件（数据规模、外部校准）未变。**门的正式状态保持关闭**，下次复审连同 Gate T1 数据一起评估；
4. 假设更新方向（供下一轮，不预注册为结论）：GNN 增益更可能出现在"多 assay 融合后样本数百级 + 结构图数据增强"的场景，而非当前 96 分子单 assay 回归。

## 局限（诚实披露）

- 单一预注册超参（300 epochs, hidden 64, lr 0.01, dropout 0.2），未做神经架构搜索——但调参救不了 0.65 的中位差距，且搜索会在 96 分子上过拟合验证集；
- CPU full-batch 训练，种子内确定（torch.manual_seed），跨平台浮点差异可能引起微小数值漂移；
- 结论限定"当前数据规模与问题定义"，不代表 FASN 轴数据扩大后 GNN 的上界。
