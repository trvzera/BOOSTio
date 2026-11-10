from services.catalogo_service.gravar_especificacoes_peca_service import preencher_especificacoes
from dataclasses import replace, asdict
from datetime import datetime
import pytest
from flask import Flask
from models import db, MemoriaRAM, ProdutoPendente, Oferta
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.enriquecer_peca_existente_service import EnriquecerPecaExistenteService
from services.catalogo_service.preencher_especificacoes_service import PreencherEspecificacoesService
from services.catalogo_service.associacao_inteligente_service import AssociacaoInteligenteService
from services.catalogo_service.conferir_especificacoes_service import converter


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def memoria(**dados):
    p = MemoriaRAM(**{**dict(fabricante='Crucial', modelo='8GB 3200MHz DDR4 CL22 - CT8G4DFRA32A',
        capacidade_gb=8, frequencia_mhz=3200, ddr='DDR4', quantidade_pentes=1, latencia='CL22',
        formato=None, consumo_energia=5, preco=123, part_number=None, referencia_interna='KABUM-392498'), **dados})
    db.session.add(p)
    db.session.commit()
    return p


def produto(**dados):
    return replace(ProdutoNormalizado(loja='outra_loja', id_externo='memoria-1', categoria='memoria_ram',
        categoria_confirmada=True, titulo='Crucial CT8G4DFRA32A 8GB DDR4 3200MHz CL22', modelo='CT8G4DFRA32A',
        marca='Crucial', ativo=True, fonte='https://loja.example/produto/1',
        especificacoes=dict(capacidade_gb='8 GB', frequencia_mhz='3200 MHz', ddr='DDR4',
                            quantidade_pentes=1, latencia=22, formato_ram='UDIMM')), **dados)


def test_preenche_codigo_literal_e_formato_sem_tocar_preco_e_idempotente(banco):
    p = memoria()
    s = EnriquecerPecaExistenteService()
    r = s.executar(p, produto())
    assert r['dados'] == dict(formato='DIMM', part_number='CT8G4DFRA32A')
    assert p.formato is p.part_number is p.fontes_especificacoes is None
    assert s.executar(p, produto(), simular=False)['status'] == 'atualizada'
    assert p.formato == 'DIMM' and p.part_number == 'CT8G4DFRA32A'
    assert p.preco == 123 and p.referencia_interna == 'KABUM-392498'
    assert p.fontes_especificacoes['formato']['valor_original'] == ['UDIMM']
    assert p.fontes_especificacoes['formato']['url'] == produto().fonte
    assert s.executar(p, produto(), simular=False)['status'] == 'inalterada'
    assert Oferta.query.filter(Oferta.loja != 'kabum').count() == 0


@pytest.mark.parametrize('dados', [
    dict(modelo='CT8G4DFRA32B', titulo='Crucial CT8G4DFRA32B'),
    dict(marca='Kingston'), dict(ativo=False), dict(categoria_confirmada=False),
    dict(fonte='http://loja.example/1'), dict(titulo='Crucial CT8G4DFRA32A RGB'),
    dict(especificacoes={'capacidade_gb':'16 GB', 'formato_ram':'DIMM'}),
    dict(identificadores={'mpn':['CT8G4DFRA32A', 'CT8G4DFRA32B']}),
])
def test_nao_enriquece_com_evidencia_insuficiente_ou_contraditoria(banco, dados):
    p = memoria()
    assert EnriquecerPecaExistenteService().executar(p, produto(**dados), simular=False)['status'] != 'atualizada'
    assert p.formato is p.part_number is p.fontes_especificacoes is None


def test_lote_ambiguo_nao_escolhe_primeira_peca(banco):
    memoria(); memoria()
    dto = produto()
    db.session.add(ProdutoPendente(loja=dto.loja, produto_id_loja='1', titulo=dto.titulo,
        url=dto.fonte, categoria_sugerida=dto.categoria, dados_originais={'normalizado':asdict(dto)},
        coletado_em=datetime(2026,11,4)))
    db.session.commit()
    r = PreencherEspecificacoesService().executar(simular=False)
    assert r['revisao'] == 1 and r['atualizadas'] == r['falhas'] == 0
    assert all(p.formato is None for p in MemoriaRAM.query.all())


def test_gtin_invalido_nao_vira_prova_nem_apaga_conflitos(banco):
    p = memoria(formato='DIMM')
    s = AssociacaoInteligenteService()
    r = s.avaliar(p, produto(identificadores={'gtin':['invalido']}))
    assert r['classificacao'] == 'confirmada'
    assert 'gtin_remoto_invalido' in r['avisos'] and 'gtin' not in r['evidencias']
    r = s.avaliar(p, produto(especificacoes={'capacidade_gb':'16 GB'}, identificadores={'gtin':['invalido']}))
    assert r['classificacao'] == 'rejeitada'


@pytest.mark.parametrize('campo,entrada,esperado', [
    ('formato_ram','UDIMM','dimm'), ('formato_ram','SO-DIMM','sodimm'),
    ('tamanho_mm','12 cm',120), ('comprimento_m','200 cm',2),
    ('resolucao','1920px x 1080px','1920x1080'), ('microfone','Não',False),
    ('conexao','USB, Bluetooth','bluetooth|usb'), ('conexao','bluetooth|usb','bluetooth|usb'),
])
def test_conversoes_explicitas(campo, entrada, esperado):
    assert converter(campo, entrada) == esperado


def test_concorrencia_bloqueia_proposta_antiga_e_campos_protegidos(banco):
    from utils.identidade_peca import assinatura_peca
    p = memoria()
    proposta = EnriquecerPecaExistenteService().preparar(p, produto())
    assinatura = assinatura_peca(p)
    p.frequencia_mhz = 2666
    db.session.commit()
    with pytest.raises(ValueError, match='mudou'):
        preencher_especificacoes(p, proposta, assinatura, simular=False)
    assert p.formato is p.part_number is None
    p.frequencia_mhz = 3200
    db.session.commit()
    proposta = EnriquecerPecaExistenteService().preparar(p, produto())
    proposta['dados']['preco'] = 1
    with pytest.raises(ValueError, match='protegido'):
        preencher_especificacoes(p, proposta, assinatura_peca(p), simular=False)
    assert p.preco == 123 and p.formato is None


def test_codigo_completo_nao_iguala_sufixos_e_nao_basta_sem_ficha(banco):
    p = memoria()
    s = EnriquecerPecaExistenteService()
    assert s.preparar(p, produto(modelo='CT8G4DFRA32A-US', titulo='Crucial CT8G4DFRA32A-US'))['status'] != 'proposta'
    assert s.preparar(p, produto(titulo='Crucial CT8G4DFRA32A', especificacoes={'formato_ram':'DIMM'}))['status'] != 'proposta'


def test_normalizador_prefere_gtins_individuais_sem_concatenar():
    from services.mercadolivre_service.normalizar_produto_service import NormalizarProdutoService
    p = NormalizarProdutoService().executar({'id':'MLB123','attributes':[
        {'id':'GTIN','value_name':'123, 456','values':[{'name':'123'},{'name':'456'}]}]}, 'memoria_ram')
    assert p.identificadores['gtin'] == ['123','456']


def test_nao_preenche_lacuna_quando_titulo_contradiz_ficha(banco):
    p = memoria()
    r = EnriquecerPecaExistenteService().preparar(p, produto(titulo='Crucial CT8G4DFRA32A SO-DIMM 8GB DDR4 3200MHz CL22'))
    assert r['status'] == 'revisao' and 'Título diverge' in r['motivo']
