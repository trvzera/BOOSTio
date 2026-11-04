from dataclasses import asdict
from datetime import datetime
from flask import Flask
from models import db,Processador,ProdutoPendente,ControleColeta,Oferta,HistoricoOferta
from utils.identidade_peca import assinatura_documento
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.classificar_pendencias_service import ClassificarPendenciasService
from services.catalogo_service.importar_catalogo_service import ImportarCatalogoService


def test_duas_lojas_mesma_peca_sem_mpn_sem_transporte_mercadolivre():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all();ControleColeta.inicializar()
        p=Processador(fabricante='AMD',modelo='Ryzen 5 5500',part_number='SEED-CPU-1',soquete='AM4',nucleo=6,thread=12,clockbase=3.6,clockmax=4.2,preco=500,consumo_energia=65,status_validacao='aprovado')
        db.session.add(p);db.session.commit()
        for loja in ('loja_a','loja_b'):
            dto=ProdutoNormalizado(loja=loja,id_externo='cpu-1',categoria='processador',categoria_confirmada=True,titulo='AMD Ryzen 5 5500',modelo='Ryzen 5 5500',marca='AMD',ativo=True,especificacoes={'soquete':'AM4','nucleo':6,'thread':12})
            bruto={'normalizado':asdict(dto)}
            pend=ProdutoPendente(loja=loja,produto_id_loja='oferta-1',titulo=dto.titulo,url='https://loja.example/cpu',categoria_sugerida='processador',dados_originais=bruto,coletado_em=datetime(2026,11,3))
            db.session.add(pend);db.session.commit()
            assert ClassificarPendenciasService().executar(simular=False)['confirmadas']>=1
            ficha={'dados':{},'identidade':{},'pronto':False,'conflitos':[],'produto':{'id':'cpu-1'},'benchmark':{'dados':{}}}
            anuncio={'produto_id_loja':'oferta-1','preco':'450.00','url':'https://loja.example/cpu','esgotado':False}
            s=ImportarCatalogoService()
            r=s.executar(pend.id,dto,ficha,anuncio,assinatura_documento(bruto),simular=False)
            assert r['acao']=='importada' and r['criterio']=='modelo_especificacoes'
            assert s.executar(pend.id,dto,ficha,anuncio,assinatura_documento(bruto),simular=False)['acao']=='inalterada'
        assert Processador.query.count()==1 and Oferta.query.count()==HistoricoOferta.query.count()==2
        assert p.preco==500
        db.session.remove();db.engine.dispose()


def test_cadastra_novo_sem_mpn_quando_ficha_e_fontes_estao_completas():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all();ControleColeta.inicializar()
        dto=ProdutoNormalizado(loja='loja_nova',id_externo='5500',categoria='processador',categoria_confirmada=True,
            titulo='AMD Ryzen 5 5500',marca='AMD',modelo='Ryzen 5 5500',ativo=True,especificacoes={'soquete':'AM4','nucleo':6,'thread':12})
        bruto={'normalizado':asdict(dto)}
        p=ProdutoPendente(loja='loja_nova',produto_id_loja='oferta',titulo=dto.titulo,url='https://loja.example/cpu',categoria_sugerida='processador',dados_originais=bruto,coletado_em=datetime(2026,11,3))
        db.session.add(p);db.session.commit()
        dados=dict(fabricante='AMD',modelo='Ryzen 5 5500',soquete='AM4',nucleo=6,thread=12,clockbase=3.6,clockmax=4.2,preco=500,consumo_energia=65,esgotado=False,videointegrado=False,cooler=True)
        ficha=dict(dados=dados,identidade={'mpn':None,'gtin':None},pronto=True,conflitos=[],produto={'id':'5500'},benchmark={'dados':{}},
                   fontes={k:{'url':'https://fabricante.example/ficha' if k not in ('preco','esgotado') else 'https://loja.example/cpu'} for k in dados})
        a={'produto_id_loja':'oferta','preco':'500.00','url':'https://loja.example/cpu','esgotado':False}
        s=ImportarCatalogoService()
        semfonte={**ficha,'fontes':{}}
        assert s.executar(p.id,dto,semfonte,a,assinatura_documento(bruto),permitir_novos=True)['acao']=='revisao'
        r=s.executar(p.id,dto,ficha,a,assinatura_documento(bruto),simular=False,permitir_novos=True)
        assert r['acao']=='importada' and r['novo_componente'] and r['criterio']=='modelo_especificacoes'
        assert Processador.query.one().part_number is None and Oferta.query.count()==HistoricoOferta.query.count()==1
        db.session.remove();db.engine.dispose()
