# Workbench 同步记录

## 本轮策略

Workbench 不重设计。`pages/17_Research_State.py` 与 `core/research_workflow.py` 已以只读方式读取 AIDD 主库 `qualification_v1` 与 `asset_preservation_and_gnn_replan_v1`。

## 本轮同步字段（与 AIDD 主库一致）

- `project_stage=fifth_round_direction_exploration`；
- FASN Gate T1=`FAIL`（来源于 `fifth_round_direction_exploration_20260915/GATE_DECISION.json` 与 `研究状态.json::fasn.gate_t1_decision`）；
- GNN enable gate `closed`，GNN activity `gated`；
- THRβ 2J4A `historical_mutant`，WT docking ranking `rejected`；
- FXR `evidence_anchor`（`pActivity=8` 为 assay-specific label，不可作普适阈值）；
- Moracin N `experimental_start_qualified` / `biological_validation=not_executed` / `material=not_arrived`；
- `candidate_release=false`；
- 资产保留轮精选 registry 46 项，旧文件未删除。

## 已做的同步

- `_render_round5_hard_findings` 改为读取 `workflow` 字段，不再写死 Primary / FASN / GNN / candidate / Research Readiness 五个指标；
- `load_research_workflow` 已读取 `qualification_v1/RESEARCH_STATE.md`、`研究状态.json`、asset preservation `MASTER_ASSET_REGISTRY.csv`、`fifth_round_direction_exploration_20260915/GATE_DECISION.json`、`方向探索矩阵` 等多源；
- `pages/17_Research_State.py` 的 `G0–G5` 段标题改为 `AIDD 主库只读资格文档（G0–G5）` 并注明 Workbench 不修改主库。

## 边界

- 缺少主库目录时显示 BLOCKED；页面不生成候选榜、不写回科学结论；
- 不覆盖 Round 5.1 并行 Agent 未提交文件（核心科研模块、页面、CandidateEligibility 等）；
- Round 5 硬结论卡显示的 Primary / FASN Gate T1 / GNN / candidate / Research Readiness 均来自 `workflow` 字段；AIDD 主库字段变化时 Workbench 自动同步，但 Workbench 不会因工具运行状态改变这些字段。