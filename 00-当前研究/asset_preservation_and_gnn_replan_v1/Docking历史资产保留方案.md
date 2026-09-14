# Docking 历史资产保留方案

## 保留层

- receptor PDB/PDBQT、ligand PDBQT/CCD、grid、seed、exhaustiveness、software version、stdout/stderr、pose 和 run manifest：保留；
- WT gate 与旧 mutant gate 原始分数、日志和姿态：保留，用于复现、错误分析和结构假说。

## 解释层降级

所有 docking score ranking、Top-K、TOPSIS、selectivity score 和“分数代表活性”的解释统一降为 HISTORICAL/REJECTED interpretation。当前最高角色是 `structure hypothesis support`：几何恢复、口袋占据假设、技术复现。

## 发布规则

任何候选 release、activity prediction、AD/UQ 或模型 ranking 不得读取 docking score 作为排序变量；Workbench 仅展示协议和状态，不生成新的 docking 候选榜。
