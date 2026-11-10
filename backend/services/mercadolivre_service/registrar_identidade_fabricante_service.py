"""Registra o MPN revisado de uma peça sem substituir a referência interna."""
from models import db, IdentidadeFabricante
from repositories.identificadores_peca_repository import _vinculos, reassinar_vinculos
from services.catalogo_service.normalizar_produto import codigo
from utils.codigos_peca import codigo_interno
from utils.identidade_peca import assinatura_peca


class RegistrarIdentidadeFabricanteService:
    def executar(self, peca, mpn, fonte, especificacoes, *, simular=True, gtin=None):
        try:
            if not isinstance(mpn, str) or not mpn.strip() or len(mpn) > 100 or codigo_interno(mpn):
                raise ValueError('Informe um código real do fabricante')
            # Releitura bloqueada protege contra mudança da peça durante a importação.
            db.session.refresh(peca, with_for_update=True)
            if not IdentidadeFabricante.conferem(peca, especificacoes):
                raise ValueError('Especificações locais divergem da fonte revisada')
            if peca.part_number and not codigo_interno(peca.part_number) and codigo(peca.part_number) != codigo(mpn):
                raise ValueError('Part number existente diverge da fonte revisada')
            antiga, numero = assinatura_peca(peca), peca.part_number
            vinculos = [v for v in _vinculos(peca) if v[0].name == 'vinculo_mercado_livre']
            if codigo_interno(numero):
                peca.referencia_interna = peca.referencia_interna or numero
            peca.part_number = mpn.strip()
            reassinar_vinculos(peca, vinculos, antiga, numero)
            atual = IdentidadeFabricante.query.filter_by(tabela_peca=peca.__tablename__, peca_id=peca.id).with_for_update().first()
            dados = dict(assinatura_peca=assinatura_peca(peca), mpn=mpn, fonte=fonte, especificacoes=especificacoes, gtin=gtin)
            if atual:
                if any(getattr(atual, k) != v for k, v in dados.items()):
                    raise ValueError('Identidade existente diverge; exige revisão manual')
                return 'inalterada'
            if not simular:
                db.session.add(IdentidadeFabricante(tabela_peca=peca.__tablename__, peca_id=peca.id, **dados))
                db.session.commit()
            return 'proposta' if simular else 'cadastrada'
        except Exception:
            db.session.rollback()
            raise
        finally:
            # Encerra também transações de leitura e simulações.
            db.session.rollback()

