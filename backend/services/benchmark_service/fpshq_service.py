from collections import OrderedDict, deque
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from threading import RLock
import math
import time
import logging

import requests

logger = logging.getLogger(__name__)


class ErroBenchmark(Exception):
    def __init__(self, mensagem, codigo="provedor", status=502, espera=0, diagnostico=None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.status = status
        self.espera = espera
        self.diagnostico = {}
        if isinstance(diagnostico, dict):
            http = diagnostico.get("httpProvedor")
            if type(http) is int and 100 <= http <= 599:
                self.diagnostico["httpProvedor"] = http
            if diagnostico.get("tipoResposta") in ("json", "html", "outro"):
                self.diagnostico["tipoResposta"] = diagnostico["tipoResposta"]
            if type(diagnostico.get("redirecionamento")) is bool:
                self.diagnostico["redirecionamento"] = diagnostico["redirecionamento"]
            if diagnostico.get("pausa") is True:
                self.diagnostico["pausa"] = True


class FpshqService:
    BASE_URL = "https://fpshq.com/api/public/v1/"
    TTL = 3600
    TTL_RESERVA = 86400
    MAX_CACHE = 256
    LIMITE_MINUTO = 45
    LIMITE_DIA = 9000
    LIMITE_USUARIO = 10

    def __init__(self, buscar=None, relogio=None, data_atual=None):
        self.buscar = buscar or requests.get
        self.relogio = relogio or time.monotonic
        self.data_atual = data_atual or time.time
        self.cache = OrderedDict()
        self.minuto = deque()
        self.dia = deque()
        self.usuarios = OrderedDict()
        self.bloqueado_ate = 0
        self.falha_temporaria = None
        self.lock = RLock()
        self.chaves = [RLock() for _ in range(32)]

    def travar(self, caminho, dados):
        chave = (caminho, tuple(sorted((campo, str(valor)) for campo, valor in dados.items())))
        return self.chaves[hash(chave) % len(self.chaves)]

    def executar(self, caminho, parametros, usuario_id):
        if not isinstance(parametros, dict):
            raise ValueError("Informe parametros como um objeto válido")

        if caminho not in ("fps", "games"):
            raise ValueError("Consulta de benchmark inválida.")
        chave = (caminho, tuple(sorted(parametros.items())))
        with self.lock:
            agora = self.relogio()
            salvo = self.cache.get(chave)
            if salvo and agora - salvo[0] < self.TTL:
                self.cache.move_to_end(chave)
                return {**deepcopy(salvo[1]), "cache": True}
            if salvo and agora - salvo[0] >= self.TTL_RESERVA:
                self.cache.pop(chave, None)
                salvo = None
            if self.falha_temporaria:
                ate, mensagem, codigo, status, diagnostico = self.falha_temporaria
                if agora < ate:
                    if salvo:
                        return {**deepcopy(salvo[1]), "cache": True, "desatualizado": True}
                    raise ErroBenchmark(mensagem, codigo, status, math.ceil(ate - agora), {**diagnostico, "pausa": True})
                self.falha_temporaria = None
            self._validar_limites(agora, usuario_id)
        return self._consultar(caminho, parametros, salvo)

    def _consultar(self, caminho, parametros, salvo):
        try:
            resposta = self.buscar(
                self.BASE_URL + caminho, params={**parametros, "lang": "pt"},
                headers={"Accept": "application/json", "User-Agent": "BOOSTio/1.0 (benchmark)"}, timeout=(4, 10),
                allow_redirects=False,
            )
        except requests.Timeout as causa:
            erro = self._falhar("A FPSHQ não respondeu a tempo. Aguarde antes de tentar novamente.", "timeout", 504, 30, causa)
            if salvo:
                return {**deepcopy(salvo[1]), "cache": True, "desatualizado": True}
            raise erro from causa
        except requests.exceptions.SSLError as causa:
            erro = self._falhar("Não foi possível estabelecer uma conexão segura com o serviço de testes de jogos. Tente novamente mais tarde.", "tls", 503, 60, causa)
            if salvo:
                return {**deepcopy(salvo[1]), "cache": True, "desatualizado": True}
            raise erro from causa
        except requests.RequestException as causa:
            erro = self._falhar("A BOOSTio não conseguiu receber os dados do serviço de testes de jogos. Tente novamente em instantes.", "rede", 503, 30, causa)
            if salvo:
                return {**deepcopy(salvo[1]), "cache": True, "desatualizado": True}
            raise erro from causa
        if 300 <= resposta.status_code < 400:


            erro = self._falhar("O serviço de testes de jogos está indisponível agora. Tente novamente mais tarde. Não calculamos um resultado sem os dados.",
                                "redirecionamento", 503, 60, diagnostico=self._metadados(resposta))
            if salvo:
                return {**deepcopy(salvo[1]), "cache": True, "desatualizado": True}
            raise erro
        if resposta.status_code == 429:
            espera = self._espera(resposta.headers.get("Retry-After"))
            with self.lock:
                self.bloqueado_ate = self.relogio() + espera
            raise ErroBenchmark("O limite de consultas foi atingido. Aguarde para tentar novamente.", "limite", 429, espera)
        if resposta.status_code == 404:
            raise ErroBenchmark("Jogo ou componente sem correspondência no provedor.", "nao-encontrado", 404)
        if resposta.status_code >= 500:
            erro = self._falhar("A FPSHQ está temporariamente indisponível. Nenhum FPS foi estimado pela BOOSTio.",
                                "provedor", 503, self._espera(resposta.headers.get("Retry-After")), diagnostico=self._metadados(resposta))
            if salvo:
                return {**deepcopy(salvo[1]), "cache": True, "desatualizado": True}
            raise erro
        if resposta.status_code != 200:
            raise ErroBenchmark("O provedor não conseguiu atender à consulta agora.")
        try:
            dados = resposta.json()
        except ValueError as causa:
            html = "text/html" in str(resposta.headers.get("Content-Type", "")).lower()
            mensagem = "O serviço de testes de jogos não enviou os dados necessários. A resposta é inválida; tente novamente mais tarde."
            erro = self._falhar(mensagem, "resposta-nao-json" if html else "resposta", 502, 60, diagnostico=self._metadados(resposta))
            if salvo:
                return {**deepcopy(salvo[1]), "cache": True, "desatualizado": True}
            raise erro from causa
        if not isinstance(dados, dict) or dados.get("ok") is not True:
            raise ErroBenchmark("Não há dados disponíveis para esta consulta.", "sem-dados", 422)
        return {"dados": dados, "consultadoEm": int(self.data_atual() * 1000), "cache": False}

    @staticmethod
    def _metadados(resposta):
        tipo = str(resposta.headers.get("Content-Type", "")).lower()
        return {
            "httpProvedor": resposta.status_code,
            "tipoResposta": "json" if "json" in tipo else "html" if "text/html" in tipo else "outro",
            "redirecionamento": 300 <= resposta.status_code < 400,
        }

    def _falhar(self, mensagem, codigo, status, espera, causa=None, diagnostico=None):
        erro = ErroBenchmark(mensagem, codigo, status, espera, diagnostico)
        meta = erro.diagnostico
        logger.warning("FPSHQ: %s; http_boostio=%s; http_provedor=%s; formato=%s; causa=%s",
                       codigo, status, meta.get("httpProvedor", "desconhecido"),
                       meta.get("tipoResposta", "desconhecido"), type(causa).__name__ if causa else "resposta")
        with self.lock:
            self.falha_temporaria = (self.relogio() + espera, mensagem, codigo, status, deepcopy(meta))
        return erro

    def salvar(self, caminho, parametros, resultado):
        chave = (caminho, tuple(sorted(parametros.items())))
        with self.lock:
            self.cache[chave] = (self.relogio(), deepcopy(resultado))
            self.cache.move_to_end(chave)
            while len(self.cache) > self.MAX_CACHE:
                self.cache.popitem(last=False)

    def _validar_limites(self, agora, usuario_id):
        if agora < self.bloqueado_ate:
            raise ErroBenchmark("Aguarde o intervalo solicitado pelo provedor.", "limite", 429, math.ceil(self.bloqueado_ate - agora))
        for fila, janela in ((self.minuto, 60), (self.dia, 86400)):
            while fila and agora - fila[0] >= janela:
                fila.popleft()
        usuario = self.usuarios.setdefault(str(usuario_id), deque())
        self.usuarios.move_to_end(str(usuario_id))
        while usuario and agora - usuario[0] >= 60:
            usuario.popleft()
        for fila, limite, janela in ((usuario, self.LIMITE_USUARIO, 60), (self.minuto, self.LIMITE_MINUTO, 60), (self.dia, self.LIMITE_DIA, 86400)):
            if len(fila) >= limite:
                raise ErroBenchmark("Aguarde antes de fazer outra consulta de desempenho.", "limite", 429, max(1, math.ceil(janela - agora + fila[0])))
        usuario.append(agora)
        self.minuto.append(agora)
        self.dia.append(agora)
        while len(self.usuarios) > 1000:
            self.usuarios.popitem(last=False)

    @staticmethod
    def _espera(valor):
        try:
            espera = float(valor)
            if not math.isfinite(espera) or espera <= 0:
                return 60
            return max(1, math.ceil(espera))
        except (TypeError, ValueError, OverflowError):
            try:
                data = parsedate_to_datetime(valor)
                return max(1, math.ceil((data - datetime.now(timezone.utc)).total_seconds()))
            except (TypeError, ValueError, OverflowError):
                return 60


cliente_fpshq = FpshqService()
