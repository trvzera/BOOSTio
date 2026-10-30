from models import Processador, PlacaMae, MemoriaRAM, SSD


def pecas_estudo_medio():
    comum = {"preco": 0, "esgotado": True}
    return {
        Processador: [
            {**comum, "fabricante": "AMD", "modelo": "Ryzen 5 4600G",
             "part_number": "100-100000147BOX", "kabum_external": "https://www.kabum.com.br/produto/333145/processador-amd-ryzen-5-4600g-3-7ghz-4-2ghz-max-turbo-cache-11mb-am4-video-integrado-100-100000147box",
             "consumo_energia": 65, "soquete": "AM4", "nucleo": 6, "thread": 12,
             "clockbase": 3.7, "clockmax": 4.2, "videointegrado": True,
             "modelo_videointegrado": "Radeon Graphics", "cooler": True,
             "modelo_cooler": "Wraith Stealth"},
            {**comum, "fabricante": "Intel", "modelo": "Core i5-13400",
             "part_number": "BX8071513400", "kabum_external": None,
             "consumo_energia": 65, "soquete": "LGA1700", "nucleo": 10, "thread": 16,
             "clockbase": 2.5, "clockmax": 4.6, "videointegrado": True,
             "modelo_videointegrado": "UHD Graphics 730", "cooler": True,
             "modelo_cooler": "Intel Laminar RM1"},
        ],
        PlacaMae: [
            {**comum, "fabricante": "ASUS", "modelo": "Prime A520M-E",
             "part_number": "90MB1510-C1BAY0", "kabum_external": "https://www.kabum.com.br/produto/129653/placa-mae-asus-prime-a520m-e-amd-am4-matx-ddr4-preto-90mb1510-c1bay0",
             "consumo_energia": 45, "socket": "AM4", "chipset": "A520", "formato": "mATX",
             "tipo_memoria": "DDR4", "quantidade_slots_ram": 2,
             "memoria_maxima_gb": 64, "quantidade_slots_m2": 1},
            {**comum, "fabricante": "MSI", "modelo": "PRO H610M-E DDR4",
             "part_number": "PRO-H610M-E-DDR4", "kabum_external": "https://www.kabum.com.br/produto/524359/placa-mae-msi-pro-h610m-e-ddr4-intel-lga-1700-m-atx-ddr4-preto-pro-h610m-e-ddr4",
             "consumo_energia": 45, "socket": "LGA1700", "chipset": "H610", "formato": "mATX",
             "tipo_memoria": "DDR4", "quantidade_slots_ram": 2,
             "memoria_maxima_gb": 64, "quantidade_slots_m2": 1},
            {**comum, "fabricante": "Gigabyte", "modelo": "A520M S2H",
             "part_number": "A520M-S2H", "kabum_external": "https://www.kabum.com.br/produto/594688/placa-mae-gigabyte-a520m-s2h-micro-atx-soquete-am4-2xddr4-64gb-1x-d-sub-1x-dvi-d-1x-hdmi-4x-usb-3-2-2x-usb-2-0",
             "consumo_energia": 45, "socket": "AM4", "chipset": "A520", "formato": "mATX",
             "tipo_memoria": "DDR4", "quantidade_slots_ram": 2,
             "memoria_maxima_gb": 64, "quantidade_slots_m2": 1},
        ],
        MemoriaRAM: [
            {**comum, "fabricante": "Kingston", "modelo": "Fury Beast DDR4 16GB 3200",
             "part_number": "KF432C16BB1/16", "kabum_external": "https://www.kabum.com.br/produto/309631/memoria-kingston-fury-beast-16gb-3200mhz-ddr4-cl16-preto-kf432c16bb1-16",
             "consumo_energia": 5, "capacidade_gb": 16, "ddr": "DDR4",
             "frequencia_mhz": 3200, "latencia": "CL16", "quantidade_pentes": 1,
             "iluminacao": False},
        ],
        SSD: [
            {**comum, "fabricante": "WD", "modelo": "Blue SN580 1TB",
             "part_number": "WDS100T3B0E", "kabum_external": "https://www.kabum.com.br/produto/495571/ssd-wd-blue-sn580-nvme-1t-m-2-pcle-gen4-leitura-4150-e-gravacao-4150-azul-wds100t3b0e",
             "consumo_energia": 4, "capacidade_gb": 1000, "tipo": "NVMe",
             "interface": "PCIe 4.0", "formato": "M.2",
             "velocidade_leitura_mbps": 4150, "velocidade_gravacao_mbps": 4150},
        ],
    }
