from services.catalogo_service.gravar_especificacoes_peca_service import preencher_especificacoes
"""Propõe somente lacunas com código completo em comum e ficha compatível."""
import re
from decimal import Decimal
from urllib.parse import urlsplit
from sqlalchemy import Integer, Float, Numeric, Boolean
from utils.codigos_peca import codigo_interno
from utils.identidade_peca import assinatura_peca, assinatura_documento, assinatura_tecnica
from .normalizar_produto import codigo
from .comparar_codigo_modelo_service import CompararCodigoModeloService
from .associacao_inteligente_service import AssociacaoInteligenteService
from .conferir_especificacoes_service import ESSENCIAIS, OPCIONAIS, converter, valores, extrair_titulo
from .normalizar_especificacoes import CONJUNTOS, agregar


class EnriquecerPecaExistenteService:
    CAMPOS_PROTEGIDOS = {'id','part_number','referencia_interna','preco','esgotado','kabum_external',
        'status_validacao','validacao_motivo','validado_em','preco_atualizado_em','criado_em','atualizado_em','fontes_especificacoes'}
    ALIASES = {'formato_ram':'formato','tipo_fone':'tipo','categoria_cabo':'categoria'}

    @staticmethod
    def ausente(valor):
        return valor is None or isinstance(valor,str) and not valor.strip()

    def preparar(self, peca, produto):
        motor = AssociacaoInteligenteService()
        fonte = urlsplit(produto.fonte or '')
        if (not produto.categoria_confirmada or produto.ativo is not True or produto.categoria != peca.__tablename__
                or fonte.scheme != 'https' or not fonte.hostname or fonte.username or fonte.password):
            return dict(status='revisao',motivo='Fonte, categoria ou estado não comprovado')
        if motor.comparar_marca(peca,produto)['pontos'] != 10:
            return dict(status='sem_correspondencia',motivo='Marca não comprovada')
        extrator = CompararCodigoModeloService()
        locais = extrator.extrair(peca.modelo,peca.__tablename__)
        if peca.part_number and not codigo_interno(peca.part_number):
            locais = locais | {codigo(peca.part_number)}
        remotos = set().union(*(extrator.extrair(v,peca.__tablename__) for v in
            (produto.modelo or '', *produto.modelos_alternativos, *valores(produto.identificadores.get('mpn')))))
        if produto.contexto.get('mpn_confirmado_na_fonte'):
            remotos |= {codigo(v) for v in valores(produto.identificadores.get('mpn'))}
        comuns = locais & remotos
        origem_confirmada = False
        if (produto.contexto.get('finalidade') == 'especificacoes'
                and produto.contexto.get('origem_peca') == f'{peca.__tablename__}:{peca.id}'):
            from models import Oferta
            origem_confirmada = Oferta.corresponde_origem(peca, produto.loja, produto.id_externo)
        if origem_confirmada:
            remotos |= extrator.extrair(produto.titulo, peca.__tablename__)
            if peca.__tablename__ == 'memoria_ram':
                padrao = r'(?:kvr|kf|ksm|kcp|hx)[a-z0-9]+/[a-z0-9._-]+|ct\d[a-z0-9]*(?:[./-][a-z0-9]+)*|cm[a-z]\d[a-z0-9]+'
                declarados = {v for texto in (produto.modelo or '', *produto.modelos_alternativos)
                              for v in extrator.extrair(texto, peca.__tablename__) if re.fullmatch(padrao, v)}
                no_titulo = {v for v in extrator.extrair(produto.titulo, peca.__tablename__) if re.fullmatch(padrao, v)}
                if declarados and no_titulo and declarados != no_titulo:
                    return dict(status='revisao', motivo='Código do fabricante diverge entre título e ficha')
        if len(comuns) != 1 and not origem_confirmada:
            return dict(status='sem_correspondencia',motivo='Código exato ausente ou ambíguo')
        codigo_exato = next(iter(comuns)) if len(comuns) == 1 else f'{produto.loja}:{produto.id_externo}'
        nomes = motor.comparar_nome_modelo(peca,produto)
        nome_original_compativel = False
        if origem_confirmada:
            from .comparar_nomes_service import chave
            local = chave(peca.modelo, peca.__tablename__, peca.fabricante)
            remoto = chave(produto.titulo, peca.__tablename__, peca.fabricante)
            nome_original_compativel = bool(len(local) >= 4 and local in remoto)
        tecnicas = motor.comparar_especificacoes(peca,produto)
        identidade = motor.comparar_identificadores(peca,produto)
        avaliacao = motor.avaliar(peca,produto)
        conflitos = avaliacao['conflitos']
        if any(c.startswith('titulo_divergente:') for c in conflitos):
            return dict(status='revisao', motivo='Título diverge da ficha técnica', conflitos=conflitos)
        pendencias = [p for p in avaliacao['pendencias'] if not p.startswith('especificacao_essencial_ausente:')
                      and p != 'formato_notebook_nao_comprovado_localmente']
        if origem_confirmada and (nomes['exato'] or nome_original_compativel):
            pendencias = [p for p in pendencias if p != 'modelo_exato_nao_comprovado'
                          and p != 'quantidade_nao_comprovada'
                          and not p.startswith('variante_nao_comprovada:')]
        minimo = min(2, len(ESSENCIAIS.get(peca.__tablename__, ()))) if origem_confirmada else 2
        ficha_suficiente = len(set(tecnicas['conferidos'])) >= minimo or bool(identidade['evidencias'])
        identidade_original = origem_confirmada and (nomes['exato'] or nome_original_compativel) and bool(extrator.extrair(peca.modelo, peca.__tablename__))
        if conflitos or pendencias or not (nomes['exato'] or nome_original_compativel) or not (ficha_suficiente or identidade_original):
            return dict(status='revisao',motivo='Ficha incompatível ou insuficiente',conflitos=conflitos)
        dados, origens = {}, {}
        no_titulo = extrair_titulo(peca.__tablename__, produto.titulo)
        campos = (*ESSENCIAIS.get(peca.__tablename__,()), *OPCIONAIS.get(peca.__tablename__,()))
        for campo in dict.fromkeys(campos):
            if not ficha_suficiente:
                continue
            destino = self.ALIASES.get(campo,campo)
            if destino not in peca.__table__.columns or destino in self.CAMPOS_PROTEGIDOS or not self.ausente(getattr(peca,destino)):
                continue
            brutos = valores(produto.especificacoes.get(campo))
            observados = {converter(campo,v) for v in brutos}
            if campo in CONJUNTOS:
                observados = {agregar(observados)}
            if len(observados) != 1 or None in observados:
                continue
            valor = next(iter(observados))
            if campo in no_titulo:
                titulo = {converter(campo, v) for v in valores(no_titulo[campo])}
                if None not in titulo and titulo != {valor}:
                    return dict(status='revisao', motivo='Título diverge da ficha: ' + campo)
            tipo = peca.__table__.columns[destino].type
            if isinstance(tipo,Boolean):
                if type(valor) is not bool:continue
            elif isinstance(tipo,(Integer,Float,Numeric)):
                n = Decimal(str(valor))
                if not n.is_finite() or n < 0 or isinstance(tipo,Integer) and n != int(n):continue
                valor = int(n) if isinstance(tipo,Integer) else float(n)
            else:
                valor = str(valor)
                if campo in ('formato_ram','ddr','tipo_memoria','tipo_painel','conector'):valor = valor.upper()
                if campo=='latencia':valor = 'CL' + str(valor)
                if campo in CONJUNTOS:valor = valor.replace('|', ', ')
                if getattr(tipo,'length',None) and len(valor)>tipo.length:continue
            dados[destino] = valor
            origens[destino] = dict(url=produto.fonte,campo_fonte=campo,valor_original=brutos)
        mpns = {codigo(v):v for v in valores(produto.identificadores.get('mpn'))}
        if origem_confirmada and not comuns:
            codigos = [v for v in remotos if re.fullmatch(r'(?:kvr|kf|ksm|kcp|hx)[a-z0-9]+/[a-z0-9._-]+|ct\d[a-z0-9]*(?:[./-][a-z0-9]+)*|cm[a-z]\d[a-z0-9]+', v)]
            if len(codigos) == 1:
                codigo_exato = codigos[0]
        prefixo_ram = peca.__tablename__=='memoria_ram' and (
            re.fullmatch(r'(?:kvr|kf|ksm|kcp|hx)[a-z0-9]+/[a-z0-9._-]+',codigo_exato) and produto.marca.casefold()=='kingston'
            or re.fullmatch(r'ct\d[a-z0-9]*(?:[./-][a-z0-9]+)*',codigo_exato) and produto.marca.casefold()=='crucial'
            or re.fullmatch(r'cm[a-z]\d[a-z0-9]+',codigo_exato) and produto.marca.casefold()=='corsair')
        if ficha_suficiente and self.ausente(peca.part_number) and (codigo_exato in mpns or prefixo_ram):
            numero = mpns.get(codigo_exato,codigo_exato.upper())
            if len(numero) > peca.__table__.columns['part_number'].type.length:
                return dict(status='revisao',motivo='MPN excede o limite do campo')
            dados['part_number'] = numero
            origens['part_number'] = dict(url=produto.fonte,campo_fonte='MPN' if codigo_exato in mpns else 'MODEL',
                valor_original=dados['part_number'])
        if origem_confirmada and self.ausente(getattr(peca, 'codigo_modelo_fabricante', None)):
            declarados = []
            for v in (produto.modelo or '', *produto.modelos_alternativos):
                c = codigo(v)
                if (len(c) >= (6 if peca.__tablename__ in ('placa_mae','processador','memoria_ram') else 5) and (re.search('[a-z]', c) or re.fullmatch(r'\d{3}-\d{6,12}', c)) and re.search(r'\d', c)
                        and re.fullmatch(r'[a-z0-9]+(?:[-./][a-z0-9]+)*', c)
                        and not re.match(r'^(?:g?ddr|cl\d|rtx|gtx|rx\d|wifi|usb|hdmi|pcie|nvme|sata|abnt|[me]?atx|itx|a?rgb|lga|am[2345]|cat[5678])', c)
                        and not re.match(r'^\d+(?:gb|tb|mhz|hz|mm|w|dpi|a?rgb)', c)
                        and not (peca.__tablename__ == 'placa_mae' and re.fullmatch(r'[abhxzwq]\d{3}[a-z]?', c))
                        and re.search(r'(?<![a-z0-9/_.-])' + re.escape(c) + r'(?![a-z0-9/_.-])', produto.titulo.casefold())):
                    declarados.append(v)
            declarados = sorted(set(declarados))
            if len(declarados) == 1 and len(declarados[0]) <= 150:
                dados['codigo_modelo_fabricante'] = declarados[0]
                campo_fonte = 'Título' if declarados[0] in produto.contexto.get('codigos_titulo', []) and declarados[0] not in produto.contexto.get('rotulos_originais', {}).get('modelo', []) else 'Modelo'
                origens['codigo_modelo_fabricante'] = dict(url=produto.fonte,campo_fonte=campo_fonte,valor_original=declarados[0],titulo_origem=produto.titulo)
        return dict(status='proposta' if dados else 'inalterada',dados=dados,fontes=origens,codigo=codigo_exato,
            criterio='anuncio_original_e_especificacoes_compativeis' if origem_confirmada else 'codigo_exato_e_especificacoes_compativeis',sha256=assinatura_documento(produto.especificacoes),
            assinatura_tecnica=assinatura_tecnica(peca),
            origem={'loja': produto.loja, 'id_externo': produto.id_externo} if origem_confirmada else None)

    def executar(self, peca, produto, *, simular=True):
        assinatura = assinatura_peca(peca)
        proposta = self.preparar(peca,produto)
        if proposta['status']=='proposta':
            return preencher_especificacoes(peca, proposta,assinatura,simular=simular)
        return proposta
