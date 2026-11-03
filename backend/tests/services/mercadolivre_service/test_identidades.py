import json
from types import SimpleNamespace

import pytest
from flask import Flask
from models import db, MemoriaRAM, IdentidadeFabricante
from migrations.identidades_fabricante import preparar_identidades_fabricante
from services.mercadolivre_service.importar_identidades_service import ImportarIdentidadesService
from services.mercadolivre_service.associar_catalogo_service import AssociarCatalogoService


@pytest.fixture
def contexto(tmp_path):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        MemoriaRAM.__table__.create(db.engine)
        assert preparar_identidades_fabricante()['criadas'] == ['identidade_fabricante']
        assert preparar_identidades_fabricante()['criadas'] == []
        p = MemoriaRAM(fabricante='Kingston', modelo='Fury Beast 8GB', part_number='SEED-RAM-01',
                      preco=100, consumo_energia=5, capacidade_gb=8, ddr='DDR4', frequencia_mhz=3200, quantidade_pentes=1,
                      kabum_external='https://www.kabum.com.br/produto/172365/teste')
        db.session.add(p); db.session.commit()
        manifesto = [dict(categoria='memoria_ram', referencia=p.part_number, fabricante=p.fabricante,
                         modelo=p.modelo, mpn='KF432C16BB/8', fonte='https://www.kingston.com/datasheets/kf432c16bb_8.pdf',
                         url_peca=p.kabum_external, especificacoes=dict(capacidade_gb=8, ddr='DDR4', quantidade_pentes=1, iluminacao=0))]
        arquivo = tmp_path / 'revisadas.json'
        arquivo.write_text(json.dumps(manifesto))
        yield p, arquivo, manifesto
        db.session.remove(); db.engine.dispose()


def test_simulacao_importacao_idempotencia_e_associacao(contexto):
    p, arquivo, _ = contexto
    service = ImportarIdentidadesService()
    assert service.executar(arquivo)['propostas'] == 1
    assert IdentidadeFabricante.query.count() == 0
    assert service.executar(arquivo, simular=False)['cadastradas'] == 1
    assert service.executar(arquivo, simular=False)['inalteradas'] == 1
    assert p.part_number == 'SEED-RAM-01' and MemoriaRAM.query.count() == 1
    assert AssociarCatalogoService._mpn(p) == 'KF432C16BB/8'
    produto = dict(status='active', attributes=[dict(id='BRAND', value_name='Kingston'),
                    dict(id='MPN', value_name='KF432C16BB/8')])
    assert AssociarCatalogoService.comprova_mpn(p, produto)
    produto['attributes'][1]['value_name'] = 'KF432C16BB/16'
    assert not AssociarCatalogoService.comprova_mpn(p, produto)
    p.ddr = 'DDR5'; db.session.commit()
    assert IdentidadeFabricante.buscar(p) is None


@pytest.mark.parametrize('mudanca', ['ddr', 'link', 'duplicada', 'ausente'])
def test_divergencias_nao_cadastram(contexto, mudanca):
    p, arquivo, dados = contexto
    if mudanca == 'ddr': dados[0]['especificacoes']['ddr'] = 'DDR5'
    if mudanca == 'link': dados[0]['url_peca'] = 'https://www.kabum.com.br/produto/999/outro'
    if mudanca == 'ausente': dados[0]['referencia'] = 'SEED-RAM-99'
    if mudanca == 'duplicada': dados.append(dados[0])
    arquivo.write_text(json.dumps(dados))
    if mudanca == 'duplicada':
        with pytest.raises(ValueError, match='duplicada'):
            ImportarIdentidadesService().executar(arquivo, simular=False)
    else:
        assert ImportarIdentidadesService().executar(arquivo, simular=False)['revisao'] == 1
    assert IdentidadeFabricante.query.count() == 0


def test_codigos_internos_nao_sao_mpn():
    for codigo in ['SEED-RAM-1', 'REDE-WIFI-01', 'DEMO-1', 'BOOSTIO-1']:
        assert AssociarCatalogoService._mpn(SimpleNamespace(part_number=codigo)) is None
