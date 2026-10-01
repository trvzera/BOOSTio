from datetime import datetime, timedelta, timezone

from . import db
from .base import ModeloBase


class TokensMeli(ModeloBase):
    __tablename__ = "tokens_meli"

    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    data_expiracao = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(hours=6),
        nullable=False,
    )
