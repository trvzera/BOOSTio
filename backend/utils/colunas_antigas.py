"""Colunas que as tabelas de peças ainda guardam na fase 1 da migração para ofertas.

O model não as mapeia mais; elas permanecem como cópia de segurança até o comando da fase 2.
Verificações de esquema devem ignorá-las, em vez de tratar o banco como incompatível.
"""
COLUNAS_ANTIGAS_DA_PECA = frozenset({'preco', 'esgotado', 'preco_atualizado_em', 'kabum_external'})
