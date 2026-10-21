from collections import OrderedDict, deque
from copy import deepcopy
import math
import re
from threading import RLock
import time

import requests

from .fpshq_service import ErroBenchmark, FpshqService


class BlenderService:
    """Consulta agregados públicos, nunca executa Blender ou mede o computador do usuário."""
    URL = "https://opendata.blender.org/benchmarks/query/"
    TTL = 3600
    MAX_CACHE = 128
    COLUNAS = ("Device Name", "Compute Type", "Blender Version", "Median Score", "Number of Benchmarks")

    def __init__(self, buscar=None, relogio=None, data_atual=None):
        self.buscar = buscar or requests.get
        self.relogio = relogio or time.monotonic
        self.data_atual = data_atual or time.time
        self.cache = OrderedDict()
        self.usuarios = OrderedDict()
        self.chamadas = deque()
        self.bloqueado_ate = 0
        self.lock = RLock()
        self.chaves = [RLock() for _ in range(32)]

    def executar(self, dados, usuario_id):
        nome, tipo = dados.get("dispositivo"), dados.get("tipo")
        if not isinstance(nome, str) or not re.fullmatch(r"[A-Za-z0-9() +._/\-]{2,160}", nome) or tipo not in ("cpu", "gpu"):
            raise ValueError("Selecione um modelo identificado de CPU ou GPU para consultar o Blender.")
        nome = re.sub(r"^\d{2}(?:st|nd|rd|th) Gen\s+", "", nome, flags=re.I)
        nome = re.sub(r"\((?:R|TM)\)", "", nome, flags=re.I)
        chave = (nome, tipo)
        with self.chaves[hash(chave) % len(self.chaves)]:
            with self.lock:
                agora = self.relogio()
                salvo = self.cache.get(chave)
                if salvo and agora - salvo[0] < self.TTL:
                    self.cache.move_to_end(chave)
                    return {**deepcopy(salvo[1]), "cache": True}
                self._limitar(agora, usuario_id)
            parametros = [("device_name", nome), ("group_by", "device_name"), ("group_by", "compute_type"),
                          ("group_by", "blender_version"), ("response_type", "datatables")]
            try:
                resposta = self.buscar(self.URL, params=parametros, headers={"Accept": "application/json"},
                                      timeout=(4, 10), allow_redirects=False)
            except requests.Timeout as erro:
                raise ErroBenchmark("O Blender Open Data não respondeu a tempo. Tente novamente mais tarde.", "timeout", 504) from erro
            except requests.RequestException as erro:
                raise ErroBenchmark("Não foi possível consultar o Blender Open Data agora.", "rede", 503) from erro
            if resposta.status_code == 429:
                espera = FpshqService._espera(resposta.headers.get("Retry-After"))
                with self.lock:
                    self.bloqueado_ate = self.relogio() + espera
                raise ErroBenchmark("A fonte solicitou uma pausa. Aguarde para consultar novamente.", "limite", 429, espera)
            if resposta.status_code != 200:
                raise ErroBenchmark("O Blender Open Data está indisponível no momento.", "provedor", 503)
            try:
                bruto = resposta.json()
            except ValueError as erro:
                raise ErroBenchmark("O Blender retornou dados inválidos.", "resposta") from erro
            resultado = self._normalizar(bruto, nome, tipo)
            resultado.update(consultadoEm=int(self.data_atual() * 1000), cache=False)
            with self.lock:
                self.cache[chave] = (self.relogio(), deepcopy(resultado))
                self.cache.move_to_end(chave)
                while len(self.cache) > self.MAX_CACHE:
                    self.cache.popitem(last=False)
            return resultado

    def _normalizar(self, bruto, nome, tipo):
        if not isinstance(bruto, dict) or not isinstance(bruto.get("columns"), list) or not isinstance(bruto.get("rows"), list) or len(bruto["rows"]) > 1000:
            raise ErroBenchmark("O Blender retornou um formato de dados inesperado.", "resposta")
        colunas = [coluna.get("display_name") if isinstance(coluna, dict) else None for coluna in bruto["columns"]]
        if not all(isinstance(coluna, str) for coluna in colunas) or any(colunas.count(campo) != 1 for campo in self.COLUNAS):
            raise ErroBenchmark("O formato do Blender mudou. A integração precisa ser revisada.", "resposta")
        metodos = {"CPU"} if tipo == "cpu" else {"CUDA", "OPTIX", "HIP", "METAL", "ONEAPI"}
        registros = []
        for linha in bruto["rows"]:
            if not isinstance(linha, list) or len(linha) != len(colunas):
                continue
            registro = dict(zip(colunas, linha))
            dispositivo, metodo = registro["Device Name"], registro["Compute Type"]
            versao, score, quantidade = registro["Blender Version"], registro["Median Score"], registro["Number of Benchmarks"]
            identidade = re.sub(r"^\d{2}(?:st|nd|rd|th) Gen\s+", "", dispositivo, flags=re.I) if isinstance(dispositivo,str) else ""
            identidade = re.sub(r"\((?:R|TM)\)", "", identidade, flags=re.I)
            if identidade.casefold() != nome.casefold() or not isinstance(metodo, str) or metodo not in metodos:
                continue
            if not isinstance(versao, str) or not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{1,2}", versao):
                continue
            if type(score) not in (int, float) or not math.isfinite(score) or score < 0 or type(quantidade) is not int or quantidade < 1:
                continue
            registros.append(registro)
        if not registros:
            raise ErroBenchmark("Não há resultados públicos para esse modelo. Não substituímos por uma peça parecida.", "sem-dados", 422)
        # Versão mais recente disponível; nela, o método com mais resultados, não a maior pontuação.
        escolhido = max(registros, key=lambda r: (tuple(map(int, r["Blender Version"].split("."))), r["Number of Benchmarks"]))
        return {"dispositivo": escolhido["Device Name"], "tipo": tipo, "versao": escolhido["Blender Version"],
                "metodo": escolhido["Compute Type"], "score": escolhido["Median Score"], "quantidade": escolhido["Number of Benchmarks"],
                "unidade": "amostras/min", "url": self.URL + "?" + requests.compat.urlencode({"device_name": escolhido["Device Name"], "blender_version": escolhido["Blender Version"], "group_by": "device_name"})}

    def _limitar(self, agora, usuario_id):
        if agora < self.bloqueado_ate:
            raise ErroBenchmark("Aguarde o intervalo solicitado pelo Blender Open Data.", "limite", 429, math.ceil(self.bloqueado_ate - agora))
        usuario = self.usuarios.setdefault(str(usuario_id), deque())
        self.usuarios.move_to_end(str(usuario_id))
        for fila in (usuario, self.chamadas):
            while fila and agora - fila[0] >= 60:
                fila.popleft()
        if len(usuario) >= 10 or len(self.chamadas) >= 30:
            raise ErroBenchmark("Aguarde antes de consultar o Blender novamente.", "limite", 429, 60)
        usuario.append(agora)
        self.chamadas.append(agora)
        while len(self.usuarios) > 1000:
            self.usuarios.popitem(last=False)


cliente_blender = BlenderService()
