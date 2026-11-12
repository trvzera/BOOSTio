from datetime import timedelta
import hashlib
import json
import logging
from threading import Event
from contextlib import contextmanager
from repositories.fila_marketplace_repository import RepositorioFilaMarketplace
from repositories.controle_catalogo_repository import RepositorioControleCatalogo
from .controle_requisicoes_service import ControleRequisicoesMarketplaceService, controle_em_execucao, agora_utc
from .erros import FalhaMarketplace, FilaAguardando

logger = logging.getLogger(__name__)
LOJAS = ('mercado_livre', 'shopee')


class ProcessarFilaMarketplaceService:
    def __init__(self, executores, repositorio=None, *, relogio=agora_utc, trava=None, controle=None):
        self.executores = executores
        self.repositorio = repositorio or RepositorioFilaMarketplace()
        self.relogio = relogio
        self.trava = trava or self._bloquear
        self.verificar = lambda: None
        self.controle = controle

    @contextmanager
    def _bloquear(self, loja):
        repositorio = RepositorioControleCatalogo(escopo='fila_'+loja)
        with repositorio.bloquear() as adquirido:
            if adquirido:
                self.verificar = repositorio.verificar
            yield adquirido

    def enfileirar(self, loja, tipo, dados, *, execucao):
        if loja not in LOJAS or (loja, tipo) not in self.executores:
            raise ValueError('Marketplace ou tarefa não suportados')
        if not isinstance(dados, dict) or any(c in json.dumps(dados).lower() for c in ('secret', 'access_token', 'refresh_token', 'password', 'authorization')):
            raise ValueError('Dados da tarefa inválidos ou sensíveis')
        if not isinstance(execucao, str) or not 1 <= len(execucao) <= 100:
            raise ValueError('Informe uma identificação da execução')
        documento = json.dumps([execucao, tipo, dados], sort_keys=True, ensure_ascii=False, allow_nan=False)
        chave = hashlib.sha256(documento.encode()).hexdigest()
        return self.repositorio.enfileirar(loja, chave, tipo, dados)

    def executar(self, loja):
        if loja not in LOJAS:
            raise ValueError('Marketplace inválido')
        with self.trava(loja) as adquirido:
            if not adquirido:
                return {'loja': loja, 'status': 'ocupado'}
            tarefa = self.repositorio.reservar(loja, self.relogio())
            if tarefa is None:
                return {'loja': loja, 'status': 'aguardando'}
            controle = self.controle or ControleRequisicoesMarketplaceService(loja, self.repositorio)
            controle.verificar = self.verificar
            contexto = controle_em_execucao.set(controle)
            try:
                executor = self.executores.get((loja, tarefa['tipo']))
                if executor is None:
                    raise ValueError('Tipo de tarefa não disponível')
                resultado = executor(tarefa['dados'])
                if controle.erro is not None:
                    raise controle.erro
                self.verificar()
                self.repositorio.finalizar(tarefa, 'concluida', resultado=resultado)
                self.repositorio.normalizar_limitacoes(loja)
                status = 'concluida'
            except FilaAguardando:
                self.repositorio.finalizar(tarefa, 'pendente', disponivel_em=self.relogio()+timedelta(seconds=1))
                status = 'aguardando'
            except FalhaMarketplace as erro:
                if erro.autenticacao:
                    self.repositorio.suspender(loja, self.relogio(), bloquear=True)
                    status = 'bloqueada'
                elif erro.status == 429 or erro.temporaria:
                    status = 'pendente'
                else:
                    status = 'falhou'
                minimo = 60 if erro.status == 429 else 5
                espera = max(erro.espera, min(3600, minimo * 2 ** min(tarefa['tentativas']-1, 10)))
                if erro.status == 429:
                    self.repositorio.suspender(loja, self.relogio(), espera=espera)
                self.repositorio.finalizar(tarefa, status, erro=f'HTTP {erro.status or "rede"}',
                    disponivel_em=self.relogio()+timedelta(seconds=espera))
                logger.warning('Fila loja=%s tarefa=%s status=%s espera_s=%s', loja, tarefa['id'], status, espera)
            except (ValueError, TypeError, KeyError):
                status = 'falhou'
                self.repositorio.finalizar(tarefa, status, erro='Dados ou resposta incompatíveis; revisar')
            finally:
                controle_em_execucao.reset(contexto)
            logger.info('Fila loja=%s tarefa=%s status=%s', loja, tarefa['id'], status)
            return {'loja': loja, 'tarefa': tarefa['id'], 'status': status}

    def acompanhar(self, *, parada=None, sondagem=1):
        parada = parada or Event()
        while not parada.is_set():
            for loja in LOJAS:
                if not parada.is_set():
                    self.executar(loja)
            parada.wait(max(1, sondagem))
