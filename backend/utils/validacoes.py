
def validacao_campos(dados: dict, campos_obrigatorios: list[str]):
  campos_obrigatorios_resp = []

  for campo in campos_obrigatorios:
    if not dados.get(campo):
      campos_obrigatorios_resp.append(campo)

  if campos_obrigatorios_resp:
    raise ValueError(f"Campo(s) obrigatório(s) faltando: {', '.join(campos_obrigatorios_resp)}")