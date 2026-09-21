from urllib.parse import quote_plus

from models import (
  db,
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
)
from services.scapring_service.buscar_link_produto_service import BuscarLinkProdutoService


def _link_busca_kabum(fabricante: str, modelo: str) -> str:
  return f"https://www.kabum.com.br/busca/{quote_plus(f'{fabricante} {modelo}')}"


class PopularPecasService:
  """Garante pelo menos 10 registros cadastrados para cada tipo de peça."""

  QUANTIDADE_MINIMA = 10
  #Palavra usada na busca da kabum e que precisa aparecer no nome do produto encontrado
  CATEGORIAS_KABUM = {
    Processador: "Processador",
    PlacaMae: "Placa Mãe",
    PlacaVideo: "Placa de Vídeo",
    MemoriaRAM: "Memória",
    SSD: "SSD",
    HD: "HD",
    Fonte: "Fonte",
    Gabinete: "Gabinete",
    WaterCooler: "Water Cooler",
    AirCooler: "Cooler",
    Fan: "Fan",
    Fone: "Headset",
    Teclado: "Teclado",
    Mouse: "Mouse",
    Monitor: "Monitor",
  }

  def __init__(self) -> None:
    self._buscar_link = BuscarLinkProdutoService()

  def executar(self) -> None:
    for classe, itens in self._dados_seed().items():
      self._popular_classe(classe, itens)

  def _popular_classe(self, classe, itens: list[dict]) -> None:
    com_link_produto = 0
    existentes = {
      item["part_number"]: classe.query.filter_by(part_number=item["part_number"]).first()
      for item in itens
    }
    #Peca que ja tem o link da pagina do produto nao precisa buscar de novo
    pendentes = [
      item for item in itens
      if not existentes[item["part_number"]] or "/busca/" in existentes[item["part_number"]].link
    ]
    com_link_produto += len(itens) - len(pendentes)

    for item in pendentes:
      ja_existe = existentes[item["part_number"]]
      #Uma busca por vez: em paralelo a kabum passa a recusar as requisicoes
      link = self._link_produto(classe, item)

      if link:
        com_link_produto += 1

      if ja_existe:
        #Peca criada antes com link de busca: so troca se achou a pagina do produto
        if link:
          ja_existe.link = link
        continue

      item = dict(item)
      #Se a kabum nao tiver o produto, fica o link de busca (a coluna link nao aceita vazio)
      item["link"] = link or _link_busca_kabum(item["fabricante"], item["modelo"])

      db.session.add(classe(**item))

    db.session.commit()
    print(f"[kabum] {classe.__name__}: {com_link_produto}/{len(itens)} com link da página do produto")

  def _link_produto(self, classe, item: dict) -> str | None:
    #Nas placas de video o fabricante (NVIDIA/AMD) e do chip, nao aparece no nome do produto
    return self._buscar_link.executar(
      item["fabricante"],
      item["modelo"],
      self.CATEGORIAS_KABUM[classe],
      exigir_fabricante=classe is not PlacaVideo,
    )

  def _dados_seed(self) -> dict:
    return {
      Processador: self._processadores(),
      PlacaMae: self._placas_mae(),
      PlacaVideo: self._placas_video(),
      MemoriaRAM: self._memorias_ram(),
      SSD: self._ssds(),
      HD: self._hds(),
      Fonte: self._fontes(),
      Gabinete: self._gabinetes(),
      WaterCooler: self._water_coolers(),
      AirCooler: self._air_coolers(),
      Fan: self._fans(),
      Fone: self._fones(),
      Teclado: self._teclados(),
      Mouse: self._mouses(),
      Monitor: self._monitores(),
    }

  def _processadores(self) -> list[dict]:
    base = [
      ("AMD", "Ryzen 5 5600", "AM4", 6, 12, 3.5, 4.4, True, "Radeon Vega", True, "Wraith Stealth", 65),
      ("AMD", "Ryzen 7 5700X", "AM4", 8, 16, 3.4, 4.6, False, None, False, None, 65),
      ("AMD", "Ryzen 5 7600", "AM5", 6, 12, 3.8, 5.1, True, "Radeon Graphics", True, "Wraith Stealth", 65),
      ("AMD", "Ryzen 7 7700X", "AM5", 8, 16, 4.5, 5.4, True, "Radeon Graphics", False, None, 105),
      ("AMD", "Ryzen 9 7900X", "AM5", 12, 24, 4.7, 5.6, True, "Radeon Graphics", False, None, 170),
      ("Intel", "Core i3-12100F", "LGA1700", 4, 8, 3.3, 4.3, False, None, False, None, 58),
      ("Intel", "Core i5-12400F", "LGA1700", 6, 12, 2.5, 4.4, False, None, False, None, 65),
      ("Intel", "Core i5-13400F", "LGA1700", 10, 16, 2.5, 4.6, False, None, False, None, 65),
      ("Intel", "Core i7-13700K", "LGA1700", 16, 24, 3.4, 5.4, True, "UHD Graphics 770", False, None, 125),
      ("Intel", "Core i9-14900K", "LGA1700", 24, 32, 3.2, 6.0, True, "UHD Graphics 770", False, None, 125),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": consumo,
        "preco": preco,
        "part_number": f"SEED-CPU-{indice:02d}",
        "soquete": soquete,
        "nucleo": nucleo,
        "thread": thread,
        "clockbase": clockbase,
        "clockmax": clockmax,
        "videointegrado": videointegrado,
        "modelo_videointegrado": modelo_videointegrado,
        "cooler": cooler,
        "modelo_cooler": modelo_cooler,
      }
      for indice, (
        fabricante, modelo, soquete, nucleo, thread, clockbase, clockmax,
        videointegrado, modelo_videointegrado, cooler, modelo_cooler, consumo,
      ) in enumerate(base, start=1)
      for preco in [self._preco(indice, 650, 180)]
    ]

  def _placas_mae(self) -> list[dict]:
    base = [
      ("ASUS", "Prime A520M-K", "AM4", "A520", "mATX", "DDR4", 2, 64, 1),
      ("ASUS", "TUF Gaming B550-Plus", "AM4", "B550", "ATX", "DDR4", 4, 128, 2),
      ("Gigabyte", "B550M DS3H", "AM4", "B550", "mATX", "DDR4", 4, 128, 1),
      ("Gigabyte", "B650M DS3H", "AM5", "B650", "mATX", "DDR5", 4, 128, 2),
      ("ASRock", "B450M Steel Legend", "AM4", "B450", "mATX", "DDR4", 4, 64, 1),
      ("ASUS", "Prime B660M-A", "LGA1700", "B660", "mATX", "DDR4", 4, 128, 2),
      ("MSI", "PRO B760M-P", "LGA1700", "B760", "mATX", "DDR5", 4, 128, 2),
      ("MSI", "MAG B650 Tomahawk", "AM5", "B650", "ATX", "DDR5", 4, 128, 2),
      ("Gigabyte", "Z790 Aorus Elite", "LGA1700", "Z790", "ATX", "DDR5", 4, 128, 3),
      ("ASRock", "X670E Steel Legend", "AM5", "X670E", "ATX", "DDR5", 4, 128, 3),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 45.0,
        "preco": self._preco(indice, 500, 90),
        "part_number": f"SEED-MB-{indice:02d}",
        "socket": socket,
        "chipset": chipset,
        "formato": formato,
        "tipo_memoria": tipo_memoria,
        "quantidade_slots_ram": slots_ram,
        "memoria_maxima_gb": memoria_max,
        "quantidade_slots_m2": slots_m2,
      }
      for indice, (
        fabricante, modelo, socket, chipset, formato, tipo_memoria,
        slots_ram, memoria_max, slots_m2,
      ) in enumerate(base, start=1)
    ]

  def _placas_video(self) -> list[dict]:
    base = [
      ("NVIDIA", "GeForce GTX 1660 Super", 6, "GDDR6", "192-bit", 125, 1),
      ("NVIDIA", "GeForce RTX 3060", 12, "GDDR6", "192-bit", 170, 2),
      ("NVIDIA", "GeForce RTX 3060 Ti", 8, "GDDR6", "256-bit", 200, 2),
      ("NVIDIA", "GeForce RTX 4060", 8, "GDDR6", "128-bit", 115, 2),
      ("NVIDIA", "GeForce RTX 4060 Ti", 8, "GDDR6", "128-bit", 160, 2),
      ("NVIDIA", "GeForce RTX 4070", 12, "GDDR6X", "192-bit", 200, 3),
      ("NVIDIA", "GeForce RTX 4070 Super", 12, "GDDR6X", "192-bit", 220, 3),
      ("AMD", "Radeon RX 6600", 8, "GDDR6", "128-bit", 132, 2),
      ("AMD", "Radeon RX 6700 XT", 12, "GDDR6", "192-bit", 230, 3),
      ("AMD", "Radeon RX 7600", 8, "GDDR6", "128-bit", 165, 2),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": float(consumo_w),
        "preco": self._preco(indice, 1400, 250),
        "part_number": f"SEED-GPU-{indice:02d}",
        "memoria_gb": memoria_gb,
        "tipo_memoria": tipo_memoria,
        "interface_memoria": interface_memoria,
        "consumo_w": consumo_w,
        "quantidade_fans": fans,
        "conectores_energia": "1x 8-pin" if consumo_w < 180 else "1x 12-pin",
      }
      for indice, (
        fabricante, modelo, memoria_gb, tipo_memoria, interface_memoria, consumo_w, fans,
      ) in enumerate(base, start=1)
    ]

  def _memorias_ram(self) -> list[dict]:
    base = [
      ("Kingston", "Fury Beast 8GB", 8, "DDR4", 3200, "CL16", 1),
      ("Kingston", "Fury Beast 16GB (2x8GB)", 16, "DDR4", 3200, "CL16", 2),
      ("Kingston", "Fury Beast 16GB", 16, "DDR5", 5600, "CL36", 1),
      ("Corsair", "Vengeance LPX 16GB (2x8GB)", 16, "DDR4", 3200, "CL16", 2),
      ("Corsair", "Vengeance RGB 32GB (2x16GB)", 32, "DDR5", 6000, "CL30", 2),
      ("XPG", "Gammix D30 8GB", 8, "DDR4", 3000, "CL16", 1),
      ("Adata", "XPG Lancer 16GB", 16, "DDR5", 6000, "CL30", 1),
      ("TeamGroup", "T-Force Vulcan 16GB (2x8GB)", 16, "DDR4", 3200, "CL16", 2),
      ("Crucial", "Basics 8GB", 8, "DDR4", 2666, "CL19", 1),
      ("G.Skill", "Trident Z5 32GB (2x16GB)", 32, "DDR5", 6400, "CL32", 2),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 5.0,
        "preco": self._preco(indice, 700, 90),
        "part_number": f"SEED-RAM-{indice:02d}",
        "capacidade_gb": capacidade_gb,
        "ddr": ddr,
        "frequencia_mhz": frequencia,
        "latencia": latencia,
        "quantidade_pentes": pentes,
        "iluminacao": False,
      }
      for indice, (
        fabricante, modelo, capacidade_gb, ddr, frequencia, latencia, pentes,
      ) in enumerate(base, start=1)
    ]

  def _ssds(self) -> list[dict]:
    base = [
      ("Kingston", "NV2 500GB", 500, "NVMe", "PCIe 4.0", "M.2", 3500, 2100),
      ("Kingston", "NV2 1TB", 1000, "NVMe", "PCIe 4.0", "M.2", 3500, 2800),
      ("Crucial", "MX500 500GB", 500, "SATA", "SATA III", "2.5", 560, 510),
      ("Crucial", "P3 1TB", 1000, "NVMe", "PCIe 3.0", "M.2", 3500, 3000),
      ("Samsung", "970 EVO Plus 500GB", 500, "NVMe", "PCIe 3.0", "M.2", 3500, 3200),
      ("Samsung", "980 1TB", 1000, "NVMe", "PCIe 3.0", "M.2", 3500, 3000),
      ("WD", "Green 480GB", 480, "SATA", "SATA III", "2.5", 545, 465),
      ("WD", "Black SN770 1TB", 1000, "NVMe", "PCIe 4.0", "M.2", 5150, 4900),
      ("Adata", "Legend 800 500GB", 500, "NVMe", "PCIe 4.0", "M.2", 3500, 2200),
      ("TeamGroup", "MP34 512GB", 512, "NVMe", "PCIe 3.0", "M.2", 3400, 3000),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 4.0,
        "preco": self._preco(indice, 450, 50),
        "part_number": f"SEED-SSD-{indice:02d}",
        "capacidade_gb": capacidade_gb,
        "tipo": tipo,
        "interface": interface,
        "formato": formato,
        "velocidade_leitura_mbps": leitura,
        "velocidade_gravacao_mbps": gravacao,
      }
      for indice, (
        fabricante, modelo, capacidade_gb, tipo, interface, formato, leitura, gravacao,
      ) in enumerate(base, start=1)
    ]

  def _hds(self) -> list[dict]:
    base = [
      ("Seagate", "Barracuda 1TB", 1000, 7200, "SATA III", 64),
      ("Seagate", "Barracuda 2TB", 2000, 7200, "SATA III", 256),
      ("WD", "Blue 1TB", 1000, 7200, "SATA III", 64),
      ("WD", "Blue 2TB", 2000, 5400, "SATA III", 256),
      ("WD", "Purple 4TB", 4000, 5400, "SATA III", 256),
      ("Toshiba", "P300 1TB", 1000, 7200, "SATA III", 64),
      ("Toshiba", "P300 2TB", 2000, 7200, "SATA III", 64),
      ("Seagate", "SkyHawk 2TB", 2000, 5900, "SATA III", 256),
      ("WD", "Black 1TB", 1000, 7200, "SATA III", 64),
      ("Seagate", "Barracuda 4TB", 4000, 5400, "SATA III", 256),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 6.5,
        "preco": self._preco(indice, 350, 40),
        "part_number": f"SEED-HDD-{indice:02d}",
        "capacidade_gb": capacidade_gb,
        "velocidade_rpm": rpm,
        "interface": interface,
        "memoria_cache_mb": cache,
      }
      for indice, (
        fabricante, modelo, capacidade_gb, rpm, interface, cache,
      ) in enumerate(base, start=1)
    ]

  def _fontes(self) -> list[dict]:
    base = [
      ("Corsair", "CV450", 450, "ATX", 78.0),
      ("Corsair", "RM650x", 650, "ATX", 87.0),
      ("EVGA", "500 W1", 500, "ATX", 82.0),
      ("XPG", "Core Reactor 650W", 650, "ATX", 82.0),
      ("Cooler Master", "MWE 550 Bronze", 550, "ATX", 82.0),
      ("Cooler Master", "MWE 650 Gold", 650, "ATX", 87.0),
      ("Gigabyte", "P450B", 450, "ATX", 82.0),
      ("Pichau", "Gaming 550W", 550, "ATX", 80.0),
      ("Thermaltake", "Smart 500W", 500, "ATX", 78.0),
      ("Seasonic", "Focus GX-750", 750, "ATX", 90.0),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": consumo,
        "preco": self._preco(indice, 600, 100),
        "part_number": f"SEED-PSU-{indice:02d}",
        "potencia_w": potencia_w,
        "formato": formato,
      }
      for indice, (
        fabricante, modelo, potencia_w, formato, consumo,
      ) in enumerate(base, start=1)
    ]

  def _gabinetes(self) -> list[dict]:
    base = [
      ("Cooler Master", "MasterBox Q300L", "mATX", "ATX, mATX, ITX", 2, 2, 2, True, 360, 160, True),
      ("Cooler Master", "MasterBox TD500", "ATX", "ATX, mATX, ITX", 4, 2, 3, True, 410, 165, True),
      ("Pichau", "Aeron", "ATX", "ATX, mATX, ITX", 4, 2, 2, True, 350, 160, True),
      ("Redragon", "Deepsea", "mATX", "ATX, mATX, ITX", 2, 2, 1, False, 320, 155, False),
      ("Gamemax", "Vega Vision", "ATX", "ATX, mATX, ITX", 4, 2, 4, True, 380, 165, True),
      ("Xtreme Gamer", "Prisma", "mATX", "mATX, ITX", 2, 1, 1, False, 300, 150, False),
      ("Corsair", "4000D Airflow", "ATX", "ATX, mATX, ITX", 4, 2, 2, True, 360, 170, True),
      ("NZXT", "H510", "ATX", "ATX, mATX, ITX", 4, 2, 2, True, 381, 165, True),
      ("Lian Li", "Lancool 205", "mATX", "mATX, ITX", 2, 1, 3, True, 350, 160, True),
      ("Montech", "Air 100", "mATX", "ATX, mATX, ITX", 2, 2, 3, True, 320, 160, True),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 0.0,
        "preco": self._preco(indice, 400, 60),
        "part_number": f"SEED-CASE-{indice:02d}",
        "formato": formato,
        "formatos_placa_mae": formatos_placa_mae,
        "slots_expansao": slots_expansao,
        "bays_disco": bays_disco,
        "fans_inclusos": fans_inclusos,
        "suporte_water_cooler": suporte_water_cooler,
        "tamanho_max_gpu_mm": tamanho_max_gpu,
        "tamanho_max_cooler_mm": tamanho_max_cooler,
        "painel_vidro": painel_vidro,
      }
      for indice, (
        fabricante, modelo, formato, formatos_placa_mae, slots_expansao, bays_disco,
        fans_inclusos, suporte_water_cooler, tamanho_max_gpu, tamanho_max_cooler, painel_vidro,
      ) in enumerate(base, start=1)
    ]

  def _water_coolers(self) -> list[dict]:
    base = [
      ("Cooler Master", "MasterLiquid ML240L", "Intel/AMD", 240, 2, True),
      ("Cooler Master", "MasterLiquid ML360R", "Intel/AMD", 360, 3, True),
      ("Deepcool", "LS320", "Intel/AMD", 240, 2, True),
      ("Deepcool", "LS520", "Intel/AMD", 240, 2, True),
      ("Corsair", "iCUE H100i", "Intel/AMD", 240, 2, True),
      ("Corsair", "iCUE H150i", "Intel/AMD", 360, 3, True),
      ("NZXT", "Kraken 240", "Intel/AMD", 240, 2, True),
      ("Lian Li", "Galahad 240", "Intel/AMD", 240, 2, True),
      ("ID-Cooling", "AURAFLOW X 240", "Intel/AMD", 240, 2, True),
      ("Pichau", "Fenix 240", "Intel/AMD", 240, 2, True),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 12.0,
        "preco": self._preco(indice, 550, 90),
        "part_number": f"SEED-WCOOL-{indice:02d}",
        "compatibilidade": compatibilidade,
        "tamanho_radiador_mm": radiador,
        "quantidade_fans": fans,
        "iluminacao": iluminacao,
      }
      for indice, (
        fabricante, modelo, compatibilidade, radiador, fans, iluminacao,
      ) in enumerate(base, start=1)
    ]

  def _air_coolers(self) -> list[dict]:
    base = [
      ("Cooler Master", "Hyper 212 Black", "Intel/AMD", 154, True),
      ("Deepcool", "AK400", "Intel/AMD", 129, False),
      ("Deepcool", "Gammaxx 400", "Intel/AMD", 152, True),
      ("Cooler Master", "Hyper H410R", "Intel/AMD", 130, True),
      ("Thermaltake", "UX200", "Intel/AMD", 121, True),
      ("PCYes", "Fantom Beta", "Intel/AMD", 130, True),
      ("Pichau", "Vortex Air 200", "Intel/AMD", 125, True),
      ("Redragon", "Tyr", "Intel/AMD", 155, True),
      ("ID-Cooling", "SE-224-XT", "Intel/AMD", 154, False),
      ("Cooler Master", "Hyper 212 Halo", "Intel/AMD", 155, True),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 3.0,
        "preco": self._preco(indice, 220, 40),
        "part_number": f"SEED-ACOOL-{indice:02d}",
        "compatibilidade": compatibilidade,
        "dimensoes": dimensoes,
        "iluminacao": iluminacao,
      }
      for indice, (
        fabricante, modelo, compatibilidade, dimensoes, iluminacao,
      ) in enumerate(base, start=1)
    ]

  def _fans(self) -> list[dict]:
    base = [
      ("Cooler Master", "SickleFlow 120", 120, 1, True),
      ("Deepcool", "RF120", 120, 1, True),
      ("Corsair", "LL120", 120, 1, True),
      ("NZXT", "Aer RGB 2", 120, 1, True),
      ("Pichau", "Gaming ARGB", 120, 3, True),
      ("Redragon", "GC-F007", 120, 3, True),
      ("Rise Mode", "Wind Z3", 120, 3, True),
      ("Thermaltake", "Riing 12", 120, 1, True),
      ("Cooler Master", "MasterFan MF120", 120, 1, False),
      ("Deepcool", "FC140", 140, 1, True),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 3.5,
        "preco": self._preco(indice, 120, 25),
        "part_number": f"SEED-FAN-{indice:02d}",
        "tamanho_mm": tamanho_mm,
        "quantidade": quantidade,
        "iluminacao": iluminacao,
      }
      for indice, (
        fabricante, modelo, tamanho_mm, quantidade, iluminacao,
      ) in enumerate(base, start=1)
    ]

  def _fones(self) -> list[dict]:
    base = [
      ("HyperX", "Cloud Stinger", "Com fio", True, False, "P2 3.5mm"),
      ("Logitech", "G335", "Com fio", True, False, "P2 3.5mm"),
      ("Razer", "Kraken X", "Com fio", True, False, "USB"),
      ("Corsair", "HS55", "Com fio", True, False, "P2 3.5mm"),
      ("JBL", "Quantum 100", "Com fio", True, False, "P2 3.5mm"),
      ("HyperX", "Cloud II", "Com fio", True, False, "USB"),
      ("Havit", "H2002d", "Com fio", True, False, "P2 3.5mm"),
      ("Redragon", "Zeus", "Com fio", True, True, "USB"),
      ("Logitech", "G435", "Sem fio", True, False, "Bluetooth"),
      ("SteelSeries", "Arctis 1", "Sem fio", True, False, "USB"),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 1.0,
        "preco": self._preco(indice, 350, 60),
        "part_number": f"SEED-HEADSET-{indice:02d}",
        "conexao": conexao,
        "iluminacao": False,
        "tipo": "Headset",
        "microfone": microfone,
        "cancelamento_ruido": cancelamento_ruido,
        "resposta_frequencia": resposta_frequencia,
      }
      for indice, (
        fabricante, modelo, conexao, microfone, cancelamento_ruido, resposta_frequencia,
      ) in enumerate(base, start=1)
    ]

  def _teclados(self) -> list[dict]:
    base = [
      ("Redragon", "Kumara K552", "ABNT2", "Outemu Blue", True, "Padrão"),
      ("Logitech", "G213 Prodigy", "ABNT2", None, False, "Padrão"),
      ("HyperX", "Alloy Core", "ABNT2", None, False, "Padrão"),
      ("Razer", "Cynosa V2", "ABNT2", None, False, "Padrão"),
      ("Corsair", "K55 RGB", "ABNT2", None, False, "Padrão"),
      ("Fortrek", "GK-702", "ABNT2", "Blue", True, "Padrão"),
      ("Redragon", "Karura", "ABNT2", "Outemu Red", True, "Compacto"),
      ("Logitech", "G413", "ABNT2", "Romer-G", True, "Padrão"),
      ("HyperX", "Alloy Origins Core", "ABNT2", "Red", True, "Compacto"),
      ("Motospeed", "CK62", "ABNT2", "Outemu Red", True, "Compacto"),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 2.5,
        "preco": self._preco(indice, 350, 60),
        "part_number": f"SEED-KEYB-{indice:02d}",
        "conexao": "USB",
        "iluminacao": mecanico,
        "layout": layout,
        "switch": switch,
        "mecanico": mecanico,
        "tamanho": tamanho,
      }
      for indice, (
        fabricante, modelo, layout, switch, mecanico, tamanho,
      ) in enumerate(base, start=1)
    ]

  def _mouses(self) -> list[dict]:
    base = [
      ("Logitech", "G203", 8000, 6, "Óptico"),
      ("Redragon", "Cobra", 10000, 7, "Óptico"),
      ("Razer", "DeathAdder Essential", 6400, 5, "Óptico"),
      ("HyperX", "Pulsefire Core", 6200, 7, "Óptico"),
      ("Corsair", "Harpoon RGB", 6000, 6, "Óptico"),
      ("Fortrek", "Vickers", 3200, 6, "Óptico"),
      ("Logitech", "G502 Hero", 25600, 11, "Óptico"),
      ("Razer", "Viper Mini", 8500, 6, "Óptico"),
      ("Redragon", "Ranger", 12400, 7, "Óptico"),
      ("Pichau", "Nyx", 10000, 6, "Óptico"),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 1.0,
        "preco": self._preco(indice, 250, 40),
        "part_number": f"SEED-MOUSE-{indice:02d}",
        "conexao": "USB",
        "iluminacao": True,
        "dpi_max": dpi_max,
        "botoes": botoes,
        "sensor": sensor,
      }
      for indice, (
        fabricante, modelo, dpi_max, botoes, sensor,
      ) in enumerate(base, start=1)
    ]

  def _monitores(self) -> list[dict]:
    base = [
      ("AOC", "24G2", 23.8, "1920x1080", 144, "IPS", 1.0, False),
      ("LG", "24MP400", 23.8, "1920x1080", 75, "IPS", 5.0, False),
      ("Samsung", "T350", 24.0, "1920x1080", 75, "VA", 4.0, False),
      ("AOC", "27G2", 27.0, "1920x1080", 144, "IPS", 1.0, False),
      ("LG", "27GN800", 27.0, "2560x1440", 144, "IPS", 1.0, False),
      ("Dell", "S2721DGF", 27.0, "2560x1440", 165, "IPS", 1.0, False),
      ("Samsung", "Odyssey G5", 27.0, "2560x1440", 144, "VA", 1.0, True),
      ("LG", "UltraGear 24GQ50", 23.8, "1920x1080", 165, "VA", 1.0, False),
      ("BenQ", "GW2480", 23.8, "1920x1080", 60, "IPS", 5.0, False),
      ("AOC", "Q27G3XMN", 27.0, "2560x1440", 165, "VA", 1.0, True),
    ]

    return [
      {
        "fabricante": fabricante,
        "modelo": modelo,
        "consumo_energia": 25.0,
        "preco": self._preco(indice, 1200, 250),
        "part_number": f"SEED-MONITOR-{indice:02d}",
        "conexao": "HDMI/DP",
        "iluminacao": False,
        "tamanho_polegadas": tamanho_polegadas,
        "resolucao": resolucao,
        "taxa_atualizacao_hz": taxa_atualizacao,
        "tipo_painel": tipo_painel,
        "tempo_resposta_ms": tempo_resposta,
        "hdr": hdr,
      }
      for indice, (
        fabricante, modelo, tamanho_polegadas, resolucao, taxa_atualizacao,
        tipo_painel, tempo_resposta, hdr,
      ) in enumerate(base, start=1)
    ]

  @staticmethod
  def _preco(indice: int, base: float, passo: float) -> float:
    return round(base + (indice - 1) * passo, 2)
