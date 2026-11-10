import json
import re
from .token_mercado_livre_service import TokenMercadoLivreService
from .controle_requisicoes_service import ErroMercadoLivre
from .normalizar_produto_service import DOMINIOS
from services.catalogo_service.normalizar_produto import atributos
from services.catalogo_service.comparar_nomes_service import marca as normalizar_marca


class LimitePaginas(ValueError):
    pass


def iterar_paginas(cliente, parametros, resumo, max_paginas, tokens=None):
    def _consultar(caminho, params, offset, tamanho):
        if resumo['paginas']>=max_paginas or offset>=1000:
            raise LimitePaginas()
        token=(tokens or TokenMercadoLivreService()).executar()
        dados=cliente._consultar(caminho,token,params={**params,'offset':offset,'limit':tamanho})
        linhas,total=_validar_pagina(dados,offset,tamanho)
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
            linhas,total=_consultar('/sites/MLB/search',params,estado['offset'],50)
            resumo['_pagina']={'total':total}
            yield [(linha,None) for linha in linhas]
        else:
            if not estado['produtos']:
                params={'site_id':'MLB','status':'active','q':parametros['consulta']}
                if parametros['dominio']:params['domain_id']=parametros['dominio']
                produtos,total=_consultar('/products/search',params,estado['offset'],20)
                for p in produtos:
                    if not isinstance(p,dict):raise ValueError('Produto inválido')
                    cliente._validar_id(p.get('id'),'catálogo')
                    if not isinstance(p.get('name'),str) or not p['name'].strip():raise ValueError('Nome ausente')
                estado['produtos']=json.loads(json.dumps([{k:p[k] for k in ('id','name','status','domain_id','attributes') if k in p} for p in produtos],default=str))
                estado['total_busca']=total;estado['indice']=0;estado['ofertas_offset']=0
                if not produtos:
                    resumo['concluido']=True;return
            if estado['indice']>=len(estado['produtos']):raise ValueError('Cursor inconsistente')
            produto=estado['produtos'][estado['indice']]
            motivo = _fora_do_grupo(produto, parametros)
            if motivo:
                resumo[motivo] += 1
                resumo['_pagina'] = {'total': 0}
                yield []
                continue
            try:
                linhas,total=_consultar('/products/'+produto['id']+'/items',{},estado['ofertas_offset'],100)
            except ErroMercadoLivre as erro:
                if erro.status not in (404, 206):
                    raise
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


def _fora_do_grupo(produto, parametros):
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


def avancar_cursor(resumo, consumidas, tamanho):
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
