"""Permite fichas técnicas parciais sem apagar dados e sem liberar para builds."""
from models.campos_tecnicos import CAMPOS_CATALOGO_PARCIAL
from .catalogo_tecnico import preparar_catalogo_tecnico


def preparar_catalogo_parcial(*, simular=True):
    return preparar_catalogo_tecnico(simular=simular,
        campos_por_tabela=CAMPOS_CATALOGO_PARCIAL)
