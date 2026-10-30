import json
from pathlib import Path

from flask import Flask

from .configurar_acesso_service import ConfigurarAcessoService


class GerarConfiguracaoFrontendService:
  def executar(self, configuracao, destino, producao=False):
    if not isinstance(configuracao, dict):
        raise ValueError("Informe configuracao como um objeto válido")

    app = Flask(__name__)
    app.config.update(configuracao)
    ConfigurarAcessoService().executar(app, producao=producao)

    api = app.config.get("API_PUBLIC_URL") or ""
    Path(destino).write_text(
      "// Gerado a partir do endereço público no ambiente do backend.\n"
      f"export const API_PUBLICA = {json.dumps(api)};\n", encoding="utf-8",
    )
