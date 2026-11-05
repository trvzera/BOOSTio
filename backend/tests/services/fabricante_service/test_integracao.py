from datetime import datetime
from unittest.mock import Mock
from flask import Flask
from models import db,ControleColeta,ProdutoPendente,MemoriaRAM,Oferta,HistoricoOferta
from services.fabricante_service.completar_ficha_service import CompletarFichaFabricanteService
from services.mercadolivre_service.importar_produto_service import ImportarProdutoService
from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService


def test_importacao_usa_fabricante_apos_icecat_e_repete_sem_duplicar():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        try:
            db.create_all();ControleColeta.inicializar()
            pendencia=ProdutoPendente(loja='mercado_livre',produto_id_loja='MLB10',vendedor_id='7',
                titulo='Corsair CMW16GX4M2C3200C16',url='https://produto.mercadolivre.com.br/MLB-10-_JM',
                categoria_sugerida='memoria_ram',coletado_em=datetime(2026,11,5),dados_originais={'catalogo':{'id':'MLB99'}})
            db.session.add(pendencia);db.session.commit()
            produto=dict(id='MLB99',name='Corsair CMW16GX4M2C3200C16',status='active',domain_id='MLB-RAM_MEMORY_MODULES',
                attributes=[dict(id=k,value_name=v) for k,v in [('BRAND','Corsair'),('MODEL','CMW16GX4M2C3200C16'),('MPN','CMW16GX4M2C3200C16')]])
            cliente=BuscarOfertasMercadoLivreService();cliente._consultar=Mock(return_value=produto)
            anuncio=cliente._normalizar(dict(item_id='MLB10',seller_id=7,site_id='MLB',currency_id='BRL',price=400,condition='new'),'MLB99')
            cliente.executar=Mock(return_value={'ofertas':[anuncio]})
            tokens=Mock();tokens.executar.return_value='teste'
            paginas=Mock();paginas.regras.return_value.site_maps.return_value=['https://www.corsair.com/us-sitemap.xml']
            pagina='''<script type="application/ld+json">{"@type":"Product","sku":"CMW16GX4M2C3200C16","brand":"Corsair","name":"Vengeance RGB Pro"}</script><table>'''
            for k,v in {'Memory Size':'16GB (2 x 8GB)','Memory Type':'DDR4','Tested Speed':'3200 MHz','Tested Latency':'16','Package Memory Format':'UDIMM'}.items():
                pagina+=f'<tr><th>{k}</th><td>{v}</td></tr>'
            pagina+='</table>'
            paginas.executar.side_effect=lambda url,*a,**kw: '<urlset><url><loc>https://www.corsair.com/us/en/p/CMW16GX4M2C3200C16</loc></url></urlset>' if url.endswith('.xml') else pagina
            icecat=Mock();icecat.executar.side_effect=lambda p,f:(p,{**f,'icecat':{'status':'nao_encontrada'}})
            service=ImportarProdutoService(cliente=cliente,tokens=tokens,base_icecat=icecat,fabricantes=CompletarFichaFabricanteService(paginas))
            assert service.executar(pendencia.id,permitir_novos=True)['acao']=='proposta'
            assert MemoriaRAM.query.count()==0
            r=service.executar(pendencia.id,simular=False,permitir_novos=True)
            assert r['acao']=='importada',r
            assert MemoriaRAM.query.one().capacidade_gb==16
            assert MemoriaRAM.query.one().quantidade_pentes==2
            assert Oferta.query.count()==HistoricoOferta.query.count()==1
            assert service.executar(pendencia.id,simular=False,permitir_novos=True)['acao']=='inalterada'
            assert MemoriaRAM.query.count()==Oferta.query.count()==1
        finally:
            db.session.remove();db.engine.dispose()
