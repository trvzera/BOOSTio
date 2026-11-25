import sqlite3

import pytest
from flask import Flask

from models import db, PlacaMae, IdentidadeFabricante
from services.catalogo_service.identidades_para_matching_service import IdentidadesParaMatchingService
from services.icecat_service.descobrir_codigos_icecat_service import DescobrirCodigosIcecatService, chave_do_modelo


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.engine.dispose()


def indice(tmp_path, *linhas):
    caminho = tmp_path / 'indice.db'
    with sqlite3.connect(caminho) as b:
        b.execute('CREATE TABLE produto (id TEXT, mpn TEXT, modelo TEXT, atualizado TEXT, categoria TEXT)')
        b.executemany('INSERT INTO produto (mpn, modelo, categoria) VALUES (?,?,?)', linhas)
    return caminho


def placa(modelo, fabricante='Asus', **campos):
    p = PlacaMae(fabricante=fabricante, modelo=modelo, socket='AM4', **campos)
    db.session.add(p)
    db.session.commit()
    return p


def test_chave_ignora_cor_pontuacao_e_caixa():
    assert chave_do_modelo('PRIME Z890-P WIFI [Black / Silver]') == chave_do_modelo('prime z890-p wifi') == 'prime z890 p wifi'
    assert chave_do_modelo('PRIME Z890-P') != chave_do_modelo('PRIME Z890-P WIFI')


def test_propoe_codigo_unico_e_separa_o_que_precisa_de_revisao(banco, tmp_path):
    unica = placa('PRIME B550M-A [Black]')
    placa('TUF Z790')
    placa('ROG X')
    repetida_a, repetida_b = placa('PRIME H610M-E [Black]'), placa('PRIME H610M-E [White]')
    placa('PRIME B760M-K', part_number='90MB1DS0-M1EAY0')
    placa('PRIME B550M-A', fabricante='MSI')
    caminho = indice(tmp_path, ('90mb14i0-m0eay0', 'prime b550m-a', '164'), ('90mb0001-m0eay0', 'tuf z790', '164'),
                     ('90mb0001-m1eay0', 'tuf z790', '164'), ('90mb0002-m0eay0', 'prime h610m-e', '164'),
                     ('911-7d76-001', 'rog x', '164'), ('90mb0003-m0eay0', 'rog x', '999'))
    resumo = DescobrirCodigosIcecatService(caminho).executar(categoria='placa_mae', marca='ASUS')
    assert resumo['pecas_da_marca'] == 6
    assert (resumo['propostas'], resumo['varios_codigos'], resumo['codigo_disputado'], resumo['sem_correspondencia'],
            resumo['ja_com_codigo']) == (1, 1, 2, 1, 1)
    assert resumo['detalhes'] == [{'peca_id': unica.id, 'modelo': unica.modelo, 'codigo': '90MB14I0-M0EAY0'}]
    assert {'codigo': '90MB0002-M0EAY0', 'pecas': sorted([repetida_a.id, repetida_b.id])} in resumo['revisao']
    assert PlacaMae.query.filter(PlacaMae.part_number.isnot(None)).count() == 1


def test_recusa_marca_ou_categoria_sem_suporte_e_indice_ausente(banco, tmp_path):
    with pytest.raises(ValueError, match='ASUS'):
        DescobrirCodigosIcecatService(tmp_path / 'x.db').executar(categoria='placa_mae', marca='msi')
    with pytest.raises(ValueError, match='icecat-indice-preparar'):
        DescobrirCodigosIcecatService(tmp_path / 'x.db').executar(categoria='placa_mae', marca='asus')


def test_aplicar_grava_so_codigo_unico_sem_mudar_part_number_e_vale_na_associacao(banco, tmp_path):
    unica = placa('PRIME B550M-A [Black]', status_validacao='aprovado')
    placa('TUF Z790')
    caminho = indice(tmp_path, ('90mb14i0-m0eay0', 'prime b550m-a', '164'), ('90mb0001-m0eay0', 'tuf z790', '164'),
                     ('90mb0001-m1eay0', 'tuf z790', '164'))
    servico = DescobrirCodigosIcecatService(caminho)
    servico.executar(categoria='placa_mae', marca='asus')
    assert IdentidadeFabricante.query.count() == 0
    resumo = servico.executar(categoria='placa_mae', marca='asus', simular=False)
    assert (resumo['gravadas'], resumo['varios_codigos']) == (1, 1)
    registro = IdentidadeFabricante.query.one()
    assert (registro.peca_id, registro.mpn) == (unica.id, '90MB14I0-M0EAY0') and 'Icecat' in registro.fonte
    assert db.session.get(PlacaMae, unica.id).part_number is None
    assert IdentidadesParaMatchingService().executar([unica])[unica.id]['mpn'] == '90MB14I0-M0EAY0'
    de_novo = servico.executar(categoria='placa_mae', marca='asus', simular=False)
    assert (de_novo['gravadas'], de_novo['ja_com_codigo']) == (0, 1)
