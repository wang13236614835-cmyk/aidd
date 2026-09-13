# AIDD Research Qualification v1（第五轮资格裁决）

**日期：2026-09-13｜性质：三库统一审计 + 资格框架冻结 + 定向复算（GNN clean benchmark），不产生新候选，不放行候选。**

## 本轮回答的三个问题

1. 前四轮（及此前全部轮次）的资产里，哪些可信保留、哪些需要复算、哪些只是历史、哪些明确废弃？
2. 在冻结数据上，GNN 是否真的优于经典 baseline？（此前 GNN 从未实跑，只有门控关闭决定）
3. 三个仓库（aidd 主库 / mash-aidd-workbench / hepato-gnn-screening）的科研事实口径是否统一、可被导师/论文直接引用？

## 文件导航

| 文件 | 作用 |
|---|---|
| [RESEARCH_STATE.md](RESEARCH_STATE.md) | 统一科研状态：已成立 / 软件验证 / 待资格验证 / 禁止发布 四层口径 |
| [ASSET_AUDIT.csv](ASSET_AUDIT.csv) | 全部历史资产 A/B/C/D 分类台账（VERIFIED/REQUALIFY/HISTORICAL/REJECTED） |
| [MASTER_EVIDENCE_MATRIX.csv](MASTER_EVIDENCE_MATRIX.csv) | claim → evidence → source → confidence 证据矩阵（含文献证据链） |
| [QUALIFICATION_GATES.md](QUALIFICATION_GATES.md) | G0–G5 资格门控定义与当前裁决 |
| [RERUN_DECISION.md](RERUN_DECISION.md) | 逐项复算裁决：为什么跑 / 为什么不跑 |
| [ASSAY_PROVENANCE 审计](derived/ASSAY_PROVENANCE.csv) | 51 个 assay 的 lineage、角色、覆盖检查（`derived/provenance_audit.json` PASS） |
| [GNN_方法学习审计.md](GNN_方法学习审计.md) | hepato-gnn-screening GNN 实现的逐项方法审计 |
| [GNN_clean_benchmark_report.md](GNN_clean_benchmark_report.md) | GNN vs RF/XGB 同折对比结果（本轮唯一大规模复算） |
| [OPEN_ISSUES.md](OPEN_ISSUES.md) | 未解决项与外部阻塞 |
| [RUN_MANIFEST.json](RUN_MANIFEST.json) | 本轮全部实际运行记录（脚本/参数/输出/哈希） |
| [AGENT_PROGRESS.md](AGENT_PROGRESS.md) | 执行 Agent 的进度检查点 |

## 与既有轮次的关系（不重复、不覆盖）

- `final_strategy_round_20260912/`：双轴战略冻结——**不变**；
- `qualification_round_20260913/`：双轴资格裁决（FASN=CONDITIONAL GO / Moracin N=GO）——**不变，本轮引用其全部数字**；
- `advancement_round_20260913/`：A2 失败分解与 Gate T1 定义——**不变**；
- 本轮 = 在三者之上的**统一审计层 + GNN 补充证据层**。若本轮数字与此前轮次冲突，以原始轮次为准并登记 OPEN_ISSUES。

## 一句话结论（详见 RESEARCH_STATE）

FASN 主轴维持 CONDITIONAL GO（canonical assay model 限定）；Moracin N 维持 GO（等物料到货）；GNN 门控维持关闭但**首次获得实证依据**（见 GNN_clean_benchmark_report）；`candidate_release = false` 不变。
