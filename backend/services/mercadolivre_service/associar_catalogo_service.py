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
            if self.comprova_identidade(peca, produto):
                cliente._validar_id(produto.get('id'), 'catálogo')
                ids.append(produto['id'])
        candidatos_revisao = [{'catalogo_id': p.get('id'), 'nome': p.get('name'), 'comparacao': self.comparar(peca, p)} for p in candidatos[:5]]
        if len(ids) == 1 and not self._unica_local(peca, next(p for p in candidatos if p['id'] == ids[0])):
            ids = []
        if len(ids) == 1 and total == len(candidatos) and len(set(p.get('id') for p in candidatos)) == len(candidatos):
            return {'status': 'encontrada', 'catalogo_id': ids[0], 'assinatura': assinatura, 'criterio': self.comparar(peca, next(p for p in candidatos if p['id'] == ids[0]))['evidencias'][0]}
        return {'status': 'nao_encontrada' if total == 0 else 'revisao',
                'motivo': 'Sem correspondência única comprovada por MPN e fabricante',
                'candidatos': candidatos_revisao}

    @staticmethod
    def _unica_local(peca, produto):
        from .comparar_produtos_service import CompararProdutosService
        pecas = type(peca).pool_para_matching(2001)
        decisao = CompararProdutosService().selecionar(pecas[:2000], produto,
            identidades=IdentidadeFabricante.para_matching(pecas[:2000]), completo=len(pecas) <= 2000)
        return decisao['classificacao'] == 'confirmada' and decisao['peca'] == f'{peca.__tablename__}:{peca.id}'

    @staticmethod
    def comparar(peca, produto):
        from .comparar_produtos_service import CompararProdutosService
        verificada = IdentidadeFabricante.buscar(peca)
        identidade = {'mpn': verificada.mpn, 'gtin': verificada.gtin} if verificada else None
        return CompararProdutosService().avaliar(peca, produto, identidade=identidade)

    @staticmethod
    def comprova_mpn(peca, produto):
        resultado = AssociarCatalogoService.comparar(peca, produto)
        return resultado['classificacao'] == 'confirmada' and 'mpn' in resultado['evidencias']

    @staticmethod
    def comprova_identidade(peca, produto):
        return AssociarCatalogoService.comparar(peca, produto)['classificacao'] == 'confirmada'

    @staticmethod
    def _mpn(peca):
        from flask import has_app_context
        verificada = IdentidadeFabricante.buscar(peca) if has_app_context() else None
        codigo = verificada.mpn if verificada else str(peca.part_number or '').strip()
        # Identificadores internos da seed não são códigos do fabricante.
        return None if not codigo or re.match(r'^(SEED|DEMO|BOOSTIO|REDE|KABUM)[-_]', codigo, re.I) else codigo
