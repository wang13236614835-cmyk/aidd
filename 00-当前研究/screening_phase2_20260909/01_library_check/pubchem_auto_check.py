# -*- coding: utf-8 -*-
"""Automated identity check of screen hits against PubChem PUG REST.

Tier A (automated, this script): name->CID resolution, canonical/isomeric SMILES
match after RDKit normalization, molecular formula, MW, stereo-center flags.
Tier B (manual, human, NOT substitutable): herb-source authenticity, extraction
reference, stereochemistry-as-isolated vs database default, reviewer sign-off.
Writes: pubchem_auto_check.csv + .json (raw payloads kept for provenance).
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
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(2 * (i + 1))

def canon(smi, isomeric=True):
    m = Chem.MolFromSmiles(smi)
    return Chem.MolToSmiles(m, isomericSmiles=isomeric) if m else None

def main():
    lib = {r["name"].strip(): r for r in csv.DictReader(open(LIB, encoding="utf-8"))}
    out_rows, raw = [], {}
    for name in PRIORITY:
        row = lib.get(name)
        assert row, f"{name} not in library"
        lib_smi = row["smiles"].strip()
        lib_canon = canon(lib_smi); lib_iso = canon(lib_smi, True)
        q = urllib.parse.quote(name)
        rec = dict(name=name, herb=row["herb"], lib_cid=row["cid"], lib_mw=row["mw_pubchem"],
                   lib_smiles=lib_smi, lib_formula=rdMolDescriptors.CalcMolFormula(Chem.MolFromSmiles(lib_smi)))
        try:
            props = fetch(f"{BASE}/name/{q}/property/IUPACName,MolecularFormula,MolecularWeight,ConnectivitySMILES,SMILES/JSON")
            p = props["PropertyTable"]["Properties"][0]
            cid = p["CID"]
            pc_canon, pc_iso = p["ConnectivitySMILES"], p["SMILES"]
            rec.update(pubchem_cid=cid, pubchem_iupac=p["IUPACName"], pubchem_formula=p["MolecularFormula"],
                       pubchem_mw=p["MolecularWeight"],
                       formula_match=(rec["lib_formula"] == p["MolecularFormula"]),
                       cid_match=(str(row["cid"]).split(".")[0] == str(cid)),
                       smiles_match_nonisomeric=(lib_canon == canon(pc_canon, False)),
                       smiles_match_isomeric=(lib_iso == canon(pc_iso, True)),
                       lib_has_stereo=("@" in lib_smi), pubchem_has_stereo=("@" in pc_iso),
                       auto_status="PASS" if (lib_canon == canon(pc_canon, False)) else "MISMATCH")
            raw[name] = p
            print(f"{name:<22s} CID={str(cid):<9s} formula_match={rec['formula_match']} "
                  f"smiles(non-iso)={rec['smiles_match_nonisomeric']} iso={rec['smiles_match_isomeric']} "
                  f"stereo lib/pc={rec['lib_has_stereo']}/{rec['pubchem_has_stereo']}", flush=True)
        except Exception as e:
            rec.update(auto_status=f"FETCH_FAILED:{e}")
            print(f"{name:<22s} FETCH_FAILED {e}", flush=True)
        rec["manual_tier_pending"] = "herb-source / isolated-stereo / reviewer sign-off (human)"
        out_rows.append(rec)
        time.sleep(0.4)
    with open(HERE / "pubchem_auto_check.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys())); w.writeheader(); w.writerows(out_rows)
    (HERE / "pubchem_auto_check_raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    n_pass = sum(r.get("auto_status") == "PASS" for r in out_rows)
    print(f"\nautomated tier: {n_pass}/{len(out_rows)} PASS (non-isomeric graph match); manual tier: all pending", flush=True)

if __name__ == "__main__":
    main()
