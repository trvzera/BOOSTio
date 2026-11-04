from unittest.mock import Mock
import pytest
from services.icecat_service.obter_ficha_icecat_service import ObterFichaIcecatService, ErroConsultaIcecat

REF=dict(id='123',atualizado='20261104000000')


def resposta(corpo=b'<ICECAT-interface><Product ID="123"/></ICECAT-interface>',status=200,tipo='application/xml'):
    r=Mock(status_code=status,headers={'Content-Type':tipo})
    r.iter_content.return_value=[corpo]
    r.__enter__=Mock(return_value=r);r.__exit__=Mock(return_value=False)
    return r


def test_cache_versionado_e_credenciais_somente_no_host_oficial(tmp_path,monkeypatch):
    get=Mock(return_value=resposta());monkeypatch.setattr('requests.get',get)
    s=ObterFichaIcecatService(tmp_path,usuario='teste',senha='segredo')
    assert s.executar(REF)==s.executar(REF)
    get.assert_called_once()
    args=get.call_args
    assert args.args==('https://data.icecat.biz/export/freexml/EN/123.xml',)
    assert args.kwargs['allow_redirects'] is False and args.kwargs['auth']==('teste','segredo')
    assert s.requisicoes==1


@pytest.mark.parametrize('r',[resposta(status=429),resposta(status=401),resposta(status=302)])
def test_http_falha_nao_grava_cache(tmp_path,monkeypatch,r):
    monkeypatch.setattr('requests.get',Mock(return_value=r))
    with pytest.raises(ErroConsultaIcecat):ObterFichaIcecatService(tmp_path,'u','s').executar(REF)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('r',[resposta(tipo='text/html'),resposta(corpo=b'x'*2_000_001),resposta(corpo=b'<html/>'),resposta(corpo=b'<broken>')])
def test_formato_e_tamanho_nao_gravam_cache(tmp_path,monkeypatch,r):
    monkeypatch.setattr('requests.get',Mock(return_value=r))
    with pytest.raises(ValueError):ObterFichaIcecatService(tmp_path,'u','s').executar(REF)
    assert not list(tmp_path.iterdir())


def test_sem_credenciais_e_sem_cache_requer_configuracao(tmp_path):
    with pytest.raises(ValueError,match='Configure'):ObterFichaIcecatService(tmp_path).executar(REF)
