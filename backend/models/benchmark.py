"""Campos opcionais compartilhados somente por CPU e GPU."""
from . import db


class BenchmarkMixin:
    benchmark_teste = db.Column(db.String(120), nullable=True)
    benchmark_versao = db.Column(db.String(60), nullable=True)
    benchmark_nome_fonte = db.Column(db.String(255), nullable=True)
    benchmark_fonte = db.Column(db.Text, nullable=True)
    benchmark_atualizado_em = db.Column(db.DateTime, nullable=True)
    benchmark_referencia_em = db.Column(db.Date, nullable=True)
