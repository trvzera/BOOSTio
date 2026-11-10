
from utils.identidade_peca import assinatura_peca
from models import VinculoMercadoLivre, IdentidadeFabricante
from services.catalogo_service.consultas_peca_service import consultas_da_peca, mpn_da_peca


class AssociarCatalogoService:
    def __init__(self):
        self._categoria = None
        self._catalogo_local = None
        self._decisoes = {}

    def _indice(self, modelo):
        from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
        if self._categoria != modelo.__tablename__:
            self._catalogo_local = IndiceCandidatosService.carregar(modelo)
            self._categoria = modelo.__tablename__
            self._decisoes.clear()
        return self._catalogo_local

    def localizar_candidatos(self, peca, cliente, token):
        """Resultados remotos são independentes; cada um exige unicidade local."""
        from services.catalogo_service.associacao_inteligente_service import AssociacaoInteligenteService
        from .normalizar_produto_service import NormalizarProdutoService, DOMINIOS
        from utils.identidade_peca import assinatura_catalogo
        existente = VinculoMercadoLivre.buscar(peca.__tablename__, peca.id)
        assinatura = assinatura_peca(peca)
        if existente:
            if existente.assinatura_peca != assinatura or not existente.especificacoes_compativeis(peca):
                return dict(status='revisao', motivo='Identificação da peça mudou desde a associação', catalogos=[])
            return dict(status='encontrada', catalogos=[dict(catalogo_id=existente.catalogo_id,
                assinatura=assinatura, criterio=existente.criterio, assinatura_catalogo=existente.assinatura_catalogo)])
        indice = self._indice(type(peca))
        motor, normalizador = AssociacaoInteligenteService(), NormalizarProdutoService()
        catalogos, revisao, vistos, buscas, ambiguos = [], [], set(), [], []
        consultas = self.consultas(peca)
        for consulta in consultas:
            offset = 0
            while len(buscas) < 4:
                parametros = dict(site_id='MLB', status='active', q=consulta, limit=20)
                if offset:
                    parametros['offset'] = offset
                if peca.__tablename__ in DOMINIOS:
                    parametros['domain_id'] = DOMINIOS[peca.__tablename__]
                dados = cliente._consultar('/products/search', token, params=parametros)
                linhas, total = self._validar_pagina(dados, cliente)
                buscas.append(dict(consulta=consulta, offset=offset, total=total, recebidos=len(linhas)))
                novos = 0
                for produto in linhas:
                    if produto['id'] in vistos:
                        continue
                    vistos.add(produto['id'])
                    novos += 1
                    normal = normalizador.executar(produto, peca.__tablename__)
                    comparacao = motor.avaliar(peca, normal, identidade=indice.identidades.get(peca.id))
                    revisao.append(dict(catalogo_id=produto['id'], nome=normal.titulo, comparacao=comparacao))
                    if comparacao['classificacao'] not in ('confirmada', 'ambigua'):
                        continue
                    chave = assinatura_catalogo(produto)
                    if chave not in self._decisoes:
                        if len(self._decisoes) >= 256:
                            self._decisoes.clear()
                        self._decisoes[chave] = indice.avaliar(normal)
                    decisao = self._decisoes[chave]
                    referencia = f'{peca.__tablename__}:{peca.id}'
                    if comparacao['classificacao'] == 'confirmada' and decisao['classificacao'] == 'confirmada' and decisao['peca'] == referencia:
                        catalogos.append(dict(catalogo_id=produto['id'], assinatura=assinatura,
                            criterio=comparacao['criterio'], percentual=comparacao['percentual']))
                    elif decisao['classificacao'] == 'ambigua' and any(c['peca'] == referencia for c in decisao['candidatos']):
                        ambiguos.append(dict(produto=produto, normal=normal, decisao=decisao))
                if catalogos or not novos or len(linhas) < 20 or offset + len(linhas) >= total or offset >= 20:
                    break
                offset += len(linhas)
            if catalogos or len(buscas) >= 4:
                break
        catalogos.sort(key=lambda c:(-c['percentual'], c['catalogo_id']))
        revisao.sort(key=lambda c: -c['comparacao']['percentual'])
        completa = all(b['offset'] + b['recebidos'] >= b['total'] for b in buscas[-1:])
        return dict(status='encontrada' if catalogos else 'nao_encontrada' if not vistos else 'revisao',
            catalogos=catalogos, busca_remota_completa=completa, total_busca=max(b['total'] for b in buscas),
            buscas=buscas, candidatos_unicos=len(vistos), ambiguos=ambiguos,
            motivo='Cada candidato requer identidade e unicidade local comprovadas', candidatos=revisao[:5])

    def consultas(self, peca):
        return consultas_da_peca(peca)

    @staticmethod
    def _validar_pagina(dados, cliente):
        if not isinstance(dados, dict):
            raise ValueError('Resposta de busca de catálogo inválida')
        linhas, pagina = dados.get('results'), dados.get('paging')
        total = pagina.get('total') if isinstance(pagina, dict) else None
        if not isinstance(linhas, list) or type(total) is not int or total < len(linhas) or len(linhas) > 20:
            raise ValueError('Resposta de busca de catálogo inválida')
        vistos = set()
        for produto in linhas:
            if not isinstance(produto, dict):
                raise ValueError('Candidato de catálogo inválido')
            cliente._validar_id(produto.get('id'), 'catálogo')
            if produto['id'] in vistos:
                raise ValueError('Catálogo repetido na pesquisa')
            vistos.add(produto['id'])
        return linhas, total

    def conferir_detalhe(self, peca, produto, *, recarregar=False):
        from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
        from .normalizar_produto_service import NormalizarProdutoService
        indice = IndiceCandidatosService.carregar(type(peca)) if recarregar else self._indice(type(peca))
        decisao = indice.avaliar(NormalizarProdutoService().executar(produto, peca.__tablename__))
        return decisao['classificacao'] == 'confirmada' and decisao['peca'] == f'{peca.__tablename__}:{peca.id}'

    def executar(self, peca, cliente, token):
        assinatura = assinatura_peca(peca)
        existente = VinculoMercadoLivre.buscar(peca.__tablename__, peca.id)
        if existente:
            if existente.assinatura_peca != assinatura or not existente.especificacoes_compativeis(peca):
                return {'status': 'revisao', 'motivo': 'Identificação da peça mudou desde a associação'}
            return {'status': 'encontrada', 'catalogo_id': existente.catalogo_id,
                    'assinatura': assinatura, 'criterio': existente.criterio,
                    'assinatura_catalogo': existente.assinatura_catalogo}
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
            return {'status': 'encontrada', 'catalogo_id': ids[0], 'assinatura': assinatura, 'criterio': self.comparar(peca, next(p for p in candidatos if p['id'] == ids[0]))['criterio']}
        return {'status': 'nao_encontrada' if total == 0 else 'revisao',
                'motivo': 'Sem correspondência única acima de 80 por identificador ou título, modelo e especificações',
                'candidatos': candidatos_revisao}

    @staticmethod
    def _unica_local(peca, produto):
        from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
        from .normalizar_produto_service import NormalizarProdutoService
        indice = IndiceCandidatosService.carregar(type(peca))
        decisao = indice.avaliar(NormalizarProdutoService().executar(produto, peca.__tablename__))
        return decisao['classificacao'] == 'confirmada' and decisao['peca'] == f'{peca.__tablename__}:{peca.id}'

    @staticmethod
    def comparar(peca, produto):
        from .comparar_produtos_service import CompararProdutosService
        verificada = IdentidadeFabricante.buscar(peca)
        identidade = {'mpn': verificada.mpn, 'gtin': verificada.gtin} if verificada else None
        return CompararProdutosService().avaliar(peca, produto, identidade=identidade)

    @staticmethod
    def comprova_identidade(peca, produto):
        return AssociarCatalogoService.comparar(peca, produto)['classificacao'] == 'confirmada'

    @staticmethod
    def _mpn(peca):
        return mpn_da_peca(peca)
