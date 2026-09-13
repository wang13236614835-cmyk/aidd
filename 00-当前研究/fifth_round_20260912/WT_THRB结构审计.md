# WT TRβ 结构审计（第五轮，2026-09-12）

**性质**：正式 WT 体系结构审计，冻结第五轮候选结构的输入状态。本文件不使用 2J4A N331S 的任何结果作为 WT 证据；旧体系见文末"历史体系冻结"。

## 一、正式结构 1：RCSB 3GWS（WT TRβ + T3，native-ligand redocking 用）

| 审计项 | 结果 | 来源 |
|---|---|---|
| PDB ID / DOI | 3GWS，10.2210/pdb3gws/pdb | RCSB `core/entry/3gws`（本包 `raw/rcsb_3GWS.json`） |
| 分子 / 链 | Thyroid hormone receptor beta（THRB / NR1A2），单链 **X**，LBD，UNP 残基 202–460 | DBREF `3GWS X 202–460 UNP P10828 THB_HUMAN` |
| 物种 / 构建 | Homo sapiens，大肠杆菌表达（工程化制备，非突变体） | COMPND/SOURCE |
| SEQADV | **无**——沉积序列即 P10828 202–460，**WT 序列** | 本地 `wt_3GWS.pdb` 全文核对 |
| 分辨率 | 2.20 Å（X-ray，100 K） | REMARK 2 / RCSB |
| 缺失残基 | X 252–262（11 个，hinge 区，远离配体口袋；不在 SITE 内） | REMARK 465 |
| 共价修饰 | MODRES CAS（二甲基胂代半胱氨酸）X 294/388/434——砷酸盐结晶衍生，非生物学突变，均不在口袋 SITE 内 | MODRES / HET |
| 天然配体 | **T3（3,5,3′-三碘甲状腺原氨酸），HET T3 X 500，23 重原子** | HETNAM / HET |
| 口袋 SITE（软件注释） | PHE272, ILE276, ALA279, ARG282, MET313, ARG316, THR329, LEU330, **ASN331**, GLY344, LEU346, ILE353, HIS435, PHE455 + 3 水 | REMARK 800 / SITE AC1 |
| **ASN331 状态** | **天然 ASN（野生型）**，位于配体口袋 | SITE 记录；与 2J4A 的 N331S 相对 |
| 主要引文 | Nascimento AS et al., *J Mol Biol* 2006（hinge 重排与受体功能） | RCSB citation（PMID 未在入口元数据回填） |

## 二、正式结构 2：RCSB 3IMY（WT TRβ + GC-1，selective thyromimetic 参考用）

| 审计项 | 结果 | 来源 |
|---|---|---|
| PDB ID / DOI | 3IMY，10.2210/pdb3imy/pdb | RCSB `core/entry/3imy`（本包 `raw/rcsb_3IMY.json`） |
| 分子 / 链 | TR-beta（NR1A2），单链 **A**，UNP 残基 202–461 | DBREF `3IMY A 202–461 UNP P10828` |
| SEQADV | 仅 1 条：MET A 201 = 起始甲硫氨酸（INITIATING METHIONINE），非点突变；201–460 区段为 **WT** | SEQADV 记录 |
| 分辨率 | 2.55 Å（X-ray，100 K；Rwork 0.225 / Rfree 0.271） | REMARK 2/3 |
| 缺失残基 | A 253–262（10 个，同 hinge 区，不在口袋内） | REMARK 465 |
| 共价修饰 | MODRES CAS A 294/388/434（同上，结晶衍生） | MODRES |
| 参考配体 | **B72 = GC-1 / sobetirome（选择性 thyromimetic），24 重原子（C20H24O4）** | HETNAM B72 / FORMUL |
| 口袋 SITE | ALA279, ARG282, MET313, LEU330, **ASN331**, GLY344, LEU346, HIS435, PHE455 + 2 水 | REMARK 800 / SITE AC1 |
| **ASN331 状态** | **天然 ASN（野生型）** | SITE 记录 |
| 主要引文 | Bleicher L et al., *BMC Struct Biol* 2008;8:8，PMID 18237438，DOI 10.1186/1472-6807-8-8（GC-1 亚型选择性结构基础） | JRNL 记录 |

**亚型口袋对照**（`pocket_residues_wt.json`，TRα 3ILZ）：TRα/TRβ 口袋残基组成实质保守——与既往"口袋残基不解释亚型选择性"结论一致；选择性来自更广区域/动力学，不能由本口袋 docking 分数差推得。

## 三、正式对接受体（3GWS-derived WT，H1Valid 批次）

| 审计项 | 结果 |
|---|---|
| 受体文件 | `C:\DockScopeData\...\H1Valid_20260910_104825_329168\input\PDB\WTheavy.pdb` → meeko `mk_prepare_receptor` → `receptor.pdbqt` |
| SHA-256 | `ce03903c86ace0adf82b9d7c202827ba47dd3f66993208c33d977359d1d83963`（`final_receptor_audit.json`，与 strict 本地副本一致） |
| 残基数 / 原子数 | 247 残基 / 1972 原子（制备后） |
| 质子化 | Meeko 模板 + Gasteiger 电荷（去除 PDBFixer 氢后）；**非 pH/互变异构体系**——PDBFixer pH7.4 氢仅中间产物，非最终对接状态 |
| 特殊残基检查 | `special_residues_ok: true`（胂代 Cys 等按模板处理，无口袋冲突） |
| 盒子（T3 晶体盒） | center (5.157, 20.080, 29.010) Å；size (22.156, 19.867, 20.893) Å |
| 配体制备 | SMILES → RDKit ETKDGv3 (seed 42) → MMFF → Meeko PDBQT（项目标准管线） |
| 引擎 | AutoDock Vina 1.2.7（DockScope 自带 `vina.exe`），rigid receptor |

## 四、多种子姿态恢复（每 seed 只取最高分 pose；禁止跨 mode 挑最低 RMSD）

### 3GWS + T3（native ligand redocking；4 seeds 7/42/123/20260910，exh 8）

| seed | 最高分 pose 分数 | 最高分 pose RMSD (Å) | 备注 |
|---|---|---|---|
| 7 | −9.497 | **0.441** | 其余 mode 0.488–8.043（含翻转姿态，仅记录） |
| 42 | −9.498 | **0.473** | |
| 123 | −9.497 | **0.469** | |
| 20260910 | −9.497 | **0.474** | |
| **median** | −9.497 | **0.471** | range 0.033；无失败 seed |

来源：`candidate_decision_20260910/raw/audits/t3_pose_rmsd_per_seed.json`（heavy-atom symmetry-aware，原始受体坐标系）；分数来自同批 4-seed 重复表。

### 3IMY + GC-1（selective thyromimetic 参考；同 4 seeds；本轮新算）

| seed | 最高分 pose 分数 | 最高分 pose RMSD (Å) | 全 mode RMSD (Å，仅透明记录) |
|---|---|---|---|
| 7 | −10.246 | **0.692** | 0.692/1.188/0.834/1.703 |
| 42 | −10.233 | **0.669** | 0.669/0.708/1.184/0.891 |
| 123 | −10.232 | **0.708** | 0.708/0.701/1.326/0.795/1.591 |
| 20260910 | −10.226 | **0.664** | 0.664/0.677/1.221/1.010/0.827/1.559/1.993 |
| **median** | −10.232 | **0.681** | range 0.044；无失败 seed |

方法：GC-1 对接 PDBQT（`h1_mash/gc1_seed*.pdbqt`，H1Valid WT 受体+T3 盒）经 Meeko 重建化学模板；晶体 B72 坐标（`wt_3IMY.pdb` HETATM）经键序无关子结构匹配转移到同一模板；RMSD = 重原子、自构象感知（RDKit GetBestRMS），逐 mode 单独计算、最高分 mode 单独判定。脚本 `derived/gc1_pose_rmsd.py`，输出 `derived/gc1_pose_rmsd_per_seed.json`。

### 几何验证结论（限定表述）

- T3 与 GC-1 全部 seed 的**最高分 pose** RMSD ≤2 Å（T3 ≤0.474；GC-1 ≤0.708）。
- 允许的唯一表述：**"docking protocol can approximately reproduce crystallographic poses."**
- 禁止表述：可预测活性、可预测激动/拮抗方向、可预测 MASH 疗效、可预测 THRβ 选择性或亚型优先级。次要 mode 含 ~8 Å 翻转姿态（T3）与 1.2–2.0 Å 备选构象（GC-1），证明打分函数对姿态排序不完美，更不支持活性外推。

## 五、历史体系冻结（不覆盖、不复活）

- **2J4A = N331S 工程突变体**（historical exploratory system）。旧 `P0_区分能力门控结果_20260909.md`（ROC-AUC 0.346，FAIL）与旧全库排名继续保留原文，但**不得重新作为 WT 结论来源**，也不得与第五轮 WT gate 结果合并。
- 旧 gate 勘误链保留：MW 残差 AUC 原报告 0.647 为符号翻转错误，正确值 **0.3527**（更正后仍无改善）；EF@Top-15 统一口径 1.4637；"化学型失配主因"降级为未证明假设。
- WP3 平台/脚本一致性（ρ=0.906）为技术复现证据，与区分能力判定无关。

## 六、原始输入/输出与哈希索引

| 项目 | 路径 |
|---|---|
| RCSB 元数据 | `raw/rcsb_3GWS.json`、`raw/rcsb_3IMY.json`（2026-09-12 拉取） |
| 3GWS FASTA | `raw/3GWS.fasta` |
| 本地结构 | `raw/source_wt_3GWS.pdb`、`raw/source_wt_3IMY.pdb`（wp_exec 副本） |
| T3 晶体配体 | `raw/source_3GWS_t3_sdf`（`T3_3GWS_corrected_crystal.sdf`） |
| 受体审计 | `raw/source_candidate_decision/final_receptor_audit.json`（sha256 见上） |
| T3 多种子 RMSD | `raw/source_candidate_decision/t3_pose_rmsd_per_seed.json` |
| GC-1 多种子 RMSD | `derived/gc1_pose_rmsd_per_seed.json`（本轮新算） |
| 旧 gate 原始结果 | `raw/source_old_gate_metrics.json`、`raw/source_old_gate_raw.json`（2J4A N331S，仅历史） |
| WT gate 运行 | `derived/wt_gate_run/`（受体副本、逐分子 log、PDBQT、raw_results.json、gate_metrics.json） |

访问日期：2026-09-12。RCSB: https://data.rcsb.org/rest/v1/core/entry/3gws 、https://data.rcsb.org/rest/v1/core/entry/3imy 。
