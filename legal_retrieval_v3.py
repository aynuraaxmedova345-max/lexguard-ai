"""Scope-aware retrieval over the existing immutable corpus and hybrid indexes.
Topic routes propose candidates, never prescribe legal outcomes.
"""
from __future__ import annotations
import re
from collections import defaultdict
from contract_analyzer import norm, classify_contract
from retriever import LegalRetriever, uz_tokenize

# Patterns apply to legal topics (positive, negative and ordinary clauses alike).
# Each route: regex, canonical query, primary articles, supporting articles.
ROUTES={
'mehnat':[
(r"bekor turib|ish.{0,35}to'xta|tizim.{0,35}ishlamay|texnik ishlar|ishlamay qol|ish bo'lmay",'bekor turib qolingan vaqt ish beruvchi aybi haq to‘lash',[266],[257]),
(r"ushlab qol|undiruv|chegirib qol",'ish haqidan ushlab qolish asoslari miqdori',[269,270],[]),
(r"ish vaqtidan tashqari|ortiqcha ish|qo'shimcha ish(?:ga| soat)", 'ish vaqtidan tashqari ish haq to‘lash rozilik davomiylik',[262,189,190],[16]),
(r"dastlabki sinov|sinov (?:davri|muddati|belgilan)", 'ishga qabul dastlabki sinov muddati istisno',[130,129,131],[132]),
(r"ta'til",'har yilgi asosiy mehnat ta’tili davomiyligi',[217,218],[16,216]),
(r"ish haqi|ish haqini|mehnatga haq|maosh|bo'nak",'ish haqi to‘lash muddati va miqdori',[253,245],[333]),
(r"ish vaqti|ish haftasi|ish soati|hafta.{0,20}soat|smena",'ish vaqtining normal davomiyligi dam olish',[182,185],[191,207]),
(r"nomuayyan muddat|shartnoma muddati|muddatli mehnat|ishga (?:kirish|boshl)|ish boshlaydi",'mehnat shartnomasining muddati ish boshlanishi',[110,108],[111]),
(r"intizom|jarima|hayfsan|yozma tushuntirish",'intizomiy jazo jarima tushuntirish',[312,313],[]),
(r"kasal|vaqtincha mehnatga layoqat|shtat.{0,25}qisqar",'ish beruvchi tashabbusiga ko‘ra bekor qilish taqiqlari',[163,161],[]),
(r"yakuniy hisob|hisob-kitob|ishdan ketganda",'mehnat shartnomasi bekor qilinganda hisob-kitob',[172,254],[]),
(r"bekor qil|ishdan bo'sha|ishdan ket|iste'fo",'mehnat shartnomasini xodim tashabbusi va ish beruvchi tashabbusi bilan bekor qilish',[160,161],[165,163]),
(r"tungi|kechasi",'tungi vaqtdagi ish uchun haq to‘lash',[264],[]),
(r"ikki nusxa|yozma shakl|ro'yxat|rekvizit|imzo",'mehnat shartnomasi shakli rekvizitlar',[106,107],[127]),
(r"majburiyat|xavfsiz mehnat|jihoz|sug'urta",'ish beruvchi va xodim majburiyatlari',[25,22],[104]),
(r"shartnoma predmeti|lavozim|ish joyi",'mehnat shartnomasi mazmuni',[104,103],[]),
],
'residential':[
(r"soliq|hisobga qo'yish|ro'yxat",'uy-joy ijarasi yozma shakli soliq organida hisobga qo‘yish',[603],[]),
(r"mulkdor.{0,35}o'zgar|sotil|hadya|mulk huquqi.{0,45}o't",'uy-joy mulk huquqi o‘tganida ijara saqlanishi',[604],[]),
(r"ko'chirib chiqar|bo'shat|majburiy chiq",'uy-joy ijarasi tugatilishi sud qarori ko‘chirib chiqarish',[616,615],[]),
(r"muddatidan oldin|bekor qil|ijaradan chiq",'uy-joy ijarasini bekor qilish yozma ogohlantirish',[615,616],[]),
(r"kommunal|suv|elektr|ta'mir|nosoz",'uy-joy ijaraga beruvchi kommunal xizmat ta’mir majburiyatlari',[605,607,610],[]),
(r"ijara haqi|ijara to'lov|oylik.{0,15}to'lov|narx|hisob-kitob",'uy-joy uchun to‘lanadigan haq',[611],[]),
(r"ijara muddati|muddatga ijaraga|yil muddat|oy muddat",'uy-joy ijarasi muddati',[612],[]),
(r"topshirish|predmet|kvartira|xonadon|turar joy",'uy-joy ijarasi obyekti topshirish',[600,602,605],[]),
(r"ijaraga oluvchining majburiyat|asray|qayta qur",'uy-joy ijaraga oluvchi majburiyati',[607],[]),
],
'ijara':[
(r"ijara haqi|to'lov|narx",'mol-mulk ijarasi haq to‘lash',[544],[]),
(r"muddatidan oldin|bekor qil",'mulk ijarasini muddatidan oldin bekor qilish',[551,552],[]),
(r"mulkdor|mulk huquqi",'taraflar o‘zgarganda ijara saqlanishi',[549],[]),
(r"shakl|ro'yxat|hisobga",'mulk ijarasi shakli',[539],[]),
(r"ta'mir|nuqson|kamchilik|nosoz",'ijara kamchiliklari saqlash majburiyati',[542,547,548],[]),
(r"muddat",'mulk ijarasi muddati',[540],[]),
(r"predmet|topshirish",'mulk ijarasi obyekti topshirish',[535,537,541],[]),
],
'oldi_sotdi':[
(r"uchinchi shaxs.{0,140}olib qo'y|olib qo'y.{0,100}uchinchi shaxs",'tovar uchinchi shaxs tomonidan olib qo‘yilganda sotuvchi javobgarligi',[395,394,393],[]),
(r"nuqson|kamchilik|nosoz|sifatsiz|sifati tegishli",'sifati tegishli darajada bo‘lmagan tovar xaridor huquqlari',[408,409],[]),
(r"kafolat|isbotla",'tovar sifat kafolati nuqson uchun isbotlash javobgarligi',[409,403,410],[404]),
(r"axborot|ma'lumot|texnik xususiyat|yo'riqnoma",'sotib oluvchiga tovar haqida axborot va hujjat berish',[427,388],[]),
(r"oldindan.{0,100}(?:to'la|mablag'|o'tkaz)|bo'nak|avans|qaytarilmay",'tovar haqini oldindan to‘lash topshirilmasa qaytarish',[420,419],[]),
(r"yetkaz|topshirma",'tovarni sotib oluvchiga yetkazib berish',[431,389,420],[]),
(r"narx|hisob-kitob|to'lov|bahosi",'tovar bahosi haq to‘lash',[418,419,420],[]),
(r"qabul qilish|butligi|dalolatnoma",'tovar qabul qilish butligi tekshirish',[417,411,407],[]),
(r"predmet|mulk qilib|tovar",'oldi-sotdi shartnomasi predmeti',[386,387],[]),
],
'retail':[
(r"nuqson|kamchilik|nosoz|sifatsiz|sifati tegishli",'chakana savdo nuqsonli tovar almashtirish ta’mirlash narx kamaytirish',[434,408,409],[]),
(r"qaytar|ushlab qol|narx.{0,25}kamaytir",'nuqsonli tovar pulini qaytarish qiymati ushlab qolish',[434,435],[]),
(r"narx|bahosi|hisob-kitob|to'lov",'chakana oldi-sotdi tovar bahosi to‘lash',[432,418,419],[]),
(r"axborot|ma'lumot|texnik xususiyat",'chakana tovar haqida axborot',[427],[]),
],
'xizmat':[
(r"qo'shimcha.{0,40}(?:xizmat|to'lov)|majbur.{0,50}(?:a'zo|xizmat)|ixtiyoriy",'qo‘shimcha haq evaziga xizmatga majburlash maishiy pudrat tatbiqi',[657,708],[]),
(r"imkonsiz|aybi|aybdor|o'tkazilmagan|o'tkazmagan|bajara olma",'xizmatni bajara olmaslik ayb xarajat haq to‘lash',[705,706,707],[]),
(r"zarar|sifat|javobgar",'xizmatni lozim darajada bajarmaslik zarar javobgarlik',[706,707],[]),
(r"bekor qil|muddatidan oldin|tugatish",'haq evaziga xizmat shartnomasini bekor qilish ijrochi buyurtmachi',[707,705],[]),
(r"narx|xizmat qiymati|to'lov|haqini|hisob-kitob",'xizmatlarga haq to‘lash',[705,703],[]),
(r"predmet|mashg'ulot|jadval|xizmat muddati|majburiyat",'haq evaziga xizmat shartnomasi bajarish',[703,704],[]),
],
'nikoh':[
(r"kuchga kir|notari|ro'yxat",'nikoh shartnomasi tuzish kuchga kirish notarial shakl',[30],[]),
(r"kasb|ta'lim|ish joy|sudga murojaat|farzand|bolalar|ko'rishish|tarbiya|ta'minot|moddiy yordam",'nikoh shartnomasi mazmuni shaxsiy nomulkiy bolalar ta’minot sud huquqlari',[31],[]),
(r"kasb|ish joy|ta'lim",'er xotin mashg‘ulot kasb tanlash huquqi',[22],[]),
(r"farzand|bola|ko'rishish|tarbiya",'ota ona bola ko‘rishish tarbiya huquqlari',[66,75,76],[]),
(r"ta'minot|moddiy yordam|layoqatsiz",'er xotinning ta’minot berish majburiyatlari',[117,118],[]),
(r"ulush|umumiy mulk|jamg'arma|daromad|alohida mulk|xarajat|mol-mulk",'nikoh shartnomasi bo‘yicha mulkiy tartib ulush alohida mulk',[31,23,28],[25]),
(r"meros|hadya|nikohgacha",'er xotin shaxsiy mulki',[25,31],[]),
(r"bir tomonlama|bosh tort|bekor qil|o'zgartir",'nikoh shartnomasini o‘zgartirish bekor qilish',[32],[]),
],
}
GENERAL=[(r"nizo|sud tartib",'fuqarolik huquqlarini sud orqali himoya qilish',[10,11]),(r"ikki nusxa|imzo|yozma shakl",'shartnomaning shakli',[366]),(r"kelishuv|shartnoma shartlari",'shartnoma erkinligi',[354])]


def subtype(text, kind=None):
    kind=kind or classify_contract(text); t=norm(text)
    if kind=='ijara':
        if re.search(r"uy-joy|turar joy|kvartira|xonadon|yashash maqsad",t):
            return 'residential_public' if re.search(r"davlat uy-joy fondi|munitsipal|idoraviy uy-joy|aniq maqsadli kommunal",t) else 'residential_private'
    if kind=='oldi_sotdi' and re.search(r"chakana|shaxsiy.{0,40}ehtiyoj|oilaviy.{0,25}ehtiyoj|iste'molchi",t): return 'retail'
    return kind


def semantic_units(text):
    # Preserve parent IDs and complete text; sentence/semicolon units are retrieval queries.
    clean=re.sub(r'^\s*\d+(?:\.\d+)*[.)]?\s+', '',text)
    pieces=[p.strip() for p in re.split(r';\s*|(?<=[.!?])\s+(?=[A-ZА-ЯЎҚҒҲ])',clean) if p.strip()]
    if len(pieces)>1 and len(pieces[0])<65 and len(pieces[0].split())<9 and norm(pieces[0]).rstrip('.') in {'shartnoma predmeti','shartnoma muddati','ijara muddati','ijara haqi','yakuniy qoidalar','dastlabki sinov','ish va dam olish vaqti','mehnatga haq to\'lash','hisob-kitob','narx','kafolat','xizmat qiymati','xizmat muddati'}:
        pieces[1]=pieces[0]+' '+pieces[1]; pieces=pieces[1:]
    return pieces or [text]


def _num(a):
    try:return int(str(a))
    except ValueError:return -1


def scope_score(doc, art, kind, sub):
    n=_num(art)
    if kind=='mehnat':return 0 if doc=='labor' else -100
    if kind=='nikoh':return 0 if doc=='family' else -100
    if doc=='civil_1':return -0.35 if 1<=n<=385 else -2
    if kind=='ijara':
        if sub=='residential_private':
            if doc=='housing':return -7 if 35<=n<=75 else -1.5
            return 1.4 if 600<=n<=616 and n!=601 else (0 if 535<=n<=557 else -5)
        if sub=='residential_public':return 1.1 if doc=='housing' else (0.5 if 600<=n<=616 else -2)
        return 1 if doc=='civil_2' and 535<=n<=616 else -3
    if doc!='civil_2':return -7
    if kind=='oldi_sotdi':
        if 386<=n<=424:return 0.5
        if 425<=n<=436:return 1.1 if sub=='retail' else -0.7
        return -4 if sub=='retail' else (0 if 437<=n<=456 else -4)
    if kind=='xizmat':return 1.3 if 703<=n<=708 else (-0.1 if 631<=n<=665 else -4)
    return 0


def route_topics(text, kind, sub):
    key='residential' if sub.startswith('residential') else kind
    routes=(ROUTES.get('retail',[]) if sub=='retail' else [])+ROUTES.get(key,[])
    q=norm(text); heading=re.sub(r'^\d+[.)]\s*','',q).split('.',1)[0]
    hits=[]
    for order,(pat,canonical,primary,support) in enumerate(routes):
        match=re.search(pat,q)
        if not match:continue
        # Specific patterns and heading matches outrank generic words.
        strength=min(2.0,len(match.group())/15)+ (1.0 if re.search(pat,heading) and len(heading)<100 else 0)
        hits.append((strength,-order,canonical,primary,support))
    return sorted(hits,key=lambda x:(-x[0],-x[1]))


class ScopedRetriever:
    def __init__(self,root,backend='offline'):
        self.eng=LegalRetriever(root,backend)
    def article(self,doc,art):
        rows=[self.eng.rows[i] for i in self.eng.by_article.get((doc,str(art)),[]) if self.eng.rows[i].get('is_active_in_index',True)]
        if not rows:return None
        return {**rows[0],'paragraphs':rows,'article_full_text':'\n'.join(r['text'] for r in rows)}
    def candidates(self,text,kind,sub,top_k=5):
        doc={'mehnat':'labor','nikoh':'family'}.get(kind,'civil_2')
        ids={'mehnat':['labor'],'nikoh':['family'],'ijara':['civil_1','civil_2','housing'],'oldi_sotdi':['civil_1','civil_2'],'xizmat':['civil_1','civil_2']}.get(kind)
        units=semantic_units(text)
        scores=defaultdict(float); reasons=defaultdict(set)
        hits=route_topics(text,kind,sub)
        # Multi-query on independent units, plus canonical legal phrases.
        queries=list(dict.fromkeys([text[:1800]]+[u[:900] for u in units if len(u)>30]+[h[2] for h in hits[:3]]))[:8]
        for q in queries:
            for rank,r in enumerate(self.eng.search(q,top_k=12,document_ids=ids,include_full_article=False,use_domain_hints=False),1):
                k=(r['document_id'],str(r['article_number']));scores[k]+=1.2/(rank+2);reasons[k].add('hybrid')
        for strength,_,canonical,primary,support in hits:
            for j,a in enumerate(primary):
                k=(doc,str(a));scores[k]+=max(2.5,4.5+strength-j*.65);reasons[k].add('topic:'+canonical)
            for a in support:
                k=(doc,str(a));scores[k]+=2.4;reasons[k].add('support')
        if kind not in ('mehnat','nikoh','unknown'):
            for pat,canonical,arts in GENERAL:
                if re.search(pat,norm(text)):
                    for a in arts:
                        k=('civil_1',str(a));scores[k]+=3.4;reasons[k].add('general:'+canonical)
        # Form/subject anchor for introductory contract identity clauses.
        if re.search(r'shartnoma.{0,80}tuzd|shartnoma.{0,80}tuzildi',norm(text)):
            anchor={'mehnat':('labor','103'),'nikoh':('family','29'),'ijara':('civil_2','600' if sub.startswith('residential') else '535'),'oldi_sotdi':('civil_2','425' if sub=='retail' else '386'),'xizmat':('civil_2','703')}.get(kind)
            if anchor:scores[anchor]+=4.5;reasons[anchor].add('contract_definition')
        # Preserve linked scope/exception provisions. Not an assertion of applicability.
        if kind=='xizmat' and ('civil_2','657') in scores:
            scores[('civil_2','708')]=max(scores[('civil_2','708')],scores[('civil_2','657')]+.1);reasons[('civil_2','708')].add('cross_reference')
        if kind=='nikoh' and hits:
            scores[('family','31')]=max(scores[('family','31')],5.2);reasons[('family','31')].add('scope_anchor')
        if kind=='mehnat' and any(a[1] in ('217','262') for a in scores):
            if any(a in [217,262] for h in hits for a in h[3]):
                scores[('labor','16')]=max(scores[('labor','16')],7.8);reasons[('labor','16')].add('worker_guarantee_anchor')
        ranked=sorted(scores,key=lambda k:(-(scores[k]+scope_score(*k,kind,sub)),k))
        out=[]
        for k in ranked:
            a=self.article(*k)
            if a:
                a['retrieval_score']=round(scores[k]+scope_score(*k,kind,sub),4);a['retrieval_reasons']=sorted(reasons[k]);out.append(a)
            if len(out)>=top_k:break
        return out,units
