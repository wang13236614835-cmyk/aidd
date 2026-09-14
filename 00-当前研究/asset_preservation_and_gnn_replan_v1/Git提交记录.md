# Git 提交记录

## 本轮计划

- AIDD 主库：独立新增 preservation/replan 目录、状态同步和 QC；不 squash 既有提交；不删除历史。
- GNN 库：只提交 README/状态/计划/索引等本轮明确新增或修正文件；保留既有未跟踪打卡说明，不代为纳入。
- Workbench：若需修改，只提交本轮与状态镜像有关的文件；当前 v0.5.2 既有未提交修改不触碰。

## 实际提交

- AIDD 主库：`62201b7`（主体）+ `4708ce6`（提交记录）+ `075dc1f`（registry/manifest）+ `f96ea65`（最终交接报告）+ `e4480a2`（报告后最终 registry/manifest）。
- GNN 库：`71a1885`（README/RESEARCH_STATE/STATUS/计划/审计/状态表、legacy-demo 文案、空 CSV 修复、软件检查结果）；之后已有 `19d518d` W1 打卡归档提交，本轮不改动。
- Workbench：`8fb6042`（17 Research State 页机器状态/registry 摘要、页面测试、frozen smoke 路由）；之后已有 `e9b2bdf` 科研加固/中文化提交，本轮不改动；发布线仍有未提交修改。


## 提交前要求

每个仓库分别运行 `git status`、相关测试、hash/manifest 检查，再按仓库独立 commit。若仓库已有非本轮修改，最终报告列出并保持原样。上述三笔提交已完成；本文件若随后更新，仅作为 AIDD 交接文档的补充，不改变其他仓库提交边界。
