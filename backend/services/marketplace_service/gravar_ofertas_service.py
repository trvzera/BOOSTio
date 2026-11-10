from models import db, Oferta


def aplicar_lote_mercado_livre(peca, catalogo_id, assinatura, assinatura_catalogo, criterio, ofertas, agora, *, simular, confirmar=True, desativar_ausentes=True, validar_identidade=None):
    from models import VinculoMercadoLivre, HistoricoOferta, ControleColeta
    from utils.identidade_peca import assinatura_peca
    propostas = []
    try:
        if not simular:
            if not ControleColeta.bloquear():
                raise ValueError('Prepare o controle de coleta antes da importação')
        db.session.refresh(peca, with_for_update=not simular)
        if assinatura_peca(peca) != assinatura:
            raise ValueError('A identificação da peça mudou durante a consulta')
        if not simular and validar_identidade is not None and not validar_identidade():
            raise ValueError('Identidade local mudou ou ficou ambígua; revisão necessária')
        vinculo = VinculoMercadoLivre.buscar(peca.__tablename__, peca.id, bloquear=not simular)
        if vinculo and not vinculo.especificacoes_compativeis(peca):
            raise ValueError('Especificações da peça mudaram desde a revisão')
        if vinculo and (vinculo.catalogo_id != catalogo_id or vinculo.assinatura_peca != assinatura or vinculo.assinatura_catalogo != assinatura_catalogo):
            raise ValueError('Vínculo existente divergente; revisão necessária')
        ocupante = VinculoMercadoLivre.buscar_por_catalogo(catalogo_id, bloquear=not simular, recarregar=not simular)
        if ocupante and (ocupante.tabela_peca, ocupante.peca_id) != (peca.__tablename__, peca.id):
            raise ValueError('Catálogo já associado a outra peça')
        existentes = Oferta.listar_da_peca(peca, 'mercado_livre', bloquear=not simular, recarregar=not simular)
        selecionadas = set()
        if not simular and vinculo is None:
            db.session.add(VinculoMercadoLivre(tabela_peca=peca.__tablename__, peca_id=peca.id,
                catalogo_id=catalogo_id, assinatura_peca=assinatura, assinatura_catalogo=assinatura_catalogo, criterio=criterio))
        for dados in ofertas:
            anuncio, vendedor = dados['produto_id_loja'], dados['vendedor_id']
            identidade = (anuncio, vendedor)
            selecionadas.add(identidade)
            registro = Oferta.buscar_por_anuncio('mercado_livre', anuncio, bloquear=not simular, recarregar=not simular)
            if registro and registro.vendedor_id != vendedor:
                raise ValueError('Vendedor do anúncio mudou; revisão necessária')
            if registro and (registro.tabela_peca, registro.peca_id) != (peca.__tablename__, peca.id):
                raise ValueError('Anúncio já vinculado a outra peça')
            acao = 'criada' if registro is None else 'atualizada' if (
                registro.preco != dados['preco'] or registro.esgotado != dados.get('esgotado') or not registro.ativa or registro.url != dados['url']) else 'inalterada'
            ultimo = HistoricoOferta.ultimo(registro.id, bloquear=not simular) if registro else None
            registrar_historico = ultimo is None or ultimo.preco != dados['preco'] or ultimo.esgotado != dados.get('esgotado') or ultimo.coletado_em.date() != agora.date()
            propostas.append({'anuncio': anuncio, 'vendedor': vendedor, 'preco': str(dados['preco']), 'acao': acao, 'historico': registrar_historico})
            if simular:
                continue
            if registro is None:
                registro = Oferta(tabela_peca=peca.__tablename__, peca_id=peca.id, loja='mercado_livre',
                               produto_id_loja=anuncio, vendedor_id=vendedor, url=dados['url'])
                db.session.add(registro)
            mudou = registro.preco != dados['preco']
            registro.preco = dados['preco']
            registro.url = dados['url']
            registro.esgotado = dados.get('esgotado')
            registro.ativa = True
            registro.consultado_em = agora
            if mudou:
                registro.preco_atualizado_em = agora
            db.session.flush()
            if registrar_historico:
                db.session.add(HistoricoOferta(oferta_id=registro.id, preco=registro.preco, esgotado=dados.get('esgotado'), coletado_em=agora))
        for registro in existentes:
            if desativar_ausentes and registro.ativa and (registro.produto_id_loja, registro.vendedor_id) not in selecionadas:
                propostas.append({'anuncio': registro.produto_id_loja, 'acao': 'desativada'})
                if not simular:
                    registro.ativa = False
        if not simular and confirmar:
            from services.marketplace_service.controle_requisicoes_service import verificar_execucao
            verificar_execucao()
            db.session.commit()
        return propostas
    except Exception:
        if not simular:
            db.session.rollback()
        raise


def aplicar_ofertas_loja(peca,loja,ofertas,agora):
    from decimal import Decimal,InvalidOperation
    from urllib.parse import urlsplit
    from models import HistoricoOferta
    propostas=[]
    for dados in ofertas:
        try:
            preco=Decimal(str(dados['preco']))
            if not preco.is_finite() or preco<=0 or preco>Decimal('999999999999.99') or preco.quantize(Decimal('.01'))!=preco:raise ValueError('Preço inválido')
        except (InvalidOperation,KeyError):raise ValueError('Preço inválido') from None
        url=urlsplit(dados['url'])
        if url.scheme!='https' or not url.hostname or url.username or url.password:raise ValueError('URL da oferta inválida')
        chave=str(dados['produto_id_loja'])
        if not loja or len(loja)>20 or not chave or len(chave)>80:raise ValueError('Identidade de anúncio inválida')
        registro=Oferta.buscar_por_anuncio(loja,chave,bloquear=True)
        if registro and (registro.tabela_peca!=peca.__tablename__ or registro.peca_id!=peca.id):raise ValueError('Anúncio já pertence a outra peça')
        if registro and registro.vendedor_id!=str(dados.get('vendedor_id') or ''):raise ValueError('Vendedor mudou; avaliar')
        novo=registro is None
        if novo:
            registro=Oferta(loja=loja,produto_id_loja=chave,tabela_peca=peca.__tablename__,peca_id=peca.id,
                vendedor_id=str(dados.get('vendedor_id') or ''),url=dados['url'])
            db.session.add(registro)
        mudou=novo or registro.preco!=preco or registro.esgotado!=dados.get('esgotado') or registro.url!=dados['url'] or not registro.ativa
        if mudou:
            registro.preco=preco;registro.esgotado=dados.get('esgotado');registro.url=dados['url'];registro.ativa=True
            registro.consultado_em=agora;registro.preco_atualizado_em=agora
        if loja == 'shopee':
            from services.shopee_service.normalizar_produto_service import validar_url_shopee
            afiliado = dados.get('url_afiliado')
            if afiliado and validar_url_shopee(afiliado, afiliado=True):
                registro.url_afiliado = afiliado
        registro.consultado_em = agora
        db.session.flush()
        ultimo=HistoricoOferta.ultimo(registro.id,bloquear=True)
        historico=ultimo is None or ultimo.preco!=preco or ultimo.esgotado!=registro.esgotado
        if historico:db.session.add(HistoricoOferta(oferta_id=registro.id,preco=preco,esgotado=registro.esgotado,coletado_em=agora))
        propostas.append(dict(anuncio=chave,acao='criada' if novo else 'atualizada' if mudou else 'inalterada',historico=historico))
    return propostas


def atualizar_ofertas_validadas(peca, loja, itens, assinatura, *, simular, desativar_ausentes=False, revisao_manual=None):
    from datetime import datetime, timezone
    from models import ControleColeta
    from utils.identidade_peca import assinatura_peca
    from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
    try:
        db.session.rollback()
        if not ControleColeta.bloquear():
            raise ValueError('Prepare o controle de coleta')
        db.session.refresh(peca, with_for_update=True)
        if assinatura_peca(peca) != assinatura or not peca.publicavel:
            raise ValueError('Peça mudou durante a consulta')
        if revisao_manual is None:
            indice = IndiceCandidatosService.carregar(type(peca))
            for _, produto in itens:
                decisao = indice.avaliar(produto)
                if decisao['classificacao'] != 'confirmada' or decisao['peca'] != f'{peca.__tablename__}:{peca.id}':
                    raise ValueError('Associação mudou durante a consulta')
        agora = datetime.now(timezone.utc).replace(tzinfo=None)
        propostas = aplicar_ofertas_loja(peca, loja, [oferta for oferta, _ in itens], agora)
        if loja == 'shopee':
            _registrar_vinculos_shopee(peca, itens, agora, revisao_manual)
        if desativar_ausentes:
            propostas += _desativar_ausentes(peca, loja, {produto.id_externo for _, produto in itens})
        if simular:
            db.session.rollback()
        else:
            from services.marketplace_service.controle_requisicoes_service import verificar_execucao
            verificar_execucao()
            db.session.commit()
        return propostas
    except Exception:
        db.session.rollback()
        raise


def _registrar_vinculos_shopee(peca, itens, agora, revisao_manual=None):
    from dataclasses import asdict
    from models import ProdutoPendente
    from utils.identidade_peca import assinatura_peca, assinatura_tecnica
    for oferta, produto in itens:
        registro = Oferta.buscar_unica_por_anuncio('shopee', produto.id_externo)
        pendente = ProdutoPendente.buscar_por_anuncio('shopee', produto.id_externo)
        if pendente is None:
            pendente = ProdutoPendente(loja='shopee', produto_id_loja=produto.id_externo,
                vendedor_id=oferta['vendedor_id'], titulo=produto.titulo, url=produto.fonte,
                categoria_sugerida=produto.categoria, dados_originais={'normalizado': asdict(produto)}, coletado_em=agora)
            db.session.add(pendente)
        pendente.status = 'importado'
        pendente.oferta_id = registro.id
        pendente.revisado_em = agora
        pendente.evidencias = {**(pendente.evidencias or {}), 'vinculo': {
            'assinatura_peca': assinatura_peca(peca), 'assinatura_tecnica': assinatura_tecnica(peca)}}
        if revisao_manual:
            pendente.motivo = 'Associação aprovada por um administrador'
            pendente.evidencias = {**pendente.evidencias, 'revisao_manual': revisao_manual}


def _desativar_ausentes(peca, loja, mantidas):
    propostas = []
    for registro in Oferta.listar_da_peca(peca, loja, apenas_ativas=True, bloquear=True):
        if registro.produto_id_loja not in mantidas:
            registro.ativa = False
            propostas.append(dict(anuncio=registro.produto_id_loja, acao='desativada', historico=False))
    return propostas
