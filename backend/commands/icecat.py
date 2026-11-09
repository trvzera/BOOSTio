"""Preparação e diagnóstico da fonte técnica, sem criar peças diretamente."""
import json
import os
import click
from defusedxml.common import DefusedXmlException
from xml.etree.ElementTree import ParseError
from services.icecat_service.indice_icecat_service import IndiceIcecatService
from services.icecat_service.completar_ficha_icecat_service import CompletarFichaIcecatService
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.peca_service.modelos_pecas import MODELOS_PECAS


def registrar_comandos_icecat(app):
    @app.cli.command('icecat-indice-preparar')
    @click.option('--arquivo', required=True, type=click.Path(exists=True, dir_okay=False))
    @click.option('--destino', envvar='ICECAT_INDICE', required=True, type=click.Path(dir_okay=False))
    def preparar(arquivo, destino):
        """Constrói cache de busca local a partir do índice completo baixado."""
        try:
            click.echo(json.dumps(IndiceIcecatService(destino).preparar(arquivo), ensure_ascii=False))
        except (ValueError, OSError, ParseError, DefusedXmlException):
            raise click.ClickException('Índice não preparado; confira formato, espaço e permissões. O índice anterior foi preservado') from None

    @app.cli.command('icecat-consultar')
    @click.option('--categoria', required=True, type=click.Choice([m.__tablename__ for m in MODELOS_PECAS]))
    @click.option('--marca', required=True)
    @click.option('--modelo', required=True)
    @click.option('--titulo')
    @click.option('--mpn')
    @click.option('--gtin')
    @click.option('--anuncio-ativo', is_flag=True, help='Simula um anúncio ativo somente neste diagnóstico.')
    def consultar(categoria, marca, modelo, titulo, mpn, gtin, anuncio_ativo):
        """Consulta uma ficha para diagnóstico, sem gravar no banco de peças."""
        service = CompletarFichaIcecatService.configurado()
        if service is None:
            raise click.ClickException('Configure ICECAT_INDICE')
        produto = ProdutoNormalizado(loja='diagnostico', id_externo='diagnostico', categoria=categoria,
            categoria_confirmada=True, ativo=True if anuncio_ativo else None, titulo=titulo or f'{marca} {modelo}', marca=marca, modelo=modelo,
            identificadores={k:v for k,v in {'mpn':mpn, 'gtin':gtin}.items() if v})
        ficha = dict(dados={}, fontes={}, identidade={}, conflitos=[], pronto=False)
        try:
            _, resultado = service.executar(produto, ficha)
            click.echo(json.dumps(resultado, ensure_ascii=False, default=str))
        except (ValueError, OSError, ParseError, DefusedXmlException):
            raise click.ClickException('Consulta não concluída; confira acesso Icecat, índice e ficha') from None
