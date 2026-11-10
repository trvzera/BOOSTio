"""Mínimos para candidatura. Identidade e compatibilidade final são verificações distintas."""
from .conferir_especificacoes_service import ESSENCIAIS

DISPENSAVEIS = {
    'memoria_ram': {'latencia'}, 'hd': {'velocidade_rpm'},
    'fan': {'iluminacao'}, 'air_cooler': {'iluminacao'},
    'water_cooler': {'iluminacao'}, 'monitor': {'tipo_painel'},
}
MINIMOS = {categoria: tuple(c for c in campos if c not in DISPENSAVEIS.get(categoria,set()))
           for categoria,campos in ESSENCIAIS.items()}
CONSUMO_CONFIRMADO = {'processador','placa_video'}
