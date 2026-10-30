from models.medidas_fisicas import produto_kabum
from .pecas_complementares import pecas_complementares


class CadastrarComplementaresService:
    def executar(self, simular=False):
        resumo = {"simulacao": simular, "inseridas": 0, "existentes": 0, "categorias": {}}
        for classe, itens in pecas_complementares().items():
            existentes = classe.mostrar_pecas()
            numeros = {p.part_number for p in existentes if p.part_number}
            produtos = {produto_kabum(p.kabum_external) for p in existentes} - {None}
            novos = [item for item in itens if item["part_number"] not in numeros
                     and (produto_kabum(item["kabum_external"]) is None
                          or produto_kabum(item["kabum_external"]) not in produtos)]
            inseridas = len(novos) if simular else classe.cadastrar_ausentes(novos)
            resumo["categorias"][classe.__tablename__] = {
                "a_inserir" if simular else "inseridas": inseridas,
                "existentes": len(itens) - len(novos),
            }
            resumo["inseridas"] += 0 if simular else inseridas
            resumo["existentes"] += len(itens) - len(novos)
        return resumo
