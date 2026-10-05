"""Teste opcional: uma coleta real, com gravação somente em SQLite temporário."""
import os

import pytest
from dotenv import load_dotenv
from flask import Flask

from models import db, PlacaVideo, ConsultaPreco
from services.peca_service.migrar_links_service import MigrarLinksService
from services.peca_service.salvar_peca_service import SalvarPecaService
from services.peca_service.atualizar_precos_service import AtualizarPrecosService


@pytest.mark.skipif(os.getenv("BRIGHTDATA_E2E") != "1", reason="Requer opt-in; consome uma coleta real")
def test_preco_real(tmp_path):
    load_dotenv()
    assert os.getenv("BRIGHTDATA_API_KEY"), "Configure BRIGHTDATA_API_KEY"
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + (tmp_path / "precos.db").as_posix()
    db.init_app(app)
    with app.app_context():
        MigrarLinksService().executar()
        peca = SalvarPecaService().executar(PlacaVideo, {
            "fabricante": "Palit", "modelo": "RTX 3050 StormX", "memoria_gb": 6,
            "consumo_energia": 70,
            "meli_external": "https://www.mercadolivre.com.br/placa-de-video-geforce-nvidia-palit-rtx3050-6gb-stormx-gddr6/p/MLB64959148?pdp_filters=item_id:MLB4771805087",
        })
        resumo = AtualizarPrecosService().executar(limite=1)
        # 202 é retomado por GET. Nenhuma nova coleta é iniciada para o mesmo link.
        import time
        for _ in range(6):
            if ConsultaPreco.query.one().status != "pendente":
                break
            time.sleep(10)
            resumo = AtualizarPrecosService().executar(limite=1)
        consulta = ConsultaPreco.query.one()
        assert consulta.status == "concluida", f"{consulta.status}: {consulta.erro}; snapshot={consulta.snapshot_id}"
        db.session.expire_all()
        assert peca.preco > 0 and peca.preco_atualizado_em is not None
        print(f"Anúncio MLB4771805087: R$ {peca.preco:.2f}; persistência no banco temporário confirmada")
        db.session.remove()
