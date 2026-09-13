# -*- coding: utf-8 -*-
"""Advancement round Track A: assay-aware FASN transferability runs.

Executes: (1) assay-aware master enrichment; (2) E1-E5 external stratification;
(3) stratified external validation (Ridge champion + RF tree + baselines);
(4) small-label assay calibration pilots (methods A-E) vs canonical-only and
cal-mean baseline, 10 seeds; (5) NP54 domain status v2. GNN stays closed.
"""
from pathlib import Path
import json, sys, io, platform
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem, Crippen, Descriptors, Lipinski
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RDLogger.DisableLog("rdApp.*")
try:
    from xgboost import XGBRegressor
    HAVE_XGB = True
except Exception:
    HAVE_XGB = False

ROOT = Path(r"D:/zcode-workspace/aidd-repo-work/00-当前研究")
OUT = ROOT / "advancement_round_20260913"
MASTER = ROOT / "final_strategy_round_20260912/FASN_activity_master.csv"
LIB54 = ROOT.parent / "03-课题-MASH研究-v2/data/tcm/np_library_filtered.csv"
CANONICAL_ASSAY = "CHEMBL5731051"
MIRROR_ASSAY = "CHEMBL5734379"
SEEDS = list(range(20260912, 20260922))
KAPPA = 20.0  # shrinkage strength for method D
FPGEN = AllChem.GetMorganGenerator(radius=2, fpSize=2048)


def parse(s):
    return Chem.MolFromSmiles(str(s)) if s and str(s) != "nan" else None


def fp(s):
    m = parse(s)
    return FPGEN.GetFingerprint(m) if m is not None else None


def fp_matrix(smiles):
    arr = np.zeros((len(smiles), 2048), dtype=np.float32)
    for i, s in enumerate(smiles):
        f = fp(s)
        if f is not None:
            DataStructs.ConvertToNumpyArray(f, arr[i])
    return arr


def descriptors(s):
    m = parse(s)
    if m is None:
        return [np.nan] * 10
    return [Descriptors.MolWt(m), Crippen.MolLogP(m), Descriptors.TPSA(m),
            Lipinski.NumHDonors(m), Lipinski.NumHAcceptors(m), Lipinski.NumRotatableBonds(m),
            Lipinski.RingCount(m), Lipinski.NumAromaticRings(m), Lipinski.FractionCSP3(m),
            Descriptors.HeavyAtomCount(m)]


def scaffold(s):
    m = parse(s)
    if m is None:
        return ""
    v = MurckoScaffold.MurckoScaffoldSmiles(mol=m)
    return v or Chem.MolToSmiles(m, isomericSmiles=True)


def metrics(y, p):
    y = np.asarray(y, float); p = np.asarray(p, float)
    return {"n": int(len(y)),
            "r2": float(r2_score(y, p)) if len(np.unique(y)) > 1 else None,
            "rmse": float(mean_squared_error(y, p) ** .5),
            "mae": float(mean_absolute_error(y, p)),
            "spearman": float(pd.Series(y).corr(pd.Series(p), method="spearman")) if len(np.unique(p)) > 1 else None,
            "bias": float(np.mean(p - y))}


# ---------- assay classification rules (documented, keyword-based, no guessing) ----------
def classify_assay(aid, desc):
    d = (desc or "").lower()
    substrates = []
    for key, tag in [("acetyl-coa", "acetyl-CoA"), ("malonyl-coa", "malonyl-CoA"), ("nadph", "NADPH"),
                     ("3h-acetyl", "3H-acetyl-CoA"), ("4-methylumbelliferyl", "4-MUH"), ("[14c]-acetate", "14C-acetate")]:
        if key in d:
            substrates.append(tag)
    if "scintillation proximity" in d or aid in {"CHEMBL5731051", "CHEMBL5734379", "CHEMBL4123591", "CHEMBL3619925"}:
        family = "SPA_radiometric"
    elif "skbr3" in d:
        family = "SKBr3_cell_extract_CPM"
    elif "nadph" in d and ("time-point" in d or "resazurin" in d or "kinetic" in d):
        family = "NADPH_kinetic_absorbance"
    elif "4-methylumbelliferyl" in d or "4-muh" in d:
        family = "fluorogenic_substrate_domain"
    elif "cyclopropane" in d:
        family = "description_conflict_bacterial_FAS"
    elif "cell" in d or "hela" in d or "bt474" in d or "zr-75" in d:
        family = "cell_based_or_cell_extract_other"
    else:
        family = "generic_enzyme_inhibition"
    if "cell extract" in d or "skbr3" in d or "cell derived" in d or "hela cell derived" in d:
        construct_cls = "cell_extract"
    elif "ketoacyl reductase" in d or "kr domain" in d:
        construct_cls = "fragment_KR"
    elif "thioster" in d or "te activity" in d:
        construct_cls = "fragment_TE"
    elif "full length" in d or "full-length" in d:
        construct_cls = "full_length"
    else:
        construct_cls = "unknown"
    if family == "SPA_radiometric" and construct_cls in {"full_length", "cell_extract"} and len(substrates) >= 2:
        conf = "high"
    elif family != "generic_enzyme_inhibition" and construct_cls != "unknown":
        conf = "medium"
    elif family == "description_conflict_bacterial_FAS":
        conf = "low"
    else:
        conf = "medium" if substrates else "low"
    cluster = f"{family}|{construct_cls}"
    return family, cluster, construct_cls, ";".join(substrates) if substrates else "unknown", conf


def main():
    import rdkit, sklearn
    env = {"python": platform.python_version(), "rdkit": getattr(rdkit, "__version__", "?"),
           "sklearn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__,
           "xgboost_available": HAVE_XGB, "seeds": SEEDS, "date": "2026-09-13"}
    master = pd.read_csv(MASTER)

    # ================= 1) assay-aware master =================
    aw = master.copy()
    cls = aw.apply(lambda r: classify_assay(r.assay_id, r.get("assay_description", "")), axis=1)
    aw["assay_family"] = [c[0] for c in cls]
    aw["assay_cluster"] = [c[1] for c in cls]
    aw["full_length_or_fragment"] = [c[2] for c in cls]
    aw["substrate_cofactor_info"] = [c[3] for c in cls]
    aw["confidence_level"] = [c[4] for c in cls]
    aw["biochemical_or_cellular"] = aw["biochemical_or_cellular"]
    aw["species"] = aw["species"]
    aw["construct_reported"] = aw["construct"]
    aw["endpoint_type"] = aw["activity_type"]
    aw["document_family"] = aw["document_id"]
    aw["medicinal_chemistry_series"] = np.where(
        aw.assay_id == CANONICAL_ASSAY, "document_series_proxy_CHEMBL5725564", "unknown")
    aw.to_csv(OUT / "FASN_assay_aware_master.csv", index=False, encoding="utf-8-sig")

    # ================= canonical training set =================
    rec = master[(master.assay_id == CANONICAL_ASSAY) & (master.activity_type == "IC50")
                 & (master.unit.str.lower() == "nm") & (master.relation == "=")
                 & (master.standardized_nM > 0) & (master.is_valid_smiles == 1)].copy()
    rec["pActivity"] = -np.log10(rec.standardized_nM.astype(float) * 1e-9)
    clean = rec.groupby("molecule_id", as_index=False).agg(
        canonical_smiles=("canonical_smiles", "first"), pActivity=("pActivity", "median"))
    clean["scaffold"] = clean.canonical_smiles.map(scaffold)
    train_smiles = clean.canonical_smiles.tolist(); y_tr = clean.pActivity.to_numpy(float)
    X_tr = fp_matrix(train_smiles)
    train_fps = [fp(s) for s in train_smiles]
    train_ids = set(clean.molecule_id)

    # conformal quantiles from canonical grouped CV (RF residuals)
    gkf = GroupKFold(n_splits=5)
    resid = []
    for tr_i, cal_i in gkf.split(clean, groups=clean.scaffold):
        m = RandomForestRegressor(n_estimators=700, max_features="sqrt", min_samples_leaf=2,
                                  random_state=SEEDS[0], n_jobs=-1)
        m.fit(X_tr[tr_i], y_tr[tr_i])
        resid.extend(np.abs(y_tr[cal_i] - m.predict(X_tr[cal_i])))
    resid = np.sort(np.asarray(resid))
    def cq(a):
        r = int(np.ceil((len(resid) + 1) * (1 - a))) - 1
        return float(resid[min(max(r, 0), len(resid) - 1)])
    q10, q20 = cq(0.10), cq(0.20)
    loo_nn = [max(DataStructs.BulkTanimotoSimilarity(train_fps[i], [train_fps[j] for j in range(len(train_fps)) if j != i]))
              for i in range(len(train_fps))]
    ad_thr = float(np.quantile(loo_nn, 0.05))

    # ================= 2) external stratification =================
    pool = master[(master.construct == "full_length_human_FASN_stated_in_assay_description")
                  & (master.activity_type == "IC50") & (master.unit.str.lower() == "nm")
                  & (master.relation == "=") & (master.standardized_nM > 0)
                  & (master.is_valid_smiles == 1)
                  & (~master.assay_id.isin([CANONICAL_ASSAY, MIRROR_ASSAY]))].copy()
    pool["pActivity"] = -np.log10(pool.standardized_nM.astype(float) * 1e-9)
    ext = pool.groupby("molecule_id", as_index=False).agg(
        canonical_smiles=("canonical_smiles", "first"), pActivity=("pActivity", "median"),
        assay_id=("assay_id", "first"), assay_description=("assay_description", "first"),
        document_id=("document_id", "first"), document_year=("document_year", "first"))
    ext["overlap_canonical"] = ext.molecule_id.isin(train_ids)
    excluded = ext[ext.overlap_canonical].copy()
    ext = ext[~ext.overlap_canonical].reset_index(drop=True)
    ext_fps = [fp(s) for s in ext.canonical_smiles]
    ext["max_Tanimoto_to_canonical"] = [float(max(DataStructs.BulkTanimotoSimilarity(f, train_fps))) for f in ext_fps]
    ext["ad_status"] = np.where(ext.max_Tanimoto_to_canonical >= ad_thr, "in_domain", "out_of_domain")
    # strata: E1 = SPA-same-detection (CHEMBL4123591); E2 = same target, different assay method;
    # E3 = cross-document attribute (all True); E4 = OOD chemistry attribute (ad_status);
    # E5 = conditions insufficient -> none identified (all three assays have substrate+detection info)
    ext["stratum"] = np.where(ext.assay_id == "CHEMBL4123591", "E1", "E2")
    ext["cross_document_E3_attribute"] = True
    desc_ok = ext.assay_description.str.contains("NADPH|acetyl|malonyl", case=False)
    ext["E5_candidate"] = ~desc_ok
    ext.to_csv(OUT / "FASN_external_stratified.csv", index=False, encoding="utf-8-sig")

    # ================= 3) stratified external validation =================
    X_ext = fp_matrix(ext.canonical_smiles.tolist())
    y_ext = ext.pActivity.to_numpy(float)
    models = {
        "ecfp_ridge_champion": make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=10.0)),
        "ecfp_rf_tree_baseline": RandomForestRegressor(n_estimators=700, max_features="sqrt",
                                                       min_samples_leaf=2, random_state=SEEDS[0], n_jobs=-1),
        "global_mean_baseline": DummyRegressor(strategy="mean"),
    }
    for name, m in models.items():
        m.fit(X_tr, y_tr)
    preds = {name: m.predict(X_ext) for name, m in models.items()}
    subsets = {
        "all": np.ones(len(ext), bool),
        "E1": (ext.stratum == "E1").to_numpy(),
        "E2": (ext.stratum == "E2").to_numpy(),
        "E1_ADin": ((ext.stratum == "E1") & (ext.ad_status == "in_domain")).to_numpy(),
        "E1_OOD": ((ext.stratum == "E1") & (ext.ad_status == "out_of_domain")).to_numpy(),
        "E2_ADin": ((ext.stratum == "E2") & (ext.ad_status == "in_domain")).to_numpy(),
        "E2_OOD": ((ext.stratum == "E2") & (ext.ad_status == "out_of_domain")).to_numpy(),
        "ADin_all": (ext.ad_status == "in_domain").to_numpy(),
        "OOD_all": (ext.ad_status == "out_of_domain").to_numpy(),
    }
    rows = []
    for sub_name, mask in subsets.items():
        if mask.sum() < 3:
            continue
        for mname, p in preds.items():
            r = metrics(y_ext[mask], p[mask])
            r.update({"model": mname, "subset": sub_name,
                      "coverage_q10": float(np.mean((y_ext[mask] >= p[mask] - q10) & (y_ext[mask] <= p[mask] + q10))),
                      "coverage_q20": float(np.mean((y_ext[mask] >= p[mask] - q20) & (y_ext[mask] <= p[mask] + q20))),
                      "ad_coverage": float(ext.ad_status[mask].eq("in_domain").mean()),
                      "n": int(mask.sum())})
            rows.append(r)
    strat = pd.DataFrame(rows)
    strat.to_csv(OUT / "FASN_external_stratified_results.csv", index=False, encoding="utf-8-sig")

    # ================= 4) calibration pilots (A-E) =================
    # Per external assay: split cal (25%, min 6, max 12) / test, 10 seeds.
    # Methods: none | cal_mean_baseline | A_offset | B_linear | C_indicator_ridge | D_shrunk_offset | E_pool_ridge
    cal_rows = []
    assays = sorted(ext.assay_id.unique())
    rng_global = np.random.default_rng(SEEDS[0])
    for seed in SEEDS:
        cal_idx_by_assay = {}
        for aid in assays:
            idx = np.where(ext.assay_id.to_numpy() == aid)[0]
            n_cal = int(min(12, max(6, round(0.25 * len(idx)))))
            rng = np.random.default_rng(seed + hash(aid) % 1000)
            perm = rng.permutation(idx)
            cal_idx_by_assay[aid] = (perm[:n_cal], perm[n_cal:])
        # pooled arrays
        all_cal = np.concatenate([cal_idx_by_assay[a][0] for a in assays])
        # per-method predictions on all external test molecules
        p_none = preds["ecfp_ridge_champion"].copy()
        p_off = p_none.copy(); p_lin = p_none.copy(); p_shr = p_none.copy()
        p_ind = None; p_pool = None
        # A / B / D per assay
        for aid in assays:
            ci, ti = cal_idx_by_assay[aid]
            pc, yc = p_none[ci], y_ext[ci]
            delta = float(np.mean(yc - pc))
            p_off[ti] = p_none[ti] + delta
            p_shr[ti] = p_none[ti] + (len(ci) / (len(ci) + KAPPA)) * delta
            var = np.var(pc)
            if var > 1e-9:
                a = float(np.cov(yc, pc)[0, 1] / var); b = float(np.mean(yc) - a * np.mean(pc))
            else:
                a, b = 1.0, delta
            p_lin[ti] = a * p_none[ti] + b
        # cal_mean baseline per assay
        p_cm = p_none.copy()
        for aid in assays:
            ci, ti = cal_idx_by_assay[aid]
            p_cm[ti] = np.mean(y_ext[ci])
        # C: ridge with assay indicators trained on canonical + cal
        n_ext = len(ext)
        ind = np.zeros((n_ext, len(assays)), dtype=np.float32)
        for j, aid in enumerate(assays):
            ind[ext.assay_id.to_numpy() == aid, j] = 1.0
        Xc_ind = np.hstack([X_tr, np.zeros((len(clean), len(assays)), dtype=np.float32)])
        yc_ind = y_tr
        Xcal = np.hstack([X_ext[all_cal], ind[all_cal]])
        ycal = y_ext[all_cal]
        mC = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=10.0))
        mC.fit(np.vstack([Xc_ind, Xcal]), np.concatenate([yc_ind, ycal]))
        p_ind = mC.predict(np.hstack([X_ext, ind]))
        # E: pooled ridge (canonical + cal, no indicators)
        mE = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=10.0))
        mE.fit(np.vstack([X_tr, X_ext[all_cal]]), np.concatenate([y_tr, y_ext[all_cal]]))
        p_pool = mE.predict(X_ext)
        # metrics per assay-test and pooled (test rows only)
        test_mask = np.zeros(n_ext, bool)
        for aid in assays:
            test_mask |= (ext.assay_id.to_numpy() == aid) & np.isin(np.arange(n_ext), cal_idx_by_assay[aid][1])
        for aid in assays:
            _, ti = cal_idx_by_assay[aid]
            for meth, p in [("none_canonical_only", p_none), ("cal_mean_baseline", p_cm), ("A_assay_offset", p_off),
                            ("B_assay_linear", p_lin), ("C_indicator_ridge", p_ind), ("D_shrunk_offset", p_shr),
                            ("E_pool_ridge", p_pool)]:
                r = metrics(y_ext[ti], p[ti])
                r.update({"method": meth, "assay_id": aid, "seed": seed, "n_cal": int(len(cal_idx_by_assay[aid][0])),
                          "n_test": int(len(ti))})
                cal_rows.append(r)
        for meth, p in [("none_canonical_only", p_none), ("cal_mean_baseline", p_cm), ("A_assay_offset", p_off),
                        ("B_assay_linear", p_lin), ("C_indicator_ridge", p_ind), ("D_shrunk_offset", p_shr),
                        ("E_pool_ridge", p_pool)]:
            r = metrics(y_ext[test_mask], p[test_mask])
            r.update({"method": meth, "assay_id": "POOLED", "seed": seed, "n_cal": int(len(all_cal)),
                      "n_test": int(test_mask.sum())})
            cal_rows.append(r)
    cal = pd.DataFrame(cal_rows)
    cal.to_csv(OUT / "FASN_assay_calibration_results.csv", index=False, encoding="utf-8-sig")
    cal_agg = cal.groupby(["method", "assay_id"]).agg(
        seeds=("seed", "nunique"), n_test=("n_test", "first"), n_cal=("n_cal", "first"),
        r2_med=("r2", "median"), r2_min=("r2", "min"), r2_max=("r2", "max"),
        mae_med=("mae", "median"), rmse_med=("rmse", "median"),
        rho_med=("spearman", "median"), rho_min=("spearman", "min"), rho_max=("spearman", "max"),
        bias_med=("bias", "median")).reset_index()
    cal_agg.to_csv(OUT / "derived/FASN_assay_calibration_aggregated.csv", index=False, encoding="utf-8-sig")

    # ================= 5) NP54 domain status v2 =================
    lib = pd.read_csv(LIB54)
    libfps = [fp(s) for s in lib.smiles]
    np_rows = []
    for i, r in lib.iterrows():
        f = libfps[i]
        sim = float(max(DataStructs.BulkTanimotoSimilarity(f, train_fps))) if f else np.nan
        np_rows.append({"herb": r.herb, "name": r["name"], "max_Tanimoto_to_canonical": sim,
                        "ad_threshold_loo5pct": ad_thr,
                        "ad_status": "in_domain" if sim >= ad_thr else "out_of_domain",
                        "bridge_extended_training_note": "no; bridge molecules (phloretin/asiatic acid/quercetin/kaempferol/cerulenin/thiolactomycin etc.) are not members of NP54 and bridge set is too small to retrain"})
    np54 = pd.DataFrame(np_rows)
    np54.to_csv(OUT / "NP54_domain_status_v2.csv", index=False, encoding="utf-8-sig")

    summary = {"env": env,
               "assay_aware_master_rows": int(len(aw)),
               "assay_cluster_counts": aw.assay_cluster.value_counts().to_dict(),
               "confidence_counts": aw.confidence_level.value_counts().to_dict(),
               "external": {"pool": int(len(pool.groupby('molecule_id'))), "excluded_overlap": int(len(excluded)),
                            "evaluated": int(len(ext)), "strata": ext.stratum.value_counts().to_dict(),
                            "ad": ext.ad_status.value_counts().to_dict(),
                            "E5_candidates": int(ext.E5_candidate.sum()),
                            "excluded_ids": excluded.molecule_id.tolist()},
               "conformal": {"q10": q10, "q20": q20}, "ad_threshold": ad_thr,
               "stratified": strat.to_dict("records"),
               "calibration_aggregated": cal_agg.to_dict("records"),
               "np54": {"n": int(len(np54)), "in_domain": int((np54.ad_status == "in_domain").sum()),
                        "median_sim": float(np54.max_Tanimoto_to_canonical.median()),
                        "max_sim": float(np54.max_Tanimoto_to_canonical.max())}}
    (OUT / "derived/advancement_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (OUT / "logs/run_advancement_fasn.log").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"stratified": strat.to_dict("records"),
                      "calibration_pooled": cal_agg[cal_agg.assay_id == "POOLED"].to_dict("records"),
                      "calibration_E1": cal_agg[cal_agg.assay_id == "CHEMBL4123591"].to_dict("records"),
                      "calibration_5730715": cal_agg[cal_agg.assay_id == "CHEMBL5730715"].to_dict("records"),
                      "np54": summary["np54"], "ad_thr": ad_thr, "q10": q10, "q20": q20},
                     ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
