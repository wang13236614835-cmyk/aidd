# 复算裁决（RERUN DECISION）

**原则：禁止为"完整"机械重跑。每项裁决给出触发条款（对应十条复算标准）、不重跑损失、重跑新增证据价值。**

## 十条复算标准（引用）

①数据实质变化 ②assay/endpoint 变化 ③去重/标准化变化 ④split 方法变化 ⑤发现 leakage ⑥模型实现实质 bug ⑦calibration/AD/UQ 不合格 ⑧外部验证不足 ⑨receptor/ligand/CCD/structure 身份修正 ⑩旧结果是论文/结题核心证据但当前资格不足。

## 逐项裁决

| # | 项目 | 裁决 | 触发条款 | 理由与损益 |
|---|---|---|---|---|
| R1 | canonical QC + 清洗集构建（96/39） | **不重跑** | 无条款触发 | 资格轮 QC 0 异常、哈希在案；重跑零新增。本轮 provenance 审计再次 PASS（0 缺失 lineage） |
| R2 | 10-seed scaffold 基线（Ridge/RF/XGB/均值） | **不重跑**（引用原数字） | 无条款触发 | 数据未变、split 未变、实现无 bug、结果已多 seed 报告。重跑只会烧算力 |
| R3 | Y-scrambling ×20 | **不重跑**（GNN 补做） | ⑦不合格？否——0/20 exceeded 已成立 | 经典模型的 scrambling 证据完整。**GNN 此前从未做过 scrambling** → 本轮对 GNN 补做（新增而非重跑） |
| R4 | 泄漏审计 | **不重跑** | 无条款触发 | 10 seed 无重复/骨架共享/复制跨集；同数据同 split 的 GNN benchmark 自动继承该审计结论（本轮脚本内置同折断言） |
| R5 | 外部验证（105 分子/3 assay） | **不重跑** | ⑧外部验证不足？——量已足、结论为阴性且冻结 | 阴性结果是有效研究结果；禁止为翻盘重跑。GNN 在同一外部集上的表现 = **新增评估**（模型维度的空白），非重跑 |
| R6 | AD/UQ（conformal） | **不重跑**（GNN 附带 MC dropout） | 无条款触发 | 内部有效/外部失效已记录。GNN benchmark 附带 MC-dropout 方差-误差 Spearman 作学习件 |
| R7 | **GNN vs 经典 baseline 同折对比** | **本轮执行**（唯一大规模复算） | ⑩——GNN 门控决定（关闭）此前**无实证**；论文若讨论"GNN 不适用"需要证据 | 此前 GNN gate 6/8 条件不满足故未训练——正确；但"当前数据上 GNN 是否有增益"从未测过。本轮以完全相同数据/split/种子补齐 GCN+GIN vs RF/XGB，无论正负都是新证据 |
| R8 | assay 效价校准（推进轮小标签校准） | **不重跑** | 无条款触发 | 10 seeds rho 稳定 0.689/0.691；cal_mean 对照在案 |
| R9 | Gate T1（多 assay 对齐数据集） | **不启动**（挂起） | ①需要新数据组装（≥15 共享分子/assay 对） | 属于下一阶段计算，不是复算；在 OPEN_ISSUES 登记。本轮不采集新外部数据（审计轮纪律） |
| R10 | docking（WT gate / redock 协议） | **不重跑** | C9 已终审（ROC 0.472） | 排序用途永久废弃；redock 协议记录在案即可 |
| R11 | Moracin N Gate M0/B0/1/2/3 | **不执行** | 外部阻塞（物料未到货） | 启动包已冻结 not_executed；到货即执行，与复算无关 |
| R12 | NP54 域间隙复检 | **不重跑** | 无条款触发 | 0/54 域内 + 桥接数据≈0 可用点 → 双重证据冻结 |
| R13 | 旧 Top-10 / 旧筛选管线（GNN 库） | **不重跑** | ⑤旧标签 REJECTED（D05）+ C9 | 数据标签废弃 + docking 排序废弃；重跑无科学价值。仅保留为 HISTORICAL |
| R14 | Workbench 平台功能 | **冒烟不重设计** | — | 只加只读 Research State/Gate 接线；跑既有 frozen smoke 作回归 |

## 净效果

本轮实际新算力 = R7（GNN benchmark：10 seed × {GCN, GIN, RF, XGB} + 20×GNN scrambling + 外部集评估，96 分子 CPU 分钟级）+ provenance/审计脚本。其余全部引用既有冻结数字。
