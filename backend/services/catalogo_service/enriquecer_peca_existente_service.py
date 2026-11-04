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
        comuns = locais & remotos
        if len(comuns) != 1:
            return dict(status='sem_correspondencia',motivo='Código exato ausente ou ambíguo')
        codigo_exato = next(iter(comuns))
        nomes = motor.comparar_nome_modelo(peca,produto)
        tecnicas = motor.comparar_especificacoes(peca,produto)
        identidade = motor.comparar_identificadores(peca,produto)
        avaliacao = motor.avaliar(peca,produto)
        conflitos = avaliacao['conflitos']
        pendencias = [p for p in avaliacao['pendencias'] if not p.startswith('especificacao_essencial_ausente:')
                      and p != 'formato_notebook_nao_comprovado_localmente']
        if conflitos or pendencias or not nomes['exato'] or (len(set(tecnicas['conferidos'])) < 2 and not identidade['evidencias']):
            return dict(status='revisao',motivo='Ficha incompatível ou insuficiente',conflitos=conflitos)
        dados, origens = {}, {}
        no_titulo = extrair_titulo(peca.__tablename__, produto.titulo)
        campos = (*ESSENCIAIS.get(peca.__tablename__,()), *OPCIONAIS.get(peca.__tablename__,()))
        for campo in dict.fromkeys(campos):
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
        prefixo_ram = peca.__tablename__=='memoria_ram' and (
            re.fullmatch(r'(?:kvr|kf|ksm|kcp|hx)[a-z0-9]+/[a-z0-9._-]+',codigo_exato) and produto.marca.casefold()=='kingston'
            or re.fullmatch(r'ct\d[a-z0-9]*(?:[./-][a-z0-9]+)*',codigo_exato) and produto.marca.casefold()=='crucial'
            or re.fullmatch(r'cm[a-z]\d[a-z0-9]+',codigo_exato) and produto.marca.casefold()=='corsair')
        if self.ausente(peca.part_number) and (codigo_exato in mpns or prefixo_ram):
            numero = mpns.get(codigo_exato,codigo_exato.upper())
            if len(numero) > peca.__table__.columns['part_number'].type.length:
                return dict(status='revisao',motivo='MPN excede o limite do campo')
            dados['part_number'] = numero
            origens['part_number'] = dict(url=produto.fonte,campo_fonte='MPN' if codigo_exato in mpns else 'MODEL',
                valor_original=dados['part_number'])
        return dict(status='proposta' if dados else 'inalterada',dados=dados,fontes=origens,codigo=codigo_exato,
            criterio='codigo_exato_e_especificacoes_compativeis',sha256=assinatura_documento(produto.especificacoes),
            assinatura_tecnica=assinatura_tecnica(peca))

    def executar(self, peca, produto, *, simular=True):
        assinatura = assinatura_peca(peca)
        proposta = self.preparar(peca,produto)
        if proposta['status']=='proposta':
            return peca.preencher_especificacoes(proposta,assinatura,simular=simular)
        return proposta
