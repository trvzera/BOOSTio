from datetime import timezone

from models import HistoricoPreco, HistoricoOferta, Oferta, VinculoMercadoLivre
from utils.identidade_peca import assinatura_peca
from .modelos_pecas import MODELOS_PECAS
from services.preco_service.validar_link_service import ValidarLinkService


class ConsultarHistoricoPrecosService:
    def executar(self, categoria, peca_id, oferta_id=None):
        classe = next((c for c in MODELOS_PECAS if c.__tablename__ == categoria), None)
        if classe is None or type(peca_id) is not int or peca_id <= 0:
            raise ValueError('Identificação da peça inválida')
        peca = classe.buscar_por_id(peca_id)
        if peca is None:
            raise LookupError('Peça não encontrada')
        if oferta_id is not None:
            return self._historico_oferta(peca, oferta_id)
        resultado = {'peca_id': f'{categoria}:{peca_id}', 'loja': 'kabum',
                     'historico_precos': [], 'limite': 1000, 'tem_mais': False}
        try:
            anuncio = ValidarLinkService().codigo_produto(peca.kabum_external or '')
        except ValueError:
            return resultado
        linhas = HistoricoPreco.listar_por_peca_anuncio(categoria, peca_id, 'kabum', anuncio,
                                                       limite=resultado['limite'])
        resultado['tem_mais'] = len(linhas) > resultado['limite']
        resultado['produto_id_loja'] = anuncio
        resultado['historico_precos'] = [
            {'data': linha.coletado_em.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds'),
             'preco': float(linha.preco) if linha.preco is not None else None,
             'esgotado': linha.esgotado, 'loja': linha.loja,
             'produto_id_loja': linha.produto_id_loja}
            for linha in reversed(linhas[:resultado['limite']])]
        return resultado


    @staticmethod
    def _historico_oferta(peca, oferta_id):
        categoria, peca_id = peca.__tablename__, peca.id
        vinculo = VinculoMercadoLivre.buscar(categoria, peca_id)
        if vinculo is None or vinculo.assinatura_peca != assinatura_peca(peca):
            raise LookupError("Identificação da peça precisa de revisão")
        if type(oferta_id) is not int or oferta_id <= 0:
            raise ValueError('Oferta inválida')
        oferta = Oferta.buscar_para_peca(oferta_id, categoria, peca_id)
        if oferta is None or oferta.para_exibicao() is None:
            raise LookupError('Oferta não encontrada')
        linhas = HistoricoOferta.listar(oferta.id)
        return {'peca_id': f'{categoria}:{peca_id}', 'oferta_id': oferta.id, 'loja': 'mercado_livre',
                'produto_id_loja': oferta.produto_id_loja, 'limite': 1000, 'tem_mais': len(linhas) > 1000,
                'historico_precos': [
                    {'data': linha.coletado_em.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds'),
                     'preco': float(linha.preco), 'esgotado': linha.esgotado,
                     'loja': 'mercado_livre', 'produto_id_loja': oferta.produto_id_loja}
                    for linha in reversed(linhas[:1000])]}
