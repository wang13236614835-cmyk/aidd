import json
from pathlib import Path
import pandas as pd

ROOT = Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
DATA = ROOT / 'derived' / 'chembl_numeric_nM_exact_candidates.csv'
df = pd.read_csv(DATA, low_memory=False)

common = {
    'standard_flag': 1,
    'standard_relation': '=',
    'standard_units': 'nM',
    'bao_label': 'single protein format',
    'standard_type': 'IC50',
    'potential_duplicate': 0,
}

def select(target: str, assay: str) -> pd.DataFrame:
    mask = (
        (df['target_label'] == target)
        & (df['assay_chembl_id'] == assay)
        & (df['standard_flag'] == common['standard_flag'])
        & (df['standard_relation'] == common['standard_relation'])
        & (df['standard_units'] == common['standard_units'])
        & (df['bao_label'] == common['bao_label'])
        & (df['standard_type'] == common['standard_type'])
        & (df['potential_duplicate'] == common['potential_duplicate'])
    )
    return df.loc[mask, ['molecule_chembl_id', 'canonical_smiles', 'pActivity_nM', 'standard_value', 'document_chembl_id', 'assay_description']].drop_duplicates('molecule_chembl_id')

beta = select('thrb', 'CHEMBL925135').rename(columns={
    'pActivity_nM': 'pActivity_TRbeta',
    'standard_value': 'value_TRbeta_nM',
    'document_chembl_id': 'document_TRbeta',
    'assay_description': 'assay_description_TRbeta',
})
alpha = select('thra', 'CHEMBL925134').drop(columns=['canonical_smiles']).rename(columns={
    'pActivity_nM': 'pActivity_TRalpha',
    'standard_value': 'value_TRalpha_nM',
    'document_chembl_id': 'document_TRalpha',
    'assay_description': 'assay_description_TRalpha',
})
pair = beta.merge(alpha, on='molecule_chembl_id', how='inner')
pair['delta_pActivity_TRbeta_minus_TRalpha'] = pair['pActivity_TRbeta'] - pair['pActivity_TRalpha']
pair['TRbeta_preferential_delta_ge_0.5'] = (pair['delta_pActivity_TRbeta_minus_TRalpha'] >= 0.5).astype(int)
pair['TRbeta_preferential_delta_ge_1.0'] = (pair['delta_pActivity_TRbeta_minus_TRalpha'] >= 1.0).astype(int)
pair.to_csv(ROOT / 'derived' / 'trb_tra_paired_benchmark.csv', index=False, encoding='utf-8-sig')

summary = {
    'generated_at': '2026-09-10',
    'target_beta': {'chembl_target': 'CHEMBL1947', 'assay': 'CHEMBL925135', 'organism': 'Homo sapiens'},
    'target_alpha': {'chembl_target': 'CHEMBL1860', 'assay': 'CHEMBL925134', 'organism': 'Homo sapiens'},
    'common_document': 'CHEMBL1140629',
    'endpoint': 'IC50',
    'format': 'single protein',
    'n_paired_molecules': int(len(pair)),
    'n_beta_preferential_delta_ge_0.5': int(pair['TRbeta_preferential_delta_ge_0.5'].sum()),
    'n_beta_preferential_delta_ge_1.0': int(pair['TRbeta_preferential_delta_ge_1.0'].sum()),
    'delta_summary': {k: float(v) for k, v in pair['delta_pActivity_TRbeta_minus_TRalpha'].describe().to_dict().items()},
    'limitations': [
        'same ChEMBL document and assay family, but full construct/condition audit remains pending',
        'paired n is small for a robust selectivity model',
        'delta thresholds are assay-specific and not universal receptor-selectivity standards',
        'candidate library has no experimental paired TRalpha/TRbeta labels',
        'not used to claim TRbeta selectivity for any natural product',
    ],
}
(ROOT / 'derived' / 'trb_tra_paired_benchmark_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
