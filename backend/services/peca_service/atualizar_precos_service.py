import os
from datetime import datetime, timezone, timedelta

import requests
from sqlalchemy import func

from models import db, ConsultaPreco
from .modelos_pecas import MODELOS_PECAS
from services.preco_service.brightdata_service import ColetaPendenteError
from services.preco_service.buscar_preco_meli_service import BuscarPrecoMeliService
from services.preco_service.reservar_consulta_service import ReservarConsultaService
from services.preco_service.validar_link_service import ValidarLinkService


class AtualizarPrecosService:
    def executar(self, limite: int = 140):
        if not 1 <= limite <= 140:
            raise ValueError("O limite por execução deve estar entre 1 e 140")
        if not os.getenv("BRIGHTDATA_API_KEY", "").strip():
            raise ValueError("Configure BRIGHTDATA_API_KEY no backend/.env")
        resumo = {"consultas": 0, "atualizadas": 0, "pendentes": 0, "falhas": 0, "ignoradas": 0}
        agora = datetime.now(timezone(timedelta(hours=-3)))
        for consulta in ConsultaPreco.query.filter_by(status="pendente").order_by(ConsultaPreco.id).limit(140).all():
            if not self._consultar(consulta, resumo):
                return resumo
        for classe, peca in self._selecionar_pecas():
            if resumo["consultas"] >= limite:
                break
            try:
                ValidarLinkService().executar(peca.meli_external, "meli")
            except ValueError:
                resumo["ignoradas"] += 1
                continue
            consulta = ReservarConsultaService().executar(classe, peca, agora)
            if consulta is None:
                continue
            resumo["consultas"] += 1
            if not self._consultar(consulta, resumo):
                break
        return resumo

    def _selecionar_pecas(self):
        ultimas = dict(db.session.query(ConsultaPreco.url, func.max(ConsultaPreco.id)).group_by(ConsultaPreco.url).all())
        pendentes = {row.url for row in ConsultaPreco.query.filter_by(status="pendente").all()}
        candidatas = [
            (classe, peca) for classe in MODELOS_PECAS
            for peca in classe.query.filter(classe.meli_external.isnot(None), classe.meli_external != "").all()
            if peca.meli_external not in pendentes
        ]
        return sorted(candidatas, key=lambda par: (ultimas.get(par[1].meli_external, 0), par[0].__tablename__, par[1].id))

    def _consultar(self, consulta, resumo):
        classe = next(c for c in MODELOS_PECAS if c.__tablename__ == consulta.tabela_peca)
        peca = db.session.get(classe, consulta.peca_id)
        if peca is None or peca.meli_external != consulta.url:
            consulta.status = "ignorada"
            db.session.commit()
            resumo["ignoradas"] += 1
            return True
        continuar = True
        try:
            resultado = BuscarPrecoMeliService().executar(consulta.url, consulta.snapshot_id)
            db.session.refresh(peca)
            if peca.meli_external != consulta.url:
                consulta.status = "ignorada"
                resumo["ignoradas"] += 1
            else:
                if resultado["preco"] is not None:
                    peca.preco = float(resultado["preco"])
                peca.esgotado = resultado["esgotado"]
                peca.preco_atualizado_em = datetime.now(timezone.utc).replace(tzinfo=None)
                consulta.status = "concluida"
                consulta.erro = None
                resumo["atualizadas"] += 1
        except ColetaPendenteError as erro:
            consulta.snapshot_id = erro.snapshot_id
            consulta.status = "pendente"
            resumo["pendentes"] += 1
        except requests.HTTPError as erro:
            status = erro.response.status_code if erro.response is not None else 0
            consulta.status = "falha"
            consulta.erro = f"Bright Data HTTP {status}"
            resumo["falhas"] += 1
            continuar = status not in {401, 402, 403, 429} and status < 500
        except requests.RequestException:
            consulta.status = "pendente" if consulta.snapshot_id else "incerta"
            consulta.erro = "Falha de rede; nenhuma nova coleta foi iniciada automaticamente"
            resumo["falhas"] += 1
            continuar = False
        except ValueError as erro:
            consulta.status = "falha"
            consulta.erro = str(erro)[:300]
            resumo["falhas"] += 1
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return continuar
