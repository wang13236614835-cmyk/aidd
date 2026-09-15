# 当前 MASH-AIDD 研究主入口

**负责人：王启龙。当前优先方向：证据驱动的 MASH-AIDD 靶点资格认证与候选发现。**

> 2026-09-15 起，原“FXR/GNN/CW-BCS 主稿优先”方案降为历史阶段性方案，不再作为当前唯一主线。新的正式研究范式以 **AI 高覆盖探索 → 人工关键核验 → 正式替换重算 → 模型资格认证 → 双库筛选** 为核心。

根目录总章程见：[`../README.md`](../README.md)。

---

## 1. 当前总路线

```text
Workbench：AI 自动 / 半自动探索
        ↓
AI_PROVISIONAL
        ↓
AIDD 主库保存完整过程、原始文件、日志、manifest 与结果
        ↓
Workbench 生成 HUMAN_REVIEW_REQUIRED
        ↓
GNN 库：真人逐项核验、纠错、补证据、签名
        ↓
HUMAN_VERIFIED / CORRECTED / REJECTED
        ↓
上报 AIDD 主库
        ↓
真人使用 Workbench 导入人工核验结果
        ↓
替换 AI 暂定值；受影响下游全部标记 STALE
        ↓
冻结 Qualified Activity Dataset
        ↓
Ridge / RF / XGBoost / GNN 同条件正式重跑
        ↓
scaffold split + 多 seed + external
+ Y-scrambling + leakage audit + AD/UQ
        ↓
MODEL QUALIFICATION
        ↓
通过资格认证的最优模型
        ↓
天然产物 / 民族药库 与 老药 / 再利用库分轨筛选
        ↓
ADMET + Docking + 少量 MD（补强证据）
        ↓
3–5 个一级候选
        ↓
条件允许时进入酶活 / 细胞实验与最终 go / no-go
```

核心原则：

- **先证据，后模型；先可信，后复杂。**
- AI 负责覆盖面与重复性工作，真人负责关键真实性与最终签字。
- 不预设 GNN 一定优于传统机器学习。
- Docking、MD、网络药理学不得替代真实活性与外部验证。
- 历史结果保留，但未经新 Gate 重新认证不得直接升格为正式结论。

---

## 2. 当前靶点优先级

当前正式比较对象：

1. **FXR**：主轴候选；
2. **ACC**：强竞争靶点；
3. **THR-β**：临床转化证据强的竞争靶点；
4. **FASN**：机制强节点，重新接受化学数据资格审查，必要时定位为 `MECHANISM_ONLY`。

不再使用“疾病相关性强 = 一定适合 AIDD 建模”的简单推断。

每个靶点必须分别完成：

- 临床 / 指南证据；
- GEO / 疾病组学证据；
- 机制证据；
- 成药性与化学可建模性证据。

输出：

- `QUALIFIED`
- `CONDITIONAL`
- `MECHANISM_ONLY`
- `REJECTED`

---

## 3. 当前统一 Gate

| Gate | 名称 | 当前要求 |
| --- | --- | --- |
| G0 | 研究问题冻结 | 明确疾病、靶点、endpoint、成功标准与研究边界 |
| G1 | Target Qualification | 临床/指南、组学、机制、成药性证据通过 |
| G2 | Activity Data Qualification | assay、结构身份、终点、单位、冲突、scaffold 等通过人工核验 |
| G3 | Model Qualification | scaffold/external、多 seed、Y-scrambling、泄漏、AD/UQ 通过 |
| G4 | Screening Qualification | 候选处于适用域且不确定性可接受 |
| G5 | Structural Support | Docking / MD 等与主证据相容 |
| G6 | Candidate Release | 人工审计后允许成为一级候选 |
| G7 | Experimental / Final Decision | 实验或最终证据形成 go / no-go |

当前不得跳过 G1/G2 直接为了“跑模型”进入正式 G3。

---

## 4. AI 与真人职责边界

### AI / Workbench 可先完成

- 文献与数据库检索；
- 证据预分类；
- 活性数据抓取与预清洗；
- 化合物初步标准化与异常提示；
- baseline / GNN 探索性预跑；
- AD/UQ、ADMET、Docking 等批量执行；
- 自动生成待核验队列。

以上默认属于 `AI_PROVISIONAL`，不是正式科研事实。

### 必须进入真人核验的关键内容

- 化合物名称 / CID / SMILES / 分子式 / 立体化学；
- assay lineage、endpoint、organism、单位与关系符号；
- IC50 / Ki / EC50 是否允许合并；
- 重复实验冲突和关键异常值；
- GEO 分组与关键疾病证据；
- 关键文献原文是否真的支持结论；
- 外部验证集与泄漏风险；
- docking 关键构象与最终候选；
- candidate release。

人工核验必须记录：

```text
AI 暂定值
→ 原始来源
→ 真人判断
→ 修正值
→ 理由
→ 核验人
→ 日期
→ VERIFIED / CORRECTED / REJECTED
```

---

## 5. 数据与模型正式重算规则

人工核验不是给 AI 结果“加备注”，而是**替换错误或暂定数据，并使所有受影响下游结果失效**。

例如：

```text
AI 抓取 1200 条活性记录
→ 人工排除 endpoint 不一致、结构错误、重复冲突、物种不符等记录
→ 得到正式 Qualified Dataset
→ 此前 AI 模型全部 STALE
→ Workbench 重新执行 split / baseline / GNN / external / AD/UQ
```

正式模型比较至少包括：

- Ridge；
- Random Forest；
- XGBoost；
- GCN / GAT / MPNN 等经批准 GNN。

**最终目标不是强行让 GNN 赢。**

如果 RF / XGBoost 在严格外部验证下更可靠，则其可成为正式筛选模型；只有当 GNN 在同一冻结数据、同一 split、同一评价体系下稳定增益时，才允许进入 `RESEARCH_VALIDATED` 并承担正式筛选。

---

## 6. 当前筛选方向

正式筛选拆为两条独立轨道：

### Track A：天然产物 / 民族药

用于发现新颖化学空间与民族药 / 中药来源候选。

### Track B：老药 / 再利用

用于发现具有已知药理、安全或临床基础的再利用候选。

两条轨道分别排名，不直接把天然产物与老药混成一个榜单。

统一筛选顺序：

```text
结构身份
→ PAINS / 反应性过滤
→ 资格模型预测
→ AD
→ UQ
→ ADMET
→ 结构补强
→ 人工候选裁决
```

---

## 7. Docking / MD 的边界

- Docking 用于检查姿势、关键残基和结构合理性；
- MD 原则上只用于 3–5 个一级候选 + 阳性对照；
- 网络药理学主要用于候选后的机制解释；
- 三者均不得替代真实活性、严格外部验证或人工核验。

---

## 8. 三库关系

### AIDD 主库

完整研究档案、正式科研事实、冻结版本和最终裁决。

### GNN 库

真人科研操作、数据/结构/文献/模型核验、组员分工和任务提交。

### MASH-AIDD Workbench

AI + 真人共同使用的执行器：负责流程编排、Gate、审计、任务生成、核验结果导入、stale 传播与正式重算。

---

## 9. 当前第一优先任务

现阶段不优先重新跑大库筛选，按以下顺序推进：

1. 完成新 G0 研究问题冻结；
2. 对 FXR / ACC / THR-β / FASN 建立统一 G1 靶点资格表；
3. 选择最优 1–2 个靶点进入 G2；
4. AI 用 Workbench 完成活性数据预整理；
5. 将关键待核验项送入 GNN 库；
6. 真人核验后回填 AIDD；
7. 真人在 Workbench 中导入核验结果并冻结正式数据；
8. 重跑 Ridge / RF / XGBoost / GNN 正式 benchmark；
9. 通过 G3 后才允许启动双库正式筛选；
10. 最终形成 3–5 个一级候选和 go / no-go 结论。

---

## 10. 当前科研边界

当前**尚无经新路线完整人工核验、严格外部验证和 G0–G6 认证的抗 MASH 正式候选**。

以下内容可作为历史资产保留，但不得直接作为当前正式结论：

- 旧 Top 排名；
- 旧未知标签当阴性的分类结果；
- 未经 assay 谱系复核的活性数据；
- 旧非 scaffold-disjoint split；
- 仅凭 docking score 得到的候选排序；
- 未经人工结构身份核验的天然产物结果；
- 为展示而生成的 DEMO / exploratory 结果。

软件检查通过 ≠ 科学有效；AI 自检通过 ≠ 真人核验；模型能运行 ≠ 模型可用于正式筛选。

---

## 11. 现有入口与历史资产

- [根目录总研究章程](../README.md)
- [仓库范围与历史边界](REPO_SCOPE.md)
- [给指导老师的研究进展](给指导老师的研究进展.md)
- [分工与计划](../10-任务分配与进度/后续任务分配.md)
- [诊断数据摘要](validation/20260905/diagnostic_summary.json)
- [结构审计](validation/structure_audit/summary.json)
- [数据审核台账](data_review/README.md)
- [GNN 真人核验工作区](https://github.com/wang13236614835-cmyk/hepato-gnn-screening)
- [MASH-AIDD Workbench](https://github.com/wang13236614835-cmyk/mash-aidd-workbench)

现有诊断脚本仍保留用于历史复核和方法验证：

```text
python 00-当前研究/verify_methods.py
python 00-当前研究/run_diagnostics.py --fit-baseline --output <新目录>
python 00-当前研究/validate_docking.py --output <新目录>
```

这些脚本的输出默认不自动升级为新路线下的正式候选结论。
