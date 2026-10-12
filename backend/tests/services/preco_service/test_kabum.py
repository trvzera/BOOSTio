import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import requests
from flask import Flask
from sqlalchemy import inspect, text

from models import db, PlacaVideo, ConsultaPreco
from services.preco_service.reservar_consulta_service import ReservarConsultaService
from services.preco_service.validar_link_service import ValidarLinkService
from services.peca_service.atualizar_precos_service import AtualizarPrecosService
from services.peca_service.migrar_links_service import MigrarLinksService
from services.peca_service.modelos_pecas import MODELOS_PECAS
from services.peca_service.popular_pecas_service import PopularPecasService
from services.peca_service.salvar_peca_service import SalvarPecaService


URL_1 = "https://www.kabum.com.br/produto/123/placa-a"
URL_2 = "https://www.kabum.com.br/produto/456/placa-b"


def pagina(codigo, preco="999.90", disponibilidade="InStock"):
    return (f'<script type="application/ld+json">{{"@context":"https://schema.org",'
            f'"@type":"Product","sku":"{codigo}","offers":{{"@type":"Offer",'
            f'"price":"{preco}","priceCurrency":"BRL",'
            f'"availability":"https://schema.org/{disponibilidade}"}}}}</script>')


class ColetaKabumTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        db.init_app(self.app)
        self.contexto = self.app.app_context()
        self.contexto.push()
        MigrarLinksService().executar()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.contexto.pop()

    def criar(self, url, modelo):
        return SalvarPecaService().executar(PlacaVideo, {
            "fabricante": "Palit", "modelo": modelo, "memoria_gb": 6,
            "consumo_energia": 70, "kabum_external": url,
        })

    def test_percorre_cada_link_e_salva_preco(self):
        primeira = self.criar(URL_1, "A")
        segunda = self.criar(URL_2, "B")

        def buscar(url, **kwargs):
            codigo = "123" if url == URL_1 else "456"
            return Mock(url=url, text=pagina(codigo, "999.90" if codigo == "123" else "1200.50"),
                        raise_for_status=Mock())

        with patch("services.preco_service.buscar_preco_kabum_service.requests.get", side_effect=buscar) as get:
            resumo = AtualizarPrecosService().executar(intervalo=0)
            self.assertEqual(resumo["consultas"], 2)
            self.assertEqual(resumo["atualizadas"], 2)
            self.assertEqual(get.call_count, 2)
        self.assertEqual(primeira.preco, 999.90)
        self.assertEqual(segunda.preco, 1200.50)
        self.assertEqual({c.status for c in ConsultaPreco.query.all()}, {"concluida"})
        self.assertEqual(AtualizarPrecosService().executar()["consultas"], 0)

    def test_popular_cadastra_uma_vez_e_chama_atualizacao(self):
        resumo = {"consultas": 0, "atualizadas": 0, "falhas": 0, "ignoradas": 0}
        with patch("services.peca_service.popular_pecas_service.AtualizarPrecosService.executar",
                   return_value=resumo) as atualizar, patch("builtins.print"):
            self.assertEqual(PopularPecasService().executar(intervalo=0), resumo)
            self.assertEqual(sum(classe.query.count() for classe in MODELOS_PECAS), 750)
            peca = PlacaVideo.query.first()
            SalvarPecaService().executar(PlacaVideo, {"kabum_external": URL_1}, peca.id)
            peca.preco = 500
            db.session.commit()
            PopularPecasService().executar(intervalo=0)
            self.assertEqual(sum(classe.query.count() for classe in MODELOS_PECAS), 750)
            self.assertEqual(peca.kabum_external, URL_1)
            self.assertEqual(peca.preco, 500)
        self.assertEqual(atualizar.call_count, 2)
        atualizar.assert_called_with(limite=None, intervalo=0)

    def test_popular_depois_atualiza_pecas_uma_a_uma(self):
        dados = [
            {"fabricante": "Palit", "modelo": str(codigo), "memoria_gb": 6,
             "consumo_energia": 70, "preco": 0, "esgotado": True,
             "part_number": f"SEED-TESTE-{codigo}",
             "kabum_external": f"https://www.kabum.com.br/produto/{codigo}/placa"}
            for codigo in (123, 456)
        ]

        def buscar(url, **kwargs):
            codigo = url.split("/produto/")[1].split("/")[0]
            return Mock(url=url, text=pagina(codigo), raise_for_status=Mock())

        with patch.object(PopularPecasService, "_dados_seed", return_value={PlacaVideo: dados}), \
             patch("services.preco_service.buscar_preco_kabum_service.requests.get", side_effect=buscar) as get, \
             patch("builtins.print"):
            resumo = PopularPecasService().executar(intervalo=0)
        self.assertEqual(resumo["atualizadas"], 2)
        self.assertEqual(get.call_count, 2)
        self.assertEqual({peca.preco for peca in PlacaVideo.query.all()}, {999.90})

    def test_id_incorreto_preserva_preco(self):
        peca = self.criar(URL_1, "A")
        peca.preco = 500
        db.session.commit()
        resposta = Mock(url=URL_1, text=pagina("456"), raise_for_status=Mock())
        with patch("services.preco_service.buscar_preco_kabum_service.requests.get", return_value=resposta):
            self.assertEqual(AtualizarPrecosService().executar()["falhas"], 1)
        self.assertEqual(peca.preco, 500)
        self.assertEqual(ConsultaPreco.query.one().status, "falha")

    def test_consulta_uma_vez_por_peca_a_cada_dia(self):
        peca = self.criar(URL_1, "A")
        agora = datetime(2026, 10, 11, tzinfo=timezone.utc)
        self.assertIsNotNone(ReservarConsultaService().executar(PlacaVideo, peca, agora))
        self.assertIsNone(ReservarConsultaService().executar(PlacaVideo, peca, agora))
        self.assertIsNotNone(ReservarConsultaService().executar(PlacaVideo, peca, agora + timedelta(days=1)))

    def test_atualiza_mais_de_700_pecas_na_mesma_execucao(self):
        for indice in range(701):
            self.criar(f"https://www.kabum.com.br/produto/{1000 + indice}/placa", str(indice))

        def buscar(url, **kwargs):
            codigo = url.split("/produto/")[1].split("/")[0]
            return Mock(url=url, text=pagina(codigo), raise_for_status=Mock())

        with patch("services.preco_service.buscar_preco_kabum_service.requests.get", side_effect=buscar) as get:
            resumo = AtualizarPrecosService().executar(intervalo=0)
        self.assertEqual(resumo["atualizadas"], 701)
        self.assertEqual(get.call_count, 701)
        self.assertEqual(AtualizarPrecosService().executar(intervalo=0)["consultas"], 0)

    def test_interrupcao_retorna_no_proximo_link(self):
        for codigo in (123, 456, 789):
            self.criar(f"https://www.kabum.com.br/produto/{codigo}/placa", str(codigo))

        def buscar(url, **kwargs):
            codigo = url.split("/produto/")[1].split("/")[0]
            if codigo == "456":
                erro = requests.HTTPError(response=Mock(status_code=403))
                return Mock(url=url, raise_for_status=Mock(side_effect=erro))
            return Mock(url=url, text=pagina(codigo), raise_for_status=Mock())

        with patch("services.preco_service.buscar_preco_kabum_service.requests.get", side_effect=buscar):
            self.assertEqual(AtualizarPrecosService().executar(intervalo=0)["consultas"], 2)
            self.assertEqual(AtualizarPrecosService().executar(intervalo=0)["atualizadas"], 1)
        self.assertEqual(ConsultaPreco.query.count(), 3)

    def test_troca_de_link_invalida_preco_anterior(self):
        peca = self.criar(URL_1, "A")
        peca.preco = 500
        db.session.commit()
        SalvarPecaService().executar(PlacaVideo, {"kabum_external": URL_2}, peca.id)
        self.assertEqual(peca.preco, 0)
        self.assertIsNone(peca.preco_atualizado_em)
        self.assertTrue(peca.esgotado)

    def test_link_fora_da_kabum_e_rejeitado(self):
        with self.assertRaises(ValueError):
            ValidarLinkService().executar("https://exemplo.invalid/produto/123")

    def test_migracao_preserva_links_kabum(self):
        peca = self.criar(URL_1, "A")
        with db.engine.begin() as conexao:
            conexao.execute(text("ALTER TABLE placa_video ADD COLUMN link TEXT"))
            conexao.execute(text("UPDATE placa_video SET link = :url WHERE id = :id"),
                            {"id": peca.id, "url": URL_1})
        MigrarLinksService().executar()
        MigrarLinksService().executar()
        self.assertNotIn("link", {c["name"] for c in inspect(db.engine).get_columns("placa_video")})
        self.assertEqual(db.session.get(PlacaVideo, peca.id).kabum_external, URL_1)

    def test_esgotado_preserva_ultimo_preco(self):
        peca = self.criar(URL_1, "A")
        peca.preco = 500
        db.session.commit()
        html = ('<script type="application/ld+json">{"@type":"Product","sku":"123",'
                '"offers":{"availability":"https://schema.org/OutOfStock"}}</script>')
        resposta = Mock(url=URL_1, text=html, raise_for_status=Mock())
        with patch("services.preco_service.buscar_preco_kabum_service.requests.get", return_value=resposta):
            self.assertEqual(AtualizarPrecosService().executar()["atualizadas"], 1)
        self.assertTrue(peca.esgotado)
        self.assertEqual(peca.preco, 500)


if __name__ == "__main__":
    unittest.main()
