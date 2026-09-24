from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail


#Importante iniciar antes de importar
db = SQLAlchemy()

#Iniciar o flask_login
lm = LoginManager()

#Iniciar o flask_mail
mail = Mail()


#Importar em ordem de heranca
from .base import ModeloBase
from .peca import Peca
from .perifericos import Periferico
from .usuario import Usuario
from .fonte import Fonte
from .processador import Processador
from .placa_mae import PlacaMae
from .placa_video import PlacaVideo
from .memoria_ram import MemoriaRAM
from .ssd import SSD
from .hd import HD
from .gabinete import Gabinete
from .water_cooler import WaterCooler
from .air_cooler import AirCooler
from .fan import Fan
from .fone import Fone
from .teclado import Teclado
from .mouse import Mouse
from .monitor import Monitor
from .setup import Setup
from .codigo import Codigo
from .build import Build
from .token_recuperacao import TokenRecuperacao

#Funcão obrigatória para o login buscar informações do usuario pelo id
@lm.user_loader
def user_loader(id: str) -> Usuario | None:
    usuario = Usuario.buscar_por_id(id)
    return usuario


__all__ = [
    'lm','db','Peca','Periferico','Usuario','ModeloBase','Fonte',
    'Processador','PlacaMae','PlacaVideo','MemoriaRAM','SSD','HD',
    'Gabinete','WaterCooler','AirCooler','Fan','Fone','Teclado','Mouse','Monitor',
    'Setup','Codigo','TokenRecuperacao','Build'
]