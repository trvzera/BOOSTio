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

#Funcão obrigatória para o login buscar informações do usuario pelo id
@lm.user_loader
def user_loader(id):
    usuario = Usuario.buscar_por_id(id)
    return usuario


__all__ = ['lm','db','Peca','Usuario','ModeloBase','Fonte','Setup']