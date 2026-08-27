# -*- coding: utf-8 -*-
"""
Step 0 (v2): GSE135251 (RNA-seq, 216 liver biopsies, Govaere/Suppli 2019-2021,
Sci Transl Med 2020 PMID:33268509) -> DEG analysis validating MASH targets.
Groups from series matrix: Normal / NAFL / NASH_F0-F1 / NASH_F2 / NASH_F3(-4).
Method: per-sample counts -> gene matrix -> filter -> DESeq2-style median-ratio
size factors -> log1p -> Welch t-test + BH FDR. KEGG ORA via live REST.
Targets: NR1H4(FXR) THRB(THRb) ACACA/ACACB(ACC) + controls.
"""
import glob, gzip, io, json, os, re, tarfile, urllib.request
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

D = "D:/zcode-workspace/mash_research"
GEO = f"{D}/data/geo"
RES = f"{D}/results"

# ---------- 1. extract RAW.tar ----------
tar_path = f"{GEO}/GSE135251_RAW.tar"
exdir = f"{GEO}/raw"
if not os.path.isdir(exdir) or not os.listdir(exdir):
    os.makedirs(exdir, exist_ok=True)
    with tarfile.open(tar_path) as tf:
        tf.extractall(exdir)
files = sorted(glob.glob(f"{exdir}/*"))
print("extracted files:", len(files), "| example:", os.path.basename(files[0]))
print("first file preview:")
with open(files[0], "rt", encoding="utf-8", errors="ignore") as f:
    for i, line in enumerate(f):
        print("   ", line.rstrip()[:80])
        if i >= 4: break

# ---------- 2. parse series matrix metadata ----------
txt = gzip.open(f"{GEO}/GSE135251_series_matrix.txt.gz", "rt",
                encoding="utf-8", errors="ignore").read()
samples, chars = None, {}
for line in txt.splitlines():
    if line.startswith("!Sample_geo_accession"):
        samples = [x.strip('"') for x in line.split("\t")[1:]]
    elif line.startswith("!Sample_characteristics_ch1"):
        vals = [x.strip('"') for x in line.split("\t")[1:]]
        key = re.sub(r":.*$", "", vals[0]).strip()
        chars[key] = [re.sub(r"^[^:]*:\s*", "", v).strip() for v in vals]
meta = pd.DataFrame(chars, index=samples)
print("\nmetadata fields:", list(meta.columns))
print(meta[[c for c in meta.columns if "group" in c or "fibrosis" in c][0]].value_counts())

# ---------- 3. count matrix (cached if available) ----------
CACHE = f"{GEO}/count_matrix_raw.csv.gz"
if os.path.exists(CACHE):
    count = pd.read_csv(CACHE, index_col=0)
    print("loaded cached count matrix:", count.shape)
else:
    count = None

def read_count(path):
    if path.endswith(".gz"):
        f = gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    else:
        f = open(path, "rt", encoding="utf-8", errors="ignore")
    header = f.readline().rstrip("\n").split("\t")
    gene_col = 0
    for i, h in enumerate(header):
        if "gene" in h.lower() or "ensembl" in h.lower() or "symbol" in h.lower():
            gene_col = i; break
    cnt_col = len(header) - 1
    for i, h in enumerate(header):
        if "count" in h.lower() or "htseq" in h.lower():
            cnt_col = i; break
    d = {}
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) <= max(gene_col, cnt_col):
            continue
        try:
            d[parts[gene_col]] = int(float(parts[cnt_col]))
        except ValueError:
            continue
    f.close()
    return d

# map GSM -> file
gsm2file = {}
for fp in files:
    base = os.path.basename(fp)
    m = re.match(r"(GSM\d+)", base)
    if m:
        gsm2file[m.group(1)] = fp
print("\nGSM files matched:", len(gsm2file), "/", len(samples))

gsm_order = [s for s in samples if s in gsm2file]
mats, genes_ref = {}, None
for s in gsm_order:
    d = read_count(gsm2file[s])
    mats[s] = d
all_genes = sorted(set().union(*[set(d) for d in mats.values()]))
print("genes union:", len(all_genes))
count = pd.DataFrame(0, index=all_genes, columns=gsm_order, dtype=np.int64)
for s in gsm_order:
    for g, v in mats[s].items():
        count.loc[g, s] = v
count.to_csv(f"{GEO}/count_matrix_raw.csv.gz", compression="gzip")
print("count matrix:", count.shape)

# Ensembl -> symbol mapping via live BioMart/MyGene? use static gtf-less approach:
# keep as-is; files likely carry gene symbols already (check first-file preview).
# If IDs look like ENSG, map via BioMart REST.
MAP_CACHE = f"{GEO}/ensembl2symbol.tsv"
if re.match(r"ENSG\d+", all_genes[0]):
    print("Ensembl IDs detected")
    # filter FIRST in Ensembl space (symbols not needed for filtering)
    libsize0 = count.sum(0)
    keep = (count / (libsize0 / 1e6)).ge(1).sum(1) >= 10
    ens_ids_to_map = [g.split(".")[0] for g in count.index[keep]]
    print(f"CPM-filtered genes to map: {len(ens_ids_to_map)}")
    if os.path.exists(MAP_CACHE):
        pairs = [l.rstrip("\n").split("\t") for l in open(MAP_CACHE) if "\t" in l]
        idx_map_full = {a: b for a, b in pairs}
    else:
        import requests, time
        e2sym = {}
        B = 10000
        for bi in range(0, len(ens_ids_to_map), B):
            chunk = ens_ids_to_map[bi:bi + B]
            rj = requests.post("https://rest.uniprot.org/idmapping/run",
                               data={"from": "Ensembl", "to": "UniProtKB",
                                     "ids": ",".join(chunk)}, timeout=120)
            jid = rj.json()["jobId"]
            print(f"  batch {bi//B+1}: job {jid}")
            for _ in range(120):
                st = requests.get(f"https://rest.uniprot.org/idmapping/status/{jid}",
                                  timeout=60).json()
                if st.get("jobStatus") == "FINISHED":
                    break
                if "errorMessage" in st or st.get("jobStatus") == "ERROR":
                    print("  job error:", st); break
                time.sleep(3)
            res = requests.get(
                f"https://rest.uniprot.org/idmapping/uniprotkb/results/stream/{jid}",
                params={"format": "tsv", "fields": "accession,gene_primary", "size": 500},
                timeout=600)
            for line in res.text.splitlines()[1:]:
                parts = line.split("\t")
                if len(parts) >= 3 and parts[2].strip():
                    e2sym[parts[0]] = parts[2].split(";")[0].split(",")[0].strip()
            print(f"  mapped so far: {len(e2sym)}")
        with open(MAP_CACHE, "w") as f:
            for k, v in e2sym.items():
                f.write(f"{k}\t{v}\n")
        idx_map_full = e2sym
    idx_map = {g: idx_map_full[g.split(".")[0]] for g in count.index
               if g.split(".")[0] in idx_map_full}
    print(f"UniProt mapping covers {len(idx_map)}/{len(count)} genes")
    count = count[count.index.isin(idx_map.keys())].copy()
    count.index = [idx_map[i] for i in count.index]
    count = count.groupby(level=0).sum()
    count.to_csv(CACHE)  # cache symbol-level matrix
    print("after symbol mapping:", count.shape)

# ---------- 4. DESeq2-style normalization ----------
meta2 = meta.loc[gsm_order]
libsize = count.sum(0)
count_f = count.loc[(count / (libsize / 1e6)).ge(1).sum(1) >= 10]  # CPM>=1 in >=10 samples
print("genes after CPM filter:", count_f.shape[0])
# median-of-ratios size factors
gm = np.exp(np.log(count_f.replace(0, np.nan)).mean(1))
ratios = count_f.divide(gm, axis=0)
sf = ratios.median(0).fillna(1)
norm = count_f.divide(sf, axis=1)
logn = np.log2(norm + 1)
logn.to_csv(f"{GEO}/lognorm_matrix.csv.gz", compression="gzip")

group_col = [c for c in meta2.columns if "group in paper" in c][0]
grp = meta2[group_col]
print("\ngroup counts:\n", grp.value_counts())
normal = grp[grp.str.upper().str.contains("NORMAL|HEALTHY|CONTROL")].index
nash = grp[grp.str.startswith("NASH")].index
nafl = grp[grp == "NAFL"].index
print(f"Normal={len(normal)} NAFL={len(nafl)} NASH={len(nash)}")

def welch_ttest_mat(A, B):
    """A, B: (n_genes, n_a) vs (n_genes, n_b) -> t, p (Welch, vectorized)"""
    na, nb = A.shape[1], B.shape[1]
    ma, mb = A.mean(1), B.mean(1)
    va, vb = A.var(1, ddof=1), B.var(1, ddof=1)
    se2 = va / na + vb / nb
    t = (ma - mb) / np.sqrt(se2)
    df = se2 ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    p = 2 * stats.t.sf(np.abs(t), df)
    return t, p

def deg(a_ids, b_ids, label):
    A, B = logn[list(a_ids)].values, logn[list(b_ids)].values
    t, p = welch_ttest_mat(A, B)
    padj = multipletests(p, method="fdr_bh")[1]
    res = pd.DataFrame({"log2FC": A.mean(1) - B.mean(1), "p": p, "padj": padj},
                       index=logn.index)
    res.to_csv(f"{GEO}/deg_{label}.csv")
    sig = res[(res.padj < 0.05) & (res.log2FC.abs() > 0.5)]
    print(f"[{label}] DEGs: {len(sig)} (up {(sig.log2FC>0).sum()} / down {(sig.log2FC<0).sum()})")
    return res

res1 = deg(list(nash), list(normal), "NASH_vs_Normal")
res2 = deg(list(grp[grp.str.startswith("NASH_F3")].index) +
           list(grp[grp.str.startswith("NASH_F4")].index),
           list(normal), "advFibrosis_vs_Normal")

# ---------- 5. target genes ----------
fib_col = [c for c in meta2.columns if "fibrosis" in c][0]
fib = meta2[fib_col].astype(float)
TARGETS = {"NR1H4": "FXR(main)", "THRB": "THR-b", "ACACA": "ACC1", "ACACB": "ACC2",
           "PPARA": "PPARa(+ctrl)", "SREBF1": "SREBP1c(+ctrl)", "FASN": "FASN(+ctrl)",
           "CYP7A1": "FXR-downstream", "ABCB11": "FXR-downstream(BSEP)",
           "COL1A1": "fibrosis(+ctrl)", "ACTA2": "fibrosis(+ctrl)",
           "TIMP1": "fibrosis(+ctrl)", "TNF": "inflam(+ctrl)", "IL6": "inflam(+ctrl)"}
rows = []
for g, note in TARGETS.items():
    if g not in res1.index:
        rows.append(dict(gene=g, role=note)); continue
    r = res1.loc[g]
    r2 = res2.loc[g] if g in res2.index else None
    tr = stats.spearmanr(fib, logn.loc[g, fib.index]).statistic if g in logn.index else np.nan
    rows.append(dict(gene=g, role=note,
                     log2FC=round(r.log2FC, 3), padj=f"{r.padj:.2e}",
                     log2FC_advF=round(r2.log2FC, 3) if r2 is not None else None,
                     padj_advF=f"{r2.padj:.2e}" if r2 is not None else None,
                     spearman_vs_fibrosis=round(float(tr), 3) if np.isfinite(tr) else None))
tg = pd.DataFrame(rows)
tg.to_csv(f"{RES}/tables/target_genes_validation.csv", index=False)
print("\n=== TARGET GENES (NASH vs Normal) ===")
print(tg.to_string(index=False))

# ---------- 6. KEGG ORA ----------
sig_genes = set(res1[(res1.padj < 0.05) & (res1.log2FC.abs() > 0.5)].index)
print(f"\nORA universe n={len(set(logn.index))}, DEGs n={len(sig_genes)}")
links = urllib.request.urlopen("https://rest.kegg.jp/link/pathway/hsa", timeout=180)
m2p_entrez = {}
for line in links:
    g, p = line.decode().split()
    m2p_entrez.setdefault(p.split(":")[1], set()).add(g.split(":")[1])
# KEGG entrez -> symbol via NCBI EUtils (KEGG list/hsa returns genome view now)
t2s = {}
entrez_needed = sorted({t for gset in m2p_entrez.values() for t in gset})
print(f"entrez ids to symbolize: {len(entrez_needed)}")
import requests, time
for i in range(0, len(entrez_needed), 200):
    chunk = entrez_needed[i:i + 200]
    r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                     params={"db": "gene", "id": ",".join(chunk), "retmode": "json"},
                     timeout=60)
    try:
        res = r.json().get("result", {})
        for uid in res.get("uids", []):
            nm = res[uid].get("name", "")
            if nm:
                t2s[uid] = nm
    except Exception:
        pass
    time.sleep(0.4)
print(f"symbols resolved: {len(t2s)}")
m2p = {pid: {t2s[t] for t in gset if t in t2s} for pid, gset in m2p_entrez.items()}
pnames = {}
for line in urllib.request.urlopen("https://rest.kegg.jp/list/pathway/hsa", timeout=60):
    parts = line.decode().rstrip("\n").split("\t")
    if len(parts) < 2 or ":" not in parts[0]:
        continue
    pnames[parts[0].split(":")[1]] = parts[1].split(" - ")[0]
universe = set(logn.index) & set().union(*m2p.values())
N = len(universe)
enr = []
for pid, gset in m2p.items():
    ov = (sig_genes & gset & universe)
    if len(ov) < 5:
        continue
    K = len(gset & universe)
    pval = stats.hypergeom.sf(len(ov) - 1, N, K, len(sig_genes & universe))
    enr.append(dict(pathway=pid, name=pnames.get(pid, pid), overlap=len(ov), size=K, p=pval))
enr = pd.DataFrame(enr)
enr["padj"] = multipletests(enr.p, method="fdr_bh")[1]
enr.sort_values("p").head(25).to_csv(f"{RES}/tables/kegg_ora_top25.csv", index=False)
print(enr.sort_values("p").head(15).to_string(index=False))

json.dump(dict(dataset="GSE135251", n_normal=int(len(normal)), n_nafl=int(len(nafl)),
               n_nash=int(len(nash)), n_deg=int(len(sig_genes))),
          open(f"{RES}/tables/geo_summary.json", "w"), indent=2)
print("\nGEO stage complete.")
