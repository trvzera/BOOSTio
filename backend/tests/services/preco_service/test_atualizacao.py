from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
import requests
from flask import Flask
from sqlalchemy import inspect, text

from models import db, PlacaVideo, ConsultaPreco, ControleColeta
from services.peca_service.atualizar_precos_service import AtualizarPrecosService
from services.peca_service.migrar_links_service import MigrarLinksService
from services.peca_service.popular_pecas_service import PopularPecasService
from services.peca_service.salvar_peca_service import SalvarPecaService
from services.preco_service.reservar_consulta_service import ReservarConsultaService
from services.preco_service.brightdata_service import BrightDataService, ColetaPendenteError


HTTP = "services.preco_service.brightdata_service.requests"
URL = "https://www.mercadolivre.com.br/placa/p/MLB64959148?pdp_filters=item_id:MLB4771805087"


@pytest.fixture
def banco(monkeypatch):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    monkeypatch.setenv("BRIGHTDATA_API_KEY", "chave-teste")
    with app.app_context():
        MigrarLinksService().executar()
        yield app
        db.session.remove()
        db.drop_all()


def criar_peca(url=URL):
    return SalvarPecaService().executar(PlacaVideo, {
        "fabricante": "Palit", "modelo": "RTX3050", "memoria_gb": 6,
        "consumo_energia": 70, "meli_external": url,
    })


def resposta(status=200, dados=None):
    r = Mock(status_code=status)
    r.json.return_value = dados
    if status >= 400:
        r.raise_for_status.side_effect = requests.HTTPError(response=r)
    return r


def produto(**campos):
    return {"product_id": "MLB4771805087", "final_price": 1519.05,
            "currency": "BRL", "in_stock": True, **campos}


def test_fluxo_cadastro_coleta_persistencia_e_rodizio(banco):
    peca = criar_peca()
    with patch(f"{HTTP}.post", return_value=resposta(dados=[produto()])) as post:
        resumo = AtualizarPrecosService().executar()
        assert resumo["atualizadas"] == 1
        db.session.expire_all()
        assert db.session.get(PlacaVideo, peca.id).preco == 1519.05
        assert peca.preco_atualizado_em is not None
        assert not peca.esgotado
        assert AtualizarPrecosService().executar()["consultas"] == 0
        post.assert_called_once()
        assert post.call_args.kwargs["json"]["input"][0]["url"] == "https://produto.mercadolivre.com.br/MLB-4771805087-_JM"
    assert ConsultaPreco.query.one().status == "concluida"


@pytest.mark.parametrize("alteracao", [
    {"final_price": None}, {"final_price": "NaN"}, {"final_price": -1},
    {"product_id": "MLB64959148"}, {"currency": "USD"}, {"in_stock": None},
    {"error": "failed"},
])
def test_falha_preserva_preco_anterior(banco, alteracao):
    peca = criar_peca()
    peca.preco = 123
    db.session.commit()
    with patch(f"{HTTP}.post", return_value=resposta(dados=[produto(**alteracao)])):
        assert AtualizarPrecosService().executar()["falhas"] == 1
    assert peca.preco == 123
    assert peca.preco_atualizado_em is None


def test_esgotado_e_reposicao(banco):
    peca = criar_peca()
    peca.preco = 100
    db.session.commit()
    with patch(f"{HTTP}.post", return_value=resposta(dados=[produto(in_stock=False, final_price=None)])):
        AtualizarPrecosService().executar()
    assert peca.esgotado and peca.preco == 100
    consulta = ConsultaPreco.query.one()
    consulta.dia = (datetime.now().date() - timedelta(days=6)).isoformat()
    db.session.commit()
    with patch(f"{HTTP}.post", return_value=resposta(dados=[produto()])):
        AtualizarPrecosService().executar()
    assert not peca.esgotado and peca.preco == 1519.05


def test_202_retoma_sem_nova_coleta(banco):
    peca = criar_peca()
    with patch(f"{HTTP}.post", return_value=resposta(202, {"snapshot_id": "sd_teste"})) as post:
        assert AtualizarPrecosService().executar()["pendentes"] == 1
        with patch(f"{HTTP}.get", side_effect=[
            resposta(dados={"status": "ready"}), resposta(dados=[produto()]),
        ]):
            assert AtualizarPrecosService().executar()["atualizadas"] == 1
        assert post.call_count == 1
    assert ConsultaPreco.query.count() == 1
    assert peca.preco == 1519.05


@pytest.mark.parametrize("status", [401, 402, 403, 429, 500])
def test_erro_global_interrompe_lote(banco, status):
    criar_peca()
    criar_peca("https://produto.mercadolivre.com.br/MLB-1234567890-produto-_JM")
    with patch(f"{HTTP}.post", return_value=resposta(status)) as post:
        resumo = AtualizarPrecosService().executar()
    assert post.call_count == 1
    assert resumo["falhas"] == 1


def test_timeout_nao_repete_post(banco):
    criar_peca()
    with patch(f"{HTTP}.post", side_effect=requests.Timeout) as post:
        AtualizarPrecosService().executar()
        AtualizarPrecosService().executar()
    assert post.call_count == 1
    assert ConsultaPreco.query.one().status == "incerta"


def test_limites_persistidos_e_virada_do_mes(banco):
    peca = criar_peca()
    agora = datetime(2026, 10, 5, tzinfo=timezone.utc)
    with patch.object(ReservarConsultaService, "LIMITE_DIARIO", 1), patch.object(ReservarConsultaService, "LIMITE_MENSAL", 1):
        assert ReservarConsultaService().executar(PlacaVideo, peca, agora)
        assert ReservarConsultaService().executar(PlacaVideo, peca, agora) is None
        assert ReservarConsultaService().executar(PlacaVideo, peca, agora + timedelta(days=6)) is None
        assert ReservarConsultaService().executar(PlacaVideo, peca, agora.replace(month=11))


def test_prioriza_nunca_consultadas(banco):
    primeira = criar_peca()
    outra = criar_peca("https://produto.mercadolivre.com.br/MLB-1234567890-produto-_JM")
    ReservarConsultaService().executar(PlacaVideo, primeira, datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert AtualizarPrecosService()._selecionar_pecas()[0][1].id == outra.id


def test_seed_idempotente_sem_links_inventados(banco):
    PopularPecasService().executar()
    peca = PlacaVideo.query.first()
    SalvarPecaService().executar(PlacaVideo, {"meli_external": URL}, peca.id)
    peca.preco = 123
    db.session.commit()
    quantidade = PlacaVideo.query.count()
    PopularPecasService().executar()
    assert PlacaVideo.query.count() == quantidade
    assert peca.meli_external == URL and peca.preco == 123
    assert peca.kabum_external is None


def test_migracao_preserva_dados_e_pode_repetir(banco):
    peca = criar_peca(None)
    with db.engine.begin() as con:
        con.execute(text('ALTER TABLE placa_video ADD COLUMN link TEXT'))
        con.execute(text('UPDATE placa_video SET link = :url'), {"url": "https://www.kabum.com.br/produto/123/placa"})
    MigrarLinksService().executar()
    MigrarLinksService().executar()
    db.session.expire_all()
    assert peca.kabum_external == "https://www.kabum.com.br/produto/123/placa"
    assert "link" not in {c["name"] for c in inspect(db.engine).get_columns("placa_video")}


def test_troca_de_link_invalida_preco_e_ignora_snapshot_antigo(banco):
    peca = criar_peca()
    with patch(f"{HTTP}.post", return_value=resposta(202, {"snapshot_id": "sd_teste"})):
        AtualizarPrecosService().executar()
    SalvarPecaService().executar(PlacaVideo, {"meli_external": None}, peca.id)
    with patch(f"{HTTP}.get") as get:
        AtualizarPrecosService().executar()
        get.assert_not_called()
    assert ConsultaPreco.query.one().status == "ignorada"


def test_kabum_nao_faz_rede(banco):
    peca = criar_peca(None)
    SalvarPecaService().executar(PlacaVideo, {"kabum_external": "https://www.kabum.com.br/produto/123/placa"}, peca.id)
    with patch(f"{HTTP}.post") as post:
        assert AtualizarPrecosService().executar()["consultas"] == 0
        post.assert_not_called()
