import pytest
from models import Usuario
from werkzeug.security import generate_password_hash

#fixture coloca o retorno na função que a chama(so passar o nome da func no parametro)
@pytest.fixture
def mock_usuario_salvar(mocker):
    #mocker.patch é onde aponto para função do db que vou querer simular(não mexe no db de verdade)
    #qualquer codigo de chamar Usuario.salvar, vai estar mockado durante o funcionamento da func
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
    # deixa atualizar_dados rodar de verdade, só mocka o commit interno dele
    mocker.patch("models.usuario.db.session.commit")

# tests/conftest.py (adicionar essas, junto com as que você já tem)

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