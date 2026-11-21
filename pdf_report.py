"""Generate a PDF from already available analysis; no model requests."""
import io
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr
from urllib.parse import urlparse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab
from threading import Lock
FONT_LOCK=Lock()

def fonts():
    with FONT_LOCK:
        if 'LexPDF' not in pdfmetrics.getRegisteredFontNames():
            base=Path('/usr/share/fonts/truetype/dejavu')
            if (base/'DejaVuSans.ttf').exists():
                regular,bold=base/'DejaVuSans.ttf',base/'DejaVuSans-Bold.ttf'
            else:
                base=Path(reportlab.__file__).parent/'fonts'; regular,bold=base/'Vera.ttf',base/'VeraBd.ttf'
            pdfmetrics.registerFont(TTFont('LexPDF',str(regular)))
            pdfmetrics.registerFont(TTFont('LexPDFBold',str(bold)))

def make_pdf(result, saved=False):
    fonts(); out=io.BytesIO(); green='#08766B'; grey='#49566A'
    def style(name,size,**kw):
        return ParagraphStyle(name,fontName='LexPDF',fontSize=size,leading=size*1.42,spaceAfter=6,splitLongWords=True,**kw)
    title=ParagraphStyle('title',fontName='LexPDFBold',fontSize=23,leading=28,spaceAfter=12,textColor=colors.HexColor(green))
    body=style('body',10); small=style('small',8.5,textColor=colors.HexColor(grey)); heading=ParagraphStyle('heading',fontName='LexPDFBold',fontSize=12,leading=17,spaceBefore=10,spaceAfter=5,keepWithNext=True,textColor=colors.HexColor(green))
    story=[]
    def p(text,st=body):
        # All text from document/model is escaped, never interpreted as PDF markup.
        text=str(text or '').replace('\x00','').replace('\r','')
        story.append(Paragraph(escape(text).replace('\n','<br/>'),st))
    def link(url):
        try:
            u=urlparse(url)
            if u.scheme=='https' and u.hostname in {'lex.uz','www.lex.uz'} and not u.username and not u.password:
                story.append(Paragraph('<a color="#08766B" href='+quoteattr(url)+'>LexUZ rasmiy manbasini ochish</a>',small))
        except (ValueError,TypeError): pass
    clauses=result.get('clauses',[]); labels={'potential_risk':'Ehtimoliy xavf','no_obvious_risk':'Xavf aniqlanmadi','insufficient_evidence':'Dalil yetarli emas'}
    p('LexGuard AI | Huquqiy tahlil hisoboti',title)
    p('ARXIV: avvalgi V3.0 sinovi; jonli tahlil emas. Arxivda nomuayyan muddat bo‘yicha bitta asossiz xavf mavjud.' if saved else 'Jonli AI tahlili | '+str(result.get('version','V3.1')),heading)
    p(result.get('filename','Shartnoma'));p('Tahlil sanasi (UTC): '+str(result.get('analyzed_at_utc','—')),small)
    p('Qamrov: '+str(len(clauses))+'/'+str(result.get('total_clause_count',len(clauses)))+' birlik',small)
    p('  |  '.join(f'{label}: {sum(c.get("ai_assessment",{}).get("status")==status for c in clauses)}' for status,label in labels.items()))
    p('Dastlabki huquqiy yordam. Xavf aniqlanmagani hujjat to‘liq qonuniyligini tasdiqlamaydi. Korpus amaldagi rasmiy tahrir bilan to‘liq tekshirilmagan.',small)
    for w in result.get('warnings',[]): p(w,small)
    if not result.get('coverage_complete'): p('Qamrov to‘liq emas; qolgan bandlar ko‘rilmagan.',small)
    for c in clauses:
        a=c.get('ai_assessment') or {};status=a.get('status','insufficient_evidence')
        h=ParagraphStyle('clause',parent=heading,textColor=colors.HexColor({'potential_risk':'#A62C37','no_obvious_risk':'#08766B'}.get(status,'#81540C')))
        p(str(c.get('clause_id','Band'))+' | '+labels.get(status,'Dalil yetarli emas'),h)
        p('Asl band: '+str(c.get('text','')))
        if a.get('issue'):p('Xulosa: '+a['issue'])
        if a.get('recommendation'):p('Tavsiya: '+a['recommendation'])
        if a.get('rule_application'):p('Huquqiy mantiq: '+a['rule_application'],small)
        for b in a.get('legal_basis') or []:
            p(str(b.get('document_name','Huquqiy manba'))+' | '+str(b.get('article_number','—'))+'-modda',small)
            p(b.get('evidence_quote','Iqtibos mavjud emas.'),small);link(b.get('source_url',''))
        if not a.get('legal_basis'):p('Tasdiqlangan korpus iqtibosi mavjud emas.',small)
        story.append(Spacer(1,8))
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#DCE5E4'));canvas.line(40,37,A4[0]-40,37);canvas.setFont('LexPDF',8);canvas.setFillColor(colors.HexColor(grey));canvas.drawString(40,23,'LexGuard AI | Dastlabki huquqiy tahlil');canvas.drawRightString(A4[0]-40,23,str(doc.page));canvas.restoreState()
    SimpleDocTemplate(out,pagesize=A4,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=49,title='LexGuard AI - Huquqiy tahlil').build(story,onFirstPage=footer,onLaterPages=footer)
    return out.getvalue()
