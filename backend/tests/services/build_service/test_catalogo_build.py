from datetime import datetime, timedelta, timezone

import pytest

from models import PlacaVideo


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
