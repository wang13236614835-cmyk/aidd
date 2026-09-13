# 采购公开核查阻断记录（2026-09-10）

## 事实
- Week 1要求核查Sigma/MCE/TargetMol/Selleck/Cayman/APExBIO等公开产品页。
- 自动公开检索遇到Google异常流量验证；部分供应商页返回403/412、地区/登录限制。
- 本轮未保存未经核验的货号、价格、库存、纯度或CoA；没有采购、下单或对外联系。

## 影响
- `priority_compounds_identity_audit.csv`中的supplier_status为`BLOCKED_PUBLIC_LOOKUP`。
- PubChem/CID/结构身份已完成，但这不能代替标准品批次/纯度/盐型/CoA核验。
- 在采购人工核查前，不允许把任一候选标为“可实验放行”。

## 人工核查清单
对每个重点分子至少记录3家供应商：URL、访问日期、货号、CAS、HPLC/LC-MS纯度、分子式、分子量、母体/盐型、水合物、储存条件、公开溶解性、批号/CoA、库存/交期和价格。

## 风险控制
- 3'-methoxydaidzein必须核对B环3'-OMe/4'-OH、A环7-OH，不能按名称替代。
- Alisol B与AB23A等衍生物不能混购或混写。
- Puerarin、hyperoside、isoquercitrin等糖苷需要核对立体化学和糖基连接。
