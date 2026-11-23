"""Grava em build_salva a build que a IA gerou, junto com as peças que o usuário já tem."""
from models import BuildSalva
from models.build_salva import MODELOS, MULTIPLAS
from services.validacoes_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService
from services.validacoes_service.validar_estado_build_service import validar_estado

PERIFERICOS_DO_ESTADO = ("monitor", "teclado", "mouse", "fone")


def salvar_build(usuario_id, build, pedido):
  componentes = {}
  for tipo, nome in pedido["proprias"].items():
    if tipo in MODELOS:
      item = {"proprio": nome, "quantidade": 1}
      componentes[tipo] = [item] if tipo in MULTIPLAS else item
  for item in build["componentes"]:
    selecao = {"id": item["id"], "quantidade": item["quantidade"]}
    componentes[item["tipo"]] = [selecao] if item["tipo"] in MULTIPLAS else selecao

  estado = validar_estado({
    "titulo": build["nome"][:100], "descricao": build["descricao"][:300],
    "orcamento": pedido["orcamento"], "componentes": componentes, "rede": pedido["rede"],
    "incluirRede": pedido["rede"].get("tipo") in ("cabo", "wifi", "ambos"),
    "incluirPerifericos": pedido["percentual"] > 0 or any(tipo in componentes for tipo in PERIFERICOS_DO_ESTADO),
    "percentualPerifericos": pedido["percentual"],
    "aparencia": pedido["aparencia"],
    "pecasExtras": {tipo: nome for tipo, nome in pedido["proprias"].items() if tipo not in MODELOS},
  })
  return AvaliarCompatibilidadeService().para_resposta(BuildSalva.criar_limitada(usuario_id, estado))
