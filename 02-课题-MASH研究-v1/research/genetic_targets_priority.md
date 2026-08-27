# 遗传学靶点优先级(2026-08实测:GWAS Catalog Solr管道+OpenTargets v4)
## TOP10机会靶点(遗传验证+无在研药)
1. MARC1/MTARC1: p=1e-43(PMID 33310085 Emdin肝硬化meta-GWAS);OT肝硬化遗传0.818/MASLD 0.662;Structure-with-Ligand;竞争空白 -> 首选
2. TM6SF2: p=3e-83;OT 0.647/0.526;需ASO/siRNA路线;空白
3. SLC39A8: p=1e-133(PMID 32247823 MRI-cT1);细胞表面(抗体可行);空白
4. SERPINA1: p=8e-56;CIR遗传0.902(全表最高);Structure+HQ Pocket;肝表达5622TPM
5. GCKR: p=1e-9 OR=1.38;肝表达99.3TPM;变构难点
6. MBOAT7: p=1e-9 OR=1.35;膜酶结构先例
7. SUGP1: p=2e-22(PMID 34841290 UKB NAFLD);剪接因子新机制
8. FARSB: CIR遗传0.818;必需基因风险
9. SAMM50: p=2e-20 OR=2.02(儿童PMID 23535911);PROTAC方向
10. CMIP/LIPC/APOA5: 0.6-0.74
## 降权(竞争激烈)
- PNPLA3(p=2e-290): AZD2693 ASO已Ph2 -> 非空白
- HSD17B13(p=3e-54): GSK Ph2b HORIZON(NCT05583344)+Visirna+Alnylam三家 -> 极拥挤
## 技术注记
- GWAS REST findByTrait/findByEfoTrait全部失效(404/恒空);替代管道=Solr搜索→study efoTraits验证→HAL关联→SNP补映射(96 studies/797关联)
- OT v4已移除knownDrugs/expressions(改drugAndClinicalCandidates/baselineExpression);facetFilters触发500需全量拉取
- fatty liver=MONDO_0004790;MASLD=MONDO_0013209;MASH=MONDO_0007027
