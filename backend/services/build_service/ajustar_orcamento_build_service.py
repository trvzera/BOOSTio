from copy import deepcopy
from decimal import Decimal
from math import isfinite
import re

from utils.memorias import normalizar_ddr
from .preferencias_cores_service import PreferenciasCoresService


class AjustarOrcamentoBuildService:
    AJUSTAVEIS = ('memoria_ram', 'ssd', 'hd', 'fan')
    PERIFERICOS = frozenset(('monitor', 'teclado', 'mouse', 'fone'))
    MAX_OPCOES = 12
    MAX_ESTADOS = 256

    @staticmethod
    def numero(valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float, Decimal)) or not isfinite(valor):
            return None
        return Decimal(str(valor))

    @classmethod
    def custos(cls, build, catalogo):
        if not isinstance(build, dict) or not isinstance(build.get('componentes'), list):
            return None
        subtotais = {}
        for item in build['componentes']:
            if not isinstance(item, dict):
                return None
            tipo, ident, qtd = item.get('tipo'), item.get('id'), item.get('quantidade', 1)
            if not isinstance(tipo, str) or type(ident) is not int or tipo in subtotais:
                return None
            if type(qtd) is not int or not 1 <= qtd <= 64:
                return None
            peca = next((p for p in catalogo.get(tipo, []) if p.get('id') == ident), None)
            preco = cls.numero((peca or {}).get('preco'))
            if preco is None or preco <= 0 or peca.get('esgotado') is True:
                return None
            subtotais[tipo] = preco * qtd
        return subtotais

    @classmethod
    def cabe(cls, custos, orcamento, teto_pc, teto_perifericos):
        pc = sum((v for k, v in custos.items() if k not in cls.PERIFERICOS), Decimal(0))
        perif = sum((v for k, v in custos.items() if k in cls.PERIFERICOS), Decimal(0))
        return pc + perif <= orcamento and pc <= teto_pc and perif <= teto_perifericos

    def executar(self, build, catalogo, orcamento, teto_pc, teto_perifericos, validar,
                 proprias=None, cor='sem-preferencia'):
        custos = self.custos(build, catalogo)
        if custos is None:
            return None
        orcamento, teto_pc, teto_perifericos = map(lambda x: Decimal(str(x)), (orcamento, teto_pc, teto_perifericos))
        if self.cabe(custos, orcamento, teto_pc, teto_perifericos):
            return None
        if sum((v for k, v in custos.items() if k in self.PERIFERICOS), Decimal(0)) > teto_perifericos:
            return None
        originais = {i['tipo']: next(p for p in catalogo[i['tipo']] if p['id'] == i['id']) for i in build['componentes']}
        estados = [(deepcopy(build), [], Decimal(0))]
        for item in build['componentes']:
            tipo = item['tipo']
            if tipo not in self.AJUSTAVEIS or tipo in (proprias or {}):
                continue
            opcoes = self._opcoes(item, originais[tipo], catalogo.get(tipo, []), cor)
            expandidos = {}
            for anterior, trocas, perda in estados:
                for novo, mudanca, penalidade in opcoes:
                    candidata = deepcopy(anterior)
                    alvo = next(i for i in candidata['componentes'] if i['tipo'] == tipo)
                    alvo.update(novo)
                    chave = tuple((i['tipo'], i['id'], i.get('quantidade', 1)) for i in candidata['componentes'])
                    expandidos[chave] = (candidata, [*trocas, *([mudanca] if mudanca else [])], perda + penalidade)
            estados = sorted(expandidos.values(), key=lambda e: self._ordem(e, catalogo, orcamento, teto_pc))[:self.MAX_ESTADOS]
        avaliadas = 0
        for candidata, trocas, _ in sorted(estados, key=lambda e: self._ordem(e, catalogo, orcamento, teto_pc)):
            if not trocas:
                continue
            novos_custos = self.custos(candidata, catalogo)
            if not self.cabe(novos_custos, orcamento, teto_pc, teto_perifericos):
                continue
            avaliadas += 1
            try:
                validada = validar(deepcopy(candidata))
            except ValueError:
                continue
            finais = self.custos(validada, catalogo)
            if finais is None or not self.cabe(finais, orcamento, teto_pc, teto_perifericos):
                continue
            if not self._preservou_invariantes(build, validada, catalogo):
                continue
            return {'build': validada, 'diagnostico': {
                'total_anterior': float(sum(custos.values())), 'total_final': float(sum(finais.values())),
                'economia': float(sum(custos.values()) - sum(finais.values())),
                'subtotais_anteriores': {k: float(v) for k, v in custos.items()},
                'subtotais_finais': {k: float(v) for k, v in finais.items()},
                'trocas': trocas, 'propostas_validadas': avaliadas,
                'limite_estados': self.MAX_ESTADOS,
            }}
        return None

    def _ordem(self, estado, catalogo, orcamento, teto_pc):
        build, trocas, perda = estado
        custos = self.custos(build, catalogo)
        total = sum(custos.values())
        pc = sum((v for k, v in custos.items() if k not in self.PERIFERICOS), Decimal(0))
        excesso = max(Decimal(0), total - orcamento, pc - teto_pc)
        return (excesso, len(trocas), perda, total,
                tuple((i['tipo'], i['id'], i.get('quantidade', 1)) for i in build['componentes']))

    def _opcoes(self, item, original, pecas, cor):
        tipo, qtd = item['tipo'], item.get('quantidade', 1)
        subtotal = self.numero(original['preco']) * qtd
        opcoes = [(dict(id=item['id'], quantidade=qtd), None, Decimal(0))]
        candidatas = []
        for peca in pecas:
            if type(peca.get('id')) is not int or peca['id'] == item['id'] or peca.get('esgotado') is True:
                continue
            quantidade = self._quantidade_equivalente(tipo, original, qtd, peca)
            preco = self.numero(peca.get('preco'))
            if quantidade is None or preco is None or preco <= 0 or preco * quantidade >= subtotal:
                continue
            if cor != 'sem-preferencia' and PreferenciasCoresService.prioridade(peca, cor) > PreferenciasCoresService.prioridade(original, cor):
                continue
            diferencas, perda = self._diferencas(original, peca)
            mudanca = {'tipo': tipo, 'id_anterior': item['id'], 'id_novo': peca['id'],
                       'quantidade_anterior': qtd, 'quantidade_nova': quantidade,
                       'subtotal_anterior': float(subtotal), 'subtotal_novo': float(preco * quantidade),
                       'economia': float(subtotal - preco * quantidade), 'diferencas_cadastradas': diferencas}
            candidatas.append((dict(id=peca['id'], quantidade=quantidade), mudanca, perda))
        por_preco = sorted(candidatas, key=lambda x: (x[1]['subtotal_novo'], x[0]['id']))
        por_recurso = sorted(candidatas, key=lambda x: (x[2], x[1]['subtotal_novo'], x[0]['id']))
        vistas = set()
        for a, b in zip(por_preco, por_recurso):
            for opcao in (a, b):
                chave = (opcao[0]['id'], opcao[0]['quantidade'])
                if chave not in vistas and len(opcoes) < self.MAX_OPCOES:
                    vistas.add(chave)
                    opcoes.append(opcao)
        return opcoes

    @staticmethod
    def texto(valor):
        return re.sub(r'[^a-z0-9]', '', str(valor or '').casefold())

    @classmethod
    def _classe_interface(cls, valor):
        texto = cls.texto(valor)
        if 'pcie' in texto or 'nvme' in texto:
            return 'pcie'
        if 'sata' in texto:
            return 'sata'
        return texto or None

    def _quantidade_equivalente(self, tipo, original, qtd, nova):
        if tipo == 'fan':
            campos = ('tamanho_mm', 'conector_fan', 'tensao_fan_v', 'conector_rgb', 'tensao_rgb_v')
            if original.get('tamanho_mm') is None or any(original.get(c) is not None and nova.get(c) != original[c] for c in campos):
                return None
            if (original.get('fluxo_ar') and original.get('fonte_fluxo_ar') != 'nome_comercial'
                and nova.get('fluxo_ar') != original['fluxo_ar']):
                return None
            antes, depois = original.get('quantidade'), nova.get('quantidade')
            if type(antes) is not int or type(depois) is not int or min(antes, depois) < 1:
                return None
            total = antes * qtd
            if total % depois:
                return None
            quantidade = total // depois
            for campo in ('fluxo_ar_cfm', 'pressao_estatica_mmh2o'):
                a, b = self.numero(original.get(campo)), self.numero(nova.get(campo))
                if a is not None and (b is None or b < a):
                    return None
        else:
            a, b = original.get('capacidade_gb'), nova.get('capacidade_gb')
            if type(a) is not int or type(b) is not int or min(a, b) < 1:
                return None
            quantidade = (a * qtd + b - 1) // b
            if tipo == 'memoria_ram':
                if not normalizar_ddr(original.get('ddr')) or normalizar_ddr(original.get('ddr')) != normalizar_ddr(nova.get('ddr')):
                    return None
                for campo in ('frequencia_mhz',):
                    antes, depois = self.numero(original.get(campo)), self.numero(nova.get(campo))
                    if antes is not None and (depois is None or depois < antes):
                        return None
                for campo in ('numero_pinos', 'formato'):
                    if original.get(campo) is not None and nova.get(campo) != original[campo]:
                        return None
                antes, depois = original.get('quantidade_pentes'), nova.get('quantidade_pentes')
                if type(antes) is not int or type(depois) is not int or min(antes, depois) < 1 or antes*qtd != depois*quantidade:
                    return None
                a = re.fullmatch(r'\s*CL\s*(\d+)\s*', str(original.get('latencia') or ''), re.I)
                b = re.fullmatch(r'\s*CL\s*(\d+)\s*', str(nova.get('latencia') or ''), re.I)
                if a and (not b or int(b[1]) > int(a[1])):
                    return None
            else:
                interface = self._classe_interface(original.get('interface'))
                if interface is None or interface != self._classe_interface(nova.get('interface')):
                    return None
                if original.get('formato') and self.texto(original['formato']) != self.texto(nova.get('formato')):
                    return None
        return quantidade if 1 <= quantidade <= 64 else None

    def _diferencas(self, original, nova):
        campos = ('interface', 'velocidade_leitura_mbps', 'velocidade_gravacao_mbps',
                  'fluxo_ar', 'fluxo_ar_cfm', 'pressao_estatica_mmh2o', 'rotacao_max_rpm')
        diferencas, perda = [], Decimal(0)
        for campo in campos:
            if original.get(campo) != nova.get(campo):
                diferencas.append({'campo': campo, 'antes': original.get(campo), 'depois': nova.get(campo)})
            if campo in ('velocidade_leitura_mbps', 'velocidade_gravacao_mbps'):
                a, b = self.numero(original.get(campo)), self.numero(nova.get(campo))
                if a is not None and a > 0:
                    perda += max(Decimal(0), (a - b) / a) if b is not None else Decimal(1)
        return diferencas, perda

    def _preservou_invariantes(self, original, final, catalogo):
        antes = {i['tipo']: i for i in original['componentes']}
        depois = {i['tipo']: i for i in final['componentes']}
        if antes.keys() != depois.keys():
            return False
        for tipo, item in antes.items():
            novo = depois[tipo]
            if (item['id'], item.get('quantidade', 1)) == (novo['id'], novo.get('quantidade', 1)):
                continue
            if tipo not in self.AJUSTAVEIS:
                if (item['id'], item.get('quantidade', 1)) != (novo['id'], novo.get('quantidade', 1)):
                    return False
            else:
                peca = next(p for p in catalogo[tipo] if p['id'] == item['id'])
                nova = next(p for p in catalogo[tipo] if p['id'] == novo['id'])
                qtd = self._quantidade_equivalente(tipo, peca, item.get('quantidade', 1), nova)
                if qtd is None or qtd != novo.get('quantidade', 1):
                    return False
        return True
