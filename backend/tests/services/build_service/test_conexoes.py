"""Casos compartilhados com o editor JS; sem rede, LLM ou banco real."""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from services.build_service.armazenamento import avaliar_armazenamento, avaliar_baias
from services.build_service.conectores import avaliar_conectores
from services.build_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService
from models.medidas_fisicas import completar_medidas

CASOS = json.loads((Path(__file__).resolve().parents[4] / 'frontend/tests/fixtures/conexoes.json').read_text())


@pytest.mark.parametrize('caso', CASOS['conectores'], ids=lambda c:c['nome'])
def test_conectores_tipos_quantidades_e_cabos(caso):
    antes = deepcopy(caso)
    resultado, mensagem = avaliar_conectores(caso['fonte'], caso['consumidores'])
    assert resultado is caso['esperado'], mensagem
    assert caso == antes


@pytest.mark.parametrize('caso', CASOS['armazenamento'], ids=lambda c:c['nome'])
def test_slot_padrao_tamanho_e_compartilhamento(caso):
    antes = deepcopy(caso)
    regras = {r['codigo']:r for r in avaliar_armazenamento(caso['placa'], caso['discos'])}
    for codigo, esperado in caso['esperado'].items():
        assert regras[codigo]['condicao'] is esperado, regras[codigo]
    assert caso == antes


@pytest.mark.parametrize('caso', CASOS['baias'], ids=lambda c:c['nome'])
def test_baias_nao_somam_montagens_alternativas(caso):
    antes = deepcopy(caso)
    regras = {r['codigo']:r for r in avaliar_baias(caso['gabinete'], caso['discos'])}
    for codigo, esperado in caso['esperado'].items():
        assert regras[codigo]['condicao'] is esperado, regras[codigo]
    assert caso == antes


def avaliar(pecas):
    componentes = {p['categoria']:{'id':p['id'],'quantidade':p.pop('selecionadas',1)} for p in pecas}
    return AvaliarCompatibilidadeService().executar({'componentes':componentes}, catalogo=pecas)


def test_servico_bloqueia_conectores_e_storage_sem_esconder_ausencias():
    r = avaliar([
        {'id':1,'categoria':'fonte','conectores_alimentacao':{'pcie_8':1},'conectores_alimentacao_completos':True},
        {'id':2,'categoria':'placa_mae','conectores_alimentacao':{'eps_8':1},'conectores_alimentacao_completos':True},
    ])
    assert any(e['codigo']=='fonte-conectores' for e in r['erros'])
    caso = CASOS['armazenamento'][6]
    r = avaliar([{'id':1,'categoria':'placa_mae',**caso['placa']},
                 {'id':2,'categoria':'ssd',**caso['discos'][0][1]}])
    assert any(e['codigo']=='discos-compartilhamento' for e in r['erros'])


def test_observacao_generica_permanece_visivel_sem_aumentar_pendencias():
    r = avaliar([{'id':1,'categoria':'gabinete','observacoes_medidas':'Consulte condições de montagem.'}])
    assert r['orientacoes'][0]['codigo']=='gabinete-condicoes'
    assert 'Consulte' in r['orientacoes'][0]['mensagem']
    assert not any(v['codigo']=='gabinete-condicoes' for v in r['verificacoes']+r['naoVerificado'])


def test_fichas_reais_h610_cx650_e_3050_sem_cabo_auxiliar():
    def p(categoria,fabricante,modelo,part_number,produto):
        return completar_medidas(dict(categoria=categoria,fabricante=fabricante,modelo=modelo,part_number=part_number,
                                     link='https://www.kabum.com.br/produto/'+produto))
    placa=p('placa_mae','Husky','Nexus H610, LGA 1700, 12ª/13ª Gen, M.2 NVMe/SATA, DDR4 3200MHz, Micro-ATX, HDMI/VGA - HPM610','KABUM-692458','692458')
    fonte=p('fonte','Corsair','CX Series CX650','SEED-PSU-04','516056')
    gpu=p('placa_video','Zotac','RTX 3050 6gb Twin Edge Oc Gddr6 96 Bits Zotac','KABUM-1063804','1063804')
    assert avaliar_conectores(fonte,[('placa_mae',{},placa),('placa_video',{},gpu)])[0] is True
    assert fonte['cabos_pcie_independentes']==1 and fonte['conectores_alimentacao']['pcie_6_2']==2
