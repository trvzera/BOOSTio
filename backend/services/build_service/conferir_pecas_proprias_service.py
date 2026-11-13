from models.build_salva import MODELOS
from services.build_service.planejamento_geracao import ErroPlanejamentoBuild


class ConferirPecasPropriasService:
    """Processador, placa de vídeo e fonte próprios entram no cálculo de consumo e de potência da fonte.
    Se o modelo digitado não for reconhecido, a validação não tem dados e a geração falharia depois de
    gastar a IA, com uma mensagem que culpa a IA. Aqui o usuário é avisado antes, com sugestões."""

    ROTULOS = {"processador": "o processador", "placa_video": "a placa de vídeo", "fonte": "a fonte"}
    MAXIMO_SUGESTOES = 3

    @classmethod
    def executar(cls, proprias):
        desconhecidas = [(tipo, nome) for tipo, nome in proprias.items()
                         if tipo in cls.ROTULOS and tipo in MODELOS and MODELOS[tipo].buscar_por_nome(nome) is None]
        if not desconhecidas:
            return
        partes = [cls._descrever(tipo, nome) for tipo, nome in desconhecidas]
        raise ErroPlanejamentoBuild(
            "Não reconhecemos " + " e ".join(partes) + ". Sem o modelo exato do catálogo não calculamos o consumo "
            "nem conferimos a fonte. Escreva o nome como aparece no catálogo ou deixe a BOOSTio escolher essa peça. "
            "Nenhuma build foi salva.",
            "pecas", "Não reconhecemos uma peça que você já possui", "pecas")

    @classmethod
    def _descrever(cls, tipo, nome):
        texto = f'{cls.ROTULOS[tipo]} "{nome}"'
        sugestoes = cls.sugestoes(tipo, nome)
        return texto + (" (modelos parecidos: " + "; ".join(sugestoes) + ")" if sugestoes else "")

    @classmethod
    def sugestoes(cls, tipo, nome):
        termos = [t for t in nome.casefold().split() if t]
        if not termos:
            return []
        achadas = []
        for peca in MODELOS[tipo].query.all():
            completo = " ".join(f"{peca.fabricante} {peca.modelo}".split())
            if all(t in completo.casefold() for t in termos):
                achadas.append(completo[:70])
        return sorted(set(achadas), key=lambda texto: (len(texto), texto))[:cls.MAXIMO_SUGESTOES]
