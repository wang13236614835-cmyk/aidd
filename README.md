# AIDD · MASH 证据驱动研究主库

队长：**王启龙**。

本库是 MASH-AIDD 项目的**完整研究档案、正式科研事实与最终裁决主库**。当前优先研究方向已由“围绕单一靶点直接做 GNN 虚拟筛选”调整为：

> **AI 先用 Workbench 完成高覆盖探索 → AIDD 主库保存全过程文件 → 将必须人工确认的项目送入 GNN 库 → 真人逐项核验并上报 → 真人重新使用 Workbench 以核验结果替换 AI 暂定结果并重跑正式研究 → 只有通过严格资格认证的模型才进入正式筛选。**

核心原则：**先证据，后模型；先可信，后复杂；AI 负责覆盖面，真人负责关键真实性。**

---

## 1. 三库统一定位

### AIDD 主库：完整研究档案 + 正式科研事实

本库保存从 AI 探索到真人复核、正式重算、模型资格认证、候选发布的**全过程**，包括：

- 原始数据、文献证据与来源；
- AI 暂定结果及其完整运行记录；
- 人工核验任务与核验结论；
- 修订前后数据及 provenance；
- 冻结后的正式数据集；
- 模型训练、验证、AD/UQ、筛选与候选结果；
- 失败、拒判、撤回、stale 与历史版本；
- 最终 go / no-go 与候选发布决策。

AIDD 主库回答的问题是：**“这项研究到底发生了什么，哪些结果最终可以作为正式科研事实？”**

### GNN 库：真人科研操作与核验工作区

[GNN 组员核验和打卡库](https://github.com/wang13236614835-cmyk/hepato-gnn-screening) 用于承接 Workbench 自动生成的人工核验任务，包括但不限于：

- 化合物名称 / CID / SMILES / 分子式 / 立体化学核验；
- assay 来源、endpoint、organism、单位、关系符号与 assay lineage 核验；
- IC50 / Ki / EC50 等终点是否可合并的人工判断；
- 重复实验冲突、异常值与标签问题；
- GEO 样本分组、靶点证据与关键文献原文核验；
- scaffold、外部集、泄漏风险与异常预测人工检查；
- docking 关键构象、关键残基及最终候选人工复核；
- 组员分工、任务提交、核验记录与学习打卡。

GNN 库**不是最终科研事实源**。真人核验完成后，结果需上报 AIDD 主库，再由 Workbench 重新构建正式数据和下游结果。

### MASH-AIDD Workbench：AI + 真人共同使用的研究执行器

Workbench 负责：

- AI 高吞吐探索与预跑；
- 文献、靶点、数据、模型、候选的统一流程编排；
- 自动生成 Gate、审计、待核验任务与 stale 状态；
- 接收人工核验结果；
- 用人工核验结果替换 AI 暂定数据；
- 自动使受影响下游产物失效并重新计算；
- 支撑正式模型资格认证和双库筛选。

Workbench 不单独宣布科研结论；**正式结论以 AIDD 主库中的冻结版本和最终裁决为准。**

---

## 2. 完整研究闭环

```text
Workbench：AI 自动 / 半自动探索
        ↓
AI_PROVISIONAL（AI 暂定结果）
        ↓
AIDD 主库：完整保存原始数据、过程文件、日志、manifest、模型与结果
        ↓
Workbench 自动生成 HUMAN_REVIEW_REQUIRED 清单
        ↓
GNN 库：真人逐项核验、纠错、补证据、签名
        ↓
HUMAN_VERIFIED / CORRECTED / REJECTED
        ↓
核验结果上报 AIDD 主库
        ↓
真人重新打开 Workbench
        ↓
导入人工核验结果并替换 AI 暂定值
        ↓
受影响下游结果全部标记 STALE
        ↓
冻结正式数据集（Qualified Dataset）
        ↓
Ridge / RF / XGBoost / GNN 同条件重跑
        ↓
scaffold split + 多 seed + 外部验证
+ Y-scrambling + 泄漏审计 + AD/UQ
        ↓
MODEL QUALIFICATION
        ↓
通过资格认证的最优模型
        ↓
天然产物 / 民族药库 与 老药 / 再利用库分别正式筛选
        ↓
ADMET + 结构补强（Docking / 少量 MD）
        ↓
3–5 个一级候选
        ↓
条件允许时进行酶活 / 细胞实验
        ↓
最终 go / no-go 与结题 / 论文输出
```

**最终目标不是“必须让 GNN 赢”，而是让经过真人核验的数据训练出的最优模型达到正式筛选资格；只有当 GNN 在严格验证下稳定胜出时，GNN 才承担正式筛选。**

---

## 3. 第一阶段：靶点资格认证

当前优先比较：

- **FXR**：主轴候选；
- **ACC**：强竞争靶点；
- **THR-β**：临床转化价值高的强竞争靶点；
- **FASN**：机制强节点，必须重新接受化学数据资格审查，必要时保留为机制靶点而非直接筛选主靶点。

每个靶点至少整合四类证据：

1. **临床 / 指南证据**：MASH/MASLD 指南、已上市药、临床试验；
2. **疾病组学证据**：GEO 多队列、DEG、WGCNA、必要时多算法筛选；
3. **机制证据**：靶点在 MASH 发生发展链中的位置；
4. **成药性证据**：已知配体、实验活性、三维结构、结合口袋与化学可建模性。

输出 `Target Qualification`，允许四类结果：

- `QUALIFIED`
- `CONDITIONAL`
- `MECHANISM_ONLY`
- `REJECTED`

只有通过靶点资格门的靶点，才进入正式活性数据资格认证。

---

## 4. 第二阶段：活性数据资格认证

AI 可先完成大规模收集与预清洗，但正式数据必须经过人工核验。

### 数据来源

- ChEMBL
- PubChem
- 权威文献补充数据

### 强制审计内容

- target / organism 一致性；
- assay lineage 与实验体系；
- IC50 / Ki / EC50 等终点分层；
- 单位与关系符号统一；
- pIC50 / pKi 转换；
- 去盐、去重、canonical SMILES；
- 名称 / CID / SMILES / 分子式 / 立体化学身份；
- 重复实验冲突；
- 异常值；
- scaffold 与化学空间；
- 数据分布与可建模性。

输出正式冻结的 `Qualified Activity Dataset`。

如果人工核验导致数据发生变化，则此前 AI 训练得到的模型、预测与候选自动降级为 `STALE`，必须重跑。

---

## 5. 第三阶段：模型构建与资格认证

模型体系采用并行比较，不预设深度学习一定优于传统方法。

### Baseline

- Ridge
- Random Forest

### 强传统模型

- XGBoost + Morgan / 其他经审计分子表示
- RF + 指纹

### 深度模型

- GCN
- GAT
- MPNN 或经批准的其他 GNN

### 所有模型必须共用

- 同一个冻结数据集；
- 同一 preprocessing；
- 同一 scaffold split；
- 同一 external set；
- 固定评价指标；
- 多 seed 重复；
- Y-scrambling；
- 数据与系列泄漏审计；
- 适用域 AD；
- 不确定度 UQ。

模型输出状态：

- `RESEARCH_VALIDATED`
- `EXPLORATORY_ONLY`
- `REJECTED`

只有 `RESEARCH_VALIDATED` 模型允许进入正式大库筛选。

如果 GNN 没有稳定增益，则保留为方法比较 / 负结果资产，不为了让 GNN “赢”而改 split、隐藏阴性结果或人为调参。

---

## 6. 第四阶段：双库正式筛选

正式筛选必须拆为两条独立轨道，**不直接混榜**。

### Track A：天然产物 / 民族药库

```text
结构身份确认
→ PAINS / 反应性过滤
→ 资格模型预测
→ AD 过滤
→ UQ 过滤
→ ADMET
→ 结构补强
→ Natural Product Ranking
```

重点回答：**是否存在具有新颖化学空间和机制价值的天然产物候选？**

### Track B：老药 / 再利用库

```text
结构身份确认
→ 已知药理与安全信息整理
→ 资格模型预测
→ AD 过滤
→ UQ 过滤
→ ADMET
→ 结构补强
→ Drug Repurposing Ranking
```

重点回答：**是否存在具有较好已知安全基础和转化潜力的再利用候选？**

---

## 7. Docking、MD 与网络药理学的正式定位

这些方法全部**降级为补强证据，不作为活性主裁判**。

### Docking

用于：

- 与阳性对照比较；
- 检查结合姿势是否合理；
- 检查关键残基相互作用；
- 为模型预测提供结构解释。

不能因为 docking score 高就直接宣布候选有效。

### 分子动力学 MD

仅建议对 **3–5 个一级候选 + 阳性对照**进行，用于观察结合稳定性与构象变化，不做全库大规模 MD。

### 网络药理学 / 通路分析

主要用于候选后的机制解释和证据回填，不再承担主筛选器角色。

---

## 8. 人工核验规则

真人核验必须保留可追踪记录，至少包含：

```text
AI 暂定值
→ 原始来源 / 原文 / 数据库记录
→ 真人判断
→ 修正值（如有）
→ 判断理由
→ 核验人
→ 核验日期
→ 状态：VERIFIED / CORRECTED / REJECTED
```

以下项目原则上不得仅由 AI 自动签字为正式通过：

- 关键化合物身份与立体化学；
- assay 是否可合并；
- 关键终点与单位；
- 关键文献原文支持关系；
- GEO 分组与关键疾病证据；
- 冲突实验值与异常值处理；
- 外部验证集来源；
- 最终 3–5 个候选；
- 正式 candidate release。

---

## 9. 统一 Gate

后续三个库统一采用同一套研究资格门：

| Gate | 内容 | 核心问题 |
| --- | --- | --- |
| G0 | 研究问题冻结 | 我们到底在研究什么？ |
| G1 | Target Qualification | 这个靶点值得进入 AIDD 主流程吗？ |
| G2 | Activity Data Qualification | 这些活性数据足够可信且可建模吗？ |
| G3 | Model Qualification | 模型能在严格外部 / scaffold 条件下成立吗？ |
| G4 | Screening Qualification | 该候选是否位于模型适用域且不确定性可接受？ |
| G5 | Structural Support | 结构证据是否与预测相容？ |
| G6 | Candidate Release | 是否允许成为正式一级候选？ |
| G7 | Experimental / Final Decision | 是否形成最终 go / no-go？ |

原则：

- **G1 不过：不进入正式活性建模；**
- **G2 不过：不训练正式模型；**
- **G3 不过：不允许正式大库筛选；**
- **G4 不过：不得进入一级候选；**
- **G5 是结构补强，不替代真实活性；**
- **G6 以后才能称为正式候选。**

---

## 10. 建议统一的研究状态

后续工作台、AIDD 主库和 GNN 人工核验尽量统一以下状态名：

- `AI_PROVISIONAL`：AI 暂定；
- `HUMAN_REVIEW_REQUIRED`：需要人工核验；
- `HUMAN_VERIFIED`：真人确认；
- `CORRECTED`：人工修正；
- `REJECTED`：拒绝进入下游；
- `STALE`：上游改变，旧结果失效；
- `QUALIFIED`：通过当前资格门；
- `EXPLORATORY_ONLY`：仅探索，不可作为正式结论；
- `RESEARCH_VALIDATED`：达到正式研究使用条件；
- `RELEASED`：正式发布候选 / 结果。

---

## 11. 建议统一的跨库 Manifest

为避免三个库复制和篡改科研事实，后续优先通过带 hash 与来源的 manifest 交接：

```text
target_qualification_manifest.json
activity_dataset_manifest.json
model_validation_manifest.json
screening_manifest.json
candidate_evidence_manifest.json
release_decision.json
```

每份 manifest 至少记录：

```text
version
created_at
source_commit
input_hash
upstream_manifest_hash
target
endpoint
status
reviewer
evidence_refs
decision_reason
```

---

## 12. 当前阶段的研究优先级

现阶段**不以重新跑大规模候选筛选为第一任务**，而优先完成：

1. 更新并冻结新的研究问题与 G0；
2. 对 FXR、ACC、THR-β、FASN 进行正式 G1 靶点资格认证；
3. 对最优 1–2 个靶点开展 G2 活性数据资格认证；
4. 将 AI 不能可靠签字的内容输出到 GNN 库进行真人核验；
5. 将人工核验结果重新导入 Workbench，替换 AI 暂定数据；
6. 冻结正式数据集并重新训练 Ridge / RF / XGBoost / GNN；
7. 只有通过 G3 的模型才进入天然产物与老药双库正式筛选；
8. 输出 3–5 个一级候选，并在条件允许时进入酶活 / 细胞验证。

---

## 13. 当前科研边界

当前仍**没有经完整人工核验、严格外部验证和最终 Gate 认证的抗 MASH 有效候选**。

历史计算结果、旧 Top 排名、旧 docking 分数、未经资格认证的 GNN 输出均可保留用于复盘、教学和错误分析，但不得直接升级为正式科研结论。

软件测试通过 ≠ 科学有效；AI 自检通过 ≠ 真人核验；模型能运行 ≠ 模型可筛选；Docking 稳定 ≠ 候选有效。

---

## 14. 主要入口

- [当前研究主入口](00-当前研究/README.md)
- [仓库范围、现有内容与缺口](00-当前研究/REPO_SCOPE.md)
- [给指导老师的研究进展与问题修订](00-当前研究/给指导老师的研究进展.md)
- [五人分工与课程前置](10-任务分配与进度/后续任务分配.md)
- [历史目录与边界](00-索引.md)
- [GNN 真人核验与组员工作区](https://github.com/wang13236614835-cmyk/hepato-gnn-screening)
- [MASH-AIDD Workbench](https://github.com/wang13236614835-cmyk/mash-aidd-workbench)

---

## 15. 项目最终目标

形成一套能够被复核、被重跑、被人工纠错且保留完整证据链的 MASH-AIDD 研究范式：

> **疾病证据 + 靶点资格 + 活性数据资格 + 严格模型验证 + AD/UQ + 双库筛选 + 结构补强 + 真人核验 + 最终实验 / go-no-go**

最终争取产出：

- 经资格认证的主靶点和备选靶点；
- 可复用的高质量活性数据集；
- 经严格验证的最优预测模型；
- 3–5 个具有明确证据等级的一级候选；
- 方法学规范、审计规则与标准化工作台流程；
- 大创结题、论文、专利、竞赛与答辩材料。
