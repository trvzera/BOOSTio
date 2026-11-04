from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from models import Oferta, VinculoMercadoLivre
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.identidade_peca import assinatura_peca, assinatura_catalogo
from .associar_catalogo_service import AssociarCatalogoService
from .buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from .controle_requisicoes_service import ControleRequisicoesService, OrcamentoRequisicoesEsgotado, ErroMercadoLivre
from .token_mercado_livre_service import TokenMercadoLivreService


class AtualizarOfertasMercadoLivreService:
    def executar(self, *, categoria=None, peca_id=None, depois_id=0, limite_pecas=20, limite_ofertas=5,
                 max_requisicoes=100, intervalo=1.0, simular=True):
        if type(limite_pecas) is not int or not 1 <= limite_pecas <= 5000:
            raise ValueError('Limite de peças deve estar entre 1 e 5000')
        if type(limite_ofertas) is not int or not 1 <= limite_ofertas <= 20:
            raise ValueError('Limite de ofertas deve estar entre 1 e 20')
        modelos = [c for c in MODELOS_PECAS if categoria is None or c.__tablename__ == categoria]
        if not modelos or (peca_id is not None and (categoria is None or type(peca_id) is not int or peca_id <= 0)):
            raise ValueError('Filtro de peça inválido')
        if type(depois_id) is not int or depois_id < 0 or (depois_id and (categoria is None or peca_id is not None)):
            raise ValueError('Cursor requer categoria e não pode ser combinado com peça única')
        controle = ControleRequisicoesService(max_requisicoes, intervalo)
        cliente = BuscarOfertasMercadoLivreService(controle)
        resumo = {'simulacao': simular, 'pecas': 0, 'associadas': 0, 'revisao': 0, 'nao_encontradas': 0,
                  'sem_ofertas': 0, 'falhas': 0, 'requisicoes': 0, 'ofertas_criadas': 0,
                  'ofertas_atualizadas': 0, 'ofertas_inalteradas': 0, 'ofertas_desativadas': 0, 'historicos': 0, 'interrompido': False, 'ultima_peca_concluida': None, 'detalhes': []}
        for peca in self._pecas(modelos, peca_id, limite_pecas, depois_id):
            resumo['pecas'] += 1
            detalhe = {'peca': f'{peca.__tablename__}:{peca.id}', 'modelo': peca.modelo}
            try:
                # O token pode precisar de renovação entre lotes; não manter um token por horas.
                token = TokenMercadoLivreService().executar()
                vinculo = AssociarCatalogoService().executar(peca, cliente, token)
                if vinculo['status'] != 'encontrada':
                    chave = 'nao_encontradas' if vinculo['status'] == 'nao_encontrada' else 'revisao'
                    resumo[chave] += 1
                    detalhe.update(vinculo)
                else:
                    produto = cliente._consultar(f"/products/{vinculo['catalogo_id']}", token)
                    assinatura = assinatura_catalogo(produto)
                    if vinculo['criterio'] in ('mpn', 'gtin', 'modelo_especificacoes') and not AssociarCatalogoService.comprova_identidade(peca, produto):
                        raise ValueError('MPN/fabricante divergiram no detalhe do catálogo')
                    if vinculo.get('assinatura_catalogo') and vinculo['assinatura_catalogo'] != assinatura:
                        raise ValueError('Ficha do catálogo mudou; revisão necessária')
                    resultado = cliente.executar(vinculo['catalogo_id'], access_token=token, produto=produto)
                    ofertas = self._selecionar(resultado['ofertas'], limite_ofertas)
                    if not ofertas:
                        resumo['sem_ofertas'] += 1
                        detalhe['status'] = 'sem_ofertas'
                    else:
                        propostas = Oferta.aplicar_lote_mercado_livre(
                            peca, vinculo['catalogo_id'], vinculo['assinatura'], assinatura,
                            vinculo['criterio'], ofertas, datetime.now(timezone.utc).replace(tzinfo=None), simular=simular)
                        for proposta in propostas:
                            resumo['ofertas_' + {'criada': 'criadas', 'atualizada': 'atualizadas', 'inalterada': 'inalteradas', 'desativada': 'desativadas'}[proposta['acao']]] += 1
                            resumo['historicos'] += int(proposta.get('historico', False))
                        resumo['associadas'] += 1
                        detalhe.update(status='proposta' if simular else 'concluida', catalogo_id=vinculo['catalogo_id'], ofertas=propostas)
            except (OrcamentoRequisicoesEsgotado, ErroMercadoLivre) as erro:
                resumo['falhas'] += 1
                detalhe.update(status='falha', motivo=str(erro))
                if isinstance(erro, OrcamentoRequisicoesEsgotado) or erro.status in (401, 403, 429) or erro.status >= 500:
                    resumo['interrompido'] = True
                    resumo['detalhes'].append(detalhe)
                    break
            except ValueError as erro:
                resumo['falhas'] += 1
                detalhe.update(status='falha', motivo=str(erro))
            except SQLAlchemyError:
                resumo['falhas'] += 1
                detalhe.update(status='falha', motivo='Falha de persistência; lote da peça não confirmado')
                resumo['interrompido'] = True
                resumo['detalhes'].append(detalhe)
                break
            resumo['detalhes'].append(detalhe)
            if detalhe.get('status') != 'falha':
                resumo['ultima_peca_concluida'] = detalhe['peca']
        resumo['requisicoes'] = controle.total
        return resumo

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
    def _pecas(modelos, peca_id, limite, depois_id=0):
        total = 0
        for classe in modelos:
            if peca_id is not None:
                peca = classe.buscar_por_id(peca_id)
                if peca is None:
                    raise ValueError('Peça não encontrada')
                yield peca
                return
            depois = depois_id
            while total < limite:
                lote = classe.lote_para_ofertas(depois, min(50, limite - total))
                if not lote:
                    break
                for peca in lote:
                    yield peca
                    total += 1
                    depois = peca.id

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
