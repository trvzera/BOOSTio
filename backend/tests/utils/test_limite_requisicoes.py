import unittest
from unittest.mock import patch
from uuid import uuid4

from flask import Flask
from flask_login import LoginManager, UserMixin

from controllers.admin_controller import admin_bp
from controllers.auth_controller import auth_bp
from controllers.build_controller import build_bp
from controllers.email_controller import email_bp
from controllers.usuario_controller import usuario_bp
from utils.csrf import configurar_csrf
from utils.limite_requisicoes import configurar_limites


class UsuarioTeste(UserMixin):
    id = 1


class TestLimitesRequisicoes(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="segredo-apenas-para-testes",
            RATELIMIT_STORAGE_URI="memory://",
            RATELIMIT_KEY_PREFIX=f"teste-{uuid4().hex}",
        )
        configurar_csrf(self.app)
        configurar_limites(self.app)
        login = LoginManager(self.app)
        login.user_loader(lambda _id: UsuarioTeste())
        self.app.register_blueprint(auth_bp)
        self.app.register_blueprint(admin_bp)
        self.app.register_blueprint(build_bp)
        self.app.register_blueprint(email_bp)
        self.app.register_blueprint(usuario_bp)
        self.cliente = self.app.test_client()
        self.token = self.cliente.get("/auth/csrf").json["csrf_token"]

    @patch("utils.limite_requisicoes.usuario_atual_e_administrador", return_value=True)
    def test_csrf_limita_por_ip_inclusive_para_administrador(self, _administrador):
        # O setUp já fez a primeira consulta deste IP.
        for _ in range(59):
            resposta = self.cliente.get("/auth/csrf")
            self.assertEqual(resposta.json["csrf_token"], self.token)

        resposta = self.cliente.get("/auth/csrf")
        self.assertEqual(resposta.status_code, 429)
        self.assertEqual(resposta.json["codigo"], "limite-requisicoes")
        self.assertGreater(int(resposta.headers["Retry-After"]), 0)
        self.assertEqual(resposta.headers["Cache-Control"], "no-store")
        outro = self.cliente.get("/auth/csrf", environ_overrides={"REMOTE_ADDR": "192.0.2.1"})
        self.assertEqual(outro.status_code, 200)

    @patch("models.Usuario.buscar_por_sessao", return_value=None)
    def test_limite_segundo_fator_por_conta(self, buscar):
        import time
        with self.cliente.session_transaction() as sessao:
            sessao["desafio_admin"] = {"conta": "1:1", "expira": time.time() + 300}
        for indice in range(6):
            resposta = self.cliente.post(
                "/auth/admin/confirmar", json={"codigo": "000000"},
                headers={"X-CSRF-Token": self.token},
                environ_overrides={"REMOTE_ADDR": f"192.0.2.{indice + 1}"},
            )
            self.assertEqual(resposta.status_code, 401 if indice < 5 else 429)
        self.assertEqual(buscar.call_count, 5)

    def login(self, email, ip="127.0.0.1"):
        return self.cliente.post(
            "/auth/entrar",
            json={"email": email, "senha": "senha-errada"},
            headers={"X-CSRF-Token": self.token},
            environ_overrides={"REMOTE_ADDR": ip},
        )

    @patch("utils.limite_requisicoes.usuario_atual_e_administrador", return_value=True)
    @patch("controllers.auth_controller.EntrarUsuarioService.executar", side_effect=ValueError("Credenciais inválidas"))
    def test_login_administrativo_respeita_limite(self, executar, _administrador):
        for indice in range(20):
            self.assertEqual(self.login(f"admin{indice}@example.test").status_code, 400)
        self.assertEqual(self.login("admin@example.test").status_code, 429)

    @patch.object(UsuarioTeste, "administrador", True, create=True)
    @patch("controllers.admin_controller.RemoverOfertaService.executar", return_value={})
    @patch("controllers.admin_controller.EnviarPendenciasParaIAService.executar", return_value={})
    def test_admin_lotes_e_remocoes_compartilham_limite_por_conta(self, enviar, remover):
        with self.cliente.session_transaction() as sessao:
            sessao["_user_id"] = "1"
        headers = {"X-CSRF-Token": self.token}
        for _ in range(5):
            self.assertEqual(self.cliente.post("/admin/pendencias/enviar-ia", json={"ids": [1]}, headers=headers).status_code, 200)
        for indice in range(25):
            self.assertEqual(self.cliente.post(f"/admin/ofertas/{indice + 1}/remover", headers=headers).status_code, 200)
        resposta = self.cliente.post("/admin/ofertas/55/remover", headers=headers)
        self.assertEqual(resposta.status_code, 429)
        self.assertTrue(resposta.headers.get("Retry-After"))
        self.assertEqual(remover.call_count, 25)
        self.assertEqual(enviar.call_count, 5)

    @patch.object(UsuarioTeste, "administrador", True, create=True)
    @patch("controllers.admin_controller.EnviarPendenciasParaIAService.executar", return_value={})
    def test_sexto_lote_aguarda_mesmo_se_ip_mudar(self, enviar):
        with self.cliente.session_transaction() as sessao:
            sessao["_user_id"] = "1"
        for indice in range(6):
            resposta = self.cliente.post("/admin/pendencias/enviar-ia", json={"ids": [1]},
                                         headers={"X-CSRF-Token": self.token},
                                         environ_overrides={"REMOTE_ADDR": f"192.0.2.{indice + 1}"})
            self.assertEqual(resposta.status_code, 200 if indice < 5 else 429)
        self.assertEqual(enviar.call_count, 5)

    @patch("controllers.auth_controller.EntrarUsuarioService.executar", side_effect=ValueError("Credenciais inválidas"))
    def test_login_limita_ip_mesmo_com_emails_diferentes(self, executar):
        for indice in range(20):
            self.assertEqual(self.login(f"pessoa{indice}@example.test").status_code, 400)
        resposta = self.login("outra@example.test")
        self.assertEqual(resposta.status_code, 429)
        self.assertEqual(resposta.json["codigo"], "limite-requisicoes")
        self.assertTrue(resposta.headers.get("Retry-After"))
        self.assertEqual(executar.call_count, 20)

    @patch("controllers.auth_controller.EntrarUsuarioService.executar", side_effect=ValueError("Credenciais inválidas"))
    def test_login_limita_conta_entre_ips_diferentes(self, executar):
        for indice in range(10):
            self.assertEqual(self.login("Pessoa@Example.Test", f"10.0.0.{indice + 1}").status_code, 400)
        resposta = self.login("pessoa@example.test", "10.0.0.20")
        self.assertEqual(resposta.status_code, 429)
        self.assertEqual(executar.call_count, 10)

    @patch("controllers.build_controller.ListarBuildService.executar", return_value=[])
    @patch("services.build_service.criar_build_service.CriarBuildService.executar", return_value={"id": "teste"})
    def test_geracao_ia_limita_usuario(self, criar, listar):
        with self.cliente.session_transaction() as sessao:
            sessao["_user_id"] = "1"
            sessao["_fresh"] = True
        for indice in range(10):
            resposta = self.cliente.post(
                "/build/", json={}, headers={"X-CSRF-Token": self.token},
                environ_overrides={"REMOTE_ADDR": f"10.2.0.{indice + 1}"},
            )
            self.assertEqual(resposta.status_code, 201)
        resposta = self.cliente.post(
            "/build/", json={}, headers={"X-CSRF-Token": self.token},
            environ_overrides={"REMOTE_ADDR": "10.2.0.20"},
        )
        self.assertEqual(resposta.status_code, 429)
        self.assertEqual(criar.call_count, 10)

    @patch("models.usuario.Usuario.buscar_por_email", return_value=None)
    def test_recuperacao_limita_email_mesmo_entre_ips(self, buscar):
        for indice in range(3):
            resposta = self.cliente.post(
                "/usuarios/esqueci-senha",
                json={"email": "Pessoa@Example.Test"},
                headers={"X-CSRF-Token": self.token},
                environ_overrides={"REMOTE_ADDR": f"10.1.0.{indice + 1}"},
            )
            self.assertEqual(resposta.status_code, 200)
        resposta = self.cliente.post(
            "/usuarios/esqueci-senha",
            json={"email": "pessoa@example.test"},
            headers={"X-CSRF-Token": self.token},
            environ_overrides={"REMOTE_ADDR": "10.1.0.20"},
        )
        self.assertEqual(resposta.status_code, 429)
        self.assertEqual(buscar.call_count, 3)

    @patch("controllers.email_controller.EnviarEmailService.executar", return_value=True)
    @patch("models.usuario.Usuario.buscar_por_id", return_value=UsuarioTeste())
    def test_envio_de_codigo_limita_conta(self, buscar, enviar):
        with self.cliente.session_transaction() as sessao:
            sessao["_user_id"] = "1"
            sessao["_fresh"] = True
        for _ in range(5):
            resposta = self.cliente.post("/email/verificar/enviar/1", headers={"X-CSRF-Token": self.token})
            self.assertEqual(resposta.status_code, 200)
        resposta = self.cliente.post("/email/verificar/enviar/1", headers={"X-CSRF-Token": self.token})
        self.assertEqual(resposta.status_code, 429)
        self.assertEqual(enviar.call_count, 5)

    def test_producao_exige_redis(self):
        app = Flask(__name__)
        app.config["RATELIMIT_STORAGE_URI"] = "memory://"
        with self.assertRaises(RuntimeError):
            configurar_limites(app, producao=True)


if __name__ == "__main__":
    unittest.main()
