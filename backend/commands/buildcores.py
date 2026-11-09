"""Cruzamento administrativo do catálogo; sem rotas públicas ou execução automática."""
import json
from pathlib import Path
import click
from sqlalchemy.exc import SQLAlchemyError
from services.buildcores_service.cruzar_catalogo_service import CruzarCatalogoBuildcoresService
from services.buildcores_service.baixar_snapshot_service import BaixarSnapshotBuildcoresService


def registrar_comandos_buildcores(app):
    @app.cli.command('buildcores-importar')
    @click.option('--pasta',required=True,type=click.Path(exists=True,file_okay=False))
    @click.option('--aplicar',is_flag=True)
    @click.option('--resumo',required=True,type=click.Path(dir_okay=False))
    @click.option('--lote',default=100,type=click.IntRange(1,1000))
    def importar(pasta,aplicar,resumo,lote):
        """Importa fichas nativas; simula por padrão, sem preços, ofertas ou aprovações."""
        from services.buildcores_service.importar_catalogo_service import ImportarCatalogoBuildcoresService
        try:
            if not Path(resumo).parent.is_dir():raise ValueError('Pasta do resumo não existe')
            r=ImportarCatalogoBuildcoresService().executar(pasta,simular=not aplicar,tamanho_lote=lote)
            Path(resumo).write_text(json.dumps(r,ensure_ascii=False,indent=2))
            click.echo(json.dumps({k:v for k,v in r.items() if k!='detalhes'},ensure_ascii=False))
            if r['interrompido']:raise click.ClickException('Importação interrompida; consulte o resumo. Lotes anteriores já foram confirmados')
        except (ValueError,OSError,SQLAlchemyError) as erro:raise click.ClickException(str(erro) if isinstance(erro,ValueError) else 'Falha de leitura ou persistência') from None

    @app.cli.command('buildcores-baixar')
    @click.option('--pasta',required=True,type=click.Path(file_okay=False))
    @click.option('--commit',default=None)
    def baixar(pasta,commit):
        try:click.echo(json.dumps(BaixarSnapshotBuildcoresService().executar(pasta,commit=commit)))
        except (OSError,ValueError,KeyError):raise click.ClickException('Não foi possível baixar um snapshot válido') from None

    @app.cli.command('buildcores-cruzar')
    @click.option('--pasta',required=True,type=click.Path(exists=True,file_okay=False))
    @click.option('--aplicar',is_flag=True)
    @click.option('--resumo',required=True,type=click.Path(dir_okay=False))
    def cruzar(pasta,aplicar,resumo):
        """Simula por padrão; --aplicar preenche apenas campos vazios no banco configurado."""
        try:
            if not Path(resumo).parent.is_dir():raise ValueError('Pasta do resumo não existe')
            r=CruzarCatalogoBuildcoresService().executar(pasta,simular=not aplicar)
            Path(resumo).write_text(json.dumps(r,ensure_ascii=False,indent=2))
            click.echo(json.dumps({k:v for k,v in r.items() if k!='detalhes'},ensure_ascii=False))
            if r['interrompido']:raise click.ClickException('Cruzamento interrompido; consulte o resumo. Lotes anteriores já foram confirmados')
        except (OSError,ValueError,SQLAlchemyError) as erro:raise click.ClickException(str(erro) if isinstance(erro,ValueError) else 'Falha de leitura ou persistência') from None
