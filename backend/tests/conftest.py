import pytest

#fixture coloca o retorno na função que a chama(so passar o nome da func no parametro)
@pytest.fixture
def mock_usuario_salvar(mocker):
    #mocker.patch é onde aponto para função do db que vou querer simular(não mexe no db de verdade)
    #qualquer codigo de chamar Usuario.salvar, vai estar mockado durante o funcionamento da func
    return mocker.patch("models.usuario.Usuario.salvar")


@pytest.fixture
def mock_usuario_sem_email_existente(mocker):
    return mocker.patch("models.usuario.Usuario.buscar_por_email", return_value=None)