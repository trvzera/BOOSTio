"""Índice local descartável, separado do banco de peças e reconstruído atomicamente."""
import fcntl
import gzip
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from defusedxml.ElementTree import iterparse
from services.catalogo_service.normalizar_produto import codigo, gtin, nome
from services.catalogo_service.conferir_especificacoes_service import valores


class IndiceIcecatService:
    def __init__(self, caminho):
        self.caminho = Path(caminho)

    def preparar(self, arquivo):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with self.caminho.with_suffix('.lock').open('a') as trava:
            try:
                fcntl.flock(trava, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError('Preparação do índice Icecat já em andamento') from None
            return self._construir(Path(arquivo))

    def _construir(self, arquivo):
        descriptor, temporario = tempfile.mkstemp(dir=self.caminho.parent, prefix='.indice-icecat-')
        os.close(descriptor)
        total = 0
        try:
            with sqlite3.connect(temporario) as banco:
                banco.executescript('''
                    CREATE TABLE produto (id TEXT PRIMARY KEY, mpn TEXT, modelo TEXT, atualizado TEXT, categoria TEXT);
                    CREATE TABLE identificador (gtin TEXT, produto_id TEXT);
                    CREATE TABLE metadados (versao INTEGER, gerado TEXT, produtos INTEGER);
                ''')
                abrir = gzip.open if arquivo.suffix == '.gz' else open
                with abrir(arquivo, 'rb') as fonte:
                    eventos = iterparse(fonte, events=('start', 'end'))
                    _, raiz = next(eventos)
                    if raiz.tag != 'ICECAT-interface':
                        raise ValueError('Arquivo não é um índice Icecat')
                    gerado = None
                    container = None
                    for evento, elemento in eventos:
                        if evento == 'start' and elemento.tag == 'files.index':
                            gerado = elemento.get('Generated')
                            container = elemento
                        if evento != 'end' or elemento.tag != 'file':
                            continue
                        a = elemento.attrib
                        identificador = a.get('Product_ID', '')
                        if not re.fullmatch(r'[0-9]+', identificador):
                            raise ValueError('ID inválido no índice Icecat')
                        banco.execute('INSERT INTO produto VALUES (?,?,?,?,?)',
                            (identificador, codigo(a.get('Prod_ID')), nome(a.get('Model_Name')),
                             a.get('Updated', ''), a.get('Catid', '')))
                        eans = {(gtin(e.get('Value')), identificador) for e in elemento.findall('./EAN_UPCS/EAN_UPC')
                                if e.get('IsApproved') == '1' and gtin(e.get('Value'))}
                        banco.executemany('INSERT INTO identificador VALUES (?,?)', eans)
                        total += 1
                        container.clear()
                        if total % 10000 == 0:
                            banco.commit()
                if not total or not gerado:
                    raise ValueError('Índice Icecat vazio ou sem data de geração')
                banco.executescript('CREATE INDEX ix_icecat_mpn ON produto(mpn); CREATE INDEX ix_icecat_modelo ON produto(modelo); CREATE INDEX ix_icecat_gtin ON identificador(gtin);')
                banco.execute('INSERT INTO metadados VALUES (1,?,?)', (gerado, total))
            os.replace(temporario, self.caminho)
            return dict(produtos=total, gerado=gerado, indice=str(self.caminho))
        finally:
            if os.path.exists(temporario):
                os.unlink(temporario)

    def buscar(self, produto):
        if not self.caminho.is_file():
            raise ValueError('Prepare o índice com icecat-indice-preparar')
        with sqlite3.connect(self.caminho.resolve().as_uri() + '?mode=ro', uri=True) as banco:
            banco.row_factory = sqlite3.Row
            if banco.execute('SELECT versao FROM metadados').fetchone()[0] != 1:
                raise ValueError('Reconstrua o índice Icecat')
            grupos = []
            for campo in ('mpn', 'gtin'):
                for valor in valores(produto.identificadores.get(campo)):
                    chave = codigo(valor) if campo == 'mpn' else gtin(valor)
                    if not chave:
                        continue
                    sql = ('SELECT * FROM produto WHERE mpn=? LIMIT 21' if campo == 'mpn' else
                           'SELECT p.* FROM produto p JOIN identificador i ON i.produto_id=p.id WHERE i.gtin=? LIMIT 21')
                    grupos.append({r['id']:dict(r) for r in banco.execute(sql, (chave,))})
            if grupos:
                # Identificadores contraditórios nunca cedem a uma busca por nome.
                ids = set(grupos[0])
                for grupo in grupos[1:]:
                    ids.intersection_update(grupo)
                encontrados = [grupos[0][i] for i in sorted(ids)]
                if any(len(g) > 20 for g in grupos):
                    return []
                return encontrados
            modelo = nome(produto.modelo)
            if not modelo or not produto.marca:
                return []
            return [dict(r) for r in banco.execute('SELECT * FROM produto WHERE modelo=? LIMIT 21', (modelo,))]
