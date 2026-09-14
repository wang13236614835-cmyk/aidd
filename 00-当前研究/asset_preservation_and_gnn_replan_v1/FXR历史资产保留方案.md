# FXR 历史资产保留方案

## 保留

- `chembl_fxr_data.csv`、raw/page JSON、`fxr_locked_model` joblib、manifest、locked metrics、multiseed sensitivity、predictions 全部保留；
- manifest 已明确：human FXR/CHEMBL2047、CHEMBL5735838、EC50、single protein、324 unique molecules、Murcko scaffold split、locked test 未用于训练。

## 结论限定

该模型是内部 assay-specific scaffold 参考，`pActivity=8` 是该 assay 的 100 nM 标签阈值，不是普适 efficacy threshold。FXR 当前角色为 disease evidence anchor/QC；不把内部锁定测试当 external validation，不恢复旧的多靶点候选发布链。

## 文案修正

历史文本中若出现“100 nM”与“10 nM”混用，新的权威文案统一使用：**10 nM = 1e-8 M；pActivity=8**。本轮已新增 `FXR元数据口径修正记录.md`；原模型数据和 artifact 不重跑、不覆盖。
