import pytest
from flask import Flask

from services.llm_service import reservar_chamada_service as cota
from services.llm_service.bloquear_geracao_service import BloquearGeracaoService, GeracaoEmAndamentoError


def test_cota_global_conta_cada_chamada_e_rejeita_a_seguinte(monkeypatch):
    monkeypatch.setattr(cota, "_dia_local", None)
    monkeypatch.setattr(cota, "_chamadas_locais", 0)
    monkeypatch.setattr(cota.ReservarChamadaService, "LIMITE_DIARIO", 2)
    app = Flask(__name__)
    app.config["RATELIMIT_STORAGE_URI"] = "memory://"
    with app.app_context():
        servico = cota.ReservarChamadaService()
        servico.executar()
        servico.executar()
        with pytest.raises(cota.CotaGlobalIAError) as erro:
            servico.executar()
    assert 0 < erro.value.espera <= 24 * 60 * 60


def test_mesmo_usuario_nao_gera_em_paralelo():
    app = Flask(__name__)
    app.config["RATELIMIT_STORAGE_URI"] = "memory://"
    with app.app_context():
        servico = BloquearGeracaoService()
        with servico.executar(7):
            with pytest.raises(GeracaoEmAndamentoError):
                with servico.executar(7):
                    pass
            with servico.executar(8):
                pass
        with servico.executar(7):
            pass


def test_redis_compartilha_cota_entre_processos(monkeypatch):
    class RedisFalso:
        chamadas = 0

        @classmethod
        def from_url(cls, *_args, **_kwargs):
            return cls()

        def eval(self, _script, _num_chaves, _chave, _expiracao):
            type(self).chamadas += 1
            return type(self).chamadas

    monkeypatch.setattr(cota, "Redis", RedisFalso)
    monkeypatch.setattr(cota.ReservarChamadaService, "LIMITE_DIARIO", 1)
    app = Flask(__name__)
    app.config["RATELIMIT_STORAGE_URI"] = "redis://redis:6379/0"
    with app.app_context():
        cota.ReservarChamadaService().executar()
        with pytest.raises(cota.CotaGlobalIAError):
            cota.ReservarChamadaService().executar()
