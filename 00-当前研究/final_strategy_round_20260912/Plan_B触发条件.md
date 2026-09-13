# Plan B 触发条件

## 一、Plan B 的含义

本最终架构中，Plan B不是另一个同时铺开的主线，而是：

> 当FASN长期主AIDD资格赛或Moracin N近期功能轴出现预注册停止信号时，如何切换到仍然可复用、可验证的路径。

## 二、FASN轴的停止/切换条件

### 停止天然产物预测

- provenance审核后没有可解释的同质assay；
- canonical/assay-family数据在scaffold、time和external test中不稳定；
- 模型不优于均值/简单描述符，或UQ不能识别域外；
- 54库全部OOD且没有可追溯Tier 2扩展库；
- 直接酶阳性参照无法复现。

这时不能用更多GNN、更多docking或人工总分掩盖失败。

### FASN轴保留为方法学结果

即使模型失败，仍可形成：

- FASN数据provenance审计；
- relation/censor和assay异质性分析；
- scaffold/time外推失败；
- 天然产物OOD拒判案例；
- “为何不能把公开activity直接用于天然产物总榜”的方法报告。

## 三、Moracin N轴的停止/切换条件

- Gate 0无法排除关键光学、聚集、溶解或探针干扰；
- Gate 1无毒窗口内无TG/脂滴改善；
- Gate 2无至少两个机制读出改善；
- Gate 3 ML385削减率<30%，且正交Nrf2干预不支持；
- 材料供应在合理期限内无法获得或COA不合格。

不同失败分别记录为：材料不可行、本模型未获支持、机制主张失败或候选停止。

## 四、切换后的优先顺序

### 情形A：FASN模型通过，Moracin N失败

保留FASN为唯一计算主轴，进入Tier 2天然产物库和直接FASN酶实验；不因为Moracin N失败而放弃FASN。

### 情形B：FASN模型失败，Moracin N通过

以Moracin N机制重定位为主要科学结果，FASN数据审计作为方法学或附录，不硬做GNN。

### 情形C：两条轴都失败

优先评估THRβ single-protein IC50 ligand model或现成reporter实验；若数据/平台仍不满足，保留阴性结果并停止扩大项目，不自动跳回docking。

### 情形D：Moracin N材料失败但FASN仍未准备好

先按预注册启动isorhamnetin干扰门（仅书面备选）；不把3'-methoxydaidzein作为替补。

## 五、切换的客观记录

每次切换必须记录：

- 触发的预注册条件；
- 直接数据路径；
- 是材料、模型、实验还是机制失败；
- 复用哪些资产；
- 新预算、时间和停止线；
- 是否改变课题题目和论文范围。

不以“某路线更热门”“已经投入很多”作为切换理由。
