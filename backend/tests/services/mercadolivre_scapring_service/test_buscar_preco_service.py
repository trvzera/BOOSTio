from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
import requests
from flask import Flask

from models import db, TokensMeli
from services.mercadolivre_scapring_service.buscar_preco_service import (
    BuscarPrecoMercadoLivreService, PrecoMercadoLivreIndisponivelError,
)
from services.mercadolivre_scapring_service.salvar_tokens_service import SalvarTokensMeliService


MODULO = "services.mercadolivre_scapring_service.consultar_api_service"


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        SalvarTokensMeliService().executar({
            "access_token": "teste", "refresh_token": "refresh", "expires_in": 3600,
        })
        yield
        db.session.remove()
        db.drop_all()


def resposta(status=200, dados=None, headers=None):
    retorno = Mock(ok=status < 400, status_code=status, headers=headers or {})
    retorno.json.return_value = dados
    return retorno


def test_consulta_preco_com_token_do_banco(banco):
    with patch(f"{MODULO}.requests.get", return_value=resposta(dados={
        "amount": 899.90, "regular_amount": 999.90, "currency_id": "BRL",
    })) as get:
        assert BuscarPrecoMercadoLivreService().executar("MLB1234567890") == Decimal("899.90")
    get.assert_called_once_with(
        "https://api.mercadolibre.com/items/MLB1234567890/sale_price",
        params={"context": "channel_marketplace"},
        headers={"Authorization": "Bearer teste"}, timeout=15,
    )


@pytest.mark.parametrize("dados", [
    {}, {"amount": None}, {"amount": 0}, {"amount": -1},
    {"amount": "NaN"}, {"amount": "Infinity"},
    {"amount": 100, "currency_id": "USD"},
])
def test_nao_retorna_preco_invalido(banco, dados):
    with patch(f"{MODULO}.requests.get", return_value=resposta(dados=dados)):
        with pytest.raises(PrecoMercadoLivreIndisponivelError):
            BuscarPrecoMercadoLivreService().executar("MLB1234567890")


@pytest.mark.parametrize("status", [403, 404])
def test_preserva_erro_http(banco, status):
    with patch(f"{MODULO}.requests.get", return_value=resposta(status)):
        with pytest.raises(requests.HTTPError) as erro:
            BuscarPrecoMercadoLivreService().executar("MLB1234567890")
    assert erro.value.response.status_code == status


def test_renova_token_rejeitado_uma_vez(banco):
    def renovar(*args):
        SalvarTokensMeliService().executar({
            "access_token": "novo", "refresh_token": "refresh-novo", "expires_in": 3600,
        })
    with patch(f"{MODULO}.requests.get", side_effect=[resposta(401), resposta(401)]) as get, \
         patch(f"{MODULO}.RefreshTokenMercadoLivreService.executar", side_effect=renovar) as refresh:
        with pytest.raises(requests.HTTPError):
            BuscarPrecoMercadoLivreService().executar("MLB1234567890")
    assert get.call_count == 2
    refresh.assert_called_once_with("refresh")
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer novo"


def test_limita_tentativas_429(banco):
    with patch(f"{MODULO}.requests.get", return_value=resposta(429, headers={"Retry-After": "1"})) as get, \
         patch(f"{MODULO}.time.sleep") as sleep:
        with pytest.raises(requests.HTTPError):
            BuscarPrecoMercadoLivreService().executar("MLB1234567890")
    assert get.call_count == 3
    assert sleep.call_count == 2


def test_banco_vazio_usa_refresh_inicial(banco):
    TokensMeli.query.delete()
    db.session.commit()
    renovacao = resposta(dados={"access_token": "inicial", "refresh_token": "novo", "expires_in": 3600})
    with patch(f"{MODULO}.os.getenv", return_value="refresh-env"), \
         patch("services.mercadolivre_scapring_service.refresh_token_service.requests.post", return_value=renovacao) as post, \
         patch(f"{MODULO}.requests.get", return_value=resposta(dados={"amount": 10, "currency_id": "BRL"})):
        assert BuscarPrecoMercadoLivreService().executar("MLB1234567890") == Decimal("10")
    assert post.call_args.kwargs["data"]["refresh_token"] == "refresh-env"
    assert TokensMeli.buscar_atual().access_token == "inicial"


def test_timeout_e_json_invalido(banco):
    with patch(f"{MODULO}.requests.get", side_effect=requests.Timeout):
        with pytest.raises(requests.Timeout):
            BuscarPrecoMercadoLivreService().executar("MLB1234567890")
    retorno = resposta()
    retorno.json.side_effect = requests.exceptions.JSONDecodeError("invalid", "", 0)
    with patch(f"{MODULO}.requests.get", return_value=retorno):
        with pytest.raises(ValueError, match="sem JSON válido"):
            BuscarPrecoMercadoLivreService().executar("MLB1234567890")
