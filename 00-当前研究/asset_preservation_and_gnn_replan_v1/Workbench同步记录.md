# Workbench 同步记录

## 本轮策略

Workbench 不重设计。现有 `pages/17_Research_State.py` 已经以只读方式读取 aidd 主库 `qualification_v1`；本轮只要求它继续显示：

- `project_stage=pipeline_revalidation`；
- asset registry 的 VERIFIED/REQUALIFY/HISTORICAL/REJECTED；
- FASN Gate T1 pending；
- GNN enable gate closed/gated；
- THRβ 2J4A historical mutant 与 docking ranking rejected；
- FXR evidence anchor；
- Moracin N experimental_start_qualified / biological_validation not_executed；
- `candidate_release=false`；
- 资产保留轮精选 registry 由 46 项（具体状态数见 `derived/registry_summary.json`）组成，旧文件未删除。

## 边界

缺少主库目录时必须显示 BLOCKED；页面不生成候选榜、不写回科学结论、不覆盖 Workbench v0.5.2 发布线的既有未提交修改。
