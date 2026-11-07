import time
from decimal import Decimal

import pytest
from flask import Flask

from models import db, Processador, ControleColeta, Oferta, HistoricoOferta, ProdutoPendente
from services.shopee_service.normalizar_produto_service import NormalizarProdutoShopeeService, limpar_titulo
from services.shopee_service.processar_ofertas_service import ProcessarOfertasShopeeService

AGORA = int(time.time())


def anuncio(item, shop, titulo, preco='1000.00', maximo=None, categorias=(101950,)):
    return dict(itemId=str(item), shopId=str(shop), productName=titulo, priceMin=preco, priceMax=maximo or preco,
                productLink=f'https://shopee.com.br/product/{shop}/{item}', offerLink=None,
                productCatIds=list(categorias), periodStartTime=AGORA - 3600, periodEndTime=AGORA + 3600)


class ClienteFalso:
    """Devolve páginas prontas por texto de busca e registra o que foi pedido."""
    def __init__(self, paginas):
        self.paginas, self.pedidos = paginas, []

    def buscar(self, termo, *, pagina=1, limite=20):
        self.pedidos.append((termo, pagina))
        nos, proxima = self.paginas.get((termo, pagina), ([], False))
        return dict(nodes=nos, pageInfo=dict(page=pagina, limit=limite, hasNextPage=proxima))


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        ControleColeta.inicializar()
        p5500 = Processador(fabricante='AMD', modelo='Ryzen 5 5500', part_number='100-100000457BOX', soquete='AM4',
                            nucleo=6, thread=12, clockbase=3.6, clockmax=4.2, consumo_energia=65, status_validacao='aprovado')
        p5600 = Processador(fabricante='AMD', modelo='Ryzen 5 5600', part_number='100-100000927BOX', soquete='AM4',
                            nucleo=6, thread=12, clockbase=3.5, clockmax=4.4, consumo_energia=65, status_validacao='aprovado')
        db.session.add_all([p5500, p5600])
        db.session.commit()
        yield p5500, p5600
        db.session.remove()
        db.engine.dispose()


CPU = 'Processador AMD Ryzen 5 5500 AM4 6 Núcleos 12 Threads'


def servico(*paginas_por_consulta):
    return ProcessarOfertasShopeeService(ClienteFalso(dict(paginas_por_consulta)))


def consultas(p):
    from services.catalogo_service.consultas_peca_service import consultas_da_peca
    return consultas_da_peca(p)


def rodar(servico_, p, **kw):
    return servico_.ofertas_peca(categoria='processador', peca_id=p.id, **kw)


def test_limpa_propaganda_sem_tocar_no_modelo():
    assert limpar_titulo('🔥 Processador AMD Ryzen 5 5500 | FRETE GRÁTIS | Original Lacrado | Garantia 12 meses') == \
        'Processador AMD Ryzen 5 5500'
    assert limpar_titulo('SSD NVMe 500GB 3500MB/s') == 'SSD NVMe 500GB 3500MB/s'


def test_associa_menor_preco_de_cada_loja_e_grava_oferta(banco):
    p5500, _ = banco
    consulta = consultas(p5500)[0]
    s = servico((
        (consulta, 1), ([anuncio(1, 10, '🔥 ' + CPU + ' Frete Grátis', '900.00'),
                          anuncio(2, 10, CPU, '800.00'),
                          anuncio(3, 11, CPU + ' Original', '850.00')], False)))
    r = rodar(s, p5500, simular=False, limite_ofertas=2)
    assert r['associadas'] == 2 and r['peca'] == f'processador:{p5500.id}'
    ofertas = {o.produto_id_loja: o for o in Oferta.query.filter_by(loja='shopee')}
    assert set(ofertas) == {'10:2', '11:3'}  # um anúncio por loja: o mais barato
    assert ofertas['10:2'].preco == Decimal('800.00') and ofertas['10:2'].ativa
    assert HistoricoOferta.query.count() == 2
    assert all(pend.status == 'importado' for pend in ProdutoPendente.query.all())
    db.session.refresh(p5500)
    assert p5500.preco == 800  # o menor preço entre as ofertas passa a ser o da peça


def test_simulacao_nao_grava_nada(banco):
    p5500, _ = banco
    s = servico(((consultas(p5500)[0], 1), ([anuncio(1, 10, CPU)], False)))
    r = rodar(s, p5500, simular=True)
    assert r['associadas'] == 1 and Oferta.query.count() == 0 and ProdutoPendente.query.count() == 0


def test_anuncio_de_outra_peca_ou_usado_ou_faixa_de_variantes_nao_associa(banco):
    p5500, _ = banco
    s = servico(((consultas(p5500)[0], 1), ([
        anuncio(1, 10, 'Processador AMD Ryzen 5 5600 AM4 6 Núcleos 12 Threads'),
        anuncio(2, 11, CPU + ' USADO'),
        anuncio(3, 12, CPU, '800.00', maximo='1200.00'),
        anuncio(4, 13, CPU, categorias=(999,))], False)))
    r = rodar(s, p5500, simular=False)
    assert r['associadas'] == 0 and r['revisao'] == 4 and Oferta.query.count() == 0


def test_titulo_ambiguo_entre_duas_pecas_nao_associa(banco):
    p5500, _ = banco
    s = servico(((consultas(p5500)[0], 1), ([anuncio(1, 10, 'Processador AMD Ryzen 5 AM4 6 Núcleos 12 Threads')], False)))
    assert rodar(s, p5500, simular=False)['associadas'] == 0 and Oferta.query.count() == 0


def test_busca_por_mpn_antes_do_nome_e_cai_para_a_proxima_consulta(banco):
    p5500, _ = banco
    q = consultas(p5500)
    assert q[0] == '100-100000457BOX' and len(q) >= 2
    cliente = ClienteFalso({(q[1], 1): ([anuncio(1, 10, CPU)], False)})
    r = ProcessarOfertasShopeeService(cliente).ofertas_peca(categoria='processador', peca_id=p5500.id, simular=False)
    assert [c[0] for c in cliente.pedidos][:2] == q[:2]
    assert r['associadas'] == 1


def test_paginacao_limitada_a_quatro_buscas_e_sem_repetir_anuncio(banco):
    p5500, _ = banco
    q = consultas(p5500)
    lixo = [anuncio(i, 50 + i, 'Cabo HDMI 2m') for i in range(20)]
    paginas = {(c, n): (lixo if n == 1 else [anuncio(100 * n + i, 60 + i, 'Cabo HDMI 2m') for i in range(20)], True)
               for c in q for n in range(1, 6)}
    cliente = ClienteFalso(paginas)
    r = ProcessarOfertasShopeeService(cliente).ofertas_peca(categoria='processador', peca_id=p5500.id, simular=True)
    assert len(cliente.pedidos) == 4 and r['associadas'] == 0 and r['busca_completa'] is False


def test_desativa_ofertas_ausentes_somente_com_busca_completa(banco):
    p5500, _ = banco
    q = consultas(p5500)[0]
    rodar(servico(((q, 1), ([anuncio(1, 10, CPU, '900.00')], False))), p5500, simular=False)
    # busca completa sem o anúncio antigo: o novo menor preço entra e o antigo é desativado
    r = rodar(servico(((q, 1), ([anuncio(2, 11, CPU, '800.00')], False))), p5500, simular=False)
    antigo = Oferta.query.filter_by(produto_id_loja='10:1').one()
    assert antigo.ativa is False and any(d['acao'] == 'desativada' for d in r['detalhes'])
    # busca incompleta (há mais páginas): nada é desativado
    rodar(servico(((q, 1), ([anuncio(3, 12, CPU, '700.00')], True))), p5500, simular=False)
    assert Oferta.query.filter_by(produto_id_loja='11:2').one().ativa is True


def test_peca_nao_aprovada_ou_filtro_invalido(banco):
    p5500, _ = banco
    p5500.status_validacao = 'pendente'
    db.session.commit()
    with pytest.raises(ValueError):
        rodar(servico(), p5500)
    with pytest.raises(ValueError):
        servico().ofertas_peca(categoria='inexistente', peca_id=1)
    with pytest.raises(ValueError):
        servico().ofertas_peca(categoria='processador', peca_id=1, limite_ofertas=0)


def test_normalizador_exige_link_coerente_e_preco_valido():
    n = NormalizarProdutoShopeeService()
    ruim = anuncio(1, 10, CPU)
    ruim['productLink'] = 'https://shopee.com.br/product/10/999'
    with pytest.raises(ValueError):
        n.executar(ruim, 'processador')
    ruim = anuncio(1, 10, CPU, preco='0')
    with pytest.raises(ValueError):
        n.executar(ruim, 'processador')
    produto, oferta = n.executar(anuncio(1, 10, '🔥 ' + CPU), 'processador')
    assert produto.titulo == CPU and produto.contexto['titulo_original'].startswith('🔥')
    assert oferta['vendedor_id'] == '10' and oferta['produto_id_loja'] == '10:1' and oferta['esgotado'] is None
