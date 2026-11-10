from dataclasses import replace, asdict
from decimal import Decimal, InvalidOperation
from services.catalogo_service.conferir_especificacoes_service import converter
from services.catalogo_service.validar_ficha_tecnica_service import ValidarFichaTecnicaService


class MesclarFichaTecnicaService:
    def executar(self, produto, ficha, tecnica):
        dados = dict(ficha['dados'])
        fontes = dict(ficha.get('fontes', {}))
        conflitos = list(ficha.get('conflitos', []))
        for campo, valor in tecnica['dados'].items():
            if campo in dados and dados[campo] is not None:
                if not self._equivalentes(produto.categoria, campo, dados[campo], valor):
                    conflitos.append('fonte_tecnica_divergente:' + campo)
            else:
                dados[campo] = valor
                fontes[campo] = tecnica['fontes'][campo]
        fontes['mpn'] = tecnica['fontes']['mpn']
        identidade = tecnica['identidade']
        identificadores = dict(produto.identificadores)
        for campo, valor in identidade.items():
            if valor and not identificadores.get(campo):
                identificadores[campo] = valor
        produto = replace(produto, identificadores=identificadores)
        validacao = ValidarFichaTecnicaService().executar(produto.categoria, dados, produto,
            identidade, fontes=fontes, finalidade='catalogo')
        conflitos.extend(validacao['conflitos'])
        nova = {**ficha, 'fonte_identidade':tecnica['fonte_identidade'],
                'dados':dados, 'fontes':fontes, 'identidade':identidade,
                'campos_pendentes':validacao['campos_pendentes'], 'conflitos':sorted(set(conflitos)),
                'pronto':validacao['pronto'] and not conflitos,
                'finalidade_validacao':'catalogo', 'normalizado':asdict(produto)}
        return produto, nova

    @staticmethod
    def _equivalentes(categoria, campo, a, b):
        if campo in ('fabricante', 'modelo'):
            if campo == 'modelo':
                return True
            from services.catalogo_service.comparar_nomes_service import marca
            return marca(a) == marca(b)
        chave = 'formato_ram' if categoria == 'memoria_ram' and campo == 'formato' else campo
        if campo in ('consumo_energia', 'clockbase', 'clockmax'):
            try:
                return Decimal(str(a)) == Decimal(str(b))
            except InvalidOperation:
                return False
        x, y = converter(chave, a), converter(chave, b)
        return x is not None and y is not None and x == y
