# -*- coding: utf-8 -*-
"""
Step 6b: AutoDock Vina docking.
(1) redocking validation of co-crystal ligands (RMSD<2A gate)
(2) positive-control docking (real drugs: OCA/GW4064/CDCA/tanshinoneIIA for FXR,
    T3/resmetirom for THR-b, ND-646/soraphen A for ACC)
(3) batch docking of the natural-product library (THR-b and ACC proxy scores)
Ligands: RDKit ETKDG 3D + MMFF94s -> meeko PDBQT (Gasteiger).
"""
import json, os, re, subprocess, sys, time
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem import rdMolDescriptors as rdMD
from meeko import MoleculePreparation, PDBQTWriterLegacy

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
VINA = f"{D}/tools/vina_1.2.5_win.exe"
BOXES = json.load(open(f"{D}/docking/boxes.json"))
LIGD = f"{D}/docking/ligands"
OUTD = f"{D}/docking/outputs"
os.makedirs(LIGD, exist_ok=True); os.makedirs(OUTD, exist_ok=True)

def embed_3d(smi, seed=42):
    m = Chem.MolFromSmiles(smi)
    if m is None: return None
    m = Chem.AddHs(m)
    p = AllChem.ETKDGv3()
    p.randomSeed = seed
    if AllChem.EmbedMolecule(m, p) != 0:
        p.useRandomCoords = True
        if AllChem.EmbedMolecule(m, p) != 0:
            return None
    try:
        AllChem.MMFFOptimizeMolecule(m, mmffVariant='MMFF94s', maxIters=500)
    except Exception:
        try: AllChem.UFFOptimizeMolecule(m, maxIters=500)
        except Exception: pass
    return m

MK = MoleculePreparation()
def to_pdbqt(mol, path):
    setups = MK(mol)
    s, ok, err = PDBQTWriterLegacy.write_string(setups[0])
    if not ok:
        return None
    open(path, "w").write(s)
    return path

AFF_RE = re.compile(r"^\s+\d+\s+(-?\d+\.\d+)\s+")
def run_vina(receptor_tag, ligand_pdbqt, out_pdbqt, exh=8, seed=42):
    b = BOXES[receptor_tag]
    c, s = b["center"], b["size"]
    cmd = [VINA, "--receptor", f"{D}/docking/receptors/{receptor_tag}.pdbqt",
           "--ligand", ligand_pdbqt, "--out", out_pdbqt,
           "--center_x", str(c[0]), "--center_y", str(c[1]), "--center_z", str(c[2]),
           "--size_x", str(s[0]), "--size_y", str(s[1]), "--size_z", str(s[2]),
           "--exhaustiveness", str(exh), "--seed", str(seed), "--num_modes", "9"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
    affs = [float(AFF_RE.match(l).group(1)) for l in r.stdout.splitlines()
            if AFF_RE.match(l)]
    return affs[0] if affs else (999.0 if "cluster" not in r.stdout else None), r

# ---------------- (1) redocking validation ----------------
print("=== redocking validation ===")
REDock = {"FXR_3FLI": "33Y", "THRB_3GWS": "T3", "ACC2_5KKN": "6U3", "ACC2_3GID": "S1A"}
redock_results = {}
for tag, lig in REDock.items():
    sdf = f"{D}/docking/receptors/{tag}_{lig}_crystal.sdf"
    if not os.path.exists(sdf):
        print(f"{tag}: no crystal SDF, skip"); continue
    ref = Chem.SDMolSupplier(sdf, removeHs=False)[0]
    refH = Chem.AddHs(ref, addCoords=True)
    lp = to_pdbqt(refH, f"{LIGD}/{tag}_{lig}_redock.pdbqt")
    if lp is None: print(f"{tag}: pdbqt prep failed"); continue
    aff, r = run_vina(tag, lp, f"{OUTD}/{tag}_{lig}_redock_out.pdbqt", exh=16)
    # RMSD of best pose vs crystal: rebuild mol from vina output pdbqt via meeko
    txt = open(f"{OUTD}/{tag}_{lig}_redock_out.pdbqt").read()
    models = txt.split("MODEL")[1:]
    rmsd = float("nan")
    if models:
        first = "MODEL" + models[0].split("ENDMDL")[0] + "ENDMDL\n"
        try:
            from meeko import PDBQTMolecule
            from meeko.rdkit_mol_create import RDKitMolCreate
            from rdkit.Chem import rdMolAlign
            pmol = PDBQTMolecule(first, skip_typing=True)
            out = RDKitMolCreate.from_pdbqt_mol(pmol)
            mol = out[0] if isinstance(out, list) and out else None
            if mol is not None:
                pose_noh = Chem.RemoveHs(mol)
                refH_noH = Chem.RemoveHs(refH)
                try:
                    rmsd = float(rdMolAlign.GetBestRMS(pose_noh, refH_noH))
                except Exception:
                    rmsd = float("nan")
        except Exception as e:
            print("pose rebuild failed:", str(e)[:100])
    redock_results[tag] = dict(ligand=lig, affinity=aff, rmsd=float(rmsd))
    print(f"{tag} | {lig}: best affinity {aff} kcal/mol | pose RMSD {rmsd:.2f} A")
json.dump(redock_results, open(f"{D}/docking/redock_validation.json", "w"), indent=2)

# ---------------- (2) positive controls ----------------
print("\n=== positive controls ===")
import requests, urllib.parse
HEADERS = {"User-Agent": "academic-virtual-screening/1.0 (university research project)"}
def pc_smiles(name):
    q = urllib.parse.quote(name)
    for att in range(5):
        r = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}"
                         f"/property/IsomericSMILES/JSON", timeout=30, headers=HEADERS)
        if r.status_code == 200 and "PropertyTable" in r.text:
            p0 = r.json()["PropertyTable"]["Properties"][0]
            return p0.get("IsomericSMILES") or p0.get("SMILES")
        time.sleep(2.0 * (att + 1))
    return None

CONTROLS = {
    "FXR_3FLI": ["obeticholic acid", "GW4064", "chenodeoxycholic acid", "tanshinone IIA"],
    "THRB_3GWS": ["liothyronine", "resmetirom"],
    "ACC2_5KKN": ["ND-646", "soraphen A"],
}
ctrl_rows = []
for tag, names in CONTROLS.items():
    for nm in names:
        smi = pc_smiles(nm); time.sleep(0.45)
        if smi is None:
            ctrl_rows.append(dict(target=tag, control=nm, affinity=None, note="PUBCHEM_MISS"))
            continue
        mol = embed_3d(smi)
        if mol is None:
            ctrl_rows.append(dict(target=tag, control=nm, affinity=None, note="EMBED_FAIL"))
            continue
        safe = re.sub(r"[^A-Za-z0-9]+", "_", nm)
        lp = to_pdbqt(mol, f"{LIGD}/ctrl_{safe}.pdbqt")
        aff, _ = run_vina(tag, lp, f"{OUTD}/ctrl_{tag}_{safe}_out.pdbqt", exh=16)
        ctrl_rows.append(dict(target=tag, control=nm, affinity=aff, note=""))
        print(f"{tag} | {nm}: {aff} kcal/mol")
pd.DataFrame(ctrl_rows).to_csv(f"{D}/results/tables/positive_controls_docking.csv", index=False)

# ---------------- (3) NP library docking ----------------
if len(sys.argv) > 1 and sys.argv[1] == "nps":
    print("\n=== NP library docking (THR-b, ACC) ===")
    lib = pd.read_csv(f"{D}/data/tcm/tcm_library_filtered.csv")
    out_rows = []
    for target in ["THRB_3GWS", "ACC2_5KKN"]:
        for _, r in lib.iterrows():
            key = re.sub(r"[^A-Za-z0-9]+", "_", f"{r['herb']}_{r['name']}")[:60]
            lp_path = f"{LIGD}/np_{key}.pdbqt"
            mol = embed_3d(r["smiles"])
            if mol is None or to_pdbqt(mol, lp_path) is None:
                out_rows.append(dict(target=target, herb=r["herb"], name=r["name"],
                                     affinity=None, note="PREP_FAIL")); continue
            aff, rr = run_vina(target, lp_path, f"{OUTD}/np_{target}_{key}_out.pdbqt", exh=8)
            out_rows.append(dict(target=target, herb=r["herb"], name=r["name"],
                                 affinity=aff, note=""))
            print(f"{target} | {r['herb']} | {r['name']}: {aff}")
    pd.DataFrame(out_rows).to_csv(f"{D}/results/tables/np_docking_raw.csv", index=False)
    print("NP docking done:", len(out_rows))
