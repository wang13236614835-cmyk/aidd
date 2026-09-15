# 第五轮方向探索 QC 报告

**判定：PASS**（0 项问题）

## 检查项

- required_outputs: {'count': 13, 'missing': []}
- t1_counts: {'all_assay_pairs': 1275, 'shared_ge15': 4, 'comparable_ge15': 1, 'transformations': 1, 'stable_transformations': 1}
- leakage: {'exact_duplicate_count': 0, 'canonical_overlap_count': 0, 'scaffold_overlap_rate': 0.0, 'scaffold_overlap_count_across_10_seeds': 0, 'stereoisomer_overlap_count': 0, 'assay_mirror_overlap_count': 89, 'external_overlap_count': 3, 'near_duplicate_count': 82, 'near_duplicate_rate': 0.8541666666666666, 'chemical_series_confinement_count': 82, 'chemical_series_confinement_rate': 0.8541666666666666, 'leakage_definition': '仅 exact structure/canonical duplicate、scaffold cross-split、复制记录跨集计 leakage；高相似 NN>=0.85 且无上述跨集重复计 chemical-series confinement。', 'verdict': 'PASS'}
- data_audit: {'master_records': 1652, 'master_molecules': 1139, 'assays': 51, 'activity_types': {'IC50': 1630, 'Ki': 20, 'Kd': 2}, 'protein_layers': {'cell_extract': 1140, 'full_length': 302, 'unknown': 184, 'fragment_TE': 24, 'fragment_KR': 2}}
- direction_matrix: {'rows': 9, 'roles': ['Methodology', 'Primary', 'Rejected', 'Reserve', 'Secondary']}
- main_state: {'project_stage': 'fifth_round_direction_exploration', 'current_stage': '第五轮方向探索（FASN Gate T1已裁决）', 'fasn_gate_t1_decision': 'FAIL', 'gnn_gate': 'closed', 'candidate_release': False, 'primary': 'Moracin N–NRF2/ferroptosis肝细胞机制验证'}
- protected_inputs_exist: True