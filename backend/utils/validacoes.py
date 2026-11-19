import math



def numero_nao_negativo(valor):
  """Converte para float; devolve None se vazio, booleano, infinito, negativo ou não numérico."""
  if valor is None or isinstance(valor, bool) or valor == "":
    return None
  try:
    valor = float(valor)
    return valor if math.isfinite(valor) and valor >= 0 else None
  except (ValueError, TypeError):
    return None


def validacao_campos(dados: dict, campos_obrigatorios: list[str]):
  if not isinstance(dados, dict):
    raise ValueError("Envie um objeto JSON válido")
  campos_obrigatorios_resp = []

  for campo in campos_obrigatorios:
    if not dados.get(campo):
      campos_obrigatorios_resp.append(campo)

  if campos_obrigatorios_resp:
    raise ValueError(f"Campo(s) obrigatório(s) faltando: {', '.join(campos_obrigatorios_resp)}")


def validar_senha_forte(senha: str) -> None:
  if len(senha) < 8:
    raise ValueError("A senha deve ter no minimo oito caracteres")

  if not any(c.isupper() for c in senha):
    raise ValueError("A senha deve ter no minimo uma letra maiuscula")

  if not any(c.islower() for c in senha):
    raise ValueError("A senha deve ter no minimo uma letra minuscula")

  if not any(c.isdigit() for c in senha):
    raise ValueError("A senha deve conter ao menos um numero")

  if not any(not c.isalnum() for c in senha):
    raise ValueError("A senha deve conter ao menos um caractere especial")
