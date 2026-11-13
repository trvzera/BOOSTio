from copy import deepcopy

from services.build_service.ajustar_perifericos_ao_plano_service import AjustarPerifericosAoPlanoService

TIPOS = ("monitor", "teclado", "mouse", "fone")


def componentes(ids):
    return [{"tipo": tipo, "id": ids[tipo], "quantidade": 1} for tipo in TIPOS]


def catalogo():
    return {tipo: [{"id": 1, "preco": 50}, {"id": 2, "preco": 150}, {"id": 3, "preco": 80}] for tipo in TIPOS}


def plano(*conjuntos, teto=1000):
    return {"viavel": True, "teto": teto, "combinacoes": [
        {"total": sum(150 if i == 2 else 80 if i == 3 else 50 for i in c.values()), "componentes": componentes(c)}
        for c in conjuntos]}


def build(ids):
    return {"nome": "PC", "componentes": [{"tipo": "processador", "id": 1, "quantidade": 1}, *componentes(ids)]}


def ids_dos_perifericos(resultado):
    return {i["tipo"]: i["id"] for i in resultado["componentes"] if i["tipo"] in TIPOS}


def test_conjunto_do_plano_nao_e_alterado():
    entrada = build(dict.fromkeys(TIPOS, 1))
    saida, diagnostico = AjustarPerifericosAoPlanoService().executar(
        entrada, plano(dict.fromkeys(TIPOS, 2), dict.fromkeys(TIPOS, 1)), catalogo())
    assert saida is entrada and diagnostico is None


def test_fora_do_plano_e_gastando_pouco_usa_a_melhor_combinacao():
    entrada = build(dict.fromkeys(TIPOS, 1))
    antes = deepcopy(entrada)
    saida, diagnostico = AjustarPerifericosAoPlanoService().executar(
        entrada, plano(dict.fromkeys(TIPOS, 2), dict.fromkeys(TIPOS, 3)), catalogo())
    assert ids_dos_perifericos(saida) == dict.fromkeys(TIPOS, 2)
    assert saida["componentes"][0] == {"tipo": "processador", "id": 1, "quantidade": 1}
    assert diagnostico["gasto_anterior"] == 200 and diagnostico["gasto_novo"] == 600 and diagnostico["reserva"] == 1000
    assert entrada == antes


def test_fora_do_plano_mas_gastando_perto_da_reserva_e_mantido():
    entrada = build({"monitor": 2, "teclado": 2, "mouse": 2, "fone": 1})
    saida, diagnostico = AjustarPerifericosAoPlanoService().executar(
        entrada, plano(dict.fromkeys(TIPOS, 2), dict.fromkeys(TIPOS, 3), teto=700), catalogo())
    assert saida is entrada and diagnostico is None


def test_peca_inexistente_no_catalogo_fica_para_a_validacao_normal():
    entrada = build({"monitor": 99, "teclado": 1, "mouse": 1, "fone": 1})
    saida, diagnostico = AjustarPerifericosAoPlanoService().executar(
        entrada, plano(dict.fromkeys(TIPOS, 2)), catalogo())
    assert saida is entrada and diagnostico is None


def test_periferico_omitido_pela_ia_e_completado_pelo_plano():
    entrada = build(dict.fromkeys(TIPOS, 1))
    entrada["componentes"] = [i for i in entrada["componentes"] if i["tipo"] != "fone"]
    saida, diagnostico = AjustarPerifericosAoPlanoService().executar(
        entrada, plano(dict.fromkeys(TIPOS, 2)), catalogo())
    assert ids_dos_perifericos(saida) == dict.fromkeys(TIPOS, 2) and diagnostico


def test_sem_plano_ou_plano_inviavel_nada_muda():
    entrada = build(dict.fromkeys(TIPOS, 1))
    servico = AjustarPerifericosAoPlanoService()
    assert servico.executar(entrada, None, catalogo()) == (entrada, None)
    assert servico.executar(entrada, {"viavel": False, "combinacoes": []}, catalogo()) == (entrada, None)
    assert servico.executar(entrada, {"viavel": True, "teto": 1000, "combinacoes": []}, catalogo()) == (entrada, None)


def test_pecas_proprias_ficam_fora_do_plano_e_nao_sao_tocadas():
    sem_monitor = {"viavel": True, "teto": 1000, "combinacoes": [
        {"total": 450, "componentes": [{"tipo": t, "id": 2, "quantidade": 1} for t in ("teclado", "mouse", "fone")]}]}
    entrada = build(dict.fromkeys(TIPOS, 1))
    saida, _ = AjustarPerifericosAoPlanoService().executar(entrada, sem_monitor, catalogo())
    resultado = ids_dos_perifericos(saida)
    assert resultado["monitor"] == 1 and resultado["teclado"] == resultado["mouse"] == resultado["fone"] == 2
