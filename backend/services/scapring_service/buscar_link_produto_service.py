import json
import re
import time
import unicodedata
from urllib.parse import quote

import requests


class BuscarLinkProdutoService:
  """Procura um produto na Kabum e devolve o link da página dele."""

  URL_BUSCA = "https://www.kabum.com.br/busca/{termo}"
  URL_PRODUTO = "https://www.kabum.com.br/produto/{codigo}/{slug}"
  HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  }
  #Resultados que nao sao a peca sozinha (kits, pcs montados...)
  PRIMEIRAS_PALAVRAS_IGNORADAS = {"kit", "pc", "computador", "notebook", "combo", "desktop"}
  #Se vier logo depois do modelo, e outra versao da peca (ex: RTX 4060 -> RTX 4060 Ti)
  SUFIXOS_OUTRA_VERSAO = {"ti", "super", "xt", "xtx", "gre", "x3d", "kf", "ks", "pro", "max", "plus", "x", "f", "k", "g", "gt"}
  #A kabum escreve "650W" onde o modelo tem so "650"
  UNIDADES = ("w", "gb", "tb", "mm", "hz")
  TENTATIVAS = 3

  def executar(self, fabricante: str, modelo: str, categoria: str = "", exigir_fabricante: bool = True) -> str | None:
    """Devolve o link da página do produto ou None se não achar (ou se a Kabum não responder)."""
    try:
      produtos = self._buscar_produtos(f"{categoria} {fabricante} {modelo}".strip())
    except (requests.RequestException, ValueError):
      return None

    produto = self._escolher_produto(produtos, fabricante if exigir_fabricante else "", modelo, categoria)

    if produto is None:
      return None

    return self.URL_PRODUTO.format(codigo=produto["code"], slug=produto["friendlyName"])

  def _buscar_produtos(self, termo: str) -> list[dict]:
    for tentativa in range(self.TENTATIVAS):
      try:
        return self._requisitar_produtos(termo)
      except (requests.RequestException, ValueError):
        #A kabum recusa parte das requisicoes quando vem muitas seguidas: espera um pouco e tenta de novo
        if tentativa == self.TENTATIVAS - 1:
          raise

        time.sleep(1.5 * (tentativa + 1))

  def _requisitar_produtos(self, termo: str) -> list[dict]:
    response = requests.get(self.URL_BUSCA.format(termo=quote(termo)), headers=self.HEADERS, timeout=20)
    response.raise_for_status()

    #A kabum devolve os resultados da busca dentro do json do next.js
    achou = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', response.text, re.S)

    if not achou:
      raise ValueError("Resposta da Kabum sem dados de busca")

    dados = json.loads(achou.group(1))
    #Busca sem nenhum resultado vem sem catalogServer: e uma resposta valida ("nao achei"), nao um erro
    catalogo = dados.get("props", {}).get("pageProps", {}).get("data", {}).get("catalogServer") or {}
    return catalogo.get("data") or []

  def _escolher_produto(self, produtos: list[dict], fabricante: str, modelo: str, categoria: str) -> dict | None:
    #O que vem entre parenteses (ex: "(2x8GB)") e detalhe do kit, nao entra na comparacao do modelo
    palavras_modelo = self._palavras(re.sub(r"\(.*?\)", " ", modelo))
    palavras_exigidas = set(self._palavras(f"{categoria} {fabricante}"))
    candidatos = []

    for produto in produtos:
      if not produto.get("code") or not produto.get("friendlyName"):
        continue

      palavras = self._palavras(produto["name"])

      if palavras[0] in self.PRIMEIRAS_PALAVRAS_IGNORADAS or not palavras_exigidas <= set(palavras):
        continue

      posicoes = [self._posicao(palavra, palavras) for palavra in palavras_modelo]

      if None in posicoes or self._e_outra_versao(palavras, max(posicoes)):
        continue

      em_sequencia = posicoes == list(range(posicoes[0], posicoes[0] + len(posicoes)))
      candidatos.append((not em_sequencia, not produto.get("available"), produto))

    if not candidatos:
      return None

    #Prefere quem tem o modelo em sequencia e esta disponivel. O sort e estavel: o resto segue a relevancia da kabum
    candidatos.sort(key=lambda candidato: candidato[:2])
    return candidatos[0][2]

  def _posicao(self, palavra: str, palavras: list[str]) -> int | None:
    aceitas = {palavra}

    if palavra.isdigit():
      aceitas |= {palavra + unidade for unidade in self.UNIDADES}

    for indice, atual in enumerate(palavras):
      if atual in aceitas:
        return indice

    return None

  def _e_outra_versao(self, palavras: list[str], ultima_posicao: int) -> bool:
    if ultima_posicao + 1 >= len(palavras):
      return False

    proxima = palavras[ultima_posicao + 1]
    #Numero solto depois do modelo tambem e outra geracao (ex: Cloud Stinger -> Cloud Stinger 2)
    return proxima in self.SUFIXOS_OUTRA_VERSAO or proxima.isdigit()

  @staticmethod
  def _palavras(texto: str) -> list[str]:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    palavras = []

    for palavra in re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", texto):
      #"RTX4060" e "RTX 4060" precisam ser a mesma coisa
      letras_numeros = re.fullmatch(r"([a-z]+)(\d+)", palavra)
      palavras.extend(letras_numeros.groups() if letras_numeros else [palavra])

    return palavras
