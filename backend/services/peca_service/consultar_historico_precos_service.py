from datetime import datetime, time, timedelta, timezone

from models import HistoricoOferta, Oferta, VinculoMercadoLivre
from repositories.ofertas_kabum_repository import buscar_ativa
from utils.identidade_peca import assinatura_peca
from models.modelos_pecas import MODELOS_PECAS


LOJAS = ('kabum', 'mercado_livre', 'shopee')
LIMITE_LINHAS = 3000


class ConsultarHistoricoPrecosService:
    def executar(self, categoria, peca_id, oferta_id=None, loja=None):
        classe = next((c for c in MODELOS_PECAS if c.__tablename__ == categoria), None)
        if classe is None or type(peca_id) is not int or peca_id <= 0:
            raise ValueError('Identificação da peça inválida')
        peca = classe.buscar_publicada_por_id(peca_id)
        if peca is None:
            raise LookupError('Peça não encontrada')
        if oferta_id is not None:
            return self._historico_oferta(peca, oferta_id)
        if loja is not None:
            return self._historico_por_loja(peca, loja)
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


    @staticmethod
    def _exibivel(oferta, peca):
        if oferta.para_exibicao() is None:
            return False
        if oferta.loja == 'mercado_livre':
            vinculo = VinculoMercadoLivre.buscar(peca.__tablename__, peca.id)
            return vinculo is not None and vinculo.assinatura_peca == assinatura_peca(peca) and vinculo.especificacoes_compativeis(peca)
        return oferta.loja == 'kabum' or oferta.shopee_validada(peca)

    def _historico_por_loja(self, peca, loja):
        if loja != 'todas' and loja not in LOJAS:
            raise ValueError('Loja inválida')
        ofertas = [o for nome in LOJAS for o in Oferta.listar_da_peca(peca, nome, apenas_ativas=True) if self._exibivel(o, peca)]
        escolhidas = {o.id: o for o in ofertas if loja in ('todas', o.loja)}
        linhas = HistoricoOferta.listar_das_ofertas(list(escolhidas), LIMITE_LINHAS)
        tem_mais = len(linhas) > LIMITE_LINHAS
        linhas = sorted(linhas[:LIMITE_LINHAS], key=lambda l: (l.coletado_em, l.id))
        por_oferta = {}
        for linha in linhas:
            por_oferta.setdefault(linha.oferta_id, []).append(linha)
        pontos = []
        for dia in sorted({l.coletado_em.date() for l in linhas}):
            fim = datetime.combine(dia + timedelta(days=1), time.min)
            vigentes = [[l for l in lista if l.coletado_em < fim][-1] for lista in por_oferta.values() if lista[0].coletado_em < fim]
            melhor = min(vigentes, key=lambda l: (l.esgotado is True, l.preco, l.id))
            origem = escolhidas[melhor.oferta_id]
            pontos.append({'data': datetime.combine(dia, time.min).replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds'),
                           'preco': float(melhor.preco), 'esgotado': melhor.esgotado,
                           'loja': origem.loja, 'produto_id_loja': origem.produto_id_loja})
        return {'peca_id': f'{peca.__tablename__}:{peca.id}', 'loja': loja,
                'lojas': [nome for nome in LOJAS if any(o.loja == nome for o in ofertas)],
                'limite': LIMITE_LINHAS, 'tem_mais': tem_mais, 'historico_precos': pontos}
