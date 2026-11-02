from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy.exc import IntegrityError
from models import db, ConsultaPreco, HistoricoPreco


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    with app.app_context():
        ConsultaPreco.__table__.create(db.engine)
        HistoricoPreco.__table__.create(db.engine)
        yield
        db.session.remove()
        db.engine.dispose()


def registrar(preco, esgotado=False, consulta=None):
    consulta = consulta or ConsultaPreco(tabela_peca="placa_video", peca_id=1,
        url="https://www.kabum.com.br/produto/123", dia="2026-11-02", status="concluida")
    db.session.add(consulta)
    db.session.flush()
    linha = HistoricoPreco(consulta_id=consulta.id, tabela_peca="placa_video", peca_id=1,
        loja="kabum", produto_id_loja="123", url=consulta.url, preco=preco, esgotado=esgotado)
    db.session.add(linha)
    db.session.commit()
    return linha


def test_guarda_cotacoes_iguais_em_consultas_diferentes_sem_sobrescrever(banco):
    primeira = registrar(Decimal("999.90"))
    segunda = registrar(Decimal("999.90"))
    registrar(Decimal("899.99"))
    assert primeira.id != segunda.id
    assert primeira.preco == Decimal("999.90")
    assert HistoricoPreco.query.count() == 3
    assert primeira.coletado_em is not None


def test_impede_duplicar_a_mesma_consulta(banco):
    original = registrar(Decimal("999.90"))
    consulta = db.session.get(ConsultaPreco, original.consulta_id)
    with pytest.raises(IntegrityError):
        registrar(Decimal("800.00"), consulta=consulta)
    db.session.rollback()
    assert HistoricoPreco.query.count() == 1
    assert HistoricoPreco.query.one().preco == Decimal("999.90")


@pytest.mark.parametrize("preco,esgotado", [(None, False), (Decimal("0"), False), (Decimal("-1"), True)])
def test_rejeita_preco_zero_negativo_ou_ausente_quando_disponivel(banco, preco, esgotado):
    with pytest.raises(IntegrityError):
        registrar(preco, esgotado)
    db.session.rollback()
    assert HistoricoPreco.query.count() == 0


def test_indisponibilidade_nao_vira_preco_zero(banco):
    observacao = registrar(None, esgotado=True)
    assert observacao.preco is None and observacao.esgotado is True
