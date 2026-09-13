# WT TRβ 区分能力门控预注册（第五轮，2026-09-12）

## 状态与不可回改规则

本文件在正式 WT 3GWS 基准对接前冻结。执行后不回改数据筛选、指标方向、并列处理、bootstrap 设定或通过阈值；任何替代数据集或打分函数只能另列为事后探索。旧 `P0_区分能力门控结果_20260909.md` 是 **2J4A N331S historical exploratory system** 的失败结果（ROC-AUC 0.346），保留但不覆盖本门控。

## 科学问题

在固定人源 WT TRβ 结构和固定 Vina 协议下，分数是否能区分可追溯的 TRβ 活性分子与 assay-floor 记录？该门控只评估排序区分能力，不评估姿态正确性、激动方向、TRα 选择性或 MASH 疗效。

## 受体和协议

- 正式受体：RCSB **3GWS**，human TRβ ligand-binding domain + T3；本地审计输入 `wp_exec_20260909/00_task_ledger/wt_receptor_validation/wt_3GWS.pdb`。
- 受体状态：WT TRβ 结构审计后采用 3GWS-derived prepared receptor；2J4A 的 N331S 不进入正式 WT gate。
- 盒子：沿用已验证 3GWS T3 crystal box，center = `(5.157, 20.080, 29.010)` Å，size = `(22.156, 19.867, 20.893)` Å。
- AutoDock Vina 1.2.7 CPU；rigid receptor；exhaustiveness 8；CPU 8；num_modes 9；每个分子一个固定 seed = 20260912（如实际引擎使用不同 seed，记录实际 seed，不回写预注册）。
- Vina 原始分数越负越优。分析前定义 `positive_score = -vina_score`，因此越大越可能为阳性；同时报告原始 score 和变换方向，禁止把 AUC 方向翻转后当作改善。

## 数据来源、标签和记录粒度

- 主数据来源：`p0_refs/chembl_tr_reference_raw.json`，由 ChEMBL human TRβ target CHEMBL1947 活性记录构建；扫描范围和原始响应保留。
- 阳性：standard_type ∈ {Ki, IC50, Kd, EC50, Potency, AC50, XC50}，standard_relation `=`，standard_value ≤ 1000 nM，且有可用 canonical SMILES。按 ≤10、10–100、100–1000 nM 三层各取按 potency 升序的前 15 个，目标 45 个。
- 阴性：standard_relation `>` 且 assay floor ≥10000 nM，有可用 canonical SMILES；全部 31 个保留。该标签只表示“在该 assay 条件下未达到检测下限”，不是证明非结合。
- 记录字段：compound/ChEMBL ID、activity_id（如原始记录可回填）、value、relation、unit、standard_type、assay_id、assay description、species/target、construct/variant、document/reference、SMILES、MW、label、stratum、docking score、prep/docking status。
- 结合与功能终点不混写为同一种机制；主结果给合并集，并按 endpoint/活性层级做敏感性分析。构建体、物种或 assay 条件不一致者保留但标记可比性限制。
- 不把项目 54 天然产物库当真阴性；库内分数只能作为描述性附录，不进入主 ROC 标签。

## 预注册统计指标

主指标：

1. ROC-AUC，阳性 vs floor 阴性，使用 `-vina_score` 方向。
2. PR-AUC，正类定义为阳性，使用相同方向。
3. bootstrap 95% CI：stratified resampling within positive and negative labels, 10,000 replicates，seed = 20260912；每次样本不足/单一标签导致指标不可算时记 NaN 并报告有效重复数。
4. Top-K enrichment：固定 K=15，按 positive_score 降序；相同分数使用 mid-rank，进入 cutoff 的并列记录全部纳入并报告实际 n；EF = (top-K positive fraction)/(总体 positive fraction)。另报告 top 20% 比例作为描述性指标，不将不可达阈值硬写成通过条件。

次级：按 ≤10、10–100、100–1000 nM 阳性层分别计算 ROC/PR；按 binding/function、assay type、可比构建体可用性做敏感性分析；不使用 MW 残差替换主指标。若做 MW 相关分析只作为描述性混杂检查，不能回写主判定。

## 判定规则（执行前锁定）

- 支持：ROC-AUC ≥ 0.70，且 bootstrap CI 不主要覆盖随机/反向区间，PR-AUC 和 EF 方向一致支持；
- 弱/不足：ROC-AUC 0.50–0.70 或 CI 很宽/PR-AUC、EF 不一致；
- 失败：ROC-AUC <0.50，或结果显示反向排序，或 PR-AUC/EF 不支持且 CI 与随机/反向大量重叠。
- 任何失败/不足都触发硬规则：**停止使用 docking score 作为候选排序核心**。后续候选释放按疾病实验证据、新机制可证伪性、创新性、可操作性、ADMET/成药性和证据完整度；docking 只能写 `structural hypothesis support`。

## 数据泄漏和停止规则

- 选择集、受体、盒子、参数、指标方向和阈值在正式运行前冻结。
- 不能用结果删除难看的分子、替换 floor 阴性、调整 seed/盒子/引擎后重新声称门控通过。
- 如果 3GWS prepared receptor、ligand preparation 或完整输出无法审计，门控结论为 `NOT_TESTED/INSUFFICIENT`，不填补结果。
- 旧 2J4A N331S gate 只作历史对照，不能与 WT 结果合并。

## 原始输出要求

保存：输入 JSON/CSV、受体和配体 SHA-256、每条 Vina stdout/stderr/log、PDBQT、运行 manifest、统计脚本、软件版本、执行时间和异常。结果报告必须给原始 score、`-score` 方向、tie/mid-rank 规则、bootstrap seed/有效重复数、PR-AUC、CI、Top-K EF、分层结果及所有失败/排除理由。
