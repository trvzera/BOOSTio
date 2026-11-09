"""Aprova peças importadas que passam em regras objetivas; o restante continua em revisão.

Regras (versão `aprovacao_lote_v1`):
- identidade: fabricante e modelo preenchidos, e o modelo tem algum algarismo (nome genérico não identifica);
- ficha: todos os campos mínimos da categoria para montagem estão preenchidos e a ficha não foi reprovada;
- sem duplicata: nenhuma outra peça da categoria tem o mesmo fabricante+modelo ou o mesmo part number;
- opcionalmente, exige part number ou código do fabricante.
"""
import random
import re
from collections import Counter
from datetime import datetime, timezone

from models import db
from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.identidade_peca import normalizar_identidade

VERSAO = "aprovacao_lote_v1"
MOTIVO = f"{VERSAO}: identidade e ficha mínima conferidas por regra"
LOTE_GRAVACAO = 500


class AprovarEmLoteService:
    def executar(self, *, categoria=None, limite=None, semente=None, exigir_identificador=False, simular=True):
        modelos = [m for m in MODELOS_PECAS if categoria is None or m.__tablename__ == categoria]
        if not modelos:
            raise ValueError("Categoria inválida")
        if limite is not None and (type(limite) is not int or limite < 1):
            raise ValueError("Limite inválido")
        sorteio = random.Random(semente)
        resumo = {"simulacao": simular, "regra": VERSAO, "categorias": {}, "total_aprovaveis": 0,
                  "total_aprovadas": 0, "exemplos_recusadas": []}
        for modelo in modelos:
            aprovaveis, recusas = self._avaliar(modelo, exigir_identificador)
            escolhidas = list(aprovaveis)
            if limite is not None and len(escolhidas) > limite:
                escolhidas = sorteio.sample(escolhidas, limite)
            gravadas = 0 if simular else self._aprovar(modelo, [p.id for p in escolhidas])
            resumo["categorias"][modelo.__tablename__] = {
                "em_revisao": len(aprovaveis) + sum(len(v) for v in recusas.values()),
                "aprovaveis": len(aprovaveis), "aprovadas": gravadas if not simular else 0,
                "recusadas": {motivo: len(ids) for motivo, ids in sorted(recusas.items())},
                "sem_identificador": sum(1 for p in aprovaveis if not self._identificador(p)),
            }
            resumo["total_aprovaveis"] += len(aprovaveis)
            resumo["total_aprovadas"] += gravadas
            for motivo, ids in recusas.items():
                if len(resumo["exemplos_recusadas"]) < 8 and ids:
                    resumo["exemplos_recusadas"].append({"peca": f"{modelo.__tablename__}:{ids[0]}", "motivo": motivo})
        return resumo

    def _avaliar(self, modelo, exigir_identificador):
        todas = modelo.query.all()
        por_nome = Counter(self._nome(p) for p in todas if self._nome(p)[0] and self._nome(p)[1])
        por_codigo = Counter(normalizar_identidade(p.part_number) for p in todas if normalizar_identidade(p.part_number))
        aprovaveis, recusas = [], {}
        for peca in todas:
            if peca.status_validacao != "em_revisao":
                continue
            motivo = self._recusa(peca, por_nome, por_codigo, exigir_identificador)
            if motivo:
                recusas.setdefault(motivo, []).append(peca.id)
            else:
                aprovaveis.append(peca)
        return aprovaveis, recusas

    @staticmethod
    def _nome(peca):
        return normalizar_identidade(peca.fabricante), normalizar_identidade(peca.modelo)

    @staticmethod
    def _identificador(peca):
        return bool(normalizar_identidade(peca.part_number) or normalizar_identidade(getattr(peca, "codigo_modelo_fabricante", None)))

    def _recusa(self, peca, por_nome, por_codigo, exigir_identificador):
        fabricante, nome = self._nome(peca)
        if len(fabricante) < 2 or len(nome) < 2:
            return "identidade_incompleta"
        if not re.search(r"\d", nome):
            return "modelo_generico"
        if exigir_identificador and not self._identificador(peca):
            return "sem_part_number"
        if peca.ficha_montagem_validada is False:
            return "ficha_reprovada"
        if pendencias_para_montagem(peca):
            return "ficha_incompleta"
        codigo = normalizar_identidade(peca.part_number)
        if por_nome[(fabricante, nome)] > 1 or (codigo and por_codigo[codigo] > 1):
            return "possivel_duplicata"
        return None

    @staticmethod
    def _aprovar(modelo, ids):
        agora = datetime.now(timezone.utc).replace(tzinfo=None)
        total = 0
        try:
            for inicio in range(0, len(ids), LOTE_GRAVACAO):
                lote = ids[inicio:inicio + LOTE_GRAVACAO]
                total += modelo.query.filter(modelo.id.in_(lote), modelo.status_validacao == "em_revisao").update(
                    {"status_validacao": "aprovado", "validacao_motivo": MOTIVO, "validado_em": agora},
                    synchronize_session=False)
                db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return total

    def reverter(self, *, categoria=None, simular=True):
        """Volta para revisão as aprovadas por esta regra que ainda não têm nenhuma oferta."""
        from models import Oferta
        modelos = [m for m in MODELOS_PECAS if categoria is None or m.__tablename__ == categoria]
        if not modelos:
            raise ValueError("Categoria inválida")
        resumo = {"simulacao": simular, "categorias": {}}
        for modelo in modelos:
            com_oferta = db.session.query(Oferta.peca_id).filter(Oferta.tabela_peca == modelo.__tablename__)
            consulta = modelo.query.filter(modelo.status_validacao == "aprovado", modelo.validacao_motivo == MOTIVO,
                                           ~modelo.id.in_(com_oferta))
            quantidade = consulta.count()
            if not simular and quantidade:
                try:
                    consulta.update({"status_validacao": "em_revisao", "validacao_motivo": None, "validado_em": None},
                                    synchronize_session=False)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    raise
            resumo["categorias"][modelo.__tablename__] = quantidade
        return resumo
