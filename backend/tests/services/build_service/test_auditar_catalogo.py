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


def test_auditoria_reconhece_volume_e_rejeita_caminho_fora_dele(monkeypatch, tmp_path):
    volume = tmp_path / "coletados"
    (volume / "imagens").mkdir(parents=True)
    (volume / "imagens" / "peca.jpg").write_bytes(b"foto")
    (tmp_path / "fora.jpg").write_bytes(b"fora")
    pecas = [{"id": "ssd:1", "imagem": "../coletados/imagens/peca.jpg"},
             {"id": "ssd:2", "imagem": "../coletados/../fora.jpg"}]
    monkeypatch.setattr("services.peca_service.auditar_catalogo_service.PASTA_COLETADOS", volume)
    monkeypatch.setattr("services.peca_service.auditar_catalogo_service.MODELOS_PECAS", [modelo("ssd", pecas)])
    resumo = AuditarCatalogoService().executar()["categorias"]["ssd"]
    assert resumo["imagensLocais"] == 1
    assert resumo["pendencias"]["imagem_local_ausente"] == 1


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


def test_auditoria_indica_especificacoes_ausentes_sem_tratar_zero_como_ausente(monkeypatch):
    peca = {"id": "gabinete:1", "fans_inclusos": 0, "quantidade_max_fans": None, "posicoes_fans": []}
    monkeypatch.setattr("services.peca_service.auditar_catalogo_service.MODELOS_PECAS", [modelo("gabinete", [peca])])
    resumo = AuditarCatalogoService().executar(1)["categorias"]["gabinete"]
    assert "fans_inclusos" not in resumo["camposTecnicosAusentes"]
    assert resumo["camposTecnicosAusentes"]["quantidade_max_fans"] == 1
    assert resumo["camposTecnicosAusentes"]["posicoes_fans"] == 1
    assert resumo["amostrasTecnicas"][0]["id"] == "gabinete:1"
    assert not AuditarCatalogoService().executar(0)["categorias"]["gabinete"]["amostrasTecnicas"]


def test_detalhamento_tecnico_inclui_todas_as_pecas_sem_limite_de_amostras(monkeypatch):
    pecas = [{"id": f"fonte:{i}", "modelo": f"Fonte {i}", "potencia_w": 650} for i in range(25)]
    monkeypatch.setattr("services.peca_service.auditar_catalogo_service.MODELOS_PECAS", [modelo("fonte", pecas)])
    resultado = AuditarCatalogoService().executar(0, detalhar=True)
    fonte = resultado["categorias"]["fonte"]
    assert fonte["camposCompatibilidadeAusentes"]["conectores_alimentacao"] == 25
    assert len(fonte["detalhesCompatibilidade"]) == 25
    assert not fonte["amostrasTecnicas"]
    assert len(resultado["verificacoesSemprePendentes"]) == 4
    assert "detalhesCompatibilidade" not in AuditarCatalogoService().executar()["categorias"]["fonte"]


def test_campos_condicionais_e_booleanos_nao_geram_falta_falsa():
    falta = AuditarCatalogoService._ausente
    assert not falta({"fans_inclusos": 0}, "fans_inclusos")
    assert not falta({"videointegrado": False}, "videointegrado")
    assert not falta({"quantidade_slots_m2": 0, "slots_m2": []}, "slots_m2")
    assert not falta({"conectores_alimentacao": {}, "conectores_alimentacao_completos": True}, "conectores_alimentacao")
    assert falta({"conectores_alimentacao": {}}, "conectores_alimentacao")
    assert falta({"conectores_alimentacao_completos": False}, "conectores_alimentacao_completos")
    assert not falta({"interface": "SATA", "formato": "2.5"}, "formato_m2")
    assert not falta({"interface": "PCIe NVMe", "formato": "M.2 2280"}, "formato_m2")
    assert falta({"interface": "PCIe NVMe", "formato": "M.2"}, "formato_m2")
    assert falta({"altura_mm": " não informado "}, "altura_mm")
    assert falta({"altura_mm": float("nan")}, "altura_mm")


def test_cli_auditoria_detalhada(monkeypatch):
    app = Flask(__name__)
    registrar_comandos_precos(app)
    monkeypatch.setattr(AuditarCatalogoService, "executar", lambda self, amostras, **kwargs: kwargs)
    resultado = app.test_cli_runner().invoke(args=["catalogo-auditar", "--detalhar"])
    assert resultado.exit_code == 0 and '"detalhar": true' in resultado.output


def test_auditoria_distingue_referencia_de_chip_de_modelo_comercial(monkeypatch):
    pecas = [{"id": "placa_video:1", "fabricante": "NVIDIA", "modelo": "GeForce RTX 4060"},
             {"id": "placa_video:2", "fabricante": "ASUS", "modelo": "Dual GeForce RTX 4060 OC"}]
    monkeypatch.setattr("services.peca_service.auditar_catalogo_service.MODELOS_PECAS", [modelo("placa_video", pecas)])
    resultado = AuditarCatalogoService().executar(0, detalhar=True)["categorias"]["placa_video"]
    assert resultado["quantidadeReferenciasGenericas"] == 1
    assert resultado["referenciasGenericas"][0]["id"] == "placa_video:1"
