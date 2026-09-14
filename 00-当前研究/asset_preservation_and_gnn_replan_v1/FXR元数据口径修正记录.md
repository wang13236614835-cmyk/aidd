# FXR 元数据口径修正记录

**日期：2026-09-14**

## 发现

`candidate_decision_20260910/derived/fxr_locked_model/model_manifest.json` 的旧 `threshold_note` 写作“100 nM”，但该模型的 `threshold_pActivity=8.0` 按 pActivity 定义对应 **10 nM（1e-8 M）**。这是元数据/文案不一致，不改变模型 artifact、训练数据、split、指标或预测结果。

## 处理

- 旧 manifest 不删除，作为历史 provenance 资产保留并已登记 hash；
- 新增本记录和主库状态说明，权威解释统一为：`pActivity=8` 是该 assay-specific 标签阈值，数值换算为 10 nM；
- 不把该阈值解释为普适 efficacy threshold；
- 未重跑 FXR 模型，因为输入、标签数值和训练流程没有变化，只有说明文字需修正。

## 当前状态

FXR 模型仍是 VERIFIED 的内部 scaffold reproducibility reference / evidence anchor；不是 external validation，不直接放行候选。
