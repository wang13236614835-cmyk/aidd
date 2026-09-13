# GitHub 项目架构调整建议

## 一、目标

将 `hepato-gnn-screening` 和 AIDD研究库改造成能体现“数据—模型—适用域—实验验证”的可复现项目，同时保留历史结果，不破坏已完成打卡和旧版本。

## 二、建议目录

```text
hepato-gnn-screening/
├── data/
│   ├── raw/                         # 原始API/文献/供应商响应
│   ├── curation/                    # 人工身份、标签、来源审核
│   ├── fasn/
│   │   ├── activity_master.csv
│   │   ├── assay_provenance.csv
│   │   ├── model_ready/
│   │   └── external_test/
│   └── natural_products/
├── src/
│   ├── curation/
│   ├── baseline/
│   ├── gnn/                         # 只有门控通过后启用
│   ├── applicability_domain/
│   ├── uncertainty/
│   └── reporting/
├── experiments/
│   ├── fasn/
│   └── moracin_n/
├── evidence/
│   ├── fasn/
│   ├── ferroptosis/
│   ├── regulatory/
│   └── provenance/
├── reports/
│   ├── final_strategy_round_20260912/
│   └── archive/
├── docs/
│   ├── data_dictionary.md
│   ├── model_cards/
│   ├── gates/
│   └── reproducibility/
└── tests/
```

## 三、不能直接迁移的历史内容

- 一般“有保肝证据/无保肝证据”的GNN标签不能当作FASN活性标签；
- 旧随机split和错误cluster split不能直接复制到正式模型；
- 旧FXR GNN和CW-BCS结果应放在archive/历史分支；
- docking输出放结构解释目录，不进入model_ready候选排序。

## 四、版本和哈希

每个模型发布包至少包含：

- 数据版本和原始API日期；
- activity/assay/document哈希；
- 清洗脚本、参数和seed；
- random/scaffold/time/external split；
- baseline比较；
- AD/UQ和拒判规则；
- 失败日志；
- model card和release note。

## 五、GitHub科学叙事

仓库首页建议只写：

> 面向MASH的可审计天然产物计算研究：FASN/de novo lipogenesis定量建模与Moracin N的NRF2-dependent ferroptosis机制验证。

不要写：

- AI发现新药；
- 54个天然产物已筛出有效药物；
- GNN一定优于RF；
- docking分数证明结合/药效。

## 六、迁移顺序

1. 先只读备份现有仓库和历史tag；
2. 添加FASN master和raw provenance，不移动旧文件；
3. 添加baseline和UQ脚本；
4. 添加Moracin N证据和实验模板；
5. 只有导师批准并且模型门控满足后才增加GNN目录内容；
6. PR中引用路径、数据日期和QC结果。
