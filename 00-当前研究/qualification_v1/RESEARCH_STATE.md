# 统一科研状态（RESEARCH STATE）

**冻结日期：2026-09-13｜本文件是三个仓库唯一的科研事实口径入口。任何与本文冲突的表述以本文为准，或登记 OPEN_ISSUES。**

## 1. 研究到了哪里（一段话）

MASH（代谢功能障碍相关脂肪性肝炎）干实验研究，双轴架构（2026-09-12 冻结）：**长期 AIDD 主轴 = FASN**（de novo 脂肪合成），**近期验证轴 = Moracin N**（NRF2-dependent ferroptosis 重定位）。两轴均已完成实验前资格裁决：FASN = CONDITIONAL GO（canonical assay 建模资格成立，跨 assay/天然产物资格不发放）；Moracin N = GO（实验启动包冻结，物料未到货，0 个生物学结果）。本项目至今**没有任何湿实验数据**，所有结论来自公开数据库 + 计算。

## 2. 已成立的科学结论（可引用，须带限定语）

| # | 结论 | 关键数字 | 证据位置 |
|---|---|---|---|
| C1 | FASN canonical assay（CHEMBL5731051）内存在可学习信号 | 96 分子/39 骨架，10 seed scaffold split，ECFP-Ridge R² 中位 0.732（IQR 0.55–0.76），Spearman 中位 0.820 | qualification_round_20260913 |
| C2 | 该信号非伪学习 | Y-scrambling ×20：0/20 permutations exceeded（+1 校正 p=0.0476） | qualification_round_20260913 |
| C3 | 内部性能属化学系列集中（chemical-series confinement），非泄漏 | 10 seed 无结构重复/骨架共享/复制跨集；NN Tanimoto 100%≥0.60、67%≥0.85 | qualification_round_20260913 |
| C4 | 跨 assay 外推失败（阴性结果，同样成立） | 外部 105 分子/3 assay：Ridge R² 0.180、分 assay 全负（−0.16/−0.21/−1.35）、conformal 覆盖 0.629 | qualification_round_20260913 |
| C5 | 天然产物域间隙（阴性结果） | NP54 全部域外（max-Tanimoto 中位 0.136 vs 阈值 0.812）→ NP 定量筛选资格不发放 | qualification_round_20260913 |
| C6 | 化学域内排序可迁移、效价不可迁移（A2 裁决） | E1_ADin（n=14，同检测 SPA+域内）rho=0.880 但偏移 −0.663；小标签校准池化 rho 0.689/0.691；pooled R²≤0.267 不敌 cal_mean 基线 0.272 | advancement_round_20260913 |
| C7 | Moracin N 的 NRF2 证据等级 = involvement（非因果） | 直接功能 + ML385 药理阻断；siNRF2 前不升因果等级 | fifth/qualification_round |
| C8 | MASH 监管事实 | FDA 已批准 resmetirom（2024-03）与 semaglutide（2025-08）；OCA 无 MASH 批准；denifanstat（FASN）Ph2b 组织学阳性（PMID 39396529） | fifth_round_20260912 / final_strategy |
| C9 | WT TRβ docking 区分能力门控失败（阴性结果） | ROC-AUC 0.472（CI 0.341–0.607）→ docking 分数永久退出候选排序 | fifth_round_20260912 |
| C10 | GNN 未证明优于经典 baseline（本轮首次实证，阴性结论） | 同折 10-seed：GCN R²中位 0.078、GINE −0.040 vs Ridge 0.732；GINE 未过置换检验（13/20 反超）；外部全负且无 ADin 排序优势 | qualification_v1（GNN_clean_benchmark_report） |

## 3. 只完成软件验证（不等于科学结论）

- Workbench v0.5.2 全部页面（数据导入/QC/DTI/ADMET/docking 入口/Evidence/Literature Hub）——软件冒烟通过，**其中没有承载任何正式科研结论**；`qualification/` 里的 3×3 DTI、3 化合物 ADMET、vina smoke 是平台验收用的演示件，不是研究结果。
- hepato-gnn-screening 的 numpy GCN 实现——代码审计（梯度/骨架/描述符）通过，但其旧 Top-10 输出是历史结果（见第 5 节）。
- 主库 `src/methods.py`、`verify_methods.py`、`run_diagnostics.py`——数值方法修正工具，软件层验证完毕。

## 4. 需要科学资格验证（尚未取得）

- FASN 跨 assay 泛化（Gate T1：多 assay 对齐数据集，≥15 共享分子/assay 对）——**未开始**，需要新数据组装；
- FASN 模型任何"一般 FASN activity model"表述——禁止，直到 T1 或外部校准集通过；
- GNN 是否在当前数据上提供增益——**本轮以 clean benchmark 首次实证**（结论见 C10，无论正负）；
- Moracin N 全部 Gate M0/B0/1/2/3 生物学判读——等待物料。

## 5. 禁止发布 / 不能再用的表述

- ❌ "已验证最终候选 / 正式 Top-10 / 已证明有效"（旧 Top-10、黄芩苷居首、旧 FXR/Keap1/FASN 榜单 = HISTORICAL，只能作历史参考/教学示例）；
- ❌ "唯一获批药物"（监管口径已于第五轮修正为两个获批药）；
- ❌ 用 docking score 排名候选或宣称机制成立（C9 之后永久禁止）；
- ❌ GNN 优于 baseline / GNN 已验证——在 C10 实证落地前，任何方向的说法都没有证据；
- ❌ "FASN 抑制预测"不带 assay 限定语（必须写 canonical assay model / CHEMBL5731051 系列）。

## 6. 当前主靶点与路线状态

| 路线 | 状态 | 下一道门 |
|---|---|---|
| FASN（AIDD 主轴） | CONDITIONAL GO，A2 收窄后只保排序迁移 | Gate T1（多 assay 对齐） |
| Moracin N（验证轴） | GO，物料未到货 | 到货即执行 M0 |
| THR-β | 临床机制参照/备选 reporter 线 | 暂停主动投入 |
| FXR | 疾病锚点/QC（formononetin 支线） | 暂停主动投入 |
| ACC | 附录级 | 暂停 |
| 旧 GNN 筛选线 | HISTORICAL | 不重启（除非 C10 转正） |
| Docking 筛选线 | REJECTED（排序用途） | 仅保留结构假说支持用途 |

## 7. 三库角色（冻结）

| 仓库 | 路径 | 角色 | 禁止事项 |
|---|---|---|---|
| **aidd**（主库） | `D:\zcode-workspace\aidd-repo-work` | 唯一正式科研结论入口：数据/provenance/模型/验证/文献/结论/导师材料 | 未过资格门控的结果不得写成正式结论 |
| **mash-aidd-workbench** | `D:\aidd destoop` | 执行与审计基础设施（导入/QC/manifest/gate/evidence/日志） | 不得成为第二条候选发布链；不为界面而界面 |
| **hepato-gnn-screening** | `D:\zcode-workspace\hepato-gnn-screening` | GNN 方法学习 + 历史结果核验 + 组员工作台 | 旧 Top-10 等只能标注为历史/验证对象/教学示例 |

## 8. 下一阶段

1. **Gate T1（FASN）**：组装多 assay 对齐数据集（≥15 共享分子/assay 对 → assay 间变换 → 归一化训练集重跑分层验证）；失败则 FASN 降级方法学线。
2. **Moracin N**：导师批准 + 下单（GlpBio ¥520 / MCE 试用装）→ 到货执行 M0 六项。
3. C10 的 GNN 结论并入 FASN_GNN_gate_decision 的下一版复审。
