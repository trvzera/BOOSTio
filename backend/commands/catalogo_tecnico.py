"""Administração local do catálogo técnico, sem rotas públicas."""
import json
from pathlib import Path
import click
from sqlalchemy.exc import SQLAlchemyError
from models import FichaTecnicaCatalogo
from models.ficha_tecnica_catalogo import ESTADOS_FICHA
from migrations.catalogo_tecnico import preparar_catalogo_tecnico
from services.catalogo_tecnico_service.importar_base_tecnica_service import ImportarBaseTecnicaService
from services.catalogo_tecnico_service.revisar_ficha_service import RevisarFichaService


def registrar_comandos_catalogo_tecnico(app):
    @app.cli.command('catalogo-tecnico-preparar')
    @click.option('--aplicar', is_flag=True)
    def preparar(aplicar):
        """Simula a migração. --aplicar confirma as alterações do esquema."""
        try:
            click.echo(json.dumps(preparar_catalogo_tecnico(simular=not aplicar),ensure_ascii=False))
        except (ValueError,SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro,ValueError) else 'Falha ao preparar esquema técnico') from None

    @app.cli.command('catalogo-tecnico-importar')
    @click.option('--arquivo',required=True,type=click.Path(exists=True,dir_okay=False))
    @click.option('--aplicar',is_flag=True)
    def importar(arquivo,aplicar):
        """Lê JSON interno v1 (objeto ou lista de até 1000 fichas). Simula por padrão."""
        try:
            caminho=Path(arquivo)
            if caminho.stat().st_size>10*1024*1024:raise ValueError('Arquivo excede 10 MiB')
            documentos=json.loads(caminho.read_text(encoding='utf-8'))
            if isinstance(documentos,dict):documentos=[documentos]
            if not isinstance(documentos,list) or not 1<=len(documentos)<=1000:raise ValueError('Informe entre 1 e 1000 fichas')
            service=ImportarBaseTecnicaService()
            documentos=[service.normalizar(d) for d in documentos]
            origens=[(d['provedor'],d['id_externo']) for d in documentos]
            if len(set(origens))!=len(origens):raise ValueError('Origem duplicada no lote; separe versões para revisão')
            resumo={'simulacao':not aplicar,'processadas':0,'falhas':0,'acoes':{},'detalhes':[]}
            for documento in documentos:
                try:
                    r=service.processar(documento,simular=not aplicar)
                    resumo['acoes'][r['acao']]=resumo['acoes'].get(r['acao'],0)+1
                    resumo['detalhes'].append(r);resumo['processadas']+=1
                except (ValueError,SQLAlchemyError):
                    resumo['falhas']+=1
                    resumo['detalhes'].append({'provedor':documento['provedor'],'id_externo':documento['id_externo'],'acao':'falha'})
                    break
            click.echo(json.dumps(resumo,ensure_ascii=False))
            if resumo['falhas']:raise click.ClickException('Lote interrompido; fichas anteriores já foram concluídas. Consulte o resumo')
        except (OSError,UnicodeError,ValueError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro,ValueError) else 'Não foi possível ler o arquivo') from None

    @app.cli.command('catalogo-tecnico-listar')
    @click.option('--estado',type=click.Choice(ESTADOS_FICHA))
    @click.option('--depois-id',default=0,type=click.IntRange(min=0))
    @click.option('--limite',default=50,type=click.IntRange(1,200))
    def listar(estado,depois_id,limite):
        try:
            click.echo(json.dumps([f.resumo() for f in FichaTecnicaCatalogo.listar(estado=estado,depois_id=depois_id,limite=limite)],ensure_ascii=False))
        except SQLAlchemyError:raise click.ClickException('Prepare o esquema técnico antes de listar') from None

    @app.cli.command('catalogo-tecnico-revisar')
    @click.option('--id', 'identificador',required=True,type=click.IntRange(min=1))
    @click.option('--acao',required=True,type=click.Choice(['aprovar','rejeitar','reabrir']))
    @click.option('--responsavel',required=True)
    @click.option('--motivo',required=True)
    @click.option('--aplicar',is_flag=True)
    def revisar(identificador,acao,responsavel,motivo,aplicar):
        """Revalida antes de aprovar; nunca ignora conflitos. Simula por padrão."""
        try:
            r=RevisarFichaService().executar(identificador,acao,responsavel=responsavel,motivo=motivo,simular=not aplicar)
            click.echo(json.dumps(r,ensure_ascii=False))
        except (ValueError,SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro,ValueError) else 'Falha ao revisar ficha') from None
