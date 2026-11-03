from unittest.mock import Mock

import pytest

from services.mercadolivre_service.controle_requisicoes_service import ControleRequisicoesService, ErroMercadoLivre, OrcamentoRequisicoesEsgotado


def test_429_respeita_retry_after_e_conta_tentativas():
    pausas=[]; chamada=Mock(side_effect=[ErroMercadoLivre(429,'5'),{'ok':True}])
    c=ControleRequisicoesService(3,1,dormir=pausas.append,relogio=lambda:0,jitter=lambda:0)
    assert c.executar(chamada)=={'ok':True}
    assert c.total==2 and 5 in pausas


def test_retry_after_longo_ou_403_nao_repetem():
    for erro in [ErroMercadoLivre(429,'120'),ErroMercadoLivre(403)]:
        chamada=Mock(side_effect=erro)
        c=ControleRequisicoesService(5,1,dormir=lambda _:None)
        with pytest.raises(ErroMercadoLivre):c.executar(chamada)
        chamada.assert_called_once()


def test_orcamento_e_tentativas_limitados():
    c=ControleRequisicoesService(2,1,dormir=lambda _:None,jitter=lambda:0)
    chamada=Mock(side_effect=ErroMercadoLivre(429))
    with pytest.raises(OrcamentoRequisicoesEsgotado):c.executar(chamada)
    assert chamada.call_count==2


@pytest.mark.parametrize('intervalo',[0,float('nan'),float('inf')])
def test_intervalo_valido(intervalo):
    with pytest.raises(ValueError):ControleRequisicoesService(intervalo=intervalo)
