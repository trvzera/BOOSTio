from pathlib import Path
import argparse, shutil, zipfile, json, re
from xml.etree import ElementTree
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader

root=Path(__file__).resolve().parents[4]
task=root/'materiais/apresentacao/2026-11-10'
parser=argparse.ArgumentParser(description='Prepara o pacote da apresentação a partir do PowerPoint e dos slides exportados.')
parser.add_argument('--exports',type=Path,required=True,help='Pasta com BOOSTio-Pitch-3A2.pptx e slide-1.png até slide-20.png.')
exports=parser.parse_args().exports.expanduser().resolve()
if not exports.is_dir():parser.error('A pasta de slides exportados não existe.')
generated=root/'materiais/exportacoes/apresentacao'
intermediates=generated/task.name/'build'
intermediates.mkdir(parents=True,exist_ok=True)
stage=generated/'BOOSTio-Pitch-CMI'
if stage.exists():
    n=2
    while stage.with_name(stage.name+f'-v{n}').exists():n+=1
    stage=stage.with_name(stage.name+f'-v{n}')
for sub in ['01-Apresentacao','02-Roteiros','03-Telas-do-site','04-Marca-e-uniforme','05-Diagrama','06-Slides-em-PNG/Apoio']:
    (stage/sub).mkdir(parents=True,exist_ok=True)

pptx=exports/'BOOSTio-Pitch-3A2.pptx'
with zipfile.ZipFile(pptx) as archive:
    assert archive.testzip() is None
    slides=[name for name in archive.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',name)]
    assert len(slides)==20,len(slides)
    hidden=[]
    for name in archive.namelist():
        if name.endswith('.xml'): ElementTree.fromstring(archive.read(name))
    for name in slides:
        if ElementTree.fromstring(archive.read(name)).get('show')=='0':hidden.append(name)
    assert len(hidden)==3,hidden
shutil.copy2(pptx,stage/'01-Apresentacao'/pptx.name)

pdf=stage/'01-Apresentacao/BOOSTio-Pitch-3A2-previa.pdf'
doc=canvas.Canvas(str(pdf),pagesize=(960,540),pageCompression=1)
doc.setTitle('BOOSTio - Pitch 3A2')
doc.setAuthor('Equipe BOOSTio - Turma 3A2')
doc.setSubject('Previa visual dos 17 slides do pitch. Arquivo editavel no PowerPoint que acompanha este pacote.')
for index in range(1,18):
    source=exports/f'slide-{index}.png'
    assert source.is_file(),source
    doc.drawImage(ImageReader(str(source)),0,0,width=960,height=540)
    doc.bookmarkPage(f'slide-{index}')
    doc.addOutlineEntry(f'Slide {index:02d}',f'slide-{index}',level=0)
    doc.showPage()
doc.save()
assert len(PdfReader(str(pdf)).pages)==17

for source in (task/'roteiros').iterdir():
    if source.is_file(): shutil.copy2(source,stage/'02-Roteiros'/source.name)
for source in (task/'assets').iterdir():
    if source.is_file():shutil.copy2(source,stage/'03-Telas-do-site'/source.name)
shutil.copy2(root/'materiais/brand/LOGO1V2-PNG_00000.png',stage/'04-Marca-e-uniforme/logo-oficial-BOOSTio.png')
shutil.copy2(root/'materiais/brand/uniformes/boostio-polo-preta-logo-detalhes-azuis.png',stage/'04-Marca-e-uniforme/polo-preta-logo-detalhes-azuis.png')
for ext in ['png','dot']:shutil.copy2(root/f'docs/diagrama-classes.{ext}',stage/f'05-Diagrama/diagrama-classes.{ext}')
for index in range(1,21):
    source=exports/f'slide-{index}.png'
    dest=stage/'06-Slides-em-PNG'/('Apoio' if index>17 else '')/f'slide-{index:02d}.png'
    shutil.copy2(source,dest)
(stage/'LEIA-ME.txt').write_text('''BOOSTio - Pitch 3A2 e preparacao para o CMI

01-Apresentacao
PowerPoint editavel: 17 slides do pitch e 3 slides de apoio ocultos.
PDF: previa visual dos 17 slides principais, sem os slides de apoio.
As notas do PowerPoint incluem tempo e apresentador sugerido.

02-Roteiros
Falas e divisao da equipe, ideias para o CMI e pendencias tecnicas da rubrica.
O tempo planejado e de 6min30, incluindo uma demonstracao de 1min50.

03-Telas-do-site
Capturas da interface real com respostas de API e dados demonstrativos.
Detalhes da origem em origem-telas.json.

04-Marca-e-uniforme
Logo oficial e mockup final da polo preta com logo e detalhes azuis.

05-Diagrama
Diagrama de montagem existente em PNG e fonte editavel DOT.

06-Slides-em-PNG
Imagens individuais dos slides. Os tres slides de apoio ficam em Apoio/.

Antes de apresentar, conferir pendencias-da-rubrica.md.
O video da demonstracao real ainda precisa ser gravado e nao esta neste pacote.
''',encoding='utf-8')
(intermediates/'pacote-info.json').write_text(json.dumps({'stage':str(stage),'pdf':str(pdf),'pptx':str(stage/'01-Apresentacao'/pptx.name),'files':sum(1 for p in stage.rglob('*') if p.is_file())},ensure_ascii=False),encoding='utf-8')
print(json.dumps({'stage':str(stage),'pdf':str(pdf),'slides_pptx':20,'slides_ocultos':3,'paginas_pdf':17},ensure_ascii=False))
