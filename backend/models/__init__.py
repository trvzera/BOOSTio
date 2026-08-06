from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

#Importante iniciar antes de importar
db = SQLAlchemy()

#Iniciar o flask_login
lm = LoginManager()

#Importar em ordem de heranca
from .base import ModeloBase
from .peca import Peca
from .usuario import Usuario
from .fonte import Fonte
from .setup import Setup





__all__ = ['lm','db','Peca','Usuario','ModeloBase','Fonte','Setup']