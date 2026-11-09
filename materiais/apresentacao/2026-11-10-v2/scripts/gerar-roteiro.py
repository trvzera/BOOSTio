from pathlib import Path
from xml.sax.saxutils import escape
import json, shutil
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT=Path('/Users/trvzera/Desktop/BOOSTio')
SRC=ROOT/'materiais/apresentacao/2026-11-10-v2'
OUT=ROOT/'materiais/exportacoes/apresentacao/2026-11-10-v2'
URL='https://docs.google.com/presentation/d/1v7uBdnImOjQyGoJw894cq6zYIyeRh4UGZs4FQOSNMck/edit'
notes=json.loads((SRC/'roteiros/notas-slides.json').read_text())
assert len(notes)==17 and sum(n['tempo'] for n in notes)==390
def clock(n): return f'{n//60}:{n%60:02d}'
now=0
for n in notes:
    n['inicio']=clock(now);now+=n['tempo'];n['fim']=clock(now)

md=['# BOOSTio · Roteiro da apresentação · 3A2','',
    'Versão revisada em 09/11/2026 para a apresentação de 10/11/2026.',
    '',f'Google Apresentações: {URL}','','**17 slides · 6min30 no total · vídeo principal de 1min50 incluído · margem de 30s até 7min.**','',
    '## Como usar este roteiro','', 'Os slides são apoio visual. Falar com a banca, usando as telas, os diagramas e os GIFs para demonstrar o que está sendo explicado. Não ler os textos do slide nem os nomes completos da equipe. As falas abaixo são uma base natural para ensaiar; os comandos entre colchetes são ações de demonstração, não frases para ler.','', '## Divisão das falas','',
    '- Arthur Ferreira Raymundo: slides 1–7, 0:00–1:15 (1min15).',
    '- Gustavo Azevedo Oliveira: slides 8–10, 1:15–2:35 (1min20).',
    '- Gustavo Lopes Horta: slides 11–12, 2:35–3:30 (55s).',
    '- Giovanni de Castro Morais Trivellato: slide 13, 3:30–5:20 (1min50).',
    '- Kayky Luiz Ferreira de Paula da Silva: slides 14–17, 5:20–6:30 (1min10).','',
    'O tempo é um planejamento de ensaio, não uma duração de fala medida. Reproduzir os trechos curtos durante a fala. A narração do slide 13 acompanha o vídeo e não acrescenta outros 110 segundos.','']
for n in notes:
    md += [f"## {n['slide']:02d}. {n['title']} · {n['inicio']}–{n['fim']} · {n['tempo']}s",'',
           f"**{n['apresentador']}**",'',n['fala'],'']
md += ['## Ajustes antes do ensaio','',
       '- Inserir os vídeos/GIFs reais. Os espaços estão preparados, sem gravações simuladas.',
       '- No bloco de comparação da demo, substituir a indicação entre colchetes pelo resultado observado na gravação.',
       '- A escrita manual ainda acessa a Model, sem Repository. Não apresentar essa adequação como concluída.',
       '- Preços são da última consulta e não incluem frete; consumo é estimativa.',
       '- Só reivindicar IA funcional após a execução real; consentimento precisa de registro no servidor.',
       '- Notas técnicas e fontes de cada slide estão nas notas do apresentador e em notas-slides.json.',
       '- Consultar materiais-pendentes.md e guia-de-gravacao.md para as mídias.','']
(SRC/'roteiros/roteiro-da-apresentacao.md').write_text('\n'.join(md),encoding='utf-8')

pdfmetrics.registerFont(TTFont('Poppins',str(OUT/'fonts/Poppins-Regular.ttf')))
blue=HexColor('#007BFF');ink=HexColor('#15171B');gray=HexColor('#616570')
styles={
 'title':ParagraphStyle('title',fontName='Poppins',fontSize=24,leading=30,textColor=ink,spaceAfter=14),
 'sub':ParagraphStyle('sub',fontName='Poppins',fontSize=11,leading=16,textColor=gray,spaceAfter=16),
 'head':ParagraphStyle('head',fontName='Poppins',fontSize=12.5,leading=17,textColor=blue,spaceBefore=10,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='Poppins',fontSize=10.7,leading=15.2,textColor=ink,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Poppins',fontSize=9.5,leading=14,textColor=gray,spaceAfter=8)
}
def para(t,sty='body'): return Paragraph(escape(t).replace('\n','<br/>'),styles[sty])
def footer(c,d):
    c.setFillColor(gray);c.setFont('Poppins',8)
    c.drawString(44,28,'BOOSTio · 3A2 · Roteiro para ensaio · 09/11/2026')
    c.drawRightString(A4[0]-44,28,str(d.page))
story=[para('BOOSTio\nRoteiro da apresentação','title'),para('Colégio Cotemig · 3A2\nApresentação de 10/11/2026','sub'),
       para('6min30 planejados','head'),para('17 slides, com demonstração de 1min50 incluída. O limite é de 7 minutos; os 30 segundos restantes servem de margem para as transições.'),
       para('Divisão das falas','head')]
groups=[]
for name in dict.fromkeys(n['apresentador'] for n in notes):
    group=[n for n in notes if n['apresentador']==name];groups.append(group)
    story += [para(name,'body'),para(f"Slides {group[0]['slide']}–{group[-1]['slide']} · {group[0]['inicio']}–{group[-1]['fim']}",'small')]
story += [Spacer(1,9),para('Antes de apresentar','head'),para('Inserir as gravações reais e ensaiar com os vídeos rodando. Os trechos dos casos de uso passam durante a fala. O vídeo principal ocupa todo o bloco de Giovanni, com a narração sincronizada.'),
          para('As notas técnicas e as fontes estão nas notas dos slides. A lista de materiais pendentes e o guia de gravação são arquivos separados.','small')]
for group in groups:
    story.append(PageBreak());story.append(para(group[0]['apresentador'],'title'))
    story.append(para(f"Slides {group[0]['slide']}–{group[-1]['slide']} · {group[0]['inicio']}–{group[-1]['fim']}",'sub'))
    for n in group:
        story.append(KeepTogether([para(f"{n['slide']:02d} · {n['title']} · {n['tempo']}s",'head'),para(n['fala'])]))
    if group[0]['slide']==13:
        story += [para('Para sincronizar','head'),para('Iniciar o vídeo na passagem de Gustavo Horta. Os quatro blocos têm 35s, 25s, 25s e 25s. No bloco de comparação, trocar o trecho entre colchetes pelo resultado real gravado. Mostrar o controle de acesso no compartilhamento.','small')]
    if group[0]['slide']==8:
        story += [para('Nota técnica','head'),para('A escrita de BuildSalva ainda não usa Repository, e o histórico também tem leitura direta na Model. As falas descrevem essa limitação; não apresentar a adequação como pronta.','small')]
pdf=OUT/'Roteiro-BOOSTio-3A2-v2.pdf'
SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=44,bottomMargin=48,title='BOOSTio · Roteiro do pitch 3A2',author='Equipe BOOSTio').build(story,onFirstPage=footer,onLaterPages=footer)
shutil.copyfile(OUT/'build/google-render/presentation.pdf',OUT/'BOOSTio-Pitch-3A2-v2.pdf')
assert len(PdfReader(str(OUT/'BOOSTio-Pitch-3A2-v2.pdf')).pages)==17
print(json.dumps({'roteiro_paginas':len(PdfReader(str(pdf)).pages),'slides_paginas':17,'tempo':390},ensure_ascii=False))
