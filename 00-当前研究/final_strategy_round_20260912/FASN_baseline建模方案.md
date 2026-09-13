# FASN baseline 建模方案

## 一、当前模型状态

**状态：baseline 已实际运行；模型未达到天然产物候选释放条件。**

运行脚本：`run_fasn_canonical_multiseed.py`。输出：

- `derived/FASN_canonical_multiseed_summary.json`
- `derived/FASN_canonical_multiseed_metrics.csv`
- `derived/FASN_canonical_multiseed_predictions.csv`
- `derived/FASN_canonical_multiseed_summary.json`

## 二、主开发集

选择单一 canonical assay `CHEMBL5731051`：

- 97 条精确 nM IC50记录；
- 96 个分子；
- 39 个 Murcko scaffold；
- 1 个分子有同 assay 重复记录，取分子内中位数；
- 目标为人源 FASN，但 assay描述、底物条件和检测方式仍需人工复核。

`CHEMBL5734379`虽然同为SPA格式，但与主 assay共享89个分子、数值高度镜像，不能当作独立外部验证。

## 三、特征和模型顺序

### Baseline 0：均值/中位数

用途：确定机器学习是否超过简单预测。不能把“超过均值”写成已具备外部泛化。

### Baseline 1：理化描述符 RF

使用MW、logP、TPSA、HBD、HBA、rotatable bonds、ring count、aromatic rings、fraction CSP3、heavy atom count。

### Baseline 2：ECFP/Morgan + RF

radius=2，2048 bits；报告随机和scaffold split。

### Baseline 3：ECFP/Morgan + XGBoost

仅在前面基线完成后运行；参数与seed全部记录，不删失败结果。

### 辅助线：ECFP Ridge

本轮小样本结果中 Ridge 在scaffold split表现优于树模型，必须保留；不能为了强调“非线性AI”而删除。

## 四、实际结果

### 五种子随机 split 的中位数

| 模型 | MAE | RMSE | R² | Spearman |
|---|---:|---:|---:|---:|
| 均值 | 0.518 | 0.654 | −0.047 | 不适用 |
| 描述符RF | 0.382 | 0.477 | 0.440 | 0.660 |
| ECFP-RF | 0.407 | 0.510 | 0.394 | 0.765 |
| ECFP-Ridge | 0.252 | 0.345 | 0.722 | 0.882 |
| ECFP-XGBoost | 0.254 | 0.351 | 0.729 | 0.908 |

### 五种子 scaffold split 的中位数

| 模型 | MAE | RMSE | R² | Spearman |
|---|---:|---:|---:|---:|
| 均值 | 0.579 | 0.705 | −0.016 | 不适用 |
| 描述符RF | 0.451 | 0.567 | 0.490 | 0.516 |
| ECFP-RF | 0.450 | 0.549 | 0.336 | 0.583 |
| ECFP-Ridge | 0.261 | 0.307 | 0.736 | 0.844 |
| ECFP-XGBoost | 0.331 | 0.448 | 0.626 | 0.755 |

这些是单一 assay、小样本、内部 scaffold 分组结果，不能写成外部泛化。

### 时间敏感性

在较宽的 full-length-stated数据中，以分子最早记录年份作时间切分：2017训练133个分子，2018–2019测试75个分子。结果：

- 均值 R² −0.231；
- ECFP-RF R² −0.061，Spearman 0.226；
- ECFP-XGBoost R² −0.423，Spearman 0.251。

该分析存在 assay-family异质性，因此是敏感性而非正式外部验证；它仍然足以阻止“随机split表现好所以可直接预测天然产物”的表述。

## 五、模型资格判据

FASN长期主轴要进入天然产物预测，必须同时满足：

1. primary assay provenance经人工核对；
2. scaffold split多种子不接近均值，且不由单一随机seed支撑；
3. time split或文献外部集不出现系统性失败，或失败原因已被明确限制；
4. UQ/AD能识别域外样本；
5. 至少一个 assay 外的独立正交数据集可作为真正验证；
6. ECFP-RF/XGB/Ridge与简单基线比较完整；
7. 结果不依赖人工综合评分；
8. 天然产物预测仅对在域样本释放，OOD样本拒判。

## 六、当前是否放行

- **数据资格：有条件通过。** 记录数量和字段足以继续数据工程。
- **可学习性：初步支持。** canonical assay内部scaffold split显示结构信号，但模型差异大。
- **适用域：不通过天然产物释放。** 54个天然产物到canonical训练集最大Tanimoto中位约0.136、最高约0.171。
- **外部验证：未完成。** 镜像SPA assay不算外部验证，真正时间/文献外部集未锁定。
- **GNN：不启用。** 当前不满足“基线稳定+外部验证+深度模型增量”条件。

## 七、后续实验与模型关系

模型不能替代直接酶实验。后续采用：

1. 先锁定FASN数据和外部test；
2. 再输出带AD/UQ的候选假说；
3. 先测阳性参照和化学型阴性对照；
4. 再测天然产物FASN酶抑制和肝细胞DNL/TG；
5. 酶阳性、细胞阳性、二者不一致均分别记录。
