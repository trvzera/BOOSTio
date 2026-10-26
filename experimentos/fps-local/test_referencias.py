"""Contratos com números sintéticos. Nenhuma chamada real, licença ou FPS confirmado."""
from copy import deepcopy
import unittest

from laboratorio import validar_base
from referencias import normalizar_referencia

FPSHQ = {"game": "valorant", "cpu": "ryzen-5-5600", "gpu": "rtx-3060", "res": "1080p", "preset": "high"}
HMF = {"game": "Valorant", "cpu": "Ryzen 5 5600", "gpu": "RTX 3060", "resolution": "1920x1080", "upscaling": "Native"}


def resposta_fpshq():
    return {"ok": True, **{campo: {"slug": FPSHQ[campo]} for campo in ("game", "cpu", "gpu")},
            "res": "1080p", "preset": "high", "fps": 100, "low1": 70, "source": "model", "basis": "model"}


class ReferenciasTest(unittest.TestCase):
    def test_fpshq_modelado_nao_vira_medicao(self):
        resposta = resposta_fpshq()
        copia = deepcopy(resposta)
        resultado = normalizar_referencia("fpshq", FPSHQ, resposta)
        self.assertEqual(resultado["origem_declarada"], "model")
        self.assertEqual(resultado["consulta_confirmada_no_retorno"], FPSHQ)
        self.assertFalse(resultado["pronta_para_calibracao"])
        self.assertEqual(resultado["direitos_de_armazenamento_e_treinamento"], "nao-verificados")
        self.assertEqual(resposta, copia)

    def test_fpshq_rejeita_hardware_e_ajustes_divergentes(self):
        for campo, valor in (("gpu", {"slug": "outra-gpu"}), ("res", "1440p"), ("preset", "low"), ("ok", False)):
            with self.subTest(campo=campo):
                with self.assertRaises(ValueError):
                    normalizar_referencia("fpshq", FPSHQ, {**resposta_fpshq(), campo: valor})

    def test_declaracao_measured_nao_completa_contexto_ausente(self):
        resultado = normalizar_referencia("fpshq", FPSHQ, {**resposta_fpshq(), "source": "measured", "basis": "measured"})
        self.assertEqual(resultado["origem_declarada"], "measured")
        self.assertIn("ram_gb", resultado["contexto_nao_confirmado"])
        self.assertFalse(resultado["pronta_para_calibracao"])

    def test_howmanyfps_exemplo_publico_nao_confirma_preset_ram_ou_modelos(self):
        resultado = normalizar_referencia("howmanyfps", HMF, {"avgFps": 100, "min1Fps": 70, "segredo": "nao-copiar"})
        self.assertEqual(resultado["fps_medio"], 100)
        self.assertIsNone(resultado["consulta_confirmada_no_retorno"])
        self.assertEqual(resultado["origem_declarada"], "unknown")
        self.assertNotIn("preset", resultado["consulta_solicitada"])
        self.assertIn("qualidade", resultado["contexto_nao_confirmado"])
        self.assertIn("gpu_vram_gb", resultado["contexto_nao_confirmado"])
        self.assertNotIn("segredo", resultado)
        self.assertFalse(resultado["pronta_para_calibracao"])

    def test_sem_1_low_nao_deduz_valor(self):
        for provedor, consulta, resposta in (("fpshq", FPSHQ, {**resposta_fpshq(), "low1": None}),
                                            ("howmanyfps", HMF, {"avgFps": 100})):
            with self.subTest(provedor=provedor):
                self.assertIsNone(normalizar_referencia(provedor, consulta, resposta)["fps_1_low"])

    def test_html_erro_metricas_invalidas_e_upscaling_sao_rejeitados(self):
        for resposta in ("<html>hospedagem inativa</html>", {"erro": "sem acesso"}, {"avgFps": True},
                         {"avgFps": float("nan")}, {"avgFps": 100, "min1Fps": 120}):
            with self.subTest(resposta=resposta):
                with self.assertRaises(ValueError):
                    normalizar_referencia("howmanyfps", HMF, resposta)
        with self.assertRaises(ValueError):
            normalizar_referencia("howmanyfps", {**HMF, "upscaling": "DLSS"}, {"avgFps": 100})

    def test_referencia_externa_nao_e_aceita_na_base_de_medicoes(self):
        referencia = normalizar_referencia("howmanyfps", HMF, {"avgFps": 100})
        with self.assertRaises(ValueError):
            validar_base({"versao": 1, "medicoes": [referencia]})


if __name__ == "__main__":
    unittest.main()
