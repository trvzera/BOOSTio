from datetime import timedelta

from sqlalchemy import update

from models import db, ConsultaPreco, ControleColeta


class ReservarConsultaService:
    LIMITE_DIARIO = 140
    LIMITE_MENSAL = 4500
    INTERVALO_DIAS = 5

    def executar(self, classe, peca, agora):
        # UPDATE bloqueia esta linha até o commit, inclusive no SQLite.
        bloqueio = db.session.execute(update(ControleColeta).where(ControleColeta.id == 1).values(
            versao=ControleColeta.versao + 1,
        ))
        if not bloqueio.rowcount:
            db.session.rollback()
            raise ValueError("Execute a migração de preços antes da atualização")
        dia = agora.date().isoformat()
        mes = dia[:7]
        consultas = ConsultaPreco.query.filter_by(usa_brightdata=True)
        if (consultas.filter_by(dia=dia).count() >= self.LIMITE_DIARIO
                or consultas.filter_by(mes=mes).count() >= self.LIMITE_MENSAL):
            db.session.rollback()
            return None
        recente = ConsultaPreco.query.filter(
            ConsultaPreco.url == peca.meli_external,
            ConsultaPreco.dia > (agora.date() - timedelta(days=self.INTERVALO_DIAS)).isoformat(),
        ).first()
        if recente:
            db.session.rollback()
            return None
        consulta = ConsultaPreco(
            loja="meli", tabela_peca=classe.__tablename__, peca_id=peca.id,
            url=peca.meli_external, dia=dia, mes=mes, usa_brightdata=True, status="reservada",
        )
        db.session.add(consulta)
        db.session.commit()
        return consulta
