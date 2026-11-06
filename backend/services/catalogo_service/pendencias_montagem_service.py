from math import isfinite


def pendencias_para_montagem(peca):
  from services.catalogo_service.conferir_especificacoes_service import converter
  from services.catalogo_service.requisitos_montagem import MINIMOS, CONSUMO_CONFIRMADO
  campos = MINIMOS.get(peca.__tablename__, ())
  aliases = {'tipo_fone':'tipo','categoria_cabo':'categoria','formato_ram':'formato'}
  faltantes = [campo for campo in campos if converter(campo,getattr(peca,aliases.get(campo,campo),None)) is None]
  if peca.__tablename__ in CONSUMO_CONFIRMADO:
    consumo=peca.consumo_energia
    try: valido=not isinstance(consumo,bool) and consumo is not None and isfinite(float(consumo)) and float(consumo)>0
    except (TypeError,ValueError,OverflowError): valido=False
    if not valido:faltantes.append('consumo_energia')
  return sorted(set(faltantes))

