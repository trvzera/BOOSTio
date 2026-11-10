from sqlalchemy import inspect, text

from models import db


def preparar_administrador_usuario(*, simular=True):
    if db.engine.dialect.name not in ('sqlite', 'mysql'):
        raise ValueError('Banco não suportado')
    inspetor = inspect(db.engine)
    if not inspetor.has_table('usuario'):
        raise ValueError('Inicialize o banco antes de preparar o papel de administrador')
    if 'administrador' in {c['name'] for c in inspetor.get_columns('usuario')}:
        return {'simulacao': simular, 'alteracoes': []}
    comando = 'ALTER TABLE usuario ADD COLUMN administrador BOOLEAN NOT NULL DEFAULT 0'
    if not simular:
        with db.engine.begin() as conexao:
            conexao.execute(text(comando))
    return {'simulacao': simular, 'alteracoes': [comando]}
