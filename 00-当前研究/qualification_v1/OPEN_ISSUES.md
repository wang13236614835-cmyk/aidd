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
