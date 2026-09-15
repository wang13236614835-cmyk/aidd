# 第五轮方向探索执行总览

**日期：2026-09-15｜主题：FASN Gate T1 最终裁决与后续方向资格筛选。**

## 最终结果

- FASN Gate T1：**FAIL**；
- FASN：从跨 assay/天然产物扩展门收窄为 canonical assay 内局部 SAR + assay/provenance 方法学线；
- Primary：Moracin N–NRF2/ferroptosis 肝细胞机制验证；
- Secondary：FXR evidence-anchor/Formononetin 依赖性桥接 + Biochanin A QC；
- Reserve：THRβ reporter、Isorhamnetin、FASN 直接酶实验、SCD1/DGAT2 重资格化；
- Rejected：NP54 FASN 定量榜、docking score 排序、旧 GNN/CW-BCS/TOPSIS 正向结论、ACC1/ACC2 合并模型、3′-methoxydaidzein 当前创新候选；
- GNN：CLOSED；`candidate_release=false`。

## T1 证据

- 51 assays 两两矩阵 1,275 对；共享 identity≥15 的 4 对；
- CHEMBL5731051↔CHEMBL5734379 共享89，为 mirror，排除；
- CHEMBL3888977↔CHEMBL5733207 共享325，cell_extract/cell_extract，唯一有效 pair；线性变换 slope=1.000439、intercept=−0.002712、R²=.99958，10-seed holdout 稳定；
- CHEMBL2328957↔CHEMBL3705868 共享17，unknown/cell_extract，排除；
- CHEMBL4402021↔CHEMBL4402023 共享17，full_length/unknown，排除；
- 有效 pair=1<预冻结至少2，因此不构建 normalized dataset，不做新的 pooled model benchmark。

## 前四轮结果的使用

本轮直接引用既有 canonical/scaffold/external/leakage/AD-UQ/校准结果，不修改原文件。T1 新增的审计输出全部写入当前目录；不通过重跑翻转外部阴性结论。

## 当前下一动作

1. 主发现轴转为 Moracin N：导师批准、采购到货、执行 M0/B0；
2. FASN：只等待第二个可比 assay pair，不继续堆模型；
3. Workbench/GNN 仅同步状态字段，不创建第二套科研事实。
