# 未解决项与外部阻塞（OPEN ISSUES）

**分级：P0=影响科研事实/数据安全｜P1=影响资格链完整性｜P2=体验/后续。**

## 外部阻塞（非 Agent 可解）

| # | 项 | 状态 | 等级 |
|---|---|---|---|
| O1 | Moracin N 物料未到货（无 COA/批号） | 等导师批准 + GlpBio(¥520)/MCE 试用装下单；到货即执行 M0 六项 | P0 |
| O2 | 导师对双轴战略冻结包 + 资格裁决的签核 | `teacher_approval = not_recorded` | P0 |
| O3 | CNIPA(412)/Google Patents(503)/CNKI(登录墙) 检索边界 | 新颖性/专利面检索不完整，登记不扩大 | P1 |
| O4 | BindingDB SMILES 端点 404 | UniProt 通道可用；SMILES 直查不可用 | P2 |

## 待决计算/数据项

| # | 项 | 依赖 | 等级 |
|---|---|---|---|
| O5 | Gate T1：多 assay 对齐数据集（≥15 共享分子/assay 对→assay 间变换→归一化重跑） | 需要从 master 51 assay 中做共享分子对组装（新计算，非复算）；失败则 FASN 降级方法学线 | P1 |
| O6 | GNN benchmark 结论并入 FASN_GNN_enable_gate 复审 | 本轮 benchmark 完成后触发（按门控条款逐条复审，不因单一 benchmark 翻转） | P1 |
| O7 | GNN 库 100 条结构修订的逐条人工身份审核 | 组员任务（VERIFY_TASKS）；不可自动签名 | P1 |
| O8 | FASN 外部校准新数据源（T1 之外的路） | 若 T1 不可行，需要锁定新的可对齐外部校准集 | P2 |
| O9 | ADMET-AI 全量候选 profiling | 未运行（第五轮登记）；当前无放行候选，优先级低 | P2 |

## 本轮已知限制（诚实披露）

- L1：本轮不采集新外部数据（审计轮纪律），T1 所需的 assay 对组装留给下一轮；
- L2：GNN benchmark 为 CPU 小规模训练（96 分子），结论限定"当前数据规模与问题定义下"，不代表更大数据上的上界；
- L3：三库 git 状态：主库 2026-09-12/13 各轮此前未提交（本轮统一归档提交）；workbench 存在未提交的平台修改（v0.5.2 发布线），本轮只追加只读页面并分开提交；
- L4：旧 Top-10 等历史标注依赖 GNN 库 PROJECT_STATUS.md 的既有口径，本轮抽查一致，未逐文件重扫（HISTORICAL 类不投入复核资源）。

## 2026-09-22 路径断链修复登记（W3 计划任务，已完成）

- **问题**：GNN 库（hepato-gnn-screening）19 处引用不存在的权威状态路径 `qualification_v1/研究状态.md`，实际文件为 `qualification_v1/RESEARCH_STATE.md`（v2 方案 §1 第 7 行登记项）。
- **修复范围**：`状态.json`（authority 字段）、`README.md`、`docs/全员工作台导航.md`、`tools/gen_member_pages.py`（action_path + source）、`tools/patch_leader_template.py`（CHAIN 模板×2 + CTX source）、5 份成员打卡 HTML（RESEARCH_CHAIN 内嵌 JS×2/份 + 王启龙 currentContext×1）。
- **验证**：修复后零残留（全库扫描）；`状态.json` 合法 JSON；两 tools 脚本 py_compile 通过；`pytest tests/test_workbench_contract.py` 4 passed；5 份 HTML 内嵌 JS `node --check` 通过；`node tools/test_checkin_contract.cjs` 95 项通过（原件 tab 结构、旧存储键、确认弹窗均未破坏）。
- **版本账**：5 份打卡 HTML 是 research_chain_v2_20260921/来源快照.json 的哈希对象，按"只追加版本"规则在快照 `revisions[0]` 登记前后哈希，`verify_plan.py` 已升级为按最新版本校验。修复不改变任何科研裁决（candidate_release=false、GNN gate=closed、T1=FAIL 维持）。

## 2026-09-22 研究链路 v2 采纳与三库任务同步登记（已完成）

- **决策**：负责人采纳 `research_chain_v2_20260921` 为学期执行方案；导师终审 not_recorded（待补，不阻塞线 A 执行但阻塞正式发布类动作）。
- **工时模型（用户拍板）**：组员 4h/周（任务 2.5h＋学习 1.5h）；王启龙 6–8h/周（本线 4–5h＋辅助组员 1–2h＋学习 1h，辅助记 hepato 库工作台台账）；W4 轻量周减半。
- **同步范围**：hepato 五份打卡页（W3–W16 任务/里程碑/研究链/角色/工时换新；界面、DOM id、存储键、W1/W2 历史卡、已有勾选不动）＋五份工作台.md＋研究状态.md＋状态.json＋导航/README；v2 侧计划数据.json＋周计划 CSV＋六份 HTML 内嵌＋来源快照 revisions[2]。
- **验证**：hepato 契约 95 项＋pytest 4 项通过；v2 verify_plan 159/159 通过；生成脚本 `hepato-gnn-screening/tools/sync_v2_to_pages.py` 留档可重跑。
- **Gate 不变**：G2=HUMAN_REVIEW_REQUIRED、G3=BLOCKED、candidate_release=false、gnn_enable_gate=closed、FASN T1=FAIL、real_human_review=0。


## 2026-09-22 任务载体五点修订登记（已完成）

- **要求**：①任务载体不出现"周五组会"（节奏统一为周日进度汇总）；②不提导师（界面与任务文本改"负责人"）；③W3 聚焦本周 Phase 2B 第一批 11 项，主做条目对应具体文件；④每条任务明确目标/注意/工具/流程，描述简洁；⑤全中文。
- **范围**：hepato 五份打卡页（模板静态文案+周卡+我的工作台）与五份工作台.md；v2 计划数据.json 19 处任务文本净化（六 HTML 内嵌与周计划 CSV 同步重建）。完整研究链路_v2.md 等方案档案为 9/21 历史文档，保留原文。
- **验证**：checkin 契约 95 项、pytest 4 项、五页 JS、Workbench 投影 8 项、verify_plan 159/159 全过；禁词扫描零残留。
- **不变式**：Gate 全部维持；工时模型不变（组员 4h/周；负责人 6–8h/周含辅助组员 1–2h）。


## 2026-09-22 核验文件直达部署与载体精简登记（已完成）

- **直达部署**：五份打卡页"我的工作台"新增五个核验文件直通链接（核验首页 index.html、任务总表.csv、回填表模板、核验填写说明、第一批任务书），行动卡改指核验首页；五份工作台加"文件直达"表（①–⑤顺序）。核验首页本身每条任务已带 ChEMBL 原始数据链接。
- **精简**：任务载体去除预算类表述（同折同条件、超参设置、必要性决定等中性替换；v2 计划数据 15 字段同步净化，六 HTML 与 CSV 重建）；主线在工作台压缩为一句话。
- **说明三节**：工作台新增"新旧文件说明"（更新了什么/保留了什么/新在哪）、"工作台怎么用"（每天/每条/每周日三句话）、"下发流程"（任务已写入各人页面、群发三入口、每周更新节奏、回填收件）。
- **验证**：checkin 95、pytest 4、投影 8、verify_plan 159/159、五页 JS、直达目标文件存在性、禁词（导师/组会/预算）零残留。Gate 与工时模型不变。