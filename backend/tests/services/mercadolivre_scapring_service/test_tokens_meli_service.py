import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from flask import Flask

from controllers.auth_controller import auth_bp
from configs import oauth
from models import TokensMeli, db
from services.mercadolivre_scapring_service.refresh_token_service import RefreshTokenMercadoLivreService
from services.mercadolivre_scapring_service.mercado_livre_scapring_service import MercadoLivreScapringService
from services.mercadolivre_scapring_service.salvar_tokens_service import SalvarTokensMeliService
from services.mercadolivre_scapring_service.consultar_api_service import ConsultarApiMercadoLivreService


class TestTokensMeliService(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SECRET_KEY="chave-de-teste",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        )
        db.init_app(self.app)
        oauth.init_app(self.app)
        self.app.register_blueprint(auth_bp)
        self.contexto = self.app.app_context()
        self.contexto.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.contexto.pop()

    def test_callback_salva_tokens_iniciais(self):
        resposta_meli = {
            "access_token": "access-inicial",
            "refresh_token": "refresh-inicial",
            "expires_in": 21600,
        }

        with patch.object(oauth.mercadolivre, "authorize_access_token", return_value=resposta_meli):
            resposta = self.app.test_client().get("/auth/mercadolivre/entrar")

        tokens = TokensMeli.buscar_atual()
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn(b"access-inicial", resposta.data)
        self.assertEqual(tokens.access_token, "access-inicial")
        self.assertEqual(tokens.refresh_token, "refresh-inicial")
        self.assertEqual(TokensMeli.query.count(), 1)

    def test_refresh_atualiza_ambos_tokens_no_mesmo_registro(self):
        original = SalvarTokensMeliService().executar({
            "access_token": "access-antigo",
            "refresh_token": "refresh-antigo",
            "expires_in": 21600,
        })
        resposta_meli = {
            "access_token": "access-novo",
            "refresh_token": "refresh-novo",
            "expires_in": 3600,
        }
        resposta_http = Mock()
        resposta_http.json.return_value = resposta_meli

        with patch("services.mercadolivre_scapring_service.refresh_token_service.requests.post", return_value=resposta_http) as post:
            retorno = RefreshTokenMercadoLivreService().executar()

        atual = TokensMeli.buscar_atual()
        self.assertEqual(retorno, resposta_meli)
        self.assertEqual(post.call_args.kwargs["data"]["refresh_token"], "refresh-antigo")
        self.assertEqual(atual.id, original.id)
        self.assertEqual(atual.access_token, "access-novo")
        self.assertEqual(atual.refresh_token, "refresh-novo")
        self.assertEqual(TokensMeli.query.count(), 1)
        expira_em = atual.data_expiracao.replace(tzinfo=timezone.utc)
        self.assertLess(abs(expira_em - (datetime.now(timezone.utc) + timedelta(hours=1))), timedelta(seconds=5))

    def test_busca_usa_termo_informado_e_token_do_banco(self):
        SalvarTokensMeliService().executar({
            "access_token": "access-banco", "refresh_token": "refresh-banco", "expires_in": 21600,
        })
        resposta = Mock(ok=True, status_code=200, headers={"Content-Type": "application/json"})
        resposta.json.return_value = {"results": [{"id": "MLB-teste"}]}
        with patch("services.mercadolivre_scapring_service.consultar_api_service.requests.get", return_value=resposta) as get:
            retorno = MercadoLivreScapringService().executar(["  Ryzen 5 5600  "])
        self.assertEqual(retorno, resposta.json.return_value["results"])
        self.assertEqual(get.call_args.args[0], "https://api.mercadolibre.com/products/search")
        self.assertEqual(get.call_args.kwargs["params"]["q"], "Ryzen 5 5600")
        self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], "Bearer access-banco")

    def test_busca_vazia_nao_faz_requisicao(self):
        with patch("services.mercadolivre_scapring_service.consultar_api_service.requests.get") as get:
            with self.assertRaisesRegex(ValueError, "Informe os termos"):
                MercadoLivreScapringService().executar([])
            get.assert_not_called()

    def test_busca_por_id_sem_termos(self):
        service = MercadoLivreScapringService()
        resposta = Mock(ok=True)
        resposta.json.return_value = {"id": "MLB48991060", "name": "Produto"}
        for termos in (None, []):
            with patch.object(ConsultarApiMercadoLivreService, "_requisitar_com_tentativas", return_value=resposta) as requisitar:
                retorno = service.executar(termos, produto_id="MLB48991060")
                self.assertEqual(retorno, [resposta.json.return_value])
                requisitar.assert_called_once_with("https://api.mercadolibre.com/products/MLB48991060", None)

    def test_lista_ignora_busca_sem_resultados_e_atualiza_cabecalho(self):
        from types import SimpleNamespace

        respostas = []
        for produtos in ([], [{"id": "primeiro"}, {"id": "segundo"}]):
            resposta = Mock(ok=True, status_code=200, headers={})
            resposta.json.return_value = {"results": produtos}
            respostas.append(resposta)

        service = MercadoLivreScapringService()
        with patch.object(ConsultarApiMercadoLivreService, "_obter_token_atual", side_effect=[
            SimpleNamespace(access_token="antigo"), SimpleNamespace(access_token="renovado"),
        ]), patch("services.mercadolivre_scapring_service.consultar_api_service.requests.get", side_effect=respostas) as get:
            retorno = service.executar(["inexistente", "Ryzen 7 5700G"])

        self.assertEqual(retorno, [{"id": "primeiro"}])
        self.assertEqual([c.kwargs["params"]["q"] for c in get.call_args_list], ["inexistente", "Ryzen 7 5700G"])
        self.assertEqual(get.call_args_list[0].kwargs["headers"]["Authorization"], "Bearer antigo")
        self.assertEqual(get.call_args_list[1].kwargs["headers"]["Authorization"], "Bearer renovado")


if __name__ == "__main__":
    unittest.main()
