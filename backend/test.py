from services.scapring_service.mercado_livre_scapring_service import MercadoLivreScapringService

service = MercadoLivreScapringService()

produtos = service.executar("Ryzen 7 5700g")