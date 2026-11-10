from services.especificacoes_service.aplicar_revisao_identidade_service import AplicarRevisaoIdentidadeService
"""Migração e auditoria somente em MySQL local explicitamente descartável."""
import os
from dataclasses import replace
import pytest
from flask import Flask
from sqlalchemy import text, inspect
from sqlalchemy.engine import make_url
from models import db, Usuario, PlacaVideo, Oferta, RevisaoIdentidadePeca
from migrations.catalogo_automatizado import preparar_catalogo_automatizado
from services.especificacoes_service.converter_referencias_gpu_service import ConverterReferenciasGpuService
from services.catalogo_service.produto_normalizado import ProdutoNormalizado

URI=os.getenv('BOOSTIO_MYSQL_TEST_URI')
pytestmark=pytest.mark.skipif(not URI,reason='Requer MySQL local descartável')


def test_migracao_e_auditoria_preservam_catalogo_mysql():
    url=make_url(URI)
    assert url.host in ('localhost','127.0.0.1') and url.database=='boostio_ml_teste' and url.get_backend_name()=='mysql'
    a=Flask(__name__);a.config['SQLALCHEMY_DATABASE_URI']=URI;db.init_app(a)
    with a.app_context():
        db.drop_all();db.create_all()
        try:
            u=Usuario(nome='Preservado',email='teste@example.test',senha='hash')
            p=PlacaVideo(fabricante='NVIDIA',modelo='GeForce RTX 4060',memoria_gb=8,tipo_memoria='GDDR6',preco=1500,consumo_energia=115,kabum_external='https://www.kabum.com.br/produto/123')
            db.session.add_all([u,p]);db.session.commit();ident=p.id
            db.session.add(Oferta(tabela_peca='placa_video',peca_id=ident,loja='kabum',produto_id_loja='123',url=p.kabum_external));db.session.commit()
            antes=list(db.session.execute(text('SELECT * FROM usuario')))
            db.session.remove()
            with db.engine.begin() as conn:
                conn.execute(text('DROP TABLE revisao_identidade_peca'))
                for campo in ('fabricante_chip','modelo_referencia','codigo_modelo_fabricante'):
                    conn.execute(text(f'ALTER TABLE placa_video DROP COLUMN {campo}'))
            plano=preparar_catalogo_automatizado()
            assert plano['alteracoes'] and 'fabricante_chip' not in {c['name'] for c in inspect(db.engine).get_columns('placa_video')}
            preparar_catalogo_automatizado(simular=False)
            assert preparar_catalogo_automatizado()['alteracoes']==[]
            assert list(db.session.execute(text('SELECT * FROM usuario')))==antes
            p=db.session.get(PlacaVideo,ident)
            d=ProdutoNormalizado(loja='kabum',id_externo='123',categoria='placa_video',categoria_confirmada=True,titulo='Placa Marca RTX 4060 8GB GDDR6 - GV-N4060-8GD',marca='Marca',modelo='GV-N4060-8GD',modelos_alternativos=('GV-N4060-8GD',),ativo=True,fonte=p.kabum_external,especificacoes={'memoria_gb':8,'tipo_memoria':'GDDR6'},contexto={'finalidade':'especificacoes','origem_peca':f'placa_video:{ident}'})
            s=ConverterReferenciasGpuService();proposta=s.preparar(p,d)
            AplicarRevisaoIdentidadeService().executar(p,proposta,simular=True)
            assert p.fabricante=='NVIDIA' and RevisaoIdentidadePeca.query.count()==0
            AplicarRevisaoIdentidadeService().executar(p,proposta,simular=False)
            assert p.fabricante=='Marca' and p.preco==1500 and p.id==ident
            assert RevisaoIdentidadePeca.query.count()==1
            assert s.preparar(p,d)['status']=='inalterada'
        finally:
            db.session.remove();db.drop_all();db.engine.dispose()
