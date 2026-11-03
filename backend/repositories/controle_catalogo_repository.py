"""Trava por banco. MySQL advisory lock; SQLite flock liberado com o processo."""
import hashlib
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import text
from models import db


class RepositorioControleCatalogo:
    def __init__(self):
        self.conexao=None;self.arquivo=None;self.nome=None

    @contextmanager
    def bloquear(self):
        dialecto=db.engine.dialect.name
        if dialecto=='mysql':
            self.nome='boostio:catalogo:'+hashlib.sha256(str(db.engine.url.database).encode()).hexdigest()[:16]
            with db.engine.connect() as conexao:
                self.conexao=conexao
                resultado=conexao.execute(text('SELECT GET_LOCK(:nome,0)'),{'nome':self.nome}).scalar()
                if resultado is None:raise RuntimeError('Não foi possível adquirir a trava do catálogo')
                adquirido=resultado==1
                try:yield adquirido
                finally:
                    if adquirido:
                        try:conexao.execute(text('SELECT RELEASE_LOCK(:nome)'),{'nome':self.nome})
                        finally:self.conexao=None
                    self.conexao=None
        elif dialecto=='sqlite':
            import fcntl
            caminho=db.engine.url.database
            if not caminho or caminho==':memory:':raise ValueError('Worker SQLite requer arquivo persistente')
            arquivo=Path(caminho).resolve().with_suffix('.catalogo.lock')
            with arquivo.open('a') as trava:
                try:fcntl.flock(trava,fcntl.LOCK_EX|fcntl.LOCK_NB);adquirido=True
                except BlockingIOError:adquirido=False
                self.arquivo=trava if adquirido else None
                try:yield adquirido
                finally:
                    if adquirido:fcntl.flock(trava,fcntl.LOCK_UN)
                    self.arquivo=None
        else:raise ValueError('Banco não suportado para worker')

    def verificar(self):
        if self.conexao is not None:
            valido=self.conexao.execute(text('SELECT IS_USED_LOCK(:nome)=CONNECTION_ID()'),{'nome':self.nome}).scalar()
            if valido!=1:raise RuntimeError('Trava de catálogo perdida; operação interrompida')
        elif self.arquivo is None or self.arquivo.closed:
            raise RuntimeError('Worker sem trava; operação recusada')


    def verificar_esquema(self, trabalhos):
        from sqlalchemy import inspect
        from models import EstadoCatalogo, ProdutoPendente, Oferta, HistoricoOferta, VinculoMercadoLivre, IdentidadeFabricante, ControleColeta
        from services.peca_service.modelos_pecas import MODELOS_PECAS
        modelos=[EstadoCatalogo,ProdutoPendente,Oferta,HistoricoOferta,VinculoMercadoLivre,IdentidadeFabricante,ControleColeta]
        modelos += [m for m in MODELOS_PECAS if m.__tablename__ in {t['categoria'] for t in trabalhos}]
        insp=inspect(db.engine)
        for m in modelos:
            if not insp.has_table(m.__tablename__) or {c['name'] for c in insp.get_columns(m.__tablename__)}!={c.name for c in m.__table__.columns}:
                raise ValueError('Esquema incompleto; execute as preparações do catálogo, identidades e ofertas')
