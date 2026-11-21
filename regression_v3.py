"""Offline retrieval regression only; not model accuracy or held-out evaluation."""
from pathlib import Path
import json,sys
from contract_analyzer import extract_contract_text,split_clauses,classify_contract
from legal_retrieval_v3 import ScopedRetriever,subtype
from openai_analyzer_v3 import prepare_clause
ROOT=Path(__file__).resolve().parent
GOLD={
 'Mehnat shartnomasi 01.docx':('labor',{'C04':['130'],'C05':['182'],'C06':['253'],'C07':['262'],'C08':['217'],'C10':['160']}),
 'Mehnat shartnomasi 02.docx':('labor',{'C08':['312'],'C09':['266'],'C12':['264'],'C14':['270'],'C16':['313'],'C17':['163'],'C18':['172','254']}),
 'Ijara shartnomasi 03.docx':('civil_2',{'C03':['612'],'C05':['603'],'C07':['605'],'C09':['604'],'C10':['615'],'C11':['616']}),
 'Oldi-sotdi shartnomasi 04.docx':('civil_2',{'C04':['427'],'C06':['420'],'C08':['409'],'C09':['408','434'],'C10':['434'],'C12':['395']}),
 'Xizmat korsatish shartnomasi 05.docx':('civil_2',{'C05':['705'],'C07':['706'],'C08':['707'],'C09':['707'],'C10':['705','707']}),
 'Nikoh shartnomasi 06.docx':('family',{'C03':['30'],'C05':['31'],'C07':['31'],'C09':['31'],'C11':['31'],'C12':['32']}),
 'Mehnat shartnomasi 07.docx':('labor',{}),
}
def run(folder,backend='offline'):
 engine=ScopedRetriever(ROOT,backend);records=[];tests=[]
 for filename,(doc,expected) in GOLD.items():
  t=extract_contract_text(Path(folder)/filename);kind=classify_contract(t);sub=subtype(t,kind);clauses=split_clauses(t,1000)
  tests.append({'file':filename,'type':kind,'subtype':sub,'clauses':len(clauses)})
  for c in clauses:
   a,u=engine.candidates(c['text'],kind,sub,5);found=[(r['document_id'],r['article_number']) for r in a]
   if c['clause_id'] in expected:
    targets=expected[c['clause_id']];hit=any((doc,n) in found for n in targets)
    records.append({'file':filename,'clause':c['clause_id'],'expected_any':[(doc,n) for n in targets],'retrieved':found,'hit':hit})
   if filename.startswith('Oldi-sotdi') and c['clause_id']=='C10':
    assert 'civil_2:434:0007' in prepare_clause(c,a,u)['_evidence']
  assert set(expected)<={c['clause_id'] for c in clauses}
 return {'backend':backend,'method':'development regression, any expected article in top 5; no live LLM evaluation; special law case excluded','document_count':len(tests),'clause_count':sum(r['clauses'] for r in tests),'expected_count':len(records),'hits':sum(r['hit'] for r in records),'tests':tests,'details':records}
if __name__=='__main__':
 report=run(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else 'offline');print(json.dumps(report,ensure_ascii=False,indent=2))
