from utils.colunas_antigas import COLUNAS_ANTIGAS_DA_PECA
from sqlalchemy import inspect, text
from sqlalchemy.schema import CreateIndex
from models import db, Oferta, ProdutoPendente, ExecucaoDescoberta, EstadoCatalogo, RevisaoIdentidadePeca
from models.modelos_pecas import MODELOS_PECAS

CAMPOS = {'status_validacao', 'validacao_motivo', 'validado_em'}
ESTADOS = "'pendente','em_revisao','aprovado','rejeitado','legado'"
TABELAS = (Oferta, ProdutoPendente, ExecucaoDescoberta, EstadoCatalogo, RevisaoIdentidadePeca)


def preparar_catalogo_automatizado(*, simular=True):
    dialecto = db.engine.dialect.name
    if dialecto not in ('sqlite', 'mysql'):
        raise ValueError('Banco não suportado para catálogo automatizado')
    insp = inspect(db.engine)
    for modelo in TABELAS:
        tabela = modelo.__table__
        if insp.has_table(tabela.name):
            if {c['name'] for c in insp.get_columns(tabela.name)} != set(tabela.columns.keys()):
                raise ValueError(f'Tabela {tabela.name} incompatível; revise as migrações anteriores')
    if insp.has_table('oferta'):
        cols = {c['name']: c for c in insp.get_columns('oferta')}
        if any(cols[c]['nullable'] for c in ('loja', 'produto_id_loja')):
            raise ValueError('Identidade da oferta permite NULL; revisar antes de migrar')
        with db.engine.connect() as conn:
            duplicados = conn.execute(text('SELECT loja, produto_id_loja, COUNT(*) AS total FROM oferta GROUP BY loja, produto_id_loja HAVING COUNT(*) > 1 LIMIT 10')).mappings().all()
            invalidos = conn.execute(text("SELECT COUNT(*) FROM oferta WHERE trim(loja) = '' OR trim(produto_id_loja) = ''")).scalar_one()
        if duplicados or invalidos:
            raise ValueError(f'Ofertas duplicadas ou sem identidade: {list(map(dict, duplicados))}; vazias={invalidos}. Nenhum registro foi removido; revisar manualmente.')
    existentes = []
    for modelo in MODELOS_PECAS:
        nome = modelo.__tablename__
        if not insp.has_table(nome):
            continue
        cols = {c['name'] for c in insp.get_columns(nome)} - COLUNAS_ANTIGAS_DA_PECA
        esperadas = set(modelo.__table__.columns.keys())
        novos = CAMPOS | {'referencia_interna','fontes_especificacoes','codigo_modelo_fabricante','ficha_montagem_validada'} | ({'formato'} if nome=='memoria_ram' else set())
        if nome == 'placa_video':novos |= {'fabricante_chip','modelo_referencia'}
        if not esperadas - novos <= cols or not cols <= esperadas:
            raise ValueError(f'Tabela {nome} incompatível; migração de catálogo não corrige outras alterações')
        existentes.append((modelo, cols))
    plano = []
    for modelo in TABELAS:
        if not insp.has_table(modelo.__tablename__):
            plano.append({'acao': 'criar_tabela', 'tabela': modelo.__tablename__})
    for modelo, cols in existentes:
        nome = modelo.__tablename__
        campos=[('status_validacao','VARCHAR(20)'),('validacao_motivo','TEXT'),('validado_em','DATETIME'),('referencia_interna','VARCHAR(100)'),('fontes_especificacoes','JSON'),('codigo_modelo_fabricante','VARCHAR(150)'),('ficha_montagem_validada','BOOLEAN')]
        if nome=='memoria_ram':campos.append(('formato','VARCHAR(20)'))
        if nome=='placa_video':campos.extend([('fabricante_chip','VARCHAR(30)'),('modelo_referencia','VARCHAR(120)')])
        for campo, tipo in campos:
            if campo not in cols:
                ddl = f'ALTER TABLE `{nome}` ADD COLUMN `{campo}` {tipo} NULL'
                if campo == 'status_validacao' and dialecto == 'sqlite':
                    ddl += f" CONSTRAINT ck_{nome}_validacao CHECK (status_validacao IS NULL OR status_validacao IN ({ESTADOS}))"
                plano.append({'acao': 'sql', 'sql': ddl})
        if dialecto == 'sqlite':
            with db.engine.connect() as conn:
                existe_trigger = conn.execute(text("SELECT 1 FROM sqlite_master WHERE type='trigger' AND name=:nome"), {'nome': f'tr_{nome}_validacao'}).first()
            if not existe_trigger:
                plano.append({'acao': 'sql', 'sql': f"CREATE TRIGGER `tr_{nome}_validacao` AFTER INSERT ON `{nome}` WHEN NEW.status_validacao IS NULL BEGIN UPDATE `{nome}` SET status_validacao = 'pendente' WHERE id = NEW.id; END"})
        else:
            atuais = {c['name']: c for c in insp.get_columns(nome)}
            if 'status_validacao' not in atuais or str(atuais['status_validacao'].get('default')).strip("'\"") != 'pendente':
                plano.append({'acao': 'sql', 'sql': f"ALTER TABLE `{nome}` ALTER COLUMN `status_validacao` SET DEFAULT 'pendente'"})
            checks = {c['name'] for c in insp.get_check_constraints(nome)}
            if f'ck_{nome}_validacao' not in checks:
                plano.append({'acao': 'sql', 'sql': f"ALTER TABLE `{nome}` ADD CONSTRAINT `ck_{nome}_validacao` CHECK (status_validacao IS NULL OR status_validacao IN ({ESTADOS}))"})
        indices = {i['name'] for i in insp.get_indexes(nome)}
        for indice in modelo.__table__.indexes:
            if indice.name not in indices:
                plano.append({'acao': 'sql', 'sql': str(CreateIndex(indice).compile(db.engine))})
    if insp.has_table('oferta'):
        unicos = [*insp.get_unique_constraints('oferta'), *[i for i in insp.get_indexes('oferta') if i.get('unique')]]
        if not any(set(i['column_names']) == {'loja', 'produto_id_loja'} for i in unicos):
            plano.append({'acao': 'sql', 'sql': 'CREATE UNIQUE INDEX uq_oferta_loja_produto ON oferta (loja, produto_id_loja)'})
        nomes = {i['name'] for i in insp.get_indexes('oferta')}
        for indice in Oferta.__table__.indexes:
            if indice.name not in nomes:
                plano.append({'acao': 'sql', 'sql': str(CreateIndex(indice).compile(db.engine))})
    if not simular:
        with db.engine.begin() as conn:
            for item in plano:
                if item['acao'] == 'criar_tabela':
                    db.metadata.tables[item['tabela']].create(conn)
                else:
                    conn.execute(text(item['sql']))
    return {'simulacao': simular, 'alteracoes': plano}
