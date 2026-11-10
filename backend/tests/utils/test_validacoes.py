import pytest
from utils.validacoes import validacao_campos

def test_nao_lanca_erro_quando_todos_campos_estao_preenchidos():
  dados = {
    "nome": "test",
    "email": "test@gmail.com",
    "senha": "Test.000"
  }
  campos_obrigatorios = ["nome","email","senha"]

  validacao_campos(dados,campos_obrigatorios)

def test_lanca_erro_faltando_um_campo_preenchido():
  dados = {
    "nome": "test",
    "email": "test@gmail.com",
  }
  campos_obrigatorios = ["nome","email","senha"]

  with pytest.raises(ValueError):
    validacao_campos(dados,campos_obrigatorios)

def test_lanca_erro_faltando_dois_campos_preenchidos():
  dados = {
    "nome": "test",
    "email": "test@gmail.com",
  }
  campos_obrigatorios = ["nome","email","senha"]

  with pytest.raises(ValueError):
    validacao_campos(dados,campos_obrigatorios)

def test_mensagem_de_erro_lista_o_campo_faltando():
    dados = {"nome": "Gustavo"}
    campos = ["nome", "email"]

    with pytest.raises(ValueError, match="email"):
      validacao_campos(dados, campos)

def test_lanca_erro_quando_campo_esta_vazio():
    dados = {"nome": "", "email": "gustavo@teste.com"}
    campos = ["nome", "email"]

    with pytest.raises(ValueError):
        validacao_campos(dados, campos)