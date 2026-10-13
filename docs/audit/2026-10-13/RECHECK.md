# 2026-10-13 来源与计算入口复核

| 问题 | 结论 | 依据 | 修正 |
|---|---|---|---|
| GEO元数据与计划主/验证队列混淆 | 需来源分离 | GEO官方GSE135251为216例RNA-seq，GSE89632为63例芯片 | 公共来源目录，旧调研文档增加更正；不移植logFC |
| Resmetirom/小檗碱终点错配 | 不允许以药名或报告响应代替直接靶点证据 | FDA标签、PMID32292349、PMID24166454 | 同步药物靶点与assay限定目录，直接结合EC50保持空 |
| 活跃hepato镜像NaN融合排序 | 成立 | 原_score_rows未有限数检查 | 拒绝非有限总分/非法方差；非有限对接视缺测，tie按ID稳定序列化 |
| 镜像旧mock产物与发布入口 | 需限制演示用途 | 旧mock及融合源码 | 仅显式DEMO、独立demo目录；历史融合入口停用 |
| Vina路径可移植性 | 不应依赖捆绑本机exe | common.VINA旧fallback | PATH或显式VINA_BIN；未知可执行版本不授科学资格 |
| 历史MASH v2算法问题 | 当前入口已有隔离/修正，不重新启用 | 历史脚本入口RuntimeError；00-当前研究/src/methods.py | 保留历史，原5项方法检验通过；新增镜像5项回归通过 |

修改只针对计算入口与来源事实；未重做真实模型、对接或湿实验，未授候选发布资格。

公开依据：

- https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE89632
- https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE135251
- https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/217785s000lbl.pdf
- https://pubmed.ncbi.nlm.nih.gov/32292349/
- https://pubmed.ncbi.nlm.nih.gov/24166454/
- https://vina.scripps.edu/license/
