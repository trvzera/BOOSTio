import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from smtplib import SMTPAuthenticationError, SMTPRecipientsRefused, SMTPException
from urllib.parse import parse_qs, urlsplit

from flask import Flask

from controllers.email_controller import email_bp
from models import Codigo, Usuario, db, lm, mail
from utils.csrf import configurar_csrf


class TestCodigosEmail(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        app = Flask(__name__)
        app.config.update(
            TESTING=True,
            SECRET_KEY="segredo-apenas-para-testes",
            FRONTEND_URL="https://boostio.example",
            SQLALCHEMY_DATABASE_URI=f"sqlite:///{Path(self.temporario.name) / 'teste.db'}",
        )
        db.init_app(app)
        lm.init_app(app)
        mail.init_app(app)
        configurar_csrf(app)
        app.register_blueprint(email_bp)
        self.contexto = app.app_context()
        self.contexto.push()
        db.create_all()

        usuario = Usuario(nome="Teste", email="teste@example.test", verificado=False)
        usuario.salvar()
        self.usuario_id = usuario.id
        self.cliente = app.test_client()
        with self.cliente.session_transaction() as sessao:
            sessao["_user_id"] = usuario.get_id()
            sessao["_fresh"] = True
        with self.cliente.session_transaction() as sessao:
            sessao["csrf_token"] = "token-para-testes"
        self.cabecalhos = {"X-CSRF-Token": "token-para-testes"}
        self.mail_mock = patch("services.email_service.enviar_codigo_email_service.mail.send")
        self.enviados = self.mail_mock.start()

    def tearDown(self):
        self.mail_mock.stop()
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.contexto.pop()
        self.temporario.cleanup()

    def enviar(self):
        return self.cliente.post(f"/email/verificar/enviar/{self.usuario_id}", headers=self.cabecalhos)

    def conferir(self, codigo):
        return self.cliente.post(
            f"/email/verificar/conferir/{self.usuario_id}",
            json={"codigo": codigo},
            headers=self.cabecalhos,
        )

    def test_codigo_seis_digitos_e_uso_unico(self):
        self.assertEqual(self.enviar().status_code, 200)
        codigo = Codigo.buscar_codigo_recente(self.usuario_id).codigo
        self.assertRegex(codigo, r"^[0-9]{6}$")
        self.assertEqual(self.conferir(codigo).status_code, 200)
        self.assertEqual(self.conferir(codigo).status_code, 400)
        self.assertEqual(self.cliente.post(
            "/email/verificar/link", json={"token": self.token_do_email()}, headers=self.cabecalhos,
        ).status_code, 400)

    def token_do_email(self):
        mensagem = self.enviados.call_args.args[0]
        endereco = next(linha for linha in mensagem.body.splitlines() if linha.startswith("https://"))
        url = urlsplit(endereco)
        self.assertEqual(url.netloc, "boostio.example")
        self.assertEqual(url.path, "/pages/verificar-email.html")
        self.assertFalse(url.query)
        return parse_qs(url.fragment)["token"][0]

    def test_link_confirma_sem_login_apenas_via_post_e_consume_codigo(self):
        self.assertEqual(self.enviar().status_code, 200)
        navegador = self.cliente.application.test_client()
        token = self.token_do_email()
        rota = "/email/verificar/link"
        self.assertEqual(navegador.get(rota).status_code, 405)
        self.assertEqual(navegador.post(rota, json={"token": token}).status_code, 403)
        self.assertFalse(Usuario.buscar_por_id(self.usuario_id).verificado)
        with navegador.session_transaction() as sessao:
            sessao["csrf_token"] = self.cabecalhos["X-CSRF-Token"]
        self.assertEqual(navegador.post(rota, json={"token": token + "x"}, headers=self.cabecalhos).status_code, 400)
        self.assertEqual(navegador.post(rota, json={"token": token}, headers=self.cabecalhos).status_code, 200)
        self.assertTrue(Usuario.buscar_por_id(self.usuario_id).verificado)
        with navegador.session_transaction() as sessao:
            self.assertNotIn("_user_id", sessao)
        self.assertEqual(navegador.post(rota, json={"token": token}, headers=self.cabecalhos).status_code, 400)
        self.assertEqual(self.conferir(Codigo.buscar_codigo_recente(self.usuario_id).codigo).status_code, 400)

    def test_link_anterior_e_expirado_nao_confirmam(self):
        self.assertEqual(self.enviar().status_code, 200)
        antigo = self.token_do_email()
        registro = Codigo.buscar_codigo_recente(self.usuario_id)
        registro.criado_em -= timedelta(seconds=31)
        db.session.commit()
        self.assertEqual(self.enviar().status_code, 200)
        rota = "/email/verificar/link"
        self.assertEqual(self.cliente.post(rota, json={"token": antigo}, headers=self.cabecalhos).status_code, 400)
        registro = Codigo.buscar_codigo_recente(self.usuario_id)
        registro.data_expiracao = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.session.commit()
        self.assertEqual(self.cliente.post(rota, json={"token": self.token_do_email()}, headers=self.cabecalhos).status_code, 400)
        self.assertFalse(Usuario.buscar_por_id(self.usuario_id).verificado)

    def test_erro_smtp_nao_expoe_detalhes_do_provedor(self):
        for erro, status in ((SMTPAuthenticationError(535,b"detalhe-interno"),503),
                             (SMTPRecipientsRefused({"privado@test.invalid":"detalhe-interno"}),400),
                             (SMTPException("detalhe-interno"),503), (OSError("detalhe-interno"),503)):
            with self.subTest(erro=type(erro).__name__),patch("controllers.email_controller.EnviarEmailService.executar_para_usuario",side_effect=erro):
                resposta=self.enviar()
                self.assertEqual(resposta.status_code,status)
                self.assertIn("erro",resposta.json)
                self.assertNotIn("detalhe-interno",str(resposta.json))

    def test_email_usa_codigo_emitido_e_cabecalhos_transacionais(self):
        self.assertEqual(self.enviar().status_code, 200)
        mensagem = self.enviados.call_args.args[0]
        codigo = Codigo.buscar_codigo_recente(self.usuario_id).codigo
        self.assertEqual(mensagem.recipients, ["teste@example.test"])
        self.assertIn(codigo, mensagem.body)
        self.assertIn(codigo, mensagem.html)
        self.assertIn("Teste", mensagem.html)
        self.assertEqual(mensagem.extra_headers, {"Auto-Submitted": "auto-generated", "X-Auto-Response-Suppress": "All"})

    def test_cinco_tentativas_por_codigo(self):
        self.assertEqual(self.enviar().status_code, 200)
        codigo = Codigo.buscar_codigo_recente(self.usuario_id).codigo
        errado = "000000" if codigo != "000000" else "999999"
        for _ in range(5):
            self.assertEqual(self.conferir(errado).status_code, 400)
        self.assertEqual(self.conferir(codigo).status_code, 400)
        self.assertFalse(Usuario.buscar_por_id(self.usuario_id).verificado)

    def test_reenvio_tem_intervalo_e_limite_horario(self):
        agora = datetime.now(timezone.utc)
        for indice in range(5):
            self.assertEqual(self.enviar().status_code, 200)
            if indice == 0:
                self.assertEqual(self.enviar().status_code, 400)
            ultimo = Codigo.query.order_by(Codigo.id.desc()).first()
            ultimo.criado_em = agora - timedelta(minutes=50 - indice * 10)
            db.session.commit()
        self.assertEqual(self.enviar().status_code, 400)
        self.assertEqual(Codigo.query.count(), 5)

    def test_rotas_publicas_antigas_foram_removidas(self):
        self.assertEqual(self.cliente.post("/email/recuperar/enviar", headers=self.cabecalhos).status_code, 404)
        self.assertEqual(self.cliente.post("/email/recuperar/conferir", headers=self.cabecalhos).status_code, 404)


if __name__ == "__main__":
    unittest.main()
