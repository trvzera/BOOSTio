"""Adapta ofertas Shopee aos serviços comuns; rede fora das transações."""
from dataclasses import asdict
from datetime import datetime, timezone

from models import ProdutoPendente
from models.modelos_pecas import MODELOS_PECAS
from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
from services.catalogo_service.importar_catalogo_service import ImportarCatalogoService
from services.catalogo_service.enriquecer_normalizado_service import EnriquecerNormalizadoService
from services.marketplace_service.gravar_ofertas_service import atualizar_ofertas_validadas
from services.catalogo_service.consultas_peca_service import consultas_da_peca
from utils.identidade_peca import assinatura_documento, assinatura_peca
from .cliente_service import ClienteShopeeService
from .normalizar_produto_service import NormalizarProdutoShopeeService


class ProcessarOfertasShopeeService:
    def __init__(self, cliente=None):
        self.cliente = cliente or ClienteShopeeService()
        self._marcas = None

    def _normalizador(self):
        """Marcas conhecidas: as do catálogo e as da base técnica; só elas identificam o fabricante."""
        if self._marcas is None:
            marcas = {m for modelo in MODELOS_PECAS for m in modelo.fabricantes_para_descoberta()}
            marcas |= {m[1] for m in self._marcas_da_base_tecnica()}
            self._marcas = tuple(sorted(marcas))
        return NormalizarProdutoShopeeService(self._marcas)

    @staticmethod
    def _marcas_da_base_tecnica():
        from services.catalogo_service.consultar_base_hardware_service import ConsultarBaseHardwareService
        base = ConsultarBaseHardwareService()
        try:
            base._ler()
        except (OSError, ValueError, KeyError):
            return []
        return [(g, linha['vendor']) for g, linhas in base.por_marca.items() for linha in linhas[:1]]

    MAX_BUSCAS = 4
    POR_PAGINA = 20

    def ofertas_peca(self, *, categoria, peca_id, simular=True, limite_ofertas=1):
        """Associa anúncios à peça como no Mercado Livre: busca por MPN, depois por nome, e exige
        correspondência única; fica o menor preço de cada loja (vendedor), até `limite_ofertas`."""
        modelo = next((m for m in MODELOS_PECAS if m.__tablename__ == categoria), None)
        if modelo is None or type(peca_id) is not int or not 1 <= limite_ofertas <= 20:
            raise ValueError('Filtro de peça inválido')
        peca = modelo.buscar_por_id(peca_id)
        if peca is None or not peca.publicavel:
            raise ValueError('Peça ausente ou não aprovada')
        assinatura = assinatura_peca(peca)
        identificador = f'{categoria}:{peca_id}'
        indice = IndiceCandidatosService.carregar(modelo)
        resumo = dict(peca=identificador, associadas=0, revisao=0, invalidas=0, ambiguas=0, buscas=[], detalhes=[])
        confirmados, ambiguos, vistos, completa = [], [], set(), False
        for consulta in consultas_da_peca(peca):
            pagina = 1
            while len(resumo['buscas']) < self.MAX_BUSCAS:
                resposta = self.cliente.buscar(consulta[:200], pagina=pagina, limite=self.POR_PAGINA)
                nos = resposta['nodes']
                resumo['buscas'].append(dict(consulta=consulta, pagina=pagina, recebidos=len(nos)))
                novos = 0
                for bruto in nos:
                    chave = str(bruto.get('itemId')) if isinstance(bruto, dict) else None
                    if chave in vistos:
                        continue
                    vistos.add(chave)
                    novos += 1
                    self._classificar(bruto, categoria, identificador, indice, confirmados, ambiguos, resumo)
                tem_mais = resposta['pageInfo']['hasNextPage']
                completa = not tem_mais
                if confirmados or not novos or not tem_mais or len(nos) < self.POR_PAGINA:
                    break
                pagina += 1
            if confirmados or len(resumo['buscas']) >= self.MAX_BUSCAS:
                break
        selecionados = self._selecionar(confirmados, limite_ofertas)
        resumo['busca_completa'] = completa
        resumo['candidatos_unicos'] = len(vistos)
        resumo['ambiguas'] = len(ambiguos)
        if ambiguos and not simular:
            resumo['ambiguas_registradas'] = self._registrar_ambiguos(categoria, ambiguos)
        if selecionados:
            propostas = atualizar_ofertas_validadas(peca, 'shopee', selecionados, assinatura,
                simular=simular, desativar_ausentes=completa)
            resumo['associadas'] = len(selecionados)
            resumo['detalhes'].extend(propostas)
        return resumo

    def _classificar(self, bruto, categoria, identificador, indice, confirmados, ambiguos, resumo):
        try:
            produto, oferta = self._normalizador().executar(bruto, categoria)
        except ValueError:
            resumo['invalidas'] += 1
            return
        decisao = indice.avaliar(produto)
        if decisao['classificacao'] == 'confirmada' and decisao['peca'] == identificador:
            confirmados.append((oferta, produto))
        else:
            resumo['revisao'] += 1
            if decisao['classificacao'] == 'ambigua' and any(c['peca'] == identificador for c in decisao['candidatos']):
                ambiguos.append((bruto, produto, oferta, decisao))

    @staticmethod
    def _registrar_ambiguos(categoria, ambiguos):
        """Grava em produto_pendente (em_revisao) com os candidatos; nunca reabre pendência encerrada."""
        agora = datetime.now(timezone.utc).replace(tzinfo=None)
        registradas = 0
        for bruto, produto, oferta, decisao in ambiguos:
            linha = dict(loja='shopee', produto_id_loja=produto.id_externo, vendedor_id=oferta['vendedor_id'],
                titulo=produto.titulo, url=produto.fonte, categoria_sugerida=categoria, coletado_em=agora,
                dados_originais={'normalizado': asdict(produto), 'anuncio': bruto})
            ProdutoPendente.registrar_descobertos([linha], simular=False)
            pendente = ProdutoPendente.buscar_por_anuncio('shopee', produto.id_externo)
            try:
                ProdutoPendente.registrar_matching(pendente.id, decisao, assinatura_documento(pendente.dados_originais), simular=False)
                registradas += 1
            except ValueError:
                continue
        return registradas

    @staticmethod
    def _selecionar(confirmados, limite):
        """Menor preço primeiro, um anúncio por loja da Shopee, como o Mercado Livre faz por vendedor."""
        vendedores, selecionados = set(), []
        for oferta, produto in sorted(confirmados, key=lambda i: (i[0]['preco'], i[0]['vendedor_id'], i[0]['produto_id_loja'])):
            if oferta['vendedor_id'] in vendedores:
                continue
            vendedores.add(oferta['vendedor_id'])
            selecionados.append((oferta, produto))
            if len(selecionados) == limite:
                break
        return selecionados

    def descobrir_pagina(self, *, categoria, termo, pagina=1, limite=20, simular=True):
        if categoria not in {m.__tablename__ for m in MODELOS_PECAS}:
            raise ValueError('Categoria inválida')
        resposta = self.cliente.buscar(termo, pagina=pagina, limite=limite)
        linhas, invalidas = [], 0
        for bruto in resposta['nodes']:
            try:
                produto, oferta = self._normalizador().executar(bruto, categoria)
            except ValueError:
                invalidas += 1
                continue
            linhas.append(dict(loja='shopee', produto_id_loja=produto.id_externo,
                vendedor_id=oferta['vendedor_id'], titulo=produto.titulo, url=produto.fonte,
                categoria_sugerida=categoria, dados_originais={'normalizado': asdict(produto), 'anuncio': bruto},
                coletado_em=datetime.now(timezone.utc).replace(tzinfo=None)))
        resultado = ProdutoPendente.registrar_descobertos(linhas, simular=simular)
        return dict(**resultado, invalidas=invalidas, pagina=resposta['pageInfo'],
                    anuncios=[linha['produto_id_loja'] for linha in linhas])

    def importar_anuncio(self, *, anuncio_id, simular=True, permitir_novos=False):
        pendencia = ProdutoPendente.buscar_por_anuncio('shopee', anuncio_id)
        if pendencia is None:
            raise ValueError('Anúncio não descoberto')
        shop, item = anuncio_id.split(':')
        resposta = self.cliente.consultar_anuncio(shop, item)
        if not resposta['nodes']:
            return dict(acao='sem_oferta', anuncio=anuncio_id)
        produto, oferta = self._normalizador().executar(resposta['nodes'][0], pendencia.categoria_sugerida)
        if produto.id_externo != anuncio_id:
            raise ValueError('Consulta retornou outro anúncio')
        if produto.contexto.get('variantes_nao_resolvidas'):
            return dict(acao='revisao', motivo='Variantes sem identificação de preço individual')
        produto, ficha = EnriquecerNormalizadoService().executar(produto)
        ficha['dados'].setdefault('preco', float(oferta['preco']))
        ficha['dados'].setdefault('esgotado', False)
        for campo in ('preco', 'esgotado'):
            ficha['fontes'].setdefault(campo, {'url': produto.fonte})
        return ImportarCatalogoService().executar(pendencia.id, produto, ficha, oferta,
            assinatura_documento(pendencia.dados_originais), simular=simular, permitir_novos=permitir_novos)
