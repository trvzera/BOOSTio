"""Operações curtas e atômicas; nenhuma transação permanece aberta durante HTTP."""
from datetime import timedelta
from uuid import uuid4
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models import db
from models.tarefa_marketplace import TarefaMarketplace as Tarefa, LimiteMarketplace as Limite


class RepositorioFilaMarketplace:
    def preparado(self):
        with Session(db.engine) as s:
            return s.execute(select(Limite.id).limit(1)).first() is not None

    def _limite(self, sessao, loja, agora):
        limite = sessao.execute(select(Limite).filter_by(loja=loja)).scalar_one_or_none()
        if limite is None:
            raise ValueError('Inicialize a fila com marketplaces-fila-preparar')
        return limite

    def inicializar(self):
        for loja in ('mercado_livre', 'shopee'):
            try:
                with Session(db.engine) as s, s.begin():
                    if s.execute(select(Limite.id).filter_by(loja=loja)).first() is None:
                        s.add(Limite(loja=loja))
            except IntegrityError:
                pass  # Outro preparador inseriu a mesma identidade única.

    def enfileirar(self, loja, chave, tipo, dados):
        try:
            with Session(db.engine) as s, s.begin():
                tarefa = Tarefa(loja=loja, chave=chave, tipo=tipo, dados=dados)
                s.add(tarefa)
                s.flush()
                return tarefa.id
        except IntegrityError:
            with Session(db.engine) as s:
                return s.execute(select(Tarefa.id).filter_by(loja=loja, chave=chave)).scalar_one()

    def reservar(self, loja, agora):
        with Session(db.engine) as s, s.begin():
            limite = self._limite(s, loja, agora)
            if limite.bloqueado or limite.pausado_ate > agora:
                return None
            # Chamador mantém uma trava exclusiva por marketplace. Executando é
            # recuperável assim que o processo anterior libera a trava ou encerra.
            tarefa = s.execute(select(Tarefa).where(Tarefa.loja == loja,
                ((Tarefa.status == 'pendente') & (Tarefa.disponivel_em <= agora)) |
                (Tarefa.status == 'executando')).order_by(Tarefa.id).limit(1)).scalar_one_or_none()
            if tarefa is None:
                return None
            tarefa.status, tarefa.reserva = 'executando', uuid4().hex
            tarefa.tentativas += 1
            s.flush()
            return dict(id=tarefa.id, tipo=tarefa.tipo, dados=tarefa.dados,
                        reserva=tarefa.reserva, tentativas=tarefa.tentativas)

    def finalizar(self, tarefa, status, *, resultado=None, erro=None, disponivel_em=None):
        with Session(db.engine) as s, s.begin():
            valores = dict(status=status, resultado=resultado, erro=erro, reserva=None)
            if disponivel_em is not None:
                valores['disponivel_em'] = disponivel_em
            alteradas = s.execute(update(Tarefa).where(Tarefa.id == tarefa['id'],
                Tarefa.reserva == tarefa['reserva'], Tarefa.status == 'executando').values(**valores)).rowcount
            if alteradas != 1:
                raise RuntimeError('Reserva da tarefa foi perdida')

    def intervalo(self, loja, agora, segundos):
        with Session(db.engine) as s, s.begin():
            limite = self._limite(s, loja, agora)
            if limite.bloqueado:
                return None
            espera = max(limite.proxima_requisicao, limite.pausado_ate)
            if espera > agora:
                return max(0, (espera - agora).total_seconds())
            alteradas = s.execute(update(Limite).where(Limite.id == limite.id,
                Limite.proxima_requisicao <= agora, Limite.pausado_ate <= agora,
                Limite.bloqueado.is_(False)).values(proxima_requisicao=agora + timedelta(seconds=segundos))).rowcount
            return 0 if alteradas == 1 else segundos

    def suspender(self, loja, agora, *, espera=0, bloquear=False, rate_limit=False):
        with Session(db.engine) as s, s.begin():
            limite = self._limite(s, loja, agora)
            # UPDATE condicional impede que concorrentes encurtem uma pausa longa.
            ate = agora + timedelta(seconds=espera)
            s.execute(update(Limite).where(Limite.id == limite.id, Limite.pausado_ate < ate).values(pausado_ate=ate))
            if rate_limit:
                s.execute(update(Limite).where(Limite.id == limite.id).values(limitacoes=Limite.limitacoes + 1))
            if bloquear:
                s.execute(update(Limite).where(Limite.id == limite.id).values(bloqueado=True))

    def reativar(self, loja, agora):
        with Session(db.engine) as s, s.begin():
            s.execute(update(Limite).where(Limite.loja == loja).values(bloqueado=False,
                limitacoes=0, pausado_ate=agora))
            s.execute(update(Tarefa).where(Tarefa.loja == loja,
                Tarefa.status == 'bloqueada').values(status='pendente', disponivel_em=agora))

    def limitacoes(self, loja):
        with Session(db.engine) as s:
            return s.execute(select(Limite.limitacoes).where(Limite.loja == loja)).scalar_one()

    def resumo(self):
        with Session(db.engine) as s:
            return [dict(loja=l, status=e, quantidade=n) for l, e, n in s.execute(
                select(Tarefa.loja, Tarefa.status, func.count()).group_by(Tarefa.loja, Tarefa.status))]
