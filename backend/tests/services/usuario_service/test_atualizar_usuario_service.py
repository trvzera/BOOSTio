# tests/services/usuario_service/test_atualizar_usuario_service.py
import pytest
from services.usuario_service.atualizar_usuario_service import AtualizarUsuarioService
from werkzeug.security import check_password_hash


def test_retorna_none_quando_usuario_id_nao_informado():
    service = AtualizarUsuarioService()
    resultado = service.executar(None, {"nome": "Teste"})
    assert resultado is None


def test_retorna_none_quando_usuario_nao_encontrado(mocker):
    mocker.patch("models.usuario.Usuario.buscar_por_id", return_value=None)

    service = AtualizarUsuarioService()
    resultado = service.executar(1, {"nome": "Teste"})

    assert resultado is None


def test_atualiza_nome_com_sucesso(mocker, usuario_fake_com_senha, mock_atualizar_dados_sem_commit):
    mocker.patch("models.usuario.Usuario.buscar_por_id", return_value=usuario_fake_com_senha)

    dados = {"nome": "GustavoAzevedo"}

    service = AtualizarUsuarioService()
    resultado = service.executar(1, dados)

    assert resultado["nome"] == "GustavoAzevedo"


def test_lanca_erro_quando_email_ja_pertence_a_outro_usuario(mocker, usuario_fake_com_senha, mock_atualizar_dados_sem_commit):
    usuario_fake_com_senha.id = 1
    outro_usuario = mocker.Mock(id=2)

    mocker.patch("models.usuario.Usuario.buscar_por_id", return_value=usuario_fake_com_senha)
    mocker.patch("models.usuario.Usuario.buscar_por_email", return_value=outro_usuario)

    dados = {"email": "jaexiste@teste.com"}

    service = AtualizarUsuarioService()

    with pytest.raises(ValueError, match="Já existe um usuario"):
        service.executar(1, dados)


def test_lanca_erro_quando_senha_atual_informada_esta_errada(mocker, usuario_fake_com_senha):
    mocker.patch("models.usuario.Usuario.buscar_por_id", return_value=usuario_fake_com_senha)

    dados = {
        "senha": "NovaSenha.123",
        "senha_atual": "SenhaErrada"
    }

    service = AtualizarUsuarioService()

    with pytest.raises(ValueError, match="Digite a senha atual correta"):
        service.executar(1, dados)


def test_lanca_erro_quando_nova_senha_e_fraca(mocker, usuario_fake_com_senha):
    mocker.patch("models.usuario.Usuario.buscar_por_id", return_value=usuario_fake_com_senha)

    dados = {
        "senha": "fraca",
        "senha_atual": "SenhaAtual.123"
    }

    service = AtualizarUsuarioService()

    with pytest.raises(ValueError, match="no minimo oito caracteres"):
        service.executar(1, dados)


def test_atualiza_senha_com_sucesso(mocker, usuario_fake_com_senha, mock_atualizar_dados_sem_commit):
    mocker.patch("models.usuario.Usuario.buscar_por_id", return_value=usuario_fake_com_senha)

    dados = {
        "senha": "NovaSenha.123",
        "senha_atual": "SenhaAtual.123"
    }

    service = AtualizarUsuarioService()
    service.executar(1, dados)

    assert check_password_hash(usuario_fake_com_senha.senha, "NovaSenha.123") is True