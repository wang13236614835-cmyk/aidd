# GNN 方法学习审计

**审计对象：① hepato-gnn-screening 旧实现（numpy GCN，宁显泷，分类任务）；② 本轮 qualification_v1 新实现（PyTorch Geometric，回归任务）。结论先行：旧实现是"真 GNN"而非形式代码，但特征体系与 split 不达标；新实现补齐审计清单全部条目，并给出两者对比学习点。**

## 一、旧实现审计（`hepato-gnn-screening/src/models/gnn.py` + `dataset.py`）

| 审计项 | 现状 | 判定 |
|---|---|---|
| graph 构建 | 自研 SMILES→图解析器（`chem/smiles_graph.py`），原子+邻接 | ✔ 真实图，非拼接特征 |
| node feature | 13 维：元素 one-hot(10) + 芳香 + 度/6 + 氢数/4 | ⚠️ **缺陷：未知元素回退到碳槽位**（`ELEMS.index(...) else 0`）；缺形式电荷/杂化/成环 |
| edge feature | 无（仅无权邻接） | ✘ 键型/共轭/成环全部丢失 |
| message passing | `D^-1/2(A+I)D^-1/2 @ H`，对称归一化 + 自环 | ✔ 教科书式 GCN 传播 |
| aggregation | 节点均值池化 → 图级向量 | ✔ |
| batching | 逐图循环 forward/backward，full-batch 更新 | ✔（小数据可接受，无图拼接优化） |
| loss | 加权 BCE，正类权重在 {1.0,1.25,1.5} 按验证集 F1 选 | ✔（选择在验证集，未泄漏测试） |
| optimizer | 手写 Adam（含 bias correction） | ✔ 与 PyTorch 行为一致（组内已对账） |
| 反向传播 | 手推梯度，含 dropout 掩码的 backward 处理 | ✔ 组内 N 系列任务核验过 |
| overfitting 控制 | dropout 0.3 + 小网络；数据仅 88 分子 | ⚠️ 无早停/无正则曲线记录 |
| oversmoothing | 2 层，风险低；未做显式检查 | ✔（层数浅） |
| split leakage | **实测（本轮）：train/test 共享 2 个 Murcko 骨架、train/val 共享 3 个**；无相同 SMILES | ✘ **split 非 scaffold 分组**——按当前标准不达标 |
| 标签 | 旧二分类标签 = REJECTED（D05：未知当阴性/混合终点） | ✘ 输出只能 HISTORICAL |
| uncertainty | MC Dropout（T=30 前向，输出均值/方差） | ✔ 机制真实；但见下，方差质量存疑 |

**判定：不是形式代码——消息传递、手推反向、MC dropout 都是真的。** 问题在数据侧（标签废弃、split 不分组）与特征侧（无键特征、元素回退缺陷）。其全部输出维持 HISTORICAL 标注不变。

## 二、新实现审计（本轮 `run_gnn_clean_benchmark.py`）

| 审计项 | 现状 |
|---|---|
| graph | RDKit Mol→PyG Data，原子 33 维特征（元素 11、度 6、形式电荷 4、H 数 6、杂化 4、芳香、成环） |
| edge feature | GINE 变体带 6 维键特征（单/双/三/芳香、共轭、成环）；GCN 变体按定义不用 |
| message passing | GCNConv（内置归一化）/ GINEConv（可学习 ε + edge encoder） |
| aggregation | global mean pool |
| batching | 图拼接全批训练（77 图级节点一次前向） |
| loss | MSE on z-scored y（训练集统计量）——回归 |
| optimizer | Adam lr 0.01 wd 5e-4，300 epochs 固定（预注册，不因结果调参） |
| split | **与资格轮同折（断言 PASS）**：scaffold 分组 + 10 seeds + 零重叠断言 |
| uncertainty | MC dropout T=30，实测方差-|误差| Spearman 中位 GCN −0.088 / GINE +0.074 → **当前不可用**，如实记录 |

## 三、学习结论（写给组员的 GNN 方法课）

1. **GNN 增益不是免费的**：96 分子、单系列 SAR 下，参数量即劣势（Ridge 0.732 vs GCN 0.078 vs GINE −0.040）。图结构信息已被 ECFP（子结构计数）高度覆盖时，GNN 学到的增量不足以抵消方差；
2. **edge feature 不是越多越好**：GINE（带键特征）在极小样本上比 GCN 更差（过拟合面更大）；
3. **split 分组决定结论性质**：旧实现 train/test 共享骨架会把"系列内插值"包装成"泛化"；本轮同折断言是两轮结果可比的技术基础；
4. **MC dropout 不是万能 UQ**：方差与误差几乎零相关（|rho|<0.1）时必须如实废弃，不能硬当置信度用；
5. **手写实现的价值**：旧 numpy GCN 让组员理解了传播/反向/Adam 的每一步；PyG 版本用于正式对比——"教学实现"与"科研实现"分工是合理的，但科研结论只能出自后者这类可断言可比性的管道。

## 四、与门控的衔接

本审计 + [GNN_clean_benchmark_report.md](GNN_clean_benchmark_report.md) 一起构成 FASN_GNN_enable_gate 复审的"方法学习"与"模型增益"两维度输入。**门的正式状态保持关闭**（数据规模/外部校准条件未变），复审排在 Gate T1 数据工作之后。
