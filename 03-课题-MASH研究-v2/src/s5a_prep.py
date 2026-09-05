# -*- coding: utf-8 -*-
"""
S5a: 对接准备（全新实现）。
受体制备: PDB清洗(留蛋白链+参考配体) -> mk_prepare_receptor(pdbqt+盒子)。
配体制备: 晶体配体直接取坐标; 化合物SMILES -> ETKDG/MMFF -> meeko pdbqt。
结构: THRB=2J4A(OEF/sobetirome共晶), FASN=7MHD(ZEP磺酰胺噻唑抑制剂共晶)。
"""

# Historical pipeline: its outputs are invalidated; corrected code lives in 00-当前研究.
raise RuntimeError("此历史入口已停用以保留原数据与结果；请使用仓库00-当前研究中的诊断/修订流程。")
import json, os, re, subprocess, sys
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from meeko import MoleculePreparation, PDBQTWriterLegacy

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_v2_new"
VINA = f"{D}/tools/vina_1.2.5_win.exe"
MKR = r"C:\Users\user\AppData\Roaming\Python\Python312\Scripts\mk_prepare_receptor.exe"
PDBD, RCP, LGD, OUT = f"{D}/data/pdb", f"{D}/docking/receptors", f"{D}/docking/ligands", f"{D}/docking/outputs"

STRUCTS = {"THRB": ("2J4A", "OEF"), "FASN": ("7MHD", "ZEP")}

def split_pdb(path, keep_lig):
    """蛋白链(无水/无配体) + 参考配体坐标; 返回(clean_pdb_block, lig_pdb_block, lig_chain)"""
    prot, lig = [], []
    for l in open(path):
        if l.startswith(("ATOM", "TER", "END")):
            prot.append(l)
        elif l.startswith("HETATM") and l[17:20].strip() == keep_lig:
            lig.append(l)
    return "".join(prot), "".join(lig)

boxes = {}
for name, (pid, ligname) in STRUCTS.items():
    raw = f"{PDBD}/{pid}.pdb"
    prot, ligpdb = split_pdb(raw, ligname)
    assert len(ligpdb) > 0, f"{pid} ligand {ligname} not found"
    clean = f"{RCP}/{name}_{pid}_clean.pdb"
    open(clean, "w").write(prot + "END\n")
    ligp = f"{RCP}/{name}_{pid}_{ligname}_lig.pdb"
    open(ligp, "w").write(ligpdb + "END\n")
    print(f"{name}: clean pdb {len(prot)//80} lines, ligand {ligname} {len(ligpdb)} atoms")

    # 受体pdbqt + 盒子(包络配体+10Å padding)
    outbase = f"{RCP}/{name}_{pid}"
    cmd = [MKR, "--read_pdb", clean, "-o", outbase, "-p", "--charge_model", "gasteiger",
           "--box_enveloping", ligp, "--padding", "10.0", "-v"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    pdbqt = f"{outbase}.pdbqt"
    ok = os.path.exists(pdbqt)
    print(f"  receptor pdbqt: {ok} | {'ERR: ' + r.stderr[-300:] if not ok else ''}")
    if not ok:
        sys.exit(f"receptor prep failed for {name}")

    # 盒子(从mk_prepare_receptor输出的vina box文件或自行计算)
    boxfile = None
    for f in os.listdir(RCP):
        if f.startswith(f"{name}_{pid}") and "box" in f.lower():
            boxfile = f"{RCP}/{f}"
    if boxfile and os.path.exists(boxfile):
        txt = open(boxfile).read()
        cx = re.search(r"center_x\s*=\s*([\d.\-]+)", txt)
        cy = re.search(r"center_y\s*=\s*([\d.\-]+)", txt)
        cz = re.search(r"center_z\s*=\s*([\d.\-]+)", txt)
        sx = re.search(r"size_x\s*=\s*([\d.\-]+)", txt)
        sy = re.search(r"size_y\s*=\s*([\d.\-]+)", txt)
        sz = re.search(r"size_z\s*=\s*([\d.\-]+)", txt)
        if all([cx, cy, cz, sx, sy, sz]):
            boxes[name] = dict(pdb=pid, ligand=ligname,
                               center=[float(cx.group(1)), float(cy.group(1)), float(cz.group(1))],
                               size=[float(sx.group(1)), float(sy.group(1)), float(sz.group(1))])
    if name not in boxes:  # 手动计算包络盒
        coords = []
        for l in ligpdb.splitlines():
            coords.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
        c = np.array(coords)
        center = c.mean(0).round(2).tolist()
        size = (c.max(0) - c.min(0) + 20).round(1).tolist()
        boxes[name] = dict(pdb=pid, ligand=ligname, center=center, size=size)
    print(f"  box: {boxes[name]}")

json.dump(boxes, open(f"{D}/docking/boxes.json", "w"), indent=1)

# ---------- 晶体配体 -> 3D分子 -> pdbqt ----------
MK = MoleculePreparation()
def pdbblock_to_pdbqt(block, outpath):
    m = Chem.MolFromPDBBlock(block, removeHs=False, proximityBonding=True)
    if m is None:
        return None
    m = Chem.AddHs(m, addCoords=True)
    try:
        setups = MK(m)
        s, ok, err = PDBQTWriterLegacy.write_string(setups[0])
        if not ok:
            return None
        open(outpath, "w").write(s)
        return outpath
    except Exception:
        return None

for name, (pid, ligname) in STRUCTS.items():
    _, ligpdb = split_pdb(f"{PDBD}/{pid}.pdb", ligname)
    p = pdbblock_to_pdbqt(ligpdb, f"{LGD}/{name}_{ligname}_redock.pdbqt")
    # 存参考分子(RMSD用)
    m = Chem.MolFromPDBBlock(ligpdb, removeHs=False, proximityBonding=True)
    if m is not None:
        Chem.AddHs(m, addCoords=True)
        w = Chem.SDWriter(f"{RCP}/{name}_{pid}_{ligname}_crystal.sdf")
        w.write(m); w.close()
    print(f"{name} redock ligand pdbqt: {p is not None}")

print("\nS5a prep done.")
