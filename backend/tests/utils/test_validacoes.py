#PYTESTE encontra os arquivos que começam com _test ou termina com _test e mesma coisa nas funções
# tests/utils/test_validacoes.py
import pytest
from utils.validacoes import validacao_campos

def test_nao_lanca_erro_quando_todos_campos_estao_preenchidos():
  #Parametros são declarados dentro da func de testes
  dados = {
    "nome": "test",
    "email": "test@gmail.com",
    "senha": "Test.000"
  }
  campos_obrigatorios = ["nome","email","senha"]

  #Chamada func
  #Se nao lancar erro o teste passa automaticamente
  validacao_campos(dados,campos_obrigatorios)

def test_lanca_erro_faltando_um_campo_preenchido():
  #Parametros são declarados dentro da func de testes
  dados = {
    "nome": "test",
    "email": "test@gmail.com",
  } #Faltando senha
  campos_obrigatorios = ["nome","email","senha"]

  #Chamada func
  #Act & Assert
  #Se lancar erro o teste passa automaticamente
  with pytest.raises(ValueError):
    validacao_campos(dados,campos_obrigatorios)

def test_lanca_erro_faltando_dois_campos_preenchidos():
  #Parametros são declarados dentro da func de testes
  dados = {
    "nome": "test",
    "email": "test@gmail.com",
  }
  campos_obrigatorios = ["nome","email","senha"]

  #Chamada func
  #Espera o erro com with, se lançar o erro passa no teste
  with pytest.raises(ValueError):
    validacao_campos(dados,campos_obrigatorios)

def test_mensagem_de_erro_lista_o_campo_faltando():
    # Arrange
    dados = {"nome": "Gustavo"}
    campos = ["nome", "email"]

    # Act & Assert
    #match verifica se o texto de erro contem nesse caso 'email'
    with pytest.raises(ValueError, match="email"):
      validacao_campos(dados, campos)

def test_lanca_erro_quando_campo_esta_vazio():
    # Arrange
    dados = {"nome": "", "email": "gustavo@teste.com"}
    campos = ["nome", "email"]

    # Act & Assert
    with pytest.raises(ValueError):
        validacao_campos(dados, campos)