from types import SimpleNamespace

import pytest

from services.usuario_service.solicitar_recuperacao_senha_service import SolicitarRecuperacaoSenhaService


@pytest.mark.parametrize("dados", [None,[],{}, {"email":1},{"email":"x"*151}])
def test_entrada_invalida_nao_consulta_conta_nem_envia_email(mocker,dados):
    buscar=mocker.patch("models.usuario.Usuario.buscar_por_email")
    enviar=mocker.patch("services.email_service.enviar_email_recuperar_service.EnviarEmailRecuperarService.executar")
    assert SolicitarRecuperacaoSenhaService().executar(dados) is None
    buscar.assert_not_called();enviar.assert_not_called()


@pytest.mark.parametrize("usuario", [None,SimpleNamespace(ativo=False)])
def test_conta_inexistente_ou_inativa_nao_dispara_envio(mocker,usuario):
    mocker.patch("models.usuario.Usuario.buscar_por_email",return_value=usuario)
    enviar=mocker.patch("services.email_service.enviar_email_recuperar_service.EnviarEmailRecuperarService.executar")
    assert SolicitarRecuperacaoSenhaService().executar({"email":"teste@example.test"}) is None
    enviar.assert_not_called()


def test_normaliza_email_e_delega_emissao_ao_service_sem_retornar_dados_da_conta(mocker):
    usuario=SimpleNamespace(ativo=True)
    buscar=mocker.patch("models.usuario.Usuario.buscar_por_email",return_value=usuario)
    enviar=mocker.patch("services.email_service.enviar_email_recuperar_service.EnviarEmailRecuperarService.executar")
    assert SolicitarRecuperacaoSenhaService().executar({"email":" Teste@Example.test "}) is None
    buscar.assert_called_once_with("teste@example.test");enviar.assert_called_once_with(usuario)
