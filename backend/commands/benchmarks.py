import json
import click
from sqlalchemy.exc import SQLAlchemyError
from services.benchmark_service.importar_benchmarks_service import ImportarBenchmarksService


def registrar_comandos_benchmarks(app):
    @app.cli.command("benchmarks-importar")
    @click.option("--cpu", type=click.Path(exists=True, dir_okay=False), help="Snapshot local cpus.csv (ehan03/passmark).")
    @click.option("--gpu", type=click.Path(exists=True, dir_okay=False), help="Snapshot local gpus.csv (ehan03/passmark).")
    @click.option("--simular", is_flag=True, help="Mostra propostas sem gravar.")
    @click.option("--lote", default=100, type=click.IntRange(min=1), show_default=True)
    def importar(cpu, gpu, simular, lote):
        """Preenche benchmarks somente em peças já cadastradas, sem rede."""
        try:
            resumo = ImportarBenchmarksService().executar(cpu, gpu, simular, lote)
        except (ValueError, OSError, RuntimeError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro)) from erro
        click.echo(json.dumps(resumo, ensure_ascii=False))
