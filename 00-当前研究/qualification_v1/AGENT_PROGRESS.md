# Agent 执行进度（qualification_v1）

**轮次：AIDD Research Qualification v1 / 第五轮资格裁决｜Agent 会话开始 2026-09-13**

> 本文件是长任务防停检查点。任何接手的 Agent/组员读此文件即可继续，不需要会话记忆。

## 已完成（按时间序）

1. **三库审计**：aidd 主库（`D:\zcode-workspace\aidd-repo-work`，最新轮=advancement_20260913）、workbench（`D:\aidd destoop`，v0.5.2，16 页面）、GNN 库（`D:\zcode-workspace\hepato-gnn-screening`，历史标注口径已确认）。git 状态：主库 2026-09-12/13 各轮 untracked（本轮统一提交）；workbench 有未提交平台改动（分开提交）。
2. **assay provenance 审计实跑**：`audit_assay_provenance.py` → PASS（51 assay/0 缺失 lineage/96 canonical 全覆盖/外部 0 重叠）→ `derived/ASSAY_PROVENANCE.csv` + `provenance_audit.json`。
3. **冻结文档落盘**：README / RESEARCH_STATE / ASSET_AUDIT（A22 项）/ MASTER_EVIDENCE_MATRIX（E01–E21）/ QUALIFICATION_GATES（G0 PASS、G1 PASS 限 canonical、G2 PASS、G3 FAIL、G4 FAIL、G5 false）/ RERUN_DECISION（R1–R14）/ OPEN_ISSUES。
4. **GNN clean benchmark 实跑**（275.5 s）：同折断言 PASS（Ridge 中位 0.732008 逐位复现）→ GCN 0.078 / GINE −0.040 vs Ridge 0.732；Y-scrambling GCN 0/20、GINE 13/20 反超；外部 GNN 全负、Ridge ADin rho=0.880 复现；MC-dropout UQ 无效。报告 `GNN_clean_benchmark_report.md`。修复过两个 bug：PyG GINEConv 的 edge_dim 用法、scrambling 汇总聚合键名（`--summary-only` 从 CSV 重建，模型未重训）。
5. **GNN 方法学习审计**：旧 numpy GCN = 真实现但特征/split 不达标（实测 train/test 共享 2 骨架、元素回退缺陷、无键特征、标签 REJECTED）；新 PyG 实现清单全过 → `GNN_方法学习审计.md`。
6. **Workbench 接线**：新增 `D:/aidd destoop/pages/17_Research_State.py`（只读镜像，AIDD_QUALIFICATION_ROOT 可覆盖，缺失即 BLOCKED 不伪造）+ `tests/test_research_state_page.py`；AppTest 真实渲染 0 异常。
7. **全量测试**：见下表（本轮 QC PASS；两轮历史 QC 回归 PASS；workbench 113 passed）。
8. **状态同步**：`研究状态.json` 增加 batch_qualification_v1_20260913；`00-当前研究/README.md` 头部改为 qualification_v1 为当前最新。

## 当前状态

**本轮全部计划项已完成**；git 提交与最终报告见下一步。

## 下一步（按序）

1. git 提交（主库：归档此前 untracked 各轮 + 本轮 qualification_v1；workbench：新页面与测试）；
2. 输出最终执行报告（23 节格式）；
3. 交回人工事项：O1 物料采购、O2 导师签核、O5 Gate T1（下一轮计算）、O7 组员结构审核。

## 关键文件

- 本轮根目录：`00-当前研究/qualification_v1/`
- 数字来源：`qualification_round_20260913/`（Ridge/外部/AD）与 `advancement_round_20260913/`（A2/E1_ADin）
- 运行命令：`python audit_assay_provenance.py`；`python run_gnn_clean_benchmark.py [--summary-only]`；`python run_qualification_qc.py`；`python write_run_manifest.py`

## 测试结果登记（全部实跑）

| 测试 | 结果 |
|---|---|
| `audit_assay_provenance.py` | PASS（51 assay/0 缺失/0 外部重叠） |
| `run_gnn_clean_benchmark.py` | COMPLETED 275.5s；同折断言 PASS（Ridge 中位 0.732008 逐位复现）；QC 独立复算再次一致 |
| `run_qualification_qc.py`（本轮） | **PASS，0 issues**（38 资产行/21 证据行/路径全解析/0 违禁表述/ADin rho 0.8796·n14） |
| `qualification_round_20260913/run_qualification_qc.py`（回归复跑） | PASS（qc_auto.json 0 issues） |
| `advancement_round_20260913/run_advancement_qc.py`（回归复跑） | PASS（qc_auto.json 0 issues） |
| workbench pytest 全套 | **113 passed**，1 deselected（conplex 真实模型测试：Windows 页面文件不足 os error 1455，环境资源限制、与本轮改动无关、预存问题） |
| workbench Streamlit headless | `/` 与 `/17_Research_State` 均 HTTP 200 |
| 新页面 AppTest 渲染 | 0 异常；10 markdown/3 dataframe；门控与 G5=false 均渲染 |
| hepato-gnn-screening 导入冒烟 | models.{gnn,dataset,baseline} 导入 OK |
| 修复过程 | GINEConv edge_dim 用法（→GINEConv+维度规则）；scrambling 汇总键名 bug（→--summary-only 重建）；QC 路径解析器 3 轮迭代（括注/上下文/尾斜杠） |

## 未解决问题

见 [OPEN_ISSUES.md](OPEN_ISSUES.md)（O1 物料 / O2 导师签核为外部阻塞；O5 Gate T1 为下一轮计算）。
