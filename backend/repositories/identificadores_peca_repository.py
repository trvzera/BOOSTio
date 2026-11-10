"""Migração transacional de identificadores, preservando a identidade das peças."""
from sqlalchemy import MetaData, Table, inspect, select, update
from flask import g
from models import db, Oferta, IdentidadeFabricante
from utils.codigos_peca import codigo_interno
from utils.identidade_peca import assinatura_peca


def _vinculos(peca):
    resultado = []
    conexao = db.session.connection()
    if not hasattr(g, '_tabelas_identificadores'):
        g._tabelas_identificadores = [Table(nome, MetaData(), autoload_with=conexao)
            for nome in ('identidade_fabricante', 'vinculo_mercado_livre') if inspect(conexao).has_table(nome)]
    for tabela in g._tabelas_identificadores:
        registro = db.session.execute(select(tabela).where(
            tabela.c.tabela_peca == peca.__tablename__, tabela.c.peca_id == peca.id)).mappings().first()
        if registro:
            resultado.append((tabela, registro))
    return resultado


def reassinar_vinculos(peca, vinculos, antiga, numero, campos_preenchidos=()):
    nova = assinatura_peca(peca)
    if nova == antiga and not campos_preenchidos:
        return
    for tabela, registro in vinculos:
        if registro['assinatura_peca'] != antiga:
            continue
        valores = {'assinatura_peca': nova}
        for campo in ('especificacoes', 'especificacoes_revisadas'):
            specs = registro.get(campo)
            if isinstance(specs,dict) and any(k in specs and specs[k] is None for k in campos_preenchidos):
                specs = {k:v for k,v in specs.items() if not (k in campos_preenchidos and v is None)}
                valores[campo] = specs
            if isinstance(specs, dict) and codigo_interno(numero) and specs.get('part_number') == numero:
                specs = {k:v for k,v in specs.items() if k != 'part_number'}
                valores[campo] = {**specs, 'referencia_interna': numero}
        db.session.execute(update(tabela).where(tabela.c.id == registro['id']).values(**valores))


def separar_identificadores(peca, *, simular=True, ids_ambiguos=None):
    try:
        db.session.refresh(peca, with_for_update=True)
        antiga = assinatura_peca(peca)
        numero = peca.part_number
        referencia = peca.referencia_interna
        vinculos = _vinculos(peca)
        if codigo_interno(numero):
            if referencia and referencia != numero:
                raise ValueError('Referências internas divergentes; revisar antes de separar')
            peca.referencia_interna = numero
            peca.part_number = None
        for tabela, registro in vinculos:
            if tabela.name != 'identidade_fabricante' or registro['assinatura_peca'] != antiga:
                continue
            specs = registro['especificacoes']
            from types import SimpleNamespace
            anterior = SimpleNamespace(**{c.name: getattr(peca, c.name) for c in peca.__table__.columns})
            anterior.part_number = numero
            if (not codigo_interno(registro['mpn']) and IdentidadeFabricante.conferem(anterior, specs)
                    and (not numero or codigo_interno(numero))):
                peca.part_number = registro['mpn']
        reassinar_vinculos(peca, vinculos, antiga, numero)
        revisao = None
        try:
            oferta = Oferta.registrar_identidade_kabum(peca, simular=simular, ids_ambiguos=ids_ambiguos)
        except ValueError as erro:
            oferta = 'revisao'
            revisao = str(erro)
        mudou = numero != peca.part_number or referencia != peca.referencia_interna
        resultado = dict(peca=f'{peca.__tablename__}:{peca.id}', alterada=mudou,
            part_number=peca.part_number, referencia_interna=peca.referencia_interna,
            oferta=oferta, revisao=revisao)
        if simular:
            db.session.rollback()
        else:
            db.session.commit()
        return resultado
    except Exception:
        db.session.rollback()
        raise
