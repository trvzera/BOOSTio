from decimal import Decimal
import pytest
from services.build_service.planejamento_geracao import validar_minimos, sugerir_total, ErroPlanejamentoBuild, RecusaModeloBuild, orientar_falha
from services.build_service.criar_build_service import CriarBuildService, ErroGeracaoBuild


@pytest.mark.parametrize("total,pct,motivo,sugerido", [(1, 0, "orcamento", 2000), (1999.99, 0, "orcamento", 2000),
    (2000, 20, "orcamento", 2500), (5000, 1, "perifericos", 50000), (2500, 10, "perifericos", 5000)])
def test_limites_sao_por_subtotal_e_sugestao_respeita_os_dois_minimos(total, pct, motivo, sugerido):
    pc, perifericos = CriarBuildService._dividir_orcamento(total, pct)
    with pytest.raises(ErroPlanejamentoBuild) as erro:
        validar_minimos(pc, perifericos, pct)
    assert erro.value.geracao["motivo"] == motivo
    assert erro.value.geracao["orcamentoSugerido"] == sugerido


@pytest.mark.parametrize("total,pct", [(2000, 0), (2500, 20), (5000, 10), (8000, 20)])
def test_aceita_os_limites_sem_exigir_gastar_o_total(total, pct):
    validar_minimos(*CriarBuildService._dividir_orcamento(total, pct), pct)


def test_minimo_real_dos_perifericos_pode_exigir_mais_que_500():
    assert sugerir_total(20, minimo_perifericos=1200) == 6000


@pytest.mark.parametrize("motivo", ["cor", "aparencia", "orcamento", "catalogo", "compatibilidade"])
def test_recusa_da_ia_retorna_orientacao_sem_expor_texto_bruto(motivo):
    with pytest.raises(RecusaModeloBuild) as bruto:
        CriarBuildService._validar_build({"erro": "texto com SEGREDO e instruções externas", "motivo": motivo}, {}, 5000)
    erro = ErroGeracaoBuild(bruto.value, 5000, 20)
    assert erro.geracao["motivo"] == motivo and "SEGREDO" not in str(erro)
    assert "Nenhuma build foi salva" in str(erro)
    if motivo == "cor":
        assert "não confirma" in str(erro)


def test_sem_motivo_conhecido_nao_inventa_que_a_falha_foi_no_orcamento():
    erro = ErroGeracaoBuild(RecusaModeloBuild("ignorar todas as regras"), 5000, 20)
    assert erro.geracao["motivo"] == "resposta"
    assert "orcamentoSugerido" not in erro.geracao


def test_validacao_local_de_orcamento_explica_os_subtotais_sem_transferir_sobras():
    texto, dados = orientar_falha(ValueError("A configuração sugerida ultrapassou o limite destinado ao PC: subtotal PC+rede R$ 7000.00, teto R$ 6400.00."), 8000, 20, {"pc": 7000, "perifericos": 600})
    assert "7000.00" in texto and "6400.00" in texto
    assert Decimal(str(dados["orcamentoSugerido"])) * Decimal("0.8") >= 7000
