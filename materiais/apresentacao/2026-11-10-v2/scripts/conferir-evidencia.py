"""Evidência do pitch em SQLite em memória. Não importa app.py nem abre o banco do projeto."""
from pathlib import Path
from decimal import Decimal
import json, sys, inspect

ROOT=Path('/Users/trvzera/Desktop/BOOSTio')
sys.path.insert(0,str(ROOT/'backend'))
from flask import Flask
from models import db, Oferta, Processador
from repositories.ofertas_kabum_repository import buscar_ativa

app=Flask('boostio-pitch-evidencia-isolada')
app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',SQLALCHEMY_TRACK_MODIFICATIONS=False)
db.init_app(app)
with app.app_context():
    Processador.__table__.create(db.engine)
    Oferta.__table__.create(db.engine)
    peca=Processador(id=7,fabricante='DEMO',modelo='Peça de demonstração',nucleo=6,thread=12,clockbase=3.5,clockmax=4.0)
    peca.salvar()
    for ident,ref,valor,ativa,categoria in [(11,'demo-11','199.90',True,'processador'),(12,'demo-12','189.90',True,'processador'),(13,'demo-13','99.90',False,'processador'),(14,'demo-14','49.90',True,'ssd')]:
        Oferta(id=ident,tabela_peca=categoria,peca_id=7,loja='kabum',produto_id_loja=ref,vendedor_id='',url='https://example.invalid/'+ref,preco=Decimal(valor),esgotado=False,ativa=ativa).salvar()
    escolhido=buscar_ativa(peca)
    assert escolhido.id==12
    antes={'id':escolhido.id,'loja':escolhido.loja,'preco':str(escolhido.preco),'ativa':escolhido.ativa}
    consulta=Oferta.query.filter_by(tabela_peca=peca.__tablename__,peca_id=peca.id,loja='kabum',ativa=True).order_by(Oferta.id.desc()).limit(1)
    sql=str(consulta.statement.compile(db.engine,compile_kwargs={'literal_binds':True}))
    escolhido.preco=Decimal('194.90');escolhido.salvar();db.session.expire_all()
    assert buscar_ativa(peca).preco==Decimal('194.90')
    depois={'id':buscar_ativa(peca).id,'preco':str(buscar_ativa(peca).preco)}
    buscar_ativa(peca).deletar();db.session.expire_all()
    assert buscar_ativa(peca).id==11
    dados={'ambiente':'SQLite em memória, isolado. Sem rede, conta ou banco de produção.',
      'dados':'Dados de demonstração criados exclusivamente para conferir o código.',
      'consulta_real':'backend/repositories/ofertas_kabum_repository.py:buscar_ativa',
      'criterio':'Oferta KaBuM ativa de maior ID para a peça e categoria informadas. Não equivale à oferta de menor preço.',
      'entrada':{'categoria':'processador','peca_id':7},'retorno_consulta':antes,
      'controle':'A oferta 13 está inativa e a 14 pertence a outra categoria; ambas ficam fora do resultado.',
      'crud_orm':{'criar':'ModeloBase.salvar: inserção confirmada','ler':antes,'atualizar':depois,'excluir':{'id_removido':12,'proxima_oferta_ativa':11}},
      'codigo_repository':inspect.getsource(buscar_ativa),'sql_gerado_pelo_orm':sql,
      'observacao':'O SQL foi compilado a partir da consulta ORM, não copiado como SQL literal do Repository. Não comprova MySQL ou uma integração com loja.'}
    out=ROOT/'materiais/apresentacao/2026-11-10-v2/referencias/evidencia-orm-repository.json'
    out.write_text(json.dumps(dados,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'consulta':antes,'atualizacao':depois,'apos_exclusao':buscar_ativa(peca).id,'arquivo':str(out)},ensure_ascii=False))
