"""Consulta de ofertas do catálogo oficial; não persiste nem associa peças por nome."""
import json
import re
from decimal import Decimal, InvalidOperation

import requests
from .token_mercado_livre_service import TokenMercadoLivreService


class BuscarOfertasMercadoLivreService:
    BASE_URL = "https://api.mercadolibre.com"
    TAMANHO_MAXIMO = 2 * 1024 * 1024
    TAMANHO_PAGINA = 100
    MAX_OFERTAS = 1000

    def executar(self, catalogo_id: str, *, access_token: str | None = None):
        self._validar_id(catalogo_id, "produto de catálogo")
        token = access_token if access_token is not None else TokenMercadoLivreService().executar()
        if not isinstance(token, str) or not token.strip() or any(c in token for c in "\r\n"):
            raise ValueError("Token OAuth fornecido está ausente ou inválido")
        token = token.strip()
        produto = self._consultar(f"/products/{catalogo_id}", token)
        if produto.get("id") != catalogo_id or not isinstance(produto.get("name"), str) or not produto["name"].strip():
            raise ValueError("Identificação do produto de catálogo inválida no Mercado Livre")
        if produto.get("status") != "active":
            raise ValueError("Produto de catálogo inativo no Mercado Livre")
        ofertas = {}
        offset = 0
        total_anterior = None
        while True:
            pagina = self._consultar(f"/products/{catalogo_id}/items", token,
                                    params={"offset": offset, "limit": self.TAMANHO_PAGINA})
            paging, linhas = pagina.get("paging"), pagina.get("results")
            if not isinstance(paging, dict) or not isinstance(linhas, list):
                raise ValueError("Formato de ofertas inválido no Mercado Livre")
            total = paging.get("total")
            if type(total) is not int or total < 0 or paging.get("offset") != offset:
                raise ValueError("Paginação inválida no Mercado Livre")
            if total > self.MAX_OFERTAS:
                raise ValueError("Catálogo excede o limite de ofertas por consulta")
            if total_anterior is not None and total != total_anterior:
                raise ValueError("Catálogo mudou durante a paginação; repita a consulta")
            total_anterior = total
            if len(linhas) > self.TAMANHO_PAGINA or offset + len(linhas) > total or (not linhas and offset < total):
                raise ValueError("Paginação incompleta no Mercado Livre")
            for linha in linhas:
                oferta = self._normalizar(linha, catalogo_id)
                identidade = oferta["produto_id_loja"]
                if identidade in ofertas:
                    raise ValueError("Anúncio duplicado durante a paginação do Mercado Livre")
                ofertas[identidade] = oferta
            offset += len(linhas)
            if offset == total:
                break
        return {"catalogo_id": catalogo_id, "nome": produto["name"].strip(),
                "ofertas": list(ofertas.values())}

    def _consultar(self, caminho, token, params=None):
        try:
            resposta = requests.get(
                self.BASE_URL + caminho, params=params,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=(10, 30), stream=True, allow_redirects=False,
            )
            try:
                if resposta.status_code != 200:
                    raise ValueError(f"Mercado Livre HTTP {resposta.status_code}; consulta não concluída")
                if resposta.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                    raise ValueError("Mercado Livre não retornou JSON")
                partes, tamanho = [], 0
                for bloco in resposta.iter_content(64 * 1024):
                    tamanho += len(bloco)
                    if tamanho > self.TAMANHO_MAXIMO:
                        raise ValueError("Resposta do Mercado Livre maior que 2 MB")
                    partes.append(bloco)
                try:
                    dados = json.loads(b"".join(partes), parse_float=Decimal)
                except (ValueError, UnicodeDecodeError):
                    raise ValueError("JSON inválido no Mercado Livre") from None
                if not isinstance(dados, dict):
                    raise ValueError("Formato de resposta inválido no Mercado Livre")
                return dados
            finally:
                resposta.close()
        except requests.RequestException:
            # Não propagar objetos de request, cabeçalhos ou credenciais para logs.
            raise ValueError("Falha de rede na consulta ao Mercado Livre") from None

    @staticmethod
    def _validar_id(valor, tipo):
        if not isinstance(valor, str) or not re.fullmatch(r"MLB[0-9]+", valor):
            raise ValueError(f"Informe um ID MLB válido de {tipo}")

    def _normalizar(self, linha, catalogo_id):
        if not isinstance(linha, dict):
            raise ValueError("Oferta inválida no Mercado Livre")
        anuncio = linha.get("item_id")
        self._validar_id(anuncio, "anúncio")
        vendedor = linha.get("seller_id")
        if type(vendedor) is not int or vendedor <= 0:
            raise ValueError("Vendedor inválido no Mercado Livre")
        if linha.get("site_id") != "MLB" or linha.get("currency_id") != "BRL":
            raise ValueError("Oferta do Mercado Livre fora do Brasil ou sem preço em reais")
        preco = self._preco(linha.get("price"))
        original = linha.get("original_price")
        original = self._preco(original) if original is not None else None
        condicao = linha.get("condition")
        if condicao not in {"new", "used", "not_specified"}:
            raise ValueError("Condição da oferta desconhecida no Mercado Livre")
        return {"loja": "mercado_livre", "catalogo_id": catalogo_id,
                "produto_id_loja": anuncio, "vendedor_id": str(vendedor),
                "preco": preco, "preco_original": original, "moeda": "BRL",
                "condicao": condicao, "esgotado": None, "condicao_pagamento": None,
                "url": f"https://produto.mercadolivre.com.br/MLB-{anuncio[3:]}-_JM",
                "url_afiliado": None}

    @staticmethod
    def _preco(valor):
        if isinstance(valor, bool) or not isinstance(valor, (str, int, float, Decimal)):
            raise ValueError("Preço inválido no Mercado Livre")
        try:
            preco = Decimal(str(valor))
            if not preco.is_finite() or preco <= 0 or preco > Decimal("999999999999.99"):
                raise ValueError("Preço inválido no Mercado Livre")
            centavos = preco.quantize(Decimal("0.01"))
            if centavos != preco:
                raise ValueError("Preço do Mercado Livre com fração de centavo")
            return centavos
        except InvalidOperation:
            raise ValueError("Preço inválido no Mercado Livre") from None
