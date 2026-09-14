# FASN 历史资产保留方案

## 当前分层

- 原始 activity JSON：`VERIFIED raw`；
- `FASN_activity_master.csv` 和 assay-aware master：`VERIFIED`，可作为 Gate T1 输入，但跨 assay 仍需对齐；
- canonical clean/外部/10-seed/Y-scrambling/leakage/AD-UQ：`VERIFIED`，范围限定为 CHEMBL5731051 canonical assay；
- 旧诊断 split/cluster prediction/旧模型：`HISTORICAL` 或 `REQUALIFY`，不删除；
- provenance 不完整的聚合标签：登记为 `historical_aggregated_label`，不进入正式训练。

## 旧 split 处理

旧 split 的预测和 R² 仍是可复现的历史输出，但不能证明外部泛化。当前严格 benchmark 的同折断言和外部失败结果优先；旧 split 文件不覆盖、不重跑、不改名。

## Gate T1 输入纪律

下一轮只从 assay-aware master 组装共享分子对；每个 assay 保留 assay_id、document、species、construct、format、endpoint、unit、relation 和转换方法。若无法确认 lineage，保留但排除正式训练，并写入排除原因。
