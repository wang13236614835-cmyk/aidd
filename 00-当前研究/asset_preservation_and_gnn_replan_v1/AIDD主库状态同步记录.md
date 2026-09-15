# AIDD 主库状态同步记录

**同步目标：** 将 `fifth_round_direction_exploration` / FASN Gate T1=FAIL / GNN gated-closed / `candidate_release=false` 设为主库当前权威阶段。

## 最新同步（2026-09-15）

- AIDD HEAD：`2020779c339f8df03dc87bf4e13fbdd7065230a1`（`round5-direction-exploration-20260915`）。
- hepato-GNN HEAD：`f87aa5088101360b71595ff5d9e5ca76a376516e`（`round5-direction-exploration-20260915`），工作区 clean。
- Workbench HEAD：`b918fa37851b2fd40cac68b6d265f9f1d7c0e82b`（`round5-direction-exploration-20260915`），工作区保留 Round 5.1 并行未提交文件，不 reset、不覆盖。
- `00-当前研究/fifth_round_direction_exploration_20260915/GATE_DECISION.json` 已确认 `decision=FAIL`；`RUN_MANIFEST.json` 内嵌的旧 AIDD `e1bda0d` snapshot 已在本轮 `build_manifest.py` 输出（`repository_snapshots.aidd.head=2020779…`）刷新。
- `研究状态.json` 关键字段：`project_stage=fifth_round_direction_exploration`，`fasn.gate_t1=FAIL`，`fasn.gate_t1_decision=FAIL`，`fasn.gnn_enable_gate=closed`，`candidate_release=false`，`moracin_n.status=experimental_start_qualified`，`moracin_n.material=not_arrived`。

## 已同步

- 新建本目录及 `MASTER_ASSET_REGISTRY.csv`（当前 46 项精选高价值资产，状态数以 `derived/registry_summary.json` 为准）；
- 新增 `GNN_ASSET_STATUS.csv`（12 行）将 GNN 仓库 12 项资产映射到 canonical 四类，并显式标记 `human_review=pending` 的 1 条 `NEEDS_HUMAN_CHECK`；
- `MASTER_ASSET_REGISTRY` 增加 `original_or_derived`、`current_scientific_role`、`reproducible`、`human_review` 四列；旧 `current_role`/`notes` 列保留；
- `qualification_v1/RESEARCH_STATE.md` 保持为当前科研状态明细；
- `研究状态.json` 新增/更新 `project_stage=fifth_round_direction_exploration`、FASN canonical/external/GNN 状态、THRβ mutant/WT docking 状态、FXR evidence-anchor、Moracin N 实验未执行；
- `00-当前研究/README.md` 头部增加本轮保留/重规划入口；
- `candidate_release=false` 保持不变。

## 不同步

- 不把 Workbench 的演示/平台结果写成主库科研证据；
- 不把 GNN 旧 Top-10、旧 split 或 docking ranking 重新升格；
- 不覆盖 qualification_v1 的原始报告和结果文件；
- 不在 AIDD 主库重跑前四轮 baseline/GNN，不修改 GNN 仓库；
- 不在本轮生成 NP54 FASN 定量榜，不放开 GNN 启用门控。