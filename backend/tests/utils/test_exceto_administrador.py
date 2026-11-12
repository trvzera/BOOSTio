import pytest
from flask import Flask

from services.llm_service import reservar_chamada_service as cota
from utils.decorators import exceto_administrador


@exceto_administrador
def verificar():
    return "executou"


def test_executa_para_usuario_comum(monkeypatch):
    monkeypatch.setattr("utils.decorators.usuario_atual_e_administrador", lambda: False)
    assert verificar() == "executou"


def test_pula_a_funcao_para_administrador(monkeypatch):
    monkeypatch.setattr("utils.decorators.usuario_atual_e_administrador", lambda: True)
    assert verificar() is None


def test_administrador_nao_consome_a_cota_diaria_de_ia(monkeypatch):
    monkeypatch.setattr(cota.ReservarChamadaService, "LIMITE_DIARIO", 1)
    monkeypatch.setattr(cota, "_dia_local", None)
    monkeypatch.setattr(cota, "_chamadas_locais", 0)
    monkeypatch.setattr("utils.decorators.usuario_atual_e_administrador", lambda: True)
    with Flask(__name__).app_context():
        for _ in range(3):
            cota.ReservarChamadaService().executar()
        assert cota._chamadas_locais == 0
