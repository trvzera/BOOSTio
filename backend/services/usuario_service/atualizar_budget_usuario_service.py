from decimal import Decimal

from models import Usuario


class AtualizarBudgetUsuarioService:
    def executar(self, usuario_id: int, dados: dict) -> dict | None:
        if not isinstance(dados, dict) or set(dados) != {"budget", "usar_budget"}:
            raise ValueError("Informe apenas budget e usar_budget.")

        usar_budget = dados["usar_budget"]
        if not isinstance(usar_budget, bool):
            raise ValueError("A autorização de uso do budget deve ser verdadeira ou falsa.")

        budget = self._validar_budget(dados["budget"], usar_budget)

        usuario = Usuario.buscar_por_id(usuario_id)
        if usuario is None:
            return None
        usuario.atualizar_budget(budget, usar_budget)
        return usuario.to_dict(incluir_budget=True)

    @staticmethod
    def _validar_budget(valor, usar_budget):
        budget = None
        if valor is not None:
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise ValueError("Informe um budget numérico ou nulo para removê-lo.")
            budget = Decimal(str(valor))
            if not budget.is_finite() or not 0 <= budget <= 1000000:
                raise ValueError("Informe um budget entre R$ 0 e R$ 1.000.000.")
            if budget != budget.quantize(Decimal("0.01")):
                raise ValueError("Informe no máximo duas casas decimais no budget.")

        if usar_budget and (budget is None or budget <= 0):
            raise ValueError("Informe um budget maior que zero para usá-lo nas novas configurações.")

        return budget
