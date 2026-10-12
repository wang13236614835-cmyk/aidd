# AIDD 主库状态同步记录

**同步目标：** 将 `fifth_round_direction_exploration` / FASN Gate T1=FAIL / GNN gated-closed / `candidate_release=false` 设为主库当前权威阶段。

## 最新同步（2026-09-21：GNN 库文件名全面中文化，两轮）

- 范围：GNN 库共 58 个文件改中文名——第一轮 37 个（顶层状态文档 15 + 数据/结果 22），第二轮 21 个（docs 湿实验就绪评估/纪要/个人档案、final-aidd-screening 数据与结果、results/ad 适用域报告）。
- 删除过时：docs/archive 历史归档、五人"待核文件"快照副本、全部 __pycache__。
- 保持不改：results/runs/ 历史快照、docking 二进制（HP/NV 配体与受体）、docs/audit 封存审计、human_review/phase2b_20260915 冻结核验包、learning 个人产物、全部 .py 代码文件名、README（GitHub 平台约定）、主库自身 qualification_v1 文件名。
- 引用链同步：GNN 库内约 150 个文件引用替换；src/data 与 final-aidd-screening/src 代码路径修复（ad/clean/s3_model/redock/common）；主库 registry（GNN-STATE/GNN-STATUSJSON/GNN-PLAN/GNN-STATUS/GNN-FIX 等 10 行新路径）+ run_preservation_qc.py + build_asset_registry.py 更新。
- 再生成：MASTER_ASSET_REGISTRY（46 项、30/12/3/1 不变、missing=0）、GNN_ASSET_STATUS（12 行）、manifest（33 文件）、主库 file_inventory（6360）。
- 复验全绿：preservation QC PASS；qualification QC PASS（issues=0）；GNN pytest 15 passed；verify_research 9/9；五页 HTML 语法 PASS + 契约 95 checks + 坏链仅目标态输出；run_all.py 冒烟正常；Workbench 投影一致 + 对齐套件 13 passed。
- 科研状态零改动：FASN Gate T1=FAIL、GNN gate=closed、candidate_release=false、Moracin N 待物料/导师签核。

## 历史同步（2026-09-20：一致性对齐修复）

- 触发：三库逐字核验发现两处文字失配（GNN 库状态表 GNN02 理由列、本库 `qualification_v1/RESEARCH_STATE.md` §8.2 Secondary 措辞）。
- GNN HEAD：`7ffcf75d97839e3ec78c6bd64c00df98dea95b0c`（`research/phase2b-human-review-20260916`）。
- AIDD HEAD：`ce2b25461498b40f6a4984ab61093f72e10954d9`（`research/phase2b-human-review-20260916`）。
- Workbench HEAD：`2576b405eec70c6c0bac77a08b41fb62fd9ab974`（`research/phase2b-human-review-20260916`）。
- 修复内容（仅文字与索引，不改任何科研状态值）：
  - `hepato-gnn-screening/GNN数据与模型状态表.csv` GNN02 理由列更新为“未知元素缺陷已修复2026-09-17（默认显式报错，可选独立UNK 14维；历史13维逐位不变；REQUALIFY不自动升级）”；`qualification_status` 保持 REQUALIFY 不升级；
  - `build_asset_registry.py` SPECS 中 `GNN-DATASET-001` 备注同步为修复后口径；
  - `qualification_v1/RESEARCH_STATE.md` §8.2 补为 `FXR evidence-anchor/Formononetin 依赖性桥接 + Biochanin A QC`，与 `研究状态.json`、`GATE_DECISION.json` 逐字一致。
- 衍生件按 09-15 惯例全量再生：`MASTER_ASSET_REGISTRY.csv`（46 项、30/12/3/1 不变）、`GNN_ASSET_STATUS.csv`（12 行）、`derived/registry_summary.json`、`derived/gnn_asset_status_summary.json`、`derived/test_results.json`、`manifest.json`、主库 `file_inventory.csv/json`、`qualification_v1/RUN_MANIFEST.json`。
- 哈希对齐结果：hepato-gnn-screening 全部 14 个文件行 hash 与现场字节 SAME（此前 4 行漂移已清除）。
- 复验：preservation QC PASS；qualification QC PASS（issues=0）；GNN `verify_research` 9/9；GNN pytest 15 passed；Workbench 对齐套件 13 passed。
- 状态值一律不变：`project_stage=fifth_round_direction_exploration`、FASN Gate T1=FAIL、GNN gate=closed、`candidate_release=false`、Moracin N `not_executed`。

## 历史同步（2026-09-15）

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