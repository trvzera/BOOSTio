from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from flask import Flask
from sqlalchemy.exc import OperationalError
from models import db, ProdutoPendente, Oferta, ExecucaoDescoberta, Processador
from services.mercadolivre_service.descobrir_produtos_service import DescobrirProdutosService
from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from services.mercadolivre_service.controle_requisicoes_service import ControleRequisicoesService, ErroMercadoLivre


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def pagina(linhas, total=None, offset=0):
    return dict(results=linhas, paging=dict(total=len(linhas) if total is None else total, offset=offset))


def anuncio(numero=1):
    return dict(item_id=f'MLB{numero}', seller_id=7, site_id='MLB', currency_id='BRL',
                price=Decimal('199.90'), condition='new')


def service(respostas, limite=30):
    controle = ControleRequisicoesService(limite, 0.1, dormir=lambda _: None)
    cliente = BuscarOfertasMercadoLivreService(controle)
    cliente._requisitar = Mock(side_effect=respostas)
    tokens = Mock()
    tokens.executar.return_value = 'segredo-nao-exibir'
    return DescobrirProdutosService(cliente, controle, tokens), cliente


def executar(s, **extras):
    return s.executar(**dict(categoria='memoria_ram', consulta='Kingston DDR4', **extras))


def catalogo(ofertas=None):
    return [pagina([dict(id='MLB20', name='Kingston DDR4')]), pagina(ofertas or [anuncio()])]


def test_simulacao_nao_grava_e_aplicacao_e_repeticao_nao_duplicam(banco):
    s, _ = service(catalogo())
    r = executar(s)
    assert r['novos'] == 1 and r['requisicoes'] == 2
    assert ProdutoPendente.query.count() == ExecucaoDescoberta.query.count() == 0
    for esperado in ('novos', 'ja_coletados'):
        s, cliente = service(catalogo())
        r = executar(s, simular=False)
        assert r[esperado] == 1 and not r['interrompido']
        assert cliente._requisitar.call_args_list[0].args[0] == '/products/search'
    p = ProdutoPendente.query.one()
    assert p.status == 'pendente' and p.vendedor_id == '7'
    assert p.dados_originais['anuncio']['price'] == '199.90'
    assert Oferta.query.count() == Processador.query.count() == 0
    assert ExecucaoDescoberta.query.count() == 2
    assert ExecucaoDescoberta.query.first().status == 'concluida'


def test_nao_reabre_rejeitado_nem_modifica_oferta_existente(banco):
    s, _ = service(catalogo());executar(s, simular=False)
    p = ProdutoPendente.query.one();p.status = 'rejeitado';p.motivo = 'Revisado'
    db.session.add(Oferta(loja='mercado_livre', produto_id_loja='MLB2', tabela_peca='memoria_ram',
                          peca_id=99, url='https://example.test', preco=100))
    db.session.commit()
    s, _ = service(catalogo([anuncio(), anuncio(2)]))
    r = executar(s, simular=False)
    assert r['ja_coletados'] == r['ja_associados'] == 1
    assert p.status == 'rejeitado' and p.motivo == 'Revisado'
    assert Oferta.query.one().preco == 100


def test_busca_direta_categoria_palavras_paginacao_e_deduplicacao(banco):
    a = {**anuncio(), 'id':'MLB1', 'title':'RAM Kingston', 'seller':{'id':7}}
    s, cliente = service([pagina([a], 2), pagina([a], 2, 1)])
    r = executar(s, origem='anuncios', categoria_ml='MLB123', simular=False)
    assert r['novos'] == r['repetidos'] == 1
    assert cliente._requisitar.call_args_list[1].args[2] == dict(q='Kingston DDR4', category='MLB123', offset=1, limit=50)
    assert ProdutoPendente.query.one().titulo == 'RAM Kingston'


@pytest.mark.parametrize('status', [401, 403, 429, 500])
def test_falhas_http_registradas_sem_credenciais_e_sem_fallback(banco, status):
    s, cliente = service([ErroMercadoLivre(status)] * 3)
    r = executar(s, origem='anuncios', simular=False)
    assert r['interrompido'] and str(status) in r['falhas'][0]
    assert cliente._requisitar.call_count == (3 if status == 429 else 1)
    assert ProdutoPendente.query.count() == 0
    registro = ExecucaoDescoberta.query.one()
    assert registro.status == 'interrompida'
    assert 'segredo' not in str(registro.resumo) + str(registro.parametros)


@pytest.mark.parametrize('dados', [dict(results=[], paging={'total':2,'offset':0}),
    dict(results=[], paging={'total':True,'offset':0}), dict(results=[], paging={'total':0,'offset':99})])
def test_paginacao_invalida_interrompe_sem_gravar(banco, dados):
    s, _ = service([dados]);r = executar(s)
    assert r['interrompido'] and r['novos'] == 0


def test_linha_invalida_nao_impede_demais_e_limite_de_anuncios(banco):
    s, _ = service(catalogo([{'item_id':'errado'}, anuncio(), anuncio(2)]))
    r = executar(s, max_anuncios=2, simular=False)
    assert r['invalidos'] == r['novos'] == 1 and r['limitado']
    assert not r['interrompido']


def test_limites_de_paginas_e_requisicoes(banco):
    s, cliente = service(catalogo())
    r = executar(s, max_paginas=1)
    assert r['limitado'] and not r['interrompido'] and cliente._requisitar.call_count == 1
    s, _ = service(catalogo(), limite=1)
    r = executar(s)
    assert r['interrompido'] and r['requisicoes'] == 1


def test_transacao_por_pagina_preserva_lote_anterior(banco):
    s, _ = service([pagina([dict(id='MLB20', name='Kingston')]),
                    pagina([anuncio()], 2), pagina([anuncio(2)], 2, 1)])
    original = ProdutoPendente.registrar_descobertos
    def gravar(linhas, **args):
        if linhas[0]['produto_id_loja'] == 'MLB2':
            raise OperationalError('dados-sensiveis', {}, None)
        return original(linhas, **args)
    with patch.object(ProdutoPendente, 'registrar_descobertos', side_effect=gravar):
        r = executar(s, simular=False)
    assert r['interrompido'] and r['novos'] == 1
    assert ProdutoPendente.query.count() == 1
    assert 'dados-sensiveis' not in str(r)


@pytest.mark.parametrize('extras', [dict(categoria='inventada'), dict(consulta=''), dict(max_paginas=True),
    dict(max_anuncios=0), dict(categoria_ml='MLB123'), dict(origem='anuncios', dominio='MLB-RAM')])
def test_opcoes_invalidas_antes_de_chamar_api(banco, extras):
    s, cliente = service([])
    with pytest.raises(ValueError):
        s.executar(**{**dict(categoria='memoria_ram',consulta='DDR4'), **extras})
    assert not cliente._requisitar.called


def test_comando_simula_por_padrao(banco):
    from commands.mercadolivre import registrar_comandos_mercadolivre
    registrar_comandos_mercadolivre(banco)
    with patch.object(DescobrirProdutosService, 'executar', return_value={'interrompido':False}) as chamada:
        resultado = banco.test_cli_runner().invoke(args=['mercadolivre-descobrir','--categoria','memoria_ram','--consulta','Kingston DDR4'])
    assert resultado.exit_code == 0
    assert chamada.call_args.kwargs['simular'] is True


def test_falha_no_segundo_registro_reverte_pagina_inteira(banco):
    from sqlalchemy.exc import IntegrityError
    from datetime import datetime
    dados = dict(loja='mercado_livre', produto_id_loja='MLB1', vendedor_id='7', titulo='RAM',
                 url='https://example.test', dados_originais={}, coletado_em=datetime(2026,11,3))
    with pytest.raises(IntegrityError):
        ProdutoPendente.registrar_descobertos([dados, {**dados, 'produto_id_loja':'MLB2', 'titulo':None}], simular=False)
    assert ProdutoPendente.query.count() == 0


def test_limite_exato_nao_consulta_pagina_extra(banco):
    s, cliente = service(catalogo([anuncio()]))
    r = executar(s, max_anuncios=1)
    assert r['novos'] == 1 and r['limitado']
    assert cliente._requisitar.call_count == 2


def test_checkpoint_catalogo_retoma_proximo_produto_sem_repetir_busca(banco):
    s, _ = service([pagina([dict(id='MLB20',name='RAM A'),dict(id='MLB21',name='RAM B')]),pagina([anuncio()])])
    primeiro=executar(s,max_paginas=2,simular=False)
    assert primeiro['limitado'] and primeiro['cursor']['indice']==1
    s, cliente=service([pagina([anuncio(2)])])
    segundo=executar(s,cursor=primeiro['cursor'],simular=False)
    assert segundo['concluido'] and segundo['novos']==1
    assert cliente._requisitar.call_args.args[0]=='/products/MLB21/items'
    assert ProdutoPendente.query.count()==2


def test_checkpoint_dentro_da_pagina_e_nao_avanca_em_falha_de_gravacao(banco):
    s,_=service(catalogo([anuncio(),anuncio(2)]))
    r=executar(s,max_anuncios=1,simular=False)
    assert r['cursor']['ofertas_offset']==1 and not r['concluido']
    s,c=service([pagina([anuncio(2)],2,1)])
    r2=executar(s,cursor=r['cursor'],simular=False)
    assert r2['concluido'] and r2['novos']==1
    assert c._requisitar.call_args.args[2]['offset']==1
    s,_=service(catalogo())
    with patch.object(ProdutoPendente,'registrar_descobertos',side_effect=OperationalError('falha',{},None)):
        erro=executar(s)
    assert erro['interrompido'] and erro['cursor']['ofertas_offset']==0
