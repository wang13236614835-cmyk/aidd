# When random splits mislead: quantifying scaffold-level extrapolation collapse and the limits of post-hoc uncertainty recalibration in Bayesian graph neural network screening of natural products

**Qilong Wang, [Additional team members], Xiwei Jiang\***

School of Medical Devices, Shenyang Pharmaceutical University, Shenyang, Liaoning, China

\*Corresponding author: Xiwei Jiang ([email to be completed at submission])

**Keywords:** uncertainty quantification; scaffold split; conformal prediction; natural products; graph neural networks; virtual screening; FXR; applicability domain

---

## Abstract

Machine-learning virtual screening of natural products routinely reports strong validation metrics while silently assuming that test molecules resemble training molecules. We audit this assumption with a dual-split protocol applied to a Bayesian graph neural network (GNN) trained on 354 curated farnesoid X receptor (FXR) agonists from ChEMBL. Under a single random split of the kind used in most studies (seed 42), the model attains R² = 0.790, RMSE = 0.723, and Spearman ρ = 0.768 (n = 36); under Bemis–Murcko scaffold splits that mimic genuine screening of novel chemotypes, the same architecture collapses to R² = −0.610, and fingerprint baselines collapse equally (RF 0.047, XGBoost −0.127), consistent with an extrinsic, architecture-independent failure mode on this dataset. Predictive uncertainty is informative in-domain (test-only Spearman(σ, |error|) = +0.585, p = 1.8 × 10⁻⁴) but unproven out-of-domain (+0.269, p = 0.124), and nominal 95% intervals undercover on scaffold-held-out compounds (0.735; Wilson 95% CI 0.569–0.854). Post-hoc recalibration from in-domain data—leverage-inflated σ and split-conformal variants (coverage 0.618–0.765)—cannot restore nominal coverage because the scaffold shift is invisible to descriptor-space leverage (mean test leverage 0.0096 vs 0.0126 in-domain; 0% beyond the applicability-domain threshold). Scaffold-matched conformal calibration buys back nominal 95% coverage (1.000; CI 0.899–1.000) but only at a mean half-width of 2.98 pIC₅₀ units—the resulting interval width (5.96 units) spans 91% of the dataset's full range (6.58 units)—i.e., statistical validity is recoverable only by forfeiting prioritization resolution. We therefore operationalize disclosure instead of repair: a three-tier applicability annotation (72 in-domain high-confidence, 32 in-domain low-confidence, 27 out-of-domain warning among 131 herbal natural products) and a confidence-weighted, shrinkage-corrected multi-target coverage score rank ten herbs traditionally used for hepatoprotection, with Coptis chinensis, Sophora flavescens, Glycyrrhiza uralensis, and Salvia miltiorrhiza forming a shrinkage-robust leading tier. The dual-split audit, calibration experiments, and tiered annotation are fully scripted against public data (GEO GSE135251; ChEMBL CHEMBL2047; PubChem; RCSB PDB; KEGG).

---

## 1. Introduction

Metabolic dysfunction-associated steatohepatitis (MASH) remains one of the largest unmet pharmacological needs in hepatology. The 2024 approval of the thyroid hormone receptor-β agonist resmetirom was a milestone, yet monotherapy limitations—ongoing trial attrition for FXR agonists and the modest effect sizes of single-axis agents—sustain interest in multi-target, weakly coordinated modulation by natural products. Computational prioritization is attractive because it is cheap, but it inherits a structural weakness: public bioactivity databases are dominated by synthetic medicinal-chemistry scaffolds, whereas natural products occupy a markedly different chemical space.

Two failure modes follow. First, point-estimate models (QSAR, fingerprint regressors, graph neural networks) are typically validated with random splits, which preserve the exchangeability between training and test sets that real screening of novel chemotypes violates; reported metrics therefore overstate prospective performance. Second, uncertainty quantification (UQ) methods—MC-dropout Bayesian approximations, deep ensembles—promise to flag unreliable predictions, but their calibration is itself usually assessed on the same exchangeable data, leaving their behavior under genuine extrapolation undocumented.

This study asks a deliberately simple question: **when a Bayesian GNN is audited under scaffold-level extrapolation, what survives—and can post-hoc recalibration repair what does not?** We deliver four contributions: (i) a dual-split audit that turns the "natural products over-extrapolate" concern into a measured, architecture-independent observation; (ii) an honest decomposition of predictive-uncertainty behavior in- vs out-of-domain, reported under explicit caliber labels (test-only vs pooled) with Wilson intervals; (iii) a systematic negative result: post-hoc recalibration from in-domain data cannot restore nominal coverage, because the scaffold shift is invisible to the descriptor-space leverage that would drive such corrections—and scaffold-matched conformal calibration restores coverage only at interval widths that destroy prioritization resolution; (iv) an operational screening discipline (three-tier applicability annotation plus a confidence-weighted, shrinkage-corrected multi-target coverage score, CW-BCS) that converts these findings into a defensible prioritization of ten herbs traditionally used for hepatoprotection and nine evidence-graded candidate compounds.

## 2. Methods

All analyses are scripted in Python and executed on a single desktop CPU; every number in this manuscript traces to a versioned result file (Supporting Information Table S0).

### 2.1 Pathological target validation (public transcriptomics)

MASH liver transcriptome data GSE135251 (RNA-seq, n = 216 liver biopsies: 10 normal, 51 NAFL, 155 NASH, with fibrosis staging) were obtained from GEO. Counts were normalized by the DESeq2 median-of-ratios method; differential expression used a vectorized Welch t-test on log-transformed counts with Benjamini–Hochberg FDR control (the Python implementation was benchmarked against expected positive-control behavior). Over-representation analysis used KEGG (hsa) pathway annotations. Positive-control genes (FASN, CYP7A1, COL1A1, TNF) were specified before inspection.

### 2.2 FXR bioactivity dataset curation and applicability-domain reference

Human FXR (CHEMBL2047) concentration–response records with exact ('=') IC₃₀ relations and nM units were downloaded from the ChEMBL REST API (assay type B). Curation: salt stripping and mixture removal; canonical-SMILES deduplication (replicate measurements averaged, maximum 7 replicates); PAINS removal (RDKit FilterCatalog A/B/C); then a principal-component/leverage applicability-domain (AD) filter over 11 RDKit 2D descriptors, with the critical leverage h* = 3(k+1)/n = 0.0503 (k = 5 principal components) fitted on n = 358 compounds. The final dataset contains 354 compounds (pIC₅₀ range 3.38–9.96; long tail: 87 compounds below 5, 13 above 9). The full provenance chain (548 → 449 → 367 → 358 → 354) is logged.

### 2.3 Bayesian graph neural network

Molecules were featurized as molecular graphs (atom: element, degree, formal charge, total H, hybridization, aromaticity, ring membership; bonds: type). The model is a 3-layer GIN (hidden 96) with BatchNorm and a two-head output (μ, log σ²_aleatoric), trained with a heteroscedastic Gaussian NLL and activity-stratified sample weights (inverse bin frequency over pIC₅₀ edges 5–9). At inference, dropout remains active (MC-dropout, T = 50) and five seeds are ensembled: μ is the ensemble mean; total σ combines the mean aleatoric variance, the mean MC epistemic variance, and the between-seed variance of μ.

### 2.4 Dual-split evaluation protocol

Each random split (80/10/10, seed 42) is paired with a Bemis–Murcko scaffold split of the same data: scaffolds are assigned greedily by group size to train (80%) / validation (10%) / test (10%), so every test scaffold is unseen in training. Both regimes are evaluated with identical metrics and identical fingerprint baselines (Morgan radius-2, 2048-bit; random forest with 800 trees; XGBoost with matched budget).

### 2.5 Uncertainty metrics and post-hoc recalibration

All uncertainty statistics carry an explicit caliber label. **Test-only** values are recomputed from the stored per-compound predictions of the held-out test set; **pooled** values (validation + test, as stored by the training-time early-stopping loop) are reported in footnotes because early stopping on the validation fold renders them optimistic. Coverage is the fraction of compounds with |error| ≤ 1.96σ; every coverage figure is accompanied by a Wilson 95% interval and the sample size.

Recalibration experiments use the random-split test set (n = 36) as the calibration set and the scaffold-split test set (n = 34) as the out-of-domain evaluation set:

- **M0** raw σ intervals;
- **M1** leverage-inflated σ: σ_inf = σ·√(1 + h/h*), where h is the compound's leverage in the AD reference space;
- **M2** flat split-conformal: the finite-sample-corrected (1−α) quantile of absolute residuals on the calibration set, applied as a constant half-width;
- **M3/M4** adaptive and leverage-weighted z-score conformal variants (Supporting Information);
- **M5** scaffold-matched conformal: the saved five-seed scaffold-split ensemble is reloaded, the scaffold validation fold (n = 36) is predicted, and conformal quantiles are taken on that matched-domain fold (reproduction fidelity vs stored test predictions: Pearson r = 0.9997 on μ).

### 2.6 Natural-product library and three-tier annotation

Constituents of ten hepatoprotective herbs documented in the pharmacopoeia literature (233 entries, curated with literature cross-confirmation) were resolved in PubChem with per-compound CID logging; after ADMET property filters (150 < MW < 500, LogP < 5.5, HBD ≤ 5, HBA ≤ 10) and the pre-specified exclusion list (classical flavonoids/polyphenolic acids, pan-assay scaffolds, toxic Tripterygium constituents), 131 compounds remained as the screening library. The evidence base for this study is the CID-anchored 131-compound table; a data-management incident that overwrote an intermediate resolution file is documented in the Supporting Information, and the curation pipeline was re-executed to rebuild provenance, reproducing the resolution (224) and filter (131) stages with 131/131 row-level CID concordance; two shared-CID rows (a lignan pair resolving to one CID, and one compound legitimately listed for two herbs) are retained and flagged in the Supporting Information. Each compound was scored by the production ensemble (five seeds retrained on all 354 compounds; MC T = 50) and assigned to one of three tiers by the two-layer applicability rule: in-domain high confidence (leverage h ≤ h* and σ ≤ 0.70), in-domain low confidence (h ≤ h*, σ > 0.70), or out-of-domain warning (h > h*).

### 2.7 CW-BCS: confidence-weighted multi-target coverage with shrinkage correction

CW-BCS is defined as the geometric mean of min–max-normalized target scores, s = [(w·s_FXR)·s_THRB·s_ACC]^(1/3), with confidence weight w = 1/(1 + σ). It quantifies multi-target binding-coverage propensity, **not** pharmacological synergy, and is conditional on the chosen target panel. s_FXR is the GNN μ; s_THRB and s_ACC come from AutoDock Vina docking scores, avoiding small-sample modeling of those targets. Structural redundancy across each herb's top-3 compounds (Morgan Tanimoto) linearly penalizes scores above 0.6 similarity (cap 0.5). Herb-level scores are shrinkage-corrected, s × n/(n + 5), to penalize herbs represented by few compounds; a representative-compound constraint requires the displayed representative to be in-domain high-confidence (or a flagged dual listing). A compound-level absolute-activity flag (FXR μ ≥ 6.5 or ΔG ≤ −7 kcal/mol) is reported separately from ranks.

**Candidates outside the 131-compound panel.** For evidence consolidation we additionally maintain an extended unified board that scores a wider candidate set—including *Antrodia cinnamomea* constituents, *Centella asiatica* asiatic acid, and constituents of herbs beyond the ten-herb framework—by a transparent weighted sum of multi-target predictions, docking, documented evidence, novelty, and verified purchasability. Table 5 marks each candidate's source pipeline explicitly; asiatic acid enters on literature evidence alone (no computational score), and the constituent-to-herb attributions for derrone and anthraxin follow the curation sources and are flagged for re-verification against isolation literature before any experimental use.

### 2.8 Molecular docking

AutoDock Vina 1.2.5 with receptors 3FLI/1OSH (FXR), 3GWS (THR-β), 5KKN/3GID (ACC2), prepared by single-chain cleaning and Gasteiger charges; boxes centered on co-crystallized ligands. The pipeline was gated by redocking of four co-crystallized ligands (RMSD 0.33–1.22 Å, all < 2 Å) and benchmarked with positive controls (GW4064 −9.70, tanshinone IIA −9.73, chenodeoxycholic acid −8.70, obeticholic acid −6.77 kcal/mol on FXR; resmetirom −10.11 vs T3 −9.52 on THR-β; ND-646 −10.52 on ACC2), with the known Vina under-scoring of steroidal scaffolds noted.

### 2.9 Reproducibility

Every figure and table regenerates from raw public data via numbered scripts (GEO/ChEMBL/PubChem/PDB/KEGG accessions in the Data Availability statement). The recalibration study (this work) adds two scripts that consume only the stored predictions, per-compound leverages, and the saved ensemble checkpoint.

## 3. Results

### 3.1 The FXR/THR-β/ACC panel is supported by patient-level expression data

In GSE135251, all four chosen target genes are significantly dysregulated in NASH vs normal liver (Table 1): FXR (NR1H4) −0.285 (padj = 1.03 × 10⁻²), THR-β (THRB) −0.315 (padj = 1.99 × 10⁻²), ACC1 (ACACA) +0.897 (padj = 7.42 × 10⁻⁵), ACC2 (ACACB) +0.631 (padj = 4.23 × 10⁻³). Pre-specified positive controls behave as expected (FASN +2.47; CYP7A1 +2.16, consistent with FXR de-repression; COL1A1 +1.04 with fibrosis-stage correlation ρ = 0.431; TNF +1.09), and the analysis yields 3,909 DEGs (1,962 up / 1,947 down) at FDR < 0.05. KEGG over-representation ranks bile secretion (hsa04976) first at nominal p = 8.6 × 10⁻⁴; because ~30% of assayed genes are DE, the FDR-adjusted value (0.28) does not reach significance, and we report the enrichment as nominal only.

### 3.2 Point accuracy collapses under scaffold splits—for every architecture

Table 2 and Figure 1 give the dual-split audit. Under random splits the Bayesian GNN performs strongly (R² = 0.790; RMSE = 0.723; Spearman ρ = 0.768, p = 4.6 × 10⁻⁸; n = 36), satisfying the internally pre-set contract thresholds. Under scaffold splits the same pipeline collapses to R² = −0.610 (RMSE = 1.290), and the collapse is architecture-independent: random forest falls from 0.845 to 0.047 and XGBoost from 0.811 to −0.127. Notably, rank information partially survives for every model (scaffold-split Spearman ρ: BGNN 0.533, p = 1.2 × 10⁻³; RF 0.641, p = 4.5 × 10⁻⁵; XGBoost 0.483, p = 3.8 × 10⁻³; p values recomputed and archived in the Supporting Information), which is what screening actually consumes; we therefore report both R² and ρ throughout.

### 3.3 Uncertainty is informative in-domain, unproven out-of-domain, and intervals undercover

On test-only predictions, the rank correlation between σ and absolute error is +0.585 (p = 1.8 × 10⁻⁴, n = 36) for random splits—σ carries genuine information in-domain. For scaffold splits the test-only value is +0.269 (p = 0.124, n = 34): directionally positive but not significant, i.e., out-of-domain usefulness is *unproven*, not disproven. (Pooled calibration-loop values—random +0.340, n = 71; scaffold −0.027, n = 70—are relegated to footnotes: early stopping on the validation fold makes them non-exchangeable and, in the scaffold case, the two calipers even disagree in sign, which is itself a caution for pooled reporting.) Nominal 95% intervals cover 100% of random-split test compounds (over-conservative in-domain) but only 73.5% (Wilson CI 56.9–85.4%, n = 34) of scaffold-split test compounds: in-domain, errors are smaller than the intervals (over-coverage), whereas out-of-domain the growth of errors far outpaces the only mildly larger σ (under-coverage)—the failure is relative to error growth, not a shrinkage of σ itself.

### 3.4 Post-hoc recalibration cannot repair what the leverage cannot see

Table 3 and Figure 2 report the recalibration experiments. Calibrating on in-domain data (random-split test) and evaluating on the scaffold test set: leverage-inflated σ (M1) improves coverage from 0.735 to 0.765 (CI 60.0–87.6%)—still significantly below nominal; flat split-conformal (M2) yields 0.706; adaptive and leverage-weighted variants (M3/M4, Supporting Information) fall to 0.647 and 0.618, as finite in-domain residuals simply do not span the heavy-tailed out-of-domain errors. The root cause is structural: **the scaffold shift is invisible in the descriptor-space leverage**—mean leverage is 0.0096 in the scaffold test set vs 0.0126 in the calibration set, and 0% of either exceeds h* = 0.0503. Novel-scaffold compounds are not outliers in 2D descriptor space; they are ordinary-looking points whose local structure–activity relationships were never learned. Any reweighting driven by such covariates is therefore inert by construction.

Scaffold-matched conformal calibration (M5)—reloading the scaffold-split ensemble and calibrating on its own held-out-scaffold validation fold (n = 36; val R² = 0.153, RMSE = 0.875)—buys back nominal coverage at the 95% level: 1.000 (Wilson CI 89.9–100%; the ≥ 0.90 acceptance criterion was pre-set internally by the project team). Two caveats delimit this result. First, the price: the mean interval half-width is 2.98 pIC₅₀ units (z-score variants 5.18–5.21; Supporting Information), so the full interval width (5.96 units) spans 91% of the dataset's total range (6.58 units)—valid intervals under genuine extrapolation no longer discriminate compounds. Second, the validity is level-specific: at the 80% nominal level the z-score variant still under-covers (0.618, equal to raw σ; Supporting Information Table S1), showing that M5 succeeds by width rather than by restored calibration. (Two distinct sets of n = 36 appear in this work—the random-split test set and the scaffold validation fold; the latter simultaneously serves early stopping and M5 calibration, an approximation addressed in the Limitations.)

### 3.5 Operationalizing disclosure: three-tier annotation of 131 herbal natural products

Because repair is not a viable strategy, we operationalize disclosure. The production ensemble annotates all 131 library compounds (Figure 3): 72 in-domain high confidence, 32 in-domain low confidence, 27 out-of-domain warning. The in-domain high-confidence tier is enriched for the protoberberine alkaloid cluster of Coptis chinensis (e.g., berberine predicted μ = 8.21) and Schisandra lignans—both consistent with the FXR ligand chemistry of the training set and, as a post-hoc observation only, directionally consistent with the extensive berberine metabolic-pharmacology literature. Under the discipline validated in §3.4, out-of-domain members are gated from priority queues by tier (hard down-weighting) rather than by σ itself, because an under-inflated out-of-domain σ can be spuriously small; the confidence weight w = 1/(1 + σ) is applied only within the in-domain tiers.

### 3.6 Shrinkage-corrected CW-BCS ranking of ten herbs

Table 4 and Figure 4 give the herb ranking. The raw CW-BCS ordering places Tripterygium wilfordii fourth with only two admissible (non-toxic) constituents—exceeding Salvia miltiorrhiza with eighteen—so herb scores are shrinkage-corrected (s × n/(n+5)): Tripterygium falls from 0.565 to 0.162 (rank 4 → 9), while the leading tier—Coptis chinensis (0.529), Sophora flavescens (0.458), Glycyrrhiza uralensis (0.443), Salvia miltiorrhiza (0.426)—retains its membership (we claim tier identity only, not the internal order of ranks 1–4). The representative-compound constraint replaces low-confidence representatives (e.g., coptisine for Coptis, maackiain for Sophora) with in-domain high-confidence compounds (epiberberine, CW-BCS 0.710; kushenol E) while listing the former as secondary; Silybum marianum, whose constituents are all out-of-domain warnings, carries an explicit whole-herb flag—silybin thus serving as the worked example of tier-based gating. As a cross-check of directional consistency between data-driven and physics-based scoring, predicted μ and Vina ΔG for the top-10 compounds correlate at Spearman ρ = −0.394 (n = 10, p = 0.26)—directionally consistent and explicitly exploratory at this sample size. Four THR-β docking affinities are positive (physically non-binding) for bottom-ranked compounds; these are flagged, not deleted, and the CW-BCS geometric mean is insensitive to them (Supporting Information).

### 3.7 Evidence-graded candidates

Table 5 consolidates nine prioritized compounds with explicit evidence tiers and purchasability verified at the time of analysis. The Antrodia cinnamomea cluster (antcin K, antrodin B, antrocinnamomin F) is anchored by **species-level** clinical evidence—a 28-subject double-blind trial of the mycelial powder with serum fibrosis scores (SteatoTest family) as endpoints (PMID 32657670)—plus dual-source computational convergence; we do not attribute the powder-level evidence to individual molecules. Asiatic acid (Centella asiatica) enters on direct mechanistic literature (TGF-β/Smad and hepatic stellate cell inhibition, PMID 35963324) and is explicitly labeled as carrying no computational score in our panel. Epiberberine represents the pure-computation, high-confidence tier; berberine doubles as the positive-control anchor; derrone (Glycyrrhiza) and anthraxin (Hedyotis diffusa) are purchasable pure-computation candidates; the fungal metabolite 07H239-A is retained **only** as a computational control—its source strain is absent from public culture collections and its discovery paper is titled for cytotoxicity (PMID 15387660). All ranking claims are computational prioritizations requiring experimental validation; no therapeutic efficacy is claimed for any compound.

## 4. Discussion

**The central finding is an information-theoretic one.** Random-split metrics answer "how well does the model interpolate?"—a question screening never asks. Scaffold-split auditing answers "what happens when the model meets a genuinely new chemotype?"—and the answer, here quantified as R² = 0.79 → −0.61 across three architectures, is that the useful signal degrades to partial rank information (ρ ≈ 0.53). This is consistent with the broader literature on temporal- and scaffold-split validation and sharpens it with matched UQ instrumentation: the collapse is not accompanied by any leverage-space signature that could be used to detect or repair it post hoc (§3.4). The practical corollary is uncomfortable for the recalibration program: conformal methods inherit the exchangeability assumption they are asked to fix. When calibration data are in-domain, intervals undercover (0.618–0.765); when calibration data are scaffold-matched, intervals are valid but approach the width of the entire activity range (half-width 2.98 of a 6.58-unit span). Under genuine extrapolation, honest intervals and useful intervals diverge, and no post-hoc procedure bridges that gap—only new data (or new training scaffolds) can.

**What survives the audit becomes the deliverable.** Since repair is impossible, disclosure must be engineered into the pipeline: (i) dual-split metrics as the default reporting standard, with R² and ρ both reported because ranks partially survive collapse; (ii) uncertainty calipers stated explicitly (our pooled vs test-only discrepancy—even a sign flip in the scaffold case—shows pooled early-stopping statistics can mislead); (iii) three-tier applicability gating, with out-of-domain members excluded from priority queues by rule rather than by σ-magnitude, since under-inflated out-of-domain σ can be spuriously reassuring; (iv) small-sample guards on aggregate scores (shrinkage, representative-confidence constraints) so that herbs with two constituents cannot outrank herbs with eighteen.

**On the choice of GNN despite higher baseline point accuracy.** The random forest's random-split R² (0.845) exceeds the GNN's (0.790) at this sample size, and we report that without embarrassment. The GNN is retained because the deliverable is per-compound calibrated uncertainty plus atom-level interpretability (GNNExplainer attributions concentrate on the quaternary ammonium and isoquinoline core of the protoberberines—a chemically sensible pharmacophore), not point accuracy; and because the ensemble MC-dropout σ demonstrably ranks errors in-domain (+0.585), which no variance-free baseline offers. Under scaffold splits both architectures are equally unusable for point prediction, which reinforces that the binding constraint is data coverage, not model class.

**Pharmacological semantics and boundaries.** CW-BCS is a panel-conditional binding-coverage propensity score: it is deliberately agnostic to mechanism (agonism vs antagonism), makes no synergy claim, and inherits the known scoring biases of Vina for steroidal and macrocyclic ligands. The herb ranking is a prioritization for experimental triage—an economical first-pass wet-lab design (four purchasable standards in a HepG2 lipid-accumulation assay, with TG-reduction and viability gates) follows directly from Table 5 and is planned as the external calibration loop for the computational pipeline. Herbs scoring low on this panel (e.g., Schisandra, Ganoderma) are not thereby "refuted": the panel simply does not contain their principal axes of action (e.g., Nrf2), and we interpret low scores as out-of-panel rather than inactive.

**Limitations.** (1) No wet-laboratory validation is included; all candidate claims are computational prioritizations. (2) A single target (FXR) provides the modeling substrate; multi-target QSAR extensions require scaffold-split validation per target before their outputs may be used for out-of-domain ranking, which we have not yet completed for the extended panel. (3) Sample sizes for the audit (354 compounds; 36/34 test compounds) limit precision—hence Wilson intervals throughout; the scaffold σ–error correlation (+0.269, p = 0.124) is unproven rather than null. (4) The scaffold-validation fold doubles as the early-stopping fold, an approximation that renders pooled statistics mildly optimistic; we mitigate by test-only primary reporting. (5) Shrinkage strength (k = 5) is a reasoned default, with sensitivity analysis in the Supporting Information; the leading tier is stable across k. (6) A single random split is audited per regime (seed 42), following the original study protocol; split-resampling would tighten the interval estimates. (7) Vina scoring biases (steroids, macrocycles) propagate into s_THRB/s_ACC; conclusions rest on within-library relative comparisons. (8) The 131-compound library is a curated, non-exhaustive subset of ten herbs' constituent space.

## 5. Conclusions

Under an audit that mimics what natural-product screening actually is—confronting novel scaffolds—point-estimate virtual screening collapses (R² 0.79 → −0.61) regardless of architecture, and the predictive uncertainty that looks well-calibrated on random splits both under-covers out-of-domain (73.5%) and eludes post-hoc repair, because scaffold novelty leaves no trace in descriptor-space leverage. Matched-domain conformal calibration buys back coverage (100%) only by spending the resolution that made screening worth doing (half-width ≈ 3 of a 6.6-unit range). The workable strategy is therefore disclosure engineered as process: dual-split reporting, explicit uncertainty calipers, and rule-based applicability gating—which, applied to 131 herbal constituents, yield a shrinkage-corrected, confidence-constrained prioritization (Coptis–Sophora–Glycyrrhiza–Salvia leading tier; nine evidence-graded candidate compounds). We offer the audit protocol as a minimum reporting standard for ML-based natural-product screening, and the tiered annotation as its operational output.

---

## Associated Content

**Supporting Information.** Table S0: number-to-source-file map for every quantitative claim; recalibration variants M3/M4 and z-score M5 (Table S1); shrinkage sensitivity (Table S2); library curation provenance and data-management incident note (Table S3); full 131-compound four-dimensional CW-BCS table; docking details, positive-control benchmark, and flagged non-binding THR-β entries; GNNExplainer attributions.

## Author Information

Q.W. and X.J. conceived the study; the roundtable-audit framework (adversarial red-team review with independent recomputation) was used internally to stress-test all claims before drafting. All authors have read and approved the manuscript. [Full author list, ORCIDs, and funding statement to be completed at submission.]

**Conflict of interest.** The authors declare no competing financial interest.

**Abbreviations.** MASH, metabolic dysfunction-associated steatohepatitis; FXR, farnesoid X receptor; THR-β, thyroid hormone receptor beta; ACC, acetyl-CoA carboxylase; GNN, graph neural network; UQ, uncertainty quantification; AD, applicability domain; CW-BCS, confidence-weighted binding-coverage score; DEG, differentially expressed gene.

## Data Availability

All data are public: RNA-seq, GEO GSE135251 (accessed 2026-08-17); FXR bioactivity, ChEMBL CHEMBL2047 (release 37, per database release chronology; accessed 2026-08-17 via REST API, assay type B; release status re-archived 2026-08-23); compound identifiers and structures, PubChem PUG-REST (per-compound CIDs logged); receptor structures, RCSB PDB (3FLI, 1OSH, 3GWS, 5KKN, 3GID); pathway annotations, KEGG REST (hsa; snapshot archived 2026-08-23). Per-compound predictions, leverages, the recalibration results (results/v6), all analysis scripts, a dependency manifest (requirements.txt), and per-figure source-data tables are available from the corresponding author and will be deposited in a public repository (Zenodo) upon acceptance. This study is a purely computational re-analysis of public data; no human or animal experiments were conducted.

## References

1. Govaere, O. et al. Transcriptomic profiling across the nonalcoholic fatty liver disease spectrum reveals gene signatures for steatohepatitis and fibrosis. *Sci. Transl. Med.* **2020**, 12, eaba4448 (GSE135251; PMID 33268509).
2. Harrison, S. A. et al. A phase 3, randomized, controlled trial of resmetirom in nonalcoholic steatohepatitis with liver fibrosis. *N. Engl. J. Med.* **2024**, 390, 497–509.
3. Neuschwander-Tetri, B. A. et al. Farnesoid X nuclear receptor ligand obeticholic acid for non-cirrhotic, non-alcoholic steatohepatitis (FLINT). *Lancet* **2015**, 385, 956–965.
4. Kong, W. et al. Berberine is a novel cholesterol-lowering drug with a unique mechanism of action. *Nat. Med.* **2004**, 10, 1344–1351.
5. Gaulton, A. et al. ChEMBL: a large-scale bioactivity database for drug discovery. *Nucleic Acids Res.* **2012**, 40, D1100–D1107.
6. Kim, S. et al. PubChem 2023 update. *Nucleic Acids Res.* **2023**, 51, D1373–D1380.
7. Berman, H. M. et al. The Protein Data Bank. *Nucleic Acids Res.* **2000**, 28, 235–242.
8. Kanehisa, M.; Goto, S. KEGG: Kyoto Encyclopedia of Genes and Genomes. *Nucleic Acids Res.* **2000**, 28, 27–30.
9. Bemis, G. W.; Murcko, M. A. The properties of known drugs. 1. Molecular frameworks. *J. Med. Chem.* **1996**, 39, 2887–2893.
10. Sheridan, R. P. Time-split cross-validation as a method for estimating the performance of predictive models. *J. Chem. Inf. Model.* **2013**, 53, 783–790.
11. Baell, J. B.; Holloway, G. A. New substructure filters for removal of pan assay interference compounds (PAINS). *J. Med. Chem.* **2010**, 53, 2719–2740.
12. Tropsha, A. Best practices for QSAR model development, validation, and exploitation. *Mol. Inform.* **2010**, 29, 476–488.
13. Xu, K. et al. How powerful are graph neural networks? *Proc. ICLR* **2019**.
14. Fey, M.; Lenssen, J. E. Fast graph representation learning with PyTorch Geometric. *Proc. ICLR Workshop* **2019**.
15. Gal, Y.; Ghahramani, Z. Dropout as a Bayesian approximation: representing model uncertainty in deep learning. *Proc. ICML* **2016**, 1050–1059.
16. Lakshminarayanan, B.; Pritzel, A.; Blundell, C. Simple and scalable predictive uncertainty estimation using deep ensembles. *Proc. NeurIPS* **2017**, 6402–6413.
17. Kendall, A.; Gal, Y. What uncertainties do we need in Bayesian deep learning for computer vision? *Proc. NeurIPS* **2017**, 5574–5584.
18. Papadopoulos, H.; Proedrou, K.; Vovk, V.; Gammerman, A. Inductive confidence machines for regression. *Proc. ECML* **2002**, 345–356.
19. Tibshirani, R. J.; Foygel Barber, R.; Candes, E.; Ramdas, A. Predictive inference with the jackknife+. *J. R. Stat. Soc. B* **2019**, 81, 1351–1386.
20. Angelopoulos, A. N.; Bates, S. Conformal prediction: a gentle introduction. *Found. Trends Mach. Learn.* **2023**, 16, 494–591.
21. Love, M. I.; Huber, W.; Anders, S. Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. *Genome Biol.* **2014**, 15, 550.
22. Benjamini, Y.; Hochberg, Y. Controlling the false discovery rate. *J. R. Stat. Soc. B* **1995**, 57, 289–300.
23. Eberhardt, J.; Santos-Martins, D.; Till, A. F.; McCammon, J. A. AutoDock Vina 1.2.0: new docking methods, expanded force field, and Python bindings. *J. Chem. Inf. Model.* **2021**, 61, 3891–3898.
24. Wilson, E. B. Probable inference, the law of succession, and statistical inference. *J. Am. Stat. Assoc.* **1927**, 22, 209–212.
25. Chiou, Y.-L. et al. Hepatoprotective effect of *Antrodia cinnamomea* mycelium in patients with nonalcoholic steatohepatitis: a randomized, double-blind, placebo-controlled trial. *J. Am. Coll. Nutr.* **2021** (PMID 32657670; DOI 10.1080/07315724.2020.1779850).
26. Li, Y. et al. Asiatic acid alleviates liver fibrosis via multiple signaling pathways based on integrated network pharmacology analysis and experimental validation. *Eur. J. Pharmacol.* **2022**, 931, 175193 (PMID 35963324).
27. McDonald, L. A. et al. 07H239-A, a new cytotoxic eremophilane sesquiterpene from a marine-derived xylariaceous fungus. *J. Nat. Prod.* **2004**, 67, 1565–1567 (PMID 15387660).

---

## Tables

**Table 1. Pathological validation of the target panel in GSE135251 (NASH vs normal, n = 216).**

| Gene (protein) | log2FC | padj | Interpretation |
|---|---|---|---|
| NR1H4 (FXR) | −0.285 | 1.03 × 10⁻² | receptor down-regulated |
| THRB (THR-β) | −0.315 | 1.99 × 10⁻² | receptor down-regulated |
| ACACA (ACC1) | +0.897 | 7.42 × 10⁻⁵ | lipogenesis up |
| ACACB (ACC2) | +0.631 | 4.23 × 10⁻³ | lipogenesis up |
| FASN (control) | +2.47 | — | expected direction |
| CYP7A1 (control) | +2.16 | — | FXR de-repression |
| COL1A1 (control) | +1.04 | — | fibrosis (ρ = 0.431 with stage) |
| TNF (control) | +1.09 | — | inflammation |

**Table 2. Dual-split audit (identical data and metrics; scaffold splits exclude all test scaffolds from training).**

| Model | Split | R² | RMSE | MAE | Spearman ρ |
|---|---|---|---|---|---|
| Bayesian GNN | random (n=36) | 0.790 | 0.723 | 0.592 | 0.768 |
| Bayesian GNN | scaffold (n=34) | **−0.610** | 1.290 | 1.039 | 0.533 |
| Random forest | random | 0.845 | 0.620 | 0.498 | 0.811 |
| Random forest | scaffold | **0.047** | 0.992 | 0.713 | 0.641 |
| XGBoost | random | 0.811 | 0.686 | 0.507 | 0.820 |
| XGBoost | scaffold | **−0.127** | 1.079 | 0.803 | 0.483 |

*(All values stored in results/tables/gnn_metrics_v2.json; the BGNN values were independently recomputed from per-compound test predictions.)*

**Table 3. Post-hoc recalibration of 95% intervals, evaluated on the scaffold test set (out-of-domain, n = 34).**

| Method | Calibration source | Coverage (Wilson 95% CI) | Mean half-width (pIC₅₀) |
|---|---|---|---|
| M0 raw σ | not applicable (no calibration set) | 0.735 (0.569–0.854) | 1.66 |
| M1 σ·√(1+h/h*) | not applicable (parametric formula) | 0.765 (0.600–0.876) | 1.80 |
| M2 flat split-conformal | random test (n=36) | 0.706 (0.538–0.832) | 1.51 |
| M5 scaffold-matched conformal | scaffold validation (n=36) | **1.000 (0.899–1.000)** | **2.98** |

*(M3 adaptive z-conformal 0.647; M4 leverage-weighted 0.618 — Supporting Information. Dataset pIC₅₀ range 3.38–9.96. At the 80% nominal level, M5's z-variant covers only 0.618 — the restored validity is level-specific and bought by width.)*

**Table 4. Shrinkage-corrected CW-BCS herb ranking with representative-confidence constraint.** (Raw = after redundancy penalty, before shrinkage.)

| Rank | Herb | n | Raw s | Shrunk s | Representative (tier) |
|---|---|---|---|---|---|
| 1 | *Coptis chinensis* | 14 | 0.718 | 0.529 | epiberberine (in-domain high conf.) |
| 2 | *Sophora flavescens* | 18 | 0.585 | 0.458 | kushenol E (in-domain high conf.) |
| 3 | *Glycyrrhiza uralensis* | 18 | 0.566 | 0.443 | licoflavanone (in-domain high conf.) |
| 4 | *Salvia miltiorrhiza* | 18 | 0.545 | 0.426 | salvilenone (in-domain high conf.) |
| 5 | *Artemisia annua* | 23 | 0.456 | 0.375 | chrysosplenol D + flagged OOD secondary |
| 6 | *Silybum marianum* | 11 | 0.415 | 0.285 | all-constituent OOD warning (whole-herb flag) |
| 7 | *Schisandra chinensis* | 18 | 0.354 | 0.277 | schisandrin C (in-domain high conf.) |
| 8 | *Ganoderma lucidum* | 6 | 0.406 | 0.221 | lucidenic acid C (in-domain high conf.) |
| 9 | *Tripterygium wilfordii* | 2 | 0.565 | 0.162 | triptophenolide (rank 4 → 9 after shrinkage) |
| 10 | *Bupleurum chinense* | 3 | 0.099 | 0.037 | saikogenin F (in-domain high conf.) |

**Table 5. Evidence-graded prioritized candidates (computational prioritization; no efficacy claim).**

| Compound (source) | Evidence level | Model tier | Purchasable | Anchor | Pipeline |
|---|---|---|---|---|---|
| Antcin K (*Antrodia cinnamomea*) | species-level clinical + dual-source computation | computable | standard | PMID 32657670 | extended board |
| Antrodin B (*A. cinnamomea*) | species-level clinical + dual-source computation | computable | standard | PMID 32657670 | extended board |
| Antrocinnamomin F (*A. cinnamomea*) | species-level clinical + dual-source computation | computable (unified-board 0.859) | standard | PMID 32657670 | extended board |
| Asiatic acid (*Centella asiatica*) | direct mechanistic literature (fibrosis axis) | **no computational score** (evidence-only inclusion) | standard | PMID 35963324 | evidence-only |
| Epiberberine (*Coptis chinensis*) | pure computation | in-domain high confidence | herb-derived | CW-BCS 0.710 | 131-compound panel |
| Berberine (*Coptis chinensis*) | known-mechanism anchor | in-domain high confidence (μ = 8.21) | standard | ref 4 | 131-compound panel |
| Derrone (*Glycyrrhiza uralensis*) | pure computation; attribution flagged | computable | herb-derived | unified-board 0.786 | extended board |
| Anthraxin (*Hedyotis diffusa*) | pure computation; identity flagged | computable | herb-derived | unified-board 0.792 | extended board |
| 07H239-A (Xylariaceae fungus) | **computational control only** (cytotoxicity-titled source; strain not in ATCC/NRRL) | computable | no | PMID 15387660 | extended board |

*Silybin (*Silybum marianum*) appears as the worked example of out-of-domain gating: computationally attractive but tier-excluded from the priority queue.*

## Figure Legends

**Figure 1.** Dual-split audit of the Bayesian GNN on 354 FXR agonists. Left: random split (proposal-style validation; n = 36). Right: Bemis–Murcko scaffold split (every test scaffold unseen in training; n = 34). Points: observed vs predicted pIC₅₀; whiskers: nominal 95% intervals (μ ± 1.96σ). Point accuracy collapses (R² 0.790 → −0.610) while rank information partially survives (ρ 0.768 → 0.533). Note on reading: mean interval half-widths are similar between panels (≈1.5 vs ≈1.7 pIC₅₀ units), yet coverage differs (100% vs 73.5%) because out-of-domain errors grow far faster than σ—the visual similarity of the whiskers is itself the failure mode being audited.

**Figure 2.** Post-hoc recalibration on the scaffold test set (n = 34; calibration source in parentheses). (a) 95% coverage with Wilson intervals and nominal line: in-domain-calibrated methods (M0 as-trained, M1 leverage-inflated, M2 flat split-conformal) remain significantly below nominal; scaffold-matched conformal (M5) attains 1.000. (b) The price: mean interval half-widths—M5's 2.98 pIC₅₀ units approach the full dataset range (3.38–9.96), forfeiting prioritization resolution.

**Figure 3.** Three-tier applicability annotation of 131 herbal natural products (bars, left axis) with median predictive σ per tier (line, right axis). Discipline: out-of-domain members are gated from priority queues by tier, not by σ magnitude.

**Figure 4.** Shrinkage-corrected CW-BCS herb ranking (s × n/(n+5)); vertical ticks mark pre-shrinkage scores. *Tripterygium wilfordii* (2 constituents) falls from rank 4 to 9; the leading tier retains membership. Bar color: representative-compound confidence status.
