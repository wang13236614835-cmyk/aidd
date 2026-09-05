# -*- coding: utf-8 -*-
"""
S4: 天然产物库构建（全新，文献驱动）。
10味药材均不同于旧项目：茵陈/绞股蓝/山楂/泽泻/决明子/葛根/垂盆草/叶下珠/桑叶/虎杖。
依据: 2024-2026 TCM-NAFLD系统综述 + 经典药理文献（research/literature_notes.md）。
流程: 名称清单 -> PubChem PUG-REST (CID+IsomericSMILES) -> RDKit性质过滤 -> 排除清单 -> NP库。
"""
import json, time, urllib.parse, urllib.request
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, Lipinski
from rdkit.Chem import rdMolDescriptors

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_v2_new"

HERBS = {
 "Artemisia capillaris(茵陈)": [
  "scoparone","scopoletin","umbelliferone","capillarisin","arcapillin","isocapillarislactone? no",
 ],
}
# 上面占位; 真正清单如下(去掉无效条目):
HERBS = {
 "Artemisia capillaris(茵陈)": [
  "scoparone","scopoletin","umbelliferone","capillarisin","arcapillin",
  "capillin","capillene","1,2-dimethoxy-4-vinylbenzene","isorhamnetin","methyl capillate"],
 "Gynostemma pentaphyllum(绞股蓝)": [
  "ginsenoside Rb1","ginsenoside Rd","gypenoside XLIX","gynosaponin? no",
  "damulin A","damulin B","2alpha-hydroxyprotopanaxadiol? no","spinasterol","stigmasterol"],
 "Crataegus pinnatifida(山楂)": [
  "vitexin","isovitexin","hyperoside","isoquercitrin","epicatechin","procyanidin B2",
  "ursolic acid","oleanolic acid","corosolic acid","maslinic acid","tormentic acid"],
 "Alisma orientale(泽泻)": [
  "alisol A","alisol B","alisol C","alisol A acetate","alisol B acetate","alisol C acetate",
  "16-oxo-alisol A","alisol E acetate","alismol","alismoxide"],
 "Cassia obtusifolia(决明子)": [
  "obtusifolin","obtusin","aurantio-obtusin","chryso-obtusin","2-hydroxy-1,8-dimethoxy? no",
  "rubrofusarin","nigrofusarin","toralactone","cassiaside C? no","cassiatoroside? no"],
 "Pueraria lobata(葛根)": [
  "puerarin","daidzein","daidzin","genistin","formononetin","biochanin A",
  "3'-methoxydaidzein","puerarin-6-O-xyloside? no","ononin"],
 "Sedum sarmentosum(垂盆草)": [
  "sarmentosin","N-methylalloxanthine","isovitexin? dup-ok","sedoheptulose? no",
  "methyl gallate? excl-pan","sarmentosic acid? no"],
 "Phyllanthus niruri(叶下珠)": [
  "phyllanthin","hypophyllanthin","nirtetralin","niranthin","phytetralin",
  "nirurinetin? no","5-demethoxyniranthin? no"],
 "Morus alba(桑叶)": [
  "1-deoxynojirimycin","oxyresveratrol","astragalin","isoquercitrin-dup-ok",
  "moracin N","moracin M","mulberrofuran G","sanggenon D? no"],
 "Polygonum cuspidatum(虎杖)": [
  "piceid","catechin","emodin-8-O-glucoside? big","torachrysone","2-methoxy-6-acetyl-7-methyljuglone? no",
  "xanthhumol? no"],
}
# 清洗掉带"? no"/"dup-ok"的占位与不确定条目
clean = {}
for h, lst in HERBS.items():
    items = [c.strip() for c in lst if "?" not in c and c.strip()]
    # 去重(同药内)
    seen, keep = set(), []
    for c in items:
        k = c.lower()
        if k not in seen:
            seen.add(k); keep.append(c)
    clean[h] = keep
HERBS = clean

EXCLUDE = {  # 泛活性/集落干扰清单(全新定义, 适用于本项目)
 "quercetin","kaempferol","luteolin","apigenin","genistein","curcumin","resveratrol",
 "epigallocatechin gallate","emodin","aloe-emodin","rhein","physcion","chrysophanol",
 "gallic acid","ellagic acid","chlorogenic acid","caffeic acid","ferulic acid",
 "vanillic acid","protocatechuic acid","salvianolic acid b","rosmarinic acid",
 "methyl gallate","berberine",
}

PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"
HDR = {"User-Agent": "academic-np-screening/2.0 (fresh independent project)"}

def lookup(name):
    q = urllib.parse.quote(name)
    for att in range(4):
        try:
            url = f"{PUG}/{q}/property/IsomericSMILES,MolecularWeight/JSON"
            r = urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=40)
            js = json.loads(r.read())
            p = js["PropertyTable"]["Properties"][0]
            smi = p.get("IsomericSMILES") or p.get("SMILES") or p.get("CanonicalSMILES")
            return dict(smiles=smi, mw_pubchem=p.get("MolecularWeight"), cid=p.get("CID"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (att + 1))
        except Exception:
            time.sleep(2 * (att + 1))
    return None

rows = []
total = sum(len(v) for v in HERBS.values())
print(f"total entries: {total} across {len(HERBS)} herbs")
for herb, lst in HERBS.items():
    for nm in lst:
        low = nm.lower()
        if low in EXCLUDE:
            rows.append(dict(herb=herb, name=nm, status="EXCLUDED_PANASSAY"))
            continue
        info = lookup(nm)
        time.sleep(0.4)
        if info is None or not info.get("smiles"):
            rows.append(dict(herb=herb, name=nm, status="PUBCHEM_NOT_FOUND"))
        else:
            rows.append(dict(herb=herb, name=nm, status="OK", **info))
raw = pd.DataFrame(rows)
raw.to_csv(f"{D}/data/tcm/np_library_raw.csv", index=False)
print(raw.status.value_counts().to_string())

# ---------- 性质过滤 ----------
def props(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    return dict(mw=Descriptors.MolWt(m), logp=Crippen.MolLogP(m),
                hbd=Lipinski.NumHDonors(m), hba=Lipinski.NumHAcceptors(m),
                rotb=Lipinski.NumRotatableBonds(m), tpsa=rdMolDescriptors.CalcTPSA(m))

ok = raw[raw.status == "OK"].copy()
pr = ok["smiles"].apply(lambda s: props(s) if isinstance(s, str) else None)
for k in ["mw", "logp", "hbd", "hba", "rotb", "tpsa"]:
    ok[k] = [p[k] if p else None for p in pr]

def num(r, k, default):
    v = getattr(r, k)
    return default if pd.isna(v) else v

def admet(r):
    """NP友好阈值(全新设定): 150<=MW<=700, LogP<=7.5(容纳三萜酸), HBD<=10, HBA<=14, RotB<=12, TPSA<=240"""
    fails = []
    if not (150 <= num(r, "mw", 0) <= 700): fails.append("MW")
    if num(r, "logp", 99) > 7.5: fails.append("LogP")
    if num(r, "hbd", 99) > 10: fails.append("HBD")
    if num(r, "hba", 99) > 14: fails.append("HBA")
    if num(r, "rotb", 99) > 12: fails.append("RotB")
    if num(r, "tpsa", 999) > 240: fails.append("TPSA")
    return ";".join(fails)

ok["admet_fail"] = ok.apply(admet, axis=1)
lib = ok[ok.admet_fail == ""].copy()
print(f"\nADMET pass: {len(lib)}/{len(ok)}")
print(lib.groupby("herb").size().to_string())
lib.to_csv(f"{D}/data/tcm/np_library_filtered.csv", index=False)
ok.to_csv(f"{D}/data/tcm/np_library_resolved.csv", index=False)
json.dump(dict(entries=total, resolved=int(len(ok)), passed=int(len(lib)),
               per_herb=lib.groupby("herb").size().to_dict()),
          open(f"{D}/results/tables/s4_summary.json", "w"), indent=1, ensure_ascii=False)
print("saved np_library_filtered.csv")
