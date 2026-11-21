"""Run only previously problematic clauses. Not a new independent benchmark."""
import json
from pathlib import Path
from openai_analyzer_v31 import analyze_contract_openai
from legal_retrieval_v3 import ScopedRetriever
# ground truth remains outside the AI request; only clause IDs select workload
TARGETS={'01':['C04'],'02':['C05','C09','C18'],'03':['C07','C09','C10','C11'],'04':['C10','C12'],'05':['C07','C09','C10','C11'],'06':['C03','C04'],'07':['C03','C07','C09']}
def run_targeted(package,project,client,out,ids=('01','02','03','04','05','06','07'),backend='chroma'):
    package,project,out=map(Path,(package,project,out));out.mkdir(parents=True,exist_ok=True)
    engine=ScopedRetriever(project,backend)
    results={}
    for i in ids:
        matches=list((package/'contracts').glob(f'* {i}.docx'))
        if len(matches)!=1:raise ValueError(f'{i}: asl fayl topilmadi yoki takrorlangan')
        r=analyze_contract_openai(matches[0],client=client,project_root=project,backend=backend,retriever=engine,consent=True,review=True,clause_ids=TARGETS[i])
        results[i]=r
        (out/f'{i}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
        for c in r['clauses']:
            a=c['ai_assessment']; print(i,c['clause_id'],a['status'],a['diagnostic_reason'],[(e['document_id'],e['article_number']) for e in a['legal_basis']],flush=True)
        print('API calls:',r['api_calls'],'errors:',len(r['api_errors']),flush=True)
    return results
