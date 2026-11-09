"""Contrato interno: adaptadores de lojas traduzem suas respostas para estes campos."""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProdutoNormalizado:
    loja: str
    id_externo: str
    categoria: str | None
    titulo: str
    marca: str | None = None
    modelo: str | None = None
    modelos_alternativos: tuple[str, ...] = ()
    especificacoes: dict[str, Any] = field(default_factory=dict)
    identificadores: dict[str, Any] = field(default_factory=dict)
    ativo: bool | None = None
    categoria_confirmada: bool = False
    fonte: str | None = None
    contexto: dict[str, Any] = field(default_factory=dict)
