from unittest.mock import Mock, patch

import pytest

from services.peca_service.atualizar_imagem_peca_service import AtualizarImagemPecaService
from services.peca_service.buscar_imagem_shopee_service import BuscarImagemShopeeService
from services.shopee_service.cliente_service import ClienteShopeeService

FOTO = "https://down-br.img.susercontent.com/file/br-11134207-abc"
PNG = b"\x89PNG\r\n\x1a\ndados"


def resposta(conteudo=PNG, tipo="image/png", redirect=False):
    r = Mock(is_redirect=redirect, headers={"Content-Type": tipo})
    r.iter_content.return_value = [conteudo]
    return r


def servico(url, shop="10", item="20"):
    cliente = Mock()
    cliente.consultar_imagem.return_value = {"nodes": [{"shopId": int(shop), "itemId": int(item), "imageUrl": url}]}
    return BuscarImagemShopeeService(cliente)


def test_baixa_a_imagem_do_anuncio_certo():
    with patch("requests.get", return_value=resposta()) as get:
        assert servico(FOTO).executar("10", "20") == (PNG, "png")
    assert get.call_args.args[0] == FOTO and get.call_args.kwargs["allow_redirects"] is False


@pytest.mark.parametrize("url", ["http://down-br.img.susercontent.com/a", "https://evil.com/a",
                                 "https://susercontent.com.evil.com/a", "https://u:p@cf.shopee.com.br/a", None])
def test_recusa_endereco_fora_dos_dominios_da_shopee(url):
    with patch("requests.get") as get, pytest.raises(ValueError):
        servico(url).executar("10", "20")
    get.assert_not_called()


def test_recusa_anuncio_diferente_e_arquivo_invalido():
    with pytest.raises(ValueError):
        servico(FOTO, item="99").executar("10", "20")
    with patch("requests.get", return_value=resposta(b"texto")), pytest.raises(ValueError):
        servico(FOTO).executar("10", "20")


def test_consulta_de_imagem_nao_altera_os_campos_da_consulta_de_precos():
    enviados = []
    cliente = ClienteShopeeService(app_id="a", secret="s", sessao=Mock())
    with patch.object(ClienteShopeeService, "_enviar", side_effect=lambda payload: enviados.append(payload) or {"nodes": []}):
        cliente.consultar_imagem(10, 20)
        cliente.consultar_anuncio(10, 20)
    assert "imageUrl" in enviados[0] and "imageUrl" not in enviados[1] and "priceMin" in enviados[1]


def test_peca_so_com_shopee_usa_a_oferta_ativa():
    peca = Mock(kabum_external=None, id=7, __tablename__="processador")
    consulta = Mock()
    consulta.filter_by.return_value.order_by.return_value.first.return_value = Mock(vendedor_id="10", produto_id_loja="10:20")
    with patch("services.peca_service.atualizar_imagem_peca_service.VinculoMercadoLivre.buscar", return_value=None), \
         patch("services.peca_service.atualizar_imagem_peca_service.Oferta") as oferta, \
         patch.object(BuscarImagemShopeeService, "executar", return_value=(PNG, "png")) as shopee:
        oferta.query = consulta
        assert AtualizarImagemPecaService._baixar(peca) == (PNG, "png")
    shopee.assert_called_once_with("10", "20")
