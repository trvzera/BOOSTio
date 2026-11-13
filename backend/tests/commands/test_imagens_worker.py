from threading import Event
from unittest.mock import MagicMock, patch

import requests

from commands.precos import _coletar_imagens


class PecaFalsa:
    def __init__(self, identificador):
        self.id = identificador


def modelo(nome, ids):
    classe = MagicMock()
    classe.__tablename__ = nome
    classe.sem_imagem_com_fonte.return_value = [PecaFalsa(i) for i in ids]
    return classe


def erro_http(status):
    resposta = MagicMock(status_code=status)
    return requests.HTTPError(response=resposta)


def coletar(modelos, servico, **kwargs):
    with patch("commands.precos.MODELOS_PECAS", modelos):
        return _coletar_imagens(servico, kwargs.pop("limite", None), 0, kwargs.pop("categoria", ()), **kwargs)


def test_conta_salvas_e_falhas_sem_bloquear():
    servico = MagicMock()
    servico.executar.side_effect = [None, ValueError("sem foto"), None]
    resumo = coletar([modelo("placa_video", [1, 2, 3])], servico)
    assert resumo == {"consultas": 3, "salvas": 2, "falhas": 1, "bloqueada": False}


def test_bloqueio_da_loja_encerra_a_passada():
    servico = MagicMock()
    servico.executar.side_effect = [None, erro_http(429)]
    resumo = coletar([modelo("placa_video", [1, 2, 3]), modelo("memoria_ram", [4])], servico)
    assert resumo["bloqueada"] and resumo["consultas"] == 2 and servico.executar.call_count == 2


def test_parada_pedida_interrompe_antes_da_proxima_peca():
    parada = Event()
    servico = MagicMock()
    servico.executar.side_effect = lambda peca: parada.set()
    resumo = coletar([modelo("placa_video", [1, 2, 3])], servico, parada=parada)
    assert resumo["consultas"] == 1 and not resumo["bloqueada"]


def test_categoria_e_limite_restringem_a_coleta():
    servico = MagicMock()
    resumo = coletar([modelo("placa_video", [1, 2, 3]), modelo("memoria_ram", [4, 5])], servico,
                     categoria=("memoria_ram",), limite=1)
    assert resumo["consultas"] == 1 and servico.executar.call_args.args[0].id == 4
