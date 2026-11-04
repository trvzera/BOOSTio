"""Descobre anúncios oficiais e os envia à fila, sem matching ou publicação."""
import json
from copy import deepcopy
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
from .normalizar_produto_service import DOMINIOS
from services.catalogo_service.normalizar_produto import atributos
from services.catalogo_service.comparar_nomes_service import marca as normalizar_marca

log = logging.getLogger(__name__)


class LimitePaginas(ValueError):
    pass


class DescobrirProdutosService:
    def __init__(self, cliente=None, controle=None, tokens=None):
        self.controle = controle
        self.cliente = cliente
        self.tokens = tokens

    def executar(self, *, categoria, consulta, origem='catalogo', categoria_ml=None, dominio=None,
                 max_paginas=5, max_anuncios=100, max_requisicoes=30, intervalo=1.0, simular=True, cursor=None,
                 max_produtos=None, max_ofertas_por_produto=None, marca=None):
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
        for campo, valor in (('max_produtos', max_produtos), ('max_ofertas_por_produto', max_ofertas_por_produto)):
            if valor is not None and (origem != 'catalogo' or type(valor) is not int or not 1 <= valor <= 1000):
                raise ValueError(campo + ' exige origem catalogo e valor entre 1 e 1000')
        if origem == 'catalogo' and max_produtos is not None and dominio is None:
            dominio = DOMINIOS.get(categoria)
        if marca is not None and (origem != 'catalogo' or not isinstance(marca, str)
                or not 1 <= len(marca.strip()) <= 80 or any(ord(c) < 32 for c in marca)):
            raise ValueError('Marca de pesquisa inválida')
        if type(simular) is not bool:
            raise ValueError('Simulação inválida')
        if cursor is not None:
            if not isinstance(cursor,dict) or cursor.get('origem')!=origem or type(cursor.get('offset')) is not int or not 0<=cursor['offset']<=1000:
                raise ValueError('Cursor de descoberta inválido')
            if origem=='catalogo':
                if not isinstance(cursor.get('produtos'),list) or len(cursor['produtos'])>20 or any(not isinstance(p,dict) or not isinstance(p.get('id'),str) or not re.fullmatch(r'MLB[0-9]+',p['id']) or not isinstance(p.get('name'),str) for p in cursor['produtos']):
                    raise ValueError('Produtos no cursor inválidos')
                if any(type(cursor.get(k)) is not int or cursor[k]<0 for k in ('indice','ofertas_offset','total_busca')) or cursor['indice']>len(cursor['produtos']) or cursor['ofertas_offset']>1000:
                    raise ValueError('Paginação do cursor inválida')
        controle = self.controle or ControleRequisicoesService(max_requisicoes, intervalo)
        cliente = self.cliente or BuscarOfertasMercadoLivreService(controle)
        parametros = dict(categoria=categoria, consulta=consulta.strip(), origem=origem,
                          categoria_ml=categoria_ml, dominio=dominio, max_paginas=max_paginas,
                          max_anuncios=max_anuncios, max_requisicoes=max_requisicoes, intervalo=intervalo,
                          max_produtos=max_produtos, max_ofertas_por_produto=max_ofertas_por_produto, marca=marca)
        resumo = dict(simulacao=simular, execucao_id=None, paginas=0, encontrados=0,
                      novos=0, ja_coletados=0, ja_associados=0, invalidos=0, repetidos=0,
                      catalogos_indisponiveis=0, catalogos_incompletos=0, leituras_pendentes=[],
                      fora_da_marca=0, marca_nao_confirmada=0, fora_do_dominio=0,
                      requisicoes=0, interrompido=False, limitado=False, falhas=[],
                      janela_limitada=False, cursor=deepcopy(cursor) if cursor else dict(origem=origem,offset=0,produtos=[],indice=0,ofertas_offset=0,total_busca=0), concluido=False)
        vistos = set()
        try:
            if not simular:
                resumo['execucao_id'] = ExecucaoDescoberta.iniciar(parametros)
            for linhas in self._paginas(cliente, parametros, resumo, max_paginas):
                lote = []
                consumidas = 0
                for linha, produto in linhas:
                    if resumo['encontrados'] >= max_anuncios:
                        resumo['limitado'] = True
                        break
                    resumo['encontrados'] += 1
                    consumidas += 1
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
                self._avancar_cursor(resumo,consumidas,len(linhas))
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
                resumo['http_status'] = erro.status
                resumo['aguardar_segundos'] = erro.espera
            elif isinstance(erro, OrcamentoRequisicoesEsgotado):
                motivo = 'Limite de requisições atingido'
            elif isinstance(erro, SQLAlchemyError):
                motivo = 'Falha de persistência; a página atual não foi confirmada'
            else:
                motivo = 'Falha de leitura, autorização ou formato; consulta interrompida'
            resumo['falhas'].append(motivo)
        estado = resumo['cursor']
        resumo['produtos_percorridos'] = estado['offset'] + estado['indice'] if origem == 'catalogo' else 0
        resumo['requisicoes'] = controle.total
        if resumo['execucao_id'] is not None:
            try:
                ExecucaoDescoberta.finalizar(resumo['execucao_id'], resumo)
            except SQLAlchemyError:
                db.session.rollback()
                resumo['interrompido'] = True
                resumo['falhas'].append('Não foi possível finalizar o registro da execução; revise a execução em aberto')
        resumo.pop('_pagina',None)
        log.info('Descoberta Mercado Livre: %s', json.dumps({k:v for k,v in resumo.items() if k!='cursor'}, ensure_ascii=False))
        return resumo

    def _paginas(self, cliente, parametros, resumo, max_paginas):
        def consultar(caminho, params, offset, tamanho):
            if resumo['paginas']>=max_paginas or offset>=1000:
                raise LimitePaginas()
            token=(self.tokens or TokenMercadoLivreService()).executar()
            dados=cliente._consultar(caminho,token,params={**params,'offset':offset,'limit':tamanho})
            linhas,total=self._validar_pagina(dados,offset,tamanho)
            resumo['paginas']+=1
            return linhas,total
        while not resumo['concluido']:
            estado=resumo['cursor']
            if parametros['origem'] == 'catalogo' and parametros['max_produtos'] is not None:
                if estado['offset'] + estado['indice'] >= parametros['max_produtos']:
                    resumo['concluido'] = True
                    resumo['limitado'] = True
                    return
            if parametros['origem']=='anuncios':
                params={'q':parametros['consulta']}
                if parametros['categoria_ml']:params['category']=parametros['categoria_ml']
                linhas,total=consultar('/sites/MLB/search',params,estado['offset'],50)
                resumo['_pagina']={'total':total}
                yield [(linha,None) for linha in linhas]
            else:
                if not estado['produtos']:
                    params={'site_id':'MLB','status':'active','q':parametros['consulta']}
                    if parametros['dominio']:params['domain_id']=parametros['dominio']
                    produtos,total=consultar('/products/search',params,estado['offset'],20)
                    for p in produtos:
                        if not isinstance(p,dict):raise ValueError('Produto inválido')
                        cliente._validar_id(p.get('id'),'catálogo')
                        if not isinstance(p.get('name'),str) or not p['name'].strip():raise ValueError('Nome ausente')
                    # Checkpoint pequeno: fichas completas serão consultadas novamente no enriquecimento.
                    estado['produtos']=json.loads(json.dumps([{k:p[k] for k in ('id','name','status','domain_id','attributes') if k in p} for p in produtos],default=str))
                    estado['total_busca']=total;estado['indice']=0;estado['ofertas_offset']=0
                    if not produtos:
                        resumo['concluido']=True;return
                if estado['indice']>=len(estado['produtos']):raise ValueError('Cursor inconsistente')
                produto=estado['produtos'][estado['indice']]
                motivo = self._fora_do_grupo(produto, parametros)
                if motivo:
                    resumo[motivo] += 1
                    resumo['_pagina'] = {'total': 0}
                    yield []
                    continue
                try:
                    linhas,total=consultar('/products/'+produto['id']+'/items',{},estado['ofertas_offset'],100)
                except ErroMercadoLivre as erro:
                    if erro.status not in (404, 206):
                        raise
                    # Catálogos removidos ou respostas parciais não fornecem ofertas
                    # confiáveis. Registrar a lacuna sem aceitar o conteúdo parcial.
                    # 401/403/429 continuam interrompendo, sem contornar restrições.
                    if erro.status == 206:
                        resumo['catalogos_incompletos'] += 1
                        resumo['leituras_pendentes'].append({'catalogo_id':produto['id'], 'http':206,
                            'offset':estado['ofertas_offset']})
                    else:
                        resumo['catalogos_indisponiveis'] += 1
                    resumo['paginas'] += 1
                    linhas, total = [], 0
                teto = parametros['max_ofertas_por_produto']
                if teto is not None:
                    total = min(total, teto)
                    linhas = linhas[:max(0, total - estado['ofertas_offset'])]
                resumo['_pagina']={'total':total}
                yield [(linha,produto) for linha in linhas]

    @staticmethod
    def _fora_do_grupo(produto, parametros):
        """A pesquisa textual não comprova marca nem categoria dos resultados."""
        if parametros['max_produtos'] is not None:
            categorias = {categoria for categoria, dominio in DOMINIOS.items() if dominio == produto.get('domain_id')}
            if categorias and parametros['categoria'] not in categorias:
                return 'fora_do_dominio'
            tipos = atributos(produto).get('DRIVE_STORAGE_TYPE', set())
            if (parametros['categoria'] == 'ssd' and 'hdd' in tipos
                    or parametros['categoria'] == 'hd' and 'ssd' in tipos):
                return 'fora_do_dominio'
        if parametros['dominio'] and produto.get('domain_id') and produto['domain_id'] != parametros['dominio']:
            return 'fora_do_dominio'
        if parametros['marca'] is None:
            return None
        esperada = normalizar_marca(parametros['marca'])
        marcas = {normalizar_marca(v) for v in atributos(produto).get('BRAND', set())}
        if marcas:
            return None if marcas == {esperada} else 'fora_da_marca'
        titulo = normalizar_marca(produto.get('name', ''))
        if not re.search(r'(?<!\w)' + re.escape(esperada) + r'(?!\w)', titulo):
            return 'marca_nao_confirmada'
        return None

    @staticmethod
    def _avancar_cursor(resumo, consumidas, tamanho):
        estado=resumo['cursor'];total=resumo['_pagina']['total']
        if estado['origem']=='anuncios':
            estado['offset']+=consumidas
            resumo['concluido']=estado['offset']>=total or estado['offset']>=1000
            if estado['offset']>=1000 and estado['offset']<total:
                resumo['janela_limitada']=True;resumo['limitado']=True
        else:
            estado['ofertas_offset']+=consumidas
            if estado['ofertas_offset']>=total or estado['ofertas_offset']>=1000:
                if estado['ofertas_offset']<total:
                    resumo['janela_limitada']=True;resumo['limitado']=True
                estado['indice']+=1;estado['ofertas_offset']=0
                if estado['indice']>=len(estado['produtos']):
                    estado['offset']+=len(estado['produtos']);estado['produtos']=[];estado['indice']=0
                    resumo['concluido']=estado['offset']>=estado['total_busca']

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
