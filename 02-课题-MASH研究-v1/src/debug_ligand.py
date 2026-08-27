from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
RDLogger.DisableLog('rdApp.*')
import json, os
REC = 'D:/zcode-workspace/mash_research/docking/receptors'

TARGETS = {
    "FXR_3FLI": ("33Y"),
    "FXR_1OSH": ("FEX"),
    "THRB_3GWS": ("T3"),
    "ACC2_5KKN": ("6U3"),
    "ACC2_3GID": ("S1A"),
}
for tag, lig in TARGETS.items():
    ideal = f'{REC}/{lig}_ideal.sdf'
    if not os.path.exists(ideal):
        import requests
        r = requests.get(f'https://files.rcsb.org/ligands/view/{lig}_ideal.sdf', timeout=30)
        open(ideal, 'wb').write(r.content)
    tmpl = Chem.SDMolSupplier(ideal, removeHs=False)[0]
    tmpl_noh = Chem.RemoveHs(tmpl)
    cryst = Chem.MolFromPDBFile(f'{REC}/{tag}_{lig}_crystal.pdb',
                                removeHs=False, proximityBonding=True)
    if cryst is None:
        print(tag, 'crystal parse FAILED'); continue
    try:
        m = AllChem.AssignBondOrdersFromTemplate(tmpl_noh, cryst)
        w = Chem.SDWriter(f'{REC}/{tag}_{lig}_crystal.sdf'); w.write(m); w.close()
        print(tag, f'SUCCESS bonds={m.GetNumBonds()} atoms={m.GetNumAtoms()}')
    except Exception as e:
        print(tag, 'FAIL:', str(e)[:120],
              '| tmpl heavy:', tmpl_noh.GetNumAtoms(), 'cryst:', cryst.GetNumAtoms())
