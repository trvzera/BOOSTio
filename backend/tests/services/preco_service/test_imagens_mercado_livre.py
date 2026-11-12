from unittest.mock import Mock, patch

import pytest

from services.peca_service.atualizar_imagem_peca_service import AtualizarImagemPecaService
from services.peca_service.buscar_imagem_mercado_livre_service import BuscarImagemMercadoLivreService

FOTO = "https://http2.mlstatic.com/D_NQ_NP_123-F.webp"
WEBP = b"RIFF\x00\x00\x00\x00WEBPdados"


def resposta(conteudo=WEBP, tipo="image/webp", redirect=False):
    r = Mock(is_redirect=redirect, headers={"Content-Type": tipo})
    r.iter_content.return_value = [conteudo]
    return r


def servico(pictures, catalogo_id="MLB1"):
    cliente = Mock()
    cliente._consultar.return_value = {"id": catalogo_id, "pictures": pictures}
    return BuscarImagemMercadoLivreService(cliente=cliente, token="token")


def test_baixa_a_primeira_foto_do_catalogo():
    with patch("requests.get", return_value=resposta()) as get:
        assert servico([{"url": FOTO}]).executar("MLB1") == (WEBP, "webp")
    assert get.call_args.args[0] == FOTO and get.call_args.kwargs["allow_redirects"] is False


@pytest.mark.parametrize("url", ["http://http2.mlstatic.com/a.jpg", "https://evil.com/a.jpg",
                                 "https://mlstatic.com.evil.com/a.jpg", "https://u:p@http2.mlstatic.com/a.jpg", None])
def test_recusa_endereco_fora_do_dominio_do_catalogo(url):
    with patch("requests.get") as get, pytest.raises(ValueError):
        servico([{"url": url}]).executar("MLB1")
    get.assert_not_called()


def test_recusa_catalogo_diferente_do_vinculado_e_arquivo_invalido():
    with pytest.raises(ValueError):
        servico([{"url": FOTO}], catalogo_id="MLB2").executar("MLB1")
    with patch("requests.get", return_value=resposta(b"nao-e-imagem")), pytest.raises(ValueError):
        servico([{"url": FOTO}]).executar("MLB1")
    with patch("requests.get", return_value=resposta(redirect=True)), pytest.raises(ValueError):
        servico([{"url": FOTO}]).executar("MLB1")


def test_peca_sem_kabum_usa_o_vinculo_do_catalogo():
    peca = Mock(kabum_external=None, id=7, __tablename__="processador")
    with patch("services.peca_service.atualizar_imagem_peca_service.VinculoMercadoLivre.buscar",
               return_value=Mock(catalogo_id="MLB9")), \
         patch.object(BuscarImagemMercadoLivreService, "executar", return_value=(WEBP, "webp")) as ml:
        assert AtualizarImagemPecaService._baixar(peca) == (WEBP, "webp")
    ml.assert_called_once_with("MLB9")


def test_peca_sem_kabum_e_sem_vinculo_falha_com_motivo_claro():
    peca = Mock(kabum_external=None, id=7, __tablename__="processador")
    with patch("services.peca_service.atualizar_imagem_peca_service.VinculoMercadoLivre.buscar", return_value=None), \
         pytest.raises(ValueError, match="vínculo"):
        AtualizarImagemPecaService._baixar(peca)
