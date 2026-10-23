import unittest
from unittest.mock import Mock, patch

from services.preco_service.buscar_pagina_kabum_service import BuscarPaginaKabumService


URL = "https://www.kabum.com.br/produto/123/placa"


def resposta(url, html=b"<html></html>"):
    retorno = Mock(url=url, status_code=200, headers={"Content-Type": "text/html"}, encoding="utf-8")
    retorno.iter_content.return_value = [html]
    return retorno


class BuscarPaginaKabumTest(unittest.TestCase):
    def test_rejeita_redirecionamento_externo_antes_da_segunda_requisicao(self):
        primeiro = resposta(URL)
        primeiro.status_code = 302
        primeiro.headers = {"Location": "https://exemplo.invalid/privado"}
        with patch("services.preco_service.buscar_pagina_kabum_service.requests.get", return_value=primeiro) as buscar:
            with self.assertRaisesRegex(ValueError, "KaBuM"):
                BuscarPaginaKabumService().executar(URL)
        self.assertEqual(buscar.call_count, 1)
        primeiro.close.assert_called_once()

    def test_aceita_redirecionamento_para_mesmo_produto(self):
        primeiro = resposta(URL)
        primeiro.status_code = 301
        primeiro.headers = {"Location": "/produto/123/novo-nome"}
        segundo = resposta("https://www.kabum.com.br/produto/123/novo-nome")
        with patch("services.preco_service.buscar_pagina_kabum_service.requests.get", side_effect=[primeiro, segundo]) as buscar:
            self.assertEqual(BuscarPaginaKabumService().executar(URL), "<html></html>")
        self.assertEqual(buscar.call_count, 2)
        self.assertTrue(all(chamada.kwargs["allow_redirects"] is False for chamada in buscar.call_args_list))

    def test_rejeita_html_maior_que_limite(self):
        retorno = resposta(URL, b"x" * (BuscarPaginaKabumService.TAMANHO_MAXIMO + 1))
        with patch("services.preco_service.buscar_pagina_kabum_service.requests.get", return_value=retorno):
            with self.assertRaisesRegex(ValueError, "maior que 2 MB"):
                BuscarPaginaKabumService().executar(URL)
        retorno.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
