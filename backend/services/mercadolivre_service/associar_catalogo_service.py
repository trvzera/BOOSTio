import re
from utils.identidade_peca import normalizar_identidade as normalizar, assinatura_peca
from models import VinculoMercadoLivre, IdentidadeFabricante


class AssociarCatalogoService:
    def executar(self, peca, cliente, token):
        assinatura = assinatura_peca(peca)
        existente = VinculoMercadoLivre.buscar(peca.__tablename__, peca.id)
        if existente:
            if existente.assinatura_peca != assinatura:
                return {'status': 'revisao', 'motivo': 'Identificação da peça mudou desde a associação'}
            return {'status': 'encontrada', 'catalogo_id': existente.catalogo_id,
                    'assinatura': assinatura, 'criterio': existente.criterio,
                    'assinatura_catalogo': existente.assinatura_catalogo}
        # Busca textual produz candidatos, nunca prova identidade por si só.
        consulta = self._mpn(peca) or f'{peca.fabricante} {peca.modelo}'
        parametros = {'site_id': 'MLB', 'status': 'active', 'q': consulta, 'limit': 20}
        if peca.__tablename__ == 'processador':
            parametros['domain_id'] = 'MLB-COMPUTER_PROCESSORS'
        dados = cliente._consultar('/products/search', token,
            params=parametros)
        candidatos = dados.get('results')
        paging = dados.get('paging')
        total = paging.get('total') if isinstance(paging, dict) else None
        if not isinstance(candidatos, list) or type(total) is not int or total < len(candidatos) or len(candidatos) > 20:
            raise ValueError('Resposta de busca de catálogo inválida')
        ids = []
        for produto in candidatos:
            if not isinstance(produto, dict):
                raise ValueError('Candidato de catálogo inválido')
            cliente._validar_id(produto.get('id'), 'catálogo')
            if self.comprova_mpn(peca, produto):
                cliente._validar_id(produto.get('id'), 'catálogo')
                ids.append(produto['id'])
        candidatos_revisao = [{'catalogo_id': p.get('id'), 'nome': p.get('name')} for p in candidatos[:5]]
        if len(ids) == 1 and total == len(candidatos) and len(set(p.get('id') for p in candidatos)) == len(candidatos):
            return {'status': 'encontrada', 'catalogo_id': ids[0], 'assinatura': assinatura, 'criterio': 'mpn'}
        return {'status': 'nao_encontrada' if total == 0 else 'revisao',
                'motivo': 'Sem correspondência única comprovada por MPN e fabricante',
                'candidatos': candidatos_revisao}

    @staticmethod
    def comprova_mpn(peca, produto):
        if not AssociarCatalogoService._mpn(peca) or produto.get('status') != 'active':
            return False
        if peca.__tablename__ in ('processador', 'placa_video'):
            nome = normalizar(produto.get('name'))
            if re.search(r'\b(kit|combo|upgrade|notebook|laptop)\b', nome):
                return False
            if peca.__tablename__ == 'processador' and produto.get('domain_id') != 'MLB-COMPUTER_PROCESSORS':
                return False
            if str(AssociarCatalogoService._mpn(peca)).upper().endswith('BOX') and re.search(r'\b(oem|tray)\b', nome):
                return False
        atributos = produto.get('attributes')
        if not isinstance(atributos, list):
            return False
        marcas, codigos = set(), set()
        for atributo in atributos:
            if not isinstance(atributo, dict):
                continue
            valores = [atributo.get('value_name')]
            extras = atributo.get('values')
            if isinstance(extras, list):
                valores += [v.get('name') for v in extras if isinstance(v, dict)]
            if atributo.get('id') == 'BRAND':
                marcas.update(normalizar(v) for v in valores if v)
            if atributo.get('id') in ('MPN', 'MANUFACTURER_PART_NUMBER', 'PART_NUMBER'):
                codigos.update(normalizar(v) for v in valores if v)
        return normalizar(peca.fabricante) in marcas and normalizar(AssociarCatalogoService._mpn(peca)) in codigos


    @staticmethod
    def _mpn(peca):
        from flask import has_app_context
        verificada = IdentidadeFabricante.buscar(peca) if has_app_context() else None
        codigo = verificada.mpn if verificada else str(peca.part_number or '').strip()
        # Identificadores internos da seed não são códigos do fabricante.
        return None if not codigo or re.match(r'^(SEED|DEMO|BOOSTIO|REDE)[-_]', codigo, re.I) else codigo
