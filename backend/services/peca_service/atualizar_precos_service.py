import time
from datetime import datetime, timedelta, timezone

import requests

from models import ConsultaPreco, ControleColeta
from .modelos_pecas import MODELOS_PECAS
from services.preco_service.buscar_preco_kabum_service import BuscarPrecoKabumService
from services.preco_service.reservar_consulta_service import ReservarConsultaService
from services.preco_service.validar_link_service import ValidarLinkService


class AtualizarPrecosService:
    def executar(self, limite: int | None = None, intervalo: float = 1.0):
        if limite is not None and limite < 1:
            raise ValueError("O limite deve ser positivo")

        if intervalo < 0:
            raise ValueError("O intervalo não pode ser negativo")

        ControleColeta.inicializar()

        resumo = {"consultas": 0, "atualizadas": 0, "falhas": 0, "ignoradas": 0}

        for classe, peca in self._selecionar_pecas():
            if limite is not None and resumo["consultas"] >= limite:
                break
            if not self._link_valido(peca.kabum_external):
                resumo["ignoradas"] += 1
                continue

            if resumo["consultas"] and intervalo:
                time.sleep(intervalo)

            agora = datetime.now(timezone(timedelta(hours=-3)))
            consulta = ReservarConsultaService().executar(classe, peca, agora)

            if consulta is None:
                continue

            resumo["consultas"] += 1

            if not self._consultar(consulta, resumo):
                break

        return resumo

    def _selecionar_pecas(self):
        ultimas = ConsultaPreco.ultimas_por_url()
        hoje = datetime.now(timezone(timedelta(hours=-3))).date().isoformat()
        consultadas_hoje = ConsultaPreco.consultadas_no_dia(hoje)
        candidatas = [
            (classe, peca) for classe in MODELOS_PECAS
            for peca in classe.com_link_kabum()
            if (classe.__tablename__, peca.id, peca.kabum_external) not in consultadas_hoje
        ]
        essenciais = ("processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd", "hd")
        return sorted(candidatas, key=lambda par: (
            ultimas.get(par[1].kabum_external, 0),
            par[0].__tablename__ not in essenciais, par[1].id,
            essenciais.index(par[0].__tablename__) if par[0].__tablename__ in essenciais else par[0].__tablename__,
        ))

    def _consultar(self, consulta, resumo):
        classe = next(c for c in MODELOS_PECAS if c.__tablename__ == consulta.tabela_peca)
        peca = classe.buscar_por_id(consulta.peca_id)
        if peca is None or peca.kabum_external != consulta.url:
            consulta.ignorar()
            resumo["ignoradas"] += 1
            return True
        continuar = True
        try:
            resultado = BuscarPrecoKabumService().executar(consulta.url)
            peca.recarregar()
            if peca.kabum_external != consulta.url:
                consulta.status = "ignorada"
                resumo["ignoradas"] += 1
            else:
                peca.aplicar_cotacao(resultado, datetime.now(timezone.utc).replace(tzinfo=None))
                consulta.status = "concluida"
                consulta.erro = None
                resumo["atualizadas"] += 1
        except requests.HTTPError as erro:
            status = erro.response.status_code if erro.response is not None else 0
            consulta.status = "falha"
            consulta.erro = f"KaBuM HTTP {status}"
            resumo["falhas"] += 1
            continuar = status not in {401, 403, 429} and status < 500
        except requests.RequestException:
            consulta.status = "falha"
            consulta.erro = "Falha de rede na coleta"
            resumo["falhas"] += 1
            continuar = False
        except ValueError as erro:
            consulta.status = "falha"
            consulta.erro = str(erro)[:300]
            resumo["falhas"] += 1
        consulta.confirmar()
        return continuar

    @staticmethod
    def _link_valido(url):
        try:
            ValidarLinkService().executar(url)
            return True
        except ValueError:
            return False
