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
from .preferencias_uso import PreferenciasUso
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
from .placa_rede import PlacaRede
from .cabo_rede import CaboRede
from .setup import Setup
from .codigo import Codigo
from .build import Build
from .build_salva import BuildSalva
from .token_recuperacao import TokenRecuperacao
from .consulta_preco import ConsultaPreco, ControleColeta
from .historico_preco import HistoricoPreco
from .oferta import Oferta
from .produto_pendente import ProdutoPendente
from .execucao_descoberta import ExecucaoDescoberta
from .estado_catalogo import EstadoCatalogo
from .vinculo_mercado_livre import VinculoMercadoLivre
from .historico_oferta import HistoricoOferta
from .token_integracao import TokenIntegracao
from .autorizacao_mercado_livre import AutorizacaoMercadoLivre
from .identidade_fabricante import IdentidadeFabricante
from .revisao_identidade_peca import RevisaoIdentidadePeca
from .ficha_tecnica_catalogo import FichaTecnicaCatalogo, RevisaoFichaTecnica

from .tarefa_marketplace import TarefaMarketplace, LimiteMarketplace

# Preço e link das peças vêm das ofertas; depende de todos os models acima.
from .preco_oferta import instalar_precos_derivados
instalar_precos_derivados()

#Funcão obrigatória para o login buscar informações do usuario pelo id
@lm.user_loader
def user_loader(id: str) -> Usuario | None:
    usuario = Usuario.buscar_por_sessao(id)
    return usuario


__all__ = [
    'lm','db','Peca','Periferico','Usuario','PreferenciasUso','ModeloBase','Fonte',
    'Processador','PlacaMae','PlacaVideo','MemoriaRAM','SSD','HD',
    'Gabinete','WaterCooler','AirCooler','Fan','Fone','Teclado','Mouse','Monitor',
    'PlacaRede','CaboRede','RevisaoIdentidadePeca','FichaTecnicaCatalogo','RevisaoFichaTecnica',
    'Setup','Codigo','TokenRecuperacao','Build','BuildSalva','ConsultaPreco','ControleColeta','HistoricoPreco','Oferta','ProdutoPendente','ExecucaoDescoberta','EstadoCatalogo','TokenIntegracao','VinculoMercadoLivre','HistoricoOferta','IdentidadeFabricante','AutorizacaoMercadoLivre'
]
