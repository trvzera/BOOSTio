from sqlalchemy import inspect, text
from models import db
from .benchmarks_pecas import CAMPOS

VERSAO = 'benchmarks_mysql_v1'
TABELAS = {
    'processador': {**CAMPOS, 'benchmark_multi_core': 'NUMERIC(14, 2)', 'benchmark_single_thread': 'NUMERIC(14, 2)'},
    'placa_video': {**CAMPOS, 'benchmark_g2d': 'NUMERIC(14, 2)', 'benchmark_g3d': 'NUMERIC(14, 2)'},
}


def atualizar_benchmarks_mysql(simular=True):
    engine = db.engine
    if engine.dialect.name != 'mysql':
        raise ValueError('Este comando exige MySQL existente.')
    with engine.connect() as conexao:
        if conexao.scalar(text("SELECT GET_LOCK('boostio_benchmarks_mysql_v1', 0)")) != 1:
            raise ValueError('Outra atualização do banco está em execução.')
        try:
            inspetor = inspect(conexao)
            existentes = set(inspetor.get_table_names())
            faltantes = set(TABELAS) - existentes
            if faltantes:
                raise ValueError('Tabelas obrigatórias ausentes: ' + ', '.join(sorted(faltantes)))
            plano = []
            for tabela, campos in TABELAS.items():
                colunas = {c['name']: c for c in inspetor.get_columns(tabela)}
                for nome, tipo in campos.items():
                    if nome not in colunas:
                        plano.append(f'ALTER TABLE `{tabela}` ADD COLUMN `{nome}` {tipo} NULL')
                    else:
                        esperado = db.metadata.tables[tabela].c[nome].type.compile(dialect=engine.dialect)
                        atual = colunas[nome]['type'].compile(dialect=engine.dialect)
                        if esperado.replace('NUMERIC', 'DECIMAL') != atual.replace('NUMERIC', 'DECIMAL') or not colunas[nome]['nullable']:
                            raise ValueError(f'Coluna incompatível: {tabela}.{nome}; revisão necessária.')
            divergencias = []
            for tabela in db.metadata.sorted_tables:
                if tabela.name not in existentes:
                    divergencias.append(tabela.name + ' (tabela ausente)')
                    continue
                nomes = {c['name'] for c in inspetor.get_columns(tabela.name)}
                divergencias.extend(f'{tabela.name}.{c.name}' for c in tabela.columns
                                    if c.name not in nomes and c.name not in TABELAS.get(tabela.name, {}))
            if divergencias:
                raise ValueError('Outras migrações são necessárias antes desta atualização: ' + ', '.join(divergencias))
            resultado = dict(versao=VERSAO, simulacao=simular, alteracoes=plano)
            if simular:
                return resultado
            quote = engine.dialect.identifier_preparer.quote
            def contagens():
                return {t: conexao.scalar(text(f'SELECT COUNT(*) FROM {quote(t)}')) for t in sorted(existentes)}
            antes = contagens()
            for sql in plano:
                conexao.execute(text(sql))
                conexao.commit()
            depois = contagens()
            if antes != depois:
                raise ValueError('Contagem de registros mudou durante a atualização; mantenha a aplicação parada e investigue.')
            verificador = inspect(conexao)
            for tabela, campos in TABELAS.items():
                if not set(campos) <= {c['name'] for c in verificador.get_columns(tabela)}:
                    raise ValueError('Verificação das colunas falhou; mantenha a aplicação parada.')
            resultado['registros_conferidos'] = depois
            return resultado
        finally:
            conexao.execute(text("SELECT RELEASE_LOCK('boostio_benchmarks_mysql_v1')"))
