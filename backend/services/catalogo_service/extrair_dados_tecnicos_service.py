from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, Float, String

from .conferir_especificacoes_service import converter, valores, consolidar_interfaces
from .normalizar_especificacoes import CONJUNTOS, agregar


class ExtrairDadosTecnicosService:
    CAMPOS = {
        'capacidade_gb', 'memoria_gb', 'ddr', 'tipo_memoria', 'frequencia_mhz',
        'quantidade_pentes', 'latencia', 'formato_ram', 'formato', 'tipo',
        'interface', 'velocidade_rpm', 'memoria_cache_mb', 'potencia_w',
        'dpi_max', 'conexao', 'chipset', 'socket', 'soquete', 'nucleo', 'thread',
        'tamanho_polegadas', 'resolucao', 'taxa_atualizacao_hz', 'tipo_painel',
        'tipo_fone', 'microfone', 'mecanico', 'layout', 'switch', 'tamanho_mm',
        'quantidade', 'compatibilidade', 'tamanho_radiador_mm',
        'formatos_placa_mae', 'tamanho_max_gpu_mm', 'tamanho_max_cooler_mm',
        'velocidade_mbps', 'bluetooth', 'comprimento_m', 'categoria_cabo',
        'clockbase', 'clockmax', 'consumo_energia', 'consumo_w', 'videointegrado', 'cooler',
        'conector', 'iluminacao', 'quantidade_slots_ram', 'memoria_maxima_gb',
        'quantidade_slots_m2', 'slots_expansao', 'fans_inclusos',
    }

    def executar(self, modelo, produto):
        dados, fontes, conflitos = {}, {}, []
        for chave in sorted(self.CAMPOS & produto.especificacoes.keys()):
            campo = {'formato_ram':'formato', 'tipo_fone':'tipo', 'categoria_cabo':'categoria'}.get(chave, chave)
            if campo not in modelo.__table__.columns:
                continue
            brutos = valores(produto.especificacoes[chave])
            if not brutos:
                continue
            convertidos = {converter(chave, v) for v in brutos}
            if chave == 'interface':
                convertidos = consolidar_interfaces(convertidos)
            if chave in CONJUNTOS:
                convertidos = {agregar(convertidos)}
            if None in convertidos:
                continue
            if len(convertidos) != 1:
                conflitos.append('atributos_tecnicos_divergentes:' + campo)
                continue
            valor = next(iter(convertidos))
            tipo = modelo.__table__.columns[campo].type
            if isinstance(tipo, Boolean):
                if type(valor) is not bool:
                    continue
            elif isinstance(tipo, (Integer, Numeric, Float)):
                try:
                    n = Decimal(str(valor))
                    if not n.is_finite() or n <= 0 or isinstance(tipo, Integer) and n != int(n):
                        continue
                    valor = int(n) if isinstance(tipo, Integer) else float(n)
                except (ValueError, ArithmeticError):
                    continue
            elif isinstance(tipo, String):
                valor = str(valor)
                if chave == 'compatibilidade':
                    valor = ', '.join(v for v in valor.split('|') if not v.startswith('familia:'))
                if not valor or tipo.length and len(valor) > tipo.length:
                    continue
            dados[campo] = valor
            fontes[campo] = dict(url=produto.fonte, campo_normalizado=chave, valores=brutos)
        return dict(dados=dados, fontes=fontes, conflitos=conflitos)
