from contextlib import nullcontext
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.dialects.mysql import dialect
from migrations import benchmarks_mysql as m
from models import db


def ambiente(completo=False):
    engine, c, i = MagicMock(), MagicMock(), MagicMock()
    engine.dialect = dialect()
    engine.connect.return_value = nullcontext(c)
    c.scalar.return_value = 1
    i.get_table_names.return_value = list(db.metadata.tables)
    i.get_columns.side_effect = lambda nome: [dict(name=x.name, type=x.type, nullable=x.nullable)
        for x in db.metadata.tables[nome].columns if completo or x.name not in m.TABELAS.get(nome, {})]
    return engine, c, i


def executar(engine, insp, simular=True):
    with patch.object(m, 'db') as banco, patch.object(m, 'inspect', side_effect=insp):
        banco.engine, banco.metadata = engine, db.metadata
        return m.atualizar_benchmarks_mysql(simular)


def test_simulacao_nao_escreve_e_libera_lock():
    e, c, i = ambiente()
    r = executar(e, [i])
    assert len(r['alteracoes']) == 16
    assert all('ADD COLUMN' in sql and sql.endswith(' NULL') for sql in r['alteracoes'])
    assert len(c.execute.call_args_list) == 1
    assert 'RELEASE_LOCK' in str(c.execute.call_args.args[0])


def test_aplica_conta_registros_e_repeticao_nao_adiciona_colunas():
    e, c, antes = ambiente()
    _, _, depois = ambiente(True)
    r = executar(e, [antes, depois], False)
    assert len(r['alteracoes']) == c.commit.call_count == 16
    assert set(r['registros_conferidos']) == set(db.metadata.tables)
    assert executar(e, [depois])['alteracoes'] == []


def test_outra_migracao_bloqueia_ddl():
    e, c, i = ambiente()
    i.get_table_names.return_value.remove('usuario')
    with pytest.raises(ValueError, match='Outras migrações'):
        executar(e, [i], False)
    c.commit.assert_not_called()


def test_falha_ddl_libera_lock():
    e, c, i = ambiente()
    def falha(sql):
        if 'ALTER TABLE' in str(sql):
            raise RuntimeError('falha simulada')
    c.execute.side_effect = falha
    with pytest.raises(RuntimeError):
        executar(e, [i], False)
    assert 'RELEASE_LOCK' in str(c.execute.call_args.args[0])


def test_lock_ocupado_bloqueia():
    e, c, i = ambiente()
    c.scalar.return_value = 0
    with pytest.raises(ValueError, match='Outra atualização'):
        executar(e, [], False)
    c.execute.assert_not_called()


def test_contagem_alterada_bloqueia_reabertura():
    e, c, i = ambiente()
    n = len(db.metadata.tables)
    c.scalar.side_effect = [1] + [10]*n + [11]*n
    with pytest.raises(ValueError, match='Contagem de registros mudou'):
        executar(e, [i], False)
    assert 'RELEASE_LOCK' in str(c.execute.call_args.args[0])


def test_cli_simula_por_padrao_e_aplicar_e_explicito():
    from flask import Flask
    from commands.banco import registrar_comandos_banco
    app = Flask(__name__)
    registrar_comandos_banco(app)
    with patch('commands.banco.atualizar_benchmarks_mysql', return_value={'alteracoes': []}) as migrar:
        assert app.test_cli_runner().invoke(args=['banco-atualizar-mysql']).exit_code == 0
        migrar.assert_called_once_with(simular=True)
        assert app.test_cli_runner().invoke(args=['banco-atualizar-mysql', '--aplicar']).exit_code == 0
        assert migrar.call_args.kwargs == {'simular': False}
