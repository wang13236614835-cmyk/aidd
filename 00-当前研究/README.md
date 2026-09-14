> **2026-09-14 资产保留与 GNN 重规划（当前最新）**：当前阶段为 **pipeline revalidation / 资产保留优先**，不是候选已筛完。三个仓库角色不变：aidd 主库=唯一正式科研结论入口；Workbench=执行/审计只读镜像；hepato-gnn-screening=GNN 方法学习+历史复核+组员工作区。新增 [asset_preservation_and_gnn_replan_v1/执行总览.md](asset_preservation_and_gnn_replan_v1/执行总览.md) 与 [MASTER_ASSET_REGISTRY.csv](asset_preservation_and_gnn_replan_v1/MASTER_ASSET_REGISTRY.csv)：32 项精选高价值资产全部存在并完成 hash 登记；旧数据、模型、split、日志、受体、docking 输出均保留，通过 VERIFIED/REQUALIFY/HISTORICAL/REJECTED 限定用途。GNN 仓库裁决为**小修即可、不改仓库名**，当前 `gated/closed`；FASN Gate T1 仍 pending；`candidate_release=false` 维持。

> **2026-09-13 qualification_v1 / 第五轮资格裁决（历史最新资格轮）**：三库（aidd 主库 / mash-aidd-workbench / hepato-gnn-screening）统一科研状态冻结；前四轮资产完成 **A/B/C/D 四类审计台账**（38 项：VERIFIED/REQUALIFY/HISTORICAL/REJECTED）；assay-level provenance 审计 **PASS**（51 assay 全 lineage、0 缺失、canonical 96 全覆盖、外部 0 重叠）；RERUN_DECISION 裁决**仅 GNN benchmark 进入复算**并已实跑——**GNN 未证明优于经典 baseline**（同折断言 PASS：Ridge 中位 R²=0.732008 逐位复现；GCN 0.078 / GINE −0.040；GINE 13/20 置换反超；外部 105 全负、无 ADin 排序优势；MC-dropout UQ 无效）→ GNN 门控维持关闭但首次有实证；门控现状 G0/G1/G2 PASS（G1 限 canonical）、G3/G4 FAIL（阴性冻结）、**candidate_release=false 不变**；Workbench 新增只读 Research State 页（17）。入口 [qualification_v1/README.md](qualification_v1/README.md)，状态 [qualification_v1/RESEARCH_STATE.md](qualification_v1/RESEARCH_STATE.md)，QC PASS。

> **2026-09-13 推进轮**：双轴推进完成——**Track A（FASN）= A2**：跨 assay 失败分解为化学域失配（主）× assay 效价标尺失配（次）；化学域内排序可迁移（E1_ADin rho=0.880，n=14）、小标签校准后跨 assay 排序 rho=0.69 稳定，但绝对效价迁移不成立（cal_mean 基线仍最优）→ FASN 维持 **CONDITIONAL GO**、适用范围收窄（过 AD + 排序+不确定性输出 + 禁绝对 pIC50），下一道门 Gate T1（多 assay 对齐数据）；**Track B（Moracin N）**：物料未到货 → 实验启动包冻结，M0/B0/毒窗/Gate1 全部 not_executed，双轴判读框架与 Gate2/3 计划就绪。三项方法学口径修正生效（0/20 exceeded、chemical-series confinement、NRF2 证据等级）。交付见 [advancement_round_20260913/推进轮_执行总览.md](advancement_round_20260913/推进轮_执行总览.md)。

> **2026-09-13 资格验证轮（当前最新）**：双轴资格裁决完成——**FASN 主轴 = CONDITIONAL GO**（canonical assay 建模资格成立：10 seed scaffold ECFP-Ridge R² 中位 0.732、Y-scrambling 0/20 exceeded；但外部验证 R² 0.18/分 assay 全负、54 天然产物 0/54 域内 → 模型限定为 canonical assay model，天然产物筛选资格不发放，GNN 保持关闭）；**Moracin N = GO**（正式进入 MASH 相关肝细胞验证，Gate M0→B0→1→2→3 实验前资格冻结完毕，生物学结果未执行）。交付见 [qualification_round_20260913/资格验证_执行总览.md](qualification_round_20260913/资格验证_执行总览.md)，判定见 [双轴资格验证决策.md](qualification_round_20260913/双轴资格验证决策.md)。项目维持双轴、不对称投入（近期主投入 Moracin N 湿验证，FASN 进入条件解决期）。

> **2026-09-12 最终战略冻结轮（当前最新）**：基于前七轮全部原始数据，正式冻结双轴架构：①**长期主 AIDD 轴 = FASN / de novo lipogenesis**，先做 provenance、assay-specific baseline、scaffold/time/external validation、AD/UQ，再决定是否启用 GNN；②**近期高创新验证轴 = Moracin N 相关 NRF2-dependent ferroptosis regulation → MASH 相关肝细胞脂毒性**，用最小 Gate 0–3 功能实验验证。THRβ 为临床机制参照/备选 reporter 线，FXR 为疾病锚点/QC，ACC 为附录，docking 永不承担活性排序。最终交付见 [final_strategy_round_20260912/最终战略冻结_执行总览.md](final_strategy_round_20260912/最终战略冻结_执行总览.md) 与 [final_strategy_round_20260912/导师审批版_最终战略冻结.md](final_strategy_round_20260912/导师审批版_最终战略冻结.md)。当前无湿实验结果、导师签核和采购仍未完成；FASN 模型虽有内部 scaffold 信号但尚无独立外部验证，天然产物预测未放行。

> **2026-09-12 第六轮：候选验证计划（历史执行包）**：第五轮释放清单已转为可采购、可执行、可证伪的最小湿实验包，交付见 [sixth_round_20260912/第六轮_执行总览.md](sixth_round_20260912/第六轮_执行总览.md)。主线与Gate判据已被第七轮战略收敛重新定位；第六轮原始预算、采购与预注册文件保留不覆盖。
> **2026-09-12 第五轮审计更新**：五候选（moracin N / formononetin / 3'-methoxydaidzein / isorhamnetin / biochanin A）完成外部证据、天然来源、可开发性与 WT 结构/门控审计，交付见 [fifth_round_20260912/第五轮_执行总览.md](fifth_round_20260912/第五轮_执行总览.md)。
> 关键状态：①WT TRβ 区分能力门控失败（ROC-AUC 0.472，CI 0.341–0.607）——**docking 分数不再参与候选排序**；②moracin N 主假说转为 Nrf2/ferroptosis 机制重定位（THRβ 降为结构假说）；③3'-methoxydaidzein 因亚微摩尔 NaV 活性降 D；④监管口径修正：FDA 已批准 resmetirom（2024-03）与 semaglutide（2025-08）两个 MASH 药物，OCA 无 MASH 批准；⑤过度表述登记于 [历史错误与修正记录](fifth_round_20260912/历史错误与修正记录.md)，2026-09-10 前含"唯一获批/无人研究"等字样的文档均为历史版本。
> **历史投稿线说明**：FXR/GNN/CW-BCS主稿仍作为历史/并行投稿资产保留，真实导师未签核；第七轮已将当前主发现线冻结为 Moracin N–Nrf2/ferroptosis 机制重定位。V2诊断与FASN修复顺序不自动转为当前主线，只有实际引用的分支才验收对应证据。

# 当前MASH研究主入口

**王启龙带队；干实验优先；暂无湿实验材料。**

[给指导老师的研究进展](给指导老师的研究进展.md) · [分工与计划](../10-任务分配与进度/后续任务分配.md) · [诊断数据摘要](validation/20260905/diagnostic_summary.json) · [结构审计](validation/structure_audit/summary.json) · [数据审核台账](data_review/README.md)

当前代码：`src/methods.py`修正数值方法；`run_diagnostics.py`只读历史输入并写新的诊断目录；`validate_docking.py`进行CCD修复与独立初始构象复算，复用历史受体因此仍需受体审核。

```text
python 00-当前研究/verify_methods.py
python 00-当前研究/run_diagnostics.py --fit-baseline --output <新目录>
# 先设置VINA_BIN，以下只做结构方法诊断
python 00-当前研究/validate_docking.py --output <新目录>
```

默认不产生新正式候选榜。正式数据、模型、对接门槛未过；旧标签仍需assay谱系复核。依赖版本见requirements-validated.txt。全部历史研究在01–09类保留，新正式工作在此形成可审阅版本，打卡在GNN库。
