from models import db,Peca,PlacaMae,PlacaVideo,Processador,SSD,WaterCooler
from ..scapring_service.buscar_dados_scapring_service import BuscarDadosScapringService

class AtualizarPrecosService:
  def executar(self):
    modelos = [
      PlacaMae,
      Peca,
      Processador,
      SSD,
      PlacaVideo,
      WaterCooler
    ]

    pecas_atualizadas = []

    try:
      for modelo in modelos:
        pecas = modelo.mostrar_pecas()

        for peca in pecas:
          preco_atual = BuscarDadosScapringService().executar(peca.link)

          if preco_atual != peca.preco:
            peca.preco = preco_atual
            pecas_atualizadas.append(peca)

        db.session.commit()

        return pecas_atualizadas

    except Exception:
        db.session.rollback()
        raise

    return pecas_atualizadas
