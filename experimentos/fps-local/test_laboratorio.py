"""Valores sintéticos exclusivos dos testes; não são benchmarks nem dados de calibração."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from laboratorio import consultar, ler_json, validar_base, validar_consulta

CONSULTA = json.loads((Path(__file__).parent / "dados" / "consulta-exemplo.json").read_text())


def medicao(identificador="teste-sintetico-1", fps=100, low=70, metodo="media-do-1-por-cento-mais-lento"):
    return {"id": identificador, "configuracao": deepcopy(CONSULTA), "fps_medio": fps,
            "fps_1_low": low, "metodo_1_low": metodo, "duracao_s": 60,
            "fonte": {"tipo": "propria", "referencia": "Fixture sintética, não usar como benchmark",
                      "permissao": "Fixture de teste", "uso_confirmado": True, "coletado_em": "2026-10-26",
                      "sistema": "Ambiente sintético", "driver_gpu": "Driver sintético"}}


class LaboratorioTest(unittest.TestCase):
    def test_sem_dados_nao_inventa_fps(self):
        resultado = consultar({"versao": 1, "medicoes": []}, CONSULTA)
        self.assertEqual(resultado["status"], "dados-insuficientes")
        self.assertIsNone(resultado["fps_medio"])
        self.assertIsNone(resultado["fps_1_low"])

    def test_repeticoes_compativeis_retornam_mediana_e_faixa_observada(self):
        base = {"versao": 1, "medicoes": [medicao(), medicao("teste-sintetico-2", 120, 90)]}
        copia = deepcopy(base)
        resultado = consultar(base, CONSULTA)
        self.assertEqual((resultado["fps_medio"], resultado["fps_1_low"]), (110, 80))
        self.assertEqual(resultado["faixa_observada"], [100, 120])
        self.assertEqual(resultado["amostras"], 2)
        self.assertEqual(base, copia)

    def test_nao_transfere_fps_entre_hardware_versoes_ou_ajustes(self):
        base = {"versao": 1, "medicoes": [medicao()]}
        for campo, valor in (("cpu", "outra-cpu"), ("gpu", "rtx-3060-8gb"), ("ram_gb", 32),
                             ("ram_pentes", 1), ("ram_mts", 3600), ("qualidade", "low"),
                             ("resolucao", "1440p"), ("api_grafica", "dx12"), ("cenario", "outra-cena"),
                             ("versao_jogo", "outro-patch"), ("jogo", "cs2")):
            with self.subTest(campo=campo):
                self.assertEqual(consultar(base, {**CONSULTA, campo: valor})["status"], "dados-insuficientes")

    def test_1_low_nao_e_derivado_da_media_ou_misturado_entre_metodos(self):
        for segunda in (medicao("teste-sintetico-2", low=None), medicao("teste-sintetico-2", low=None, metodo=[]),
                        medicao("teste-sintetico-2", metodo="outro-metodo")):
            with self.subTest(segunda=segunda):
                self.assertIsNone(consultar({"versao": 1, "medicoes": [medicao(), segunda]}, CONSULTA)["fps_1_low"])

    def test_origem_sem_confirmacao_ou_data_invalida_nao_entra_na_base(self):
        for campo, valor in (("uso_confirmado", False), ("permissao", ""), ("coletado_em", "2026-02-30"), ("coletado_em", "20261026"),
                             ("driver_gpu", ""), ("sistema", ""), ("tipo", "raspagem-nao-revisada")):
            with self.subTest(campo=campo):
                item = medicao()
                item["fonte"][campo] = valor
                with self.assertRaises(ValueError):
                    validar_base({"versao": 1, "medicoes": [item]})

    def test_ids_duplicados_e_numeros_invalidos_sao_rejeitados(self):
        with self.assertRaises(ValueError):
            validar_base({"versao": 1, "medicoes": [medicao(), medicao()]})
        for campo, valor in (("fps_medio", True), ("fps_medio", float("inf")), ("fps_medio", 0),
                             ("fps_1_low", float("nan")), ("fps_1_low", 101), ("duracao_s", -1)):
            with self.subTest(campo=campo, valor=valor):
                with self.assertRaises(ValueError):
                    validar_base({"versao": 1, "medicoes": [{**medicao(), campo: valor}]})

    def test_primeira_fase_nao_mistura_ray_tracing_upscaling_ou_quadros_gerados(self):
        for campo, valor in (("ray_tracing", True), ("frame_generation", True), ("upscaling", "dlss-quality"),
                             ("ram_gb", True), ("ray_tracing", 0), ("campo-desconhecido", 1)):
            with self.subTest(campo=campo):
                with self.assertRaises(ValueError):
                    validar_consulta({**CONSULTA, campo: valor})

    def test_leitura_json_recusa_nan(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "invalido.json"
            caminho.write_text('{"fps_medio": NaN}')
            with self.assertRaises(ValueError):
                ler_json(caminho)


if __name__ == "__main__":
    unittest.main()
