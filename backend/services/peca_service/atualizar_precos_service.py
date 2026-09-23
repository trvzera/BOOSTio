from models import db,PlacaMae,PlacaVideo,Processador,SSD,WaterCooler
from ..scapring_service.buscar_dados_scapring_service import BuscarDadosScapringService,ProdutoEsgotadoError,PrecoNaoEncontradoError

class AtualizarPrecosService:
  def executar(self):
    modelos = [
      PlacaMae,
      Processador,
      SSD,
      PlacaVideo,
      WaterCooler
    ]

    pecas_atualizadas = []
    links_de_busca = 0
    falhas = 0
    scraper = BuscarDadosScapringService()

    try:
      for modelo in modelos:
        pecas = modelo.mostrar_pecas()

        for peca in pecas:
          if "/produto/" not in (peca.link or ""):
            links_de_busca += 1
            continue

          try:
            preco_atual = scraper.executar(peca.link)
          except (ProdutoEsgotadoError, PrecoNaoEncontradoError, ValueError) as e:
            print(f"[AtualizarPrecos] {peca.modelo}: {e} | {peca.link}")
            falhas += 1
            continue
          except Exception as e:
            print(f"[AtualizarPrecos] {peca.modelo}: erro ao acessar {peca.link}: {e}")
            falhas += 1
            continue

          if preco_atual is not None and preco_atual != peca.preco:
            peca.preco = preco_atual
            pecas_atualizadas.append(peca)

      db.session.commit()

      print(
        f"[AtualizarPrecos] {len(pecas_atualizadas)} precos atualizados, {falhas} falhas, "
        f"{links_de_busca} pecas ignoradas por ainda terem link de busca (sem link de produto)"
      )

    except Exception:
        db.session.rollback()
        raise

    return pecas_atualizadas
