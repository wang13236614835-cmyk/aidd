# DockScope 平台使用记录（2026-09-09，GUI 仿真人操作）

**会话范围**：按"可以用 DockScope 解决的都用它"指令，把第二阶段中平台可完成的工作全部经 GUI 执行。应用实例 pid 28684（后端 http://127.0.0.1:57938）。

## 一、分子准入筛选模块（替代本地规则筛查，S3 证据升级）

**操作流**（全程 GUI）：门户首页 → 开始分子筛选 → 批次名 `AIDD-hits13-admission-20260909` → 上传 `D:\aidd_ds\hits13.smi`（13 命中物 SMILES）→ 保留默认准入策略（PAINS/Brenk=REVIEW 不硬拒、QED≥0.45、Ro5 违规≤1、SA≤6、盐型最大母体、保留电荷/保留互变异构）→ 执行准入筛选 → 即时完成 13/13。

**结果**（`01_library_check/dockscope_admission_results.csv`，平台溯源包 screen_20260909_181513_1f8a12b1）：

| 判定 | 分子 | 明细 |
|---|---|---|
| **PASS（7）** | daidzein、formononetin、3'-methoxydaidzein、moracin M、biochanin A、capillarisin、isorhamnetin | QED 0.57–0.78、Ro5 零违规、无 PAINS/Brenk 警示 |
| **REVIEW（6）** | moracin N（Brenk isolated_alkene——异戊二烯侧链孤立烯烃，弱警示）；daidzin/piceid/genistin（QED 0.33–0.41 低于 0.45 + Veber 不达标，糖苷类共性）；epicatechin（**正式 PAINS 命中 catechol_A(92)** + Brenk catechol）；toralactone（Brenk PAH_2 蒽醌骨架） | 平台默认 REVIEW 而非拒绝——与"警示≠干扰证明"原则一致 |

**与本地筛查比对**：一致结论（苷类/多酚风险线）；平台版更完整（正式 PAINS 规则集 + Brenk + NIH）。**S3 局余项**：Aggregator Advisor/FAF-Drugs4 在线比对仍待做；警示均为风险线索。

**平台缺陷①**：ADMET-AI 端点全部 error——后端打包缺 `admet_ai` 模块（dist-info 在而模块缺，10 端点 AMES/BBB/DILI/hERG 等无法预测）。详见 `dockscope_admet_note.md`；列为平台外待办。

## 二、对接模块：梯队一 3 分子 × FXR 晶体盒（GUI 全流程）

**操作流**：上传并运行 → 运行名 `AIDD-tier1-FXR-3ligands` → 上传 3 个配体 PDBQT（浅路径 D:\aidd_ds）+ FXR_LBD_1OSH.pdbqt → 启动（无 GPU 自动回退 CPU Vina，与项目引擎同一二进制）→ 完成 3 任务 → 结果工作台 → **Edit docking box 改为 FXR 晶体盒（5.23/29.0/53.67；19.4/22.5/24.8）→ Save & re-dock**。

**结果**：

| 分子 | 自动口袋（错位点） | 晶体盒（正构位点） | 初筛协议（seed42 独立起始） |
|---|---|---|---|
| moracin N | −7.50 | **−9.36** | −9.32 |
| formononetin | −7.13 | **−8.95** | −8.95 |
| daidzein | −7.03 | **−8.78** | −8.79 |

- 晶体盒比自动口袋错位点强 1.7–1.9 kcal/mol——再次确认自动口袋未命中正构位点（本次 FXR 自动口袋偏 Δz≈13 Å，与 THRB/FASN 同型问题，**三靶全部复现**）；
- **平台 GUI 全流程与项目脚本协议两条独立管线的分数差 ≤0.04 kcal/mol、排序一致**——平台可用性实证（固定盒子路径）。

**平台缺陷②（结构性）**：Save & re-dock 的输出文件写出失败（vina returncode=1）——task 目录名把平台**内部**完整路径编码进 ligand_id（`C_DockScopeData_workspace_..._591b_2`），任务路径必然超过 Windows MAX_PATH 260，**用户把输入放浅路径也无法规避**（与此前判断不同：不是输入深浅问题，是平台 task 命名机制）。打分正常保留在 log；姿态文件按 log 原命令短路径重放补全（FASN 时已验证重放与平台逐位一致，本次 moracin N −9.359 亦逐位一致）。产物：`04_multiseed/dockscope_gui_fxr/`。

## 三、动力学/合成模块

工作台"启动动力学模拟"按钮在对接结果上下文中可用（MD 前置=已有对接结果）。本轮**未启动 MD**：按路线文档 T7，MD 需短名单+判据预注册后执行，且 CPU-only 下时长需评估。合成路径规划模块未测（moracin N 为天然产物，合成规划对采购标准品非必需）。

## 四、对证据链的增量

1. **S3（干扰筛查）从"本地规则集"升级为"平台正式 PAINS/Brenk/NIH 规则集"**：moracin N 仅弱警示（isolated_alkene），梯队一三名成员无一硬拒绝；
2. **S1 补充**：平台管线与项目协议在 FXR 正构位点的一致性（≤0.04 kcal/mol）；
3. 平台缺陷清单更新（ADMET-AI 打包缺失、Save&re-dock 长路径 bug、自动口袋三靶全部不命中正构位点）——已全部记录在案并给出规避方案。

**边界**：以上均为计算证据；警示与分数不构成活性/药效；Tier B 人工层与在线干扰库比对仍待完成。
