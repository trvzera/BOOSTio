import json
from pathlib import Path
import click
from sqlalchemy.exc import SQLAlchemyError
from services.catalogo_service.reavaliar_montagem_service import ReavaliarMontagemService


def registrar_comandos_requisitos_montagem(app):
    @app.cli.command('catalogo-montagem-reavaliar')
    @click.option('--aplicar',is_flag=True)
    @click.option('--resumo',type=click.Path(dir_okay=False))
    def reavaliar(aplicar,resumo):
        """Simula a reavaliação dos mínimos técnicos, sem aprovar identidades."""
        try:
            if resumo and not Path(resumo).parent.is_dir():raise ValueError('Pasta do resumo não existe')
            r=ReavaliarMontagemService().executar(simular=not aplicar)
            texto=json.dumps(r,ensure_ascii=False,indent=2)
            if resumo:Path(resumo).write_text(texto)
            click.echo(texto)
        except (ValueError,OSError,SQLAlchemyError) as erro:raise click.ClickException(str(erro) if isinstance(erro,ValueError) else 'Falha na reavaliação; lotes anteriores confirmados podem ser retomados') from None
