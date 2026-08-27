# 课题组合作讨论 · 决策纪要（2026-08-23）

> 参与者：方法学与统计负责人（m1/r1）、药学与中药学应用负责人（m2/r2）、数据完整性与验证负责人（m3/r3）；执笔：组长（主持agent）。
> 输入：三份独立备忘录 + 三份交叉回应 + B2 真实校准结果（results/v6/conformal_calibration.json，v6/v6b 两脚本可复现，复现校验 μ Pearson=0.9997）。
> 目标：SCI 论文（ACS Omega 定位）全部争议点收敛。

## 一、B2 校准结果的定论（全组一致）

**核心叙事：外推失效不可事后修复，只能事前披露。**
- 域内校准集（随机测试集 n=36）→ 骨架测试集（n=34）评估 95% 覆率：M0 原始 σ=0.735 [0.569, 0.854]、M1 杠杆膨胀=0.765 [0.600, 0.876]（最优）、M2 平坦 conformal=0.706、M3 自适应 z=0.647、M4 杠杆加权=0.618——全部显著欠覆。
- 根因（双重）：①可交换性在骨架位移下破坏；②位移对杠杆 AD 不可见（骨架测试集杠杆均值 0.0096 **低于**校准集 0.0126，两组 0% 越 h_crit=0.0503）。
- 同域校准（骨架 val n=36 真实推理，val R²=0.153）：M5 平坦 conformal 覆率 1.000 [0.899, 1.0]（达标 ≥0.90）但半宽 2.983 pIC50 ≈ 数据全域（3.38–9.96），筛选分辨率归零。
- 结论：双划分协议 + 三级标注 = 经校准分析验证的必要筛选纪律（不再是"待改进项"）。

## 二、论文决策清单

| # | 议题 | 决策 | 依据 |
|---|---|---|---|
| D1 | 标题 | "When random splits mislead: quantifying scaffold-level extrapolation collapse and the limits of post-hoc uncertainty recalibration in Bayesian graph neural network screening of natural products" | r1+r2：删"hepatoprotective herbs"（功效声称过强）、"recalibration"加"limits of"限定 |
| D2 | 期刊 | ACS Omega 首选（篇幅容纳统计主线），BBRC 备选 | r1 |
| D3 | 校准主表 | M0/M1/M2/M5 最小集，**覆率必须与半宽同报**+Wilson CI+口径标签；M3/M4 进 SI 作负结果 | r1 底线+r3 底线 |
| D4 | σ-err 口径 | 正文 test-only（random +0.585 p=1.8e-4；scaffold +0.269 p=0.124），pooled（0.340/-0.027）入附注并解释早停致乐观 | r1 |
| D5 | scaffold σ 措辞上限 | "欠校准/未证 falsified"——不得写"有效"也不得写"完全失效" | r1 |
| D6 | KEGG ORA | 降级为名义富集（hsa04976 名义 p=8.6e-4，padj=0.28），不进摘要 | r1+r3(问题C) |
| D7 | 交叉对接 | "方向一致（探索性，n=10，p=0.26）"，不进排名权重，候选行可信度不引用对接 | r1+r2(问题D) |
| D8 | 三级标注应用 | w=1/(1+σ) 只承诺域内有效；域外成员按杠杆 AD 事前门控 + tier 硬降权（不采用 σ 连续降权——域外 σ 可能虚小） | r2 底线 |
| D9 | 候选证据表 | 7 行定版：樟芝 antcin K/antrodin B/Antrocinnamomin F（物种级临床证据，PMID 32657670）、积雪草 asiatic acid（直接文献 PMID 35963324，注无计算分）、黄连 Epiberberine（纯计算高置信代表）、小檗碱（阳性对照锚）、甘草 Derrone、白花蛇舌草 Anthraxin、07H239-A（计算对照，PMID 15387660）；水飞蓟宾以脚注作 OOD 预范例。列=条目｜证据等级｜模型tier｜实证可购性｜锚点 | r2 |
| D10 | THRβ 正分条目（问题E） | 脚注+标记，不剔除（删除=事后删数据；4 条均为底部条目，CW-BCS 已有 eps 兜底） | r2 |
| D11 | 问题A（tcm库覆盖事件） | 方案(c)：131 化合物 CID 锚定表为证据基线；择机重跑 step4 重建 224 provenance 并以 131/131 CID 反核对——通过则 224 可用，不通过则弃用 224 表述；SI 如实记录事件 | r3 |
| D12 | 数字-来源对照表 | 进 SI 作 Table S0 | r3 |
| D13 | 收缩表述 | "robust to shrinkage" 仅指第一梯队身份保持，不主张 2-4 名次序稳定 | r1 |
| D14 | 语义边界 | 摘要/讨论前置：CW-BCS 为 panel-conditional 结合覆盖倾向、非药理协同；全文禁功效声称 | r2 底线 |
| D15 | 80% 覆率键名 | v6 JSON alpha_020 节键名 coverage95→coverage80 已更正，重跑复核 | r3 发现 |

## 三、分工

- 方法学（r1 持有人）：Methods 2.4/2.5、Results 3.3/3.4、Discussion 主线段——执笔由组长按本纪要落实。
- 药学（r2 持有人）：Results 3.5-3.7、候选表、边界句。
- 数据（r3 持有人）：Table S0 骨架、数据可用性声明、问题A重建、全部数字终审。
- 组长（执笔）：英文全稿、图 1-4（全部从已验证数据重新生成）、排版 PDF、中文导读。

## 四、遗留事项

1. step4 重跑（后台执行中）：成功且 131/131 CID 反核对通过 → SI 记"provenance rebuilt"；失败 → 论文只写 131 CID 锚定表。
2. 投稿前需人工完成：作者名单补全、单位邮箱、经费号、Reviewer 建议名单。
3. 湿实验（C1）与 v2 补骨架划分（C3）不在本稿范围，写入 Discussion/Future work。
