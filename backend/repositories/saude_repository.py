from sqlalchemy import text

from models import db


class SaudeRepository:
    """Sonda de conectividade do banco, sem criar ou alterar registros."""

    def verificar_conexao(self):
        db.session.execute(text("SELECT 1"))
