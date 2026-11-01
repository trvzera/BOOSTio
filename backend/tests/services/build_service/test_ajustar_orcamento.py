from copy import deepcopy

import pytest

from services.build_service.ajustar_orcamento_build_service import AjustarOrcamentoBuildService as Ajustar


def exemplo():
    catalogo = {
        'processador': [dict(id=1, preco=1000)], 'placa_video': [dict(id=1, preco=3000)],
        'memoria_ram': [dict(id=1, preco=500, capacidade_gb=16, ddr='DDR5', frequencia_mhz=5600,
                             quantidade_pentes=1, latencia='CL36')],
        'ssd': [dict(id=1, preco=800, capacidade_gb=500, interface='PCIe 4.0', formato='M.2',
                     velocidade_leitura_mbps=6000, velocidade_gravacao_mbps=5000)],
        'fan': [dict(id=1, preco=40, tamanho_mm=120, quantidade=1)],
    }
    build = {'componentes': [dict(tipo=t, id=1, quantidade=2 if t=='memoria_ram' else 5 if t=='fan' else 1) for t in catalogo]}
    return build, catalogo


def validar(build):
    return build


def executar(build, catalogo, teto=5700, **extras):
    return Ajustar().executar(build, catalogo, teto, teto, 0, extras.pop('validar', validar), **extras)


def test_reparo_combina_trocas_preserva_core_capacidades_e_recalcula_catalogo():
    build, catalogo = exemplo()
    catalogo['ssd'].append(dict(catalogo['ssd'][0], id=2, preco=600, velocidade_leitura_mbps=5000))
    catalogo['fan'].append(dict(catalogo['fan'][0], id=2, preco=10))
    original = deepcopy(build)
    for item in build['componentes']:
        item['preco'] = .01  # Preço não confiável da IA não entra no cálculo.
    r = executar(build, catalogo)
    assert r['diagnostico']['total_anterior'] == 6000
    assert r['diagnostico']['total_final'] == 5650
    assert r['diagnostico']['economia'] == 350
    assert len(r['diagnostico']['trocas']) == 2
    for tipo in ('processador','placa_video','memoria_ram'):
        assert next(i for i in r['build']['componentes'] if i['tipo']==tipo)['id'] == 1
    assert r['diagnostico']['subtotais_finais']['memoria_ram'] == 1000
    assert r['diagnostico']['subtotais_finais']['fan'] == 50
    assert [{k:v for k,v in i.items() if k!='preco'} for i in build['componentes']] == original['componentes']
    assert r['diagnostico']['trocas'][0]['diferencas_cadastradas']


def test_kit_ram_pode_custar_mais_por_unidade_e_menos_no_total():
    build, catalogo = exemplo()
    catalogo['memoria_ram'].append(dict(catalogo['memoria_ram'][0], id=2, preco=700, capacidade_gb=32, quantidade_pentes=2))
    r = executar(build, catalogo)
    ram = next(i for i in r['build']['componentes'] if i['tipo']=='memoria_ram')
    assert (ram['id'],ram['quantidade']) == (2,1)
    assert r['diagnostico']['subtotais_finais']['memoria_ram'] == 700
    assert r['diagnostico']['total_final'] == 5700


@pytest.mark.parametrize('mudanca', [dict(ddr='DDR4'), dict(frequencia_mhz=4800), dict(latencia='CL48'),
                                    dict(quantidade_pentes=1), dict(capacidade_gb=None)])
def test_ram_nao_perde_padrao_frequencia_pentes_ou_capacidade(mudanca):
    build, catalogo = exemplo()
    alternativa = dict(catalogo['memoria_ram'][0], id=2, preco=500, capacidade_gb=32, quantidade_pentes=2)
    catalogo['memoria_ram'].append({**alternativa, **mudanca})
    assert executar(build, catalogo) is None


def test_fan_considera_quantidade_do_kit_sem_confundir_preco_unitario():
    build, catalogo = exemplo()
    catalogo['fan'].append(dict(catalogo['fan'][0], id=2, preco=80, quantidade=5))
    r = executar(build, catalogo, teto=5880)
    fan = next(i for i in r['build']['componentes'] if i['tipo']=='fan')
    assert (fan['id'],fan['quantidade']) == (2,1)
    assert r['diagnostico']['subtotais_finais']['fan'] == 80


@pytest.mark.parametrize('mudanca', [dict(tamanho_mm=80), dict(quantidade=3), dict(esgotado=True)])
def test_fan_nao_muda_tamanho_nao_adiciona_unidades_e_nao_usa_esgotados(mudanca):
    build, catalogo = exemplo()
    catalogo['fan'].append({**catalogo['fan'][0], 'id':2, 'preco':1, **mudanca})
    assert executar(build, catalogo, teto=5880) is None


def test_nao_troca_ssd_pcie_por_sata_ou_hd_nem_core_por_modelo_barato():
    build, catalogo = exemplo()
    catalogo['ssd'].append(dict(catalogo['ssd'][0], id=2, preco=100, interface='SATA'))
    catalogo['hd'] = [dict(id=1,preco=10,capacidade_gb=1000,interface='SATA')]
    catalogo['processador'].append(dict(id=2,preco=10))
    catalogo['placa_video'].append(dict(id=2,preco=10))
    assert executar(build, catalogo) is None


def test_cada_proposta_completa_precisa_passar_no_callback():
    build, catalogo = exemplo()
    catalogo['ssd'].append(dict(catalogo['ssd'][0], id=2, preco=100))
    chamadas=[]
    def rejeitar(candidata):
        chamadas.append(candidata)
        raise ValueError('Incompatível com os conectores da placa')
    assert executar(build, catalogo, validar=rejeitar) is None
    assert chamadas


def test_callback_nao_pode_aprovar_mudanca_de_cpu_ou_um_total_invalido():
    build, catalogo = exemplo()
    catalogo['ssd'].append(dict(catalogo['ssd'][0], id=2, preco=100))
    catalogo['processador'].append(dict(id=2,preco=500))
    def mudar_cpu(candidata):
        next(i for i in candidata['componentes'] if i['tipo']=='processador')['id'] = 2
        return candidata
    assert executar(build, catalogo, validar=mudar_cpu) is None
    assert executar(build, catalogo, validar=lambda _: build) is None


def test_cor_pedida_e_reaproveitamento_sao_preservados():
    build, catalogo = exemplo()
    catalogo['ssd'][0]['modelo'] = 'SSD branco'
    catalogo['ssd'].append(dict(catalogo['ssd'][0], id=2, preco=100, modelo='SSD preto'))
    assert executar(build, catalogo, cor='branco') is None
    assert executar(build, catalogo, proprias={'ssd':'meu SSD'}) is None


def test_sobra_do_pc_nao_cobre_excesso_de_perifericos():
    build, catalogo = exemplo()
    catalogo['monitor']=[dict(id=1,preco=2000)]
    build['componentes'].append(dict(tipo='monitor',id=1,quantidade=1))
    catalogo['ssd'].append(dict(catalogo['ssd'][0], id=2, preco=100))
    assert Ajustar().executar(build,catalogo,7500,6500,1000,validar) is None


@pytest.mark.parametrize('build', [None,{}, {'componentes':[{}]}, {'componentes':[dict(tipo='ssd',id=1,quantidade=True)]}])
def test_entrada_incompleta_nao_inicia_reparo(build):
    assert executar(build, exemplo()[1]) is None


def test_fluxo_confirmado_nao_e_trocado_por_fluxo_desconhecido():
    build, catalogo = exemplo()
    catalogo['fan'][0].update(fluxo_ar='reverso',fonte_fluxo_ar='ficha_oficial')
    catalogo['fan'].append(dict(id=2,preco=1,tamanho_mm=120,quantidade=1))
    assert executar(build,catalogo,teto=5880) is None


def test_busca_tem_limite_de_estados_e_nao_aprova_callback_rejeitado():
    build, catalogo = exemplo()
    for ident in range(2,102):
        catalogo['memoria_ram'].append(dict(catalogo['memoria_ram'][0],id=ident,preco=300+ident,
                                           capacidade_gb=32,quantidade_pentes=2))
    reparador=Ajustar()
    reparador.MAX_ESTADOS=2
    chamadas=[]
    def rejeitar(candidata):
        chamadas.append(candidata)
        raise ValueError('Restrição adicional')
    assert reparador.executar(build,catalogo,5800,5800,0,rejeitar) is None
    assert len(chamadas)==2
