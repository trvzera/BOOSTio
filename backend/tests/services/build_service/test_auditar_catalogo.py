from types import SimpleNamespace

import pytest
from flask import Flask

from commands.precos import registrar_comandos_precos
from services.peca_service.auditar_catalogo_service import AuditarCatalogoService


def modelo(nome, pecas):
    return SimpleNamespace(__tablename__=nome, mostrar_pecas=lambda: [SimpleNamespace(to_catalogo=lambda p=p: p.copy()) for p in pecas])


def test_auditoria_aponta_pendencias_sem_rede_e_sem_gravacao(monkeypatch):
    boa = {"id": "processador:1", "part_number": "PN", "preco": 100, "esgotado": False, "preco_atualizado_em": "2026-10-22T12:00:00Z",
           "link": "https://www.kabum.com.br/produto/123/teste", "imagem": "../imgs/produtos/processador-1.jpg", "fonte_medidas": "https://example.test"}
    ruim = {**boa, "id": "processador:2", "preco": float("nan"), "esgotado": True, "link": "javascript:alert(1)",
            "imagem": "../data/catalogo-demo.json", "preco_atualizado_em": None}
    monkeypatch.setattr("services.peca_service.auditar_catalogo_service.MODELOS_PECAS", [modelo("processador", [boa, ruim])])
    monkeypatch.setattr("requests.get", lambda *a, **k: pytest.fail("Auditoria não deve acessar lojas"))
    from models import db
    monkeypatch.setattr(db.session, "commit", lambda: pytest.fail("Auditoria não deve gravar"))
    monkeypatch.setattr(db, "create_all", lambda: pytest.fail("Auditoria não deve preparar banco"))
    resumo = AuditarCatalogoService().executar(1)
    cpu = resumo["categorias"]["processador"]
    assert resumo["somenteLeitura"] and not resumo["temOfertasNasCategoriasObrigatorias"]
    assert cpu["total"] == 2 and cpu["disponiveisComPreco"] == 1 and cpu["imagensLocais"] == 1
    assert cpu["pendencias"]["part_number_duplicado"] == 2
    for pendencia in ("sem_preco_valido", "preco_sem_data", "indisponivel", "link_nao_validado", "imagem_local_ausente"):
        assert cpu["pendencias"][pendencia] == 1
    assert len(cpu["amostras"]) == 1


@pytest.mark.parametrize("valor", [-1, 21, True, "5", None])
def test_amostras_validacao(valor):
    with pytest.raises(ValueError):
        AuditarCatalogoService().executar(valor)


def test_comando_registrado_e_limita_amostras(monkeypatch):
    app = Flask(__name__)
    registrar_comandos_precos(app)
    monkeypatch.setattr(AuditarCatalogoService, "executar", lambda self, amostras: {"somenteLeitura": True, "amostras": amostras})
    runner = app.test_cli_runner()
    resultado = runner.invoke(args=["catalogo-auditar", "--amostras", "0"])
    assert resultado.exit_code == 0 and '"somenteLeitura": true' in resultado.output
    assert runner.invoke(args=["catalogo-auditar", "--amostras", "21"]).exit_code != 0


@pytest.mark.parametrize("imagem", [123, {"url": "foo"}, "https://[", "javascript:alert(1)"])
def test_dado_malformado_e_estoque_desconhecido_nao_aprovam_oferta(monkeypatch, imagem):
    peca = {"id": "ssd:1", "preco": 100, "imagem": imagem}
    monkeypatch.setattr("services.peca_service.auditar_catalogo_service.MODELOS_PECAS", [modelo("ssd", [peca])])
    resumo = AuditarCatalogoService().executar()["categorias"]["ssd"]
    assert resumo["disponiveisComPreco"] == 0
    assert resumo["pendencias"]["estoque_nao_confirmado"] == 1
    assert resumo["pendencias"]["imagem_invalida"] == 1
