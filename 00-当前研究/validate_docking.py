"""CCD-correct independent-start redocking diagnostic on archived receptors."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess
from rdkit import Chem
from rdkit.Chem import AllChem,rdMolAlign,rdMolDescriptors
from meeko import MoleculePreparation,PDBQTWriterLegacy,PDBQTMolecule
from meeko.rdkit_mol_create import RDKitMolCreate
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT/'03-课题-MASH研究-v2';HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def corrected_ligand(pdb,lig,smiles):
 lines=pdb.read_text().splitlines(True);atoms=[l for l in lines if l.startswith('HETATM') and l[17:20].strip()==lig]
 instances={(l[21],l[22:27]) for l in atoms}
 if len(instances)!=1:raise ValueError(f'{lig}: select and document a unique ligand instance, found {instances}')
 serials={int(l[6:11]) for l in atoms};conn=[l for l in lines if l.startswith('CONECT') and int(l[6:11]) in serials]
 m=Chem.MolFromPDBBlock(''.join(atoms+conn)+'END\n',removeHs=False,proximityBonding=False)
 if m is None:raise ValueError('Failed to parse crystal ligand')
 ref=Chem.MolFromSmiles(smiles);m=AllChem.AssignBondOrdersFromTemplate(ref,m)
 if Chem.MolToSmiles(m,isomericSmiles=False)!=Chem.MolToSmiles(ref,isomericSmiles=False):raise ValueError('CCD connectivity mismatch')
 return Chem.AddHs(m,addCoords=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--seed',type=int,default=42);a=p.parse_args();out=Path(a.output).resolve()
 if out.exists() and any(out.iterdir()):p.error('Use a new empty output directory')
 vina=Path(os.environ.get('VINA_BIN',''))
 if not vina.is_file():p.error('Set VINA_BIN to an installed Vina executable')
 out.mkdir(parents=True,exist_ok=True);records={};ccd=json.loads((HERE/'validation/structure_audit/summary.json').read_text(encoding='utf-8'))
 for target,pid,lig in [('THRB','2J4A','OEF'),('FASN','7MHD','ZEP')]:
  receptor=OLD/'docking/receptors'/f'{target}_{pid}.pdbqt';raw=OLD/'data/pdb'/f'{pid}.pdb'
  mol=corrected_ligand(raw,lig,ccd[target]['CCD_smiles']);assert rdMolDescriptors.CalcMolFormula(mol)==ccd[target]['CCD_formula']
  (out/f'{target}_corrected_crystal.sdf').write_text(Chem.MolToMolBlock(mol)+'\n$$$$\n')
  initial=Chem.Mol(mol);initial.RemoveAllConformers();params=AllChem.ETKDGv3();params.randomSeed=a.seed
  if AllChem.EmbedMolecule(initial,params)!=0:raise ValueError(lig+' independent ETKDG failed')
  opt=AllChem.MMFFOptimizeMolecule(initial,maxIters=1000)
  if opt!=0:raise ValueError(lig+' MMFF did not converge')
  text,ok,error=PDBQTWriterLegacy.write_string(MoleculePreparation()(initial)[0])
  if not ok:raise ValueError(error)
  lq=out/f'{target}_initial.pdbqt';lq.write_text(text);posefile=out/f'{target}_pose.pdbqt'
  box={'center':[4.25,20.95,32.03],'size':[31.6,29.8,25.0]} if target=='THRB' else {'center':[1.43,61.22,170.07],'size':[23.0,26.8,26.9]}
  # FASN pad8 is the archived retry condition, fixed here before corrected run.
  cmd=[str(vina),'--receptor',str(receptor),'--ligand',str(lq),'--out',str(posefile)]
  for key in ['center','size']:
   for axis,value in zip('xyz',box[key]):cmd.extend([f'--{key}_{axis}',str(value)])
  cmd+=['--seed',str(a.seed),'--exhaustiveness','32' if target=='FASN' else '16','--num_modes','9','--cpu','4']
  result=subprocess.run(cmd,capture_output=True,text=True,errors='replace',timeout=1200);(out/f'{target}.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
  if result.returncode or not posefile.exists():raise RuntimeError(target+' docking failed; inspect saved log')
  text=posefile.read_text();first='MODEL'+text.split('MODEL')[1].split('ENDMDL')[0]+'ENDMDL\n';pose=Chem.RemoveHs(RDKitMolCreate.from_pdbqt_mol(PDBQTMolecule(first,skip_typing=True))[0]);rms=rdMolAlign.CalcRMS(pose,Chem.RemoveHs(mol))
  records[target]={'CCD_formula':ccd[target]['CCD_formula'],'rmsd_no_alignment':float(rms),'pose_threshold_pass':bool(rms<2),'seed':a.seed,'independent_start':True,'box':box,'command':cmd,'receptor_sha256':sha(receptor),'raw_PDB_sha256':sha(raw),'vina_sha256':sha(vina),'pose_sha256':sha(posefile),'scientific_gate':'pending_receptor_review_and_multiseed','limitation':'Archived receptor reused; no receptor protonation/chain review; single seed does not validate target function or MASH efficacy.'}
  (out/'redock_diagnostic.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');print(target,rms,flush=True)
 if not all(r['pose_threshold_pass'] for r in records.values()):raise SystemExit('At least one pose threshold failed. No production screening released.')
if __name__=='__main__':main()
