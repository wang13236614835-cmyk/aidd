# research_chain_v2 → research_chain_v3 迁移报告

**日期：2026-09-27｜权威库：AIDD｜状态：CURRENT**

## 裁决

从 2026-09-27 起，`research_chain_v3_20260927` 成为当前默认研究链。

以下内容全部保留，但不再作为“当前默认计划”：
- research_chain_v2_20260921：HISTORICAL_BASELINE
- qualification_v1：PRESERVED_METHOD_EVIDENCE
- FASN 建模/GNN benchmark：PRESERVED_NOT_DEFAULT_CURRENT
- Moracin N–NRF2/ferroptosis：PRESERVED_NOT_DEFAULT_CURRENT
- 旧 Phase 2A/2B 和 W3–W16：HISTORICAL_BACKLOG_NOT_DEFAULT

## v3 当前研究方法

当前路线由“模型/旧周计划中心”改为“证据资格 + 人工核验 + 真实材料 + 直接药理 + 疾病场景”：

G0 研究问题与主张冻结
→ G1 靶点/方向资格
→ G2 身份、来源、关键证据真人资格
→ G3 反向药理与具名候选池
→ G4 采购/W0
→ G5 ADORA2A binding/cAMP
→ G6 HSC/hepatocyte/macrophage MASH 场景
→ G7 RELEASE/HOLD/REJECT/INCONCLUSIVE

当前状态：G0 PASS、G1 PASS（治疗方向仍保持 context-dependent 限制）、G2 HUMAN_REVIEW_REQUIRED、G3 REVIEW、G4-G7 BLOCKED。

## 三轨候选

- NEW_LEAD：5 个冻结 MCULE。
- REPURPOSING_NEW_MECHANISM：老药与成熟天然产物。
- UNDEREXPLORED_DISCOVERY：低/中研究饱和天然产物。

不再用“论文多”直接剔除老成分；研究成熟度只影响“全新分子”叙事，不削弱新机制/新适应证价值。

## 当前科学硬状态

- 5 MCULE identity gate = PASS。
- 0/5 有直接实验 ADORA2A 活性。
- ADORA2A/MASH = UNRESOLVED_CONTEXT_DEPENDENT。
- botanical pool = 37/37 retained。
- W0 ready_count = 0。
- wetlab = NOT_EXECUTED。
- candidate_release = false。
- real_human_review_completed = 0 / 7；W4 从零开始执行正式真人核验。
- 当前执行周 = W4（2026-09-28—2026-10-04）：G2 真人核验为主，G3 证据复核并行，湿实验执行方沟通并行；G4-G7 保持 BLOCKED。

## 三库职责

- AIDD：唯一正式科研事实源，维护 v3 Gate/状态/方法。
- Desktop Workbench：默认只读 v3，负责 AI 协作、任务/证据呈现、严格人工入口、W0-W4 状态与最终发布界面。
- hepato-gnn-screening：当前真人核验与成员执行工作区；GNN/旧模型成为方法学习/历史复核资产。

## 防回退

- Desktop CURRENT v3 缺失时 fail-closed，不静默回退 v2。
- GNN 的旧 sync_v2_to_pages.py 默认拒绝运行，只有显式 --legacy-v2 才能历史重放。
- 旧 Phase2B importer 保留，但只在“历史/兼容任务包”区域出现。

## 工程验证

- Desktop 定向 v3 回归：30/30 passed。
- Desktop 页面导航 + 当前 Gate：32/32 passed。
- ADMET-AI isolated real smoke：1/1 passed。
- Desktop 全套：441 passed, 3 skipped, 0 failed。
- AIDD v3 state / Gate / task / hash 验收：PASS。
- GNN v3 状态 / 5 人工作台 / 旧生成器保护验收：PASS。

## 现在真正剩下的研究动作

1. W4 优先完成 HR-ADORA2A-001～004 真人 Git 核验与交叉复核；只有 AIDD 受控导入后才计入正式完成数。
2. HR-ADORA2A-005 天然产物来源核验并行；根据 HR-003/004 冻结 G3 的药化/直接 A2A 证据表述边界。
3. 并行联系湿实验执行方/合作导师，记录 binding/cAMP 平台、样品、费用与可行性；沟通本身不改变 Gate。
4. HR-ADORA2A-006 在真实下单/到货/lot/CoA 前保持 BLOCKED；W0 ready_count 继续为 0。
5. G4/W0 真正放行后再进入 W1 binding → W2 cAMP → W3 selectivity/artifact → W4 liver-context。
6. 只有真实实验和人工审计满足主张后才进入 G7；candidate_release 继续 false。