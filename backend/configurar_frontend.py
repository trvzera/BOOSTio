"""Execute antes de publicar o frontend; não inicializa o banco nem o servidor."""
import os
from pathlib import Path

from dotenv import load_dotenv

from services.configuracao_service.gerar_configuracao_frontend_service import GerarConfiguracaoFrontendService


if __name__ == "__main__":
    backend = Path(__file__).resolve().parent
    load_dotenv(backend / ".env")
    producao = os.getenv("APP_ENV", "desenvolvimento") == "producao"
    GerarConfiguracaoFrontendService().executar({
      "FRONTEND_URL": os.getenv("FRONTEND_URL") or (None if producao else "http://127.0.0.1:5500/frontend"),
      "API_PUBLIC_URL": os.getenv("API_PUBLIC_URL"),
      "SESSION_COOKIE_SAMESITE": os.getenv("SESSION_COOKIE_SAMESITE", "Lax"),
    }, backend.parent / "frontend/js/config-publica.js", producao=producao)
    print("Endereço público da API preparado para publicação do frontend.")
