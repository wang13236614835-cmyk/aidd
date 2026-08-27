# -*- coding: utf-8 -*-
"""
Step 4: Build natural-product library from REAL PubChem data.
Compound lists for 10 hepatoprotective herbs were curated from published
literature (see research/herb_ingredients.md). Each compound is resolved via
PubChem PUG-REST by name -> CID + IsomericSMILES (traceable to PubChem).
Then: RDKit ADMET filter (150<MW<500, MolLogP<5.5, HBD<=5, HBA<=10),
PAINS flagging, classic-flavonoid/polyphenol exclusion list from proposal.
"""
import json, time, urllib.parse
import numpy as np
import pandas as pd
import requests
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, Lipinski
from rdkit.Chem import FilterCatalog

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
OUT = f"{D}/data/tcm"

# herb -> list of (compound_name_ascii, note)   note: KEEP/TOX/UNCERTAIN
HERBS = {
 "Salvia miltiorrhiza(丹参)": [
  ("Tanshinone I",""),("Tanshinone IIA",""),("Tanshinone IIB",""),("Cryptotanshinone",""),
  ("Dihydrotanshinone I",""),("Neocryptotanshinone",""),("Isocryptotanshinone","UNCERTAIN"),
  ("Miltirone",""),("Tanshindiol A",""),("Tanshindiol B",""),("Tanshindiol C",""),
  ("Methylenetanshinquinone","UNCERTAIN"),("Salvilenone","UNCERTAIN"),
  ("Danshenxinkun A",""),("Danshenxinkun B",""),("Ferruginol",""),("Sugiol",""),
  ("Przewalskin","UNCERTAIN"),("Isotanshinone IIB","UNCERTAIN"),
  ("beta-Sitosterol",""),("Stigmasterol",""),("Daucosterol","")],
 "Glycyrrhiza uralensis(甘草)": [
  ("Glycyrrhizic acid",""),("enoxolone",""),("18alpha-Glycyrrhetinic acid","UNCERTAIN"),
  ("Liquiritic acid",""),("Glycyrrhetol","UNCERTAIN"),("Glycyrol",""),("Isoglycyrol",""),
  ("Glabridin",""),("Glabrol",""),("Glabrene","UNCERTAIN"),("Licochalcone A",""),
  ("Licochalcone B",""),("Echinatin",""),("Liquiritigenin",""),("Isoliquiritigenin",""),
  ("Liquiritin",""),("Isoliquiritin",""),("Neoliquiritin",""),("Formononetin",""),
  ("Licoisoflavone A",""),("Licoisoflavone B",""),("Isolicoflavonol",""),
  ("Semilicoisoflavone B",""),("Licoricidin",""),("Glyasperin C",""),
  ("Licoflavanone",""),("beta-Sitosterol",""),("Stigmasterol","")],
 "Bupleurum chinense(柴胡)": [
  ("Saikosaponin A",""),("Saikosaponin D",""),("Saikosaponin B1",""),("Saikosaponin B2",""),
  ("Saikosaponin B3",""),("Saikosaponin B4",""),("Saikosaponin C",""),("Saikosaponin E",""),
  ("Saikosaponin F",""),("Saikosaponin H",""),("3-O-Acetylsaikosaponin A",""),
  ("3-O-Acetylsaikosaponin D",""),("Saikogenin A",""),("Saikogenin B",""),
  ("Saikogenin C",""),("Saikogenin D",""),("Saikogenin E",""),("Saikogenin F",""),
  ("Saikogenin G",""),("Spinasterol",""),("Stigmasterol",""),("beta-Sitosterol",""),
  ("Daucosterol","")],
 "Schisandra chinensis(五味子)": [
  ("Schisandrin A",""),("Schisandrin B",""),("Schisandrin C",""),("Schisandrol A",""),
  ("Schisandrol B",""),("Gomisin B",""),("Gomisin C",""),("Gomisin D",""),("Gomisin E",""),
  ("Gomisin G",""),("Gomisin H",""),("Gomisin J",""),("Gomisin K1",""),("Gomisin K3",""),
  ("Gomisin L1",""),("Gomisin L2",""),("Gomisin M1",""),("Gomisin M2",""),("Gomisin N",""),
  ("Gomisin O",""),("Schisantherin A",""),("Schisantherin B",""),("Schisanhenol",""),
  ("Angeloylgomisin H",""),("Pregomisin","UNCERTAIN"),("Chamigrenal",""),("beta-Sitosterol","")],
 "Ganoderma lucidum(灵芝)": [
  ("Ganoderic acid A",""),("Ganoderic acid B",""),("Ganoderic acid C2",""),
  ("Ganoderic acid D",""),("Ganoderic acid DM",""),("Ganoderic acid E",""),
  ("Ganoderic acid F",""),("Ganoderic acid G",""),("Ganoderic acid H",""),
  ("Ganoderic acid I",""),("Ganoderic acid J",""),("Ganoderic acid X",""),
  ("Ganoderic acid Y",""),("Ganoderic acid R",""),("Ganoderic acid S",""),
  ("Lucidenic acid A",""),("Lucidenic acid B",""),("Lucidenic acid C",""),
  ("Lucidenic acid D",""),("Lucidenic acid E1","UNCERTAIN"),("Lucidenic acid F",""),
  ("Lucidenic acid N",""),("Lucidenic acid O",""),("Ganodermanontriol",""),
  ("Ganodermanondiol",""),("Ganoderiol F",""),("Ganoderal A",""),("Ganoderal B",""),
  ("Lucidumol A",""),("Lucidumol B",""),("Ganosporeric acid A",""),("Ergosterol",""),
  ("Ergosterol peroxide","")],
 "Coptis chinensis(黄连)": [
  ("Berberine",""),("Coptisine",""),("Palmatine",""),("Epiberberine",""),
  ("Jatrorrhizine",""),("Columbamine",""),("Magnoflorine",""),("Berberrubine",""),
  ("Worenine","UNCERTAIN"),("Canadine",""),("Stylopine",""),
  ("Cheilanthifoline","UNCERTAIN"),("Groenlandicine","UNCERTAIN"),
  ("Menisperine","UNCERTAIN"),("8-Oxocoptisine","UNCERTAIN"),("beta-Sitosterol","")],
 "Sophora flavescens(苦参)": [
  ("Matrine",""),("Oxymatrine",""),("Sophoridine",""),("Sophocarpine",""),
  ("Oxysophocarpine",""),("Sophoramine",""),("Aloperine","UNCERTAIN"),
  ("N-Methylcytisine","UNCERTAIN"),("Anagyrine","UNCERTAIN"),("Baptifoline","UNCERTAIN"),
  ("Kurarinone",""),("Isokurarinone",""),("Kuraridin",""),("Kurarinol",""),
  ("Sophoraflavanone G",""),("Kushenol A",""),("Kushenol B",""),("Kushenol C",""),
  ("Kushenol D",""),("Kushenol E",""),("Kushenol F",""),("Kushenol G",""),
  ("Kushenol H",""),("Kushenol I",""),("Formononetin",""),("Maackiain",""),
  ("Lupeol",""),("beta-Sitosterol","")],
 "Silybum marianum(水飞蓟)": [
  ("Silybin A",""),("Silybin B",""),("Isosilybin A",""),("Isosilybin B",""),
  ("Silychristin A",""),("Silychristin B","UNCERTAIN"),("Silydianin",""),
  ("Isosilychristin",""),("Silandrin",""),("Silyhermin",""),
  ("Neosilyhermin A",""),("Neosilyhermin B","UNCERTAIN"),("Silymonin","UNCERTAIN"),
  ("2,3-Dehydrosilybin","UNCERTAIN"),("beta-Sitosterol",""),("Campesterol",""),
  ("Stigmasterol","")],
 "Artemisia annua(青蒿)": [
  ("Artemisinin",""),("Arteannuin B",""),("Artemisinic acid",""),
  ("Dihydroartemisinic acid",""),("Deoxyartemisinin",""),("Dihydroartemisinin",""),
  ("Artemisitene","UNCERTAIN"),("beta-Caryophyllene",""),("Caryophyllene oxide",""),
  ("Camphor",""),("1,8-Cineole",""),("Artemisia ketone","UNCERTAIN"),
  ("Casticin",""),("Chrysosplenol D",""),("Chrysosplenetin",""),("Artemetin",""),
  ("Cirsilineol",""),("Eupatorin",""),("Cirsimaritin","UNCERTAIN"),("Scopoletin",""),
  ("Scopolin","UNCERTAIN"),("4-Methylesculetin",""),("Umbelliferone",""),
  ("beta-Sitosterol",""),("Stigmasterol","")],
 "Tripterygium wilfordii(雷公藤)": [
  ("Triptophenolide",""),("Tripterifordin",""),("Wilforlide A",""),
  ("Wilforlide B","UNCERTAIN"),("Celastrol","KEEP_WITH_TOX_WARNING"),
  ("Wilforic acid A",""),("Wilforic acid B","UNCERTAIN"),("Wilforgine",""),
  ("Wilforine",""),("Wilfordine",""),("Wilfortrine",""),("Wilforzine","UNCERTAIN"),
  ("Euonomine","UNCERTAIN"),("beta-Sitosterol","")],
}

# proposal-mandated exclusions (classic pan-assay compounds)
EXCLUDE_NAMES = {
 "quercetin","luteolin","apigenin","kaempferol","hesperetin","baicalein",
 "caffeic acid","chlorogenic acid","vanillic acid","ellagic acid","gallic acid","ferulic acid",
 "choline","adenine","glucose","palmitic acid","curcumin","resveratol","epigallocatechin gallate",
 "taxifolin","triptolide","tripdiolide","triptonide","salvianolic acid a","salvianolic acid b",
 "rosmarinic acid","danshensu","protocatechuic aldehyde",
}

PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"

HEADERS = {"User-Agent": "academic-virtual-screening/1.0 (university research project)"}
def pubchem_lookup(name):
    """returns (smiles, formula, mw, cid, status_note)"""
    q = urllib.parse.quote(name)
    url = f"{PUG}/{q}/property/IsomericSMILES,MolecularFormula,MolecularWeight/JSON"
    last_code = None
    for attempt in range(6):
        try:
            r = requests.get(url, timeout=30, headers=HEADERS)
            last_code = r.status_code
            if r.status_code == 200:
                p = r.json()["PropertyTable"]["Properties"][0]
                smi = p.get("IsomericSMILES") or p.get("SMILES")
                cidv = p.get("CID")
                if cidv is None:
                    try:
                        time.sleep(0.6)
                        rc = requests.get(f"{PUG}/{q}/cids/JSON", timeout=30, headers=HEADERS)
                        if rc.status_code == 200:
                            cidv = rc.json()["IdentifierList"]["CID"][0]
                    except Exception:
                        pass
                return (smi, p.get("MolecularFormula"),
                        float(p.get("MolecularWeight", 0)), cidv, "")
            if r.status_code in (503, 504, 429):
                time.sleep(3.0 * (attempt + 1))
                continue
            if r.status_code == 404:
                return None, None, None, None, "NOT_IN_PUBCHEM"
            time.sleep(1.0)
        except Exception:
            time.sleep(2.0 * (attempt + 1))
    return None, None, None, None, f"HTTP_{last_code}"

# PAINS catalog
params = FilterCatalog.FilterCatalogParams()
params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_A)
params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_B)
params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_C)
fcat = FilterCatalog.FilterCatalog(params)

rows = []
for herb, comps in HERBS.items():
    for name, note in comps:
        low = name.lower()
        if low in EXCLUDE_NAMES:
            rows.append(dict(herb=herb, name=name, status="EXCLUDED_BY_PROPOSAL", note=note))
            continue
        smi, formula, mw_pub, cid, note_http = pubchem_lookup(name)
        time.sleep(0.65)  # stay well under PUG-REST 5 req/s
        if smi is None:
            rows.append(dict(herb=herb, name=name,
                             status="PUBCHEM_NOT_FOUND", note=(note or "") + "|" + note_http))
            print(f"  [miss {note_http}] {herb} | {name}")
            continue
        m = Chem.MolFromSmiles(smi)
        if m is None:
            rows.append(dict(herb=herb, name=name, status="RDKIT_INVALID", note=note,
                             cid=cid, smiles=smi))
            continue
        mw = Descriptors.MolWt(m); logp = Crippen.MolLogP(m)
        hbd = Lipinski.NumHDonors(m); hba = Lipinski.NumHAcceptors(m)
        pains = [e.GetDescription() for e in fcat.GetMatches(m)]
        admet_ok = (150 < mw < 500) and (logp < 5.5) and (hbd <= 5) and (hba <= 10)
        rows.append(dict(herb=herb, name=name, status="OK", note=note, cid=cid,
                         smiles=smi, formula=formula, mw=round(mw, 2), logp=round(logp, 2),
                         hbd=hbd, hba=hba, admet_pass=bool(admet_ok),
                         pains=";".join(pains), mw_pubchem=mw_pub))
        print(f"  {herb} | {name} | CID {cid} | MW {mw:.0f} | ADMET {admet_ok}"
              + (f" | PAINS:{pains}" if pains else ""))

df = pd.DataFrame(rows)
df.to_csv(f"{OUT}/tcm_library_raw.csv", index=False)
ok = df[df["status"] == "OK"]
lib = ok[ok["admet_pass"] == True].reset_index(drop=True) if "admet_pass" in ok.columns else ok.iloc[0:0]
lib.to_csv(f"{OUT}/tcm_library_filtered.csv", index=False)
print(f"\nlookup: {len(df)} entries | resolved in PubChem: {len(ok)} "
      f"| ADMET-passed library: {len(lib)} across {lib['herb'].nunique()} herbs")
print(lib.groupby("herb").size())
