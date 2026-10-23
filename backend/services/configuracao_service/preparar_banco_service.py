import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4
from sqlalchemy import inspect

from models import db
from migrations.budget_usuario import migrar_budget
from migrations.google_usuario import migrar_google_usuario
from migrations.sessao_usuario import migrar_sessao_usuario
from migrations.tokens_recuperacao import migrar_tokens_recuperacao
from migrations.imagens_pecas import migrar_imagens_pecas
from migrations.rede_build import migrar_rede_build
from migrations.codigos_email import migrar_codigos_email
from services.peca_service.migrar_links_service import MigrarLinksService


class PrepararBancoService:
  def executar(self):
    if db.engine.dialect.name == "mysql":
      if inspect(db.engine).get_table_names():
        raise ValueError("MySQL já contém tabelas; aplique migrações versionadas antes de alterar o esquema")
      db.create_all()
      return {"backup": None, "mensagem": "Banco MySQL novo preparado"}
    if db.engine.dialect.name != "sqlite":
      raise ValueError("Banco não suportado pelo comando banco-preparar")
    caminho = db.engine.url.database
    backup = self._backup(caminho)
    db.create_all()
    if caminho and caminho != ":memory:":
      migrar_budget(caminho)
    migrar_google_usuario()
    migrar_sessao_usuario()
    migrar_tokens_recuperacao()
    migrar_imagens_pecas()
    migrar_rede_build()
    migrar_codigos_email()
    MigrarLinksService().executar()
    return {"backup": backup, "mensagem": "Banco preparado"}

  def _backup(self, caminho):
    if not caminho or caminho == ":memory:" or not Path(caminho).is_file():
      return None
    origem = Path(caminho).resolve()
    destino = origem.with_name(f"{origem.stem}.antes-migracao-{uuid4().hex}.db")
    destino.touch(mode=0o600, exist_ok=False)
    with closing(sqlite3.connect(origem.as_uri() + "?mode=ro", uri=True)) as banco:
      with closing(sqlite3.connect(destino)) as copia:
        banco.backup(copia)
    return str(destino)
