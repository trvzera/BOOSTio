from app import app
from services.mercadolivre_scapring_service.mercado_livre_scapring_service import MercadoLivreScapringService

with app.app_context():
    s = MercadoLivreScapringService()
    print(s.obter_preco_catalogo("MLB19444510"))