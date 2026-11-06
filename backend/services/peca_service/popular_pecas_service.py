from .dados_seed import dados_seed
from models import (
  Processador,
  PlacaMae,
  PlacaVideo,
  MemoriaRAM,
  SSD,
  HD,
  Fonte,
  Gabinete,
  WaterCooler,
  AirCooler,
  Fan,
  Fone,
  Teclado,
  Mouse,
  Monitor,
  PlacaRede,
  CaboRede,
)
from .atualizar_precos_service import AtualizarPrecosService
from .restaurar_links_kabum_service import RestaurarLinksKabumService
from .pecas_estudo_medio import pecas_estudo_medio
from .pecas_basicas_medias import pecas_basicas_medias
from .pecas_complementares import pecas_complementares


class PopularPecasService:
  def executar(self, limite: int | None = None, intervalo: float = 1.0, atualizar_precos: bool = True):
    for classe, itens in dados_seed().items():
      self._popular_classe(classe, itens)
    self._atualizar_links_rede()
    RestaurarLinksKabumService().executar()
    self._aplicar_vinculos_revisados()
    if atualizar_precos:
      return AtualizarPrecosService().executar(limite=limite, intervalo=intervalo)

  @staticmethod
  def _aplicar_vinculos_revisados():
    from models import VinculoMercadoLivre
    from services.mercadolivre_service.importar_vinculos_revisados_service import ImportarVinculosRevisadosService
    if not VinculoMercadoLivre.tabela_preparada():
      print('[seed] Prepare as tabelas de ofertas para importar os vínculos Mercado Livre revisados')
      return
    resumo = ImportarVinculosRevisadosService().executar(simular=False)
    print(f"[seed] Mercado Livre: {resumo['cadastrados']} vínculos novos, {resumo['inalterados']} inalterados, {resumo['revisao']} pendentes")

  @staticmethod
  def _atualizar_links_rede():
    PlacaRede.atualizar_links_antigos({
      "https://www.kabum.com.br/produto/1049525/adaptador-wi-fi-tp-link-archer-t2u-plus-ac600-dual-band-usb-2-0-600mbps-antena-externa-compativel-windows-mac":
        "https://www.kabum.com.br/produto/173198/adaptador-wireless-tp-link-archer-t2u-plus-ac600-usb-dual-band",
      "https://www.kabum.com.br/produto/101797/adaptador-wireless-tp-link-usb-3-0-ac1300-archer-t3u":
        "https://www.kabum.com.br/produto/169217/adaptador-de-rede-tp-link-archer-t3u-wireless-omni-direcional-usb-mini-dual-band-mu-mimo-ac1300",
    })

  def _popular_classe(self, classe, itens: list[dict]) -> None:
    novos = classe.cadastrar_ausentes(itens)
    print(f"[seed] {classe.__name__}: {novos} inseridos, {len(itens) - novos} já cadastrados")
