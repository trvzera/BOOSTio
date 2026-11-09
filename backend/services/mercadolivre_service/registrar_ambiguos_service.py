"""Catálogos do Mercado Livre em dúvida viram pendência para revisão, como as ambíguas da Shopee."""
import json
from datetime import datetime, timezone
from decimal import Decimal

from models import ProdutoPendente
from services.marketplace_service.erros import FalhaMarketplace
from utils.identidade_peca import assinatura_documento
from .controle_requisicoes_service import ErroMercadoLivre, OrcamentoRequisicoesEsgotado

MAX_CATALOGOS = 3


def _json_exato(valor):
    if isinstance(valor, Decimal):
        return str(valor)
    raise ValueError('JSON inválido')


class RegistrarAmbiguosMercadoLivreService:
    def executar(self, categoria, ambiguos, cliente, token):
        """Cada catálogo ambíguo entra pela sua oferta nova mais barata (o anúncio que o administrador verá)."""
        registradas = 0
        for item in ambiguos[:MAX_CATALOGOS]:
            produto, normal, decisao = item['produto'], item['normal'], item['decisao']
            try:
                resultado = cliente.executar(produto['id'], access_token=token, produto=produto)
            except (FalhaMarketplace, ErroMercadoLivre, OrcamentoRequisicoesEsgotado):
                raise  # limite ou autorização: a fila decide a espera
            except ValueError:
                continue  # catálogo inativo ou formato inesperado: não vira pendência
            novas = sorted((o for o in resultado['ofertas'] if o['condicao'] == 'new'),
                           key=lambda o: (o['preco'], o['vendedor_id'], o['produto_id_loja']))
            if not novas:
                continue
            oferta = novas[0]
            linha_ml = {'item_id': oferta['produto_id_loja'], 'seller_id': int(oferta['vendedor_id']),
                        'price': oferta['preco'], 'currency_id': 'BRL', 'site_id': 'MLB',
                        'condition': 'new', 'available_quantity': oferta['quantidade_disponivel']}
            bruto = json.loads(json.dumps({'origem': 'catalogo', 'catalogo': produto, 'anuncio': linha_ml},
                                          default=_json_exato, allow_nan=False))
            titulo = (normal.titulo or produto.get('name') or '').strip()[:255]
            if not titulo:
                continue
            linha = dict(loja='mercado_livre', produto_id_loja=oferta['produto_id_loja'], vendedor_id=oferta['vendedor_id'],
                         titulo=titulo, url=oferta['url'], categoria_sugerida=categoria, dados_originais=bruto,
                         coletado_em=datetime.now(timezone.utc).replace(tzinfo=None))
            ProdutoPendente.registrar_descobertos([linha], simular=False)
            pendente = ProdutoPendente.buscar_por_anuncio('mercado_livre', oferta['produto_id_loja'])
            if pendente is None:
                continue  # o anúncio já é uma oferta (registrar_descobertos o contou como associado)
            try:
                ProdutoPendente.registrar_matching(pendente.id, decisao, assinatura_documento(pendente.dados_originais), simular=False)
                registradas += 1
            except ValueError:
                continue  # já importada ou rejeitada: a decisão anterior vale
        return registradas
