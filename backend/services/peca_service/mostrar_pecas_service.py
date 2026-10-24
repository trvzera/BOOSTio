from models import Processador, PlacaMae, PlacaVideo, MemoriaRAM, SSD, HD, Fonte

class MostrarPecasService:
    def executar(self):
        try:
            processadores = Processador.mostrar_pecas()
            placas_mae = PlacaMae.mostrar_pecas()
            placas_video = PlacaVideo.mostrar_pecas()
            memorias_ram = MemoriaRAM.mostrar_pecas()
            armazenamentos = SSD.mostrar_pecas() + HD.mostrar_pecas()
            fontes = Fonte.mostrar_pecas()

            pecas = {
                "processadores": [processador.to_catalogo() for processador in processadores],
                "placas_mae": [placa_mae.to_catalogo() for placa_mae in placas_mae],
                "placas_video": [placa_video.to_catalogo() for placa_video in placas_video],
                "memorias_ram": [memoria_ram.to_catalogo() for memoria_ram in memorias_ram],
                "armazenamentos": [armazenamento.to_catalogo() for armazenamento in armazenamentos],
                "fontes": [fonte.to_catalogo() for fonte in fontes]
            }

            return pecas

        except Exception as e:
            raise ValueError(f"Erro ao buscar as peças: {str(e)}")
