#PYTESTE encontra os arquivos que começam com _test ou termina com _test e mesma coisa nas funções
import pytest
from services.usuario_service.criar_usuario_service import CriarUsuarioService

#mocker é uma forma de simular nesse caso um banco de dados fake, apenas para teste

def test_criar_usuario_com_dados_validos(mocker,mock_usuario_salvar,mock_usuario_sem_email_existente):
  dados = {
    "nome": "test",
    "email": "test@gmail.com",
    "senha": "Test.000"
  }
  service = CriarUsuarioService()
  usuario = service.executar(dados)

  assert usuario.nome == dados["nome"]
  assert usuario.email == dados["email"]

def test_criar_usuario_com_email_invalido(mocker,mock_usuario_salvar,mock_usuario_sem_email_existente):
  dados = {
    "nome": "test",
    "email": "test@.com",
    "senha": "Test.000"
  }

  service = CriarUsuarioService()

  with pytest.raises(ValueError,match="email"):
    service.executar(dados)

def test_criar_usuario_com_senha_invalida(mocker,mock_usuario_salvar,mock_usuario_sem_email_existente):
  dados = {
    "nome": "test",
    "email": "test@gmail.com",
    "senha": "teste"
  }

  service = CriarUsuarioService()

  with pytest.raises(ValueError,match="senha"):
    service.executar(dados)

def test_criar_usuario_com_senha_invalida(mocker,mock_usuario_salvar,mock_usuario_sem_email_existente):
  dados = {
    "nome": "test",
    "email": "test@gmail.com",
    "senha": "teste"
  }

  service = CriarUsuarioService()

  with pytest.raises(ValueError,match="senha"):
    service.executar(dados)
