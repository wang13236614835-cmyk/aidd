# -*- coding: utf-8 -*-
"""Receptor deep audit v2: SEQRES-vs-ATOM sequence coverage (independent of
REMARK 465) and itemization of residues removed raw->clean for each target.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[3]
AUDIT = {
    "THRB": dict(pdb=REPO / "03-课题-MASH研究-v2/data/pdb/2J4A.pdb",
                 clean=REPO / "03-课题-MASH研究-v2/docking/receptors/THRB_2J4A_clean.pdb"),
    "FASN": dict(pdb=REPO / "03-课题-MASH研究-v2/data/pdb/7MHD.pdb",
                 clean=REPO / "03-课题-MASH研究-v2/docking/receptors/FASN_7MHD_clean.pdb"),
    "FXR": dict(pdb=Path(r"D:\zcode-workspace\final-aidd-screening\docking\pdb\1OSH.pdb"),
                clean=Path(r"D:\zcode-workspace\final-aidd-screening\docking\receptors\FXR_LBD_1OSH_clean.pdb")),
}
AA3TO1 = {"ALA":"A","ARG":"R","ASN":"N","ASP":"D","CYS":"C","GLN":"Q","GLU":"E","GLY":"G","HIS":"H",
          "ILE":"I","LEU":"L","LYS":"K","MET":"M","PHE":"F","PRO":"P","SER":"S","THR":"T","TRP":"W",
          "TYR":"Y","VAL":"V","MSE":"M"}

def residues(path, atom_only=True):
    res = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        if line.startswith("ATOM"):
            key = (line[21], int(line[22:26]), line[17:20].strip())
            res[key] = res.get(key, 0) + 1
    return res

def seqres(path):
    seqs = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        if line.startswith("SEQRES"):
            toks = line.split()
            # SEQRES <serNum> <chainID> <numRes> <res1> <res2> ...
            ch = toks[2]
            seqs.setdefault(ch, [])
            for r in toks[4:]:
                if r in AA3TO1:
                    seqs[ch].append(r)
    return seqs

def hetatm_res(path):
    hets = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        if line.startswith("HETATM"):
            key = (line[21], int(line[22:26]), line[17:20].strip())
            hets[key] = hets.get(key, 0) + 1
    return hets

def main():
    out = {}
    for tgt, cfg in AUDIT.items():
        raw_res = residues(cfg["pdb"]); clean_res = residues(cfg["clean"])
        sq = seqres(cfg["pdb"])
        hets = hetatm_res(cfg["pdb"])
        # sequence coverage per chain: SEQRES residues with >=1 ATOM (by order position is
        # approximate without alignment; count by residue-name multiset comparison)
        cov = {}
        for ch, lst in sq.items():
            from collections import Counter
            exp = Counter(lst)
            obs = Counter(f"{k[2]}" for k in raw_res if k[0] == ch and k[2] in AA3TO1)
            mapped = sum(min(exp[r], obs.get(r, 0)) for r in exp)
            if not lst:
                cov[ch] = dict(seqres_len=0, atom_residues=sum(obs.values()),
                               name_matched_residues=mapped, coverage_pct=None)
                continue
            cov[ch] = dict(seqres_len=len(lst), atom_residues=sum(obs.values()),
                           name_matched_residues=mapped,
                           coverage_pct=round(100 * mapped / len(lst), 1))
        # internal gaps in observed numbering per chain
        gaps = {}
        for ch in sorted({k[0] for k in raw_res}):
            nums = sorted(k[1] for k in raw_res if k[0] == ch)
            missing_ranges, run = [], None
            for a, b in zip(nums, nums[1:]):
                if b - a > 1:
                    gaps.setdefault(ch, []).append([a + 1, b - 1])
        removed = sorted(set(raw_res) - set(clean_res))
        removed_prot = [k for k in removed if k[2] in AA3TO1]
        het_types = {}
        for k in hets:
            het_types[k[2]] = het_types.get(k[2], 0) + 1
        out[tgt] = dict(
            seqres_coverage=cov,
            atom_numbering_gaps={ch: v for ch, v in gaps.items()},
            hetatm_types_in_raw=het_types,
            removed_raw_to_clean=dict(
                n_residues=len(removed), protein_residues=len(removed_prot),
                protein_removed_detail=[f"{k[0]}:{k[2]}{k[1]}" for k in removed_prot]),
            tierB_pending=["protonation state review (PROPKA) still pending",
                           "domain assignment & MASH cell-context relevance",
                           "gap impact on pocket if any internal gap borders box"])
        c = cov.get("A", {})
        print(f"[{tgt}] SEQRES(A)={c.get('seqres_len')} ATOMres(A)={c.get('atom_residues')} "
              f"coverage={c.get('coverage_pct')}%  numbering_gaps={sum(len(v) for v in gaps.values())} "
              f"removed_raw->clean={len(removed)} (protein {len(removed_prot)})", flush=True)
        for ch, v in gaps.items():
            if v:
                print(f"   internal numbering gaps {ch}: {v[:8]}{'...' if len(v)>8 else ''}", flush=True)
    (HERE / "sequence_coverage_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
