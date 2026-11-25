import re
from dataclasses import asdict

from models import db, ControleColeta, ProdutoPendente
from models.modelos_pecas import MODELOS_PECAS
from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
from services.catalogo_service.conferir_especificacoes_service import extrair_titulo
from services.catalogo_service.normalizar_produto import codigo
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.marketplace_service.gravar_ofertas_service import aplicar_ofertas_loja
from services.marketplace_service.controle_requisicoes_service import agora_utc
from services.shopee_service.normalizar_produto_service import derivar_modelo, limpar_titulo
from utils.identidade_peca import assinatura_peca, assinatura_documento

LOTE = 50
# Candidato com menos que isso é outra peça: não vale o tempo de quem revisa.
PERCENTUAL_MINIMO_REVISAO = 60
# O feed não traz categoria. O título da Gigantec começa pelo tipo da peça, então ele decide em quais categorias procurar.
TIPOS_NO_TITULO = (
    ('processador', r'^processador\b'), ('placa_video', r'^placa de v[ií]deo\b'), ('placa_mae', r'^placa[- ]m[ãa]e\b'),
    ('memoria_ram', r'^mem[óo]ria\b'), ('ssd', r'^ssd\b'), ('hd', r'^hd\b'), ('fonte', r'^fonte\b'), ('gabinete', r'^gabinete\b'),
    ('water_cooler', r'^water\s*cooler\b|^cooler\b.*\bwater\b'), ('air_cooler', r'^(?:air\s*)?cooler\b'),
)


def categorias_do_titulo(titulo):
    for categoria, padrao in TIPOS_NO_TITULO:
        if re.search(padrao, titulo.strip().lower()):
            return [categoria]
    return []


class AssociarFeedGigantecService:
    """Liga itens do feed a peças que já existem no catálogo, pelo código do fabricante (MPN) e pela marca.
    Não cadastra peça nova. Item sem correspondência exata, ambíguo ou em conflito fica de fora."""

    def executar(self, itens, *, simular=True, limite=None):
        resumo = {'simulacao': simular, 'itens': len(itens), 'sem_mpn': 0, 'sem_correspondencia': 0, 'revisao': 0,
                  'indisponiveis': 0, 'ligadas': 0, 'para_revisao': 0, 'criadas': 0, 'atualizadas': 0, 'inalteradas': 0, 'conflitos': 0, 'detalhes': []}
        escolhidas, ambiguos = self._escolher(itens, resumo)
        self._enviar_para_revisao(ambiguos, simular, resumo)
        if limite:
            escolhidas = dict(list(escolhidas.items())[:limite])
        resumo['ligadas'] = len(escolhidas)
        if not simular and not ControleColeta.bloquear():
            raise ValueError('Prepare o controle de coleta com mercadolivre-ofertas-preparar')
        modelos = {m.__tablename__: m for m in MODELOS_PECAS}
        for posicao, ((tabela, peca_id), (item, assinatura)) in enumerate(escolhidas.items(), 1):
            self._gravar(modelos[tabela], peca_id, item, assinatura, simular, resumo)
            if not simular and posicao % LOTE == 0:
                db.session.commit()
        if not simular:
            db.session.commit()
        return resumo

    def _escolher(self, itens, resumo):
        indices = {m.__tablename__: IndiceCandidatosService.carregar(m) for m in MODELOS_PECAS}
        por_peca, ambiguos = {}, []
        for item in sorted(itens.values(), key=lambda i: (i['preco'], i['id'])):
            if not item['mpn']:
                resumo['sem_mpn'] += 1
            chave = codigo(item['mpn'])
            por_mpn = [tabela for tabela, indice in indices.items() if indice.por_mpn.get(chave)]
            tabelas = por_mpn or categorias_do_titulo(item['titulo'])
            if not tabelas:
                resumo['sem_correspondencia'] += 1
                continue
            if not item['disponivel']:
                resumo['indisponiveis'] += 1
                continue
            confirmadas, duvidas = [], []
            for tabela in tabelas:
                indice = indices[tabela]
                titulo = limpar_titulo(item['titulo']) or item['titulo']
                produto = ProdutoNormalizado(loja='gigantec', id_externo=item['id'], categoria=tabela, titulo=titulo,
                    marca=item['marca'], modelo=derivar_modelo(titulo, item['marca']) if item['marca'] else None,
                    especificacoes=extrair_titulo(tabela, titulo), identificadores={'mpn': item['mpn']} if item['mpn'] else {},
                    ativo=True, categoria_confirmada=True, fonte=item['url'])
                decisao = indice.avaliar(produto)
                if decisao['classificacao'] == 'confirmada':
                    confirmadas.append((tabela, decisao['peca'], indice))
                elif decisao['classificacao'] == 'ambigua' and any(not c.get('conflitos') and c.get('percentual', 0) >= PERCENTUAL_MINIMO_REVISAO for c in decisao['candidatos']):
                    duvidas.append((item, produto, decisao))
            if len(confirmadas) != 1:
                resumo['revisao'] += 1
                if not confirmadas and len(duvidas) == 1:
                    ambiguos.append(duvidas[0])
                continue
            tabela, identificador, indice = confirmadas[0]
            peca_id = int(identificador.rsplit(':', 1)[1])
            peca = next(p for p in indice.pecas if p.id == peca_id)
            por_peca.setdefault((tabela, peca_id), (item, assinatura_peca(peca)))
        return por_peca, ambiguos

    def _enviar_para_revisao(self, ambiguos, simular, resumo):
        agora = agora_utc()
        linhas = [dict(loja='gigantec', produto_id_loja=item['id'], vendedor_id='', titulo=produto.titulo[:255], url=item['url'],
                       categoria_sugerida=produto.categoria, coletado_em=agora,
                       dados_originais={'normalizado': asdict(produto), 'item': {**item, 'preco': str(item['preco'])},
                                        'anuncio': {'price': str(item['preco'])}}) for item, produto, _ in ambiguos]
        resumo['para_revisao'] = ProdutoPendente.registrar_descobertos(linhas, simular=simular)['novos']
        if simular:
            return
        for linha, (_, _, decisao) in zip(linhas, ambiguos):
            pendente = ProdutoPendente.buscar_por_anuncio('gigantec', linha['produto_id_loja'])
            if pendente is not None and pendente.status == 'pendente':
                try:
                    ProdutoPendente.registrar_matching(pendente.id, decisao, assinatura_documento(pendente.dados_originais), simular=False)
                except ValueError:
                    continue

    def _gravar(self, modelo, peca_id, item, assinatura, simular, resumo):
        try:
            db.session.rollback()
            peca = modelo.buscar_por_id(peca_id)
            if peca is None or assinatura_peca(peca) != assinatura:
                raise ValueError('Peça mudou durante a leitura do feed')
            if not peca.publicavel:
                raise ValueError('Peça ainda não aprovada para publicação')
            oferta = dict(produto_id_loja=item['id'], vendedor_id='', url=item['url'], url_afiliado=item['url_afiliado'],
                          preco=item['preco'], esgotado=False)
            propostas = aplicar_ofertas_loja(peca, 'gigantec', [oferta], agora_utc())
            if simular:
                db.session.rollback()
        except ValueError as erro:
            db.session.rollback()
            resumo['conflitos'] += 1
            resumo['detalhes'].append({'anuncio': item['id'], 'peca': f'{modelo.__tablename__}:{peca_id}', 'erro': str(erro)})
            return
        resumo[{'criada': 'criadas', 'atualizada': 'atualizadas'}.get(propostas[0]['acao'], 'inalteradas')] += 1
        resumo['detalhes'].append({'anuncio': item['id'], 'peca': f'{modelo.__tablename__}:{peca_id}',
                                   'preco': str(item['preco']), 'acao': propostas[0]['acao']})
