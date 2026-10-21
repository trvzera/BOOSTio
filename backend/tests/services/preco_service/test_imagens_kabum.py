import json
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import Mock, patch

from flask import Flask

from models import db, PlacaVideo
from migrations.imagens_pecas import migrar_imagens_pecas
from services.peca_service.atualizar_imagem_peca_service import AtualizarImagemPecaService
from services.peca_service.buscar_imagem_kabum_service import BuscarImagemKabumService


URL = "https://www.kabum.com.br/produto/123/placa-a"
IMAGEM = "https://images.kabum.com.br/produtos/fotos/123/placa-a.jpg"


def pagina(codigo="123", imagem=IMAGEM):
    produto = {"@type": "Product", "@id": f"https://www.kabum.com.br/produto/{codigo}",
               "sku": codigo, "image": imagem}
    return '<script type="application/ld+json">' + json.dumps(produto) + "</script>"


class ImagensKabumTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        db.init_app(self.app)
        self.contexto = self.app.app_context()
        self.contexto.push()
        db.create_all()
        migrar_imagens_pecas()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.contexto.pop()

    def test_valida_codigo_da_imagem(self):
        self.assertEqual(BuscarImagemKabumService._imagem_do_anuncio(pagina(), "123"), IMAGEM)
        with self.assertRaisesRegex(ValueError, "não encontrada"):
            BuscarImagemKabumService._imagem_do_anuncio(pagina("456"), "123")
        with self.assertRaisesRegex(ValueError, "não encontrada"):
            BuscarImagemKabumService._imagem_do_anuncio(
                pagina(imagem="https://images.kabum.com.br/produtos/fotos/456/outra.jpg"), "123")

    def test_aceita_imagem_do_catalogo_mirakl(self):
        url = "https://images.kabum.com.br/produtos/fotos/sync_mirakl/123/large/placa.jpg"
        self.assertEqual(BuscarImagemKabumService._imagem_do_anuncio(pagina(imagem=url), "123"), url)

    def test_salva_foto_e_retorna_no_catalogo(self):
        peca = PlacaVideo(fabricante="Marca", modelo="Modelo", memoria_gb=6, consumo_energia=70,
                           preco=100, kabum_external=URL, part_number="TESTE-123")
        db.session.add(peca)
        db.session.commit()
        jpg = b"\xff\xd8\xff" + b"foto"
        pagina_response = Mock(url=URL, text=pagina())
        pagina_response.raise_for_status.return_value = None
        imagem_response = Mock(headers={"Content-Type": "image/jpeg"}, is_redirect=False)
        imagem_response.iter_content.return_value = [jpg]
        imagem_response.raise_for_status.return_value = None
        with TemporaryDirectory() as pasta:
            with patch("services.peca_service.atualizar_imagem_peca_service.PASTA_IMAGENS", Path(pasta)):
                with patch("services.peca_service.buscar_imagem_kabum_service.requests.get",
                           side_effect=[pagina_response, imagem_response]) as buscar:
                    destino = AtualizarImagemPecaService().executar(peca)
                self.assertEqual(destino.read_bytes(), jpg)
                self.assertEqual(buscar.call_count, 2)
                self.assertEqual(peca.to_catalogo()["imagem"], "../imgs/produtos/placa_video-1.jpg")
                self.assertEqual(len(PlacaVideo.sem_imagem_com_link()), 0)


if __name__ == "__main__":
    unittest.main()
