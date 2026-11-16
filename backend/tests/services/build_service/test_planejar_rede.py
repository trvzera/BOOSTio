import services.build_service.gerar_candidata_service as validacao_module
from services.build_service.gerar_candidata_service import gerar_candidata
from services.validacoes_service.validar_build_gerada_service import validar_build_gerada
import services.build_service.criar_build_service as criacao_module
from services.build_service.prompt_build_service import criar_prompt
from copy import deepcopy
from unittest.mock import patch

import pytest

from services.build_service.planejar_rede_service import PlanejarRedeService as Rede
from services.build_service.criar_build_service import CriarBuildService
from services.validacoes_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService


PEDIDO = {"tipo": "cabo", "possuiAcessorio": False, "comprimentoCaboM": 20, "velocidadeMbps": 500}
CATALOGO = {"cabo_rede": [
    {"id": 1, "preco": 30, "comprimento_m": 1},
    {"id": 2, "preco": 60, "comprimento_m": 10},
    {"id": 3, "preco": 120, "comprimento_m": 20, "esgotado": True},
]}


def test_vinte_metros_sem_cabo_adequado_vira_pendencia_sem_alterar_pedido():
    antes = deepcopy(PEDIDO)
    assert Rede.executar(CATALOGO, PEDIDO) == {"tipo": "cabo_rede", "ids_permitidos": [], "pendente": True}
    assert PEDIDO == antes
    prompt = criar_prompt({"nome": "PC", "descricao": "Jogos", "utilidade": "Jogos", "rede": PEDIDO}, 8000, 2000, CATALOGO, 10)
    assert '"acessorio_rede_obrigatorio": null' in prompt
    assert '"categorias_rede_proibidas": ["adaptador_wifi", "cabo_rede"]' in prompt
    assert "Isso não inviabiliza" in prompt


@pytest.mark.parametrize("comprimento", [None, 0, -1, True, 10, float("nan"), float("inf")])
def test_comprimento_desconhecido_ou_curto_nao_aprova_cabo(comprimento):
    assert not Rede.opcoes({"cabo_rede": [{"id": 1, "preco": 50, "comprimento_m": comprimento}]}, PEDIDO)


def test_cabo_longo_sem_taxa_cadastrada_nao_inventa_velocidade():
    cabo = {"id": 4, "preco": 80, "comprimento_m": 25, "fabricante": "Teste", "modelo": "CAT6 25m"}
    assert Rede.opcoes({"cabo_rede": [cabo]}, PEDIDO) == [cabo]
    assert "velocidade_mbps" not in cabo
    assert not Rede.opcoes({"cabo_rede": [{**cabo, "velocidade_mbps": 100}]}, PEDIDO)


def test_nao_compra_rede_ja_possuida_ou_nao_solicitada():
    for rede, proprias in [({**PEDIDO, "possuiAcessorio": True}, {}), ({}, {}), (PEDIDO, {"cabo_rede": "Meu cabo"})]:
        assert Rede.executar(CATALOGO, rede, proprias)["tipo"] is None


def test_wifi_padrao_exige_taxa_anunciada_conhecida_e_adequada():
    rede = {"tipo": "wifi", "possuiAcessorio": False, "velocidadeMbps": 500}
    catalogo = {"adaptador_wifi": [
        {"id": 1, "preco": 30, "velocidade_mbps": 300},
        {"id": 2, "preco": 60},
        {"id": 3, "preco": 80, "velocidade_mbps": 600},
        {"id": 4, "preco": 100, "velocidade_mbps": 1200, "esgotado": True},
    ]}
    assert Rede.executar(catalogo, rede)["ids_permitidos"] == [3]


def test_cat6_tem_prioridade_sem_ocultar_cabo_adequado_mais_barato():
    cat5 = {"id": 1, "preco": 20, "comprimento_m": 20, "modelo": "Cat5e"}
    cat6 = {"id": 2, "preco": 35, "comprimento_m": 20, "categoria": "CAT 6"}
    curto = {"id": 3, "preco": 10, "comprimento_m": 1, "modelo": "CAT6"}
    catalogo = {"cabo_rede": [cat5, cat6, curto]}
    antes = deepcopy(catalogo)
    assert Rede.opcoes(catalogo, PEDIDO) == [cat6, cat5]
    assert Rede.opcoes({"cabo_rede": [cat5]}, PEDIDO) == [cat5]
    assert not Rede._cat6({"modelo": "Adaptador CAT60"})
    assert Rede._cat6({"modelo": "Cabo Cat6a"})
    assert catalogo == antes


def test_complemento_remove_somente_cabo_impossivel_sem_inventar_produto():
    build = {"componentes": [{"tipo": "processador", "id": 9}, {"tipo": "cabo_rede", "id": 1}]}
    antes = deepcopy(build)
    assert Rede.completar(build, CATALOGO, PEDIDO) == {"componentes": [{"tipo": "processador", "id": 9}]}
    assert build == antes


def test_complemento_inclui_opcao_adequada_mas_total_ainda_e_validado():
    cabo = {"id": 4, "preco": 80, "comprimento_m": 25, "fabricante": "Teste", "modelo": "CAT6 25m"}
    catalogo = {"cabo_rede": [*CATALOGO["cabo_rede"], cabo]}
    build = {"componentes": [{"tipo": "cabo_rede", "id": 1}]}
    assert Rede.completar(build, catalogo, PEDIDO)["componentes"] == [{"tipo": "cabo_rede", "id": 4, "quantidade": 1}]
    assert Rede.completar({"componentes": []}, catalogo, PEDIDO)["componentes"][0]["id"] == 4
    with pytest.raises(ValueError, match="orçamento"):
        validar_build_gerada({"nome": "PC", "descricao": "Teste", "utilidade": "Jogos",
            **Rede.completar({"componentes": []}, catalogo, PEDIDO)}, catalogo, 50, rede=PEDIDO)


def test_diagnostico_preserva_pendencia_no_editor_sem_bloquear_pc():
    dados = AvaliarCompatibilidadeService().executar({"componentes": {}, "rede": PEDIDO}, catalogo=[])
    texto = next(o["mensagem"] for o in dados["orientacoes"] if o["codigo"] == "rede-pendente")
    assert "20 m" in texto and "nem no total" in texto
    assert "cabo_rede" not in dados["pecasPendentes"]


def test_recuperacao_rede_usa_mesma_chamada_e_nao_modifica_flag_de_posse():
    resposta = {"componentes": [{"tipo": "cabo_rede", "id": 1}]}
    with patch("services.build_service.gerar_candidata_service.LLMService.executar", return_value=resposta) as llm, \
         patch("services.build_service.gerar_candidata_service.CompletarVentilacaoService.executar", side_effect=lambda b,*a,**k:b), \
         patch.object(validacao_module, "validar_build_gerada", side_effect=lambda b,*a,**k:b):
        resultado = gerar_candidata(1, "Prompt", "teste", CATALOGO, 8000, 10, {}, {}, PEDIDO, tentativas_correcao=0)
    assert resultado["componentes"] == [] and PEDIDO["possuiAcessorio"] is False
    llm.assert_called_once()


def test_duas_conexoes_planejadas_e_completadas_sem_misturar_ids():
    rede = {'tipo':'ambos','possuiAcessorio':False,'velocidadeMbps':500,'comprimentoCaboM':20}
    catalogo = {'cabo_rede':[{'id':1,'preco':50,'comprimento_m':20}],
                'adaptador_wifi':[{'id':2,'preco':60,'velocidade_mbps':600}, {'id':3,'preco':10,'velocidade_mbps':150}]}
    for itens in catalogo.values():
        for peca in itens:
            peca.update(fabricante='Teste', modelo='Acessório de rede')
    planos = Rede.planos(catalogo, rede)
    assert [(p['tipo'],p['ids_permitidos']) for p in planos] == [('cabo_rede',[1]),('adaptador_wifi',[2])]
    original = {'componentes':[]}
    build = Rede.completar(original,catalogo,rede)
    assert original == {'componentes':[]}
    assert build['componentes'] == [{'tipo':'cabo_rede','id':1,'quantidade':1},{'tipo':'adaptador_wifi','id':2,'quantidade':1}]
    with pytest.raises(ValueError, match='orçamento'):
        validar_build_gerada({'nome':'PC','descricao':'Teste','utilidade':'Estudos',**build}, catalogo, 100, rede=rede)
    prompt = criar_prompt({'nome':'PC','descricao':'Teste','utilidade':'Estudos','rede':rede},8000,2000,catalogo,0)
    assert '"acessorio_rede_obrigatorio": ["cabo_rede", "adaptador_wifi"]' in prompt
    assert '"categorias_rede_proibidas": []' in prompt
    assert 'Nunca inclua ambos.' not in prompt


def test_falta_de_cabo_nao_remove_wifi_e_peca_propria_nao_e_recomprada():
    rede = {'tipo':'ambos','possuiAcessorio':False,'comprimentoCaboM':20,'velocidadeMbps':500}
    catalogo = {'cabo_rede':[{'id':1,'preco':50,'comprimento_m':2}],
                'adaptador_wifi':[{'id':2,'preco':60,'velocidade_mbps':600}]}
    build = Rede.completar({'componentes':[]},catalogo,rede)
    assert build['componentes'] == [{'tipo':'adaptador_wifi','id':2,'quantidade':1}]
    assert Rede.completar({'componentes':[]},catalogo,rede,{'adaptador_wifi':'Meu Wi-Fi'})['componentes'] == []
    assert Rede.completar({'componentes':[]},catalogo,{**rede,'possuiAcessorio':True})['componentes'] == []


def test_build_completa_aceita_duas_redes_mas_rejeita_acessorio_inadequado():
    rede = {'tipo':'ambos','possuiAcessorio':False,'comprimentoCaboM':20,'velocidadeMbps':500}
    tipos = ('processador', 'placa_mae', 'memoria_ram', 'fonte', 'gabinete', 'ssd')
    catalogo = {tipo:[{'id':1,'fabricante':'Teste','modelo':tipo,'preco':100}] for tipo in tipos}
    catalogo['processador'][0].update(videointegrado=True,cooler=True,consumo_energia=65)
    catalogo['fonte'][0]['potencia_w'] = 500
    catalogo['gabinete'][0]['fans_inclusos'] = 1
    catalogo['memoria_ram'][0]['quantidade_pentes'] = 1
    catalogo.update(cabo_rede=[{'id':1,'fabricante':'Teste','modelo':'CAT6','preco':50,'comprimento_m':20}],
        adaptador_wifi=[{'id':1,'fabricante':'Teste','modelo':'Wi-Fi 600','preco':60,'velocidade_mbps':600},
                        {'id':2,'fabricante':'Teste','modelo':'Wi-Fi 150','preco':20,'velocidade_mbps':150}])
    build = Rede.completar({'nome':'PC','descricao':'Teste','utilidade':'Estudos',
        'componentes':[{'tipo':tipo,'id':1} for tipo in tipos]},catalogo,rede)
    assert validar_build_gerada(deepcopy(build),catalogo,2000,rede=rede)['preco_total'] == 710
    sem_wifi = deepcopy(build)
    sem_wifi['componentes'] = [c for c in sem_wifi['componentes'] if c['tipo'] != 'adaptador_wifi']
    with pytest.raises(ValueError,match='escolha de conexão'):
        validar_build_gerada(sem_wifi,catalogo,2000,rede=rede)
    build['componentes'][-1]['id'] = 2
    with pytest.raises(ValueError,match='velocidade solicitada'):
        validar_build_gerada(build,catalogo,2000,rede=rede)
