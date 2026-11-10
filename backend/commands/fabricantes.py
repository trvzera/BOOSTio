"""Diagnóstico administrativo da busca técnica nos fabricantes."""
import json
import os
import click
from services.fabricante_service.completar_ficha_service import CompletarFichaFabricanteService
from services.fabricante_service.consultar_paginas_service import ConsultarPaginasFabricanteService
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from models.modelos_pecas import MODELOS_PECAS


def registrar_comandos_fabricantes(app):
    @app.cli.command('fabricantes-consultar')
    @click.option('--categoria',required=True,type=click.Choice([m.__tablename__ for m in MODELOS_PECAS]))
    @click.option('--marca',required=True)
    @click.option('--modelo',required=True)
    @click.option('--titulo',required=True)
    @click.option('--mpn')
    def consultar(categoria,marca,modelo,titulo,mpn):
        """Consulta páginas oficiais e mostra evidências sem cadastrar peças."""
        produto=ProdutoNormalizado(loja='diagnostico',id_externo='diagnostico',categoria=categoria,
            marca=marca,modelo=modelo,titulo=titulo,categoria_confirmada=True,ativo=True,
            identificadores={'mpn':mpn} if mpn else {})
        service=CompletarFichaFabricanteService(ConsultarPaginasFabricanteService(
            os.getenv('FABRICANTES_CACHE','/tmp/boostio-fabricantes')))
        _,resultado=service.executar(produto,dict(dados={},fontes={},conflitos=[],pronto=False))
        click.echo(json.dumps(resultado,ensure_ascii=False,default=str))
