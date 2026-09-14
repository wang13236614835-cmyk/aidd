# AIDD 主库状态同步记录

**同步目标：** 将“pipeline revalidation / 资产保留优先 / GNN gated”设为主库当前权威阶段。

## 已同步

- 新建本目录及 `MASTER_ASSET_REGISTRY.csv`（当前 46 项精选高价值资产，状态数以 `derived/registry_summary.json` 为准）；
- `qualification_v1/RESEARCH_STATE.md` 保持为当前科研状态明细；
- `研究状态.json` 新增/更新 `project_stage=pipeline_revalidation`、FASN canonical/external/GNN 状态、THRβ mutant/W​​T docking 状态、FXR evidence-anchor、Moracin N 实验未执行；
- `00-当前研究/README.md` 头部增加本轮保留/重规划入口；
- `candidate_release=false` 保持不变。

## 不同步

- 不把 Workbench 的演示/平台结果写成主库科研证据；
- 不把 GNN 旧 Top-10、旧 split 或 docking ranking 重新升格；
- 不覆盖 qualification_v1 的原始报告和结果文件。
