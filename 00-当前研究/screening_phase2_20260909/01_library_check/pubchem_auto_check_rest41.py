# -*- coding: utf-8 -*-
"""Tier-A PubChem check for the REMAINING 41 library compounds (54 total - 13 hits).
Same criteria as the 13-hit run: formula + isomeric-SMILES identity.
"""
import csv, json, time, urllib.parse, urllib.request
from pathlib import Path
from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolDescriptors

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
LIB = Path(r"D:\zcode-workspace\aidd-repo-work\03-课题-MASH研究-v2\data\tcm\np_library_filtered.csv")
PRIORITY = ["moracin N", "daidzein", "formononetin", "3'-methoxydaidzein", "daidzin",
            "moracin M", "piceid", "biochanin A", "genistin", "epicatechin",
            "capillarisin", "isorhamnetin", "toralactone"]
BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"

def fetch(url, retries=3):
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(2 * (i + 1))

def canon(smi, isomeric=True):
    m = Chem.MolFromSmiles(smi)
    return Chem.MolToSmiles(m, isomericSmiles=isomeric) if m else None

def main():
    lib = [r for r in csv.DictReader(open(LIB, encoding="utf-8")) if r["name"].strip() not in PRIORITY]
    print(f"remaining compounds to check: {len(lib)} (54 total - 13 hits)", flush=True)
    out_rows, raw = [], {}
    for row in lib:
        name = row["name"].strip(); lib_smi = row["smiles"].strip()
        lib_canon, lib_iso = canon(lib_smi), canon(lib_smi, True)
        rec = dict(name=name, herb=row["herb"], lib_cid=row["cid"], lib_mw=row["mw_pubchem"],
                   lib_smiles=lib_smi, lib_formula=rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(lib_smi)))
        try:
            p = fetch(f"{BASE}/name/{urllib.parse.quote(name)}/property/IUPACName,MolecularFormula,MolecularWeight,ConnectivitySMILES,SMILES/JSON")["PropertyTable"]["Properties"][0]
            graph_pass = (lib_canon == canon(p["ConnectivitySMILES"], False))
            stereo_pass = (lib_iso == canon(p["SMILES"], True))
            formula_ok = (rec["lib_formula"] == p["MolecularFormula"])
            rec.update(pubchem_cid=p["CID"], pubchem_formula=p["MolecularFormula"],
                       formula_match=formula_ok,
                       cid_match=(str(row["cid"]).split(".")[0] == str(p["CID"])),
                       smiles_match_nonisomeric=graph_pass, smiles_match_isomeric=stereo_pass,
                       lib_has_stereo=("@" in lib_smi), pubchem_has_stereo=("@" in p["SMILES"]),
                       auto_status="PASS" if (formula_ok and (graph_pass or stereo_pass)) else "MISMATCH",
                       auto_basis=("identical_isomeric_SMILES_with_stereo" if stereo_pass and not graph_pass
                                   else "identical_graph_no_stereo" if graph_pass else "n/a"),
                       manual_tier_pending="herb-source authenticity; isolated-vs-database stereo; reviewer sign-off")
            raw[name] = p
            print(f"{name:<26s} CID={str(p['CID']):<9s} formula={rec['formula_match']} "
                  f"graph={graph_pass} iso={stereo_pass} -> {rec['auto_status']}", flush=True)
        except Exception as e:
            rec.update(auto_status=f"FETCH_FAILED:{e}")
            print(f"{name:<26s} FETCH_FAILED {e}", flush=True)
        out_rows.append(rec)
        time.sleep(0.4)
    with open(HERE / "pubchem_auto_check_rest41.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys())); w.writeheader(); w.writerows(out_rows)
    (HERE / "pubchem_auto_check_rest41_raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(r.get("auto_status") == "PASS" for r in out_rows)
    mm = [r["name"] for r in out_rows if r.get("auto_status") == "MISMATCH"]
    fl = [r["name"] for r in out_rows if str(r.get("auto_status", "")).startswith("FETCH_FAILED")]
    print(f"\nTier A: {ok}/{len(out_rows)} PASS; MISMATCH: {mm}; FETCH_FAILED(retry/alias check needed): {fl}", flush=True)

if __name__ == "__main__":
    main()
