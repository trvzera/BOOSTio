import os
from types import SimpleNamespace
from services.catalogo_service.associacao_inteligente_service import AssociacaoInteligenteService

from services.catalogo_service.normalizar_produto import codigo, gtin
from services.catalogo_service.conferir_especificacoes_service import valores

from .indice_icecat_service import IndiceIcecatService
from .normalizar_ficha_icecat_service import NormalizarFichaIcecatService, CategoriaIcecatIncompativel
from .obter_ficha_icecat_service import ObterFichaIcecatService, ErroConsultaIcecat


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
            diagnostico = self.indice.diagnosticar_ausencia(produto)
            avaliacoes = []
            for referencia in diagnostico['candidatos_para_revisao'][:3]:
                tecnica, erro = self._ler_candidato(referencia, produto.categoria)
                if erro:
                    avaliacoes.append(erro)
                    continue
                local = SimpleNamespace(__tablename__=produto.categoria, id=0,
                    part_number=tecnica['identidade']['mpn'], **tecnica['dados'])
                comparacao = AssociacaoInteligenteService().avaliar(
                    local, produto, identidade=tecnica['identidade'])
                avaliacoes.append(dict(id=referencia['id'], fabricante=tecnica['dados']['fabricante'],
                    mpn=tecnica['identidade']['mpn'], classificacao=comparacao['classificacao'],
                    conflitos=sorted(set(comparacao['conflitos'] + tecnica['conflitos']))))
            diagnostico['avaliacoes_alternativas'] = avaliacoes
            return produto, {**ficha, 'icecat': {'status':'nao_encontrada', **diagnostico}}
        if len(referencias) > 3:
            return produto, {**ficha, 'icecat': {'status':'ambigua', 'candidatos':len(referencias)}}
        candidatos = []
        diagnosticos = []
        for referencia in referencias:
            tecnica, erro = self._ler_candidato(referencia, produto.categoria)
            if erro:
                diagnosticos.append(erro)
                continue
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
            if 'icecat_embalagem_com_varias_unidades' in tecnica['conflitos']:
                decisao = {**decisao, 'classificacao':'rejeitada',
                           'conflitos':sorted(set(decisao['conflitos'] + tecnica['conflitos']))}
            diagnosticos.append(dict(id=referencia['id'], classificacao=decisao['classificacao'],
                                     conflitos=decisao['conflitos'], pendencias=decisao['pendencias']))
            if decisao['classificacao'] == 'confirmada' and not tecnica['conflitos']:
                candidatos.append(tecnica)
        if len(candidatos) != 1 or any(d['classificacao']=='ambigua' for d in diagnosticos):
            return produto, {**ficha, 'icecat': {'status':'revisao', 'candidatos':diagnosticos}}
        from services.catalogo_service.mesclar_ficha_tecnica_service import MesclarFichaTecnicaService
        tecnica = candidatos[0]
        produto, nova = MesclarFichaTecnicaService().executar(produto, ficha, tecnica)
        nova.update(referencia_icecat=tecnica['referencia_icecat'],
                    icecat={'status':'encontrada', 'id':tecnica['referencia_icecat'], 'candidatos':diagnosticos})
        return produto, nova

    def _ler_candidato(self, referencia, categoria):
        try:
            tecnica = NormalizarFichaIcecatService().executar(
                self.fichas.executar(referencia), referencia, categoria)
            return tecnica, None
        except CategoriaIcecatIncompativel:
            return None, dict(id=referencia['id'], classificacao='rejeitada',
                              conflitos=['categoria_icecat_incompativel'], pendencias=[])
        except ErroConsultaIcecat as erro:
            if erro.status != 404:
                raise
            return None, dict(id=referencia['id'], classificacao='ambigua',
                              conflitos=[], pendencias=['ficha_icecat_indisponivel'], http=404)
