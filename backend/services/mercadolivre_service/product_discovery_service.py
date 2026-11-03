"""Descobre anúncios oficiais e os envia à fila, sem matching ou publicação."""
import json
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from models import db, ProdutoPendente, ExecucaoDescoberta
from services.peca_service.modelos_pecas import MODELOS_PECAS
from .buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from .controle_requisicoes_service import ControleRequisicoesService, OrcamentoRequisicoesEsgotado, ErroMercadoLivre
from .token_mercado_livre_service import TokenMercadoLivreService

log = logging.getLogger(__name__)


class LimitePaginas(ValueError):
    pass


class ProductDiscoveryService:
    def __init__(self, cliente=None, controle=None, tokens=None):
        self.controle = controle
        self.cliente = cliente
        self.tokens = tokens

    def executar(self, *, categoria, consulta, origem='catalogo', categoria_ml=None, dominio=None,
                 max_paginas=5, max_anuncios=100, max_requisicoes=30, intervalo=1.0, simular=True):
        categorias = {c.__tablename__ for c in MODELOS_PECAS}
        if not isinstance(categoria, str) or categoria not in categorias or origem not in ('catalogo', 'anuncios'):
            raise ValueError('Categoria ou origem de descoberta inválida')
        if not isinstance(consulta, str) or not 2 <= len(consulta.strip()) <= 150 or any(ord(c) < 32 for c in consulta):
            raise ValueError('Informe palavras-chave entre 2 e 150 caracteres')
        if categoria_ml is not None and (not isinstance(categoria_ml, str) or origem != 'anuncios' or not re.fullmatch(r'MLB[0-9]+', categoria_ml)):
            raise ValueError('Categoria MLB só é aceita na busca de anúncios')
        if dominio is not None and (not isinstance(dominio, str) or origem != 'catalogo' or not re.fullmatch(r'MLB-[A-Z0-9_]+', dominio)):
            raise ValueError('Domínio MLB só é aceito na busca de catálogo')
        if type(max_paginas) is not int or not 1 <= max_paginas <= 100 or type(max_anuncios) is not int or not 1 <= max_anuncios <= 5000:
            raise ValueError('Limites: 1–100 páginas e 1–5000 anúncios')
        if type(simular) is not bool:
            raise ValueError('Simulação inválida')
        controle = self.controle or ControleRequisicoesService(max_requisicoes, intervalo)
        cliente = self.cliente or BuscarOfertasMercadoLivreService(controle)
        parametros = dict(categoria=categoria, consulta=consulta.strip(), origem=origem,
                          categoria_ml=categoria_ml, dominio=dominio, max_paginas=max_paginas,
                          max_anuncios=max_anuncios, max_requisicoes=max_requisicoes, intervalo=intervalo)
        resumo = dict(simulacao=simular, execucao_id=None, paginas=0, encontrados=0,
                      novos=0, ja_coletados=0, ja_associados=0, invalidos=0, repetidos=0,
                      requisicoes=0, interrompido=False, limitado=False, falhas=[])
        vistos = set()
        try:
            if not simular:
                resumo['execucao_id'] = ExecucaoDescoberta.iniciar(parametros)
            for linhas in self._paginas(cliente, parametros, resumo, max_paginas):
                lote = []
                for linha, produto in linhas:
                    if resumo['encontrados'] >= max_anuncios:
                        resumo['limitado'] = True
                        break
                    resumo['encontrados'] += 1
                    try:
                        dados = self._normalizar(cliente, linha, produto, categoria, origem)
                    except ValueError:
                        resumo['invalidos'] += 1
                        continue
                    chave = dados['produto_id_loja']
                    if chave in vistos:
                        resumo['repetidos'] += 1
                        continue
                    vistos.add(chave)
                    lote.append(dados)
                contagens = ProdutoPendente.registrar_descobertos(lote, simular=simular)
                for chave, valor in contagens.items():
                    resumo[chave] += valor
                if resumo['encontrados'] >= max_anuncios:
                    resumo['limitado'] = True
                if resumo['limitado']:
                    break
        except LimitePaginas:
            resumo['limitado'] = True
        except (ValueError, SQLAlchemyError) as erro:
            db.session.rollback()
            resumo['interrompido'] = True
            # Não incluir corpo de resposta, URL OAuth nem detalhes de SQL nos logs.
            if isinstance(erro, ErroMercadoLivre):
                motivo = f'Mercado Livre HTTP {erro.status}; verifique acesso ou limite antes de repetir'
            elif isinstance(erro, OrcamentoRequisicoesEsgotado):
                motivo = 'Limite de requisições atingido'
            elif isinstance(erro, SQLAlchemyError):
                motivo = 'Falha de persistência; a página atual não foi confirmada'
            else:
                motivo = 'Falha de leitura, autorização ou formato; consulta interrompida'
            resumo['falhas'].append(motivo)
        resumo['requisicoes'] = controle.total
        if resumo['execucao_id'] is not None:
            try:
                ExecucaoDescoberta.finalizar(resumo['execucao_id'], resumo)
            except SQLAlchemyError:
                db.session.rollback()
                resumo['interrompido'] = True
                resumo['falhas'].append('Não foi possível finalizar o registro da execução; revise a execução em aberto')
        log.info('Descoberta Mercado Livre: %s', json.dumps(resumo, ensure_ascii=False))
        return resumo

    def _paginas(self, cliente, parametros, resumo, max_paginas):
        def consultar(caminho, params, tamanho):
            offset = 0
            while True:
                if resumo['paginas'] >= max_paginas or offset >= 1000:
                    raise LimitePaginas()
                # Reutiliza a renovação existente entre páginas, sem manter token por horas.
                token = (self.tokens or TokenMercadoLivreService()).executar()
                dados = cliente._consultar(caminho, token, params={**params, 'offset': offset, 'limit': tamanho})
                linhas, total = self._validar_pagina(dados, offset, tamanho)
                resumo['paginas'] += 1
                yield linhas
                offset += len(linhas)
                if offset >= total:
                    break
        if parametros['origem'] == 'anuncios':
            params = {'q': parametros['consulta']}
            if parametros['categoria_ml']:
                params['category'] = parametros['categoria_ml']
            for linhas in consultar('/sites/MLB/search', params, 50):
                yield [(linha, None) for linha in linhas]
        else:
            params = {'site_id': 'MLB', 'status': 'active', 'q': parametros['consulta']}
            if parametros['dominio']:
                params['domain_id'] = parametros['dominio']
            for produtos in consultar('/products/search', params, 20):
                for produto in produtos:
                    if not isinstance(produto, dict):
                        raise ValueError('Produto inválido')
                    cliente._validar_id(produto.get('id'), 'catálogo')
                    if not isinstance(produto.get('name'), str) or not produto['name'].strip():
                        raise ValueError('Nome de catálogo ausente')
                    for linhas in consultar(f"/products/{produto['id']}/items", {}, 100):
                        yield [(linha, produto) for linha in linhas]

    @staticmethod
    def _validar_pagina(dados, offset, tamanho):
        paging, linhas = dados.get('paging'), dados.get('results')
        if not isinstance(paging, dict) or not isinstance(linhas, list):
            raise ValueError('Página inválida')
        total = paging.get('total')
        if type(total) is not int or total < 0 or type(paging.get('offset')) is not int or paging['offset'] != offset:
            raise ValueError('Paginação inválida')
        if len(linhas) > tamanho or offset + len(linhas) > total or (not linhas and offset < total):
            raise ValueError('Página incompleta')
        return linhas, total

    @staticmethod
    def _normalizar(cliente, linha, produto, categoria, origem):
        if not isinstance(linha, dict):
            raise ValueError('Anúncio inválido')
        if origem == 'catalogo':
            normal = cliente._normalizar(linha, produto['id'])
            titulo = produto['name']  # Nome do catálogo, não título individual do vendedor.
        else:
            seller = linha.get('seller')
            normal = cliente._normalizar({**linha, 'item_id': linha.get('id'),
                'seller_id': seller.get('id') if isinstance(seller, dict) else None}, linha.get('catalog_product_id'))
            titulo = linha.get('title')
        if not isinstance(titulo, str) or not 1 <= len(titulo.strip()) <= 255:
            raise ValueError('Título inválido')
        # JSON monetário permanece decimal exato em texto, sem conversão para float.
        def decimal_json(valor):
            if isinstance(valor, Decimal):
                return str(valor)
            raise ValueError('JSON inválido')
        bruto = json.loads(json.dumps({'origem': origem, 'catalogo': produto, 'anuncio': linha},
                                    default=decimal_json, allow_nan=False))
        return dict(loja='mercado_livre', produto_id_loja=normal['produto_id_loja'],
                    vendedor_id=normal['vendedor_id'], titulo=titulo.strip(), url=normal['url'],
                    categoria_sugerida=categoria, dados_originais=bruto,
                    coletado_em=datetime.now(timezone.utc).replace(tzinfo=None))
