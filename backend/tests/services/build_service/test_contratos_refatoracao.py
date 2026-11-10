from services.peca_service.dados_seed import dados_seed
from services.build_service.prompt_build_service import criar_prompt
"""Referência anterior à reorganização: prompts, seed e esquema persistente."""
import hashlib
import json
from pathlib import Path

from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import mysql, sqlite
from models import db
from services.build_service.criar_build_service import CriarBuildService
from services.peca_service.popular_pecas_service import PopularPecasService

REFERENCIA = Path(__file__).parents[2] / 'fixtures' / 'refatoracao' / 'contratos.json'


def _hash(valor):
    return hashlib.sha256(valor.encode()).hexdigest()


def contratos():
    resultado = {}
    for prioridade in ('desempenho', 'custo_beneficio'):
        for percentual in (0, 20):
            pedido = dict(nome='PC', descricao='Teste', utilidade='Jogos', orcamento=8000,
                          prioridade_montagem=prioridade, armazenamento_minimo_gb=500)
            prompt = criar_prompt(pedido, 8000, 2000, {}, percentual,
                plano_perifericos={'viavel': True, 'combinacoes': []}, preferencia_neutra=True)
            resultado[f'prompt:{prioridade}:{percentual}'] = _hash(prompt)
    dados = dados_seed()
    resultado['seed'] = _hash(json.dumps({m.__tablename__: v for m,v in dados.items()}, sort_keys=True, default=str))
    for nome, dialect in [('sqlite', sqlite.dialect()), ('mysql', mysql.dialect())]:
        ddl = []
        for tabela in sorted(db.metadata.tables.values(), key=lambda t:t.name):
            if tabela.name in {"tarefa_marketplace", "limite_marketplace"}:
                continue
            ddl.append(str(CreateTable(tabela).compile(dialect=dialect)))
            ddl.extend(sorted(str(CreateIndex(i).compile(dialect=dialect)) for i in tabela.indexes))
        resultado['esquema:' + nome] = _hash('\n'.join(ddl))
    return resultado


def test_contratos_anteriores_a_refatoracao():
    assert contratos() == json.loads(REFERENCIA.read_text())
