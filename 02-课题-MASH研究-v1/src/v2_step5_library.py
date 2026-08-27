# -*- coding: utf-8 -*-
"""V2 Step5: build ultra-large NP library from COCONUT (real data, 50万+)."""
import io, json, zipfile
import pandas as pd
from rdkit import Chem, RDLogger

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
z = zipfile.ZipFile(f"{D}/data/v2/coconut_csv.zip")
name = z.namelist()[0]
print("member:", name)
df = pd.read_csv(z.open(name), low_memory=False,
                 usecols=lambda c: c in {"identifier", "canonical_smiles", "name",
                                         "organisms", "np_classifier_pathway",
                                         "np_classifier_superclass", "np_classifier_class",
                                         "chemical_super_class", "dois"})
print("rows:", len(df), "| cols:", list(df.columns))
df = df.dropna(subset=["canonical_smiles"]).drop_duplicates("canonical_smiles")
print("after dedup:", len(df))

# parseability + minimal validity
def ok(smi):
    return Chem.MolFromSmiles(smi) is not None
df["valid"] = df["canonical_smiles"].head(len(df)).map(ok)  # full scan
df = df[df["valid"]].drop(columns=["valid"])
print("valid RDKit:", len(df))

df["organism"] = df.get("organisms", pd.Series("", index=df.index)).fillna("").astype(str)
df["pathway"] = df.get("np_classifier_pathway", pd.Series("", index=df.index)).fillna("")
df.to_csv(f"{D}/data/v2/np_library_full.csv.gz", index=False, compression="gzip")
print("saved np_library_full.csv.gz |", len(df), "molecules |",
      df["organism"].str.len().gt(0).sum(), "with organism")
# quick composition
print(df["pathway"].value_counts().head(8).to_string())
