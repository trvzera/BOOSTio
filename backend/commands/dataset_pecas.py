"""Administração do snapshot técnico, sem endpoints públicos."""
import json
from pathlib import Path
import click
from sqlalchemy.exc import SQLAlchemyError
from migrations.catalogo_parcial import preparar_catalogo_parcial
from services.dataset_pecas_service.importar_dataset_service import ImportarDatasetService


def registrar_comandos_dataset_pecas(app):
    @app.cli.command('dataset-pecas-baixar')
    @click.option('--destino',required=True,type=click.Path(file_okay=False))
    @click.option('--commit',default=None)
    def baixar(destino,commit):
        from services.dataset_pecas_service.baixar_dataset_service import BaixarDatasetService
        try:click.echo(json.dumps(BaixarDatasetService().executar(destino,commit=commit),ensure_ascii=False))
        except (OSError,ValueError,KeyError):raise click.ClickException('Não foi possível baixar um snapshot válido') from None

    @app.cli.command('dataset-pecas-preparar')
    @click.option('--aplicar',is_flag=True)
    def preparar(aplicar):
        try:click.echo(json.dumps(preparar_catalogo_parcial(simular=not aplicar),ensure_ascii=False))
        except (ValueError,SQLAlchemyError) as erro:raise click.ClickException(str(erro) if isinstance(erro,ValueError) else 'Falha na migração; consulte o banco') from None

    @app.cli.command('dataset-pecas-importar')
    @click.option('--pasta',required=True,type=click.Path(exists=True,file_okay=False))
    @click.option('--aplicar',is_flag=True)
    @click.option('--lote',default=250,type=click.IntRange(1,1000))
    @click.option('--resumo',type=click.Path(dir_okay=False))
    def importar(pasta,aplicar,lote,resumo):
        """Simula por padrão. --aplicar grava somente peças e evidências técnicas."""
        try:
            if resumo and not Path(resumo).parent.is_dir():raise ValueError('A pasta do resumo não existe')
            resultado=ImportarDatasetService().executar(pasta,simular=not aplicar,tamanho_lote=lote)
            texto=json.dumps(resultado,ensure_ascii=False,indent=2)
            if resumo:Path(resumo).write_text(texto,encoding='utf-8')
            click.echo(texto)
            if resultado['interrompido']:raise click.ClickException('Importação interrompida; lotes anteriores confirmados. Consulte o resumo')
        except (OSError,ValueError,SQLAlchemyError) as erro:raise click.ClickException(str(erro) if isinstance(erro,ValueError) else 'Falha ao ler ou importar dataset') from None
