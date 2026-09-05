# 当前MASH研究主入口

**王启龙带队；干实验优先；暂无湿实验材料。**

[给指导老师的研究进展](给指导老师的研究进展.md) · [分工与计划](../10-任务分配与进度/后续任务分配.md) · [诊断数据摘要](validation/20260905/diagnostic_summary.json) · [结构审计](validation/structure_audit/summary.json) · [数据审核台账](data_review/README.md)

当前代码：`src/methods.py`修正数值方法；`run_diagnostics.py`只读历史输入并写新的诊断目录；`validate_docking.py`进行CCD修复与独立初始构象复算，复用历史受体因此仍需受体审核。

```text
python 00-当前研究/verify_methods.py
python 00-当前研究/run_diagnostics.py --fit-baseline --output <新目录>
# 先设置VINA_BIN，以下只做结构方法诊断
python 00-当前研究/validate_docking.py --output <新目录>
```

默认不产生新正式候选榜。正式数据、模型、对接门槛未过；旧标签仍需assay谱系复核。依赖版本见requirements-validated.txt。全部历史研究在01–09类保留，新正式工作在此形成可审阅版本，打卡在GNN库。
