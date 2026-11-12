import os
from dataclasses import replace

from models import db
from services.catalogo_service.enriquecer_peca_existente_service import EnriquecerPecaExistenteService
from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from models.modelos_pecas import MODELOS_PECAS
from .completar_ficha_icecat_service import CompletarFichaIcecatService
from .indice_icecat_service import IndiceIcecatService
from .obter_ficha_icecat_service import ErroConsultaIcecat, ObterFichaIcecatService

FICHA_VAZIA = dict(dados={}, fontes={}, identidade={}, conflitos=[], pronto=False)

NOME_NA_VALIDACAO = {('fone', 'tipo'): 'tipo_fone', ('memoria_ram', 'formato'): 'formato_ram',
                     ('cabo_rede', 'categoria'): 'categoria_cabo'}


class CompletarPecasIcecatService:
    def __init__(self, icecat=None, preenchedor=None):
        self.icecat = icecat or self._icecat_configurado()
        self.preenchedor = preenchedor or EnriquecerPecaExistenteService()

    @staticmethod
    def _icecat_configurado(max_fichas=200):
        indice = os.getenv('ICECAT_INDICE')
        if not indice:
            raise ValueError('Configure ICECAT_INDICE')
        fichas = ObterFichaIcecatService(os.getenv('ICECAT_PASTA_FICHAS', '/tmp/boostio-icecat-fichas'),
                                         usuario=os.getenv('ICECAT_USUARIO'), senha=os.getenv('ICECAT_SENHA'),
                                         max_requisicoes=max_fichas)
        return CompletarFichaIcecatService(IndiceIcecatService(indice), fichas)

    def executar(self, *, categoria, limite=100, depois_id=0, simular=True, incluir_publicadas=False):
        modelo = next((m for m in MODELOS_PECAS if m.__tablename__ == categoria), None)
        if modelo is None:
            raise ValueError('Categoria inválida')
        if type(limite) is not int or not 1 <= limite <= 500:
            raise ValueError('Limite entre 1 e 500 peças')
        resumo = dict(simulacao=simular, categoria=categoria, analisadas=0, ignoradas=0, sem_part_number=0,
                      proposta=0, atualizada=0, inalterada=0, ficha_liberada=0, revisao=0, sem_correspondencia=0,
                      nao_encontrada=0, ambigua=0, interrompido=False, ultima_peca_id=depois_id, detalhes=[])
        for peca in modelo.lote_para_identificadores(depois_id, limite):
            resumo['ultima_peca_id'] = peca.id
            if peca.status_validacao != 'em_revisao' and not (incluir_publicadas and peca.publicavel):
                resumo['ignoradas'] += 1
                continue
            from services.catalogo_service.conferir_especificacoes_service import OPCIONAIS
            opcionais_ausentes = any(EnriquecerPecaExistenteService.ausente(getattr(peca, campo, None))
                                     for campo in OPCIONAIS.get(categoria, ()))
            if not pendencias_para_montagem(peca) and not opcionais_ausentes:
                resumo['ficha_liberada' if self._reavaliar_ficha(peca, simular) else 'ignoradas'] += 1
                continue
            if not peca.part_number:
                resumo['sem_part_number'] += 1
                continue
            resumo['analisadas'] += 1
            try:
                resultado = self._completar(peca, simular)
            except ErroConsultaIcecat as erro:
                resumo['interrompido'] = True
                resumo['motivo_interrupcao'] = str(erro)
                break
            resumo[resultado['status']] = resumo.get(resultado['status'], 0) + 1
            if resultado['status'] in ('atualizada', 'inalterada') and self._reavaliar_ficha(peca, simular):
                resumo['ficha_liberada'] += 1
            resumo['detalhes'].append(dict(peca_id=peca.id, **{k: v for k, v in resultado.items() if k != 'fontes'}))
        return resumo

    @staticmethod
    def _reavaliar_ficha(peca, simular):
        if pendencias_para_montagem(peca) or peca.ficha_montagem_validada is True:
            return False
        if not simular:
            peca.ficha_montagem_validada = True
            db.session.commit()
        return True

    def _completar(self, peca, simular):
        base = ProdutoNormalizado(loja='icecat', id_externo=f'{peca.__tablename__}:{peca.id}',
                                  categoria=peca.__tablename__, categoria_confirmada=True,
                                  ativo=True,
                                  titulo=f'{peca.fabricante} {peca.modelo}', marca=peca.fabricante,
                                  modelo=peca.modelo, identificadores={'mpn': peca.part_number})
        _, ficha = self.icecat.executar(base, FICHA_VAZIA)
        situacao = ficha['icecat']['status']
        if situacao != 'encontrada':
            return dict(status=situacao, icecat=ficha['icecat'])
        return self.preenchedor.executar(peca, self._produto_da_ficha(base, ficha), simular=simular)

    @staticmethod
    def _produto_da_ficha(base, ficha):
        dados = ficha['dados']
        especificacoes = {NOME_NA_VALIDACAO.get((base.categoria, campo), campo): valor
                          for campo, valor in dados.items() if campo not in ('fabricante', 'modelo')}
        return replace(base, titulo=f"{dados['fabricante']} {dados['modelo']}", marca=dados['fabricante'],
                       modelo=dados['modelo'], especificacoes=especificacoes,
                       fonte=ficha['fonte_identidade'], contexto={'mpn_confirmado_na_fonte': True}, identificadores={**base.identificadores, **{
                           k: v for k, v in ficha['identidade'].items() if v}})
