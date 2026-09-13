# 推进轮 QC 报告

**日期：2026-09-13｜自动 QC 脚本：`run_advancement_qc.py`（结果 `manifest/qc_auto.json`）**

## 一、交付完整性

22/22 个指定文件齐全；全部 CSV 可解析且列宽一致（含 6 个数据 CSV + 4 个 not_executed 模板 CSV）。

## 二、数值一致性（CSV ↔ advancement_summary.json 交叉验证）

| 项 | 校验 | 状态 |
|---|---|---|
| assay_aware_master | 1,652 行；新字段全覆盖；series unknown 处数与预期一致 | ✅ |
| 外部分层 | E1 42 + E2 63 = 105；ADin 14 + OOD 91 = 105；与 canonical 重叠 = 0；E5 = 0 | ✅ |
| 分层结果表 | 3 模型 × 9 子集（含 <3 跳过）行数一致；E1_ADin rho=0.880 复核 | ✅ |
| 校准结果 | 7 方法 × (3 assay + POOLED) × 10 seeds = 280 行 | ✅ |
| NP54 v2 | 54/54 OOD；中位 0.136 | ✅ |
| 桥接 v2 | 20 行；usable=True 的行全部带 conditional/weak 限定 | ✅ |

## 三、可复现性

`run_advancement_fasn.py` 以固定 seeds 20260912–20260921 重跑输出一致（summary JSON 与 CSV 交叉核对）；模型版本/超参/environment 记录于 summary.env。

## 四、口径修正核验

- 全部当前权威文档 grep 无 `empirical p=0`/`p=0（` 残留；`0/20` 表述就位；
- "泄漏"仅存于泄漏检查语境（`FASN_leakage_audit.csv` 文件名与检查动作），高相似定性均为 chemical-series confinement；
- Moracin N NRF2 表述已统一（grep 无"因果级机制证据"残留）。

## 五、禁用表述扫描

上下文感知扫描（规则行豁免）：命中 0 条（扫描词表见 run_advancement_qc.py 的 banned 列表，不在本报告直写以免自触发）。

## 六、历史保护

- `final_strategy_round_20260912/manifest/delivery_hashes.json` 25 文件哈希复核一致；
- `qualification_round_20260913/manifest/delivery_hashes.json` 25 文件哈希复核一致；
- 本轮零覆盖、零删除；not_executed 表格不含任何模拟结果值。

## 七、入口同步

- README 顶部已加推进轮条目；
- 研究状态.json 已加 `batch_advancement_round_20260913`（含三项口径修正与全部关键数字）；
- 记忆：新增推进轮记忆 + MEMORY.md 索引更新 + 资格验证轮记忆口径修正。

## 八、判定

**PASS**（issues 为空；若 FAIL 则先修复重跑，见 qc_auto.json）。
