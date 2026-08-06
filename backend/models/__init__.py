from flask_sqlalchemy import SQLAlchemy

#Importante iniciar antes de importar
db = SQLAlchemy()

#Importar em ordem de heranca
from .base import ModeloBase
from .peca import Peca
from .usuario import Usuario
from .fonte import Fonte
from .setup import Setup





__all__ = ['db','Peca','Usuario','ModeloBase','Fonte','Setup']