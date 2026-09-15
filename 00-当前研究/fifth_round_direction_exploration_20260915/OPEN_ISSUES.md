# 第五轮未完成项与风险

## 已裁决但仍需后续处理

- FASN Gate T1 = **FAIL**：当前只有 1 个满足核心元数据约束的独立共享 assay pair，未达到至少 2 对门槛；不构建 normalized dataset，不重跑模型。
- FASN 维持 canonical assay local 方法学线：不得称通用 FASN activity model，不做 NP54 绝对 pIC50/定量总榜。
- GNN enable gate 继续 CLOSED；本轮没有以失败的 T1 为理由开放 GNN。

## 外部阻塞

- Moracin N 尚未到货，没有 COA/批号，M0/B0/Gate1/2/3 生物学验证均未执行；
- 导师对 Primary/Secondary/Reserve 方向和采购未签核；
- Workbench Round 6 DTI 分支存在并行未提交文件，本轮不接管、不混提交。

## 下一轮可计算项

- 只有获得第二个可比 assay pair，才重开 FASN T1；
- 若 T1 不再增加有效 pair，FASN 降为数据/方法学线，不继续做模型复杂度扩展；
- SCD1/DGAT2/ACC/THRβ 只有在补齐 endpoint/provenance/external 前置后才重资格化。

## 本轮明确没有做

- 没有下载新数据库数据；
- 没有重跑前四轮 baseline/GNN；
- 没有生成 FASN NP54 候选榜；
- 没有修改 docking 结果或任何历史负结果；
- 没有改变 `candidate_release=false`。
