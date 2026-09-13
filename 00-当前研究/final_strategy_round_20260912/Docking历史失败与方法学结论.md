# Docking 历史失败与方法学结论

## 一、硬事实

### TRβ旧体系

- 2J4A为N331S工程突变体；旧discrimination gate ROC-AUC 0.346；
- 旧报告中的MW残差方向曾被反转，不能以0.647作为“校正后改善”；
- 2J4A上的姿态恢复不代表野生型TRβ活性预测。

### TRβ WT体系

- 3GWS-derived WT TRβ；T3/GC-1姿态可近似重现；
- WT discrimination gate：ROC-AUC 0.472；95% CI 0.341–0.607；
- PR-AUC 0.693，仅略高于阳性率基线；分层AUC 0.596/0.232/0.587，方向不一致；
- 因此不能从Vina分数推断活性、激动/拮抗或TRβ/TRα选择性。

### FASN体系

- 历史7MHD/ZEP参考存在化学身份警示；
- 2026年固定盒多seed位点基本正确，但4个协议seed中仅1个在2 Å门槛下通过；最佳姿态约1.63–2.09 Å；
- “dual-basin/双盆地”说法已撤回，只保留连续构象梯度和分辨率不足解释；
- 54×FASN docking的Moracin N第一名是协议内相对分数，不是酶抑制证据。

## 二、可以保留的科学价值

Docking仍可承担：

- pose hypothesis；
- binding-site interpretation；
- structure visualization；
- 已知共晶姿态重现的技术说明；
- 实验阳性/阴性之后的结构解释。

## 三、永久停止的用法

- 候选总榜；
- “分数更低所以更可能有效”；
- 亲和力、IC50、EC50、Kd预测；
- 激动/拮抗方向；
- TRβ/TRα选择性排序；
- 通过换受体、盒子、打分函数或seed反复寻找“翻案”结果；
- 用姿态恢复通过掩盖区分能力失败。

## 四、为什么这不是项目失败

本轮排除的是一种证据链：天然产物→Vina分数→候选活性。它没有排除：

- FASN ligand-based QSAR的可能性；
- Moracin N的Nrf2/ferroptosis机制验证；
- THRβ的独立reporter实验；
- FXR的机制锚点价值。

这使项目从不可证伪的分数排序，转为可审计的数据模型和功能实验。

## 五、统一方法学结论

> docking在本项目中是结构解释工具，而不是候选活性排序器。任何后续模型或实验都必须独立于Vina分数，并报告assay、split、AD、UQ和直接功能读出。
