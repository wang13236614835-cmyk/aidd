# DockScope ADMET-AI 端点不可用记录（2026-09-09）

- 现象：分子准入批次 screen_20260909_181513_1f8a12b1 全部 13 条 admet_status=error
- 原因（admet_model_manifest.json）：`ModuleNotFoundError: No module named 'admet_ai'`——DockScopeLicensed 后端打包不完整（存在 admet_ai-2.0.1.dist-info 但缺实际模块）
- 影响：10 个端点（AMES、BBB_Martins、Bioavailability_Ma、ClinTox、DILI、HIA_Hou、Pgp_Broccatelli、hERG、Cacao2_Wang、Solubility_AqSolDB）无法在平台内预测
- 处置：ADMET 端点预测列为待完成（平台外：ADMET-AI 官方网页版或本地替代），不阻塞其他证据链
- 已正常完成：PAINS（正式规则集）、Brenk、QED、Ro5、Veber、SA score——结果见 dockscope_admission_results.csv
