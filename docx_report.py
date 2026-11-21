"""Build an editable Word report from existing validated analysis, no API call."""
import io, re
from urllib.parse import urlparse
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

LABELS={'potential_risk':'Ehtimoliy xavf','no_obvious_risk':'Xavf aniqlanmadi','insufficient_evidence':'Dalil yetarli emas'}
COLORS={'potential_risk':'A62C37','no_obvious_risk':'08766B','insufficient_evidence':'81540C'}
def clean(s): return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]', '',str(s or ''))
def make_docx(r):
    d=Document(); sec=d.sections[0]
    sec.top_margin=sec.bottom_margin=Inches(.65); sec.left_margin=sec.right_margin=Inches(.75)
    sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
    normal=d.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(11);normal.paragraph_format.space_after=Pt(6)
    d.styles['Title'].font.color.rgb=RGBColor.from_string('08766B')
    d.add_heading('LexGuard AI',0);d.add_paragraph('Shartnoma tahlili hisoboti',style='Subtitle')
    d.add_paragraph(clean(r.get('filename','Shartnoma')))
    cs=r.get('clauses',[])
    d.add_paragraph(' | '.join(f'{v}: {sum((c.get("ai_assessment") or {}).get("status")==k for c in cs)}' for k,v in LABELS.items()))
    d.add_paragraph('Dastlabki huquqiy yordam. Xavf aniqlanmagani to‘liq qonuniylikni tasdiqlamaydi. Korpus rasmiy amaldagi tahrir bilan to‘liq solishtirilmagan.')
    if r.get('coverage_complete') is False or len(cs)<(r.get('total_clause_count') or len(cs)):
        d.add_paragraph(f'{len(cs)}/{r.get("total_clause_count",len(cs))} ta birlik tekshirildi. Qolgan bandlar tahlil qilinmagan.')
    for w in r.get('warnings') or []: d.add_paragraph(clean(w))
    def para(head,text):
        p=d.add_paragraph();p.add_run(head+' ').bold=True;p.add_run(clean(text));return p
    for c in cs:
        a=c.get('ai_assessment') or {};s=a.get('status','insufficient_evidence')
        h=d.add_heading(level=2);run=h.add_run(clean(c.get('clause_id','Band'))+' · '+LABELS.get(s,LABELS['insufficient_evidence']));run.font.color.rgb=RGBColor.from_string(COLORS.get(s,'81540C'))
        para('Asl band:',c.get('text'))
        para('Xulosa:',a.get('issue'));para('Tavsiya:',a.get('recommendation'))
        if a.get('rule_application'):para('Huquqiy asoslash:',a['rule_application'])
        for b in a.get('legal_basis') or []:
            para('Huquqiy manba:',f'{b.get("document_name","Manba")} · {b.get("article_number","—")}-modda')
            d.add_paragraph(clean(b.get('evidence_quote')))
            try:
                u=urlparse(b.get('source_url') or '')
                if u.scheme=='https' and u.hostname in {'lex.uz','www.lex.uz'} and not u.username and not u.password:
                    p=d.add_paragraph();link=OxmlElement('w:hyperlink');link.set(qn('r:id'),p.part.relate_to(u.geturl(),RT.HYPERLINK,is_external=True));rr=OxmlElement('w:r');rp=OxmlElement('w:rPr');color=OxmlElement('w:color');color.set(qn('w:val'),'08766B');rp.append(color);rr.append(rp);t=OxmlElement('w:t');t.text='LexUZ rasmiy manbasi';rr.append(t);link.append(rr);p._p.append(link)
            except (ValueError,TypeError):pass
        if not a.get('legal_basis'):d.add_paragraph('Tasdiqlangan korpus iqtibosi mavjud emas.')
    foot=sec.footer.paragraphs[0];foot.add_run('LexGuard AI · Dastlabki huquqiy tahlil  |  ');field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');foot._p.append(field)
    d.core_properties.title='LexGuard AI — Shartnoma tahlili';d.core_properties.author='LexGuard AI'
    out=io.BytesIO();d.save(out);return out.getvalue()
