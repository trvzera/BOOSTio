from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from models import Monitor
from services.build_service.preferencias_perifericos_service import PreferenciasPerifericosService as Regras
from services.build_service.amostrar_catalogo_service import AmostrarCatalogoService
from services.build_service.criar_build_service import CriarBuildService
from services.build_service.planejar_perifericos_service import PlanejarPerifericosService


@pytest.mark.parametrize("painel",["IPS","Fast Ips","Nano IPS","Rapid-IPS","VA","Fast VA"])
def test_paineis_confirmados_aceitos(painel):
    assert Regras.painel_permitido({"tipo_painel":painel})


@pytest.mark.parametrize("painel",[None,"","TN","OLED","QD-OLED","IPS ou TN","talvez IPS","<IPS>"])
def test_painel_ausente_ou_nao_permitido_nao_e_inferido(painel):
    assert not Regras.painel_permitido({"tipo_painel":painel,"modelo":"Monitor IPS Gamer"})


def test_gamer_prioriza_hz_e_edicao_resolucao_sem_pontuacao_de_qualidade():
    rapido={"taxa_atualizacao_hz":240,"tamanho_polegadas":24,"resolucao":"1920x1080"}
    trabalho={"taxa_atualizacao_hz":75,"tamanho_polegadas":27,"resolucao":"2560x1440"}
    assert Regras.monitor(rapido,"Jogos") > Regras.monitor(trabalho,"Jogos")
    assert Regras.monitor(trabalho,"Edição e trabalho") > Regras.monitor(rapido,"Edição e trabalho")
    assert Regras.monitor({"resolucao":"4K HDR","taxa_atualizacao_hz":True},"Trabalho") == (0,0,0)


def test_catalogo_filtra_monitor_antes_de_amostrar_sem_excluir_outros_produtos():
    monitores=[Monitor(id=i,fabricante="Teste",modelo=str(i),preco=100+i,tipo_painel=p,tamanho_polegadas=24,resolucao="1920x1080",taxa_atualizacao_hz=144) for i,p in enumerate(["IPS","VA","TN","OLED",None],1)]
    modelo=SimpleNamespace(__tablename__="monitor",listar_disponiveis_ate=lambda *a,**k:monitores)
    with patch("services.build_service.criar_build_service.MODELOS_PECAS",(modelo,)):
        catalogo=CriarBuildService._gerar_catalogo(200,500,utilidade="Jogos")
    assert [p["id"] for p in catalogo["monitor"]] == [1,2]


def test_amostragem_preserva_opcoes_de_hz_e_resolucao_nao_apenas_preco():
    pecas=[{"id":i,"preco":100+i,"resolucao":"1920x1080","taxa_atualizacao_hz":60,"tamanho_polegadas":24} for i in range(1,40)]
    pecas += [{"id":40,"preco":145,"resolucao":"1920x1080","taxa_atualizacao_hz":240,"tamanho_polegadas":24},
              {"id":41,"preco":180,"resolucao":"3840x2160","taxa_atualizacao_hz":75,"tamanho_polegadas":27}]
    for uso in ("Jogos","Edição"):
        amostra=AmostrarCatalogoService().executar("monitor",pecas,utilidade=uso)
        assert 1 in {p["id"] for p in amostra}
        assert (40 if uso=="Jogos" else 41) in {p["id"] for p in amostra}
        assert len(amostra)==12


def test_planejamento_inclui_mecanico_viavel_sem_aumentar_teto_e_preserva_opcao_barata():
    catalogo={tipo:[{"id":1,"preco":50}] for tipo in ("monitor","teclado","mouse","fone")}
    catalogo["monitor"]=[{"id":i,"preco":100+i,"taxa_atualizacao_hz":60+i*10,"resolucao":"1920x1080"} for i in range(1,9)]
    catalogo["teclado"]=[{"id":i,"preco":50+i} for i in range(1,9)]+[{"id":9,"preco":100,"mecanico":True,"switch":"Modelo confirmado"}]
    antes=deepcopy(catalogo)
    plano=PlanejarPerifericosService().executar(catalogo,400,utilidade="Jogos")
    assert plano["viavel"] and len(plano["combinacoes"])<=12
    assert all(c["total"]<=400 for c in plano["combinacoes"])
    assert any(any(p["tipo"]=="teclado" and p["id"]==9 for p in c["componentes"]) for c in plano["combinacoes"])
    economico=PlanejarPerifericosService().executar(catalogo,252,utilidade="Jogos")
    assert economico["viavel"]
    assert all(not any(p["tipo"]=="teclado" and p["id"]==9 for p in c["componentes"]) for c in economico["combinacoes"])
    assert catalogo==antes


def test_prompt_explica_paineis_mecanicos_orcamento_e_preferencias():
    prompt=CriarBuildService._criar_prompt({"nome":"PC","descricao":"Teste","utilidade":"Jogos"},5000,800,{})
    for termo in ("144 Hz", "27 polegadas", "QHD/4K", "painel confirmado IPS ou VA", "modelo de switch identificado", "sRGB", "Mini Tower, Mid Tower e Full Tower", "Não inclua produtos do AliExpress"):
        assert termo in prompt
    assert "não invente" in prompt.lower()
