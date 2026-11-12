from sqlalchemy import text

from models import db


class SaudeRepository:

    def verificar_conexao(self):
        db.session.execute(text("SELECT 1"))
