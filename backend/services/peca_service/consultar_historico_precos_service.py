from datetime import timezone

from models import HistoricoOferta, Oferta, VinculoMercadoLivre
from repositories.ofertas_kabum_repository import buscar_ativa
from utils.identidade_peca import assinatura_peca
from models.modelos_pecas import MODELOS_PECAS


class ConsultarHistoricoPrecosService:
    def executar(self, categoria, peca_id, oferta_id=None):
        classe = next((c for c in MODELOS_PECAS if c.__tablename__ == categoria), None)
        if classe is None or type(peca_id) is not int or peca_id <= 0:
            raise ValueError('Identificação da peça inválida')
        peca = classe.buscar_publicada_por_id(peca_id)
        if peca is None:
            raise LookupError('Peça não encontrada')
        if oferta_id is not None:
            return self._historico_oferta(peca, oferta_id)
        resultado = {'peca_id': f'{categoria}:{peca_id}', 'loja': 'kabum',
                     'historico_precos': [], 'limite': 1000, 'tem_mais': False}
        oferta = buscar_ativa(peca)
        if oferta is None:
            return resultado
        linhas = HistoricoOferta.listar(oferta.id, limite=resultado['limite'])
        resultado['tem_mais'] = len(linhas) > resultado['limite']
        resultado['produto_id_loja'] = oferta.produto_id_loja
        resultado['historico_precos'] = [
            {'data': linha.coletado_em.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds'),
             'preco': float(linha.preco), 'esgotado': linha.esgotado, 'loja': 'kabum',
             'produto_id_loja': oferta.produto_id_loja}
            for linha in reversed(linhas[:resultado['limite']])]
        return resultado


    @staticmethod
    def _historico_oferta(peca, oferta_id):
        categoria, peca_id = peca.__tablename__, peca.id
        if type(oferta_id) is not int or oferta_id <= 0:
            raise ValueError('Oferta inválida')
        oferta = Oferta.buscar_para_peca(oferta_id, categoria, peca_id)
        if oferta is None or oferta.para_exibicao() is None:
            raise LookupError('Oferta não encontrada')
        if oferta.loja == 'mercado_livre':
            vinculo = VinculoMercadoLivre.buscar(categoria, peca_id)
            valido = vinculo is not None and vinculo.assinatura_peca == assinatura_peca(peca) and vinculo.especificacoes_compativeis(peca)
        else:
            valido = oferta.shopee_validada(peca)
        if not valido:
            raise LookupError('Identificação da peça precisa de revisão')
        linhas = HistoricoOferta.listar(oferta.id)
        return {'peca_id': f'{categoria}:{peca_id}', 'oferta_id': oferta.id, 'loja': oferta.loja,
                'produto_id_loja': oferta.produto_id_loja, 'limite': 1000, 'tem_mais': len(linhas) > 1000,
                'historico_precos': [
                    {'data': linha.coletado_em.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds'),
                     'preco': float(linha.preco), 'esgotado': linha.esgotado,
                     'loja': oferta.loja, 'produto_id_loja': oferta.produto_id_loja}
                    for linha in reversed(linhas[:1000])]}
