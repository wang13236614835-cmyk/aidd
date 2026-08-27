# 第三轮圆桌 · 审稿人A（方法与统计）体检备忘录

数值抽查：正文所有覆率、Wilson CI、杠杆均值、q 值均与 results/v6/conformal_calibration.json 逐一对上，无算错。以下为表述与证据链问题（已避开 15 条既有决策）。

## 一、问题清单

**P1 摘要"Under the random splits"用复数【高｜可修】** 实际只做了一次划分（seed 42），复数让读者以为多次重采样。修：摘要与结论改单数并加"（单次划分，种子42）"。

**P2 M5 的 1.000 只在 95% 名义下成立【高｜可修】** SI 表S1 明示 80% 名义下 M5(z) 覆率仅 0.618、与 M0 持平——说明 M5 并非"恢复校准"，只是区间宽到在 95% 水平碰巧全覆盖。正文写"restores coverage completely"却只字不提 80% 反常，有挑好听数字报之嫌。修：§3.4 补一句"上述结论限于 95% 名义水平；80% 名义下 z 变体仍欠覆盖（0.618，见SI），进一步印证宽度换有效性"，Table 3 加脚注。这反而是支持论文论点的新证据，写出来是加分项。

**P3 摘要"confirming"、引言"fact"【中｜可修】** 3 个架构×1 个数据集×1 个靶点，撑不起"证实/事实"。修：confirming→consistent with；fact→observation。中文稿写"在本数据集上与架构无关的失效模式"。

**P4 §3.2 "all p<0.01"查无实据【中｜可修】** gnn_metrics_v2.json 里 RF/XGB 只存了 ρ 值（0.641/0.483），没有 p 值，这句声称目前无法溯源。修：补算三个 p 值存档并进 Table S0，或暂时只写 BGNN 的 p=0.0012。

**P5 Table 3 破折号歧义【中｜可修】** M0"—（as trained）"、M1"—（parametric inflation）"的"—"易被读成"缺失/没做"。修：改"不适用（无校准集，参数化公式）"。

**P6 "σ under-inflated out-of-domain"措辞误导【中｜可修】** 实测骨架测试集 σ 均值（约0.85）反而略大于随机划分（约0.76）；欠覆盖是误差暴增所致，不是 σ 变小。修：改"域内误差小于半宽（区间过宽），域外误差远超半宽（相对不足）"。

**P7 Fig 1 误差棒视觉陷阱【低｜可修】** 两图 1.96σ 平均半宽相近（约1.5 与 1.7 pIC50），覆率却是 100% 对 73.5%，单看图显得自相矛盾。修：图注补平均半宽与覆率，或将 |误差|>1.96σ 的点标红。

**P8 摘要"1.000"摘引风险【低｜可修】** 虽已紧跟宽度代价，但"restores coverage (1.000…)"易被单独引用。修：改"buys back 95% coverage (1.000…) only at a mean half-width of 2.98…"。

**P9 预设标准出处不明【低｜可修】** "pre-set ≥0.90 验收标准""pre-registered contract thresholds"均为组内预设，未说明在哪注册。修：注明"课题组内部预设定"。

**P10 三个"n=36"身份不同【低｜可修】** 随机测试集、骨架验证折、M5 校准集恰好都是 36，易混。修：正文加一句"两处 n=36 为不同样本"。

**P11 "unproven, not disproven"中文难直译【中｜可修】** 见第三部分第 1 条改写。

## 二、不确定项清单（须明示，附中文句式）

1. **28 例临床样本数**：目前仅 PMID 32657670 二手引用，未核原文。句式："该 28 例双盲试验的样本数与终点以原文为准（投稿前完成核对）"。
2. **RF/XGB 为存储值，v6c 复算中**。句式："随机森林与 XGBoost 指标为单次运行存储值（种子42），独立复算进行中，如有出入以复算为准"。
3. **单次随机划分**。句式："全部指标来自单次划分（种子42），未做重复划分，精度以 Wilson 区间表达"。
4. **验证集双重角色**（早停+M5 校准）。句式："骨架验证集同时承担早停与保形校准，属近似处理；主要统计一律采用仅测试集口径"。
5. **GNNExplainer 未进正文**。句式："原子归因仅作化学合理性旁证（见SI），该方法对随机种子敏感、未做稳健性检验，不构成独立证据"。
6. **p=0.26 探索性标注**：§3.6 与 Table S0 已标，一致；中文稿统一为"（探索性分析，n=10，p=0.26，不作排名依据）"。
7. **RF/XGB 骨架 p 值未存档**（即 P4）。
8. **h* 拟合于 358、终数据 354**。句式："AD 阈值按既定流程顺序，在剔除最后 4 个化合物之前拟合"。

## 三、中文化建议

**术语对照（18 个）：** scaffold split＝骨架划分；random split＝随机划分；conformal prediction＝保形预测（首选，"一致性预测"亦通行，全文统一其一并在首现处括注英文）；split conformal＝划分保形法；coverage＝覆盖率；calibration/recalibration＝校准/再校准；exchangeability＝可交换性；applicability domain (AD)＝适用域；leverage＝杠杆值；nominal level＝名义水平；under-/over-coverage＝欠覆盖/过覆盖；half-width＝区间半宽；epistemic/aleatoric uncertainty＝认知（模型）/偶然（数据）不确定性；shrinkage correction＝收缩校正；post-hoc recalibration＝事后再校准；out-of-domain/in-domain＝域外/域内；MC-dropout＝蒙特卡罗 dropout；dual-split audit＝双划分审计。

**三处直译会别扭的英文及改写：**
1. "unproven, not disproven"：直译"未被证明也未被证伪"绕口。改："证据不足以下结论——既不能说域外不确定性有效，也不能说它失效"。
2. "the scaffold shift is invisible to descriptor-space leverage"：直译"骨架位移对杠杆不可见"费解。改："骨架层面的新颖性在描述符空间的杠杆值上不留任何痕迹，现有检测手段看不见它"。
3. "statistical validity is purchasable only by forfeiting prioritization resolution"：直译"统计有效性只能靠放弃分辨率购买"。改："要换来统计上有效的区间，代价是筛选分辨率近乎报废"。另附一处："we operationalize disclosure instead of repair"直译"把披露操作化"→改"与其事后修复，不如把适用域风险做成流程、明示于人"。
