from models import db, ControleColeta
from models.modelos_pecas import MODELOS_PECAS
from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
from services.catalogo_service.normalizar_produto import codigo
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.marketplace_service.gravar_ofertas_service import aplicar_ofertas_loja
from services.marketplace_service.controle_requisicoes_service import agora_utc
from utils.identidade_peca import assinatura_peca

LOTE = 50


class AssociarFeedGigantecService:
    """Liga itens do feed a peças que já existem no catálogo, pelo código do fabricante (MPN) e pela marca.
    Não cadastra peça nova. Item sem correspondência exata, ambíguo ou em conflito fica de fora."""

    def executar(self, itens, *, simular=True, limite=None):
        resumo = {'simulacao': simular, 'itens': len(itens), 'sem_mpn': 0, 'sem_correspondencia': 0, 'revisao': 0,
                  'indisponiveis': 0, 'ligadas': 0, 'criadas': 0, 'atualizadas': 0, 'inalteradas': 0, 'conflitos': 0, 'detalhes': []}
        escolhidas = self._escolher(itens, resumo)
        if limite:
            escolhidas = dict(list(escolhidas.items())[:limite])
        resumo['ligadas'] = len(escolhidas)
        if not simular and not ControleColeta.bloquear():
            raise ValueError('Prepare o controle de coleta com mercadolivre-ofertas-preparar')
        modelos = {m.__tablename__: m for m in MODELOS_PECAS}
        for posicao, ((tabela, peca_id), (item, assinatura)) in enumerate(escolhidas.items(), 1):
            self._gravar(modelos[tabela], peca_id, item, assinatura, simular, resumo)
            if not simular and posicao % LOTE == 0:
                db.session.commit()
        if not simular:
            db.session.commit()
        return resumo

    def _escolher(self, itens, resumo):
        indices = {m.__tablename__: IndiceCandidatosService.carregar(m) for m in MODELOS_PECAS}
        por_peca = {}
        for item in sorted(itens.values(), key=lambda i: (i['preco'], i['id'])):
            if not item['mpn']:
                resumo['sem_mpn'] += 1
                continue
            chave = codigo(item['mpn'])
            achadas = [(tabela, indice) for tabela, indice in indices.items() if indice.por_mpn.get(chave)]
            if not achadas:
                resumo['sem_correspondencia'] += 1
                continue
            if not item['disponivel']:
                resumo['indisponiveis'] += 1
                continue
            confirmadas = []
            for tabela, indice in achadas:
                produto = ProdutoNormalizado(loja='gigantec', id_externo=item['id'], categoria=tabela, titulo=item['titulo'],
                    marca=item['marca'], identificadores={'mpn': item['mpn']}, ativo=True, categoria_confirmada=True, fonte=item['url'])
                decisao = indice.avaliar(produto)
                if decisao['classificacao'] == 'confirmada':
                    confirmadas.append((tabela, decisao['peca'], indice))
            if len(confirmadas) != 1:
                resumo['revisao'] += 1
                continue
            tabela, identificador, indice = confirmadas[0]
            peca_id = int(identificador.rsplit(':', 1)[1])
            peca = next(p for p in indice.pecas if p.id == peca_id)
            por_peca.setdefault((tabela, peca_id), (item, assinatura_peca(peca)))
        return por_peca

    def _gravar(self, modelo, peca_id, item, assinatura, simular, resumo):
        try:
            db.session.rollback()
            peca = modelo.buscar_por_id(peca_id)
            if peca is None or assinatura_peca(peca) != assinatura:
                raise ValueError('Peça mudou durante a leitura do feed')
            if not peca.publicavel:
                raise ValueError('Peça ainda não aprovada para publicação')
            oferta = dict(produto_id_loja=item['id'], vendedor_id='', url=item['url'], url_afiliado=item['url_afiliado'],
                          preco=item['preco'], esgotado=False)
            propostas = aplicar_ofertas_loja(peca, 'gigantec', [oferta], agora_utc())
            if simular:
                db.session.rollback()
        except ValueError as erro:
            db.session.rollback()
            resumo['conflitos'] += 1
            resumo['detalhes'].append({'anuncio': item['id'], 'peca': f'{modelo.__tablename__}:{peca_id}', 'erro': str(erro)})
            return
        resumo[{'criada': 'criadas', 'atualizada': 'atualizadas'}.get(propostas[0]['acao'], 'inalteradas')] += 1
        resumo['detalhes'].append({'anuncio': item['id'], 'peca': f'{modelo.__tablename__}:{peca_id}',
                                   'preco': str(item['preco']), 'acao': propostas[0]['acao']})
