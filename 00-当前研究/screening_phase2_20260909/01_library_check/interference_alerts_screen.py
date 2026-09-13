# -*- coding: utf-8 -*-
"""Local structural-alert / physicochemical screen for all 54 library compounds.

TRANSPARENT SCOPE: rules below are a locally curated set informed by REOS/Brenk-
style alert chemotypes (quinones, catechols, Michael acceptors, aldehydes,
epoxides, reactive halides, sulfonates; plus polyphenol count as an aggregator
risk LINE). This is NOT the full PAINS A/B/C filter and NOT the ZINC aggregator
database; online FAF-Drugs4 / Aggregator Advisor comparison remains pending.
Alerts are risk leads only - they do not demonstrate assay interference.
"""
import csv, json
from pathlib import Path
from rdkit import Chem, RDLogger
from rdkit.Chem import Crippen, Descriptors, rdMolDescriptors
from rdkit.Chem import rdMolDescriptors as _rmd

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
LIB = Path(r"D:\zcode-workspace\aidd-repo-work\03-课题-MASH研究-v2\data\tcm\np_library_filtered.csv")

ALERTS = {
    "quinone": "[#6]1=[#6](~[#8])~[#6](~[#8])=[#6]~[#6]=1",          # p-quinone core (approximate)
    "catechol": "[#6]1~[#6]([OH])~[#6]([OH])~[#6]~[#6]~1",            # ortho-diphenol
    "Michael_acceptor_enone_rough": "[#6]=[#6]-[#6]=[#8]",            # alpha,beta-unsat carbonyl (rough, overmatches)
    "aldehyde": "[CH2]=[O]",                                          # CHO (rough)
    "epoxide_3ring": "[C;r3]1[C;r3][O;r3]1",
    "reactive_halide_aryl": "[c][Cl,Br,I]",
    "sulfonate_ester_rough": "S(=O)(=O)O[C,N]",
}
smart = {k: Chem.MolFromSmarts(v) for k, v in ALERTS.items()}

def main():
    rows = list(csv.DictReader(open(LIB, encoding="utf-8")))
    out = []
    for r in rows:
        m = Chem.MolFromSmiles(r["smiles"].strip())
        phenol = len(r["smiles"]) # placeholder
        n_oh_ar = sum(1 for a in m.GetAtoms() if a.GetSymbol() == "O" and any(n.GetSymbol() == "H" or n.GetTotalNumHs() for n in a.GetNeighbors()))
        hits = [k for k, s in smart.items() if s is not None and m.HasSubstructMatch(s)]
        arom_oh = sum(1 for a in m.GetAtoms()
                      if a.GetSymbol() == "O" and a.GetTotalNumHs() == 1
                      and any(n.GetIsAromatic() for n in a.GetNeighbors()))
        out.append(dict(
            name=r["name"].strip(), herb=r["herb"], smiles=r["smiles"].strip(),
            mw=round(Descriptors.MolWt(m), 1), clogp=round(Crippen.MolLogP(m), 2),
            hbd=rdMolDescriptors.CalcNumHBD(m), hba=rdMolDescriptors.CalcNumHBA(m),
            rotb=rdMolDescriptors.CalcNumRotatableBonds(m), tpsa=round(rdMolDescriptors.CalcTPSA(m), 1),
            aromatic_oh_count=arom_oh,
            structural_alerts=";".join(hits) if hits else "",
            polyphenol_ge4_line="aromatic-OH>=4 (aggregator/autotoxidation risk line, not proof)" if arom_oh >= 4 else "",
            lipid_like_triterpene_line="triterpene/lipid-like (solubility&assay-artifact risk line)" if rdMolDescriptors.CalcNumRotatableBonds(m) <= 3 and Descriptors.MolWt(m) > 400 and Crippen.MolLogP(m) > 6 else "",
            note="alerts=risk leads only; NOT full PAINS; aggregator DB comparison pending"))
    with open(HERE / "interference_alerts_screen.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    flagged = {r["name"]: r["structural_alerts"] for r in out if r["structural_alerts"]}
    poly = [r["name"] for r in out if r["polyphenol_ge4_line"]]
    print(f"structural alerts flagged: {len(flagged)}/{len(out)}")
    for k, v in sorted(flagged.items()):
        print(f"  {k:<24s} {v}")
    print(f"\naromatic-OH>=4 risk line: {poly}")
    (HERE / "interference_alerts_meta.json").write_text(json.dumps(dict(
        rdkit_version="2026.03.3 (validated env)", rule_source="locally curated, REOS/Brenk-informed chemotypes; NOT full PAINS A/B/C",
        rules=ALERTS, scope_limit="no online FAF-Drugs4; no ZINC aggregator DB; alerts are risk leads not interference proof",
        n_flagged=len(flagged)), ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
