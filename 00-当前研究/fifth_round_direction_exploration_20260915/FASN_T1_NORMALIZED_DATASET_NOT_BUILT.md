# FASN T1 normalized dataset 未构建说明

本轮不生成 `FASN_T1_NORMALIZED_DATASET.csv`，原因不是脚本失败，而是预冻结输入资格没有满足：

- 51 assays 中只有 1 个满足核心元数据约束、共享分子≥15 的独立 pair；
- canonical/mirror 共享89分子已排除；
- 另外两个共享≥15 pair 的 protein layer 不匹配；
- 预冻结标准要求至少 2 个有效 pair 才能建立 normalized dataset。

因此本轮不进行 normalized pooled benchmark，不训练新模型，不修改前四轮模型数字。