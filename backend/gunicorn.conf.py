import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

bind = os.getenv("GUNICORN_BIND", "127.0.0.1:8000")
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
threads = int(os.getenv("GUNICORN_THREADS", "4"))
worker_class = "gthread"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "120"))
preload_app = False
reload = False
accesslog = "-"
errorlog = "-"
# Não registrar query strings: o callback OAuth contém um código temporário.
access_log_format = '%(h)s %(m)s %(U)s %(s)s %(L)s'
# O tratamento de X-Forwarded-Proto fica centralizado no ProxyFix configurado.
secure_scheme_headers = {}

if min(workers, threads, timeout, graceful_timeout) < 1:
    raise ValueError("Workers, threads e tempos do Gunicorn devem ser positivos")
