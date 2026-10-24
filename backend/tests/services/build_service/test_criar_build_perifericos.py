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
        self.catalogo["gabinete"][0]["fans_inclusos"] = 1
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
        from models import Monitor
        monitor = Monitor(
            id=1, fabricante="Marca", modelo="Monitor", preco=500.0,
            tamanho_polegadas=Decimal("23.8"), resolucao="1920x1080",
            taxa_atualizacao_hz=144,
        )
        modelo = SimpleNamespace(__tablename__="monitor", listar_disponiveis_ate=lambda *args, **kwargs: [monitor])
        with patch("services.build_service.criar_build_service.MODELOS_PECAS", (modelo,)):
            catalogo = CriarBuildService._gerar_catalogo(1000, reserva_perifericos=1000)
        self.assertEqual(json.loads(json.dumps(catalogo))["monitor"][0]["tamanho_polegadas"], 23.8)

    def test_catalogo_nao_omite_especificacoes_da_cpu_usadas_para_o_objetivo(self):
        from models import Processador
        cpu = Processador(id=1, fabricante="Teste", modelo="CPU", soquete="AM5", preco=1000,
            nucleo=8, thread=16, clockbase=Decimal("3.5"), clockmax=Decimal("5.0"))
        campos = CriarBuildService._campos_pecas(cpu)
        self.assertEqual(campos["nucleo"], 8)
        self.assertEqual(campos["thread"], 16)
        self.assertEqual(campos["clockbase"], 3.5)
        self.assertEqual(campos["clockmax"], 5.0)
        json.dumps(campos)

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

    def test_rede_valida_tipos_medidas_e_valores_finitos(self):
        CriarBuildService._validar_rede({"tipo": "cabo", "possuiAcessorio": False, "comprimentoCaboM": 10, "velocidadeMbps": 1000})
        for rede in ([], False, "", {"tipo": "outro"}, {"possuiAcessorio": "false"},
                     {"comprimentoCaboM": True}, {"comprimentoCaboM": -1},
                     {"velocidadeMbps": float("nan")}, {"velocidadeMbps": 100001}):
            with self.subTest(rede=rede), self.assertRaises(ValueError):
                CriarBuildService._validar_rede(rede)

    def test_cabo_confirmadamente_curto_nao_atende_comprimento_solicitado(self):
        catalogo = {**self.catalogo, "cabo_rede": [{"id": 21, "fabricante": "Teste", "modelo": "CAT6 1m", "preco": 30, "comprimento_m": 1}]}
        build = {**self.build, "componentes": [*self.build["componentes"], {"tipo": "cabo_rede", "id": 21, "quantidade": 1}]}
        with self.assertRaisesRegex(ValueError, "menor que o comprimento"):
            CriarBuildService._validar_build(build, catalogo, 2000, percentual=20,
                rede={"tipo": "cabo", "possuiAcessorio": False, "comprimentoCaboM": 10})

    def test_prompt_explicita_pares_por_socket_e_rede_sem_certificar_bios(self):
        catalogo = {**self.catalogo,
                    "processador": [{"id": 1, "soquete": "LGA 1700"}, {"id": 2, "soquete": "AM4"}, {"id": 3}],
                    "placa_mae": [{"id": 10, "socket": "LGA1700"}, {"id": 20, "socket": "AM5"}, {"id": 30}]}
        dados = {"nome": "QA", "descricao": "Teste", "utilidade": "Estudos", "rede": {}}
        prompt = CriarBuildService._criar_prompt(dados, 5000, 1000, catalogo)
        bloco = json.loads(prompt.split("# RESTRIÇÕES CALCULADAS PELO SERVIDOR\n")[1].split("\n")[0])
        self.assertEqual(bloco["pares_por_socket_apenas"], [{"processador": 1, "placas_mae": [10]}, {"processador": 2, "placas_mae": []}])
        self.assertIsNone(bloco["acessorio_rede_obrigatorio"])
        self.assertEqual(bloco["categorias_rede_proibidas"], ["adaptador_wifi", "cabo_rede"])
        dados["rede"] = {"tipo": "wifi", "possuiAcessorio": False}
        prompt = CriarBuildService._criar_prompt(dados, 5000, 1000, catalogo)
        self.assertIn('"acessorio_rede_obrigatorio": "adaptador_wifi"', prompt)
        self.assertIn('"categorias_rede_proibidas": ["cabo_rede"]', prompt)

    def test_prompt_usa_o_investimento_sem_transformar_teto_em_gasto_minimo(self):
        dados = {"nome": "PC", "descricao": "Jogos exigentes", "utilidade": "Jogos"}
        prompt = CriarBuildService._criar_prompt(dados, 20000, 5000, self.catalogo)
        self.assertIn("R$ 16000.00 a R$ 20000.00", prompt)
        self.assertIn("NÃO é um gasto mínimo", prompt)
        self.assertIn("não entregue por padrão", prompt)
        self.assertIn("Não use preço isolado como prova de desempenho", prompt)

    def test_prompt_separa_3000_em_2400_pc_rede_e_600_para_conjunto_perifericos(self):
        dados = {"nome": "PC", "descricao": "Jogos", "utilidade": "Jogos", "rede": {"tipo": "wifi", "possuiAcessorio": False}}
        prompt = CriarBuildService._criar_prompt(dados, 3000, 800, self.catalogo, 20,
            {"placa_video": {"modelo_informado": "RTX 4060", "especificacoes_confirmadas": {}}})
        self.assertIn("R$ 2400.00", prompt)
        self.assertIn("R$ 600.00 (20%)", prompt)
        self.assertIn('"total": 400.0', prompt)
        self.assertIn("TODOS os periféricos", prompt)
        self.assertIn("não compre outra GPU", prompt)


if __name__ == "__main__":
    unittest.main()
