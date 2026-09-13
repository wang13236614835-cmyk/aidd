# -*- coding: utf-8 -*-
"""Download all human FASN ChEMBL activity records for censor/relation audit."""
from pathlib import Path
import json, time, urllib.parse, urllib.request

BASE='https://www.ebi.ac.uk/chembl/api/data/activity.json'
OUT=Path(r'D:/zcode-workspace/aidd-repo-work/00-当前研究/final_strategy_round_20260912/raw')
OUT.mkdir(parents=True,exist_ok=True)
records=[]; offset=0; limit=1000; total=None
while True:
    params={'target_chembl_id':'CHEMBL4158','limit':limit,'offset':offset}
    url=BASE+'?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={'User-Agent':'MASH-final-strategy-audit/2026'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req,timeout=120) as h:
                d=json.loads(h.read().decode('utf-8'))
            break
        except Exception:
            if attempt==3: raise
            time.sleep(2**attempt)
    page=d.get('activities',[]); records.extend(page)
    total=d.get('page_meta',{}).get('total_count',total)
    print('offset',offset,'page',len(page),'total',total)
    if not page or offset+len(page)>=total: break
    offset += len(page); time.sleep(.5)
out={'query_date':'2026-09-12','target_chembl_id':'CHEMBL4158','total_count':len(records),'records':records}
(OUT/'FASN_all_activity_records.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('saved',len(records))
