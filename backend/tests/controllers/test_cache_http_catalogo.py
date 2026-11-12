from unittest.mock import patch

from flask import Flask
from flask_login import LoginManager

from controllers.build_controller import build_bp


def cliente():
    app = Flask(__name__)
    app.config.update(SECRET_KEY='teste', LOGIN_DISABLED=True)
    LoginManager(app)
    app.register_blueprint(build_bp)
    return app.test_client()


def test_catalogo_envia_cache_e_responde_304_quando_nao_mudou():
    with patch('controllers.build_controller.ListarCatalogoBuildService') as servico:
        servico.return_value.executar.return_value = [{'id': 'processador:1'}]
        http = cliente()
        primeira = http.get('/build/catalogo')
        assert primeira.status_code == 200 and primeira.headers['Cache-Control'] == 'private, max-age=60'
        repetida = http.get('/build/catalogo', headers={'If-None-Match': primeira.headers['ETag']})
        assert repetida.status_code == 304
