"""Enriquece anúncios desconhecidos com ficha comprovada, sem gravar componentes."""
from dataclasses import replace, asdict
from decimal import Decimal, InvalidOperation
import os
from types import SimpleNamespace
from services.catalogo_service.associacao_inteligente_service import AssociacaoInteligenteService
from services.catalogo_service.conferir_especificacoes_service import converter
from services.catalogo_service.normalizar_produto import codigo, gtin
from services.catalogo_service.conferir_especificacoes_service import valores
from services.catalogo_service.validar_ficha_tecnica_service import ValidarFichaTecnicaService
from .indice_icecat_service import IndiceIcecatService
from .normalizar_ficha_icecat_service import NormalizarFichaIcecatService
from .obter_ficha_icecat_service import ObterFichaIcecatService


class CompletarFichaIcecatService:
    def __init__(self, indice, fichas):
        self.indice = indice
        self.fichas = fichas

    @classmethod
    def configurado(cls):
        caminho = os.getenv('ICECAT_INDICE')
        if not caminho:
            return None
        return cls(IndiceIcecatService(caminho), ObterFichaIcecatService(
            os.getenv('ICECAT_PASTA_FICHAS', '/tmp/boostio-icecat-fichas'),
            usuario=os.getenv('ICECAT_USUARIO'), senha=os.getenv('ICECAT_SENHA')))

    def executar(self, produto, ficha):
        referencias = self.indice.buscar(produto)
        if not referencias:
            return produto, {**ficha, 'icecat': {'status':'nao_encontrada'}}
        if len(referencias) > 3:
            return produto, {**ficha, 'icecat': {'status':'ambigua', 'candidatos':len(referencias)}}
        candidatos = []
        diagnosticos = []
        for referencia in referencias:
            corpo = self.fichas.executar(referencia)
            tecnica = NormalizarFichaIcecatService().executar(corpo, referencia, produto.categoria)
            if codigo(tecnica['identidade']['mpn']) != referencia['mpn']:
                raise ValueError('MPN da ficha Icecat diverge do índice')
            procurados = {gtin(v) for v in valores(produto.identificadores.get('gtin')) if gtin(v)}
            if procurados:
                if not procurados <= set(tecnica['gtins']):
                    raise ValueError('GTIN da ficha Icecat diverge do anúncio')
                if len(procurados)==1:
                    tecnica['identidade']['gtin'] = next(iter(procurados))
            local = SimpleNamespace(__tablename__=produto.categoria, id=0,
                                    part_number=tecnica['identidade']['mpn'], **tecnica['dados'])
            decisao = AssociacaoInteligenteService().avaliar(local, produto, identidade=tecnica['identidade'])
            diagnosticos.append(dict(id=referencia['id'], classificacao=decisao['classificacao'],
                                     conflitos=decisao['conflitos'], pendencias=decisao['pendencias']))
            if decisao['classificacao'] == 'confirmada' and not tecnica['conflitos']:
                candidatos.append(tecnica)
        # Mesmo um candidato não confirmado pode ser uma variante concorrente.
        if len(candidatos) != 1 or any(d['classificacao']=='ambigua' for d in diagnosticos):
            return produto, {**ficha, 'icecat': {'status':'revisao', 'candidatos':diagnosticos}}
        tecnica = candidatos[0]
        dados = dict(ficha['dados'])
        fontes = dict(ficha.get('fontes', {}))
        conflitos = list(ficha.get('conflitos', []))
        for campo, valor in tecnica['dados'].items():
            if campo in dados and dados[campo] is not None:
                if not self._equivalentes(produto.categoria, campo, dados[campo], valor):
                    conflitos.append('icecat_divergente:' + campo)
            else:
                dados[campo] = valor
                fontes[campo] = tecnica['fontes'][campo]
        fontes['mpn'] = tecnica['fontes']['mpn']
        # Mantém as especificações do anúncio para a última verificação de duplicatas.
        # Os dados da fonte permanecem em ficha['dados'], com origem individual.
        identidade = tecnica['identidade']
        identificadores = dict(produto.identificadores)
        for campo, valor in identidade.items():
            if valor and not identificadores.get(campo):
                identificadores[campo] = valor
        produto = replace(produto, identificadores=identificadores)
        validacao = ValidarFichaTecnicaService().executar(produto.categoria, dados, produto,
            identidade, fontes=fontes, finalidade='catalogo')
        conflitos.extend(validacao['conflitos'])
        nova = {**ficha, **{k:tecnica[k] for k in ('fonte_identidade', 'referencia_icecat')},
                'dados':dados, 'fontes':fontes, 'identidade':identidade,
                'campos_pendentes':validacao['campos_pendentes'], 'conflitos':sorted(set(conflitos)),
                'pronto':validacao['pronto'] and not conflitos,
                'finalidade_validacao':'catalogo', 'normalizado':asdict(produto),
                'icecat':{'status':'encontrada', 'id':tecnica['referencia_icecat'], 'candidatos':diagnosticos}}
        return produto, nova

    @staticmethod
    def _equivalentes(categoria, campo, a, b):
        if campo in ('fabricante', 'modelo'):
            # Nome de catálogo e nome comercial podem diferir com MPN comprovado.
            # Marca continua exigindo equivalência explícita.
            if campo == 'modelo':
                return True
            from services.catalogo_service.comparar_nomes_service import marca
            return marca(a) == marca(b)
        chave = 'formato_ram' if categoria == 'memoria_ram' and campo == 'formato' else campo
        if campo in ('consumo_energia', 'clockbase', 'clockmax'):
            try:
                return Decimal(str(a)) == Decimal(str(b))
            except InvalidOperation:
                return False
        x, y = converter(chave, a), converter(chave, b)
        return x is not None and y is not None and x == y
