from contextvars import ContextVar
from datetime import datetime, timezone
import math
import os
import time
import requests
from .erros import FalhaMarketplace, FilaAguardando

controle_em_execucao = ContextVar('controle_marketplace', default=None)


def verificar_execucao():
    controle = controle_em_execucao.get()
    if controle is not None:
        controle.verificar()


def agora_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def executar_requisicao(chamada, *, loja='mercado_livre'):
    controle = controle_em_execucao.get()
    if controle is not None:
        if controle.loja != loja:
            raise ValueError('Contexto de requisição pertence a outro marketplace')
        return controle.executar(chamada)
    from flask import has_app_context
    from sqlalchemy import inspect
    from models import db
    from repositories.fila_marketplace_repository import RepositorioFilaMarketplace
    if not has_app_context() or not inspect(db.engine).has_table('limite_marketplace'):
        return chamada()
    repo = RepositorioFilaMarketplace()
    if not repo.preparado():
        return chamada()
    tentativas = 0
    while True:
        controle = ControleRequisicoesMarketplaceService(loja, repo, liberar_espera=False)
        try:
            return controle.executar(chamada)
        except FalhaMarketplace as erro:
            if not erro.temporaria:
                raise
            tentativas += 1
            time.sleep(max(erro.espera, min(3600, 5 * 2 ** min(tentativas-1, 10))))


class ControleRequisicoesMarketplaceService:
    def __init__(self, loja, repositorio, *, intervalo=None, relogio=agora_utc, dormir=time.sleep, liberar_espera=True):
        valor = intervalo if intervalo is not None else os.getenv(f'{loja.upper()}_INTERVALO_REQUISICOES', '1')
        self.intervalo = float(valor)
        if not math.isfinite(self.intervalo) or self.intervalo < 1:
            raise ValueError('Intervalo entre requisições deve ser de pelo menos 1 segundo')
        self.loja, self.repositorio = loja, repositorio
        self.relogio, self.dormir = relogio, dormir
        self.erro = None
        self.verificar = lambda: None
        self.liberar_espera = liberar_espera

    def executar(self, chamada):
        self.verificar()
        if self.erro is not None:
            raise self.erro
        while True:
            espera = self.repositorio.intervalo(self.loja, self.relogio(), self.intervalo)
            if espera is None:
                self.erro = FalhaMarketplace(403)
                raise self.erro
            if espera <= 0:
                break
            if espera > self.intervalo and self.liberar_espera:
                self.erro = FilaAguardando('Marketplace aguardando retomada')
                raise self.erro
            self.dormir(min(espera, 1))
        try:
            self.verificar()
            return chamada()
        except (ValueError, requests.RequestException) as erro:
            if isinstance(erro, requests.RequestException):
                falha = FalhaMarketplace(temporaria=True)
            elif isinstance(erro, FalhaMarketplace):
                falha = erro
            elif hasattr(erro, 'status'):
                falha = FalhaMarketplace(erro.status, getattr(erro, 'espera', 0))
            else:
                raise
            if falha.status not in (404, 206):
                self.erro = falha
            if falha.status == 429:
                repeticoes = self.repositorio.limitacoes(self.loja)
                espera = max(falha.espera, min(3600, 60 * 2 ** min(repeticoes, 6)))
                self.repositorio.suspender(self.loja, self.relogio(), espera=espera, rate_limit=True)
                falha.espera = espera
            elif falha.autenticacao:
                self.repositorio.suspender(self.loja, self.relogio(), bloquear=True)
            raise falha from None
