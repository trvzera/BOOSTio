from repositories.ofertas_repository import aplicar_lote_mercado_livre
from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from models import Oferta, VinculoMercadoLivre
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.identidade_peca import assinatura_peca, assinatura_catalogo
from .associar_catalogo_service import AssociarCatalogoService
from .buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from .controle_requisicoes_service import ControleRequisicoesService, OrcamentoRequisicoesEsgotado, ErroMercadoLivre
from services.marketplace_service.erros import FalhaMarketplace
from .token_mercado_livre_service import TokenMercadoLivreService
from .cliente_catalogo_cache_service import ClienteCatalogoCacheService
from .registrar_ambiguos_service import RegistrarAmbiguosMercadoLivreService


class AtualizarOfertasMercadoLivreService:
    CRITERIOS_AUTOMATICOS = ('mpn', 'gtin', 'codigo_fabricante', 'modelo_especificacoes')

    def executar(self, *, categoria=None, peca_id=None, depois_id=0, limite_pecas=20, limite_ofertas=1,
                 max_requisicoes=100, intervalo=1.0, simular=True, somente_vinculadas=False,
                 somente_com_minimos=False, cursores=None, progresso=None, guardar_detalhes=True):
        if limite_pecas is not None and (type(limite_pecas) is not int or not 1 <= limite_pecas <= 5000):
            raise ValueError('Limite de peças deve estar entre 1 e 5000')
        if type(limite_ofertas) is not int or not 1 <= limite_ofertas <= 20:
            raise ValueError('Limite de ofertas deve estar entre 1 e 20')
        modelos = [c for c in MODELOS_PECAS if categoria is None or c.__tablename__ == categoria]
        if not modelos or (peca_id is not None and (categoria is None or type(peca_id) is not int or peca_id <= 0)):
            raise ValueError('Filtro de peça inválido')
        if type(depois_id) is not int or depois_id < 0 or (depois_id and (categoria is None or peca_id is not None)):
            raise ValueError('Cursor requer categoria e não pode ser combinado com peça única')
        if type(somente_vinculadas) is not bool:
            raise ValueError('Filtro de vínculos inválido')
        if type(somente_com_minimos) is not bool or type(simular) is not bool:
            raise ValueError('Filtros de simulação e mínimos inválidos')
        if not guardar_detalhes and progresso is None:
            raise ValueError('Forneça um relatório incremental para não manter detalhes na memória')
        cursores = dict(cursores or {})
        if any(c not in {m.__tablename__ for m in MODELOS_PECAS} or type(v) is not int or v < 0 for c,v in cursores.items()):
            raise ValueError('Cursores inválidos')
        controle = ControleRequisicoesService(max_requisicoes, intervalo)
        cliente = ClienteCatalogoCacheService(controle, simular=simular)
        associador = AssociarCatalogoService()
        resumo = {'simulacao': simular, 'detalhes_incrementais': not guardar_detalhes, 'pecas': 0, 'associadas': 0, 'revisao': 0, 'nao_encontradas': 0,
                  'sem_ofertas': 0, 'falhas': 0, 'requisicoes': 0, 'ofertas_criadas': 0,
                  'ofertas_atualizadas': 0, 'ofertas_inalteradas': 0, 'ofertas_desativadas': 0, 'historicos': 0, 'interrompido': False, 'ultima_peca_concluida': None, 'detalhes': [], 'cursores': cursores, 'ignoradas_sem_minimos': 0, 'consultas_reaproveitadas': 0}
        esquema_verificado = False
        try:
            for peca in self._pecas(modelos, peca_id, limite_pecas, depois_id, somente_vinculadas, somente_com_minimos, resumo):
                resumo['pecas'] += 1
                detalhe = {'peca': f'{peca.__tablename__}:{peca.id}', 'modelo': peca.modelo}
                try:
                    if not esquema_verificado:
                        Oferta.verificar_esquema_mercado_livre()
                        esquema_verificado = True
                    # O token pode precisar de renovação entre lotes; não manter um token por horas.
                    token = TokenMercadoLivreService().executar()
                    resultado = self._processar_peca(peca, cliente, associador, token, limite_ofertas, simular)
                    chave = resultado.pop('contador')
                    detalhe.update(resultado)
                    resumo[chave] += 1
                    for proposta in resultado.get('ofertas', []):
                        resumo['ofertas_' + {'criada':'criadas','atualizada':'atualizadas','inalterada':'inalteradas','desativada':'desativadas'}[proposta['acao']]] += 1
                        resumo['historicos'] += int(proposta.get('historico', False))
                except (OrcamentoRequisicoesEsgotado, ErroMercadoLivre) as erro:
                    resumo['falhas'] += 1
                    detalhe.update(status='falha', motivo=str(erro))
                    if isinstance(erro, OrcamentoRequisicoesEsgotado) or erro.status in (401, 403, 429) or erro.status >= 500:
                        resumo['interrompido'] = True
                        resumo['detalhes'].append(detalhe)
                        self._informar(resumo, controle, cliente, progresso)
                        break
                except ValueError as erro:
                    resumo['falhas'] += 1
                    detalhe.update(status='falha', motivo=str(erro))
                    resumo['interrompido'] = True
                except SQLAlchemyError:
                    resumo['falhas'] += 1
                    detalhe.update(status='falha', motivo='Falha de persistência; lote da peça não confirmado')
                    resumo['interrompido'] = True
                    resumo['detalhes'].append(detalhe)
                    self._informar(resumo, controle, cliente, progresso)
                    break
                resumo['detalhes'].append(detalhe)
                if detalhe.get('status') != 'falha':
                    resumo['ultima_peca_concluida'] = detalhe['peca']
                    resumo['cursores'][peca.__tablename__] = peca.id
                self._informar(resumo, controle, cliente, progresso)
                if resumo['interrompido']:break
        finally:
            cliente.fechar()
        self._informar(resumo, controle, cliente, progresso)
        return resumo

    @staticmethod
    def _informar(resumo, controle, cliente, progresso):
        resumo['requisicoes'] = controle.total
        resumo['consultas_reaproveitadas'] = cliente.reaproveitadas
        if progresso:progresso(resumo)
        if resumo['detalhes_incrementais']:resumo['detalhes'].clear()

    def _processar_peca(self, peca, cliente, associador, token, limite, simular):
        busca = associador.localizar_candidatos(peca, cliente, token)
        ambiguos = busca.pop('ambiguos', [])
        registradas = 0 if simular or not ambiguos else RegistrarAmbiguosMercadoLivreService().executar(
            peca.__tablename__, ambiguos, cliente, token)
        resultado = self._processar_busca(peca, busca, cliente, associador, token, limite, simular)
        if ambiguos:
            resultado['ambiguas'] = len(ambiguos)
            resultado['ambiguas_registradas'] = registradas
        return resultado

    def _processar_busca(self, peca, busca, cliente, associador, token, limite, simular):
        if busca['status'] != 'encontrada':
            contador = 'nao_encontradas' if busca['status'] == 'nao_encontrada' else 'revisao'
            return dict(contador=contador, **busca)
        indisponiveis = []
        for vinculo in busca['catalogos']:
            try:
                produto = cliente._consultar(f"/products/{vinculo['catalogo_id']}", token)
                assinatura = assinatura_catalogo(produto)
                if produto.get('id') != vinculo['catalogo_id']:
                    raise ValueError('Detalhe do catálogo retornou outra identidade')
                if vinculo.get('assinatura_catalogo') and vinculo['assinatura_catalogo'] != assinatura:
                    raise ValueError('Ficha do catálogo mudou; revisão necessária')
                if vinculo['criterio'] in self.CRITERIOS_AUTOMATICOS and not associador.conferir_detalhe(peca, produto):
                    indisponiveis.append(dict(catalogo_id=vinculo['catalogo_id'], motivo='Detalhe não confirma identidade única'))
                    continue
                resultado = cliente.executar(vinculo['catalogo_id'], access_token=token, produto=produto)
                ofertas = self._selecionar(resultado['ofertas'], limite)
                if not ofertas:continue
                if not simular and not peca.publicavel:
                    return dict(contador='revisao', status='revisao', motivo='Ficha local aguarda aprovação')
                validar = (lambda: associador.conferir_detalhe(peca, produto, recarregar=True)) if vinculo['criterio'] in self.CRITERIOS_AUTOMATICOS else None
                propostas = aplicar_lote_mercado_livre(peca, vinculo['catalogo_id'], vinculo['assinatura'],
                    assinatura, vinculo['criterio'], ofertas, datetime.now(timezone.utc).replace(tzinfo=None),
                    simular=simular, validar_identidade=validar)
                return dict(contador='associadas', status='proposta' if simular else 'concluida',
                    catalogo_id=vinculo['catalogo_id'], ofertas=propostas,
                    busca_remota_completa=busca.get('busca_remota_completa'),
                    buscas=busca.get('buscas', []))
            except (ErroMercadoLivre, FalhaMarketplace) as erro:
                # 404/206 (sem ofertas ou resposta parcial) não são falha da peça. Na fila o erro chega
                # como FalhaMarketplace, onde 403 é autorização e interrompe.
                if erro.status not in ((403,404,206) if isinstance(erro, ErroMercadoLivre) else (404,206)):raise
                indisponiveis.append(dict(catalogo_id=vinculo['catalogo_id'], http=erro.status))
        return dict(contador='revisao' if indisponiveis else 'sem_ofertas',
            status='revisao' if indisponiveis else 'sem_ofertas', catalogos_indisponiveis=indisponiveis)

    @staticmethod
    def _selecionar(ofertas, limite):
        novas = sorted((o for o in ofertas if o['condicao'] == 'new'),
                       key=lambda o: (o['preco'], o['vendedor_id'], o['produto_id_loja']))
        vendedores, selecionadas = set(), []
        for oferta in novas:
            if oferta['vendedor_id'] in vendedores:
                continue
            vendedores.add(oferta['vendedor_id'])
            selecionadas.append(oferta)
            if len(selecionadas) == limite:
                break
        return selecionadas

    @staticmethod
    def _pecas(modelos, peca_id, limite, depois_id=0, somente_vinculadas=False, somente_com_minimos=False, resumo=None):
        total = 0
        for classe in modelos:
            if peca_id is not None:
                peca = classe.buscar_por_id(peca_id)
                if peca is None:
                    raise ValueError('Peça não encontrada')
                if not somente_vinculadas or VinculoMercadoLivre.buscar(classe.__tablename__, peca.id):
                    if not somente_com_minimos or not pendencias_para_montagem(peca):yield peca
                    elif resumo is not None:resumo['ignoradas_sem_minimos'] += 1
                return
            depois = max(depois_id, (resumo or {}).get('cursores', {}).get(classe.__tablename__, 0))
            while limite is None or total < limite:
                lote = classe.lote_para_ofertas(depois, 50 if limite is None else min(50, limite - total), somente_vinculadas=somente_vinculadas)
                if not lote:
                    break
                for peca in lote:
                    depois = peca.id
                    if somente_com_minimos and pendencias_para_montagem(peca):
                        if resumo is not None:
                            resumo['ignoradas_sem_minimos'] += 1
                            resumo['cursores'][classe.__tablename__] = peca.id
                        continue
                    yield peca
                    total += 1

    def vincular_revisado(self, categoria, peca_id, catalogo_id):
        classe = next((c for c in MODELOS_PECAS if c.__tablename__ == categoria), None)
        if classe is None:
            raise ValueError('Categoria inválida')
        peca = classe.buscar_por_id(peca_id)
        if peca is None:
            raise ValueError('Peça não encontrada')
        cliente = BuscarOfertasMercadoLivreService(ControleRequisicoesService(limite=2))
        cliente._validar_id(catalogo_id, 'catálogo')
        token = TokenMercadoLivreService().executar()
        produto = cliente._consultar(f'/products/{catalogo_id}', token)
        if produto.get('id') != catalogo_id or produto.get('status') != 'active':
            raise ValueError('Catálogo inválido ou inativo')
        VinculoMercadoLivre.registrar_revisado(peca, catalogo_id, assinatura_peca(peca), assinatura_catalogo(produto))
        return {'peca': f'{categoria}:{peca_id}', 'catalogo_id': catalogo_id, 'nome_catalogo': produto.get('name')}
