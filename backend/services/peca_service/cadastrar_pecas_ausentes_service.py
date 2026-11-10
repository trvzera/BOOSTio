from models import db
from repositories.ofertas_kabum_repository import gravar_cotacao_inicial
from utils.codigos_peca import separar_codigos


class CadastrarPecasAusentesService:
    def executar(self, classe, itens):
      novos = []
      try:
        for original in itens:
          original = dict(original)
          oferta = {campo: original.pop(campo, None) for campo in classe.CAMPOS_DA_OFERTA}
          item = separar_codigos(original)
          referencia, numero = item.get('referencia_interna'), item.get('part_number')
          if referencia:
            existente = classe.buscar_por_codigo(referencia)
          elif numero:
            existente = classe.buscar_por_part_number(numero, item['fabricante'])
          else:
            raise ValueError('Cadastro sem identificador estável')
          if existente is None:
            existente = classe(status_validacao='legado', **{k:v for k,v in item.items() if k != 'status_validacao'})
            db.session.add(existente)
            db.session.flush()
            if oferta['kabum_external']:
                    gravar_cotacao_inicial(existente, oferta['kabum_external'], oferta['preco'],
                                     oferta['esgotado'], oferta['preco_atualizado_em'])
            novos.append(existente)
        db.session.commit()
      except Exception:
        db.session.rollback()
        raise
      return len(novos)
