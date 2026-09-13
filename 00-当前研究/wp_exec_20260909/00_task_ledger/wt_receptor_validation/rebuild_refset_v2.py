"""Ruling item 2: rebuild TR reference set at RECORD level (no aggregation loss).

Keeps per-record: activity_id, assay_chembl_id, assay description, document, type,
relation, value+units (nM enforced), molecule. Dedup summary derived separately.
Ruling item 3: metric utilities with fixed conventions + synthetic self-tests."""
import json, time, urllib.request

def fetch(url, retries=3):
    for i in range(retries):
        try:
            return json.load(urllib.request.urlopen(url, timeout=60))
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(3)

TYPES = {'Ki', 'IC50', 'Kd', 'EC50', 'AC50'}
out = {}
for tid, name in [('CHEMBL1947', 'TRB_human'), ('CHEMBL1860', 'TRA_human')]:
    records = []
    nrec = 0
    for offset in range(0, 3000, 1000):
        d = fetch(f'https://www.ebi.ac.uk/chembl/api/data/activity.json?target_chembl_id={tid}&limit=1000&offset={offset}')
        acts = d['activities']
        nrec += len(acts)
        for a in acts:
            st, rel, val, units = a.get('standard_type'), a.get('standard_relation'), a.get('standard_value'), a.get('standard_units')
            if st not in TYPES or val is None:
                continue
            try:
                val = float(val)
            except (TypeError, ValueError):
                continue
            if units != 'nM':          # unit guard: keep nM only
                continue
            records.append({
                'activity_id': a.get('activity_id'),
                'assay_chembl_id': a.get('assay_chembl_id'),
                'assay_descr': (a.get('assay_description') or '')[:160],
                'doc': a.get('document_chembl_id'),
                'molecule': a.get('molecule_chembl_id'),
                'type': st, 'relation': rel, 'value_nM': val,
                'target': name,
            })
        if len(acts) < 1000:
            break
    out[name] = {'scanned': nrec, 'records_kept_nM': len(records), 'records': records}
    print(name, 'scanned', nrec, 'kept', len(records))

json.dump(out, open(r'D:\zcode-workspace\p0_refs\chembl_tr_records_v2.json', 'w'))

# ---- metric utilities, fixed conventions (ruling item 3) ----
def auc_neg_active(pos_scores, neg_scores):
    """All scores use 'more negative = more active' convention throughout.
    AUC = P(pos more negative than neg) + 0.5 P(equal). NO sign flips anywhere."""
    if not pos_scores or not neg_scores:
        raise ValueError('empty set')
    c = sum(1 for a in pos_scores for b in neg_scores if a < b)
    t = sum(1 for a in pos_scores for b in neg_scores if a == b)
    return (c + 0.5 * t) / (len(pos_scores) * len(neg_scores))

def enrichment_topk(pos_scores, neg_scores, k=15):
    """EF@Top-K with documented tie rule: threshold = k-th best score overall,
    include ALL entries with score <= threshold (ties in). Report denominator k_eff
    = number of entries actually ranked above threshold (>= k)."""
    allsc = sorted(pos_scores + neg_scores)
    if k > len(allsc):
        raise ValueError('k too large')
    cut = allsc[k - 1]
    top = [s for s in allsc if s <= cut]
    hits = sum(1 for s in pos_scores if s <= cut)
    ef = (hits / len(pos_scores)) / (len(top) / len(allsc))
    return {'k': k, 'k_eff': len(top), 'hits': hits, 'EF': ef,
            'EF_max_possible': len(allsc) / len(pos_scores)}

# synthetic self-tests (must pass before any real use)
assert abs(auc_neg_active([-10, -9, -8], [-1, -2, -3]) - 1.0) < 1e-12   # perfect
assert abs(auc_neg_active([-1, -3, -2], [-2, -1, -3]) - 0.5) < 1e-12   # random-ish symmetric
r = enrichment_topk([-10] * 5, [-5] * 5 + [0] * 5, k=5)
# derivation: EF = (hits/P) / (k_eff/N) = (5/5) / (5/15) = 3.0 for perfect separation here
assert r['hits'] == 5 and r['k_eff'] == 5 and abs(r['EF'] - 3.0) < 1e-9, r
print('metric self-tests PASSED (perfect AUC=1, symmetric=0.5, perfect EF=3.0 per derivation)')
