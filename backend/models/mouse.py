from . import db
from . import Periferico

class Mouse(Periferico):
    __tablename__ = "mouse"

    dpi_max = db.Column(db.Integer(), nullable=False)
    botoes = db.Column(db.Integer())
    sensor = db.Column(db.String(50))