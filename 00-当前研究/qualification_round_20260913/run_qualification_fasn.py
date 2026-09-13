# -*- coding: utf-8 -*-
"""Qualification round Track A: FASN main-axis qualification runs.

Actually executes: canonical QC, clean set build, Model 0-4 baselines on
10 scaffold-split seeds, 20x Y-scrambling, train/test leakage audit,
train/test gap analysis (Ridge vs trees), external validation on
non-canonical full-length assays (mirror assay excluded), split-conformal
UQ, and NP54 domain-gap re-check. No GNN.
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
from sklearn.model_selection import GroupShuffleSplit, GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RDLogger.DisableLog("rdApp.*")
try:
    from xgboost import XGBRegressor
    HAVE_XGB = True
except Exception as exc:
    HAVE_XGB = False
    XGB_ERROR = repr(exc)

ROOT = Path(r"D:/zcode-workspace/aidd-repo-work/00-当前研究")
OUT = ROOT / "qualification_round_20260913"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "derived").mkdir(exist_ok=True); (OUT / "logs").mkdir(exist_ok=True); (OUT / "raw").mkdir(exist_ok=True)
MASTER = ROOT / "final_strategy_round_20260912/FASN_activity_master.csv"
LIB54 = ROOT.parent / "03-课题-MASH研究-v2/data/tcm/np_library_filtered.csv"
CANONICAL_ASSAY = "CHEMBL5731051"
MIRROR_ASSAY = "CHEMBL5734379"
SEEDS = list(range(20260912, 20260922))  # 10 seeds
N_SCRAMBLE = 20
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
    return {"n": int(len(y)), "mae": float(mean_absolute_error(y, p)),
            "rmse": float(mean_squared_error(y, p) ** .5),
            "r2": float(r2_score(y, p)) if len(np.unique(y)) > 1 else None,
            "spearman": float(pd.Series(y).corr(pd.Series(p), method="spearman")) if len(np.unique(p)) > 1 else None}


def build_model(name, seed):
    if name == "mean":
        return DummyRegressor(strategy="mean")
    if name == "desc_ridge":
        return make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=10.0, random_state=None))
    if name == "ecfp_ridge":
        return make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=10.0))
    if name == "ecfp_rf":
        return RandomForestRegressor(n_estimators=700, max_features="sqrt", min_samples_leaf=2, random_state=seed, n_jobs=-1)
    if name == "ecfp_xgb" and HAVE_XGB:
        return XGBRegressor(n_estimators=600, max_depth=5, learning_rate=0.03, subsample=0.8,
                            colsample_bytree=0.7, reg_lambda=2.0, objective="reg:squarederror",
                            random_state=seed, n_jobs=4)
    return None


FEATURE_OF = {"mean": "ecfp", "desc_ridge": "desc", "ecfp_ridge": "ecfp",
              "ecfp_rf": "ecfp", "ecfp_xgb": "ecfp"}
MODELS = ["mean", "desc_ridge", "ecfp_ridge", "ecfp_rf", "ecfp_xgb"]


def main():
    import rdkit, sklearn
    env = {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__,
           "rdkit": getattr(rdkit, "__version__", "2026.03.3"),
           "xgboost": __import__("xgboost").__version__ if HAVE_XGB else None,
           "sklearn": sklearn.__version__, "platform": platform.platform()}
    master = pd.read_csv(MASTER)

    # ---------- 1) Canonical QC ----------
    rec = master[(master.assay_id == CANONICAL_ASSAY) & (master.activity_type == "IC50")
                 & (master.unit.str.lower() == "nm") & (master.relation == "=")
                 & (master.standardized_nM > 0) & (master.is_valid_smiles == 1)].copy()
    rec["pActivity"] = -np.log10(rec.standardized_nM.astype(float) * 1e-9)
    rec["scaffold"] = rec.canonical_smiles.map(scaffold)
    rec["inchikey14"] = rec.inchikey.str.slice(0, 14)
    qc = {"assay_id": CANONICAL_ASSAY, "raw_records": int(len(rec)),
          "distinct_molecules": int(rec.molecule_id.nunique()),
          "documents": sorted(rec.document_id.unique().tolist()),
          "document_year": sorted(rec.document_year.unique().tolist()),
          "units": rec.unit.value_counts().to_dict(),
          "species": rec.species.unique().tolist(),
          "target": sorted(rec.target_id.unique().tolist()),
          "endpoint": rec.activity_type.unique().tolist()}
    # duplicates
    ik_dup = rec.groupby("inchikey").molecule_id.nunique()
    qc["inchikey_duplicate_molecules"] = int((ik_dup > 1).sum())
    smi_dup = rec.groupby("canonical_smiles").molecule_id.nunique()
    qc["duplicate_smiles_groups"] = int((smi_dup > 1).sum())
    # stereoisomer pairs: same first-14 block, different full key
    st_pairs = []
    for k14, g in rec.groupby("inchikey14"):
        if g.inchikey.nunique() > 1:
            st_pairs.append({k14: g.inchikey.unique().tolist()})
    qc["stereoisomer_pairs_within_assay"] = st_pairs
    qc["stereoisomer_pair_count"] = len(st_pairs)
    # fragments / salts
    qc["multi_fragment_records"] = int((rec.fragment_count > 1).sum())
    # replicates
    rep = rec.groupby("molecule_id").size()
    qc["molecules_with_replicate_records"] = int((rep > 1).sum())
    rep_detail = rec[rec.molecule_id.isin(rep[rep > 1].index)][
        ["molecule_id", "activity_id", "standardized_nM", "pActivity"]].to_dict("records")
    qc["replicate_detail"] = rep_detail
    # outliers (robust MAD)
    med = rec.pActivity.median(); mad = (rec.pActivity - med).abs().median() * 1.4826
    lo, hi = med - 3 * mad, med + 3 * mad
    out_rows = rec[(rec.pActivity < lo) | (rec.pActivity > hi)]
    qc["mad3_outlier_records"] = int(len(out_rows))
    qc["mad3_outlier_molecule_ids"] = out_rows.molecule_id.tolist()
    qc["mad3_bounds"] = [float(lo), float(hi)]
    # impossible values
    qc["impossible_records"] = int(((rec.pActivity < 2) | (rec.pActivity > 12)).sum())
    qc["nonpositive_nM"] = int((rec.standardized_nM <= 0).sum())
    # molecule-level clean set (median of replicates; keep outliers with flag)
    clean = rec.groupby("molecule_id", as_index=False).agg(
        canonical_smiles=("canonical_smiles", "first"), inchikey=("inchikey", "first"),
        scaffold=("scaffold", "first"), pActivity=("pActivity", "median"),
        n_records=("activity_id", "size"),
        activity_ids=("activity_id", lambda x: ";".join(str(v) for v in x)),
        document_id=("document_id", "first"), document_year=("document_year", "first"))
    clean["qc_flags"] = ""
    clean.loc[clean.n_records > 1, "qc_flags"] = "replicate_median"
    clean.loc[clean.molecule_id.isin(out_rows.molecule_id), "qc_flags"] += ";mad3_outlier_kept"
    clean.loc[clean.canonical_smiles.map(lambda s: len(Chem.GetMolFrags(Chem.MolFromSmiles(str(s))))) > 1, "qc_flags"] += ";multi_fragment"
    clean["excluded"] = False
    clean["exclusion_reason"] = ""
    qc["clean_molecules"] = int(len(clean)); qc["clean_scaffolds"] = int(clean.scaffold.nunique())
    qc["exclusions"] = []
    clean["pActivity"] = clean.pActivity.astype(float)
    clean.to_csv(OUT / "FASN_canonical_clean.csv", index=False, encoding="utf-8-sig")
    (OUT / "derived/FASN_canonical_qc_checks.json").write_text(json.dumps(qc, ensure_ascii=False, indent=2), encoding="utf-8")

    # features
    smiles = clean.canonical_smiles.tolist(); y = clean.pActivity.to_numpy(float)
    X = {"ecfp": fp_matrix(smiles), "desc": np.asarray([descriptors(s) for s in smiles], float)}
    fps = [fp(s) for s in smiles]

    # ---------- 2) 10-seed scaffold baselines + train/test gap + leakage ----------
    all_rows = []
    leakage_rows = []
    for seed in SEEDS:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
        tr, te = next(gss.split(clean, groups=clean.scaffold))
        tr_s, te_s = set(clean.iloc[tr].scaffold), set(clean.iloc[te].scaffold)
        # leakage stats
        sims = []
        for i in te:
            sims.append(max(DataStructs.BulkTanimotoSimilarity(fps[i], [fps[j] for j in tr])))
        leakage_rows.append({"seed": seed, "train_n": int(len(tr)), "test_n": int(len(te)),
                             "train_scaffolds": len(tr_s), "test_scaffolds": len(te_s),
                             "scaffold_overlap": int(len(tr_s & te_s)),
                             "test_to_train_max_tanimoto": float(np.max(sims)),
                             "test_to_train_mean_nn_tanimoto": float(np.mean(sims)),
                             "n_test_nn_ge_0.85": int(np.sum(np.array(sims) >= 0.85)),
                             "n_test_nn_ge_0.60": int(np.sum(np.array(sims) >= 0.60)),
                             "n_test_nn_ge_0.40": int(np.sum(np.array(sims) >= 0.40))})
        for name in MODELS:
            m = build_model(name, seed)
            if m is None:
                continue
            m.fit(X[FEATURE_OF[name]][tr], y[tr])
            p_te = m.predict(X[FEATURE_OF[name]][te]); p_tr = m.predict(X[FEATURE_OF[name]][tr])
            row = metrics(y[te], p_te)
            row.update({"split": "scaffold", "model": name, "seed": seed,
                        "train_n": int(len(tr)), "val_n": 0, "test_n": int(len(te)),
                        "train_scaffolds": len(tr_s), "test_scaffolds": len(te_s),
                        "train_r2": metrics(y[tr], p_tr)["r2"],
                        "train_test_gap_r2": metrics(y[tr], p_tr)["r2"] - row["r2"],
                        "hyperparams": "fixed:ridge_alpha10;rf700_sqrt_leaf2;xgb600_d5_lr03"})
            all_rows.append(row)
    base = pd.DataFrame(all_rows)
    base.to_csv(OUT / "FASN_baseline_results.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(leakage_rows).to_csv(OUT / "FASN_leakage_audit.csv", index=False, encoding="utf-8-sig")

    def q_summary(g, col):
        return {"median": float(g[col].median()), "q1": float(g[col].quantile(.25)), "q3": float(g[col].quantile(.75)),
                "min": float(g[col].min()), "max": float(g[col].max())}
    summ = []
    sc = base[base.split == "scaffold"]
    for name in MODELS:
        g = sc[sc.model == name]
        if g.empty:
            continue
        summ.append({"model": name, "seeds": int(g.seed.nunique()),
                     "mae": q_summary(g, "mae"), "rmse": q_summary(g, "rmse"),
                     "r2": q_summary(g, "r2"),
                     "spearman": q_summary(g, "spearman"),
                     "train_test_gap_r2": q_summary(g, "train_test_gap_r2")})
    summ_df = pd.DataFrame(summ)
    summ_df.to_csv(OUT / "FASN_10seed_scaffold_results.csv", index=False, encoding="utf-8-sig")

    # ---------- 3) Y-scrambling ----------
    seed0 = SEEDS[0]
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed0)
    tr, te = next(gss.split(clean, groups=clean.scaffold))
    scr_rows = []
    real = {}
    for name in ["ecfp_ridge", "ecfp_rf", "ecfp_xgb"]:
        m = build_model(name, seed0); m.fit(X[FEATURE_OF[name]][tr], y[tr])
        real[name] = metrics(y[te], m.predict(X[FEATURE_OF[name]][te]))
    rng = np.random.default_rng(seed0)
    for k in range(N_SCRAMBLE):
        y_perm = rng.permutation(y)
        for name in ["ecfp_ridge", "ecfp_rf", "ecfp_xgb"]:
            m = build_model(name, seed0); m.fit(X[FEATURE_OF[name]][tr], y_perm[tr])
            p = m.predict(X[FEATURE_OF[name]][te]); mm = metrics(y_perm[te], p)
            scr_rows.append({"model": name, "permutation": k, **mm})
    scr = pd.DataFrame(scr_rows)
    scr.to_csv(OUT / "FASN_y_scrambling_results.csv", index=False, encoding="utf-8-sig")
    ysc = {}
    for name in ["ecfp_ridge", "ecfp_rf", "ecfp_xgb"]:
        g = scr[scr.model == name]
        rr = real[name]["r2"]
        mu, sd = float(g.r2.mean()), float(g.r2.std(ddof=1))
        ysc[name] = {"real_test_r2": rr, "perm_r2_mean": mu, "perm_r2_sd": sd,
                     "perm_r2_max": float(g.r2.max()),
                     "empirical_p_ge_real": float((g.r2 >= rr).mean()),
                     "z_score": float((rr - mu) / sd) if sd and sd > 0 else None,
                     "real_test_spearman": real[name]["spearman"],
                     "perm_spearman_mean": float(g.spearman.mean()),
                     "perm_spearman_max": float(g.spearman.max())}

    # ---------- 4) External set ----------
    ext_pool = master[(master.construct == "full_length_human_FASN_stated_in_assay_description")
                      & (master.activity_type == "IC50") & (master.unit.str.lower() == "nm")
                      & (master.relation == "=") & (master.standardized_nM > 0)
                      & (master.is_valid_smiles == 1)
                      & (~master.assay_id.isin([CANONICAL_ASSAY, MIRROR_ASSAY]))].copy()
    ext_pool["pActivity"] = -np.log10(ext_pool.standardized_nM.astype(float) * 1e-9)
    ext = ext_pool.groupby("molecule_id", as_index=False).agg(
        canonical_smiles=("canonical_smiles", "first"), inchikey=("inchikey", "first"),
        pActivity=("pActivity", "median"), n_records=("activity_id", "size"),
        assay_ids=("assay_id", lambda x: ";".join(sorted(set(x)))),
        documents=("document_id", lambda x: ";".join(sorted(set(x)))),
        years=("document_year", lambda x: ";".join(sorted(set(str(int(v)) for v in x)))),
        assay_format=("assay_format", "first"))
    train_mols = set(clean.molecule_id)
    ext["overlaps_canonical_training"] = ext.molecule_id.isin(train_mols)
    ext_excluded = int(ext.overlaps_canonical_training.sum())
    ext_eval = ext[~ext.overlaps_canonical_training].reset_index(drop=True)
    ext["excluded"] = ext.overlaps_canonical_training
    ext["exclusion_reason"] = np.where(ext.overlaps_canonical_training, "molecule_present_in_canonical_training", "")
    ext.to_csv(OUT / "FASN_external_set.csv", index=False, encoding="utf-8-sig")
    Xe = fp_matrix(ext_eval.canonical_smiles.tolist())
    Xd = np.asarray([descriptors(s) for s in ext_eval.canonical_smiles], float)
    ye = ext_eval.pActivity.to_numpy(float)
    ext_fps = [fp(s) for s in ext_eval.canonical_smiles]

    # internal conformal q via 5-fold grouped CV residuals (ecfp_rf)
    gkf = GroupKFold(n_splits=5)
    resid = []
    for tr_i, cal_i in gkf.split(clean, groups=clean.scaffold):
        m = build_model("ecfp_rf", seed0); m.fit(X["ecfp"][tr_i], y[tr_i])
        resid.extend(np.abs(y[cal_i] - m.predict(X["ecfp"][cal_i])))
    resid = np.sort(np.asarray(resid))
    def cq(alpha):
        r = int(np.ceil((len(resid) + 1) * (1 - alpha))) - 1
        return float(resid[min(max(r, 0), len(resid) - 1)])
    q10, q20 = cq(0.10), cq(0.20)

    # training LOO-NN similarity AD threshold
    loo = []
    for i in range(len(fps)):
        loo.append(max(DataStructs.BulkTanimotoSimilarity(fps[i], [fps[j] for j in range(len(fps)) if j != i])))
    ad_thr = float(np.quantile(loo, 0.05))

    ext_rows = []
    for name in MODELS:
        m = build_model(name, seed0)
        if m is None:
            continue
        m.fit(X[FEATURE_OF[name]], y)
        p = m.predict(Xd if FEATURE_OF[name] == "desc" else Xe)
        row = metrics(ye, p); row["model"] = name
        row["bias_pred_minus_true"] = float(np.mean(p - ye))
        if name == "ecfp_rf":
            trees = np.vstack([t.predict(Xe) for t in m.estimators_]); sd = trees.std(axis=0)
        else:
            sd = np.full(len(ye), np.nan)
        row["coverage_q10"] = float(np.mean((ye >= p - q10) & (ye <= p + q10)))
        row["coverage_q20"] = float(np.mean((ye >= p - q20) & (ye <= p + q20)))
        ext_rows.append(row)
        if name in ("ecfp_ridge", "ecfp_xgb", "ecfp_rf"):
            for aid in sorted(set(";".join(ext_eval.assay_ids).split(";"))):
                mask = ext_eval.assay_ids.str.contains(aid).to_numpy()
                if mask.sum() > 0:
                    r = metrics(ye[mask], p[mask]); r.update({"model": name, "assay_id": aid, "n": int(mask.sum())})
                    ext_rows.append({**r, "by": "assay"})
    ext_perf = pd.DataFrame([r for r in ext_rows if "by" not in r])
    ext_perf.to_csv(OUT / "derived/FASN_external_validation_metrics.csv", index=False, encoding="utf-8-sig")
    # external AD and per-molecule predictions (champion = best scaffold median r2 model)
    champion = summ_df.sort_values([("r2", "median")] if isinstance(summ_df.columns[0], tuple) else "r2", ).iloc[0]["model"] if False else None
    # simpler: pick champion by median scaffold r2
    med = {s["model"]: s["r2"]["median"] for s in summ}
    champ = max(med, key=med.get)
    mch = build_model(champ, seed0); mch.fit(X[FEATURE_OF[champ]], y)
    pch = mch.predict(Xe)
    if champ == "ecfp_rf":
        trees = np.vstack([t.predict(Xe) for t in mch.estimators_]); sd_ch = trees.std(axis=0)
    else:
        sd_ch = np.full(len(ye), np.nan)
    ext_pred = pd.DataFrame({"molecule_id": ext_eval.molecule_id, "assay_ids": ext_eval.assay_ids,
                             "true_pActivity": ye, "prediction": pch, "uncertainty_tree_sd": sd_ch,
                             "max_Tanimoto_to_training": [float(max(DataStructs.BulkTanimotoSimilarity(f, fps))) for f in ext_fps]})
    ext_pred["AD_threshold_loo5pct"] = ad_thr
    ext_pred["AD_status"] = np.where(ext_pred.max_Tanimoto_to_training >= ad_thr, "in_domain", "out_of_domain")
    ext_pred["model"] = champ
    ext_pred.to_csv(OUT / "derived/FASN_external_predictions_AD.csv", index=False, encoding="utf-8-sig")

    # ---------- 5) NP54 domain gap ----------
    lib = pd.read_csv(LIB54)
    libfps = [fp(s) for s in lib.smiles]
    np_max = [float(max(DataStructs.BulkTanimotoSimilarity(f, fps))) if f else np.nan for f in libfps]
    np_out = pd.DataFrame({"herb": lib.herb, "name": lib["name"], "max_Tanimoto_to_canonical_training": np_max})
    np_out["AD_threshold_loo5pct"] = ad_thr
    np_out["AD_status"] = np.where(np_out.max_Tanimoto_to_canonical_training >= ad_thr, "in_domain", "out_of_domain")
    np_out.to_csv(OUT / "derived/NP54_FASN_domain_gap.csv", index=False, encoding="utf-8-sig")
    np_stat = {"n": int(len(np_out)), "min": float(np.nanmin(np_max)), "median": float(np.nanmedian(np_max)),
               "max": float(np.nanmax(np_max)), "n_in_domain": int((np_out.AD_status == "in_domain").sum()),
               "ad_threshold": ad_thr, "training_loo_nn_median": float(np.median(loo))}

    # ---------- summary ----------
    summary = {"date": "2026-09-13", "environment": env, "xgboost_available": HAVE_XGB,
               "canonical_qc": qc, "n_seeds": len(SEEDS), "scaffold_summary": summ,
               "y_scrambling": ysc, "leakage": leakage_rows,
               "external": {"pool_molecules": int(len(ext)), "excluded_overlap": ext_excluded,
                            "evaluated": int(len(ext_eval)),
                            "assays": sorted(set(";".join(ext_eval.assay_ids).split(";"))),
                            "metrics": ext_perf.to_dict("records"),
                            "mirror_assay_excluded": MIRROR_ASSAY,
                            "conformal_q10": q10, "conformal_q20": q20},
               "np54": np_stat, "champion_model": champ,
               "gating": {"gnn_trained": False}}
    (OUT / "derived/qualification_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (OUT / "logs/run_qualification_fasn.log").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"scaffold_summary": summ, "y_scrambling": ysc, "external": summary["external"]["metrics"],
                      "external_meta": {k: summary["external"][k] for k in ["pool_molecules", "excluded_overlap", "evaluated", "assays", "conformal_q10", "conformal_q20"]},
                      "np54": np_stat, "champion": champ, "qc": {k: qc[k] for k in ["raw_records", "distinct_molecules", "clean_molecules", "clean_scaffolds", "molecules_with_replicate_records", "mad3_outlier_records", "impossible_records", "stereoisomer_pair_count", "inchikey_duplicate_molecules", "multi_fragment_records"]},
                      "leakage_max_of_max": float(np.max([r["test_to_train_max_tanimoto"] for r in leakage_rows])),
                      "leakage_mean_nn_median": float(np.median([r["test_to_train_mean_nn_tanimoto"] for r in leakage_rows]))},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
