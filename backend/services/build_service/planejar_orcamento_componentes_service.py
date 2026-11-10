"""Estimativas de busca; a aprovação da build continua no validador final."""
from decimal import Decimal, ROUND_DOWN

from utils.memorias import normalizar_ddr
from utils.sockets import normalizar_socket, suporte_socket_cooler
from .preferencias_perifericos_service import PreferenciasPerifericosService
from .planejar_armazenamento_service import PlanejarArmazenamentoService


class PlanejarOrcamentoComponentesService:
    PERFIS = {
        'jogos': {'processador': '.22', 'placa_video': '.50', 'placa_mae': '.14', 'memoria_ram': '.16', 'plataforma': '.48'},
        'trabalho-pesado': {'processador': '.35', 'placa_video': '.35', 'placa_mae': '.18', 'memoria_ram': '.24', 'plataforma': '.65'},
        'leve': {'processador': '.30', 'placa_video': '.18', 'placa_mae': '.18', 'memoria_ram': '.20', 'plataforma': '.62'},
        'equilibrado': {'processador': '.28', 'placa_video': '.40', 'placa_mae': '.16', 'memoria_ram': '.18', 'plataforma': '.56'},
    }

    @staticmethod
    def preco(peca):
        return Decimal(str(peca.get('preco', 0)))

    @classmethod
    def perfil(cls, uso):
        if not uso:
            return 'nao-informado'
        if PreferenciasPerifericosService.jogos(uso):
            return 'jogos'
        texto = uso.casefold()
        if any(t in texto for t in ('pesado', 'render', 'servidor', 'nas')):
            return 'trabalho-pesado'
        if any(t in texto for t in ('estudo', 'casual', 'escritorio', 'escritório')):
            return 'leve'
        return 'equilibrado'

    def executar(self, contexto, pools):
        pc = Decimal(str(contexto['teto_pc']))
        absoluto = Decimal(str(contexto['teto_peca']))
        perfil = self.perfil(contexto['utilidade'])
        avisos = []
        reserva, pendencias = self._reserva_basica(contexto, pools)
        avisos.extend(pendencias)
        gpu_minimo = min((self.preco(p) for p in pools.get('placa_video', [])), default=Decimal(0))
        propria_gpu = 'placa_video' in contexto['proprias']
        exige_gpu = perfil == 'jogos' and not propria_gpu
        estimativas = {}
        cpus = pools.get('processador', [])
        cpu_propria = contexto['detalhes_proprias'].get('processador', {}).get('especificacoes_confirmadas')
        if cpu_propria:
            cpus = [{**cpu_propria, 'id': 'proprio', 'preco': 0}]
        for cpu in cpus:
            plataforma = self._plataforma_minima(cpu, contexto, pools)
            if plataforma is None:
                estimativas[cpu['id']] = None
                continue
            restante = pc - reserva - plataforma
            estimativas[cpu['id']] = {'plataforma_minima': float(plataforma),
                                      'disponivel_gpu': float(max(Decimal(0), restante)),
                                      'viavel': restante >= (gpu_minimo if exige_gpu else 0)}
        if any(v is None for v in estimativas.values()):
            avisos.append('Há CPUs sem plataforma mínima confirmável com os dados do catálogo.')
        tetos = {}
        if perfil != 'nao-informado':
            pesos = {k: Decimal(v) for k, v in self.PERFIS[perfil].items()}
            pesos.update({"ssd": Decimal('.12'), "hd": Decimal('.12'), "fonte": Decimal('.10'),
                          "gabinete": Decimal('.08'), "air_cooler": Decimal('.05'),
                          "water_cooler": Decimal('.08'), "fan": Decimal('.02'),
                          "adaptador_wifi": Decimal('.06'), "cabo_rede": Decimal('.03')})
            if pc <= 4000:
                pesos['processador'] += Decimal('.04')
                pesos['placa_video'] -= Decimal('.06')
                pesos['plataforma'] += Decimal('.06')
            elif pc > 10000:
                pesos['processador'] -= Decimal('.02')
                pesos['placa_video'] += Decimal('.04')
                pesos['plataforma'] -= Decimal('.02')
            if contexto['prioridade'] == 'custo_beneficio':
                pesos['processador'] *= Decimal('.90')
                pesos['placa_video'] *= Decimal('.90')
            if 'processador' in contexto['proprias'] and perfil == 'jogos':
                pesos['placa_video'] += Decimal('.08')
            tetos = {tipo: float(min(absoluto, (pc * peso).quantize(Decimal('.01'), rounding=ROUND_DOWN)))
                     for tipo, peso in pesos.items() if tipo != 'plataforma'}
            plataforma_alvo = float((pc * pesos['plataforma']).quantize(Decimal('.01'), rounding=ROUND_DOWN))
        else:
            plataforma_alvo = float(pc)
        return {'escopo': 'estimativas mínimas de preço; não certificam BIOS, encaixe ou refrigeração',
                'perfil': perfil, 'teto_pc': float(pc), 'reserva_basica_estimada': float(reserva),
                'meta_plataforma': plataforma_alvo, 'tetos_sugeridos': tetos,
                'estimativas_cpu': estimativas, 'avisos': avisos, 'flexibilizacoes': []}

    def _reserva_basica(self, contexto, pools):
        total, pendencias = Decimal(0), []
        proprias = contexto['proprias']
        for tipo in ('fonte', 'gabinete'):
            if tipo in proprias:
                continue
            itens = pools.get(tipo, [])
            if itens:
                total += min(self.preco(p) for p in itens)
            else:
                pendencias.append(f'Sem {tipo} disponível para estimar o custo mínimo do conjunto.')
        if not {'ssd', 'hd'} & proprias.keys():
            referencia = PlanejarArmazenamentoService().executar(pools, contexto['armazenamento_minimo_gb'] or 1)
            if referencia:
                total += Decimal(str(referencia['custo']))
            else:
                pendencias.append('Sem armazenamento com capacidade conhecida para estimar o requisito solicitado.')
        elif contexto['armazenamento_minimo_gb'] is not None:
            confirmado = sum((Decimal(str(d.get('especificacoes_confirmadas', {}).get('capacidade_gb') or 0))
                              for tipo, d in contexto['detalhes_proprias'].items() if tipo in ('ssd', 'hd')), Decimal(0))
            if confirmado < contexto['armazenamento_minimo_gb']:
                pendencias.append('O armazenamento próprio não confirma a capacidade mínima pedida; revise o reaproveitamento.')
        rede = contexto['rede']
        acessorio = {'wifi': 'adaptador_wifi', 'cabo': 'cabo_rede'}.get(rede.get('tipo'))
        if acessorio and rede.get('possuiAcessorio') is False and acessorio not in proprias:
            if pools.get(acessorio):
                total += min(self.preco(p) for p in pools[acessorio])
            else:
                pendencias.append('Sem acessório de rede adequado para estimar o custo mínimo.')
        return total, pendencias

    def _plataforma_minima(self, cpu, contexto, pools):
        detalhes = contexto['detalhes_proprias']
        placa_propria = detalhes.get('placa_mae', {}).get('especificacoes_confirmadas')
        placas = [{**placa_propria, 'preco': 0}] if placa_propria else pools.get('placa_mae', [])
        socket = normalizar_socket(cpu.get('soquete'))
        pares = []
        for placa in placas:
            if not socket or normalizar_socket(placa.get('socket')) != socket:
                continue
            ddr = normalizar_ddr(placa.get('tipo_memoria'))
            if 'memoria_ram' in contexto['proprias']:
                ram = detalhes.get('memoria_ram', {}).get('especificacoes_confirmadas', {})
                if ram and ddr and normalizar_ddr(ram.get('ddr')) != ddr:
                    continue
                custo_ram = Decimal(0)
            else:
                memorias = [p for p in pools.get('memoria_ram', []) if ddr and normalizar_ddr(p.get('ddr')) == ddr]
                if not memorias:
                    continue
                custo_ram = min(self.preco(p) for p in memorias)
            pares.append(self.preco(cpu) + self.preco(placa) + custo_ram)
        if not pares:
            return None
        cooler = Decimal(0)
        if not cpu.get('cooler') and not {'air_cooler', 'water_cooler'} & contexto['proprias'].keys():
            opcoes = [p for tipo in ('air_cooler', 'water_cooler') for p in pools.get(tipo, [])
                      if suporte_socket_cooler(cpu.get('soquete'), p) is not False]
            if not opcoes:
                return None
            cooler = min(self.preco(p) for p in opcoes)
        return min(pares) + cooler
