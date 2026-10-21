import json
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from services.build_service.criar_build_service import CriarBuildService


class CriarBuildPerifericosTest(unittest.TestCase):
    def setUp(self):
        self.tipos = (
            "processador", "placa_mae", "memoria_ram", "ssd", "fonte", "gabinete",
            "monitor", "teclado", "mouse", "fone",
        )
        self.catalogo = {
            tipo: [{"id": indice, "fabricante": "Marca", "modelo": tipo, "preco": 100}]
            for indice, tipo in enumerate(self.tipos, start=1)
        }
        self.build = {
            "nome": "Setup", "descricao": "Completo", "utilidade": "jogos",
            "componentes": [
                {"tipo": tipo, "id": self.catalogo[tipo][0]["id"], "quantidade": 1}
                for tipo in self.tipos
            ],
        }

    def test_exige_todos_os_perifericos_quando_solicitados(self):
        for tipo in CriarBuildService.PERIFERICOS:
            with self.subTest(tipo=tipo):
                build = {**self.build, "componentes": [
                    item.copy() for item in self.build["componentes"] if item["tipo"] != tipo
                ]}
                with self.assertRaisesRegex(ValueError, "não incluiu"):
                    CriarBuildService._validar_build(build, self.catalogo, 2000, percentual=20)

    def test_peca_propria_satisfaz_categoria_sem_custo(self):
        build = {**self.build, "componentes": [
            item.copy() for item in self.build["componentes"] if item["tipo"] != "monitor"
        ]}
        validada = CriarBuildService._validar_build(build, self.catalogo, 2000, percentual=20, proprias={"monitor": "Meu monitor"})
        self.assertEqual(validada["preco_total"], 900)

    def test_catalogo_envia_dados_do_monitor_em_json(self):
        monitor = SimpleNamespace(
            id=1, fabricante="Marca", modelo="Monitor", preco=500.0,
            tamanho_polegadas=Decimal("23.8"), resolucao="1920x1080",
            taxa_atualizacao_hz=144,
        )
        modelo = SimpleNamespace(__tablename__="monitor", listar_disponiveis_ate=lambda *args, **kwargs: [monitor])
        with patch("services.build_service.criar_build_service.MODELOS_PECAS", (modelo,)):
            catalogo = CriarBuildService._gerar_catalogo(1000, reserva_perifericos=1000)
        self.assertEqual(json.loads(json.dumps(catalogo))["monitor"][0]["tamanho_polegadas"], 23.8)

    def test_sem_reserva_nao_exige_perifericos(self):
        build = {**self.build, "componentes": [item.copy() for item in self.build["componentes"]
                                                if item["tipo"] not in CriarBuildService.PERIFERICOS]}
        self.assertEqual(CriarBuildService._validar_build(build, self.catalogo, 2000)["preco_total"], 600)

    def test_sem_reserva_nao_permite_comprar_perifericos(self):
        with self.assertRaisesRegex(ValueError, "limite reservado para periféricos"):
            CriarBuildService._validar_build(self.build, self.catalogo, 2000)

    def test_precos_de_perifericos_vem_do_catalogo_nao_da_resposta(self):
        self.catalogo["monitor"][0]["preco"] = 100.01
        for item in self.build["componentes"]:
            item["preco"] = 0
        with self.assertRaisesRegex(ValueError, "limite reservado para periféricos"):
            CriarBuildService._validar_build(self.build, self.catalogo, 2000, percentual=20)

    def test_nao_compra_novamente_uma_categoria_propria(self):
        with self.assertRaisesRegex(ValueError, "repetiu"):
            CriarBuildService._validar_build(self.build, self.catalogo, 2000, percentual=20,
                                            proprias={"monitor": "Meu monitor"})

    def test_rede_exige_somente_o_acessorio_escolhido(self):
        catalogo = {**self.catalogo,
                    "adaptador_wifi": [{"id": 20, "fabricante": "TP-Link", "modelo": "Archer", "preco": 100}],
                    "cabo_rede": [{"id": 21, "fabricante": "Ugreen", "modelo": "CAT6", "preco": 30}]}
        build = {**self.build, "componentes": [*self.build["componentes"],
            {"tipo": "adaptador_wifi", "id": 20, "quantidade": 1}]}
        rede = {"tipo": "wifi", "possuiAcessorio": False}
        self.assertEqual(CriarBuildService._validar_build(build, catalogo, 2000, percentual=20, rede=rede)["preco_total"], 1100)
        with self.assertRaisesRegex(ValueError, "conexão"):
            CriarBuildService._validar_build(build, catalogo, 2000, percentual=20, rede={"tipo": "cabo", "possuiAcessorio": False})

    def test_acessorio_de_rede_proprio_nao_precisa_ser_comprado(self):
        build = {**self.build, "componentes": [item.copy() for item in self.build["componentes"]]}
        validada = CriarBuildService._validar_build(
            build, self.catalogo, 2000, percentual=20,
            proprias={"adaptador_wifi": "Meu adaptador"},
            rede={"tipo": "wifi", "possuiAcessorio": True},
        )
        self.assertEqual(validada["preco_total"], 1000)


if __name__ == "__main__":
    unittest.main()
