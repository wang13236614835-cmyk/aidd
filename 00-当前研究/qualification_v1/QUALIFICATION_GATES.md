# 资格门控（QUALIFICATION GATES）

**G0–G5 定义 + 2026-09-13 当前裁决。门控裁决只升不降原则：任何门从 PASS 降级必须登记 OPEN_ISSUES 并写明触发证据。**

## G0 研究问题 —— **PASS**

- disease：MASH（代谢功能障碍相关脂肪性肝炎）✔（`研究问题协议_G0.md`）
- target：FASN（主轴）/ Moracin N–NRF2 轴（验证轴）✔（最终战略冻结轮）
- endpoint：FASN=酶抑制 pActivity（canonical CHEMBL5731051）；Moracin N=M0–Gate3 功能实验终点 ✔
- metric：R²/RMSE/MAE/Spearman（多 seed 中位数）；湿验=预注册判读框架 ✔
- assay：canonical/mirror/外部三分法已冻结 ✔
- candidate release policy：G0–G4 必要门全过才可 `candidate_release=true` ✔

## G1 数据 —— **PASS**（限定：canonical 范围）

- provenance：51 assay 全 lineage（assay/document/DOI/PMID/物种/单位转换），本轮审计 0 缺失 → PASS；
- canonical QC：0 重复分子/0 立体对/0 盐/0 不可能值 → PASS；
- duplicate QC：1 条重复记录按中位数合并留痕 → PASS；
- endpoint 审计：单一 assay 单一 endpoint（IC50→pActivity），无混合 → PASS；
- **限定**：该 PASS 仅覆盖 canonical 训练集与外部集本身；"通用 FASN 数据资格"未申请（Gate T1 前不存在多 assay 训练集）。

## G2 模型 —— **PASS（canonical 内部证据齐备；GNN 本轮补齐）**

- scaffold split：10 seeds GroupShuffleSplit(test 0.2, groups=scaffold) ✔
- 10 seed 报告 mean/std/median/min/max ✔（资格轮 CSV）
- baseline：mean/desc-Ridge/ECFP-Ridge/RF/XGB ✔；**GNN 补齐=本轮 benchmark** ✔
- Y-scrambling ×20（经典模型 ✔；GNN 本轮补 ✔）
- leakage audit：结构重复/骨架共享/复制跨集 = 0 ✔；chemical-series confinement 已披露 ✔
- **限定**：G2 通过只说明"内部建模资格成立"，不含跨 assay 泛化（归 G3）。

## G3 外部有效性 —— **FAIL（记录在案，不粉饰）**

- external validation：已独立执行（105 分子/3 文献 assay/排除镜像+重叠）→ 总体 R² 0.180、分 assay 全负 → **FAIL**；
- AD/UQ：AD 阈值 0.812 可用；conformal 外部覆盖 0.629（名义 0.90）→ 校准不合格 → **FAIL**；
- 后果（已生效）：模型身份限定 canonical assay model；绝对 pIC50 输出禁止；解法=Gate T1 或新外部校准集。

## G4 结构（docking）—— **FAIL（排序用途）/ 结构假说用途 HOLD**

- receptor identity / ligand identity / CCD：已审计（fifth_round + h1_mash 工件）✔ 记录在案；
- redock/区分门控：WT TRβ ROC-AUC 0.472 → **FAIL**；
- 后果（已生效）：docking 永久退出候选排序；只允许"结构假说支持"用途且必须带全部协议记录（receptor/PDB/chain/ligand/CCD/grid/exhaustiveness/seed/版本/RMSD）。

## G5 候选放行 —— **`candidate_release = false`（维持）**

G3、G4 未过 → 按放行政策禁止任何正式候选发布。当前池内分子状态：Moracin N=GO 进入湿验证（非候选放行，是实验启动资格）；其余全部历史/降级/对照角色。

## 门控与 FASN GNN 门（FASN_GNN_enable_gate）的关系

资格轮 GNN gate 6/8 条件不满足 → 关闭。本轮 clean benchmark 是该门第一份实证输入（模型增益维度）；其余条件（数据规模/外部校准）不变。**结论见 GNN_clean_benchmark_report.md；门的开关不因单一 benchmark 翻转，需按 G2/G3 证据链整体复审。**
