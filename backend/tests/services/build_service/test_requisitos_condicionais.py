from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
from copy import deepcopy
import pytest
from flask import Flask
from sqlalchemy import null
from models import db,ControleColeta,MemoriaRAM,Processador,HD,Fan,Monitor
from services.build_service.planejar_potencia_service import PlanejarPotenciaService
from services.validacoes_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService
from services.build_service.criar_build_service import CriarBuildService
from services.catalogo_service.reavaliar_montagem_service import ReavaliarMontagemService


def test_reservas_usam_quantidades_fisicas_e_nao_mutam_ficha():
    itens=[('processador',{'quantidade':1},{'consumo_energia':65}),
           ('memoria_ram',{'quantidade':2},{'quantidade_pentes':2}),
           ('fan',{'quantidade':2},{'quantidade':3})]
    antes=deepcopy(itens);r=PlanejarPotenciaService().executar(itens)
    assert r['consumo_conhecido_w']==65 and r['reserva_w']==100
    assert r['total_planejado_w']==165 and r['potencia_minima_w']==198
    assert itens==antes


@pytest.mark.parametrize('valor',[None,0,False,float('nan'),-1])
def test_cpu_e_gpu_sem_consumo_valido_nao_recebem_reserva(valor):
    for tipo in ('processador','placa_video'):
        r=PlanejarPotenciaService().executar([(tipo,{}, {'consumo_energia':valor})])
        assert r['potencia_minima_w'] is None and r['desconhecidos']


def test_conhecido_por_kit_prevalece_e_kit_desconhecido_nao_vira_um():
    r=PlanejarPotenciaService().executar([('fan',{'quantidade':2},{'consumo_energia':30,'quantidade':3})])
    assert r['consumo_conhecido_w']==60 and not r['estimativas']
    r=PlanejarPotenciaService().executar([('memoria_ram',{}, {})])
    assert r['potencia_minima_w'] is None


def test_fonte_com_reserva_insuficiente_e_barrada():
    catalogo=[{'categoria':'fonte','id':1,'potencia_w':190}, {'categoria':'processador','id':1,'consumo_energia':65},
              {'categoria':'memoria_ram','id':1,'quantidade_pentes':2}, {'categoria':'fan','id':1,'quantidade':3}]
    estado={'componentes':{'fonte':{'id':1},'processador':{'id':1},'memoria_ram':[{'id':1,'quantidade':2}],'fan':[{'id':1,'quantidade':2}]}}
    r=AvaliarCompatibilidadeService().executar(estado,catalogo)
    regra=next(v for v in r['verificacoes'] if v['codigo']=='fonte-potencia')
    assert regra['status']=='incompativel' and regra['detalhes']['reserva_w']==100
    catalogo[0]['potencia_w']=200
    regra=next(v for v in AvaliarCompatibilidadeService().executar(estado,catalogo)['verificacoes'] if v['codigo']=='fonte-potencia')
    assert regra['status']=='sem_conflitos' and regra['fonte']=='politica_planejamento_energia'


def test_campos_opcionais_nao_bloqueiam_minimos_mas_identidade_continua_separada():
    ram=MemoriaRAM(fabricante='Teste',modelo='RAM',capacidade_gb=16,ddr='DDR4',frequencia_mhz=3200,quantidade_pentes=2,formato='DIMM')
    assert pendencias_para_montagem(ram)==[]
    ram.formato='SO-DIMM';assert pendencias_para_montagem(ram)==[]  # Formato conhecido; a build ainda deve confrontar o slot.
    ram.quantidade_pentes=None;assert 'quantidade_pentes' in pendencias_para_montagem(ram)
    hd=HD(fabricante='Teste',modelo='HD',capacidade_gb=500,interface='SATA')
    assert pendencias_para_montagem(hd)==[]
    fan=Fan(fabricante='Teste',modelo='Fan',tamanho_mm=120,quantidade=3)
    assert pendencias_para_montagem(fan)==[]
    monitor=Monitor(fabricante='Teste',modelo='Monitor',tamanho_polegadas=24,resolucao='1920x1080',taxa_atualizacao_hz=60,conexao='HDMI')
    assert pendencias_para_montagem(monitor)==[]


def test_reavaliacao_nao_aprova_identidade_e_e_idempotente():
    app=Flask('reavaliacao');app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all();ControleColeta.inicializar()
        p=MemoriaRAM(fabricante='Teste',modelo='RAM',capacidade_gb=16,ddr='DDR4',frequencia_mhz=3200,quantidade_pentes=2,formato='DIMM',
          status_validacao='em_revisao',ficha_montagem_validada=False,preco=null(),esgotado=null(),fontes_especificacoes={'_pc_part_dataset':{}})
        db.session.add(p);db.session.commit()
        s=ReavaliarMontagemService();r=s.executar()
        db.session.refresh(p);assert r['minimos_atendidos']==1 and p.ficha_montagem_validada is False
        r=s.executar(simular=False);db.session.refresh(p)
        assert r['indicadores_alterados']==1 and p.ficha_montagem_validada is True
        assert p.status_validacao=='em_revisao' and not p.publicavel and p.preco is p.esgotado is None
        assert s.executar(simular=False)['indicadores_alterados']==0
        db.session.remove();db.engine.dispose()
