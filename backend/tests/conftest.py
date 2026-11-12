import pytest
from compat_oferta import instalar as _instalar_compat_oferta

_instalar_compat_oferta()
from models import Usuario
from werkzeug.security import generate_password_hash

@pytest.fixture
def mock_usuario_salvar(mocker):
    return mocker.patch("models.usuario.Usuario.salvar")


@pytest.fixture
def mock_usuario_sem_email_existente(mocker):
    return mocker.patch("models.usuario.Usuario.buscar_por_email", return_value=None)

@pytest.fixture
def mock_buscar_usuario_por_id(mocker):
    usuario_fake = Usuario(nome = "Original",email = "teste@teste.com",senha = "Teste.000")
    return mocker.patch("models.usuario.Usuario.buscar_por_id",return_value=usuario_fake)

@pytest.fixture
def usuario_fake_com_senha():
    return Usuario(
        nome="Original",
        email="original@teste.com",
        senha=generate_password_hash("SenhaAtual.123")
    )


@pytest.fixture
def mock_atualizar_dados_sem_commit(mocker):
    mocker.patch("models.usuario.db.session.commit")


@pytest.fixture
def mock_usuario_nao_encontrado(mocker):
    return mocker.patch("models.usuario.Usuario.buscar_por_id", return_value=None)


@pytest.fixture
def mock_email_pertence_a_outro_usuario(mocker):
    outro_usuario = mocker.Mock(id=2)
    return mocker.patch("models.usuario.Usuario.buscar_por_email", return_value=outro_usuario)


@pytest.fixture
def mock_buscar_usuario_com_senha(mocker, usuario_fake_com_senha):
    return mocker.patch("models.usuario.Usuario.buscar_por_id", return_value=usuario_fake_com_senha)