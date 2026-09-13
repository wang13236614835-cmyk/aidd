# WT TRβ 区分能力门控——结果与判定（第五轮，2026-09-12）

**性质**：预注册方案的正式执行结果。判据与数据构成见 `WT_gate_preregistration.md`（运行前冻结，本文件不回改任何判据）。旧 2J4A N331S 门控（ROC-AUC 0.346，FAIL）为历史结果，保留于 `raw/source_old_gate_metrics.json`，不与本结果合并。

## 一、执行概况（全部留痕于 `derived/wt_gate_run/`）

| 项 | 值 |
|---|---|
| 受体 | 3GWS-derived WT TRβ（H1Valid WTheavy 制备链），SHA-256 `ce03903c…d83963`，247 残基 |
| 盒子 | T3 晶体盒 center (5.157, 20.080, 29.010)，size (22.156, 19.867, 20.893) |
| 引擎/参数 | AutoDock Vina 1.2.7（rigid），exhaustiveness 8，CPU 8，num_modes 9，seed **20260912** |
| 数据集 | ChEMBL CHEMBL1947（human TRβ）：45 阳性（≤10/10–100/100–1000 nM 三层各 15）+ 31 floor 阴性；选择规则与旧 gate 同源且确定性重推 |
| 配体 | 复用项目标准制备 PDBQT（RDKit ETKDGv3 seed42 → MMFF → Meeko；即旧 gate 同批文件），78/78 无缺失 |
| 方向锁定 | `positive_score = −vina_score`（运行前写入预注册；报告同时给原始分数） |
| 并列处理 | Mann–Whitney mid-rank；EF@Top15 含与第 15 名并列的全部记录（本次无跨界并列） |
| Bootstrap | 分层重抽样 10,000 次，seed 20260912，全部有效 |

## 二、主指标与判定（对照预注册阈值）

| 指标（锁定） | 结果 | 预注册阈值 | 判定 |
|---|---|---|---|
| ROC-AUC（45 阳性 vs 31 floor 阴性） | **0.472** | ≥0.70 支持；0.50–0.70 弱；<0.50 失败 | **失败** |
| ROC-AUC bootstrap 95% CI | **[0.341, 0.607]** | 区间不得主要覆盖随机/反向 | 覆盖 0.5 且下探 0.34——不通过 |
| PR-AUC（基线阳性率 0.592） | **0.693**（CI [0.595, 0.785]） | 与 ROC/EF 方向一致支持 | 仅略高于基线，提升弱 |
| EF@Top-15（mid-rank，实际 n=15） | **1.576**（top15 含 14 阳性；期望 8.9） | 一致支持 | 顶部有富集但孤证 |
| 分层 AUC（≤10nM / 10–100nM / 100–1000nM） | **0.596 / 0.232 / 0.587** | 分层敏感性 | 中层反向（0.232），方向不一致 |
| 阳性锚（单独报告，不入 ROC） | T3 −9.527；resmetirom −10.220 | — | 锚点分数仍好——再次证明"锚点好≠管线可分"（与旧 gate 教训一致） |

**判定：门控失败（ROC-AUC<0.50 且 CI 跨随机/反向，分层方向不一致；EF 的顶部富集不足以翻案）。**

与旧 N331S gate（0.346）相比，WT 受体把整体 AUC 拉近随机（0.472），方向性问题减轻，但仍无区分能力。这属于描述性对比，不改变两次判定同为 FAIL 的事实。

## 三、硬规则（即刻生效）

按预注册第三节：

1. **立即停止使用 docking score 作为候选排序核心。** 本项目此后任何候选顺序不得由 Vina 分数决定，禁止"−10.8 优于 −9.7 所以优先"式论证。
2. 候选顺序此后由：① 疾病实验依据；② 新机制可证伪性；③ 创新性；④ 可操作性；⑤ ADMET/成药性决定。
3. Docking 在本项目中的最高地位为 `structural hypothesis support`（结构假说支持）：只允许用于（a）确认分子可在口袋采取占据构象（几何恢复通过：T3 ≤0.474 Å、GC-1 ≤0.708 Å）；（b）生成假说；（c）技术可复现性陈述。
4. 旧 N331S gate 与本次 WT gate 两次失败均保留；不得以更换打分函数/受体/盒子重跑后宣称"新门控通过"来覆盖（预注册约束）。

## 四、诚实边界与事后解释（标注为事后，不影响判定）

- floor 阴性 = "测不出至下限"，非真非结合子——方案已声明，天然压低可达 AUC 上限（该局限两次 gate 相同）。
- 化学型失配假设（甲状腺激素骨架多碘代两性 vs 天然产物/杂环）依旧未证明，仅作事后解释保留。
- EF@Top15=1.58 的顶部富集与中层 AUC 0.232 并存，提示分数在分布顶部与中部信息矛盾——这正是不能用单点指标外推排序的又一证据。
- 本门控不测：姿态正确性（另有 T3/GC-1 恢复证据）、TRα、激动/拮抗方向、MASH 疗效、亚型选择性。

## 五、产物索引

- 逐分子 Vina stdout/log：`derived/wt_gate_run/<CHEMBL_ID>.log`（78 个）与 `_out.pdbqt`
- 原始结果：`derived/wt_gate_run/raw_results.json`（id/label/score/layer/potency/returncode/n_modes/seconds）
- 指标：`derived/wt_gate_run/gate_metrics.json`（含运行参数、方向、tie、bootstrap 元数据）
- 执行脚本：`derived/run_wt_gate.py`；stdout/stderr：`logs/run_wt_gate.stdout|stderr`
- 受体副本与 SHA-256：`derived/wt_gate_run/receptor_WTheavy_3GWS.pdbqt`
- 历史对照：`raw/source_old_gate_metrics.json`（2J4A N331S，ROC 0.346）

执行时间：2026-09-12 07:19 UTC。数据访问：ChEMBL REST（2026-09-09 取数快照 `p0_refs/chembl_tr_reference_raw.json`，本轮只读复用，未重新筛选以保持与预注册一致）。
