from models import db,Processador,PlacaMae,PlacaVideo,MemoriaRam,Armazenamento,Fonte

class MostrarPecasService:
    def executar(self):
        try:
            processadores = Processador.query.all()
            placas_mae = PlacaMae.query.all()
            placas_video = PlacaVideo.query.all()
            memorias_ram = MemoriaRam.query.all()
            armazenamentos = Armazenamento.query.all()
            fontes = Fonte.query.all()

            pecas = {
                "processadores": [processador.to_dict() for processador in processadores],
                "placas_mae": [placa_mae.to_dict() for placa_mae in placas_mae],
                "placas_video": [placa_video.to_dict() for placa_video in placas_video],
                "memorias_ram": [memoria_ram.to_dict() for memoria_ram in memorias_ram],
                "armazenamentos": [armazenamento.to_dict() for armazenamento in armazenamentos],
                "fontes": [fonte.to_dict() for fonte in fontes]
            }

            return pecas

        except Exception as e:
            raise ValueError(f"Erro ao buscar as peças: {str(e)}")