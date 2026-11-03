"""Campos opcionais compartilhados somente por CPU e GPU."""
from . import db


class BenchmarkMixin:
    benchmark_teste = db.Column(db.String(120), nullable=True)
    benchmark_versao = db.Column(db.String(60), nullable=True)
    benchmark_nome_fonte = db.Column(db.String(255), nullable=True)
    benchmark_fonte = db.Column(db.Text, nullable=True)
    benchmark_atualizado_em = db.Column(db.DateTime, nullable=True)
    benchmark_referencia_em = db.Column(db.Date, nullable=True)

    @classmethod
    def listar_por_benchmark(cls, preco_maximo, prioridade, limite=12):
        """Candidatos comparáveis por pontuação ou pontos por real, sem gravar."""
        pontuacao = getattr(cls, cls.BENCHMARK_CAMPO)
        criterio = pontuacao / cls.preco if prioridade == "custo_beneficio" else pontuacao
        return (cls._consulta_benchmark(preco_maximo)
                .order_by(criterio.desc(), cls.preco.asc(), cls.id.asc()).limit(limite).all())

    @classmethod
    def listar_pool_benchmark(cls, preco_maximo):
        """Carrega todos os elegíveis antes de Pareto, faixas e diversidade."""
        return cls._consulta_benchmark(preco_maximo).order_by(cls.preco.asc(), cls.id.asc()).all()

    @classmethod
    def _consulta_benchmark(cls, preco_maximo):
        pontuacao = getattr(cls, cls.BENCHMARK_CAMPO)
        return cls.consulta_publicavel().filter(
            cls.preco > 0, cls.preco <= preco_maximo, cls.esgotado.is_(False),
            pontuacao.isnot(None), pontuacao > 0,
            cls.benchmark_teste == cls.BENCHMARK_TESTE, cls.benchmark_versao.is_(None),
        )
