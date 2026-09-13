# 资格验证轮 QC 报告

**日期：2026-09-13｜自动 QC 脚本：`run_qualification_qc.py`（结果存 `manifest/qc_auto.json`）**

## 一、交付完整性

25/25 个指定文件齐全；`FASN_canonical_clean.csv`、4 个结果 CSV、外部集 CSV、桥接集 CSV、known/unknown 矩阵 CSV 全部可解析且列宽一致。

## 二、数值一致性（CSV ↔ summary JSON 交叉验证）

| 项 | 校验值 | 状态 |
|---|---|---|
| clean 集 | 96 分子 / 39 scaffold / 0 排除 | ✅ |
| 10 seed scaffold | ECFP-Ridge R² 中位 0.732（10/10 seed 齐全） | ✅ |
| Y-scrambling | 60 行（3 模型×20 排列）；三模型真实 R² > permutation max | ✅ |
| 外部集 | 池 108 / 评估 105 / 重叠排除 3 | ✅ |
| NP54 | 54/54 out_of_domain；中位 0.136 | ✅ |
| 泄漏 | 10 seed scaffold 重叠全部=0 | ✅（近重复事实已如实写入报告） |

## 三、可重复性

seed 20260912 ECFP-Ridge 独立重跑 R² 与记录值差 <1e-9（浮点级一致）。

## 四、禁用表述扫描

上下文感知扫描（规则行"禁止/不得…"豁免）：命中 0 条。

## 五、历史文件保护

final_strategy_round_20260912 的 25 文件哈希全部与原 manifest 一致——本轮零覆盖零修改。

## 六、入口同步

README.md 已加资格验证轮条目；研究状态.json 已加 `batch_qualification_round_20260913`。

## 七、manifest

`manifest/delivery_hashes.json` 覆盖本轮 25 份交付（SHA-256）。

## 八、判定

**PASS**（若任一项失败，qc_auto.json 中 issues 非空并先修复后重验）。
