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
    assert CriarBuildService._campos_pecas(cabo)["categoria_cabo"] == "CAT6"


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


def test_nao_inventa_atualizacao_e_estoque_nao_renova_data_do_preco():
    peca = PlacaVideo(id=1, modelo="GPU", preco=100)
    assert peca.to_catalogo()["preco_atualizado_em"] is None
    anterior = datetime(2026, 10, 19, 10)
    peca.preco_atualizado_em = anterior
    peca.aplicar_cotacao({"preco": None, "esgotado": True}, datetime(2026, 10, 20, 10))
    assert peca.preco == 100 and peca.esgotado
    assert peca.preco_atualizado_em == anterior
    agora = datetime(2026, 10, 21, 10)
    peca.aplicar_cotacao({"preco": 120, "esgotado": False}, agora)
    assert peca.preco == 120 and not peca.esgotado
    assert peca.preco_atualizado_em == agora


def test_catalogo_entrega_preco_coletado_para_a_oferta_kabum_sem_inventar_outras_lojas():
    data = datetime(2026, 10, 23, 12)
    peca = PlacaVideo(id=1, modelo="GPU", preco=1234.56, preco_atualizado_em=data,
                     kabum_external="https://www.kabum.com.br/produto/123/gpu", esgotado=False)
    catalogo = peca.to_catalogo()
    assert catalogo["ofertas"] == [{"loja": "kabum", "url": peca.kabum_external, "preco": 1234.56,
                                   "atualizadoEm": "2026-10-23T12:00:00+00:00", "esgotado": False}]
    peca.aplicar_cotacao({"preco": None, "esgotado": True}, datetime(2026, 10, 23, 13))
    oferta = peca.to_catalogo()["ofertas"][0]
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
