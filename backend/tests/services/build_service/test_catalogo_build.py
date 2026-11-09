from services.build_service.catalogo_geracao_service import campos_pecas
from datetime import datetime, timedelta, timezone

import pytest

from models import PlacaVideo, CaboRede
from services.build_service.criar_build_service import CriarBuildService


def test_catalogo_preserva_cat6_sem_sobrescrever_a_categoria_do_editor():
    cabo = CaboRede(id=1, modelo="Cabo de rede 20m", categoria="CAT6", comprimento_m=20, preco=30)
    ficha = cabo.to_catalogo()
    assert ficha["categoria"] == "cabo_rede"
    assert ficha["categoria_cabo"] == "CAT6"
    assert cabo.categoria == "CAT6"
    assert campos_pecas(cabo)["categoria_cabo"] == "CAT6"


@pytest.mark.parametrize("data", [datetime(2026, 10, 20, 15, 30),
                                 datetime(2026, 10, 20, 12, 30, tzinfo=timezone(timedelta(hours=-3)))])
def test_catalogo_expoe_data_do_preco_com_fuso_sem_mudar_o_modelo(data):
    peca = PlacaVideo(id=1, modelo="GPU", preco=100, preco_atualizado_em=data,
                     imagem_url="../imgs/produtos/placa_video-1.webp")
    catalogo = peca.to_catalogo()
    assert datetime.fromisoformat(catalogo["preco_atualizado_em"]).astimezone(timezone.utc) == datetime(2026, 10, 20, 15, 30, tzinfo=timezone.utc)
    assert peca.preco_atualizado_em is data
    assert catalogo["id"] == "placa_video:1"
    assert catalogo["imagem"] == "../imgs/produtos/placa_video-1.webp"
    assert "imagem_url" not in catalogo


@pytest.fixture
def banco():
    from flask import Flask
    from models import db
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.engine.dispose()


def _peca_com_oferta(db, **oferta):
    from repositories.ofertas_kabum_repository import gravar_cotacao_inicial
    peca = PlacaVideo(modelo="GPU", fabricante="Marca", memoria_gb=8)
    db.session.add(peca)
    db.session.flush()
    gravar_cotacao_inicial(peca, "https://www.kabum.com.br/produto/123/gpu", oferta.get("preco", 100),
                           oferta.get("esgotado", False), oferta.get("atualizado_em"))
    db.session.commit()
    return peca


def test_nao_inventa_atualizacao_e_estoque_nao_renova_data_do_preco(banco):
    from repositories.ofertas_kabum_repository import aplicar_cotacao, buscar_ativa
    anterior = datetime(2026, 10, 19, 10)
    peca = _peca_com_oferta(banco, preco=100, atualizado_em=anterior)
    oferta = buscar_ativa(peca)
    aplicar_cotacao(oferta, {"preco": None, "esgotado": True}, datetime(2026, 10, 20, 10))
    banco.session.commit()
    assert peca.preco == 100 and peca.esgotado
    assert peca.preco_atualizado_em == anterior
    agora = datetime(2026, 10, 21, 10)
    aplicar_cotacao(oferta, {"preco": 120, "esgotado": False}, agora)
    banco.session.commit()
    assert peca.preco == 120 and not peca.esgotado
    assert peca.preco_atualizado_em == agora


def test_peca_sem_oferta_nao_tem_preco_nem_data(banco):
    peca = PlacaVideo(modelo="GPU", fabricante="Marca", memoria_gb=8)
    banco.session.add(peca)
    banco.session.commit()
    assert peca.preco is None and peca.esgotado is None
    assert peca.to_catalogo()["preco_atualizado_em"] is None


def test_catalogo_entrega_preco_coletado_para_a_oferta_kabum_sem_inventar_outras_lojas(banco):
    from models import Oferta
    from repositories.ofertas_kabum_repository import aplicar_cotacao, buscar_ativa
    data = datetime(2026, 10, 23, 12)
    peca = _peca_com_oferta(banco, preco=1234.56, atualizado_em=data)
    catalogo = Oferta.anexar_a_catalogo([peca.to_catalogo()])[0]
    assert len(catalogo["ofertas"]) == 1
    oferta = catalogo["ofertas"][0]
    assert (oferta["loja"], oferta["url"], oferta["preco"], oferta["esgotado"]) == (
        "kabum", "https://www.kabum.com.br/produto/123/gpu", 1234.56, False)
    assert oferta["atualizadoEm"] == "2026-10-23T12:00:00+00:00"
    aplicar_cotacao(buscar_ativa(peca), {"preco": None, "esgotado": True}, datetime(2026, 10, 23, 13))
    banco.session.commit()
    oferta = Oferta.anexar_a_catalogo([peca.to_catalogo()])[0]["ofertas"][0]
    assert oferta["esgotado"] is True
    assert oferta["preco"] == 1234.56 and oferta["atualizadoEm"] == catalogo["preco_atualizado_em"]


@pytest.mark.parametrize("link", [None, "", "https://www.kabum.com.br/busca/gpu",
                                    "https://www.pichau.com.br/produto/123", "javascript:alert(1)",
                                    "http://www.kabum.com.br/produto/123", "https://www.kabum.com.br.evil.example/produto/123",
                                    "https://usuario@www.kabum.com.br/produto/123", "https://www.kabum.com.br:8443/produto/123",
                                    "https://www.kabum.com.br:errada/produto/123"])
def test_sem_link_exato_kabum_nao_atribui_preco_a_uma_busca(link):
    peca = PlacaVideo(id=1, modelo="GPU", preco=100, preco_atualizado_em=datetime(2026, 10, 23), kabum_external=link)
    assert peca.to_catalogo()["ofertas"] == []


@pytest.mark.parametrize("preco", [None, 0, -1, True, "100", float("inf"), float("nan")])
def test_preco_invalido_nao_vira_oferta(preco):
    peca = PlacaVideo(id=1, modelo="GPU", preco=preco, preco_atualizado_em=datetime(2026, 10, 23),
                     kabum_external="https://www.kabum.com.br/produto/123/gpu")
    assert peca.to_catalogo()["ofertas"] == []


def test_preco_inicial_sem_data_de_coleta_nao_vira_oferta():
    peca = PlacaVideo(id=1, modelo="GPU", preco=100, kabum_external="https://www.kabum.com.br/produto/123/gpu")
    assert peca.to_catalogo()["ofertas"] == []
