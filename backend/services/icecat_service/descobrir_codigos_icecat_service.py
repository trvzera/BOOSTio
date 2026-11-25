import re
import sqlite3
from collections import defaultdict
from pathlib import Path

from sqlalchemy import inspect

from models import db, IdentidadeFabricante
from models.modelos_pecas import MODELOS_PECAS
from services.catalogo_service.identidades_para_matching_service import IdentidadesParaMatchingService
from services.catalogo_service.normalizar_produto import codigo, nome
from utils.identidade_peca import assinatura_peca

# Categoria da Icecat e começo do código de varejo de cada fabricante. O índice não guarda a marca,
# então o começo do código é o que garante que o modelo achado é mesmo daquele fabricante.
CATEGORIAS_ICECAT = {'placa_mae': '164'}
PREFIXOS_DE_CODIGO = {'asus': '90mb'}


def chave_do_modelo(modelo):
    """Nome comparável: sem a cor entre colchetes, sem pontuação e sem diferença de maiúsculas."""
    return re.sub(r'[^a-z0-9+]+', ' ', nome(re.sub(r'\[.*?\]', ' ', modelo or ''))).strip()


class DescobrirCodigosIcecatService:
    """Procura na Icecat, pelo nome do modelo, o código do fabricante das peças que não têm nenhum.
    Código único vira proposta; vários códigos ou código disputado vão para revisão, sem comparar só o começo do código.
    Ao aplicar, grava em identidade_fabricante: o part_number da peça não muda, então as ofertas já validadas continuam."""

    def __init__(self, indice):
        self.indice = Path(indice)

    def executar(self, *, categoria, marca, simular=True):
        modelo = next((m for m in MODELOS_PECAS if m.__tablename__ == categoria), None)
        marca = (marca or '').strip().lower()
        if modelo is None or categoria not in CATEGORIAS_ICECAT or marca not in PREFIXOS_DE_CODIGO:
            raise ValueError('Por enquanto só há suporte a placa_mae da ASUS')
        if not simular and not inspect(db.engine).has_table(IdentidadeFabricante.__tablename__):
            raise ValueError('Prepare a tabela com mercadolivre-identidades-preparar')
        codigos = self._codigos_por_modelo(CATEGORIAS_ICECAT[categoria], PREFIXOS_DE_CODIGO[marca])
        pecas = list(modelo.iterar_para_matching())
        identidades = IdentidadesParaMatchingService().executar(pecas)
        em_uso = {}
        for peca in pecas:
            atual = identidades.get(peca.id, {}).get('mpn') or peca.part_number
            if atual:
                em_uso[codigo(atual)] = peca.id
        resumo = {'simulacao': simular, 'categoria': categoria, 'marca': marca, 'pecas_da_marca': 0, 'ja_com_codigo': 0,
                  'sem_correspondencia': 0, 'varios_codigos': 0, 'codigo_disputado': 0, 'propostas': 0,
                  'gravadas': 0, 'identidade_antiga': 0, 'detalhes': [], 'revisao': []}
        candidatas = defaultdict(list)
        for peca in pecas:
            if (peca.fabricante or '').strip().lower() != marca:
                continue
            resumo['pecas_da_marca'] += 1
            if identidades.get(peca.id, {}).get('mpn') or peca.part_number:
                resumo['ja_com_codigo'] += 1
                continue
            achados = codigos.get(chave_do_modelo(peca.modelo), set())
            if not achados:
                resumo['sem_correspondencia'] += 1
            elif len(achados) > 1:
                resumo['varios_codigos'] += 1
                resumo['revisao'].append(dict(peca_id=peca.id, modelo=peca.modelo, codigos=sorted(a.upper() for a in achados)))
            else:
                candidatas[next(iter(achados))].append(peca)
        for achado, donas in candidatas.items():
            # Mesmo código em mais de uma peça indica cadastro repetido: ninguém recebe até alguém conferir.
            if len(donas) > 1 or achado in em_uso:
                resumo['codigo_disputado'] += len(donas)
                outras = [em_uso[achado]] if achado in em_uso else []
                resumo['revisao'].append(dict(codigo=achado.upper(), pecas=sorted([p.id for p in donas] + outras)))
                continue
            resumo['propostas'] += 1
            resumo['detalhes'].append(dict(peca_id=donas[0].id, modelo=donas[0].modelo, codigo=achado.upper()))
        if not simular:
            self._gravar(modelo, resumo)
        return resumo

    def _gravar(self, modelo, resumo):
        fonte = f'Icecat (índice local {self.indice.name}), busca pelo nome do modelo com código único'
        try:
            for proposta in resumo['detalhes']:
                peca = modelo.buscar_por_id(proposta['peca_id'])
                if peca is None or peca.part_number or peca.modelo != proposta['modelo']:
                    continue
                if IdentidadeFabricante.buscar_com_trava(peca):
                    # Há um registro anterior que não vale mais para a peça: alguém precisa conferir.
                    resumo['identidade_antiga'] += 1
                    continue
                db.session.add(IdentidadeFabricante(tabela_peca=peca.__tablename__, peca_id=peca.id,
                    assinatura_peca=assinatura_peca(peca), mpn=proposta['codigo'], gtin=None, fonte=fonte,
                    especificacoes={'fabricante': peca.fabricante, 'modelo': peca.modelo}))
                resumo['gravadas'] += 1
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def _codigos_por_modelo(self, categoria_icecat, prefixo):
        if not self.indice.is_file():
            raise ValueError('Prepare o índice com icecat-indice-preparar')
        resultado = defaultdict(set)
        with sqlite3.connect(self.indice.resolve().as_uri() + '?mode=ro', uri=True) as banco:
            linhas = banco.execute('SELECT mpn, modelo FROM produto WHERE categoria=? AND mpn>=? AND mpn<?',
                                   (categoria_icecat, prefixo, prefixo[:-1] + chr(ord(prefixo[-1]) + 1)))
            for mpn, modelo in linhas:
                chave = chave_do_modelo(modelo)
                if chave:
                    resultado[chave].add(codigo(mpn))
        return resultado
