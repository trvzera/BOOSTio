import csv
import json
from decimal import Decimal

from flask import Flask
import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError

from models import db, Processador, PlacaVideo
from commands.benchmarks import registrar_comandos_benchmarks
from migrations.benchmarks_pecas import migrar_benchmarks_pecas
from services.benchmark_service.importar_benchmarks_service import (
    ImportarBenchmarksService, normalizar_nome, pontuacao,
)


@pytest.fixture
def banco(tmp_path):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{tmp_path / 'teste.db'}"
    db.init_app(app)
    registrar_comandos_benchmarks(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def peca(nome, gpu=False):
    comum = dict(fabricante='NVIDIA' if gpu else 'AMD', modelo=nome, preco=999, consumo_energia=65)
    obj = PlacaVideo(**comum, memoria_gb=8) if gpu else Processador(
        **comum, soquete='AM4', nucleo=6, thread=12, clockbase=3, clockmax=4)
    db.session.add(obj)
    db.session.commit()
    return obj


def arquivo(tmp_path, linhas, gpu=False):
    path = tmp_path / ('gpu.csv' if gpu else 'cpu.csv')
    with path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'g2d', 'g3d'] if gpu else ['name', 'cpumark', 'single_thread', 'cores', 'threads'])
        writer.writerows(linhas if gpu else [list(l) + [6, 12] for l in linhas])
    return path


def test_simulacao_idempotencia_e_campos_preservados(banco, tmp_path):
    obj = peca('Ryzen 5 5600X')
    antes = obj.atualizado_em
    path = arquivo(tmp_path, [('AMD Ryzen™ 5 5600X', '22,000.00', '3000')])
    servico = ImportarBenchmarksService()
    resumo = servico.executar(cpu=path, simular=True)
    assert resumo['propostas'] == 1 and resumo['atualizadas'] == 0
    assert obj.benchmark_multi_core is None
    assert servico.executar(cpu=path)['atualizadas'] == 1
    assert obj.benchmark_multi_core == Decimal('22000')
    assert obj.benchmark_single_thread == Decimal('3000')
    assert obj.preco == 999 and obj.atualizado_em == antes
    assert obj.benchmark_versao is None and obj.benchmark_referencia_em is None
    data = obj.benchmark_atualizado_em
    assert servico.executar(cpu=path)['inalteradas'] == 1
    assert obj.benchmark_atualizado_em == data
    assert Processador.query.count() == 1


@pytest.mark.parametrize('a,b', [
    ('RTX 4060', 'RTX 4060 Laptop GPU'), ('RTX 4060', 'RTX 4060 Ti'),
    ('RTX 4070', 'RTX 4070 SUPER'), ('RX 7900 XT', 'RX 7900 XTX'),
    ('Core i5-13400', 'Core i5-13400F'), ('Ryzen 7 5800X', 'Ryzen 7 5800X3D'),
    ('RTX 3060', 'RTX 3060 Mobile'), ('Core i5-12400', 'Core i5-13400'),
])
def test_normalizacao_preserva_variantes(a, b):
    assert normalizar_nome(a) != normalizar_nome(b)


@pytest.mark.parametrize('a,b', [('Intel® Core™ i5-13400F', ' intel Core i5 13400F '),
                                  ('GeForce RTX 4060 Ti', 'geforce RTX 4060Ti'),
                                  ('RX 7900 XT', 'rx 7900xt')])
def test_normalizacao_equivalente(a, b):
    assert normalizar_nome(a) == normalizar_nome(b)


def test_gpu_notebook_e_sufixos_nao_associam_desktop(banco, tmp_path):
    desktop = peca('GeForce RTX 4060', gpu=True)
    notebook = peca('GeForce RTX 4060 Laptop GPU', gpu=True)
    path = arquivo(tmp_path, [('GeForce RTX 4060 Laptop GPU', 500, 15000),
                              ('GeForce RTX 4060 Ti', 700, 20000)], gpu=True)
    r = ImportarBenchmarksService().executar(gpu=path)
    assert r['atualizadas'] == 1 and r['nao_encontradas'] == 1
    assert desktop.benchmark_g3d is None
    assert notebook.benchmark_g2d == 500 and notebook.benchmark_g3d == 15000


def test_exata_prioritaria_e_ambiguidades(banco, tmp_path):
    primeiro = peca('Ryzen 5 5600X')
    segundo = peca('RYZEN 5 5600X')
    path = arquivo(tmp_path, [('Ryzen 5 5600X', 100, 50)])
    assert ImportarBenchmarksService().executar(cpu=path)['atualizadas'] == 1
    assert primeiro.benchmark_multi_core == 100 and segundo.benchmark_multi_core is None
    path = arquivo(tmp_path, [('ryzen 5 5600x', 200, 80)])
    r = ImportarBenchmarksService().executar(cpu=path)
    assert r['ambiguas'] == 1 and r['atualizadas'] == 0
    assert primeiro.benchmark_multi_core == 100


def test_duplicatas_conflitantes_e_equivalentes(banco, tmp_path):
    obj = peca('Ryzen 5 5600X')
    path = arquivo(tmp_path, [('Ryzen 5 5600X', 100, 50), ('AMD Ryzen 5 5600X', 200, 60)])
    assert ImportarBenchmarksService().executar(cpu=path)['ambiguas'] == 1
    assert obj.benchmark_multi_core is None
    path = arquivo(tmp_path, [('Ryzen 5 5600X', 100, 50)] * 2)
    r = ImportarBenchmarksService().executar(cpu=path)
    assert r['atualizadas'] == 1 and r['duplicadas'] == 1
    path = arquivo(tmp_path, [('Ryzen 5 5600X', 200, 50), ('RYZEN 5 5600X', 300, 60)])
    assert ImportarBenchmarksService().executar(cpu=path)['ambiguas'] == 1
    assert obj.benchmark_multi_core == 100


@pytest.mark.parametrize('valor', ['NaN', 'inf', '-1', '0', '12,34', '1e5', 'abc', '1000000000000'])
def test_pontuacao_invalida(valor):
    with pytest.raises(ValueError):
        pontuacao(valor)


def test_invalidos_e_parciais_preservam_benchmark(banco, tmp_path):
    obj = peca('Ryzen 5 5600X')
    path = arquivo(tmp_path, [('Ryzen 5 5600X', 100, 50)])
    s = ImportarBenchmarksService()
    s.executar(cpu=path)
    data = obj.benchmark_atualizado_em
    for valores in [('', ''), ('NaN', 60), (0, 60)]:
        path = arquivo(tmp_path, [('Ryzen 5 5600X', *valores)])
        assert s.executar(cpu=path)['invalidas'] == 1
        assert obj.benchmark_multi_core == 100 and obj.benchmark_single_thread == 50
        assert obj.benchmark_atualizado_em == data
    path = arquivo(tmp_path, [('Ryzen 5 5600X', '', 60)])
    assert s.executar(cpu=path)['atualizadas'] == 1
    assert obj.benchmark_multi_core == 100 and obj.benchmark_single_thread == 60
    obj.benchmark_teste = 'Outro teste'
    db.session.commit()
    assert s.executar(cpu=path)['invalidas'] == 1


def test_valida_ambos_arquivos_antes_de_gravar_e_cli(banco, tmp_path):
    obj = peca('Ryzen 5 5600X')
    path = arquivo(tmp_path, [('Ryzen 5 5600X', 100, 50)])
    invalido = tmp_path / 'invalido.csv'
    invalido.write_text('<html>erro</html>')
    with pytest.raises(ValueError, match='Cabeçalho'):
        ImportarBenchmarksService().executar(cpu=path, gpu=invalido)
    assert obj.benchmark_multi_core is None
    resultado = banco.test_cli_runner().invoke(args=['benchmarks-importar', '--cpu', str(path), '--simular'])
    assert resultado.exit_code == 0, resultado.output
    assert json.loads(resultado.output)['propostas'] == 1
    assert obj.benchmark_multi_core is None
    assert banco.test_cli_runner().invoke(args=['benchmarks-importar']).exit_code != 0


def test_falha_persistencia_reverte_lote(banco, tmp_path, mocker):
    obj = peca('Ryzen 5 5600X')
    path = arquivo(tmp_path, [('Ryzen 5 5600X', 100, 50)])
    mocker.patch.object(db.session, 'commit', side_effect=SQLAlchemyError('falha'))
    with pytest.raises(RuntimeError, match='0 peças já confirmadas'):
        ImportarBenchmarksService().executar(cpu=path)
    assert obj.benchmark_multi_core is None


def test_migracao_incremental_atomica_idempotente(banco):
    db.session.remove()
    with db.engine.begin() as c:
        c.execute(text('DROP TABLE processador'))
        c.execute(text('DROP TABLE placa_video'))
        c.execute(text('CREATE TABLE processador (id INTEGER PRIMARY KEY, modelo TEXT)'))
        c.execute(text("INSERT INTO processador VALUES (1, 'preservado')"))
        c.execute(text('CREATE TABLE placa_video (id INTEGER PRIMARY KEY, modelo TEXT)'))
    migrar_benchmarks_pecas()
    migrar_benchmarks_pecas()
    with db.engine.connect() as c:
        assert c.execute(text('SELECT modelo, benchmark_multi_core FROM processador')).one() == ('preservado', None)
        assert 'benchmark_g3d' in {r[1] for r in c.execute(text('PRAGMA table_info(placa_video)'))}


@pytest.mark.parametrize('conteudo', [
    b'name,cpumark,single_thread,cores,threads\nCPU,100,50,6\n',
    b'name,cpumark,single_thread,cores,threads\n"CPU,100,50,6,12\n',
    b'\xff\xfe',
    b'name,name,cpumark,single_thread,cores,threads\n',
])
def test_rejeita_arquivo_malformado(banco, tmp_path, conteudo):
    path = tmp_path / 'ruim.csv'
    path.write_bytes(conteudo)
    with pytest.raises(ValueError):
        ImportarBenchmarksService().executar(cpu=path)


def test_falha_leitura_e_lote_invalido(banco, tmp_path):
    with pytest.raises(OSError):
        ImportarBenchmarksService().executar(cpu=tmp_path / 'ausente.csv')
    with pytest.raises(ValueError, match='lote'):
        ImportarBenchmarksService().executar(cpu='qualquer.csv', lote=0)


def test_falha_segundo_lote_preserva_primeiro_e_permite_reexecucao(banco, tmp_path, mocker):
    a, b = peca('Ryzen 5 5600X'), peca('Ryzen 5 5600')
    path = arquivo(tmp_path, [('Ryzen 5 5600X', 100, 50), ('Ryzen 5 5600', 90, 45)])
    commit = db.session.commit
    chamadas = 0

    def confirmar():
        nonlocal chamadas
        chamadas += 1
        if chamadas == 2:
            raise SQLAlchemyError('falha segundo lote')
        commit()

    patch = mocker.patch.object(db.session, 'commit', side_effect=confirmar)
    with pytest.raises(RuntimeError, match='1 peças já confirmadas'):
        ImportarBenchmarksService().executar(cpu=path, lote=1)
    mocker.stop(patch)
    assert a.benchmark_multi_core == 100 and b.benchmark_multi_core is None
    r = ImportarBenchmarksService().executar(cpu=path, lote=1)
    assert r['atualizadas'] == 1 and r['inalteradas'] == 1


def test_migracao_reverte_ddl_se_uma_tabela_falhar(banco):
    db.session.remove()
    with db.engine.begin() as c:
        for tabela in ('processador', 'placa_video'):
            c.execute(text(f'DROP TABLE {tabela}'))
            c.execute(text(f'CREATE TABLE {tabela} (id INTEGER PRIMARY KEY)'))

    def falhar(conn, cursor, statement, parameters, context, executemany):
        if 'ALTER TABLE "placa_video"' in statement:
            raise SQLAlchemyError('falha DDL')

    event.listen(db.engine, 'before_cursor_execute', falhar)
    try:
        with pytest.raises(SQLAlchemyError):
            migrar_benchmarks_pecas()
    finally:
        event.remove(db.engine, 'before_cursor_execute', falhar)
    with db.engine.connect() as c:
        assert [r[1] for r in c.execute(text('PRAGMA table_info(processador)'))] == ['id']
