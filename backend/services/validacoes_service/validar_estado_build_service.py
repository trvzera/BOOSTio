"""Valida o estado editável; não exige uma configuração completa de IA."""
from models.build_salva import MODELOS, MULTIPLAS
from utils.aparencia import validar_aparencia


def validar_estado(dados):
    if not isinstance(dados, dict):
        raise ValueError("Envie uma build válida")
    titulo = dados.get("titulo")
    if not isinstance(titulo, str) or not titulo.strip() or len(titulo) > 100:
        raise ValueError("Informe um nome de até 100 caracteres")
    descricao = dados.get("descricao", "")
    if not isinstance(descricao, str) or len(descricao) > 300:
        raise ValueError("Descrição inválida")
    if dados.get("visibilidade", "privado") not in ("privado", "publico"):
        raise ValueError("Visibilidade inválida")
    componentes = dados.get("componentes", {})
    if not isinstance(componentes, dict) or set(componentes) - set(MODELOS):
        raise ValueError("Categoria de peça inválida")
    limpos = {}
    for tipo, selecao in componentes.items():
        itens = selecao if isinstance(selecao, list) else [selecao]
        if not itens or len(itens) > (64 if tipo in MULTIPLAS else 1):
            raise ValueError("Quantidade de modelos inválida")
        tratados = []
        for item in itens:
            if not isinstance(item, dict):
                raise ValueError("Componente inválido")
            quantidade = item.get("quantidade", 1)
            if type(quantidade) is not int or not 1 <= quantidade <= (64 if tipo in MULTIPLAS else 1):
                raise ValueError("Quantidade inválida")
            if "id" in item:
                try:
                    peca_id = int(str(item["id"]).split(":")[-1])
                except ValueError:
                    raise ValueError("ID de peça inválido") from None
                if MODELOS[tipo].buscar_publicada_por_id(peca_id) is None:
                    raise ValueError("Peça não encontrada no catálogo")
                tratados.append({"id": peca_id, "quantidade": quantidade})
            elif isinstance(item.get("proprio"), str) and 0 < len(item["proprio"].strip()) <= 120:
                tratados.append({"proprio": item["proprio"].strip(), "quantidade": quantidade})
            else:
                raise ValueError("Componente inválido")
        limpos[tipo] = tratados if tipo in MULTIPLAS else tratados[0]
    orcamento = dados.get("orcamento")
    if orcamento is not None and (type(orcamento) not in (int, float) or not 0 <= orcamento <= 1000000):
        raise ValueError("Orçamento inválido")
    percentual = dados.get("percentualPerifericos", 0)
    if type(dados.get("substituirFansWaterCooler", False)) is not bool:
        raise ValueError("Opção de substituição das fans inválida")
    if type(percentual) is not int or not 0 <= percentual <= 99:
        raise ValueError("A porcentagem para periféricos deve ser de 0 a 99")
    pecas_extras = dados.get("pecasExtras", {})
    if not isinstance(pecas_extras, dict) or set(pecas_extras) - {"webcam", "microfone"}:
        raise ValueError("Peça própria extra inválida")
    if any(not isinstance(nome, str) or not nome.strip() or len(nome.strip()) > 120 for nome in pecas_extras.values()):
        raise ValueError("Modelo de peça própria extra inválido")
    return {
        "titulo": titulo.strip(), "descricao": descricao.strip(), "visibilidade": dados.get("visibilidade", "privado"),
        "travada": bool(dados.get("travada", False)), "orcamento": orcamento,
        "incluirPerifericos": bool(dados.get("incluirPerifericos", False)),
        "percentualPerifericos": percentual,
        "aparencia": validar_aparencia(dados.get("aparencia")),
        "substituirFansWaterCooler": dados.get("substituirFansWaterCooler", False),
        "incluirRede": bool(dados.get("incluirRede", False)), "rede": dados.get("rede") or {},
        "pecasExtras": {tipo: nome.strip() for tipo, nome in pecas_extras.items()},
        "componentes": limpos,
    }
